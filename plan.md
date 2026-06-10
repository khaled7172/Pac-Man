# 🎮 Pac-Man Project — Full Plan

---

## 📖 Subject Breakdown: What's Allowed & What's Not

### ✅ ALLOWED

| Category | Details |
|---|---|
| Language | Python 3.10+ only |
| Graphics | Any simple graphical library (pygame, arcade, pyglet, tkinter canvas, etc.) |
| Maze gen | The **assigned A-Maze-ing .whl package** from another group — use it as-is |
| Config | JSON file with `#` comment support (and optionally C/C++ styles) |
| Highscore | JSON file on disk — any format you design |
| AI tools | Allowed for productivity, but you must understand every line you submit |
| Package manager | pip, uv, pipx — your choice |
| Virtual env | Strongly recommended (venv, conda) |
| Test framework | pytest or unittest (not graded, but expected) |
| Platform deploy | Steam or Itch.io (free, unlisted/private build is fine) |

### ❌ NOT ALLOWED

| Category | Details |
|---|---|
| Maze generator | You **cannot write your own** — must use the assigned package |
| Modifying assigned pkg | The `.whl` must be used **unmodified**; it will be re-installed during peer review |
| Python < 3.10 | Hard requirement |
| Crashes / tracebacks | Any unhandled exception = project considered non-functional |
| Skipping type hints | All functions need type annotations; must pass `mypy` |
| Missing docstrings | PEP 257 required on all functions and classes |
| Flake8 violations | Code must be flake8-clean |
| Missing Makefile rules | `install`, `run`, `debug`, `clean`, `lint` are all mandatory |
| Missing README sections | All listed sections are mandatory |

### ⚠️ GREY AREAS / WATCH OUT

- Config keys have **suggested names** — you can rename them but must document in README
- Ghost AI behavior is **up to you** (distance-based, BFS, random — your call)
- Time limit expiry behavior is **up to you** (restart level, end game, etc.)
- Highscore storage format is **up to you** but must be JSON, robust, and documented
- Cheat mode features are **suggested** — implement what genuinely helps a reviewer test everything

---

## 🔧 How to Use the Assigned `.whl` Package

The maze generator comes as a `.whl` file from another group (A-Maze-ing project).

### Installation
```bash
pip install path/to/amazeing_package.whl
```
Or add it to your `Makefile`'s `install` rule:
```makefile
install:
    pip install -r requirements.txt
    pip install vendor/amazeing_package.whl
```
Store the `.whl` in a `vendor/` directory at your project root so the reviewer can reinstall it.

### How It Works (Based on the Subject)
- The package generates mazes
- You **must set `PERFECT=False`** when calling it — this creates corridors compatible with Pac-Man (loops, not just a perfect maze tree)
- Your code must **adapt to their interface** — read their package's API, not the other way around
- If the generator fails (exception), catch it cleanly and handle it gracefully

### Example Integration Pattern
```python
# src/maze/loader.py
try:
    from amazeing import MazeGenerator  # adapt to their actual import name
    
    def generate_maze(width: int, height: int, seed: int | None = None) -> list[list[int]]:
        """Generate a maze using the assigned A-Maze-ing package."""
        gen = MazeGenerator(width=width, height=height, seed=seed, PERFECT=False)
        return gen.generate()
except ImportError as e:
    raise RuntimeError(f"A-Maze-ing package not installed: {e}")
except Exception as e:
    raise RuntimeError(f"Maze generation failed: {e}")
```

**First thing to do when you receive the `.whl`:**
1. `pip install amazeing_package.whl`
2. `python -c "import amazeing; help(amazeing)"` — read the actual API
3. Adjust your loader to match their exact interface

---

## 🏗️ Project Structure

```
pac-man/
│
├── pac-man.py                  # Entry point — parses args, loads config, launches game
├── config.json                 # Default config file (provided as example)
├── highscores.json             # Runtime file (gitignored or initialized empty)
├── requirements.txt            # All pip dependencies
├── Makefile                    # install / run / debug / clean / lint
├── .gitignore                  # __pycache__, .mypy_cache, *.pyc, venv/, etc.
├── README.md                   # Full mandatory README
│
├── vendor/                     # The assigned .whl maze generator
│   └── amazeing_package.whl
│
├── assets/                     # Sprites, sounds, fonts
│   ├── sprites/
│   │   ├── pacman/
│   │   ├── ghosts/
│   │   └── tiles/
│   ├── sounds/
│   └── fonts/
│
├── src/                        # All source modules
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py           # Parses JSON+comments config, validates, applies defaults
│   │
│   ├── maze/
│   │   ├── __init__.py
│   │   └── loader.py           # Wraps the assigned A-Maze-ing package
│   │
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── player.py           # Pac-Man: movement, lives, score, respawn
│   │   ├── ghost.py            # Ghost base class: movement, AI, edible state
│   │   └── pellet.py           # Pacgum + Super-pacgum
│   │
│   ├── game/
│   │   ├── __init__.py
│   │   ├── game.py             # Core game loop, level management, collision detection
│   │   ├── level.py            # Level: maze + entities + pacgums + timer
│   │   └── scoring.py          # Score tracking and combo logic
│   │
│   ├── highscore/
│   │   ├── __init__.py
│   │   └── manager.py          # Load/save/display top-10 highscores
│   │
│   └── ui/
│       ├── __init__.py
│       ├── renderer.py         # All drawing logic (decoupled from game logic)
│       ├── menu.py             # Main menu, pause menu, game-over, victory screens
│       └── hud.py              # In-game HUD: score, lives, level, timer
│
├── docs/                       # Project management documents
│   ├── gantt.md                # Timeline / Gantt chart
│   ├── progress.md             # Actual progress vs. planned
│   ├── risks.md                # Risk analysis
│   ├── team.md                 # Who did what
│   └── acceptance_tests.md     # Feature test plan
│
└── packaging/
    ├── build.sh                # Script to package for Itch.io / Steam
    └── pac-man.spec            # PyInstaller spec (or equivalent)
```

---

## 🗺️ Phases

---

### Phase 0 — Setup & Foundations
**Goal:** Everyone can run a window. Infrastructure is solid.

- [ ] Initialize Git repo with proper `.gitignore`
- [ ] Set up virtual environment (`venv`)
- [ ] Write `requirements.txt` (pygame or chosen lib, mypy, flake8)
- [ ] Write `Makefile` with all 5 required rules (`install`, `run`, `debug`, `clean`, `lint`)
- [ ] Create project directory structure as above
- [ ] Write skeleton `pac-man.py` entry point (accepts one arg: config path)
- [ ] Write `src/config/loader.py`:
  - Strip `#` comment lines before JSON parsing
  - Validate all keys, apply safe defaults for missing/invalid ones
  - Log warnings instead of crashing
- [ ] Verify `mypy` + `flake8` pass on skeleton code
- [ ] Create empty `README.md` with all required section headers

**Deliverable:** `python3 pac-man.py config.json` runs without crash, prints loaded config.

---

### Phase 1 — Maze Generation Integration
**Goal:** Display a generated maze on screen.

- [ ] Receive and install the assigned `.whl` package
- [ ] Read their API (`help()`, source if available)
- [ ] Write `src/maze/loader.py` adapting to their interface (`PERFECT=False`)
- [ ] Handle all exceptions from the generator cleanly
- [ ] Represent maze as a 2D grid (`list[list[int]]` or `list[list[Cell]]`)
- [ ] Write `src/ui/renderer.py` to draw walls vs corridors
- [ ] Test with seed=42 (fixed first level) and random seeds (subsequent levels)

**Deliverable:** A maze appears in the window, drawn from the assigned generator.

---

### Phase 2 — Player & Basic Movement
**Goal:** Pac-Man moves around the maze, constrained by walls.

- [ ] Write `src/entities/player.py`:
  - Position, direction, speed
  - Input handling (arrow keys + WASD)
  - Wall collision (can only enter corridor cells)
  - Buffered input (queue next direction while moving)
- [ ] Integrate player rendering into `renderer.py`
- [ ] Player starts in the center of the maze
- [ ] Lives system (starts at 3, configurable)
- [ ] Respawn to center on ghost collision (no ghost yet = test manually)

**Deliverable:** Pac-Man moves smoothly through corridors, can't walk through walls.

---

### Phase 3 — Pellets & Scoring
**Goal:** Dots appear, eating them scores points.

- [ ] Write `src/entities/pellet.py`:
  - `Pacgum` (small dot, +X points)
  - `SuperPacgum` (large dot in 4 corners, +Y points, triggers edible state)
- [ ] Populate maze corridors with pacgums at level start
- [ ] Place super-pacgums in the 4 corners
- [ ] Write `src/game/scoring.py` — track score, expose methods to add points
- [ ] Collision detection: player eats pellet → remove it, add score
- [ ] Level win condition: all pacgums eaten → advance to next level
- [ ] Write `src/ui/hud.py` — display score, lives, level, timer

**Deliverable:** Dots disappear when eaten, score updates on HUD, level ends when all eaten.

---

### Phase 4 — Ghosts
**Goal:** 4 ghosts move, chase, and kill Pac-Man.

- [ ] Write `src/entities/ghost.py`:
  - Base movement through corridors (BFS chase or random walk — your choice)
  - Chase mode: move toward player
  - Flee mode (edible): move away from player
  - Edible state: triggered by super-pacgum, timed
  - Eaten state: respawn to corner after N seconds
- [ ] 4 ghost instances, one per corner at level start
- [ ] Collision: ghost touches player → lose a life, respawn player
- [ ] Collision: player touches edible ghost → +Z points, ghost enters eaten state
- [ ] Ghost visual: different colors, flash when edible time is almost up

**Deliverable:** Ghosts chase you, eating a power pellet makes them flee, eating a ghost scores points.

---

### Phase 5 — Game Loop & Level Progression
**Goal:** Full game flow from level 1 to level 10+.

- [ ] Write `src/game/level.py` — encapsulates one level's state
- [ ] Write `src/game/game.py` — manages level sequence, lives between levels, timer
- [ ] Level timer (default 90s): configurable expiry behavior (e.g., lose a life)
- [ ] Player keeps score and lives across levels
- [ ] At least 10 levels configured in `config.json`
- [ ] Level 1 = seed 42, levels 2+ = random seeds
- [ ] Pause/resume functionality (P key or ESC)
- [ ] Game over when all lives lost
- [ ] Victory when all levels complete

**Deliverable:** You can play all 10 levels start to finish (or die trying).

---

### Phase 6 — Menus & UI Screens
**Goal:** Full polished UI flow as specified.

- [ ] Write `src/ui/menu.py`:
  - **Main Menu**: Start Game, View Highscores, Instructions, Exit
  - **Pause Menu**: Resume, Return to Main Menu
  - **Game Over Screen**: final score + name entry prompt
  - **Victory Screen**: final score + congratulatory message + name entry prompt
- [ ] Name entry: max 10 chars, alphanumeric + spaces only, validated
- [ ] After name entry → save highscore → return to main menu

**Deliverable:** Complete game loop: Menu → Game → Win/Lose → Name Entry → Menu.

---

### Phase 7 — Highscore System
**Goal:** Persistent top-10 leaderboard.

- [ ] Write `src/highscore/manager.py`:
  - Load from `highscores.json` at game start
  - Save to `highscores.json` at game end
  - Keep only top 10 entries
  - Validate player name (10 chars, alphanumeric + spaces)
  - Handle missing/corrupt file gracefully (start fresh)
- [ ] Display highscores in main menu
- [ ] Document format in README

**Deliverable:** Scores persist across sessions, top 10 displayed correctly.

---

### Phase 8 — Cheat Mode
**Goal:** Reviewer can test everything quickly.

Implement cheat features (toggle via keyboard shortcuts):

- [ ] **Invincibility** (`I`): ghosts can't kill the player
- [ ] **Level Skip** (`N`): immediately complete current level
- [ ] **Ghost Freeze** (`F`): ghosts stop moving
- [ ] **Extra Life** (`L`): add 1 life
- [ ] **Speed Boost** (`S`): player moves 2x faster
- [ ] Display active cheats on HUD
- [ ] Document all cheat keys in README and Instructions screen

**Deliverable:** Reviewer can toggle any feature to test it in isolation.

---

### Phase 9 — Code Quality Pass
**Goal:** Zero mypy errors, zero flake8 warnings.

- [ ] Add/verify type hints on all functions and variables
- [ ] Add/verify docstrings (Google or NumPy style) on all functions and classes
- [ ] Run `make lint` — fix all issues
- [ ] Run mypy with `--warn-return-any --warn-unused-ignores --disallow-untyped-defs --check-untyped-defs`
- [ ] Write/complete unit tests (pytest) for config loader, highscore manager, maze loader
- [ ] Test edge cases: invalid config, missing highscore file, generator failure

**Deliverable:** `make lint` is clean. Core modules have unit tests.

---

### Phase 10 — Packaging & Deployment
**Goal:** Game runs as a standalone executable on Itch.io.

- [ ] Write `packaging/build.sh` using PyInstaller (or Nuitka):
  ```bash
  pyinstaller --onefile --windowed pac-man.py --add-data "assets:assets"
  ```
- [ ] Test the built executable on a clean machine (no Python installed)
- [ ] Create Itch.io page (free, unlisted/private)
- [ ] Upload build with minimal instructions (controls, config)
- [ ] Store `.spec` file and `build.sh` in `packaging/` at repo root

**Deliverable:** Game is live on Itch.io, installable without Python.

---

### Phase 11 — Project Management Docs & README
**Goal:** All mandatory documentation complete.

- [ ] Complete `README.md` with ALL required sections:
  - Italicized first line with login(s)
  - Description, Instructions, Resources
  - Configuration, Highscore, Maze Generation, Implementation
  - General Software Architecture, Project Management
- [ ] Fill `docs/`:
  - `gantt.md` — timeline vs. actual
  - `progress.md` — progress tracking
  - `risks.md` — risks and mitigations
  - `team.md` — who did what
  - `acceptance_tests.md` — feature-by-feature test results

**Deliverable:** Repo is reviewer-ready. Nothing missing.

---

## 🗓️ Suggested Timeline (2-person team, ~4 weeks)

| Week | Phases | Focus |
|---|---|---|
| Week 1 | 0, 1, 2 | Setup, maze generation, player movement |
| Week 2 | 3, 4 | Pellets/scoring, ghost AI |
| Week 3 | 5, 6, 7 | Game loop, menus, highscores |
| Week 4 | 8, 9, 10, 11 | Cheat mode, code quality, packaging, docs |

---

## 📋 Config File Example

```json
{
    # Highscore file location
    "highscore_filename": "highscores.json",
    
    # Number of starting lives
    "lives": 3,
    
    # Points per pellet type
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,
    
    # Time limit per level in seconds
    "level_max_time": 90,
    
    # Ghost edible duration in seconds
    "ghost_edible_duration": 8,
    
    # Ghost respawn delay in seconds
    "ghost_respawn_delay": 5,
    
    # Level definitions
    "levels": [
        {"width": 21, "height": 21, "seed": 42, "pacgum_count": 80},
        {"width": 21, "height": 21, "seed": null, "pacgum_count": 80},
        {"width": 25, "height": 25, "seed": null, "pacgum_count": 100}
    ]
}
```

---

## 🔑 Key Technical Decisions to Make Early

1. **Graphics library**: Pygame is the safest bet — huge community, stable, well-documented. Arcade is also good.
2. **Ghost AI strategy**: Start with random corridor walk, upgrade to BFS pathfinding if time allows.
3. **Tile size**: 32px per tile is comfortable for a 21×21 maze (672×672 px game area).
4. **Game state machine**: Use an explicit state enum (`MENU`, `PLAYING`, `PAUSED`, `GAME_OVER`, `VICTORY`) to control the main loop cleanly.
5. **Time limit expiry**: Simplest = lose a life, restart level. Easiest for reviewer to observe.

---

## ⚡ Critical Path (Things That Can Block You)

1. **Getting the `.whl` from the other group** — do this on Day 1. You can't build without it.
2. **Reading their actual API** — don't assume anything about the interface.
3. **Packaging** — PyInstaller can be tricky. Test it early, not the last day.
4. **mypy compliance** — much easier if you write type hints from the start, not at the end.