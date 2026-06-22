"""Ghost entity with BFS pathfinding.

States: CHASE, FLEE, EATEN, FROZEN.
Each ghost has colour-based AI smartness — red is the
smartest (50% BFS), orange is dumb (20% BFS, rest random).
"""

import collections
import random
from enum import Enum, auto
from typing import Optional

from src.maze.loader import can_move

DIR_DELTA = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}
ALL_DIRS = ["N", "S", "E", "W"]


class GhostState(Enum):
    CHASE = auto()
    FLEE = auto()
    EATEN = auto()
    FROZEN = auto()


class Ghost:
    """A single ghost with tile-based movement and BFS AI."""

    FLASH_THRESHOLD = 2.0  # seconds before edible ends

    def __init__(
        self,
        spawn_row: int,
        spawn_col: int,
        colour: str = "red",
        move_speed: float = 3.5,
        edible_duration: float = 8.0,
        respawn_delay: float = 5.0,
    ) -> None:
        """Set up ghost at its corner spawn."""
        self._spawn_row = spawn_row
        self._spawn_col = spawn_col
        self.colour = colour

        self.row = spawn_row
        self.col = spawn_col
        self._prev_row = spawn_row
        self._prev_col = spawn_col
        self._progress = 1.0

        # different speeds for different states
        self._speed_chase = move_speed
        self._speed_flee = move_speed * 0.6
        self._speed_eaten = move_speed * 2.0

        self._state = GhostState.CHASE
        self._edible_timer = 0.0
        self._edible_dur = edible_duration
        self._respawn_timer = 0.0
        self._respawn_delay = respawn_delay

        self._next_dir = "N"
        self._anim_frame = 0

    @property
    def prev_row(self) -> int:
        return self._prev_row

    @property
    def prev_col(self) -> int:
        return self._prev_col

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def state(self) -> GhostState:
        return self._state

    @property
    def edible(self) -> bool:
        return self._state == GhostState.FLEE

    @property
    def flashing(self) -> bool:
        """True when edible time almost up (blink sprite)."""
        return (
            self._state == GhostState.FLEE
            and self._edible_timer <= self.FLASH_THRESHOLD
        )

    @property
    def eaten(self) -> bool:
        return self._state == GhostState.EATEN

    @property
    def anim_frame(self) -> int:
        return self._anim_frame

    @property
    def spawn_row(self) -> int:
        return self._spawn_row

    @property
    def spawn_col(self) -> int:
        return self._spawn_col

    # --- state changes ---

    def make_edible(self) -> None:
        """Go edible (flee mode) when super-pacgum eaten."""
        if self._state == GhostState.EATEN:
            return  # already dead
        self._state = GhostState.FLEE
        self._edible_timer = self._edible_dur

    def be_eaten(self) -> None:
        """Ghost got eaten by pacman."""
        self._state = GhostState.EATEN
        self._edible_timer = 0.0
        self._respawn_timer = self._respawn_delay

    def freeze(self) -> None:
        """Cheat: freeze in place."""
        if self._state not in (GhostState.EATEN,):
            self._state = GhostState.FROZEN

    def unfreeze(self) -> None:
        """Cheat: unfreeze."""
        if self._state == GhostState.FROZEN:
            self._state = GhostState.CHASE

    def reset(self) -> None:
        """Hard reset to spawn, used after player dies."""
        self.row = self._spawn_row
        self.col = self._spawn_col
        self._prev_row = self._spawn_row
        self._prev_col = self._spawn_col
        self._progress = 1.0
        self._state = GhostState.CHASE
        self._edible_timer = 0.0
        self._respawn_timer = 0.0

    # --- update ---

    def update(
        self,
        dt: float,
        grid: list[list[int]],
        player_row: int,
        player_col: int,
    ) -> None:
        """Advance ghost one frame."""
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
        """Walk back to spawn then wait for respawn timer."""
        if self.row != self._spawn_row or self.col != self._spawn_col:
            self._update_movement(
                dt, grid,
                self._spawn_row, self._spawn_col,
                self._speed_eaten,
            )
            return

        # at spawn, wait
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
        """Move tile-to-tile toward target."""
        if self._progress < 1.0:
            self._progress = min(1.0, self._progress + speed * dt)
            if self._progress >= 1.0:
                self._anim_frame ^= 1
            return

        # on a tile, pick direction
        direction = self._choose_direction(grid, target_row, target_col)
        if direction is None:
            return  # stuck (shouldn't happen normally)

        dr, dc = DIR_DELTA[direction]
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
        if self._state == GhostState.FLEE:
            return self._flee_direction(grid, target_row, target_col)

        # colour-based intelligence — dumb but not braindead
        smartness = {
            'red': 0.60, 'pink': 0.45,
            'cyan': 0.30, 'orange': 0.20,
        }
        chance = smartness.get(self.colour, 0.40)

        # sometimes just go random (makes game more fun)
        if random.random() > chance:
            valid = [
                d for d in ALL_DIRS
                if can_move(grid, self.row, self.col, d)
            ]
            if valid:
                return random.choice(valid)

        return self._bfs_direction(grid, target_row, target_col)

    def _bfs_direction(
        self,
        grid: list[list[int]],
        target_row: int,
        target_col: int,
    ) -> Optional[str]:
        """BFS shortest path, returns first step direction."""
        start = (self.row, self.col)
        goal = (target_row, target_col)

        if start == goal:
            return None

        rows, cols = len(grid), len(grid[0])

        queue: collections.deque[tuple[int, int, str]] = (
            collections.deque()
        )
        visited: set[tuple[int, int]] = {start}

        for d in ALL_DIRS:
            if (0 <= self.row < rows and 0 <= self.col < cols
                    and can_move(grid, self.row, self.col, d)):
                dr, dc = DIR_DELTA[d]
                nr, nc = self.row + dr, self.col + dc
                if (0 <= nr < rows and 0 <= nc < cols
                        and (nr, nc) not in visited):
                    visited.add((nr, nc))
                    queue.append((nr, nc, d))

        while queue:
            r, c, first_dir = queue.popleft()
            if (r, c) == goal:
                return first_dir
            for d in ALL_DIRS:
                if (0 <= r < rows and 0 <= c < cols
                        and can_move(grid, r, c, d)):
                    dr, dc = DIR_DELTA[d]
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and (nr, nc) not in visited):
                        visited.add((nr, nc))
                        queue.append((nr, nc, first_dir))

        # unreachable, just go somewhere
        valid = [
            d for d in ALL_DIRS
            if can_move(grid, self.row, self.col, d)
        ]
        return random.choice(valid) if valid else None

    def _flee_direction(
        self,
        grid: list[list[int]],
        player_row: int,
        player_col: int,
    ) -> Optional[str]:
        """Run away — pick direction that maximises distance."""
        best_dir: Optional[str] = None
        best_dist = -1

        for d in ALL_DIRS:
            if can_move(grid, self.row, self.col, d):
                dr, dc = DIR_DELTA[d]
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
