"""pac-man.py — Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py <config.json>
"""

import logging
import sys

import pygame

from src.config.loader import load_config
from src.maze.loader import generate_maze
from src.ui.renderer import Renderer

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────

WINDOW_W: int = 900
WINDOW_H: int = 700
HUD_W: int = 200
TILE_SIZE: int = 32
FPS: int = 60
TITLE: str = "Pac-Man"


def main() -> None:
    """Parse arguments, load config, open window, run game loop."""
    # ── Args ────────────────────────────────────────────────────────────────
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]

    if not config_path.endswith(".json"):
        print(f"Error: '{config_path}' is not a .json file")
        sys.exit(1)

    # ── Config ──────────────────────────────────────────────────────────────
    config = load_config(config_path)
    logger.info(
        "Config loaded — %d levels, %d lives",
        len(config["levels"]),
        config["lives"],
    )

    # ── Maze (level 1, fixed seed) ──────────────────────────────────────────
    level_cfg = config["levels"][0]
    try:
        grid = generate_maze(
            width=level_cfg["width"],
            height=level_cfg["height"],
            seed=level_cfg["seed"],
        )
    except RuntimeError as e:
        logger.error("Failed to generate maze: %s", e)
        sys.exit(1)

    maze_rows = len(grid)
    maze_cols = len(grid[0])

    # ── Pygame init ─────────────────────────────────────────────────────────
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    renderer = Renderer(
        screen=screen,
        maze_cols=maze_cols,
        maze_rows=maze_rows,
        tile_size=TILE_SIZE,
        hud_width=HUD_W,
    )

    logger.info("Window opened — ESC to quit")

    # ── Placeholder game state (will be replaced in Phase 2+) ────────────────
    score: int = 0
    lives: int = config["lives"]
    level: int = 1
    time_left: float = float(config["level_max_time"])

    # ── Game loop ───────────────────────────────────────────────────────────
    running: bool = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # delta time in seconds

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Countdown timer (placeholder behaviour)
        time_left = max(0.0, time_left - dt)

        # Draw
        renderer.clear()
        renderer.draw_maze(grid)
        renderer.draw_hud(
            score=score,
            lives=lives,
            level=level,
            time_left=time_left,
        )
        renderer.draw_debug_overlay(clock.get_fps())

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
