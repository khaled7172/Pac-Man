"""src/game/scoring.py — Score tracking for Pac-Man.

Tracks the current score, exposes atomic add methods,
and provides a combo multiplier for eating multiple ghosts
during a single super-pacgum activation.
"""


class Scoring:
    """Tracks player score and ghost-eating combo during one game.

    Args:
        points_per_pacgum:       Points awarded per regular pellet.
        points_per_super_pacgum: Points awarded per power pellet.
        points_per_ghost:        Base points for the first ghost eaten
                                 in a single edible session (doubles
                                 for each subsequent ghost: 200, 400,
                                 800, 1600).
    """

    def __init__(
        self,
        points_per_pacgum: int = 10,
        points_per_super_pacgum: int = 50,
        points_per_ghost: int = 200,
    ) -> None:
        """Initialise scoring with zero score and no active combo."""
        self._score: int = 0
        self._pts_pacgum: int = points_per_pacgum
        self._pts_super: int = points_per_super_pacgum
        self._pts_ghost_base: int = points_per_ghost

        # Combo: how many ghosts eaten in the current edible window
        self._ghost_combo: int = 0

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def score(self) -> int:
        """Current total score."""
        return self._score

    # ── Score events ────────────────────────────────────────────────────────

    def eat_pacgum(self) -> int:
        """Award points for eating a regular pellet.

        Returns:
            Points awarded.
        """
        pts = self._pts_pacgum
        self._score += pts
        return pts

    def eat_super_pacgum(self) -> int:
        """Award points for eating a power pellet and reset ghost combo.

        Returns:
            Points awarded.
        """
        pts = self._pts_super
        self._score += pts
        self._ghost_combo = 0   # new edible window starts fresh
        return pts

    def eat_ghost(self) -> int:
        """Award points for eating an edible ghost (doubles each time).

        Ghost combo resets when a new super-pacgum is eaten.
        Sequence: base, base*2, base*4, base*8 (capped at 4 ghosts).

        Returns:
            Points awarded for this ghost.
        """
        multiplier = 2 ** self._ghost_combo
        pts = self._pts_ghost_base * multiplier
        self._score += pts
        self._ghost_combo = min(self._ghost_combo + 1, 3)
        return pts

    def reset_ghost_combo(self) -> None:
        """Reset ghost combo (called when edible time expires)."""
        self._ghost_combo = 0

    def add(self, points: int) -> None:
        """Add an arbitrary point value (e.g. time bonus).

        Args:
            points: Points to add (ignored if negative).
        """
        if points > 0:
            self._score += points
