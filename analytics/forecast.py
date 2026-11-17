"""Congestion forecasting (member 3).

Rule: load = (arrivals in the last `window` min * mean service) / counters. A window is a WARNING
when load >= threshold. Ground truth: the baseline queue reaches `counters` within the next `window` min.
Extend: replace the rule with a regression / gradient-boosting model trained on simulated runs.
"""


def congestion_forecast(customers, series, p, window=15, step=5, threshold=0.85):
    horizon = series[-1][0]
    out, t = [], window
    while t < horizon:
        lam = sum(1 for x in customers if t - window < x.arr <= t) / window
        load = lam * p.svc / p.c
        peak = max((q for ts, q in series if t < ts <= t + window), default=0)
        out.append({"t": t, "load": load, "warning": load >= threshold, "actual": peak >= p.c})
        t += step
    warn = [w for w in out if w["warning"]]
    act = [w for w in out if w["actual"]]
    tp = sum(1 for w in warn if w["actual"])
    return {
        "windows": out,
        "threshold": threshold,
        "precision": tp / len(warn) if warn else None,
        "recall": tp / len(act) if act else None,
        "first_warning": warn[0]["t"] if warn else None,
        "warning_count": len(warn),
    }
