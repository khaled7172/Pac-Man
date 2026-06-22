"""Player entity for Pac-Man.

Tile-based movement with smooth interpolation between tiles.
Buffers one direction change and applies it when possible.
"""

import pygame
from src.maze.loader import can_move

# (row_delta, col_delta) for each direction
DIR_DELTA = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}

KEY_MAP = {
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
    """Pac-Man player. Handles movement, lives, death animation."""

    def __init__(
        self,
        start_row: int,
        start_col: int,
        lives: int = 3,
        move_speed: float = 5.0,
    ) -> None:
        """Set up player at maze center."""
        # spawn pos (for respawn later)
        self._spawn_row = start_row
        self._spawn_col = start_col

        self.row = start_row
        self.col = start_col

        # previous tile for interpolation
        self._prev_row = start_row
        self._prev_col = start_col

        self._direction = "E"
        self._buffered = "E"

        self._progress = 1.0  # start at rest on tile

        self._speed = move_speed  # tiles/sec

        self.lives = lives
        self.alive = True
        self._dying = False
        self._death_timer = 0.0
        self._death_time = 2.0  # how long death anim plays
        self._respawn_invincible_timer = 0.0

        # mouth anim
        self._mouth_angle = 45.0
        self._mouth_open = True
        self._mouth_speed = 8.0

    @property
    def direction(self) -> str:
        return self._direction

    @property
    def is_dying(self) -> bool:
        return self._dying

    @property
    def invincible_grace(self) -> bool:
        """True during post-respawn invincibility window."""
        return self._respawn_invincible_timer > 0

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def prev_row(self) -> int:
        return self._prev_row

    @property
    def prev_col(self) -> int:
        return self._prev_col

    # --- input ---

    def handle_keydown(self, key: int) -> None:
        """Buffer a direction from keypress."""
        if key in KEY_MAP:
            self._buffered = KEY_MAP[key]

    # --- update ---

    def update(self, dt: float, grid: list[list[int]]) -> None:
        """Advance player state one frame."""
        # tick down invincibility even while dying
        if self._respawn_invincible_timer > 0:
            self._respawn_invincible_timer = max(
                0.0, self._respawn_invincible_timer - dt,
            )
        if self._dying:
            self._update_death(dt)
            return

        self._update_movement(dt, grid)
        self._update_mouth(dt)

    def _update_movement(self, dt: float, grid: list[list[int]]) -> None:
        """Tile-to-tile movement with direction buffering."""
        if self._progress < 1.0:
            self._progress = min(1.0, self._progress + self._speed * dt)
            return

        # fully on tile, try to move
        # try buffered dir first, then current dir
        for d in (self._buffered, self._direction):
            if can_move(grid, self.row, self.col, d):
                dr, dc = DIR_DELTA[d]
                self._prev_row = self.row
                self._prev_col = self.col
                self.row += dr
                self.col += dc
                self._direction = d
                self._buffered = d
                self._progress = 0.0
                return
        # blocked — just stay put

    def _update_mouth(self, dt: float) -> None:
        """Chomp chomp animation."""
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
        """Tick death animation timer."""
        self._death_timer += dt
        if self._death_timer >= self._death_time:
            self._dying = False
            self._death_timer = 0.0

    # --- game events ---

    def die(self) -> None:
        """Lose a life, start death animation."""
        if self._dying:
            return
        self.lives -= 1
        self._dying = True
        self._death_timer = 0.0
        if self.lives <= 0:
            self.alive = False

    def respawn(self) -> None:
        """Reset to spawn after death anim finishes."""
        self.row = self._spawn_row
        self.col = self._spawn_col
        self._prev_row = self._spawn_row
        self._prev_col = self._spawn_col
        self._direction = "E"
        self._buffered = "E"
        self._progress = 1.0
        self._dying = False
        self._respawn_invincible_timer = 2.0  # brief grace period

    def get_mouth_angle(self) -> float:
        """Current mouth angle 0-45 degrees."""
        return self._mouth_angle
