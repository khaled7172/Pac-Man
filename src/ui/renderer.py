"""src/ui/renderer.py — All drawing logic for the Pac-Man game.

Uses sprite sheets from assets/sprites/ via sprite_loader.py.
Nothing here touches game state — it only reads and draws.
"""

import pygame
from typing import Optional

from src.ui.sprite_loader import (
    load_pacman_sprites,
    load_ghost_sprites,
    load_coin_sprites,
)

# ── Colours ─────────────────────────────────────────────────────────────

DARK_BLUE: tuple[int, int, int] = (0, 0, 40)
WALL_BLUE: tuple[int, int, int] = (33, 33, 222)
WALL_BORDER: tuple[int, int, int] = (50, 50, 255)
FLOOR: tuple[int, int, int] = (0, 0, 20)
YELLOW: tuple[int, int, int] = (255, 220, 0)
WHITE: tuple[int, int, int] = (255, 255, 255)
GREY: tuple[int, int, int] = (180, 180, 180)
RED: tuple[int, int, int] = (220, 50, 50)
HUD_BG: tuple[int, int, int] = (10, 10, 30)
HUD_TEXT: tuple[int, int, int] = (220, 220, 220)

# Bitmask wall constants
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8


class Renderer:
    """Handles all pygame drawing for the Pac-Man game.

    Args:
        screen:     The pygame Surface to draw on.
        maze_cols:  Number of columns in the maze grid.
        maze_rows:  Number of rows in the maze grid.
        tile_size:  Pixel size of each maze tile (default 32).
        hud_width:  Width of the HUD panel on the right (default 200).
        asset_root: Path to the assets directory.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        maze_cols: int,
        maze_rows: int,
        tile_size: int = 32,
        hud_width: int = 200,
        asset_root: str = "assets",
    ) -> None:
        """Initialise renderer and load all sprites."""
        self._screen = screen
        self._tile = tile_size
        self._hud_w = hud_width

        screen_w, screen_h = screen.get_size()
        play_w = screen_w - hud_width
        self._offset_x: int = (play_w - maze_cols * tile_size) // 2
        self._offset_y: int = (screen_h - maze_rows * tile_size) // 2

        # Fonts
        self._font_hud = pygame.font.SysFont("monospace", 20, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 14)
        self._font_title = pygame.font.SysFont("monospace", 28, bold=True)

        # Sprites
        self._pac = load_pacman_sprites(asset_root, tile_size)
        self._ghosts = load_ghost_sprites(asset_root, tile_size)
        self._coin = load_coin_sprites(asset_root, tile_size, big=False)
        self._bigcoin = load_coin_sprites(asset_root, tile_size, big=True)

    # ── Coordinate helpers ──────────────────────────────────────────────────

    def tile_rect(self, row: int, col: int) -> pygame.Rect:
        """Return pixel Rect for a grid tile.

        Args:
            row: Grid row index.
            col: Grid column index.

        Returns:
            pygame.Rect covering that tile on screen.
        """
        return pygame.Rect(
            self._offset_x + col * self._tile,
            self._offset_y + row * self._tile,
            self._tile, self._tile,
        )

    def tile_center(self, row: int, col: int) -> tuple[int, int]:
        """Return pixel centre of a grid tile.

        Args:
            row: Grid row index.
            col: Grid column index.

        Returns:
            (x, y) pixel centre coordinates.
        """
        r = self.tile_rect(row, col)
        return r.centerx, r.centery

    # ── Background ──────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Fill screen with background and draw HUD panel."""
        self._screen.fill(DARK_BLUE)
        sw, sh = self._screen.get_size()
        pygame.draw.rect(
            self._screen, HUD_BG,
            pygame.Rect(sw - self._hud_w, 0, self._hud_w, sh),
        )

    # ── Maze ────────────────────────────────────────────────────────────────

    def draw_maze(self, grid: list[list[int]]) -> None:
        """Draw the full maze grid.

        Args:
            grid: 2-D bitmask grid from src/maze/loader.py.
        """
        t = self._tile
        wt = max(2, t // 8)

        rows = len(grid)
        for row_idx, row in enumerate(grid):
            cols = len(row)
            for col_idx, cell in enumerate(row):
                rect = self.tile_rect(row_idx, col_idx)
                is_border = (
                    row_idx == 0 or row_idx == rows - 1
                    or col_idx == 0 or col_idx == cols - 1
                )
                if is_border or cell == 15:
                    pygame.draw.rect(self._screen, WALL_BLUE, rect)
                    pygame.draw.rect(self._screen, WALL_BORDER, rect, 1)
                    continue

                pygame.draw.rect(self._screen, FLOOR, rect)
                x, y = rect.x, rect.y
                # mazegenerator: bit SET = wall present, bit CLEAR = passage
                if cell & NORTH:
                    pygame.draw.line(self._screen, WALL_BLUE,
                                     (x, y), (x + t, y), wt)
                if cell & SOUTH:
                    pygame.draw.line(self._screen, WALL_BLUE,
                                     (x, y + t), (x + t, y + t), wt)
                if cell & EAST:
                    pygame.draw.line(self._screen, WALL_BLUE,
                                     (x + t, y), (x + t, y + t), wt)
                if cell & WEST:
                    pygame.draw.line(self._screen, WALL_BLUE,
                                     (x, y), (x, y + t), wt)

    # ── Player ──────────────────────────────────────────────────────────────

    def draw_player(
        self,
        row: int,
        col: int,
        prev_row: int,
        prev_col: int,
        progress: float,
        direction: str,
        anim_frame: int,
        is_dying: bool = False,
        death_frame: int = 0,
    ) -> None:
        """Draw Pac-Man with smooth inter-tile animation.

        Args:
            row:         Current tile row.
            col:         Current tile column.
            prev_row:    Previous tile row.
            prev_col:    Previous tile column.
            progress:    Animation progress 0.0->1.0 between tiles.
            direction:   Facing direction N/S/E/W.
            anim_frame:  Movement animation frame index (0-2).
            is_dying:    True if death animation is playing.
            death_frame: Death animation frame index (0-3).
        """
        cx0, cy0 = self.tile_center(prev_row, prev_col)
        cx1, cy1 = self.tile_center(row, col)
        px = int(cx0 + (cx1 - cx0) * progress)
        py = int(cy0 + (cy1 - cy0) * progress)

        if is_dying:
            frames = self._pac["death"]
            sprite = frames[min(death_frame, len(frames) - 1)]
        else:
            d = direction if direction in self._pac else "E"
            frames = self._pac[d]
            sprite = frames[anim_frame % len(frames)]

        rect = sprite.get_rect(center=(px, py))
        self._screen.blit(sprite, rect)

    # ── Ghosts ──────────────────────────────────────────────────────────────

    def draw_ghost(
        self,
        row: int,
        col: int,
        prev_row: int,
        prev_col: int,
        progress: float,
        colour: str,
        anim_frame: int,
        edible: bool = False,
        flash: bool = False,
    ) -> None:
        """Draw a ghost with smooth inter-tile animation.

        Args:
            row:        Current tile row.
            col:        Current tile column.
            prev_row:   Previous tile row.
            prev_col:   Previous tile column.
            progress:   Animation progress 0.0->1.0.
            colour:     Ghost colour: 'red','pink','cyan','orange'.
            anim_frame: Walk cycle frame (0-1).
            edible:     True when ghost is edible (blue).
            flash:      True when flashing (edible time almost up).
        """
        cx0, cy0 = self.tile_center(prev_row, prev_col)
        cx1, cy1 = self.tile_center(row, col)
        px = int(cx0 + (cx1 - cx0) * progress)
        py = int(cy0 + (cy1 - cy0) * progress)

        if edible:
            key = "white" if flash else "blue"
        else:
            key = colour if colour in self._ghosts else "red"

        frames = self._ghosts[key]
        sprite = frames[anim_frame % len(frames)]
        rect = sprite.get_rect(center=(px, py))
        self._screen.blit(sprite, rect)

    # ── Pellets ─────────────────────────────────────────────────────────────

    def draw_pacgum(self, row: int, col: int, anim_frame: int = 0) -> None:
        """Draw a regular pacgum (coin spin animation).

        Args:
            row:        Grid row.
            col:        Grid column.
            anim_frame: Coin spin frame index (0-7).
        """
        sprite = self._coin[anim_frame % len(self._coin)]
        rect = sprite.get_rect(center=self.tile_center(row, col))
        self._screen.blit(sprite, rect)

    def draw_super_pacgum(
        self,
        row: int,
        col: int,
        anim_frame: int = 0,
        visible: bool = True,
    ) -> None:
        """Draw a super-pacgum power pellet (big coin).

        Args:
            row:        Grid row.
            col:        Grid column.
            anim_frame: Spin frame index (0-7).
            visible:    False during blink-off phase.
        """
        if not visible:
            return
        sprite = self._bigcoin[anim_frame % len(self._bigcoin)]
        rect = sprite.get_rect(center=self.tile_center(row, col))
        self._screen.blit(sprite, rect)

    # ── HUD ─────────────────────────────────────────────────────────────────

    def draw_hud(
        self,
        score: int,
        lives: int,
        level: int,
        time_left: float,
        cheats_active: Optional[list[str]] = None,
    ) -> None:
        """Draw the right-side HUD panel.

        Args:
            score:         Current player score.
            lives:         Remaining lives.
            level:         Current level (1-based).
            time_left:     Seconds remaining in the level.
            cheats_active: Active cheat names to display.
        """
        sw, _ = self._screen.get_size()
        x = sw - self._hud_w + 16
        y = 30

        def hud_line(
            label: str,
            value: str,
            colour: tuple[int, int, int] = HUD_TEXT,
        ) -> None:
            nonlocal y
            self._screen.blit(
                self._font_small.render(label, True, GREY), (x, y)
            )
            y += 20
            self._screen.blit(
                self._font_hud.render(value, True, colour), (x, y)
            )
            y += 34

        self._screen.blit(
            self._font_title.render("PAC-MAN", True, YELLOW), (x - 4, y)
        )
        y += 50
        hud_line("SCORE", str(score))
        hud_line("LEVEL", str(level))
        hud_line("LIVES", "* " * max(0, lives), RED)
        hud_line(
            "TIME", f"{int(time_left)}s",
            RED if time_left < 15 else HUD_TEXT,
        )

        if cheats_active:
            y += 10
            self._screen.blit(
                self._font_small.render("CHEATS ON:", True, YELLOW), (x, y)
            )
            y += 18
            for cheat in cheats_active:
                self._screen.blit(
                    self._font_small.render(f"  {cheat}", True, YELLOW),
                    (x, y),
                )
                y += 16

    # ── Debug ───────────────────────────────────────────────────────────────

    def draw_debug_overlay(self, fps: float) -> None:
        """Draw FPS counter in the top-left corner.

        Args:
            fps: Current frames per second.
        """
        self._screen.blit(
            self._font_small.render(f"FPS: {fps:.1f}", True, WHITE), (6, 6)
        )
