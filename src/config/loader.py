"""Configuration loader for Pac-Man.

Reads a JSON file that may contain # comment lines.
Validates all keys and applies safe defaults for missing or invalid values.
Never raises — logs warnings and continues.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


DEFAULTS: dict[str, Any] = {
    "lives": 3,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,
    "level_max_time": 90,
    "ghost_edible_duration": 8,
    "ghost_respawn_delay": 5,
    "highscore_filename": "highscores.json",
    "levels": [
        {"width": 21, "height": 21, "seed": 42},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
        {"width": 21, "height": 21, "seed": 0},
    ],
}

_INT_KEYS: dict[str, tuple[int, int]] = {
    "lives": (1, 10),
    "points_per_pacgum": (1, 10000),
    "points_per_super_pacgum": (1, 10000),
    "points_per_ghost": (1, 10000),
    "level_max_time": (10, 3600),
    "ghost_edible_duration": (1, 60),
    "ghost_respawn_delay": (1, 60),
}



def _strip_comments(raw: str) -> str:
    """Remove # comment lines from a JSON string.

    Args:
        raw: Raw file contents that may contain # comment lines.

    Returns:
        A string with all comment lines removed, safe to pass to json.loads().
    """
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)



def _clamp_int(key: str, value: Any) -> int:
    """Validate and clamp an integer config value.

    Args:
        key:   Config key name (used for logging).
        value: Raw value from the config file.

    Returns:
        A valid integer within the allowed range for that key.
    """
    lo, hi = _INT_KEYS[key]
    default = DEFAULTS[key]
    try:
        v = int(value)
    except (TypeError, ValueError):
        logger.warning(
            "Config: '%s' has invalid value %r — using default %d",
            key, value, default
        )
        return int(default)
    if not (lo <= v <= hi):
        clamped = max(lo, min(hi, v))
        logger.warning(
            "Config: '%s' value %d is out of range [%d, %d] — clamped to %d",
            key, v, lo, hi, clamped
        )
        return clamped
    return v


def _validate_level(raw: Any, index: int) -> dict[str, Any]:
    """Validate a single level definition dict.

    Args:
        raw:   Raw level entry from the config file.
        index: Level index (for logging).

    Returns:
        A validated level dict with keys: width, height, seed.
    """
    default_level: dict[str, Any] = {"width": 21, "height": 21, "seed": 0}

    if not isinstance(raw, dict):
        logger.warning(
            "Config: level[%d] is not a dict — using default", index
        )
        return default_level

    result: dict[str, Any] = {}

    for dim in ("width", "height"):
        val = raw.get(dim, default_level[dim])
        try:
            v = int(val)
            result[dim] = max(7, v)   # minimum 7 so '42' logo fits
            if v < 7:
                logger.warning(
                    "Config: level[%d].%s=%d too small — clamped to 7",
                    index, dim, v
                )
        except (TypeError, ValueError):
            logger.warning(
                "Config: level[%d].%s invalid — using default %d",
                index, dim, default_level[dim]
            )
            result[dim] = default_level[dim]

    seed_val = raw.get("seed", 0)
    try:
        result["seed"] = max(0, int(seed_val))
    except (TypeError, ValueError):
        logger.warning(
            "Config: level[%d].seed invalid — using 0 (random)", index
        )
        result["seed"] = 0

    return result



def load_config(path: str) -> dict[str, Any]:
    """Load and validate the game configuration file.

    Reads a JSON file (with optional # comment lines), validates every key,
    clamps out-of-range numbers to safe values, and fills in defaults for
    anything missing or invalid. Never raises — always returns a usable dict.

    Args:
        path: Path to the JSON config file.

    Returns:
        A fully validated configuration dictionary.
    """
    config: dict[str, Any] = dict(DEFAULTS)

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        import sys
        import os
        meipass_path = None
        if hasattr(sys, '_MEIPASS'):
            meipass_path = os.path.join(getattr(sys, '_MEIPASS', ''), path)

        if meipass_path and os.path.exists(meipass_path):
            with open(meipass_path, "r", encoding="utf-8") as f:
                raw = f.read()
        else:
            logger.error("Config file not found: '%s' — using all defaults", path)
            return config
    except OSError as e:
        logger.error("Cannot read config file '%s': %s — using all defaults",
                     path, e)
        return config

    try:
        cleaned = _strip_comments(raw)
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(
            "Config file '%s' has invalid JSON: %s — using all defaults",
            path, e
        )
        return config

    if not isinstance(data, dict):
        logger.error(
            "Config file '%s' must be a JSON object — using all defaults",
            path)
        return config

    for key in _INT_KEYS:
        if key in data:
            config[key] = _clamp_int(key, data[key])

    hs = data.get("highscore_filename", DEFAULTS["highscore_filename"])
    if isinstance(hs, str) and hs.strip():
        config["highscore_filename"] = hs.strip()
    else:
        logger.warning(
            "Config: 'highscore_filename' invalid — using default '%s'",
            DEFAULTS["highscore_filename"]
        )

    raw_levels = data.get("levels", DEFAULTS["levels"])
    if not isinstance(raw_levels, list) or len(raw_levels) == 0:
        logger.warning(
            "Config: 'levels' missing or empty — using default 10 levels"
        )
    else:
        validated_levels = [
            _validate_level(lvl, i) for i, lvl in enumerate(raw_levels)
        ]
        if len(validated_levels) < 10:
            logger.warning(
                "Config: only %d levels defined (minimum recommended: 10)",
                len(validated_levels)
            )
        config["levels"] = validated_levels

    return config
