"""Multi-scenario validation (member 3): reruns the same settings with many seeds and reports mean +/- 95% CI."""
from dataclasses import replace
from math import sqrt
from statistics import mean, stdev

from sim.engine import generate_customers, simulate
from sim.strategies import STRATEGIES, get_strategy


def validate(p, runs: int = 30, keys=None, base_seed: int = 1000):
    keys = keys or list(STRATEGIES)
    if "baseline" not in keys:
        keys = ["baseline", *keys]
    avg = {k: [] for k in keys}
    for s in range(runs):
        q = replace(p, seed=base_seed + s)
        cu = generate_customers(q)
        for k in keys:
            avg[k].append(simulate(cu, q, get_strategy(k)).metrics["avg_wait"])
    rows = []
    for k in keys:
        m = mean(avg[k])
        sd = stdev(avg[k]) if runs > 1 else 0.0
        imp = mean(1 - a / b if b else 0 for a, b in zip(avg[k], avg["baseline"])) * 100
        wins = sum(1 for a, b in zip(avg[k], avg["baseline"]) if a < b) / runs
        rows.append({"key": k, "name": STRATEGIES[k].name, "mean_wait": m, "sd": sd, "ci95": 1.96 * sd / sqrt(runs),
                     "mean_improvement_pct": imp if k != "baseline" else 0.0, "win_rate": wins if k != "baseline" else None})
    return {"runs": runs, "strategies": rows}
