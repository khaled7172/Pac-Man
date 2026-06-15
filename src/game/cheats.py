"""src/game/cheats.py — Cheat mode manager for reviewer testing.

Provides keyboard-activated cheats so the reviewer can quickly test all
game features without having to play through the game normally.
"""

from __future__ import annotations

import logging
from typing import Any

import pygame

logger = logging.getLogger(__name__)


class CheatManager:
    """Manages cheat mode toggles for review and testing purposes.

    Available cheats:
        I — Invincibility (ghosts cannot kill player)
        F — Ghost Freeze  (all ghosts stop moving)
        S — Speed Boost   (2× player movement speed)
        L — Extra Life    (add 1 life; one-shot, not toggle)
        N — Level Skip    (immediately complete current level)
    """

    _NORMAL_SPEED: float = 5.0
    _BOOST_SPEED: float = 10.0

    def __init__(self) -> None:
        """Initialise with all cheats disabled."""
        self.invincible: bool = False
        self.ghost_freeze: bool = False
        self.speed_boost: bool = False

    # ── Input ────────────────────────────────────────────────────────────────

    def handle_key(self, key: int, game: Any) -> str | None:
        """Toggle a cheat on keypress.

        Args:
            key:  pygame key constant.
            game: The Game instance (used for level-skip and player access).

        Returns:
            Human-readable name of the toggled cheat, or None if no cheat
            was triggered by this key.
        """
        if key == pygame.K_i:
            self.invincible = not self.invincible
            name = "INVINCIBLE" if self.invincible else "-invincible"
            logger.info("Cheat: %s", name)
            return name

        if key == pygame.K_f:
            self.ghost_freeze = not self.ghost_freeze
            name = "FREEZE" if self.ghost_freeze else "-freeze"
            logger.info("Cheat: %s", name)
            return name

        if key == pygame.K_s:
            self.speed_boost = not self.speed_boost
            if game._player is not None:
                game._player._speed = (
                    self._BOOST_SPEED if self.speed_boost else self._NORMAL_SPEED
                )
            name = "SPEED×2" if self.speed_boost else "-speed"
            logger.info("Cheat: %s", name)
            return name

        if key == pygame.K_l:
            self.add_life(game._player)
            return "EXTRA LIFE"

        if key == pygame.K_n:
            self.skip_level(game)
            return "LEVEL SKIP"

        return None

    # ── Effects ──────────────────────────────────────────────────────────────

    def add_life(self, player: Any) -> None:
        """Add 1 extra life to the player.

        Args:
            player: The Player instance, or None (no-op).
        """
        if player is not None:
            player.lives += 1
            logger.info("Cheat: extra life — lives now %d", player.lives)

    def skip_level(self, game: Any) -> None:
        """Immediately complete the current level by eating all pellets.

        Args:
            game: The Game instance.
        """
        if game._level is not None:
            for p in game._level.pellets:
                p.eat()
            for sp in game._level.super_pellets:
                sp.eat()
            logger.info("Cheat: level skipped")

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def active_cheats(self) -> list[str]:
        """List of currently active (toggle) cheat display names.

        Returns:
            List of short strings for HUD display.
        """
        active: list[str] = []
        if self.invincible:
            active.append("INVINCIBLE")
        if self.ghost_freeze:
            active.append("FREEZE")
        if self.speed_boost:
            active.append("SPEED×2")
        return active

    def reset(self) -> None:
        """Reset all toggle cheats to off.

        Called when a new game starts so cheats don't carry over.
        """
        self.invincible = False
        self.ghost_freeze = False
        self.speed_boost = False
