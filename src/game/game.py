"""src/game/game.py — Core game class with state machine.

Manages the complete game lifecycle: main menu, gameplay, pause,
game over, and victory screens.  All game logic is coordinated here.
"""

import logging
from enum import Enum, auto
from typing import Any, Optional

import pygame

from src.game.level import Level
from src.game.scoring import Scoring
from src.maze.loader import get_center, get_corners
from src.entities.player import Player
from src.entities.ghost import Ghost, GhostState
from src.ui.renderer import Renderer

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────

HUD_W: int = 200
TILE_SIZE: int = 32
FPS: int = 60
GHOST_COLOURS: list[str] = ["red", "pink", "cyan", "orange"]


class GameState(Enum):
    """Possible states for the game state machine."""

    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Game:
    """Core game class — owns all game objects and the main loop.

    Uses an explicit state machine (GameState) to route events,
    updates, and drawing to the correct handler.

    Args:
        config: Validated configuration dictionary.
        screen: Pygame display surface.
    """

    def __init__(
        self,
        config: dict[str, Any],
        screen: pygame.Surface,
    ) -> None:
        """Initialise game objects, fonts, and start at the main menu."""
        self._config = config
        self._screen = screen
        self._clock = pygame.time.Clock()
        self._state = GameState.MAIN_MENU
        self._running: bool = True

        # Fonts
        self._font_large = pygame.font.SysFont(
            "monospace", 48, bold=True,
        )
        self._font_med = pygame.font.SysFont(
            "monospace", 28, bold=True,
        )
        self._font_small = pygame.font.SysFont("monospace", 18)

        # Scoring (re-created on each new game)
        self._scoring = Scoring(
            points_per_pacgum=config["points_per_pacgum"],
            points_per_super_pacgum=config["points_per_super_pacgum"],
            points_per_ghost=config["points_per_ghost"],
        )

        # Level state
        self._level_idx: int = 0
        self._level: Optional[Level] = None
        self._player: Optional[Player] = None
        self._ghosts: list[Ghost] = []
        self._renderer: Optional[Renderer] = None

        # Animation counters
        self._anim_timer: float = 0.0
        self._anim_frame: int = 0
        self._death_frame: int = 0
        self._coin_frame: int = 0
        self._coin_timer: float = 0.0

        # Respawn tracking
        self._was_dying: bool = False

        # Menu navigation
        self._menu_sel: int = 0
        self._pause_sel: int = 0

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def state(self) -> GameState:
        """Current game state."""
        return self._state

    # ── Main loop ───────────────────────────────────────────────────────

    def run(self) -> None:
        """Run the main loop until the player quits."""
        logger.info("Game started — main menu")
        while self._running:
            dt = self._clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ── Event routing ───────────────────────────────────────────────────

    def _handle_events(self) -> None:
        """Poll pygame events and route to the active state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key: int) -> None:
        """Route a single keypress to the current state handler.

        Args:
            key: pygame key constant.
        """
        handler = {
            GameState.MAIN_MENU: self._key_menu,
            GameState.PLAYING: self._key_playing,
            GameState.PAUSED: self._key_pause,
            GameState.GAME_OVER: self._key_endscreen,
            GameState.VICTORY: self._key_endscreen,
        }.get(self._state)
        if handler:
            handler(key)

    # ── Key handlers ────────────────────────────────────────────────────

    def _key_menu(self, key: int) -> None:
        """Handle main-menu navigation.

        Args:
            key: pygame key constant.
        """
        if key in (pygame.K_UP, pygame.K_w):
            self._menu_sel = max(0, self._menu_sel - 1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._menu_sel = min(1, self._menu_sel + 1)
        elif key == pygame.K_RETURN:
            if self._menu_sel == 0:
                self._start_game()
            else:
                self._running = False
        elif key == pygame.K_ESCAPE:
            self._running = False

    def _key_playing(self, key: int) -> None:
        """Handle gameplay keypresses (movement + pause).

        Args:
            key: pygame key constant.
        """
        if key in (pygame.K_ESCAPE, pygame.K_p):
            self._state = GameState.PAUSED
            self._pause_sel = 0
            logger.info("Game paused")
        elif self._player is not None:
            self._player.handle_keydown(key)

    def _key_pause(self, key: int) -> None:
        """Handle pause-menu navigation.

        Args:
            key: pygame key constant.
        """
        if key in (pygame.K_ESCAPE, pygame.K_p):
            self._state = GameState.PLAYING
            logger.info("Game resumed")
        elif key in (pygame.K_UP, pygame.K_w):
            self._pause_sel = max(0, self._pause_sel - 1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._pause_sel = min(1, self._pause_sel + 1)
        elif key == pygame.K_RETURN:
            if self._pause_sel == 0:
                self._state = GameState.PLAYING
                logger.info("Game resumed")
            else:
                self._state = GameState.MAIN_MENU
                self._menu_sel = 0
                logger.info("Returned to main menu")

    def _key_endscreen(self, key: int) -> None:
        """Handle game-over / victory screen (any key → menu).

        Args:
            key: pygame key constant.
        """
        if key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self._state = GameState.MAIN_MENU
            self._menu_sel = 0

    # ── State transitions ───────────────────────────────────────────────

    def _start_game(self) -> None:
        """Begin a new game from level 1."""
        self._level_idx = 0
        self._scoring = Scoring(
            points_per_pacgum=self._config["points_per_pacgum"],
            points_per_super_pacgum=self._config[
                "points_per_super_pacgum"
            ],
            points_per_ghost=self._config["points_per_ghost"],
        )
        self._was_dying = False
        self._load_level(0, self._config["lives"])
        self._state = GameState.PLAYING
        logger.info("New game started — level 1")

    def _load_level(self, idx: int, lives: int) -> None:
        """Generate maze, spawn entities, create renderer for a level.

        Args:
            idx:   Zero-based level index.
            lives: Current life count for the player.
        """
        lvl_cfg = self._config["levels"][idx]
        self._level = Level(
            cfg=lvl_cfg,
            points_per_pacgum=self._config["points_per_pacgum"],
            points_per_super_pacgum=self._config[
                "points_per_super_pacgum"
            ],
            max_time=float(self._config["level_max_time"]),
        )
        center_r, center_c = get_center(self._level.grid)
        self._player = Player(
            start_row=center_r,
            start_col=center_c,
            lives=lives,
        )
        self._ghosts = self._make_ghosts(self._level.grid)

        maze_rows = len(self._level.grid)
        maze_cols = len(self._level.grid[0])
        self._renderer = Renderer(
            screen=self._screen,
            maze_cols=maze_cols,
            maze_rows=maze_rows,
            tile_size=TILE_SIZE,
            hud_width=HUD_W,
        )

        # Reset animation state
        self._anim_timer = 0.0
        self._anim_frame = 0
        self._death_frame = 0
        self._coin_frame = 0
        self._coin_timer = 0.0
        self._was_dying = False

        logger.info(
            "Level %d loaded — %d pellets, seed=%s",
            idx + 1, len(self._level.pellets), lvl_cfg["seed"],
        )

    def _make_ghosts(
        self, grid: list[list[int]],
    ) -> list[Ghost]:
        """Spawn 4 ghosts, one per corner of the maze.

        Args:
            grid: Maze grid (corners read from it).

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
                    move_speed=3.5,
                    edible_duration=float(
                        self._config["ghost_edible_duration"]
                    ),
                    respawn_delay=float(
                        self._config["ghost_respawn_delay"]
                    ),
                )
            )
        return ghosts

    # ── Update routing ──────────────────────────────────────────────────

    def _update(self, dt: float) -> None:
        """Route update to the current state handler.

        Args:
            dt: Delta time in seconds since last frame.
        """
        if self._state == GameState.PLAYING:
            self._update_playing(dt)

    # ── Gameplay update ─────────────────────────────────────────────────

    def _update_playing(self, dt: float) -> None:
        """Update gameplay: movement, collisions, transitions.

        Args:
            dt: Delta time in seconds.
        """
        level = self._level
        player = self._player
        if level is None or player is None:
            return

        # ── Respawn after death animation ────────────────────────────
        if self._was_dying and not player.is_dying:
            self._was_dying = False
            if player.alive:
                player.respawn()
                for g in self._ghosts:
                    g.reset()
                logger.info(
                    "Player respawned. Lives: %d", player.lives,
                )
            return  # skip one frame after respawn

        if player.is_dying:
            self._was_dying = True

        # ── Entity updates ───────────────────────────────────────────
        level.update(dt)
        player.update(dt, level.grid)
        for ghost in self._ghosts:
            ghost.update(dt, level.grid, player.row, player.col)

        # ── Collisions ───────────────────────────────────────────────
        if not player.is_dying:
            self._collide_pellets()
            self._collide_ghosts()

        # ── Transitions ──────────────────────────────────────────────
        if not player.alive:
            self._state = GameState.GAME_OVER
            logger.info(
                "Game Over. Score: %d", self._scoring.score,
            )
        elif level.complete:
            self._advance_level()
        elif level.time_expired:
            self._handle_timeout()

        # ── Animation ────────────────────────────────────────────────
        self._tick_animation(dt)

    def _collide_pellets(self) -> None:
        """Check and handle pellet eating."""
        player = self._player
        level = self._level
        if player is None or level is None:
            return
        if player.progress < 1.0:
            return

        pr, pc = player.row, player.col

        pellet = level.get_pellet_at(pr, pc)
        if pellet:
            pellet.eat()
            self._scoring.eat_pacgum()

        super_p = level.get_super_pellet_at(pr, pc)
        if super_p:
            super_p.eat()
            self._scoring.eat_super_pacgum()
            for g in self._ghosts:
                g.make_edible()

    def _collide_ghosts(self) -> None:
        """Check and handle ghost-player collisions."""
        player = self._player
        if player is None:
            return

        for ghost in self._ghosts:
            if ghost.eaten:
                continue
            same_tile = (
                ghost.row == player.row
                and ghost.col == player.col
            )
            if not same_tile:
                continue
            if ghost.edible:
                ghost.be_eaten()
                self._scoring.eat_ghost()
                logger.info(
                    "Ghost eaten! Score: %d",
                    self._scoring.score,
                )
            else:
                player.die()
                self._scoring.reset_ghost_combo()
                logger.info(
                    "Player hit! Lives: %d", player.lives,
                )
                break

    def _advance_level(self) -> None:
        """Move to the next level, or trigger victory."""
        self._level_idx += 1
        if self._level_idx >= len(self._config["levels"]):
            self._state = GameState.VICTORY
            logger.info(
                "All levels complete! Score: %d",
                self._scoring.score,
            )
        else:
            lives = 0
            if self._player is not None:
                lives = self._player.lives
            logger.info(
                "Level complete! Loading level %d…",
                self._level_idx + 1,
            )
            self._load_level(self._level_idx, lives)

    def _handle_timeout(self) -> None:
        """Handle level timer expiry — lose a life."""
        player = self._player
        if player is None:
            return
        logger.info("Time up! Losing a life.")
        player.die()
        if not player.alive:
            self._state = GameState.GAME_OVER
            logger.info("Game Over — no lives left.")
        else:
            self._load_level(self._level_idx, player.lives)

    def _tick_animation(self, dt: float) -> None:
        """Advance animation frame counters.

        Args:
            dt: Delta time in seconds.
        """
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / 8:
            self._anim_timer = 0.0
            self._anim_frame = (self._anim_frame + 1) % 3
            if self._player and self._player.is_dying:
                self._death_frame = min(
                    self._death_frame + 1, 3,
                )
            else:
                self._death_frame = 0

        self._coin_timer += dt
        if self._coin_timer >= 1.0 / 12:
            self._coin_timer = 0.0
            self._coin_frame = (self._coin_frame + 1) % 8

    # ── Draw routing ────────────────────────────────────────────────────

    def _draw(self) -> None:
        """Route drawing to the current state handler."""
        if self._state == GameState.MAIN_MENU:
            self._draw_menu()
        elif self._state == GameState.PLAYING:
            self._draw_game()
        elif self._state == GameState.PAUSED:
            self._draw_game()
            self._draw_pause()
        elif self._state == GameState.GAME_OVER:
            self._draw_end("GAME OVER", (220, 50, 50))
        elif self._state == GameState.VICTORY:
            self._draw_end("YOU WIN!", (50, 220, 50))

    # ── Gameplay drawing ────────────────────────────────────────────────

    def _draw_game(self) -> None:
        """Draw the active gameplay frame."""
        rdr = self._renderer
        level = self._level
        player = self._player
        if rdr is None or level is None or player is None:
            return

        rdr.clear()
        rdr.draw_maze(level.grid)

        # Pellets
        for p in level.pellets:
            if not p.eaten:
                rdr.draw_pacgum(p.row, p.col, self._coin_frame)
        for sp in level.super_pellets:
            if not sp.eaten:
                rdr.draw_super_pacgum(
                    sp.row, sp.col, self._coin_frame,
                    visible=sp.visible,
                )

        # Ghosts (eaten at spawn are hidden)
        for ghost in sorted(
            self._ghosts, key=lambda g: g.eaten, reverse=True,
        ):
            if ghost.state == GhostState.EATEN:
                at_spawn = (
                    ghost.row == ghost.spawn_row
                    and ghost.col == ghost.spawn_col
                )
                if at_spawn:
                    continue
            rdr.draw_ghost(
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
        rdr.draw_player(
            row=player.row,
            col=player.col,
            prev_row=player.prev_row,
            prev_col=player.prev_col,
            progress=player.progress,
            direction=player.direction,
            anim_frame=self._anim_frame,
            is_dying=player.is_dying,
            death_frame=self._death_frame,
        )

        rdr.draw_hud(
            score=self._scoring.score,
            lives=player.lives,
            level=self._level_idx + 1,
            time_left=level.time_left,
        )
        rdr.draw_debug_overlay(self._clock.get_fps())

    # ── Menu / overlay drawing ──────────────────────────────────────────

    def _draw_menu(self) -> None:
        """Draw the main menu (placeholder — Phase 2 will polish)."""
        self._screen.fill((0, 0, 40))
        sw, sh = self._screen.get_size()
        cx = sw // 2

        title = self._font_large.render(
            "PAC-MAN", True, (255, 220, 0),
        )
        self._screen.blit(
            title, title.get_rect(center=(cx, sh // 4)),
        )

        opts = ["Start Game", "Exit"]
        for i, label in enumerate(opts):
            sel = i == self._menu_sel
            clr = (255, 255, 255) if sel else (120, 120, 120)
            pfx = "> " if sel else "  "
            surf = self._font_med.render(
                f"{pfx}{label}", True, clr,
            )
            self._screen.blit(
                surf, surf.get_rect(
                    center=(cx, sh // 2 + i * 50),
                ),
            )

        hint = self._font_small.render(
            "Arrow keys to select, ENTER to confirm",
            True, (100, 100, 100),
        )
        self._screen.blit(
            hint, hint.get_rect(center=(cx, sh - 60)),
        )

    def _draw_pause(self) -> None:
        """Draw semi-transparent pause overlay on top of the game."""
        sw, sh = self._screen.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self._screen.blit(overlay, (0, 0))

        cx = sw // 2
        title = self._font_large.render(
            "PAUSED", True, (255, 220, 0),
        )
        self._screen.blit(
            title, title.get_rect(center=(cx, sh // 3)),
        )

        opts = ["Resume", "Main Menu"]
        for i, label in enumerate(opts):
            sel = i == self._pause_sel
            clr = (255, 255, 255) if sel else (120, 120, 120)
            pfx = "> " if sel else "  "
            surf = self._font_med.render(
                f"{pfx}{label}", True, clr,
            )
            self._screen.blit(
                surf, surf.get_rect(
                    center=(cx, sh // 2 + i * 50),
                ),
            )

    def _draw_end(
        self,
        title_text: str,
        colour: tuple[int, int, int],
    ) -> None:
        """Draw game-over or victory screen.

        Args:
            title_text: Main heading text.
            colour:     Colour for the heading.
        """
        self._screen.fill((0, 0, 40))
        sw, sh = self._screen.get_size()
        cx = sw // 2

        title = self._font_large.render(
            title_text, True, colour,
        )
        self._screen.blit(
            title, title.get_rect(center=(cx, sh // 3)),
        )

        score = self._font_med.render(
            f"Score: {self._scoring.score}",
            True, (255, 255, 255),
        )
        self._screen.blit(
            score, score.get_rect(center=(cx, sh // 2)),
        )

        hint = self._font_small.render(
            "Press ENTER to return to menu",
            True, (150, 150, 150),
        )
        self._screen.blit(
            hint, hint.get_rect(center=(cx, sh * 2 // 3)),
        )
