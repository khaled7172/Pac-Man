"""pac-man.py — Entry point for the Pac-Man game.

Usage:
    python3 pac-man.py <config.json>
"""

import logging
import sys

import pygame

from src.config.loader import load_config
from src.game.level import Level
from src.game.scoring import Scoring
from src.maze.loader import get_center, get_corners
from src.entities.player import Player
from src.entities.ghost import Ghost, GhostState
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

GHOST_COLOURS: list[str] = ["red", "pink", "cyan", "orange"]


def make_ghosts(
    grid: list[list[int]],
    move_speed: float,
    edible_duration: float,
    respawn_delay: float,
) -> list[Ghost]:
    """Spawn 4 ghosts, one per corner.

    Args:
        grid:             Maze grid (used to read corner positions).
        move_speed:       Base tiles-per-second for ghosts.
        edible_duration:  Seconds ghosts stay edible after power pellet.
        respawn_delay:    Seconds before eaten ghost respawns.

    Returns:
        List of 4 Ghost instances.
    """
    corners = get_corners(grid)
    ghosts: list[Ghost] = []
    for i, (r, c) in enumerate(corners):
        colour = GHOST_COLOURS[i % len(GHOST_COLOURS)]
        ghosts.append(
            Ghost(
                spawn_row=r,
                spawn_col=c,
                colour=colour,
                move_speed=move_speed,
                edible_duration=edible_duration,
                respawn_delay=respawn_delay,
            )
        )
    return ghosts


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

    # ── Pygame init ─────────────────────────────────────────────────────────
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # ── Game state ──────────────────────────────────────────────────────────
    level_index: int = 0
    total_lives: int = config["lives"]
    scoring = Scoring(
        points_per_pacgum=config["points_per_pacgum"],
        points_per_super_pacgum=config["points_per_super_pacgum"],
        points_per_ghost=config["points_per_ghost"],
    )

    def load_level(idx: int, lives: int) -> tuple[Level, Player, list[Ghost], Renderer]:
        """Load level idx and return all game objects.

        Args:
            idx:   Zero-based level index.
            lives: Current life count to give the new Player.

        Returns:
            Tuple of (Level, Player, ghosts, Renderer).
        """
        lvl_cfg = config["levels"][idx]
        lvl = Level(
            cfg=lvl_cfg,
            points_per_pacgum=config["points_per_pacgum"],
            points_per_super_pacgum=config["points_per_super_pacgum"],
            max_time=float(config["level_max_time"]),
        )
        center_row, center_col = get_center(lvl.grid)
        plr = Player(
            start_row=center_row,
            start_col=center_col,
            lives=lives,
        )
        ghosts = make_ghosts(
            grid=lvl.grid,
            move_speed=3.5,
            edible_duration=float(config["ghost_edible_duration"]),
            respawn_delay=float(config["ghost_respawn_delay"]),
        )
        maze_rows = len(lvl.grid)
        maze_cols = len(lvl.grid[0])
        rdr = Renderer(
            screen=screen,
            maze_cols=maze_cols,
            maze_rows=maze_rows,
            tile_size=TILE_SIZE,
            hud_width=HUD_W,
        )
        logger.info(
            "Level %d loaded — %d pellets, seed=%s",
            idx + 1, len(lvl.pellets), lvl_cfg["seed"],
        )
        return lvl, plr, ghosts, rdr

    level, player, ghosts, renderer = load_level(level_index, total_lives)

    # Animation counters
    anim_timer: float = 0.0
    anim_frame: int = 0
    death_frame: int = 0
    coin_frame: int = 0
    coin_timer: float = 0.0

    logger.info("Window opened — arrow keys / WASD to move, ESC to quit")

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
        level.update(dt)
        player.update(dt, level.grid)

        for ghost in ghosts:
            ghost.update(dt, level.grid, player.row, player.col)

        # ── Collisions ───────────────────────────────────────────────────────
        if not player.is_dying:
            # Pellet collision (only when fully on a tile)
            if player.progress >= 1.0:
                pr, pc = player.row, player.col

                pellet = level.get_pellet_at(pr, pc)
                if pellet:
                    pellet.eat()
                    scoring.eat_pacgum()

                super_p = level.get_super_pellet_at(pr, pc)
                if super_p:
                    super_p.eat()
                    scoring.eat_super_pacgum()
                    for g in ghosts:
                        g.make_edible()

            # Ghost collision
            for ghost in ghosts:
                if ghost.eaten:
                    continue
                # Close enough to collide (same tile)
                if ghost.row == player.row and ghost.col == player.col:
                    if ghost.edible:
                        ghost.be_eaten()
                        scoring.eat_ghost()
                        logger.info("Ghost eaten! Score: %d", scoring.score)
                    else:
                        # Ghost kills Pac-Man
                        player.die()
                        scoring.reset_ghost_combo()
                        logger.info(
                            "Player hit by ghost! Lives: %d", player.lives
                        )
                        break

        # ── Level / game-over transitions ─────────────────────────────────────
        if not player.alive:
            logger.info("Game Over.")
            running = False

        elif level.complete:
            level_index += 1
            if level_index >= len(config["levels"]):
                logger.info("All levels complete — YOU WIN! Score: %d", scoring.score)
                running = False
            else:
                logger.info("Level complete! Loading level %d…", level_index + 1)
                level, player, ghosts, renderer = load_level(
                    level_index, player.lives
                )

        elif level.time_expired:
            logger.info("Time up! Losing a life.")
            player.die()
            if not player.alive:
                logger.info("Game Over — no lives left.")
                running = False
            else:
                # Restart same level
                level, player, ghosts, renderer = load_level(
                    level_index, player.lives
                )

        elif not player.is_dying and player.lives < total_lives:
            # Mid-level respawn after death animation finishes
            if not player.is_dying:
                pass   # player.respawn() called internally

        # ── Animation frames ─────────────────────────────────────────────────
        anim_timer += dt
        if anim_timer >= 1.0 / 8:
            anim_timer = 0.0
            anim_frame = (anim_frame + 1) % 3
            if player.is_dying:
                death_frame = min(death_frame + 1, 3)
            else:
                death_frame = 0

        coin_timer += dt
        if coin_timer >= 1.0 / 12:
            coin_timer = 0.0
            coin_frame = (coin_frame + 1) % 8

        # ── Draw ─────────────────────────────────────────────────────────────
        renderer.clear()
        renderer.draw_maze(level.grid)

        # Pellets
        for p in level.pellets:
            if not p.eaten:
                renderer.draw_pacgum(p.row, p.col, coin_frame)

        for sp in level.super_pellets:
            if not sp.eaten:
                renderer.draw_super_pacgum(sp.row, sp.col, coin_frame,
                                           visible=sp.visible)

        # Ghosts (draw eaten ones beneath others)
        for ghost in sorted(ghosts, key=lambda g: g.eaten, reverse=True):
            if ghost.state != GhostState.EATEN or \
               (ghost.row != ghost._spawn_row or ghost.col != ghost._spawn_col):
                renderer.draw_ghost(
                    row=ghost.row,
                    col=ghost.col,
                    prev_row=ghost.prev_row,
                    prev_col=ghost.prev_col,
                    progress=ghost.progress,
                    colour=ghost.colour,
                    anim_frame=ghost.anim_frame,
                    edible=ghost.edible,
                    flash=ghost.flashing,
                )

        # Player
        renderer.draw_player(
            row=player.row,
            col=player.col,
            prev_row=player.prev_row,
            prev_col=player.prev_col,
            progress=player.progress,
            direction=player.direction,
            anim_frame=anim_frame,
            is_dying=player.is_dying,
            death_frame=death_frame,
        )

        renderer.draw_hud(
            score=scoring.score,
            lives=player.lives,
            level=level_index + 1,
            time_left=level.time_left,
        )
        renderer.draw_debug_overlay(clock.get_fps())

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
