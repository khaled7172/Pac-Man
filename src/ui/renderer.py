"""src/ui/renderer.py — All drawing logic for the Pac-Man game.

Nothing in here touches game state directly — it only reads and draws.
The game passes data in; this module draws it out.
"""

import pygame
from typing import Optional

# ── Colours ─────────────────────────────────────────────────────────────

BLACK: tuple[int, int, int] = (0, 0, 0)
DARK_BLUE: tuple[int, int, int] = (0, 0, 40)
WALL_BLUE: tuple[int, int, int] = (33, 33, 222)
WALL_BORDER: tuple[int, int, int] = (50, 50, 255)
FLOOR: tuple[int, int, int] = (0, 0, 20)
YELLOW: tuple[int, int, int] = (255, 255, 0)
WHITE: tuple[int, int, int] = (255, 255, 255)
GREY: tuple[int, int, int] = (180, 180, 180)
RED: tuple[int, int, int] = (220, 50, 50)

HUD_BG: tuple[int, int, int] = (10, 10, 30)
HUD_TEXT: tuple[int, int, int] = (220, 220, 220)

# Bitmask constants (must match maze/loader.py)
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8


class Renderer:
    """Handles all pygame drawing for the Pac-Man game.

    Args:
        screen:    The pygame Surface to draw on.
        maze_cols: Number of columns in the maze grid.
        maze_rows: Number of rows in the maze grid.
        tile_size: Pixel size of each maze tile (default 32).
        hud_width: Width of the HUD panel on the right (default 200).
    """

    def __init__(
        self,
        screen: pygame.Surface,
        maze_cols: int,
        maze_rows: int,
        tile_size: int = 32,
        hud_width: int = 200,
    ) -> None:
        """Initialise the renderer."""
        self._screen = screen
        self._maze_cols = maze_cols
        self._maze_rows = maze_rows
        self._tile = tile_size
        self._hud_w = hud_width

        screen_w, screen_h = screen.get_size()
        play_w = screen_w - hud_width

        self._offset_x: int = (play_w - maze_cols * tile_size) // 2
        self._offset_y: int = (screen_h - maze_rows * tile_size) // 2

        self._font_hud = pygame.font.SysFont("monospace", 20, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 14)
        self._font_title = pygame.font.SysFont("monospace", 28, bold=True)

    def tile_rect(self, row: int, col: int) -> pygame.Rect:
        """Return the pixel Rect for a given grid tile.

        Args:
            row: Grid row index.
            col: Grid column index.

        Returns:
            A pygame.Rect covering that tile on screen.
        """
        x = self._offset_x + col * self._tile
        y = self._offset_y + row * self._tile
        return pygame.Rect(x, y, self._tile, self._tile)

    def tile_center(self, row: int, col: int) -> tuple[int, int]:
        """Return the pixel centre of a given grid tile.

        Args:
            row: Grid row index.
            col: Grid column index.

        Returns:
            (x, y) pixel coordinates of the tile centre.
        """
        r = self.tile_rect(row, col)
        return r.centerx, r.centery

    def clear(self) -> None:
        """Fill the entire screen with the background colour."""
        self._screen.fill(DARK_BLUE)
        screen_w, screen_h = self._screen.get_size()
        hud_rect = pygame.Rect(screen_w - self._hud_w, 0,
                               self._hud_w, screen_h)
        pygame.draw.rect(self._screen, HUD_BG, hud_rect)

    def draw_maze(self, grid: list[list[int]]) -> None:
        """Draw the full maze grid.

        Args:
            grid: 2-D bitmask grid from src/maze/loader.py.
        """
        t = self._tile
        wall_thickness = max(2, t // 8)

        for row_idx, row in enumerate(grid):
            for col_idx, cell in enumerate(row):
                rect = self.tile_rect(row_idx, col_idx)

                if (row_idx == 0 or row_idx == len(grid) - 1
                        or col_idx == 0 or col_idx == len(row) - 1
                        or cell == 0):
                    pygame.draw.rect(self._screen, WALL_BLUE, rect)
                    pygame.draw.rect(self._screen, WALL_BORDER, rect, 1)
                    continue

                pygame.draw.rect(self._screen, FLOOR, rect)

                x, y = rect.x, rect.y
                if not (cell & NORTH):
                    pygame.draw.line(self._screen, WALL_BLUE,
                                     (x, y), (x + t, y), wall_thickness)
                if not (cell & SOUTH):
                    pygame.draw.line(
                        self._screen, WALL_BLUE, (x, y + t), (x + t, y + t),
                        wall_thickness)
                if not (cell & EAST):
                    pygame.draw.line(
                        self._screen, WALL_BLUE, (x + t, y), (x + t, y + t),
                        wall_thickness)
                if not (cell & WEST):
                    pygame.draw.line(self._screen, WALL_BLUE,
                                     (x, y), (x, y + t), wall_thickness)

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
            level:         Current level number (1-based).
            time_left:     Seconds remaining in the level.
            cheats_active: List of active cheat names to display (or None).
        """
        screen_w, _ = self._screen.get_size()
        x = screen_w - self._hud_w + 16
        y = 30

        def hud_line(
            label: str,
            value: str,
            colour: tuple[int, int, int] = HUD_TEXT,
        ) -> None:
            nonlocal y
            lbl = self._font_small.render(label, True, GREY)
            val = self._font_hud.render(value, True, colour)
            self._screen.blit(lbl, (x, y))
            y += 20
            self._screen.blit(val, (x, y))
            y += 34

        title = self._font_title.render("PAC-MAN", True, YELLOW)
        self._screen.blit(title, (x - 4, y))
        y += 50

        hud_line("SCORE", str(score))
        hud_line("LEVEL", str(level))
        hud_line("LIVES", "* " * lives, RED)
        hud_line(
            "TIME",
            f"{int(time_left)}s",
            RED if time_left < 15 else HUD_TEXT,
        )

        if cheats_active:
            y += 10
            cheat_label = self._font_small.render("CHEATS ON:", True, YELLOW)
            self._screen.blit(cheat_label, (x, y))
            y += 18
            for cheat in cheats_active:
                line = self._font_small.render(f"  {cheat}", True, YELLOW)
                self._screen.blit(line, (x, y))
                y += 16

    def draw_debug_overlay(self, fps: float) -> None:
        """Draw FPS counter in top-left corner (debug/cheat mode only).

        Args:
            fps: Current frames per second.
        """
        surf = self._font_small.render(f"FPS: {fps:.1f}", True, WHITE)
        self._screen.blit(surf, (6, 6))
