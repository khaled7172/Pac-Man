# game.py — main game loop and state machine

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Any, Optional

import pygame

from src.game.level import Level
from src.game.scoring import Scoring
from src.game.cheats import CheatManager
from src.highscore.manager import HighscoreManager
from src.maze.loader import get_center, get_corners
from src.entities.player import Player
from src.entities.ghost import Ghost
from src.ui.renderer import Renderer
from src.ui.menu import MenuRenderer

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

HUD_W = 200
TILE_SIZE = 32
FPS = 60
GHOST_COLOURS = ["red", "pink", "cyan", "orange"]
HIGHSCORE_FILE = "highscores.json"

_CURSOR_BLINK = 0.5  # cursor blink speed for name entry


class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    VIEW_HIGHSCORES = auto()
    INSTRUCTIONS = auto()


class Game:
    """Owns all game objects + the main loop."""

    def __init__(
        self,
        config: dict[str, Any],
        screen: pygame.Surface,
    ) -> None:
        self._config = config
        self._screen = screen
        self._clock = pygame.time.Clock()
        self._state = GameState.MAIN_MENU
        self._running: bool = True

        # Sub-systems
        self._menu = MenuRenderer()
        self._cheats = CheatManager()
        hs_file = str(config.get("highscore_filename", HIGHSCORE_FILE))
        self._highscores = HighscoreManager(hs_file)

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

        # Name entry for highscore
        self._name_buffer: str = ""
        self._cursor_timer: float = 0.0
        self._cursor_visible: bool = True
        self._entry_score: int = 0   # score to submit after name entry
        self._awaiting_name: bool = False   # True during name-entry phase

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def state(self) -> GameState:
        return self._state

    # ── Main loop ────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Run the main loop until the player quits."""
        logger.info("Game started — main menu")
        while self._running:
            dt = self._clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    # ── Event routing ────────────────────────────────────────────────────────

    def _handle_events(self) -> None:
        """Poll pygame events and route to the active state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key, event.unicode)

    def _on_key(self, key: int, unicode_char: str = "") -> None:
        handler = {
            GameState.MAIN_MENU: self._key_menu,
            GameState.PLAYING: self._key_playing,
            GameState.PAUSED: self._key_pause,
            GameState.GAME_OVER: self._key_endscreen,
            GameState.VICTORY: self._key_endscreen,
            GameState.VIEW_HIGHSCORES: self._key_back,
            GameState.INSTRUCTIONS: self._key_back,
        }.get(self._state)
        if handler:
            handler(key, unicode_char)

    # ── Key handlers ─────────────────────────────────────────────────────────

    def _key_menu(self, key: int, _unicode: str = "") -> None:
        num_options = 4  # Start, Highscores, Instructions, Exit
        if key in (pygame.K_UP, pygame.K_w):
            self._menu_sel = (self._menu_sel - 1) % num_options
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._menu_sel = (self._menu_sel + 1) % num_options
        elif key == pygame.K_RETURN:
            if self._menu_sel == 0:
                self._start_game()
            elif self._menu_sel == 1:
                self._state = GameState.VIEW_HIGHSCORES
                logger.info("Viewing highscores")
            elif self._menu_sel == 2:
                self._state = GameState.INSTRUCTIONS
                logger.info("Viewing instructions")
            else:
                self._running = False
        elif key == pygame.K_ESCAPE:
            self._running = False

    def _key_playing(self, key: int, _unicode: str = "") -> None:
        if key in (pygame.K_ESCAPE, pygame.K_p):
            self._state = GameState.PAUSED
            self._pause_sel = 0
            logger.info("Game paused")
            return

        # Try cheat keys first
        cheat_name = self._cheats.handle_key(key, self)
        if cheat_name is not None:
            return

        # Otherwise forward to player
        if self._player is not None:
            self._player.handle_keydown(key)

    def _key_pause(self, key: int, _unicode: str = "") -> None:
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

    def _key_endscreen(self, key: int, unicode_char: str = "") -> None:
        # name entry if score qualifies
        if self._awaiting_name:
            if key == pygame.K_RETURN:
                self._submit_name()
            elif key == pygame.K_BACKSPACE:
                self._name_buffer = self._name_buffer[:-1]
            elif (
                (unicode_char.isalnum() or unicode_char == " ")
                and len(self._name_buffer) < 10
            ):
                self._name_buffer += unicode_char
        else:
            if key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self._state = GameState.MAIN_MENU
                self._menu_sel = 0

    def _key_back(self, key: int, _unicode: str = "") -> None:
        if key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self._state = GameState.MAIN_MENU
            self._menu_sel = 0

    # ── State transitions ─────────────────────────────────────────────────────

    def _start_game(self) -> None:
        """Begin a new game from level 1."""
        self._level_idx = 0
        self._scoring = Scoring(
            points_per_pacgum=self._config["points_per_pacgum"],
            points_per_super_pacgum=self._config["points_per_super_pacgum"],
            points_per_ghost=self._config["points_per_ghost"],
        )
        self._was_dying = False
        self._cheats.reset()
        self._load_level(0, self._config["lives"])
        self._state = GameState.PLAYING
        logger.info("New game started — level 1")

    def _load_level(self, idx: int, lives: int) -> None:
        lvl_cfg = self._config["levels"][idx]
        self._level = Level(
            cfg=lvl_cfg,
            points_per_pacgum=self._config["points_per_pacgum"],
            points_per_super_pacgum=self._config["points_per_super_pacgum"],
            max_time=float(self._config["level_max_time"]),
        )
        center_r, center_c = get_center(self._level.grid)
        self._player = Player(
            start_row=center_r,
            start_col=center_c,
            lives=lives,
        )

        # Apply speed boost if cheat is active
        if self._cheats.speed_boost:
            self._player._speed = CheatManager._BOOST_SPEED

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

    def _make_ghosts(self, grid: list[list[int]]) -> list[Ghost]:
        corners = get_corners(grid)
        # faster but still beatable
        speed_map = {
            'red': 2.5, 'pink': 2.2,
            'cyan': 2.0, 'orange': 1.8,
        }
        ghosts: list[Ghost] = []
        for i, (r, c) in enumerate(corners):
            colour = GHOST_COLOURS[i % len(GHOST_COLOURS)]
            ghosts.append(
                Ghost(
                    spawn_row=r,
                    spawn_col=c,
                    colour=colour,
                    move_speed=speed_map.get(colour, 1.8),
                    edible_duration=float(
                        self._config["ghost_edible_duration"]
                    ),
                    respawn_delay=float(
                        self._config["ghost_respawn_delay"]
                    ),
                )
            )
        return ghosts

    def _enter_end_state(self, state: GameState) -> None:
        self._state = state
        self._entry_score = self._scoring.score
        self._name_buffer = ""
        self._cursor_timer = 0.0
        self._cursor_visible = True
        self._awaiting_name = self._highscores.is_high_score(
            self._entry_score
        )
        logger.info(
            "%s — score: %d, high score: %s",
            state.name, self._entry_score, self._awaiting_name,
        )

    def _submit_name(self) -> None:
        """Submit the typed name to the highscore table and return to menu."""
        name = self._name_buffer.strip() or "PLAYER"
        added = self._highscores.add_score(name, self._entry_score)
        logger.info(
            "Name submitted: %r  score: %d  added: %s",
            name, self._entry_score, added,
        )
        self._state = GameState.MAIN_MENU
        self._menu_sel = 0

    # ── Update routing ────────────────────────────────────────────────────────

    def _update(self, dt: float) -> None:
        self._menu.update(dt)

        if self._state == GameState.PLAYING:
            self._update_playing(dt)
        elif self._state in (GameState.GAME_OVER, GameState.VICTORY):
            self._update_endscreen(dt)

    # ── Gameplay update ───────────────────────────────────────────────────────

    def _update_playing(self, dt: float) -> None:
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
                level.time_left = level._max_time
                logger.info(
                    "Player respawned. Lives: %d", player.lives,
                )
            return  # skip one frame after respawn

        if player.is_dying:
            self._was_dying = True

        # ── Entity updates ───────────────────────────────────────────
        level.update(dt)
        player.update(dt, level.grid)
        # freeze ghosts during death AND for the frame the anim just ended
        if not player.is_dying and not self._was_dying:
            for ghost in self._ghosts:
                if self._cheats.ghost_freeze and not ghost.eaten:
                    continue
                ghost.update(dt, level.grid, player.row, player.col)

        # ── Collisions ───────────────────────────────────────────────
        # skip collisions while dying OR the frame death anim just ended
        if not player.is_dying and not self._was_dying:
            self._collide_pellets()
            self._collide_ghosts()

        # ── Transitions ──────────────────────────────────────────────
        if not player.alive:
            self._enter_end_state(GameState.GAME_OVER)
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

            p_r = player.prev_row + (player.row - player.prev_row) * player.progress
            p_c = player.prev_col + (player.col - player.prev_col) * player.progress
            g_r = ghost.prev_row + (ghost.row - ghost.prev_row) * ghost.progress
            g_c = ghost.prev_col + (ghost.col - ghost.prev_col) * ghost.progress

            dist = abs(p_r - g_r) + abs(p_c - g_c)
            if dist > 0.8:
                continue

            if ghost.edible:
                ghost.be_eaten()
                self._scoring.eat_ghost()
                logger.info(
                    "Ghost eaten! Score: %d", self._scoring.score,
                )
            elif (not self._cheats.invincible
                  and not player.invincible_grace):
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
            self._enter_end_state(GameState.VICTORY)
        else:
            lives = 0
            if self._player is not None:
                lives = self._player.lives
            logger.info(
                "Level complete! Loading level %d…", self._level_idx + 1,
            )
            self._load_level(self._level_idx, lives)

    def _handle_timeout(self) -> None:
        """Handle level timer expiry — lose a life."""
        player = self._player
        if player is None or player.is_dying or self._level is None:
            return
        logger.info("Time up! Losing a life.")
        if not self._cheats.invincible:
            player.die()
        self._level.time_left = self._level._max_time

    def _tick_animation(self, dt: float) -> None:
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / 8:
            self._anim_timer = 0.0
            self._anim_frame = (self._anim_frame + 1) % 3
            if self._player and self._player.is_dying:
                self._death_frame = min(self._death_frame + 1, 3)
            else:
                self._death_frame = 0

        self._coin_timer += dt
        if self._coin_timer >= 1.0 / 12:
            self._coin_timer = 0.0
            self._coin_frame = (self._coin_frame + 1) % 8

    def _update_endscreen(self, dt: float) -> None:
        # blink cursor for name entry
        if not self._awaiting_name:
            return
        self._cursor_timer += dt
        if self._cursor_timer >= _CURSOR_BLINK:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

    # ── Draw routing ──────────────────────────────────────────────────────────

    def _draw(self) -> None:
        """Route drawing to the current state handler."""
        if self._state == GameState.MAIN_MENU:
            self._menu.draw_main_menu(self._screen, self._menu_sel)
        elif self._state == GameState.PLAYING:
            self._draw_game()
        elif self._state == GameState.PAUSED:
            self._draw_game()
            self._menu.draw_pause_menu(self._screen, self._pause_sel)
        elif self._state == GameState.GAME_OVER:
            self._menu.draw_game_over(
                self._screen,
                self._entry_score,
                self._name_buffer,
                self._cursor_visible,
                self._awaiting_name,
            )
        elif self._state == GameState.VICTORY:
            self._menu.draw_victory(
                self._screen,
                self._entry_score,
                self._name_buffer,
                self._cursor_visible,
                self._awaiting_name,
            )
        elif self._state == GameState.VIEW_HIGHSCORES:
            self._menu.draw_highscores(
                self._screen, self._highscores.get_top10(),
            )
        elif self._state == GameState.INSTRUCTIONS:
            self._menu.draw_instructions(self._screen)

    # ── Gameplay drawing ──────────────────────────────────────────────────────

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

        # Ghosts
        for ghost in sorted(
            self._ghosts, key=lambda g: g.eaten, reverse=True,
        ):
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
                eaten=ghost.eaten,
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
            cheats_active=self._cheats.active_cheats or None,
        )
        rdr.draw_debug_overlay(self._clock.get_fps())
