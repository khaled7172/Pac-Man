# loader.py — wraps mazegenerator 2.0.2 to produce Pac-Man maze grids.
#
# Bitmask convention: bit SET = wall present on that side
#   bit 0 (1) N, bit 1 (2) E, bit 2 (4) S, bit 3 (8) W
#   15 = fully closed, 0 = fully open corridor

import collections
from typing import cast

from mazegenerator import MazeGenerator


# Bitmask constants — bit SET means wall present on that side
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
ALL_OPEN: int = 0    # no walls — fully open 4-way corridor
ALL_WALLS: int = 15  # walls on all sides — fully closed

# opposite direction bits for wall-opening
_OPPOSITE: dict[str, int] = {'N': SOUTH, 'S': NORTH, 'E': WEST, 'W': EAST}
_DELTA: dict[str, tuple[int, int]] = {
    'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1),
}


def generate_maze(width: int, height: int, seed: int = 0) -> list[list[int]]:
    """Generate a maze and return the bitmask grid."""
    try:
        gen = MazeGenerator(
            size=(width, height),
            perfect=False,   # MUST be False — creates loops for Pac-Man
            seed=seed,
        )
        maze = cast(list[list[int]], gen.maze)
        # knock open walls until every non-wall cell is reachable from center
        _connect_isolated_pockets(maze)
        return maze
    except Exception as e:
        raise RuntimeError(
            f"Maze generation failed (size={width}x{height}, seed={seed}): {e}"
        )


def _connect_isolated_pockets(grid: list[list[int]]) -> None:
    """Ensure every non-wall interior cell is reachable from the center.

    perfect=False mazes can leave isolated pockets — cells that aren't
    solid walls (cell != 15) but are completely surrounded by walls and
    cut off from the rest of the maze.  For each such pocket we find
    the nearest wall between it and the main connected component and
    knock it out, opening exactly one passage per pocket cell.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    cr, cc = rows // 2, cols // 2

    # keep going until no isolated cells remain
    while True:
        # BFS from center to find currently reachable cells
        reachable: set[tuple[int, int]] = set()
        q: collections.deque[tuple[int, int]] = collections.deque([(cr, cc)])
        reachable.add((cr, cc))
        while q:
            r, c = q.popleft()
            for d, (dr, dc) in _DELTA.items():
                if can_move(grid, r, c, d):
                    nr, nc = r + dr, c + dc
                    if (nr, nc) not in reachable:
                        reachable.add((nr, nc))
                        q.append((nr, nc))

        # collect all isolated non-wall interior cells
        isolated = []
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                if grid[r][c] != ALL_WALLS and (r, c) not in reachable:
                    isolated.append((r, c))

        if not isolated:
            break  # all cells connected

        # for each isolated cell, open one wall toward the nearest reachable
        # neighbour — use manhattan distance as a proxy, then knock out the wall
        opened_any = False
        for ir, ic in isolated:
            # find the direction toward the closest reachable cell
            best_dir = None
            best_dist = 999999
            for d, (dr, dc) in _DELTA.items():
                nr, nc = ir + dr, ic + dc
                if nr < 1 or nr >= rows - 1 or nc < 1 or nc >= cols - 1:
                    continue
                if grid[nr][nc] == ALL_WALLS:
                    continue  # solid logo block — skip
                dist = abs(nr - cr) + abs(nc - cc)
                # prefer directions toward a reachable neighbour
                if (nr, nc) in reachable:
                    dist -= 10000  # strongly prefer already-reachable neighbours
                if dist < best_dist:
                    best_dist = dist
                    best_dir = d

            if best_dir is None:
                continue

            dr, dc = _DELTA[best_dir]
            nr, nc = ir + dr, ic + dc
            # clear the wall bit on both sides
            bit_here = {'N': NORTH, 'S': SOUTH, 'E': EAST, 'W': WEST}[best_dir]
            bit_there = _OPPOSITE[best_dir]
            grid[ir][ic] &= ~bit_here
            grid[nr][nc] &= ~bit_there
            opened_any = True

        if not opened_any:
            break  # nothing left to open (shouldn't happen)


def is_wall(grid: list[list[int]], row: int, col: int) -> bool:
    """Return True if (row, col) is impassable."""
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    if row < 0 or row >= rows or col < 0 or col >= cols:
        return True

    cell = grid[row][col]

    # outer border = always wall
    if row == 0 or row == rows - 1 or col == 0 or col == cols - 1:
        return True

    # interior cell with all walls (15) = solid block (42 logo, etc.)
    return cell == ALL_WALLS


def can_move(grid: list[list[int]], row: int, col: int, direction: str) -> bool:
    """Return True if movement from (row, col) in direction is open."""
    mapping: dict[str, int] = {
        'N': NORTH, 'E': EAST, 'S': SOUTH, 'W': WEST,
    }
    if direction not in mapping:
        raise ValueError(f"Invalid direction '{direction}'. Use N, S, E, W.")

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    if row < 0 or row >= rows or col < 0 or col >= cols:
        return False

    cell = grid[row][col]
    bit = mapping[direction]
    if bool(cell & bit):
        return False  # wall on that side

    dr, dc = _DELTA[direction]
    dest_r, dest_c = row + dr, col + dc
    if (dest_r <= 0 or dest_r >= rows - 1
            or dest_c <= 0 or dest_c >= cols - 1):
        return False
    return True


def get_walkable_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    """All non-wall interior cells."""
    cells: list[tuple[int, int]] = []
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            if not is_wall(grid, row, col):
                cells.append((row, col))
    return cells


def get_center(grid: list[list[int]]) -> tuple[int, int]:
    """Maze center — that's where Pac-Man starts."""
    return len(grid) // 2, len(grid[0]) // 2


def get_corners(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return 4 corner-ish ghost spawn positions, guaranteed reachable.

    BFS from center, then picks nearest reachable cell to each corner
    with >=2 exits so ghosts can't get stuck.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    cr, cc = rows // 2, cols // 2

    reachable: set[tuple[int, int]] = set()
    q: collections.deque[tuple[int, int]] = collections.deque([(cr, cc)])
    reachable.add((cr, cc))
    while q:
        r, c = q.popleft()
        for d, (dr, dc) in _DELTA.items():
            if can_move(grid, r, c, d):
                nr, nc = r + dr, c + dc
                if (nr, nc) not in reachable:
                    reachable.add((nr, nc))
                    q.append((nr, nc))

    target_corners = [
        (1, 1), (1, cols - 2), (rows - 2, 1), (rows - 2, cols - 2),
    ]

    result = []
    for tr, tc in target_corners:
        best: tuple[int, int] = (cr, cc)
        best_dist = 999999
        for r, c in reachable:
            exits = sum(1 for d in _DELTA if can_move(grid, r, c, d))
            if exits < 2:
                continue
            dist = abs(r - tr) + abs(c - tc)
            if dist < best_dist:
                best_dist = dist
                best = (r, c)
        result.append(best)
    return result


def get_super_pacgum_positions(
    grid: list[list[int]],
) -> list[tuple[int, int]]:
    """Return positions for super-pacgums, offset from ghost corners."""
    corners = get_corners(grid)
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    center_r, center_c = rows // 2, cols // 2
    result = []
    for cr, cc in corners:
        dr = 1 if cr < center_r else -1
        dc = 1 if cc < center_c else -1
        best = (cr, cc)
        for step in range(1, 5):
            nr = cr + dr * step
            nc = cc + dc * step
            if (nr < 1 or nr >= rows - 1 or nc < 1 or nc >= cols - 1):
                break
            if any(can_move(grid, nr, nc, d) for d in _DELTA):
                best = (nr, nc)
                break
        result.append(best)
    return result
