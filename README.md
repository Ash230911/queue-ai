# Queue Lab: Intelligent Queue Prediction and Service Allocation

**BuildX 0.1, Challenge 10.** Team identifier: `<TEAM-ID>` (replace before submission)

## Problem
Service desks in universities, hospitals and government offices see uneven demand. Queue numbers alone do not fix long waits; resources must be allocated well and congestion predicted early.

## Solution
A discrete-event simulator generates customer arrivals (with a surge), runs **four allocation strategies on identical customers**, estimates waiting times, forecasts congestion, recommends a strategy and finds the smallest staffing level that meets a wait target. Every result is compared with a **baseline** and checked over 30 random scenarios.

## Tech stack
Python 3.10+, FastAPI, Pydantic, NumPy, SQLite, WebSocket. Frontend: React 18, Vite, Recharts. Tests: pytest.

## Architecture
```
web (React)  --REST/WebSocket-->  api (FastAPI)  -->  sim (engine, strategies, optimiser)
                                       |            -->  analytics (estimator, forecast, theory, validation)
                                       +--> SQLite (scenarios, runs, series, counter stats, validations)
```
| Folder | What it holds |
|---|---|
| `sim/` | `engine.py` event simulation, `strategies.py` allocation strategies, `optimiser.py` staffing search |
| `analytics/` | wait estimator, congestion forecast, M/M/c theory, 30-scenario validation |
| `api/` | routes, request validation, DB layer, config, WebSocket live feed |
| `db/schema.sql` | database schema |
| `web/` | React website (5 pages) |
| `tests/` | engine and API tests |

## Install and run
```bash
# one command (Linux/macOS): installs, builds the website, starts on http://localhost:8000
./run.sh
```
Manual:
```bash
python3 -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn api.main:app --reload                          # API + docs at http://localhost:8000/docs
cd web && npm install && npm run dev                   # website at http://localhost:5173 (proxies to :8000)
cd web && npm run build                                # then the API serves the website on :8000
```
Tests: `python -m pytest -q`

## API
| Endpoint | Purpose |
|---|---|
| `POST /api/simulate` | Run all strategies on one scenario. `save: true` stores it |
| `POST /api/forecast` | Congestion windows, precision, recall |
| `POST /api/optimise` | Fewest counters that meet a target wait |
| `POST /api/validate` | Repeat over N seeds with 95% confidence intervals |
| `GET/POST/DELETE /api/scenarios`, `GET /api/runs/{id}` | Save and reload |
| `GET /api/strategies`, `/api/defaults`, `/api/health` | Metadata |
| `WS /ws/live` | Live frames for the animation |

## Dataset and API information
**All data is simulated.** Arrivals: Poisson process with a piecewise-constant surge. Service times: lognormal with three visit types (quick, standard, complex). Results are not real-world findings. No external APIs are used, so the demo works offline.

## Validation
- Engine matches the Erlang C (M/M/c) formula within 15% on a long exponential-service run (`tests/test_engine.py`).
- Same seed gives the same results; no counter serves two customers at once; all customers are served.
- 30-scenario validation reports mean wait, 95% CI and how often each strategy beats the baseline.

## Known limitations
- The surge is modelled with a piecewise rate, not a fitted model of real arrivals.
- The forecast is a rule on recent arrival rate, not a trained model.
- Customers never balk, renege or switch queues; counters never break down.
- The 95% CI uses the normal approximation.
- Baseline (round-robin fixed queues) is a simplification of real behaviour.
