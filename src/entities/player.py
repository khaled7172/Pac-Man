"""src/entities/player.py — Pac-Man player entity.

Handles position, direction buffering, wall-collision movement, and lives.
Movement is tile-based: the player moves one tile at a time, smoothly
animated between tiles using a progress value (0.0 -> 1.0).
"""

import pygame
from src.maze.loader import can_move

# Direction vectors: (row_delta, col_delta)
DIRECTION_VECTORS: dict[str, tuple[int, int]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}

# Key -> direction mapping
KEY_MAP: dict[int, str] = {
    pygame.K_UP: "N",
    pygame.K_w: "N",
    pygame.K_DOWN: "S",
    pygame.K_s: "S",
    pygame.K_RIGHT: "E",
    pygame.K_d: "E",
    pygame.K_LEFT: "W",
    pygame.K_a: "W",
}


class Player:
    """Pac-Man player entity.

    Movement is tile-based with smooth animation.
    The player can buffer one direction change which is applied as soon
    as the current move completes and the new direction is valid.

    Args:
        start_row:     Starting grid row (maze center).
        start_col:     Starting grid column (maze center).
        lives:         Number of lives at game start.
        move_speed:    Tiles per second (default 5).
    """

    def __init__(
        self,
        start_row: int,
        start_col: int,
        lives: int = 3,
        move_speed: float = 5.0,
    ) -> None:
        """Initialise the player at the maze center."""
        # Spawn position (never changes — used for respawn)
        self._spawn_row: int = start_row
        self._spawn_col: int = start_col

        # Current tile position
        self.row: int = start_row
        self.col: int = start_col

        # Previous tile (for smooth interpolation)
        self._prev_row: int = start_row
        self._prev_col: int = start_col

        # Current facing direction and buffered next direction
        self._direction: str = "E"
        self._buffered: str = "E"

        # Animation progress 0.0 (at prev tile) -> 1.0 (at current tile)
        self._progress: float = 1.0   # start at rest

        # Movement
        self._speed: float = move_speed   # tiles per second

        # Lives and state
        self.lives: int = lives
        self.alive: bool = True
        self._dying: bool = False
        self._death_timer: float = 0.0
        self._death_duration: float = 0.8   # seconds for death animation

        # Mouth animation
        self._mouth_angle: float = 45.0
        self._mouth_open: bool = True
        self._mouth_speed: float = 8.0   # degrees per frame tick

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def direction(self) -> str:
        """Current facing direction as N/S/E/W."""
        return self._direction

    @property
    def is_dying(self) -> bool:
        """True while the death animation is playing."""
        return self._dying

    @property
    def progress(self) -> float:
        """Animation progress between previous and current tile (0.0-1.0)."""
        return self._progress

    @property
    def prev_row(self) -> int:
        """Previous tile row (animation source)."""
        return self._prev_row

    @property
    def prev_col(self) -> int:
        """Previous tile column (animation source)."""
        return self._prev_col

    # ── Input ───────────────────────────────────────────────────────────────

    def handle_keydown(self, key: int) -> None:
        """Buffer a direction change from a keypress.

        Args:
            key: pygame key constant (e.g. pygame.K_UP).
        """
        if key in KEY_MAP:
            self._buffered = KEY_MAP[key]

    # ── Update ──────────────────────────────────────────────────────────────

    def update(self, dt: float, grid: list[list[int]]) -> None:
        """Advance player state by one frame.

        Args:
            dt:   Delta time in seconds since last frame.
            grid: Current maze grid for wall collision checks.
        """
        if self._dying:
            self._update_death(dt)
            return

        self._update_movement(dt, grid)
        self._update_mouth(dt)

    def _update_movement(self, dt: float, grid: list[list[int]]) -> None:
        """Handle tile-to-tile movement and direction buffering.

        Args:
            dt:   Delta time in seconds.
            grid: Maze grid for collision.
        """
        # Advance progress toward current tile
        if self._progress < 1.0:
            self._progress = min(1.0, self._progress + self._speed * dt)
            return

        # Progress == 1.0: player is fully on current tile — try to move
        # 1. Try buffered direction first
        # 2. Fall back to current direction
        for direction in (self._buffered, self._direction):
            if can_move(grid, self.row, self.col, direction):
                dr, dc = DIRECTION_VECTORS[direction]
                self._prev_row = self.row
                self._prev_col = self.col
                self.row += dr
                self.col += dc
                self._direction = direction
                self._buffered = direction
                self._progress = 0.0
                return
        # Blocked in all relevant directions — stay put

    def _update_mouth(self, dt: float) -> None:
        """Animate the Pac-Man mouth open/close.

        Args:
            dt: Delta time in seconds.
        """
        delta = self._mouth_speed * dt * 200
        if self._mouth_open:
            self._mouth_angle -= delta
            if self._mouth_angle <= 0:
                self._mouth_angle = 0.0
                self._mouth_open = False
        else:
            self._mouth_angle += delta
            if self._mouth_angle >= 45:
                self._mouth_angle = 45.0
                self._mouth_open = True

    def _update_death(self, dt: float) -> None:
        """Advance death animation timer.

        Args:
            dt: Delta time in seconds.
        """
        self._death_timer += dt
        if self._death_timer >= self._death_duration:
            self._dying = False
            self._death_timer = 0.0

    # ── Game events ─────────────────────────────────────────────────────────

    def die(self) -> None:
        """Trigger death: lose a life and start death animation."""
        if self._dying:
            return
        self.lives -= 1
        self._dying = True
        self._death_timer = 0.0
        if self.lives <= 0:
            self.alive = False

    def respawn(self) -> None:
        """Respawn at the maze center after death animation completes."""
        self.row = self._spawn_row
        self.col = self._spawn_col
        self._prev_row = self._spawn_row
        self._prev_col = self._spawn_col
        self._direction = "E"
        self._buffered = "E"
        self._progress = 1.0
        self._dying = False

    def get_mouth_angle(self) -> float:
        """Return current mouth opening angle in degrees (0=closed, 45=open).

        Returns:
            Float between 0.0 and 45.0.
        """
        return self._mouth_angle
