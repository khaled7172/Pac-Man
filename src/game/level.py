"""src/game/level.py — Encapsulates one level's state.

Holds the maze grid, all pellets, the timer, and the win/lose
conditions for a single level.  The Game class owns Level instances
and replaces them when a level is completed or the player dies.
"""

from typing import Any

from src.maze.loader import (
    generate_maze, get_walkable_cells,
    get_super_pacgum_positions,
)
from src.entities.pellet import Pacgum, SuperPacgum


class Level:
    """One level: maze + pellets + timer.

    Args:
        cfg:                     Level config dict (width, height, seed).
        points_per_pacgum:       Point value for regular pellets.
        points_per_super_pacgum: Point value for power pellets.
        max_time:                Time limit in seconds (0 = no limit).
    """

    def __init__(
        self,
        cfg: dict[str, Any],
        points_per_pacgum: int = 10,
        points_per_super_pacgum: int = 50,
        max_time: float = 90.0,
    ) -> None:
        """Generate maze and populate pellets."""
        # Set class-level point values before creating instances
        Pacgum.POINTS = points_per_pacgum
        SuperPacgum.POINTS = points_per_super_pacgum

        self._max_time: float = max_time
        self.time_left: float = max_time

        # Generate maze
        self.grid: list[list[int]] = generate_maze(
            width=cfg["width"],
            height=cfg["height"],
            seed=cfg["seed"],
        )

        # Populate pellets
        sp_positions = get_super_pacgum_positions(self.grid)
        walkable = get_walkable_cells(self.grid)
        walkable_set = set(walkable)

        # super-pacgums offset from ghost corners
        self.super_pellets: list[SuperPacgum] = [
            SuperPacgum(r, c)
            for (r, c) in sp_positions
            if (r, c) in walkable_set
        ]
        super_positions = {(sp.row, sp.col) for sp in self.super_pellets}

        # Regular pacgums on every other walkable cell
        self.pellets: list[Pacgum] = [
            Pacgum(r, c)
            for (r, c) in walkable
            if (r, c) not in super_positions
        ]

        # Build a fast lookup dict: (row, col) -> Pacgum | SuperPacgum
        self._pellet_map: dict[tuple[int, int], Pacgum] = {
            (p.row, p.col): p for p in self.pellets
        }
        self._super_map: dict[tuple[int, int], SuperPacgum] = {
            (sp.row, sp.col): sp for sp in self.super_pellets
        }

    # ── Queries ─────────────────────────────────────────────────────────────

    @property
    def pellets_remaining(self) -> int:
        """Number of regular pellets not yet eaten."""
        return sum(1 for p in self.pellets if not p.eaten)

    @property
    def complete(self) -> bool:
        """True when all regular pellets have been eaten."""
        return self.pellets_remaining == 0

    @property
    def time_expired(self) -> bool:
        """True when the countdown timer has reached zero."""
        return self._max_time > 0 and self.time_left <= 0.0

    def get_pellet_at(self, row: int, col: int) -> "Pacgum | None":
        """Return the uneaten Pacgum at (row, col), or None.

        Args:
            row: Grid row.
            col: Grid column.

        Returns:
            Pacgum if present and uneaten, else None.
        """
        p = self._pellet_map.get((row, col))
        if p and not p.eaten:
            return p
        return None

    def get_super_pellet_at(self, row: int, col: int) -> "SuperPacgum | None":
        """Return the uneaten SuperPacgum at (row, col), or None.

        Args:
            row: Grid row.
            col: Grid column.

        Returns:
            SuperPacgum if present and uneaten, else None.
        """
        sp = self._super_map.get((row, col))
        if sp and not sp.eaten:
            return sp
        return None

    # ── Update ──────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Advance level timer and pellet animations.

        Args:
            dt: Delta time in seconds since last frame.
        """
        if self._max_time > 0:
            self.time_left = max(0.0, self.time_left - dt)

        for sp in self.super_pellets:
            sp.update(dt)
