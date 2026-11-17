from fastapi import APIRouter, HTTPException

from analytics.validation import validate
from sim.optimiser import optimise
from sim.strategies import STRATEGIES

from .. import db
from ..schemas import OptimiseRequest, ValidateRequest
from .simulate import to_params

router = APIRouter(prefix="/api", tags=["optimisation"])


@router.post("/optimise")
def run_optimise(req: OptimiseRequest):
    if req.strategy not in STRATEGIES:
        raise HTTPException(400, f"Unknown strategy '{req.strategy}'")
    return optimise(to_params(req.params), req.target_wait, req.max_counters, req.strategy, req.runs)


@router.post("/validate")
def run_validate(req: ValidateRequest):
    bad = [k for k in (req.strategies or []) if k not in STRATEGIES]
    if bad:
        raise HTTPException(400, f"Unknown strategy: {', '.join(bad)}")
    return validate(to_params(req.params), req.runs, req.strategies)
