"""src/entities/pellet.py — Pacgum and SuperPacgum pellet entities.

A Pacgum is a small dot worth a few points.
A SuperPacgum is a large power pellet placed in the 4 corners that
triggers ghost-edible state when eaten.
"""


class Pacgum:
    """A regular small dot pellet.

    Args:
        row: Grid row of this pellet.
        col: Grid column of this pellet.
    """

    POINTS: int = 10  # overridden by config at spawn time

    def __init__(self, row: int, col: int) -> None:
        """Initialise pellet at (row, col), visible and not eaten."""
        self.row: int = row
        self.col: int = col
        self.eaten: bool = False

    def eat(self) -> int:
        """Mark this pellet as eaten and return its point value.

        Returns:
            Point value (Pacgum.POINTS), or 0 if already eaten.
        """
        if self.eaten:
            return 0
        self.eaten = True
        return self.POINTS


class SuperPacgum:
    """A large power pellet placed in corner cells.

    Eating one triggers ghost-edible (flee) mode for a configurable
    duration.  The pellet blinks on screen to draw attention.

    Args:
        row:    Grid row of this pellet.
        col:    Grid column of this pellet.
        points: Point value awarded when eaten.
    """

    POINTS: int = 50  # overridden by config at spawn time
    BLINK_INTERVAL: float = 0.4   # seconds between visible / hidden

    def __init__(self, row: int, col: int) -> None:
        """Initialise super pellet at (row, col)."""
        self.row: int = row
        self.col: int = col
        self.eaten: bool = False

        # Blink animation state
        self._blink_timer: float = 0.0
        self._visible: bool = True

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def visible(self) -> bool:
        """True when the pellet should be drawn (blink off = False)."""
        return self._visible

    # ── Update ──────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Advance blink animation timer.

        Args:
            dt: Delta time in seconds since last frame.
        """
        if self.eaten:
            return
        self._blink_timer += dt
        if self._blink_timer >= self.BLINK_INTERVAL:
            self._blink_timer = 0.0
            self._visible = not self._visible

    # ── Game events ─────────────────────────────────────────────────────────

    def eat(self) -> int:
        """Mark this pellet as eaten and return its point value.

        Returns:
            Point value (SuperPacgum.POINTS), or 0 if already eaten.
        """
        if self.eaten:
            return 0
        self.eaten = True
        self._visible = False
        return self.POINTS
