"""Maze loader — wraps the assigned A-Maze-ing package (mazegenerator 2.0.2).

The maze is a list[list[int]] where each cell is a bitmask:
    bit 0 (1)  → North wall is OPEN (passage to the north exists)
    bit 1 (2)  → East  wall is OPEN
    bit 2 (4)  → South wall is OPEN
    bit 3 (8)  → West  wall is OPEN
    0          → fully closed (solid wall / border)
    15         → fully open (4-way corridor)

We always use perfect=False so the maze has loops (required for Pac-Man).
"""

from typing import cast

from mazegenerator import MazeGenerator


# Bitmask constants — use these everywhere instead of magic numbers
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
WALL: int = 0       # solid wall cell
OPEN: int = 15      # fully open cell


def generate_maze(
    width: int,
    height: int,
    seed: int = 0,
) -> list[list[int]]:
    """Generate a maze using the assigned mazegenerator package.

    Args:
        width:  Number of columns (must be >= 7 for the '42' logo to fit).
        height: Number of rows    (must be >= 7 for the '42' logo to fit).
        seed:   Fixed seed for reproducible mazes (0 = random).

    Returns:
        A 2-D grid (row-major) of bitmask integers.
        grid[row][col] — row 0 is the top row.

    Raises:
        RuntimeError: If the mazegenerator package fails for any reason.
    """
    try:
        gen = MazeGenerator(
            size=(width, height),
            perfect=False,   # MUST be False — creates loops for Pac-Man
            seed=seed,
        )
        return cast(list[list[int]], gen.maze)
    except Exception as e:
        raise RuntimeError(
            f"Maze generation failed (size={width}x{height}, seed={seed}): {e}"
        )


def is_wall(grid: list[list[int]], row: int, col: int) -> bool:
    """Return True if the cell at (row, col) is a solid wall.

    A cell is walkable if any of its wall-bits are open (value > 0 and not
    a pure border marker).  Border markers (1,2,4,8,9,3,12,6) on the outer
    ring are treated as walls for gameplay purposes.

    Args:
        grid: The maze grid from generate_maze().
        row:  Row index.
        col:  Column index.

    Returns:
        True if the cell is impassable, False if the player
        can walk through it.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Out of bounds = wall
    if row < 0 or row >= rows or col < 0 or col >= cols:
        return True

    cell = grid[row][col]

    # Outer border cells are always walls
    if row == 0 or row == rows - 1 or col == 0 or col == cols - 1:
        return True

    # Interior cell with value 0 = solid wall
    return cell == WALL


def can_move(
    grid: list[list[int]],
    row: int,
    col: int,
    direction: str,
) -> bool:
    """Return True if movement from (row, col) in direction is allowed.

    Args:
        grid:      The maze grid.
        row:       Current row.
        col:       Current column.
        direction: One of 'N', 'S', 'E', 'W'.

    Returns:
        True if the wall in that direction is open (passage exists).

    Raises:
        ValueError: If direction is not one of N/S/E/W.
    """
    cell = grid[row][col]
    mapping: dict[str, int] = {
        'N': NORTH,
        'E': EAST,
        'S': SOUTH,
        'W': WEST,
    }
    if direction not in mapping:
        raise ValueError(f"Invalid direction '{direction}'. Use N, S, E, W.")

    bit = mapping[direction]
    # Wall is OPEN when the bit is NOT set (0 = wall closed, bit clear = open)
    # Re-reading the source: bit set means wall present on that side?
    # Actually from _generate_maze: maze[y][x] = 15 & ~from_code
    # 15 = all open, clearing a bit CLOSES that passage.
    # So: bit SET = wall open (passage), bit CLEAR = wall closed.
    return bool(cell & bit)


def get_walkable_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return a list of all (row, col) positions that are walkable.

    Args:
        grid: The maze grid from generate_maze().

    Returns:
        List of (row, col) tuples for every non-wall interior cell.
    """
    cells: list[tuple[int, int]] = []
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            if not is_wall(grid, row, col):
                cells.append((row, col))
    return cells


def get_center(grid: list[list[int]]) -> tuple[int, int]:
    """Return the (row, col) of the maze center — Pac-Man's start position.

    Args:
        grid: The maze grid from generate_maze().

    Returns:
        The center cell as (row, col).
    """
    return len(grid) // 2, len(grid[0]) // 2


def get_corners(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return the 4 corner positions for ghost spawns and super-pacgums.

    Corners are offset by 1 from the border (first walkable cell in each
    corner direction).

    Args:
        grid: The maze grid from generate_maze().

    Returns:
        List of 4 (row, col) tuples: [top-left, top-right,
        bottom-left, bottom-right].
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    return [
        (1, 1),               # top-left
        (1, cols - 2),        # top-right
        (rows - 2, 1),        # bottom-left
        (rows - 2, cols - 2),  # bottom-right
    ]
