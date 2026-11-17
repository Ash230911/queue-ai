from fastapi import APIRouter, HTTPException

from analytics.theory import mmc
from sim.engine import Params, generate_customers, simulate
from sim.strategies import STRATEGIES, get_strategy

from .. import db
from ..schemas import ScenarioParams, SimulateRequest

router = APIRouter(prefix="/api", tags=["simulation"])


def to_params(sp: ScenarioParams) -> Params:
    return Params(**sp.model_dump())


def recommendation(best, base, p, theory, results):
    gain = (1 - best["avg_wait"] / base["avg_wait"]) * 100 if base["avg_wait"] else 0
    if best["key"] == "baseline":
        return "The baseline is already the best option for this scenario."
    txt = (f"Use '{best['name']}': average wait falls from {base['avg_wait']:.1f} to {best['avg_wait']:.1f} min "
           f"({gain:.0f}% lower) and the slowest 10% wait {best['p90_wait']:.1f} min instead of {base['p90_wait']:.1f}.")
    if best["staff_minutes"] > base["staff_minutes"] * 1.01:
        txt += f" It uses {best['staff_minutes'] - base['staff_minutes']:.0f} extra staff-minutes."
    if theory and not theory["stable"]:
        txt += " Average demand exceeds counter capacity, so add counters rather than only rearranging queues."
    return txt


@router.get("/defaults")
def defaults():
    return ScenarioParams().model_dump()


@router.get("/strategies")
def strategies():
    return [{"key": s.key, "name": s.name, "description": s.description, "dedicated": s.dedicated,
             "priority": s.priority, "uses_flex": s.uses_flex} for s in STRATEGIES.values()]


@router.post("/simulate")
def run_simulation(req: SimulateRequest):
    p = to_params(req.params)
    keys = req.strategies or list(STRATEGIES)
    bad = [k for k in keys if k not in STRATEGIES]
    if bad:
        raise HTTPException(400, f"Unknown strategy: {', '.join(bad)}. Available: {', '.join(STRATEGIES)}")
    keys = ["baseline"] + [k for k in keys if k != "baseline"]

    cust = generate_customers(p)
    results = [simulate(cust, p, get_strategy(k)) for k in keys]
    base = results[0].to_dict(series=False)
    rows = []
    for r in results:
        d = r.to_dict(series=False)
        d["improvement_pct"] = 0.0 if r.key == "baseline" else (1 - d["avg_wait"] / base["avg_wait"]) * 100 if base["avg_wait"] else 0.0
        rows.append(d)
    best = min(rows, key=lambda d: d["avg_wait"])

    lam = len(cust) / cust[-1].arr
    theory = mmc(p.c, lam, p.svc)
    warnings = []
    if not theory["stable"]:
        warnings.append(f"Average load is {theory['offered_load']:.1f} counters of work but only {p.c} counters are open: queues grow without bound.")

    out = {
        "params": req.params.model_dump(),
        "summary": rows,
        "series": {r.key: [[round(t, 2), q] for t, q in r.series] for r in results},
        "best": best["key"],
        "theory": theory,
        "recommendation": recommendation(best, base, p, theory, rows),
        "warnings": warnings,
        "data_note": "All customers are simulated.",
    }
    if req.save:
        sid = db.save_scenario(req.scenario_name or "Ad-hoc run", req.params.model_dump())
        out["scenario_id"] = sid
        out["run_ids"] = {r.key: db.save_run(sid, r.key, r.metrics, r.series, r.utilisation, r.busy) for r in results}
    return out
