"""Maze loader — wraps the assigned A-Maze-ing package (mazegenerator 2.0.2).

The maze is a list[list[int]] where each cell is a bitmask:
    bit 0 (1)  → North wall is PRESENT (passage to the north is blocked)
    bit 1 (2)  → East  wall is PRESENT
    bit 2 (4)  → South wall is PRESENT
    bit 3 (8)  → West  wall is PRESENT
    0          → fully open (no walls — 4-way corridor)
    15         → fully closed (walls on all four sides)

The generator clears bits to open passages (maze[y][x] &= ~code).

We always use perfect=False so the maze has loops (required for Pac-Man).
"""

from typing import cast

from mazegenerator import MazeGenerator


# Bitmask constants — bit SET means wall present on that side
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
ALL_OPEN: int = 0    # no walls — fully open 4-way corridor
ALL_WALLS: int = 15  # walls on all sides — fully closed


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

    With the mazegenerator's bitmask convention (bit SET = wall):
      - cell == 15 means walls on all four sides → impassable block
      - cell == 0  means no walls at all → fully open corridor
      - Border cells are always treated as walls.

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

    # Interior cell with all walls present (15) = solid block (e.g. "42" logo)
    return cell == ALL_WALLS


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
    mapping: dict[str, int] = {
        'N': NORTH,
        'E': EAST,
        'S': SOUTH,
        'W': WEST,
    }
    if direction not in mapping:
        raise ValueError(f"Invalid direction '{direction}'. Use N, S, E, W.")

    # Out-of-bounds → treat as wall
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    if row < 0 or row >= rows or col < 0 or col >= cols:
        return False

    cell = grid[row][col]
    bit = mapping[direction]
    # mazegenerator convention (verified from library source):
    #   bit SET   = wall present (blocked)
    #   bit CLEAR = passage open (can move)
    # _generate_maze clears bits with & ~code to open passages.
    # _find_short_path skips when (cell & code) != 0 (wall).
    if bool(cell & bit):
        return False  # wall on that side — blocked
    # Verify destination cell is not a border or out of bounds
    deltas: dict[str, tuple[int, int]] = {
        'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1),
    }
    dr, dc = deltas[direction]
    dest_r, dest_c = row + dr, col + dc
    if (dest_r <= 0 or dest_r >= rows - 1
            or dest_c <= 0 or dest_c >= cols - 1):
        return False
    return True


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
