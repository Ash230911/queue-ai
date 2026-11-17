from fastapi import APIRouter

from analytics.forecast import congestion_forecast
from sim.engine import generate_customers, simulate
from sim.strategies import get_strategy

from ..schemas import ForecastRequest
from .simulate import to_params

router = APIRouter(prefix="/api", tags=["forecast"])


@router.post("/forecast")
def forecast(req: ForecastRequest):
    p = to_params(req.params)
    cust = generate_customers(p)
    base = simulate(cust, p, get_strategy("baseline"))
    return congestion_forecast(cust, base.series, p, window=req.window, threshold=req.threshold)
