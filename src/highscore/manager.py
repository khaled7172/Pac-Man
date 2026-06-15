"""src/highscore/manager.py — Persistent top-10 highscore manager.

Stores scores in a JSON file as a list of dicts:
    [{"name": "AAA", "score": 1234}, ...]

The file is created if missing and reset if corrupted.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MAX_SCORES: int = 10
MAX_NAME_LEN: int = 10
NAME_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9 ]+$")


class HighscoreManager:
    """Manages persistent top-10 highscore list.

    Stores scores as JSON: [{"name": "AAA", "score": 1234}, ...]
    File is created if missing, reset if corrupted.

    Args:
        filepath: Path to the JSON highscore file.
    """

    def __init__(self, filepath: str) -> None:
        """Initialise and load existing scores."""
        self.filepath = Path(filepath)
        self.scores: list[dict[str, Any]] = []
        self.load()

    # ── Persistence ─────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load scores from JSON file.

        Handles missing files gracefully (starts fresh).
        Handles corrupt JSON gracefully (resets to empty list).
        """
        if not self.filepath.exists():
            logger.info(
                "Highscore file not found — starting fresh: %s",
                self.filepath,
            )
            self.scores = []
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                raise ValueError("Highscore file root must be a JSON array.")
            validated: list[dict[str, Any]] = []
            for entry in data:
                if (
                    isinstance(entry, dict)
                    and isinstance(entry.get("name"), str)
                    and isinstance(entry.get("score"), int)
                ):
                    validated.append(
                        {"name": entry["name"], "score": entry["score"]}
                    )
            self.scores = sorted(
                validated, key=lambda x: x["score"], reverse=True,
            )[:MAX_SCORES]
            logger.info(
                "Loaded %d highscores from %s", len(self.scores), self.filepath,
            )
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.warning(
                "Could not load highscores (%s) — resetting.", exc,
            )
            self.scores = []

    def save(self) -> None:
        """Save current scores to JSON file.

        Creates parent directories if needed.
        Never raises — logs a warning on failure.
        """
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as fh:
                json.dump(self.scores, fh, indent=2, ensure_ascii=False)
            logger.info(
                "Highscores saved to %s (%d entries)",
                self.filepath, len(self.scores),
            )
        except OSError as exc:
            logger.warning("Could not save highscores: %s", exc)

    # ── Score management ─────────────────────────────────────────────────────

    def add_score(self, name: str, score: int) -> bool:
        """Add a score if it qualifies for the top-10.

        Args:
            name:  Player name (will be validated/cleaned).
            score: Player score.

        Returns:
            True if the score was added to the list, False otherwise.
        """
        clean = self.validate_name(name)
        if not clean:
            clean = "PLAYER"
        if not self.is_high_score(score) and len(self.scores) >= MAX_SCORES:
            return False
        self.scores.append({"name": clean, "score": score})
        self.scores = sorted(
            self.scores, key=lambda x: x["score"], reverse=True,
        )[:MAX_SCORES]
        self.save()
        return True

    def get_top10(self) -> list[dict[str, Any]]:
        """Return top-10 scores sorted descending.

        Returns:
            List of at most 10 dicts with 'name' and 'score' keys.
        """
        return list(self.scores[:MAX_SCORES])

    def is_high_score(self, score: int) -> bool:
        """Check if a score qualifies for the top-10.

        Args:
            score: The score to test.

        Returns:
            True if the score would enter the top-10.
        """
        if len(self.scores) < MAX_SCORES:
            return True
        return bool(score > self.scores[-1]["score"])

    # ── Validation ───────────────────────────────────────────────────────────

    @staticmethod
    def validate_name(name: str) -> str:
        """Validate and clean a player name.

        Strips leading/trailing whitespace, removes invalid characters,
        and truncates to MAX_NAME_LEN.

        Args:
            name: Raw player name string.

        Returns:
            Cleaned name string (may be empty if completely invalid).
        """
        stripped = name.strip()
        # Keep only alphanumeric + single spaces
        cleaned = re.sub(r"[^A-Za-z0-9 ]", "", stripped)
        # Collapse multiple spaces
        cleaned = re.sub(r" {2,}", " ", cleaned).strip()
        return cleaned[:MAX_NAME_LEN]
