"""src/ui/sprite_loader.py — Loads and slices all sprite sheets.

All sprites are 16x16px frames packed horizontally in a 128x16 PNG.
Frames are sliced, scaled to tile_size, and rotated as needed.

PacMan.png frame layout:
    0-3  : death animation
    4    : mouth open       (facing right)
    5    : mouth closed
    6    : mouth wide open
    7    : mouth closed

Ghost*.png frame layout:
    0-1  : walk cycle (use alternating)
    rest : duplicates — ignored

Coin.png frame layout (used for super-pacgum blink):
    0-2  : face-on
    3-4  : edge-on (thin)
    5-7  : face-on again
"""

import os
import pygame

FRAME_SIZE: int = 16          # native px per frame
PAC_ANIM_FRAMES: list[int] = [6, 4, 5]   # wide open -> open -> closed
PAC_DEATH_FRAMES: list[int] = [0, 1, 2, 3]
GHOST_WALK_FRAMES: list[int] = [0, 1]
COIN_FRAMES: list[int] = [0, 1, 2, 3, 4, 5, 6, 7]

# Rotation per direction (pygame rotates counter-clockwise)
DIR_ROTATION: dict[str, float] = {
    "E": 0.0,
    "W": 180.0,
    "N": 90.0,
    "S": 270.0,
}


def _slice_sheet(
    path: str,
    frame_indices: list[int],
    tile_size: int,
) -> list[pygame.Surface]:
    """Slice a horizontal sprite sheet into individual scaled surfaces.

    Args:
        path:          Path to the PNG sprite sheet.
        frame_indices: Which frame indices to extract.
        tile_size:     Target size to scale each frame to.

    Returns:
        List of scaled pygame Surfaces in the order of frame_indices.
    """
    sheet = pygame.image.load(path).convert_alpha()
    frames: list[pygame.Surface] = []
    for i in frame_indices:
        region = pygame.Rect(i * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE)
        frame = pygame.Surface((FRAME_SIZE, FRAME_SIZE), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), region)
        scaled = pygame.transform.scale(frame, (tile_size, tile_size))
        frames.append(scaled)
    return frames


def load_pacman_sprites(
    asset_root: str,
    tile_size: int,
) -> dict[str, list[pygame.Surface]]:
    """Load Pac-Man movement and death sprites for all directions.

    Args:
        asset_root: Root assets directory.
        tile_size:  Target tile size in pixels.

    Returns:
        Dict with keys:
            'E', 'W', 'N', 'S' -> list of 3 movement frames
            'death'             -> list of 4 death frames
    """
    path = os.path.join(asset_root, "sprites", "PacMan.png")
    base = _slice_sheet(path, PAC_ANIM_FRAMES, tile_size)
    death = _slice_sheet(path, PAC_DEATH_FRAMES, tile_size)

    sprites: dict[str, list[pygame.Surface]] = {"death": death}

    sprites["E"] = base
    sprites["W"] = [
        pygame.transform.flip(f, True, False) for f in base
    ]
    sprites["N"] = [
        pygame.transform.rotate(f, 90.0) for f in base
    ]
    sprites["S"] = [
        pygame.transform.rotate(f, -90.0) for f in base
    ]

    return sprites


def load_ghost_sprites(
    asset_root: str,
    tile_size: int,
) -> dict[str, list[pygame.Surface]]:
    """Load ghost walk sprites for all colours including edible states.

    Args:
        asset_root: Root assets directory.
        tile_size:  Target tile size in pixels.

    Returns:
        Dict mapping colour name to list of 2 walk-cycle frames.
        Keys: 'red', 'pink', 'cyan', 'orange', 'blue', 'white'
        'blue'  = edible state
        'white' = edible flashing state (uses yellowGhost)
    """
    colour_files: dict[str, str] = {
        "red": "redGhost.png",
        "pink": "pinkGhost.png",
        "cyan": "blueGhost.png",
        "orange": "orangeGhost.png",
        "blue": "blueGhost.png",
        "white": "yellowGhost.png",
    }

    sprites: dict[str, list[pygame.Surface]] = {}
    for name, filename in colour_files.items():
        path = os.path.join(asset_root, "sprites", filename)
        if os.path.exists(path):
            sprites[name] = _slice_sheet(path, GHOST_WALK_FRAMES, tile_size)
        else:
            # Fallback to red ghost if file missing
            fallback = os.path.join(asset_root, "sprites", "redGhost.png")
            sprites[name] = _slice_sheet(
                fallback, GHOST_WALK_FRAMES, tile_size)

    return sprites


def load_coin_sprites(
    asset_root: str,
    tile_size: int,
    big: bool = False,
) -> list[pygame.Surface]:
    """Load coin spin animation frames.

    Args:
        asset_root: Root assets directory.
        tile_size:  Target tile size in pixels.
        big:        If True load BigCoin.png, else Coin.png.

    Returns:
        List of 8 animation frames.
    """
    filename = "BigCoin.png" if big else "Coin.png"
    path = os.path.join(asset_root, "sprites", filename)
    return _slice_sheet(path, COIN_FRAMES, tile_size)
