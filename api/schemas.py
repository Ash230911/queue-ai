"""Request/response validation (member 4). Pydantic returns clear 422 errors for bad input."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ScenarioParams(BaseModel):
    n: int = Field(150, ge=20, le=2000, description="Number of customers")
    rate: float = Field(40, gt=0, le=300, description="Base arrivals per hour")
    svc: float = Field(6, gt=0, le=60, description="Mean service time (min)")
    cv: float = Field(0.8, ge=0.05, le=3, description="Service-time variability")
    c: int = Field(5, ge=1, le=20, description="Regular counters")
    flex: int = Field(1, ge=0, le=10, description="Flex counters")
    prio: float = Field(15, ge=0, le=100, description="% priority customers")
    mult: float = Field(2, ge=1, le=5, description="Surge arrival multiplier")
    s0: float = Field(40, ge=0, le=1000, description="Surge start (min)")
    sl: float = Field(30, ge=0, le=500, description="Surge length (min)")
    seed: int = Field(7, ge=0, le=10**9)
    dist: Literal["lognormal", "exponential"] = "lognormal"


class SimulateRequest(BaseModel):
    params: ScenarioParams = ScenarioParams()
    strategies: Optional[list[str]] = None
    save: bool = False
    scenario_name: Optional[str] = None


class ForecastRequest(BaseModel):
    params: ScenarioParams = ScenarioParams()
    threshold: float = Field(0.85, gt=0, le=2)
    window: int = Field(15, ge=5, le=60)


class OptimiseRequest(BaseModel):
    params: ScenarioParams = ScenarioParams()
    target_wait: float = Field(5, gt=0, le=120)
    max_counters: int = Field(12, ge=1, le=20)
    strategy: str = "shared"
    runs: int = Field(10, ge=2, le=50)


class ValidateRequest(BaseModel):
    params: ScenarioParams = ScenarioParams()
    runs: int = Field(30, ge=5, le=100)
    strategies: Optional[list[str]] = None


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    params: ScenarioParams = ScenarioParams()
