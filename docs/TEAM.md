# Team ownership and first extensions

| # | Member | Own these files | First extensions |
|---|---|---|---|
| 1 | Simulation engine | `sim/engine.py` | Balking and reneging, counter breakdowns, time-varying arrival profile, service times per counter. Keep `tests/test_engine.py` green |
| 2 | Strategies and optimiser | `sim/strategies.py`, `sim/optimiser.py` | New strategy (shortest-job-first by visit type, skill-based routing), joint search over regular and flex staff, P90 target, cost per counter |
| 3 | Prediction and validation | `analytics/` | Estimator using per-visit-type means, regression model for waits, trained congestion model, error metrics by hour |
| 4 | Backend, DB, repo | `api/`, `db/`, `tests/test_api.py`, `run.sh` | Export CSV, pagination, Dockerfile, CI that runs pytest |
| 5 | Frontend core | `web/src/App.jsx`, `api.js`, `pages/Setup.jsx`, `pages/Live.jsx` | Scenario load/delete, input hints, playback pause, mobile layout |
| 6 | Charts, docs, slides | `web/src/pages/Compare.jsx`, `Forecast.jsx`, `Optimise.jsx`, `README.md` | Hour-by-hour heatmap, export chart as image, slides and demo script |

## Adding a strategy (5 minutes)
1. In `sim/strategies.py` subclass `Strategy` (or `SharedQueue`), set `key`, `name`, `description`.
2. Implement `route`, `pick`, `open_flex` or `close_flex` as needed.
3. Add the class to the `STRATEGIES` tuple. It appears in the API, tables, live view and validation automatically.
4. Add a colour for its key in `web/src/api.js` (`COLORS`).

## Git rules
Branch per member (`feat/engine`, `feat/strategies`, `feat/api`, `feat/ui`...), small PRs into `dev`, merge `dev` into `main` only when `python -m pytest -q` passes.
