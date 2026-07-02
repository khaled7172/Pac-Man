# Acceptance Test Plan

### Test 1: Configuration Robustness
- **Condition:** Load a heavily malformed `config.json` (Missing keys, string values for ints).
- **Result:** **PASS** — Values properly clamped, logged to standard out without tracebacks, game runs perfectly.

### Test 2: Maze Generation
- **Condition:** Execute `test_maze.py` directly, validating border limits and connectivity.
- **Result:** **PASS** — Grid generated correctly via assigned `.whl`. Edges handled natively.

### Test 3: Player Movement & Collisions
- **Condition:** Pass through ghosts head on. Pass through ghosts laterally.
- **Result:** **PASS** — Interpolated float collision securely detects collisions across boundary borders.

### Test 4: Super-Pacgum Eating
- **Condition:** Ensure Pac-Man eating ghosts correctly increases points and respawns them at base.
- **Result:** **PASS** — Visuals change, scoring increases, ghosts respawn.

### Test 5: Pausing & Menus
- **Condition:** Press ESC mid-play, navigate menu, resume play.
- **Result:** **PASS** — All timings securely frozen, UI operates independently.

### Test 6: Cheat Modes
- **Condition:** Activate all cheats iteratively to bypass gameplay requirements.
- **Result:** **PASS** — Invincibility, Ghost freeze, Speed Boost, Next Level toggle smoothly. HUD updates dynamically.
