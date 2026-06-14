"""src/entities/ghost.py — Ghost entity with BFS AI.

Each ghost is always in one of four states:
    CHASE  — moves toward Pac-Man (BFS shortest path).
    FLEE   — runs away from Pac-Man (BFS longest safe path).
    EATEN  — just eaten by Pac-Man; returns to its corner spawn.
    FROZEN — externally paused (cheat mode).

Movement uses the same smooth tile-based interpolation as Player.
"""

import collections
import random
from enum import Enum, auto
from typing import Optional

from src.maze.loader import can_move, get_walkable_cells

DIRECTION_VECTORS: dict[str, tuple[int, int]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}
ALL_DIRS: list[str] = ["N", "S", "E", "W"]


class GhostState(Enum):
    """Ghost behaviour state."""

    CHASE = auto()
    FLEE = auto()
    EATEN = auto()
    FROZEN = auto()


class Ghost:
    """A single ghost.

    Args:
        spawn_row:       Corner row where this ghost starts (and respawns).
        spawn_col:       Corner column.
        colour:          Colour name: 'red', 'pink', 'cyan', 'orange'.
        move_speed:      Tiles per second in CHASE mode.
        edible_duration: Seconds the ghost stays edible after a super-pacgum.
        respawn_delay:   Seconds after being eaten before respawning.
    """

    # Edible flash starts this many seconds before edible time runs out
    FLASH_THRESHOLD: float = 2.0

    def __init__(
        self,
        spawn_row: int,
        spawn_col: int,
        colour: str = "red",
        move_speed: float = 3.5,
        edible_duration: float = 8.0,
        respawn_delay: float = 5.0,
    ) -> None:
        """Initialise ghost at its corner spawn."""
        self._spawn_row: int = spawn_row
        self._spawn_col: int = spawn_col
        self.colour: str = colour

        # Position
        self.row: int = spawn_row
        self.col: int = spawn_col
        self._prev_row: int = spawn_row
        self._prev_col: int = spawn_col
        self._progress: float = 1.0  # start at rest

        # Speeds
        self._speed_chase: float = move_speed
        self._speed_flee: float = move_speed * 0.6
        self._speed_eaten: float = move_speed * 2.0

        # State
        self._state: GhostState = GhostState.CHASE
        self._edible_timer: float = 0.0
        self._edible_duration: float = edible_duration
        self._respawn_timer: float = 0.0
        self._respawn_delay: float = respawn_delay

        # Pathfinding: next direction to move
        self._next_dir: str = "N"

        # Animation
        self._anim_frame: int = 0

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def prev_row(self) -> int:
        """Previous tile row (for smooth interpolation)."""
        return self._prev_row

    @property
    def prev_col(self) -> int:
        """Previous tile column (for smooth interpolation)."""
        return self._prev_col

    @property
    def progress(self) -> float:
        """Animation progress 0.0→1.0 between previous and current tile."""
        return self._progress

    @property
    def state(self) -> GhostState:
        """Current behaviour state."""
        return self._state

    @property
    def edible(self) -> bool:
        """True while the ghost can be eaten by Pac-Man."""
        return self._state == GhostState.FLEE

    @property
    def flashing(self) -> bool:
        """True when edible time is almost up (triggers blink sprite)."""
        return (
            self._state == GhostState.FLEE
            and self._edible_timer <= self.FLASH_THRESHOLD
        )

    @property
    def eaten(self) -> bool:
        """True while the ghost is returning to its spawn corner."""
        return self._state == GhostState.EATEN

    @property
    def anim_frame(self) -> int:
        """Current walk-cycle animation frame (0 or 1)."""
        return self._anim_frame

    # ── State transitions ───────────────────────────────────────────────────

    def make_edible(self) -> None:
        """Enter FLEE (edible) state — called when a super-pacgum is eaten."""
        if self._state == GhostState.EATEN:
            return  # already dead, ignore
        self._state = GhostState.FLEE
        self._edible_timer = self._edible_duration

    def be_eaten(self) -> None:
        """Enter EATEN state — called when Pac-Man eats this ghost."""
        self._state = GhostState.EATEN
        self._edible_timer = 0.0
        self._respawn_timer = self._respawn_delay

    def freeze(self) -> None:
        """Enter FROZEN state (cheat: ghost freeze)."""
        if self._state not in (GhostState.EATEN,):
            self._state = GhostState.FROZEN

    def unfreeze(self) -> None:
        """Exit FROZEN state back to CHASE."""
        if self._state == GhostState.FROZEN:
            self._state = GhostState.CHASE

    def reset(self) -> None:
        """Hard-reset ghost to spawn position in CHASE state."""
        self.row = self._spawn_row
        self.col = self._spawn_col
        self._prev_row = self._spawn_row
        self._prev_col = self._spawn_col
        self._progress = 1.0
        self._state = GhostState.CHASE
        self._edible_timer = 0.0
        self._respawn_timer = 0.0

    # ── Update ──────────────────────────────────────────────────────────────

    def update(
        self,
        dt: float,
        grid: list[list[int]],
        player_row: int,
        player_col: int,
    ) -> None:
        """Advance ghost state by one frame.

        Args:
            dt:         Delta time in seconds.
            grid:       Current maze grid.
            player_row: Pac-Man's current tile row.
            player_col: Pac-Man's current tile column.
        """
        if self._state == GhostState.FROZEN:
            return

        if self._state == GhostState.EATEN:
            self._update_eaten(dt, grid)
            return

        if self._state == GhostState.FLEE:
            self._edible_timer -= dt
            if self._edible_timer <= 0:
                self._state = GhostState.CHASE

        speed = (
            self._speed_flee
            if self._state == GhostState.FLEE
            else self._speed_chase
        )
        self._update_movement(dt, grid, player_row, player_col, speed)

    def _update_eaten(self, dt: float, grid: list[list[int]]) -> None:
        """Move back to spawn, then respawn after delay.

        Args:
            dt:   Delta time in seconds.
            grid: Maze grid.
        """
        # Still walking back?
        if self.row != self._spawn_row or self.col != self._spawn_col:
            self._update_movement(
                dt, grid,
                self._spawn_row, self._spawn_col,
                self._speed_eaten,
            )
            return

        # At spawn — wait for respawn timer
        self._respawn_timer -= dt
        if self._respawn_timer <= 0:
            self._state = GhostState.CHASE

    def _update_movement(
        self,
        dt: float,
        grid: list[list[int]],
        target_row: int,
        target_col: int,
        speed: float,
    ) -> None:
        """Tile-to-tile movement with BFS direction choice.

        Args:
            dt:         Delta time.
            grid:       Maze grid.
            target_row: Row to move toward (or away from in FLEE).
            target_col: Col to move toward (or away from in FLEE).
            speed:      Movement speed in tiles/second.
        """
        if self._progress < 1.0:
            self._progress = min(1.0, self._progress + speed * dt)
            # Tick animation every half-tile
            if self._progress >= 1.0:
                self._anim_frame ^= 1
            return

        # At a tile boundary — choose next direction
        direction = self._choose_direction(grid, target_row, target_col)
        if direction is None:
            return  # stuck

        dr, dc = DIRECTION_VECTORS[direction]
        self._prev_row = self.row
        self._prev_col = self.col
        self.row += dr
        self.col += dc
        self._next_dir = direction
        self._progress = 0.0

    def _choose_direction(
        self,
        grid: list[list[int]],
        target_row: int,
        target_col: int,
    ) -> Optional[str]:
        """Pick next direction via BFS.

        In CHASE/EATEN: moves toward target (shortest path).
        In FLEE: moves away from target (longest 1-step distance).

        Args:
            grid:       Maze grid.
            target_row: Target row.
            target_col: Target col.

        Returns:
            Direction string 'N'/'S'/'E'/'W', or None if no moves.
        """
        if self._state == GhostState.FLEE:
            return self._flee_direction(grid, target_row, target_col)
        return self._bfs_direction(grid, target_row, target_col)

    def _bfs_direction(
        self,
        grid: list[list[int]],
        target_row: int,
        target_col: int,
    ) -> Optional[str]:
        """BFS from current position to target; return first-step direction.

        Args:
            grid:       Maze grid.
            target_row: Destination row.
            target_col: Destination column.

        Returns:
            Direction of the first step, or None if unreachable.
        """
        start = (self.row, self.col)
        goal = (target_row, target_col)

        if start == goal:
            return None

        rows, cols = len(grid), len(grid[0])

        # BFS: queue holds (row, col, first_direction)
        queue: collections.deque[tuple[int, int, str]] = collections.deque()
        visited: set[tuple[int, int]] = {start}

        for d in ALL_DIRS:
            if (0 <= self.row < rows and 0 <= self.col < cols
                    and can_move(grid, self.row, self.col, d)):
                dr, dc = DIRECTION_VECTORS[d]
                nr, nc = self.row + dr, self.col + dc
                if (0 <= nr < rows and 0 <= nc < cols
                        and (nr, nc) not in visited):
                    visited.add((nr, nc))
                    queue.append((nr, nc, d))

        rows, cols = len(grid), len(grid[0])
        while queue:
            r, c, first_dir = queue.popleft()
            if (r, c) == goal:
                return first_dir
            for d in ALL_DIRS:
                if 0 <= r < rows and 0 <= c < cols and can_move(grid, r, c, d):
                    dr, dc = DIRECTION_VECTORS[d]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc, first_dir))

        # Target unreachable — pick any valid direction at random
        valid = [d for d in ALL_DIRS if can_move(grid, self.row, self.col, d)]
        return random.choice(valid) if valid else None

    def _flee_direction(
        self,
        grid: list[list[int]],
        player_row: int,
        player_col: int,
    ) -> Optional[str]:
        """Pick the direction that maximises Manhattan distance from player.

        Args:
            grid:       Maze grid.
            player_row: Pac-Man's row.
            player_col: Pac-Man's column.

        Returns:
            Best escape direction, or random valid direction as fallback.
        """
        best_dir: Optional[str] = None
        best_dist: int = -1

        for d in ALL_DIRS:
            if can_move(grid, self.row, self.col, d):
                dr, dc = DIRECTION_VECTORS[d]
                nr, nc = self.row + dr, self.col + dc
                dist = abs(nr - player_row) + abs(nc - player_col)
                if dist > best_dist:
                    best_dist = dist
                    best_dir = d

        if best_dir is None:
            valid = [d for d in ALL_DIRS
                     if can_move(grid, self.row, self.col, d)]
            return random.choice(valid) if valid else None

        return best_dir
