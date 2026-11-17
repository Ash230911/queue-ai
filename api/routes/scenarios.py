from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import ScenarioCreate

router = APIRouter(prefix="/api", tags=["scenarios"])


@router.get("/scenarios")
def list_scenarios():
    return db.list_scenarios()


@router.post("/scenarios", status_code=201)
def create_scenario(req: ScenarioCreate):
    return {"id": db.save_scenario(req.name, req.params.model_dump())}


@router.get("/scenarios/{sid}")
def get_scenario(sid: int):
    s = db.get_scenario(sid)
    if not s:
        raise HTTPException(404, "Scenario not found")
    return {**s, "runs": db.list_runs(sid)}


@router.delete("/scenarios/{sid}")
def delete_scenario(sid: int):
    if not db.delete_scenario(sid):
        raise HTTPException(404, "Scenario not found")
    return {"deleted": sid}


@router.get("/runs/{rid}")
def get_run(rid: int):
    r = db.get_run(rid)
    if not r:
        raise HTTPException(404, "Run not found")
    return r
