from dataclasses import replace
from statistics import mean

from analytics.theory import mmc
from sim.engine import Params, generate_customers, simulate
from sim.strategies import STRATEGIES, get_strategy


def run(p, key):
    return simulate(generate_customers(p), p, get_strategy(key))


def test_deterministic_for_same_seed():
    p = Params()
    assert run(p, "shared").metrics == run(p, "shared").metrics


def test_different_seed_changes_result():
    assert run(Params(seed=1), "shared").metrics["avg_wait"] != run(Params(seed=2), "shared").metrics["avg_wait"]


def test_all_customers_served_and_waits_non_negative():
    p = Params()
    for key in STRATEGIES:
        r = run(p, key)
        assert r.metrics["served"] == p.n
        assert all(x.wait >= -1e-9 for x in r.customers)


def test_no_counter_serves_two_customers_at_once():
    p = Params()
    for key in STRATEGIES:
        by_counter = {}
        for x in run(p, key).customers:
            by_counter.setdefault(x.counter, []).append((x.start, x.start + x.svc))
        for spans in by_counter.values():
            spans.sort()
            assert all(spans[i][1] <= spans[i + 1][0] + 1e-9 for i in range(len(spans) - 1))


def test_flex_staff_only_used_by_flex_strategy():
    p = Params(flex=2)
    assert len(run(p, "baseline").utilisation) == p.c
    assert len(run(p, "priority_flex").utilisation) == p.c + 2


def test_shared_queue_beats_baseline_on_average():
    gains = []
    for s in range(20):
        p = Params(seed=100 + s)
        gains.append(run(p, "baseline").metrics["avg_wait"] - run(p, "shared").metrics["avg_wait"])
    assert mean(gains) > 0


def test_priority_customers_wait_less():
    p = Params(prio=20, seed=5)
    m = run(p, "priority_flex").metrics
    shared = run(p, "shared").metrics
    assert m["priority_wait"] < shared["priority_wait"]


def test_matches_erlang_c_theory():
    """Exponential service + constant arrivals + shared queue should approach M/M/c theory."""
    p = Params(n=20000, rate=36, svc=5, c=4, mult=1, dist="exponential", seed=3)  # rho = 0.75
    sim_wait = run(p, "shared").metrics["avg_wait"]
    theory = mmc(p.c, p.rate / 60, p.svc)["wq"]
    assert abs(sim_wait - theory) / theory < 0.15
