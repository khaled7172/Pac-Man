"""pac-man.py — Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py <config.json>
"""

import logging
import sys

import pygame

from src.config.loader import load_config
from src.maze.loader import generate_maze, get_center
from src.entities.player import Player
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
    center_row, center_col = get_center(grid)

    # ── Player ──────────────────────────────────────────────────────────────
    player = Player(
        start_row=center_row,
        start_col=center_col,
        lives=config["lives"],
    )

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

    logger.info("Window opened — arrow keys / WASD to move, ESC to quit")

    # ── Game state ──────────────────────────────────────────────────────────
    score: int = 0
    level: int = 1
    time_left: float = float(config["level_max_time"])

    # ── Game loop ───────────────────────────────────────────────────────────
    running: bool = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                player.handle_keydown(event.key)

        # ── Update ───────────────────────────────────────────────────────────
        player.update(dt, grid)

        # Handle death animation finishing — respawn
        if not player.alive:
            running = False   # game over (Phase 5 will handle this properly)
        elif not player.is_dying:
            pass   # normal play

        time_left = max(0.0, time_left - dt)

        # ── Draw ─────────────────────────────────────────────────────────────
        renderer.clear()
        renderer.draw_maze(grid)
        renderer.draw_player(
            row=player.row,
            col=player.col,
            prev_row=player.prev_row,
            prev_col=player.prev_col,
            progress=player.progress,
            direction=player.direction,
            mouth_angle=player.get_mouth_angle(),
            is_dying=player.is_dying,
            death_progress=0.0,
        )
        renderer.draw_hud(
            score=score,
            lives=player.lives,
            level=level,
            time_left=time_left,
        )
        renderer.draw_debug_overlay(clock.get_fps())

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
