"""Staffing optimiser (member 2): smallest number of counters that meets a target mean wait.

Each candidate staffing level is averaged over `runs` random scenarios so one lucky seed cannot decide.
Extend: add P90 targets, cost per counter, or search regular + flex staff jointly.
"""
from dataclasses import replace
from statistics import mean

from .engine import generate_customers, simulate
from .strategies import get_strategy


def optimise(p, target_wait: float, max_counters: int = 12, strategy_key: str = "shared", runs: int = 10):
    rows = []
    for c in range(1, max_counters + 1):
        avgs, p90s = [], []
        for s in range(runs):
            q = replace(p, c=c, seed=p.seed + s)
            r = simulate(generate_customers(q), q, get_strategy(strategy_key)).metrics
            avgs.append(r["avg_wait"])
            p90s.append(r["p90_wait"])
        rows.append({"counters": c, "avg_wait": mean(avgs), "p90_wait": mean(p90s), "meets_target": mean(avgs) <= target_wait})
    rec = next((r for r in rows if r["meets_target"]), None)
    return {"strategy": strategy_key, "target_wait": target_wait, "runs_per_level": runs, "options": rows,
            "recommended_counters": rec["counters"] if rec else None,
            "achieved_wait": rec["avg_wait"] if rec else None}
