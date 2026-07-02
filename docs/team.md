# Team Organization & Decisions

### Team Members
- **khhammou:** Core Game Loop, State Machine, Rendering Engine, Highscore Manager, Code Refactoring.
- **mkhanji:** Config Loader, Ghost AI, Maze Generator Integration, PyInstaller Packaging, UI Overlays.

### Key Architectural Decisions
1. **State Machine (`GameState`):** Decided to use an explicit `Enum` to control the flow between Main Menu, Pause, Playing, and Game Over. This solved our monolithic script issue and cleaned up event processing.
2. **Tile-Based Interpolation:** Decided to decouple logical grid positions from rendering coordinates. Entities move logic tile-by-tile but interpolate visually to maintain a smooth 60 FPS experience.
3. **Maze Generator Post-Processing:** Decided to use an `_open_random_walls` algorithm directly in `src/maze/loader.py` to create extra loops, maintaining fidelity to the original arcade Pac-Man which relies heavily on loop tactics.
4. **Collision Distance Check:** Decided to rely on a Float distance threshold (`0.8`) during interpolation to detect hits dynamically, solving the problem of Pac-Man pacing identically past ghosts between full tile ticks.
