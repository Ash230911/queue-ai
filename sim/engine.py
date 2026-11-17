"""Discrete-event simulation engine (member 1).

Time unit: minutes. Deterministic for a given Params.seed. Every strategy is run on the SAME
generated customers so comparisons are fair (common random numbers).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

from analytics.estimator import estimate_wait

KINDS = [("quick", 0.5, 0.5), ("standard", 0.35, 1.0), ("complex", 0.15, 2.0)]  # name, probability, service multiplier
INF = float("inf")


@dataclass
class Params:
    n: int = 150          # customers
    rate: float = 40      # base arrivals per hour
    svc: float = 6        # mean service time (min)
    cv: float = 0.8       # service-time variability (coefficient of variation)
    c: int = 5            # regular counters
    flex: int = 1         # extra flex counters (used by flex strategies)
    prio: float = 15      # % priority customers
    mult: float = 2       # arrival-rate multiplier during the surge
    s0: float = 40        # surge start (min)
    sl: float = 30        # surge length (min)
    seed: int = 7
    dist: str = "lognormal"  # or "exponential" (used to validate against M/M/c theory)
    sla: float = 10       # wait threshold (min) for the "over SLA" metric


@dataclass
class Customer:
    id: int
    arr: float
    svc: float
    pri: bool
    kind: str
    start: float = 0.0
    wait: float = 0.0
    counter: int = -1
    pred: float = 0.0


@dataclass
class Counter:
    id: int
    open: bool
    cur: Customer | None = None
    end: float = 0.0
    busy: float = 0.0
    queue: list = field(default_factory=list)
    since: float = 0.0
    open_time: float = 0.0


@dataclass
class SimState:
    t: float
    counters: list
    pool: list
    mean_service: float
    params: Params
    dedicated: bool

    def queue_len(self) -> int:
        return sum(len(c.queue) for c in self.counters) if self.dedicated else len(self.pool)


@dataclass
class RunResult:
    key: str
    name: str
    metrics: dict
    utilisation: list
    busy: list
    series: list
    customers: list
    timeline: list

    def to_dict(self, series=True):
        d = {"key": self.key, "name": self.name, **self.metrics, "counter_utilisation": self.utilisation}
        if series:
            d["series"] = [[round(t, 3), q] for t, q in self.series]
        return d


def generate_customers(p: Params) -> list[Customer]:
    rng = np.random.default_rng(p.seed)
    norm = sum(w * m for _, w, m in KINDS)
    sg = math.sqrt(math.log(1 + p.cv ** 2))
    t, out = 0.0, []
    for i in range(p.n):
        lam = p.rate / 60 * (p.mult if p.s0 <= t < p.s0 + p.sl else 1)  # piecewise-constant approximation of a non-homogeneous Poisson process
        t += rng.exponential(1 / lam)
        if p.dist == "exponential":
            kind, svc = "standard", max(0.01, rng.exponential(p.svc))
        else:
            u, acc, kind, m = rng.random(), 0.0, KINDS[-1][0], KINDS[-1][2]
            for k, w, mm in KINDS:
                acc += w
                if u < acc:
                    kind, m = k, mm
                    break
            svc = max(0.3, p.svc * m / norm * math.exp(sg * rng.normal() - sg * sg / 2))
        out.append(Customer(i, t, svc, bool(rng.random() < p.prio / 100), kind))
    return out


def simulate(customers: list[Customer], p: Params, strategy, timeline: bool = False) -> RunResult:
    X = [replace(x) for x in customers]
    n_total = p.c + (p.flex if strategy.uses_flex else 0)
    C = [Counter(i, open=i < p.c) for i in range(n_total)]
    st = SimState(0.0, C, [], p.svc, p, strategy.dedicated)  # estimator uses the nominal historical mean, not future data
    strategy.reset()
    i = t = prev = area = 0.0
    i = 0
    peak, done, series, frames = 0, [], [(0.0, 0)], []

    while i < len(X) or any(c.cur for c in C):
        na = X[i].arr if i < len(X) else INF
        nd = min((c.end for c in C if c.cur), default=INF)
        tn = min(na, nd)
        area += st.queue_len() * (tn - prev)
        prev = t = tn
        st.t = t
        if na <= nd:
            x = X[i]
            i += 1
            if strategy.dedicated:
                b = strategy.route(st, x)
                x.pred = estimate_wait(st, x, strategy, b)
                C[b].queue.append(x)
            else:
                x.pred = estimate_wait(st, x, strategy)
                st.pool.append(x)
        else:
            for c in C:
                if c.cur and c.end <= t + 1e-9:
                    done.append(c.cur)
                    c.cur = None
        strategy.open_flex(st)
        for c in C:
            if c.cur or not c.open:
                continue
            if strategy.dedicated:
                x = c.queue.pop(0) if c.queue else None
            else:
                x = st.pool.pop(strategy.pick(st)) if st.pool else None
            if x:
                x.start, x.wait, x.counter = t, t - x.arr, c.id
                c.cur, c.end = x, t + x.svc
                c.busy += x.svc
        strategy.close_flex(st)
        q = st.queue_len()
        peak = max(peak, q)
        series.append((t, q))
        if timeline:
            frames.append({"t": t, "queue": q, "pool": len(st.pool), "served": len(done),
                           "counters": [{"open": c.open, "busy": c.cur is not None, "q": len(c.queue)} for c in C]})

    for c in C:
        if c.open:
            c.open_time += t - c.since
    waits = np.array([x.wait for x in done])
    staff = sum(c.open_time for c in C)
    pri_w = [x.wait for x in done if x.pri]
    metrics = {
        "avg_wait": float(waits.mean()),
        "p90_wait": float(np.percentile(waits, 90)),
        "max_wait": float(waits.max()),
        "priority_wait": float(np.mean(pri_w)) if pri_w else 0.0,
        "pct_over_sla": float((waits > p.sla).mean() * 100),
        "avg_queue": area / t if t else 0.0,
        "peak_queue": int(peak),
        "utilisation": sum(c.busy for c in C) / staff if staff else 0.0,
        "staff_minutes": staff,
        "est_error": float(np.mean([abs(x.pred - x.wait) for x in done])),
        "makespan": t,
        "served": len(done),
    }
    return RunResult(strategy.key, strategy.name, metrics,
                     [c.busy / c.open_time if c.open_time else 0.0 for c in C],
                     [c.busy for c in C], series, done, frames)
