"""src/ui/menu.py — All menu / overlay screen rendering for Pac-Man.

Draws main menu, pause overlay, game-over, victory, highscore table,
and instructions onto whatever pygame Surface is provided.

Design: Pac-Man themed — deep navy background, yellow title, white text.
All drawing is stateless: callers pass in the values to display.
"""

from __future__ import annotations

import math
from typing import Any

import pygame

# ── Colour palette ──────────────────────────────────────────────────────────

_DARK_NAVY: tuple[int, int, int] = (5, 5, 30)
_NAVY: tuple[int, int, int] = (10, 10, 50)
_BLUE_GLOW: tuple[int, int, int] = (30, 30, 120)
_YELLOW: tuple[int, int, int] = (255, 215, 0)
_YELLOW_DIM: tuple[int, int, int] = (180, 140, 0)
_WHITE: tuple[int, int, int] = (240, 240, 240)
_GREY: tuple[int, int, int] = (130, 130, 160)
_RED: tuple[int, int, int] = (230, 60, 60)
_GREEN: tuple[int, int, int] = (80, 210, 80)
_CYAN: tuple[int, int, int] = (80, 200, 220)
_ORANGE: tuple[int, int, int] = (255, 150, 30)
_OVERLAY: tuple[int, int, int, int] = (0, 0, 0, 170)

_GHOST_COLOURS: list[tuple[int, int, int]] = [
    _RED, _ORANGE, _CYAN, (255, 182, 255),
]


class MenuRenderer:
    """Draws all menu and overlay screens for the Pac-Man game.

    All public methods are stateless: they take the values they need as
    arguments and render directly onto *screen*.  The Game class keeps the
    mutable state (selected index, name buffer, etc.).
    """

    def __init__(self) -> None:
        """Initialise fonts."""
        self._font_title = pygame.font.SysFont("monospace", 56, bold=True)
        self._font_large = pygame.font.SysFont("monospace", 36, bold=True)
        self._font_med = pygame.font.SysFont("monospace", 26, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 18)
        self._font_tiny = pygame.font.SysFont("monospace", 14)
        self._tick: float = 0.0   # cumulative time for animations

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Advance animation tick counter.

        Args:
            dt: Delta time in seconds.
        """
        self._tick += dt

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _blit_center(
        self,
        screen: pygame.Surface,
        surf: pygame.Surface,
        cx: int,
        cy: int,
    ) -> None:
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def _render(
        self,
        text: str,
        font: pygame.font.Font,
        colour: tuple[int, int, int],
        shadow: bool = False,
        shadow_colour: tuple[int, int, int] = (0, 0, 0),
    ) -> pygame.Surface:
        if shadow:
            # Render shadow first so we can composite
            shadow_surf = font.render(text, True, shadow_colour)
            base_surf = font.render(text, True, colour)
            w = base_surf.get_width() + 3
            h = base_surf.get_height() + 3
            combined = pygame.Surface((w, h), pygame.SRCALPHA)
            combined.blit(shadow_surf, (3, 3))
            combined.blit(base_surf, (0, 0))
            return combined
        return font.render(text, True, colour)

    def _draw_background(self, screen: pygame.Surface) -> None:
        """Fill with gradient-ish dark navy."""
        screen.fill(_DARK_NAVY)
        sw, sh = screen.get_size()
        # Subtle radial vignette via a semi-transparent dark border
        for i, alpha in enumerate([30, 20, 10]):
            margin = (i + 1) * 20
            vign = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.rect(
                vign, (0, 0, 0, alpha),
                pygame.Rect(0, 0, sw, sh),
                margin,
            )
            screen.blit(vign, (0, 0))

    def _draw_dot_border(
        self, screen: pygame.Surface, y: int, count: int = 28,
    ) -> None:
        """Draw a row of animated pac-dots across the screen."""
        sw = screen.get_width()
        spacing = sw // count
        phase = self._tick * 2.0
        for i in range(count):
            pulse = 0.5 + 0.5 * math.sin(phase - i * 0.3)
            r = int(3 + pulse * 2)
            alpha = int(120 + 120 * pulse)
            dot_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(
                dot_surf, (*_YELLOW, alpha), (r + 1, r + 1), r,
            )
            screen.blit(dot_surf, (i * spacing + spacing // 2 - r, y - r))

    def _draw_title(self, screen: pygame.Surface) -> None:
        """Draw the animated PAC-MAN title."""
        sw, sh = screen.get_size()
        cx = sw // 2

        # Glow effect — slightly larger, dim yellow
        pulse = 0.8 + 0.2 * math.sin(self._tick * 2.5)
        glow_col = (
            int(_YELLOW[0] * pulse),
            int(_YELLOW[1] * 0.5 * pulse),
            0,
        )
        glow = self._font_title.render("PAC-MAN", True, glow_col)
        gw, gh = glow.get_size()
        glow_big = pygame.transform.scale(glow, (gw + 6, gh + 6))
        screen.blit(glow_big, glow_big.get_rect(center=(cx, sh // 6 + 3)))

        # Main title
        title = self._render(
            "PAC-MAN", self._font_title, _YELLOW,
            shadow=True, shadow_colour=(80, 60, 0),
        )
        self._blit_center(screen, title, cx, sh // 6)

    def _draw_ghost_decorations(self, screen: pygame.Surface) -> None:
        """Draw small animated ghost icons near the title."""
        sw, sh = screen.get_size()
        ghost_y = sh // 6 + 55
        positions = [sw // 2 - 160, sw // 2 - 80, sw // 2 + 80, sw // 2 + 160]
        for i, (gx, col) in enumerate(zip(positions, _GHOST_COLOURS)):
            bob = math.sin(self._tick * 2 + i * 1.2) * 4
            self._draw_mini_ghost(screen, gx, int(ghost_y + bob), col)

    def _draw_mini_ghost(
        self,
        screen: pygame.Surface,
        cx: int,
        cy: int,
        colour: tuple[int, int, int],
        size: int = 18,
    ) -> None:
        """Draw a simple filled ghost shape."""
        surf = pygame.Surface((size * 2, size * 2 + 4), pygame.SRCALPHA)
        # Body (semicircle top + rectangle bottom with bumps)
        body_rect = pygame.Rect(0, size // 2, size * 2, size)
        pygame.draw.ellipse(surf, colour, pygame.Rect(0, 0, size * 2, size + 2))
        pygame.draw.rect(surf, colour, body_rect)
        # Feet (3 bumps)
        for j in range(3):
            fx = j * (size * 2 // 3) + size // 3
            pygame.draw.circle(surf, colour, (fx, size + size // 2 + 4), size // 3)
        # Eyes
        eye_y = size // 2
        for ex in [size // 2, size + size // 2]:
            pygame.draw.circle(surf, _WHITE, (ex, eye_y), size // 5)
            pygame.draw.circle(
                surf, _DARK_NAVY, (ex + 2, eye_y + 1), size // 8,
            )
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def _draw_menu_option(
        self,
        screen: pygame.Surface,
        text: str,
        cx: int,
        cy: int,
        selected: bool,
        prefix: str = "▶ ",
    ) -> None:
        """Draw a single menu option with selection highlight."""
        if selected:
            # Highlight box
            surf_w = 340
            surf_h = 46
            box = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            pulse = 0.5 + 0.5 * math.sin(self._tick * 4)
            alpha = int(60 + 40 * pulse)
            pygame.draw.rect(
                box, (*_BLUE_GLOW, alpha),
                pygame.Rect(0, 0, surf_w, surf_h),
                border_radius=10,
            )
            pygame.draw.rect(
                box, (*_YELLOW, 160),
                pygame.Rect(0, 0, surf_w, surf_h),
                2, border_radius=10,
            )
            screen.blit(box, box.get_rect(center=(cx, cy)))
            label = self._render(f"{prefix}{text}", self._font_med, _YELLOW)
        else:
            label = self._render(f"  {text}", self._font_med, _GREY)
        self._blit_center(screen, label, cx, cy)

    # ── Public screens ───────────────────────────────────────────────────────

    def draw_main_menu(
        self,
        screen: pygame.Surface,
        selected_index: int,
    ) -> None:
        """Draw the main menu.

        Options: Start Game, View Highscores, Instructions, Exit.

        Args:
            screen:         Surface to draw onto.
            selected_index: Currently highlighted option (0-3).
        """
        self._draw_background(screen)
        sw, sh = screen.get_size()
        cx = sw // 2

        self._draw_title(screen)
        self._draw_ghost_decorations(screen)
        self._draw_dot_border(screen, sh // 4 + 10)

        options = ["Start Game", "Highscores", "Instructions", "Exit"]
        start_y = sh // 2 - 40
        spacing = 56

        for i, opt in enumerate(options):
            self._draw_menu_option(
                screen, opt, cx, start_y + i * spacing,
                selected=(i == selected_index),
            )

        hint = self._render(
            "↑↓ navigate  •  ENTER select  •  ESC exit",
            self._font_tiny, _GREY,
        )
        self._blit_center(screen, hint, cx, sh - 30)

    def draw_pause_menu(
        self,
        screen: pygame.Surface,
        selected_index: int,
    ) -> None:
        """Draw the pause overlay on top of the game frame.

        Args:
            screen:         Surface (game already drawn).
            selected_index: Currently highlighted option (0-1).
        """
        sw, sh = screen.get_size()

        # Semi-transparent dark overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill(_OVERLAY)
        screen.blit(overlay, (0, 0))

        cx = sw // 2

        # PAUSED title
        title = self._render(
            "PAUSED", self._font_large, _YELLOW,
            shadow=True, shadow_colour=(60, 50, 0),
        )
        self._blit_center(screen, title, cx, sh // 3)

        # Separator dots
        self._draw_dot_border(screen, sh // 3 + 50, count=16)

        options = ["Resume", "Main Menu"]
        start_y = sh // 2
        for i, opt in enumerate(options):
            self._draw_menu_option(
                screen, opt, cx, start_y + i * 56,
                selected=(i == selected_index),
            )

        hint = self._render(
            "ESC / P  to resume", self._font_tiny, _GREY,
        )
        self._blit_center(screen, hint, cx, sh - 30)

    def draw_game_over(
        self,
        screen: pygame.Surface,
        score: int,
        name_buffer: str,
        cursor_visible: bool = True,
        is_high_score: bool = False,
    ) -> None:
        """Draw the game-over screen with name entry.

        Args:
            screen:         Surface to draw onto.
            score:          Final player score.
            name_buffer:    Current name input string.
            cursor_visible: Whether the text cursor is visible.
            is_high_score:  True if this score qualifies for top-10.
        """
        self._draw_end_screen(
            screen, "GAME OVER", _RED, score, name_buffer,
            cursor_visible, is_high_score,
        )

    def draw_victory(
        self,
        screen: pygame.Surface,
        score: int,
        name_buffer: str,
        cursor_visible: bool = True,
        is_high_score: bool = False,
    ) -> None:
        """Draw the victory screen with name entry.

        Args:
            screen:         Surface to draw onto.
            score:          Final player score.
            name_buffer:    Current name input string.
            cursor_visible: Whether the text cursor is visible.
            is_high_score:  True if this score qualifies for top-10.
        """
        self._draw_end_screen(
            screen, "YOU WIN! 🎉", _GREEN, score, name_buffer,
            cursor_visible, is_high_score,
        )

    def _draw_end_screen(
        self,
        screen: pygame.Surface,
        heading: str,
        heading_colour: tuple[int, int, int],
        score: int,
        name_buffer: str,
        cursor_visible: bool,
        is_high_score: bool,
    ) -> None:
        """Shared layout for game-over / victory screens.

        Args:
            screen:          Surface to draw onto.
            heading:         Main heading text.
            heading_colour:  Colour for the heading.
            score:           Final score.
            name_buffer:     Current text input for player name.
            cursor_visible:  Blink state for text cursor.
            is_high_score:   If True, show name entry; else show return hint.
        """
        self._draw_background(screen)
        sw, sh = screen.get_size()
        cx = sw // 2

        # Heading
        title = self._render(
            heading, self._font_large, heading_colour,
            shadow=True, shadow_colour=(0, 0, 0),
        )
        self._blit_center(screen, title, cx, sh // 5)

        # Score
        score_surf = self._render(
            f"Score: {score:,}", self._font_med, _WHITE,
        )
        self._blit_center(screen, score_surf, cx, sh // 5 + 70)

        self._draw_dot_border(screen, sh // 5 + 110)

        if is_high_score:
            # New high-score banner
            banner = self._render("🏆 NEW HIGH SCORE!", self._font_med, _YELLOW)
            self._blit_center(screen, banner, cx, sh // 2 - 30)

            # Name entry prompt
            prompt = self._render("Enter your name:", self._font_small, _GREY)
            self._blit_center(screen, prompt, cx, sh // 2 + 20)

            # Name input box
            box_w, box_h = 320, 50
            box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(
                box, (*_NAVY, 220),
                pygame.Rect(0, 0, box_w, box_h), border_radius=8,
            )
            pygame.draw.rect(
                box, (*_YELLOW, 200),
                pygame.Rect(0, 0, box_w, box_h), 2, border_radius=8,
            )
            screen.blit(box, box.get_rect(center=(cx, sh // 2 + 72)))

            cursor = "|" if cursor_visible else " "
            name_text = self._render(
                f"{name_buffer}{cursor}", self._font_med, _YELLOW,
            )
            self._blit_center(screen, name_text, cx, sh // 2 + 72)

            hint = self._render(
                "ENTER to confirm  (max 10 chars, letters/numbers/spaces)",
                self._font_tiny, _GREY,
            )
            self._blit_center(screen, hint, cx, sh // 2 + 108)
        else:
            # Score not in top-10
            msg = self._render("Keep practising!", self._font_small, _GREY)
            self._blit_center(screen, msg, cx, sh // 2)

        hint2 = self._render(
            "ENTER  to return to main menu",
            self._font_tiny, _GREY,
        )
        self._blit_center(screen, hint2, cx, sh - 30)

    def draw_highscores(
        self,
        screen: pygame.Surface,
        scores: list[dict[str, Any]],
    ) -> None:
        """Draw the top-10 highscore table.

        Args:
            screen: Surface to draw onto.
            scores: List of {"name": str, "score": int} dicts, sorted desc.
        """
        self._draw_background(screen)
        sw, sh = screen.get_size()
        cx = sw // 2

        title = self._render(
            "HIGH SCORES", self._font_large, _YELLOW,
            shadow=True, shadow_colour=(60, 50, 0),
        )
        self._blit_center(screen, title, cx, sh // 8)

        self._draw_dot_border(screen, sh // 8 + 52)

        if not scores:
            empty = self._render("No scores yet!", self._font_med, _GREY)
            self._blit_center(screen, empty, cx, sh // 2)
        else:
            col_rank = cx - 200
            col_name = cx - 60
            col_score = cx + 160

            # Header row
            for text, col in [
                ("#", col_rank), ("NAME", col_name), ("SCORE", col_score),
            ]:
                hdr = self._render(text, self._font_small, _CYAN)
                screen.blit(hdr, hdr.get_rect(centerx=col, y=sh // 8 + 65))

            row_y = sh // 8 + 100
            for i, entry in enumerate(scores[:10]):
                rank_col = _YELLOW if i == 0 else (_GREY if i >= 3 else _WHITE)
                rank = self._render(f"{i + 1}.", self._font_small, rank_col)
                name = self._render(
                    entry.get("name", "???"), self._font_small, rank_col,
                )
                score_s = self._render(
                    f"{entry.get('score', 0):,}", self._font_small, rank_col,
                )
                screen.blit(rank, rank.get_rect(centerx=col_rank, y=row_y))
                screen.blit(name, name.get_rect(centerx=col_name, y=row_y))
                screen.blit(score_s, score_s.get_rect(centerx=col_score, y=row_y))
                row_y += 34

        hint = self._render(
            "ENTER / ESC  to return", self._font_tiny, _GREY,
        )
        self._blit_center(screen, hint, cx, sh - 30)

    def draw_instructions(self, screen: pygame.Surface) -> None:
        """Draw the controls and rules screen.

        Args:
            screen: Surface to draw onto.
        """
        self._draw_background(screen)
        sw, sh = screen.get_size()
        cx = sw // 2

        title = self._render(
            "HOW TO PLAY", self._font_large, _YELLOW,
            shadow=True, shadow_colour=(60, 50, 0),
        )
        self._blit_center(screen, title, cx, sh // 10)

        self._draw_dot_border(screen, sh // 10 + 52)

        sections: list[tuple[str, list[str]]] = [
            ("CONTROLS", [
                "Arrow keys / WASD  →  Move Pac-Man",
                "ESC or P           →  Pause / Resume",
            ]),
            ("OBJECTIVE", [
                "Eat all pellets on each level to advance.",
                "Avoid ghosts — they steal a life!",
                "Eat a power pellet to turn ghosts blue.",
                "Eat blue ghosts for bonus points!",
            ]),
            ("CHEATS  (reviewer mode)", [
                "I — Invincibility     F — Freeze ghosts",
                "B — Speed ×2         L — Extra life",
                "N — Skip level",
            ]),
        ]

        y = sh // 10 + 72
        for heading, lines in sections:
            hdr = self._render(heading, self._font_small, _CYAN)
            self._blit_center(screen, hdr, cx, y)
            y += 28
            for line in lines:
                ln = self._render(line, self._font_tiny, _WHITE)
                self._blit_center(screen, ln, cx, y)
                y += 22
            y += 14

        hint = self._render(
            "ENTER / ESC  to return", self._font_tiny, _GREY,
        )
        self._blit_center(screen, hint, cx, sh - 30)
