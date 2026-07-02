# Risk Analysis

| Risk | Impact | Probability | Mitigation Strategy |
|---|---|---|---|
| External `.whl` package is re-installed during review | **High** | High | Never modify the `mazegenerator` code directly. Translate outputs locally in `src/maze/loader.py` to decouple dependencies. |
| Invalid Config inputs break the game | **High** | Medium | Utilize a strict JSON parser with fallback ranges/clamps and safe default mapping. Use `try/except` for IO. |
| `mypy` strict type-checking failures | **Medium** | Low | Introduce strict typing annotations globally early in the project. Resolve all `flake8` warnings systematically. |
| Overpowered Ghost AI frustrates players | **Medium** | High | Integrate a 20-40% chance of random direction selection based on Ghost color to dilute perfect BFS tracking. |
| Large mazes overflow display boundaries | **Low** | Medium | Auto-calculate the PyGame window dimensions directly from the loaded config's level rows/cols properties. |
| Exact tile collision ignores high-speed passing | **High** | High | Swap strict tile coordinate matching with interpolated Float distance proximity logic (e.g., `dist < 0.8`). |
