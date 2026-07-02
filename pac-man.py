"""pac-man.py — Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py <config.json>

Loads configuration, calculates the window size from the largest
level, initialises pygame, and hands control to the Game class.
"""

import logging
import sys

import pygame

from src.config.loader import load_config
from src.game.game import Game, TILE_SIZE, HUD_W

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

TITLE: str = "Pac-Man"
MIN_WINDOW_H: int = 500


def main() -> None:
    """Parse arguments, load config, open window, run game."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]
    if not config_path.endswith(".json"):
        print(f"Error: '{config_path}' is not a .json file")
        sys.exit(1)

    config = load_config(config_path)
    logger.info(
        "Config loaded — %d levels, %d lives",
        len(config["levels"]),
        config["lives"],
    )

    max_cols = max(
        lvl["width"] for lvl in config["levels"]
    )
    max_rows = max(
        lvl["height"] for lvl in config["levels"]
    )
    window_w = max_cols * TILE_SIZE + HUD_W
    window_h = max(max_rows * TILE_SIZE, MIN_WINDOW_H)

    pygame.init()
    screen = pygame.display.set_mode((window_w, window_h))
    pygame.display.set_caption(TITLE)

    logger.info(
        "Window %dx%d — arrow keys / WASD to move, ESC to pause",
        window_w, window_h,
    )

    try:
        game = Game(config, screen)
        game.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception:
        logger.exception("Unexpected error")
    finally:
        pygame.quit()

    sys.exit(0)


if __name__ == "__main__":
    main()
