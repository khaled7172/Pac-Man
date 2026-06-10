#!/usr/bin/env python3
"""test_maze.py — Run this to verify the mazegenerator integration.

Usage (from your project root, with venv active):
    python3 test_maze.py

What it does:
    1. Generates a fixed maze (seed=42) and prints it as ASCII art.
    2. Generates a random maze (seed=0) and prints it.
    3. Prints walkable cell count, center, and corners.
    4. Tests can_move() on a few cells.
    5. Tests error handling with a bad size.
"""

from maze.loader import (
    generate_maze,
    is_wall,
    can_move,
    get_walkable_cells,
    get_center,
    get_corners,
)
import sys
import os

# Make sure we can import from src/ when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


# ── ASCII rendering ──────────────────────────────────────────────────────────

def render_maze(grid: list[list[int]], label: str = "") -> None:
    """Print a maze as ASCII art to the terminal."""
    WALL_CHAR = "██"
    OPEN_CHAR = "  "
    CENTER_CHAR = "PP"   # Pac-Man start
    CORNER_CHAR = "GG"   # Ghost / super-pacgum corners

    center = get_center(grid)
    corners = set(get_corners(grid))

    if label:
        print(f"\n{'─' * 40}")
        print(f"  {label}")
        print(f"{'─' * 40}")

    for row_idx, row in enumerate(grid):
        line = ""
        for col_idx, cell in enumerate(row):
            pos = (row_idx, col_idx)
            if pos == center:
                line += CENTER_CHAR
            elif pos in corners:
                line += CORNER_CHAR
            elif is_wall(grid, row_idx, col_idx):
                line += WALL_CHAR
            else:
                line += OPEN_CHAR
        print(line)


# ── Tests ────────────────────────────────────────────────────────────────────

def test_fixed_seed() -> None:
    """Test generation with seed=42 (must be identical every run)."""
    print("\n[TEST 1] Fixed seed=42 (level 1 — must always look the same)")
    grid = generate_maze(width=21, height=21, seed=42)
    render_maze(grid, "Fixed seed=42  (21×21)")

    walkable = get_walkable_cells(grid)
    center = get_center(grid)
    corners = get_corners(grid)

    print(f"\n  Grid size   : {len(grid)} rows × {len(grid[0])} cols")
    print(f"  Walkable    : {len(walkable)} cells")
    print(f"  Center (PP) : row={center[0]}, col={center[1]}")
    print(f"  Corners (GG): {corners}")


def test_random_seed() -> None:
    """Test generation with seed=0 (random — different every run)."""
    print("\n[TEST 2] Random seed=0 (subsequent levels — changes each run)")
    grid = generate_maze(width=21, height=21, seed=0)
    render_maze(grid, "Random seed  (21×21)")


def test_can_move() -> None:
    """Test the can_move() helper on a known maze."""
    print("\n[TEST 3] can_move() checks on seed=42 maze")
    grid = generate_maze(width=21, height=21, seed=42)

    # Test a few cells — just print results so you can verify visually
    test_positions = [
        (1, 1), (1, 10), (10, 10), (10, 1), (20, 20)
    ]
    for row, col in test_positions:
        cell_val = grid[row][col] if 0 <= row < len(
            grid) and 0 <= col < len(grid[0]) else "OOB"
        wall = is_wall(grid, row, col)
        if not wall and isinstance(cell_val, int):
            moves = [
                d for d in [
                    'N',
                    'S',
                    'E',
                    'W'] if can_move(
                    grid,
                    row,
                    col,
                    d)]
            print(
                f"  ({
                    row:2d},{
                    col:2d})  cell={
                    cell_val:2d}  wall={wall}  can_move→ {moves}")
        else:
            print(f"  ({row:2d},{col:2d})  cell={cell_val}  wall={wall}")


def test_error_handling() -> None:
    """Test that a bad call raises RuntimeError cleanly (no traceback leak)."""
    print("\n[TEST 4] Error handling (size too small)")
    try:
        # Size (2,2) will still run but produce a degenerate maze — test it
        grid = generate_maze(width=2, height=2, seed=42)
        print(
            f"  Generated {len(grid)}×{len(grid[0])} "
            "maze (very small,check output)")
    except RuntimeError as e:
        print(f"  RuntimeError caught cleanly: {e}")
    except Exception as e:
        print(f"  ⚠ Unexpected exception type {type(e).__name__}: {e}")


def test_different_sizes() -> None:
    """Test that larger sizes work for later levels."""
    print("\n[TEST 5] Larger maze (25×25)")
    grid = generate_maze(width=25, height=25, seed=7)
    render_maze(grid, "seed=7  (25×25)")
    print(f"  Walkable cells: {len(get_walkable_cells(grid))}")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 40)
    print("  MAZE GENERATOR INTEGRATION TEST")
    print("=" * 40)

    test_fixed_seed()
    test_random_seed()
    test_can_move()
    test_error_handling()
    test_different_sizes()

    print("\n✓ All tests ran. Check the ASCII art above for correctness.")
    print("  PP = Pac-Man start (center)")
    print("  GG = Ghost corners / super-pacgum positions")
    print("  ██ = Wall")
    print("  (space) = Walkable corridor\n")
