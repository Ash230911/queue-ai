"""WebSocket feed: streams one frame per simulated minute so the website can animate counters and queues."""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from sim.engine import generate_customers, simulate
from sim.strategies import get_strategy

from ..schemas import ScenarioParams
from .simulate import to_params

router = APIRouter()


@router.websocket("/ws/live")
async def live(ws: WebSocket):
    await ws.accept()
    try:
        cfg = await ws.receive_json()
        p = to_params(ScenarioParams(**cfg.get("params", {})))
        strategy = get_strategy(cfg.get("strategy", "baseline"))
        speed = min(max(float(cfg.get("speed", 30)), 1.0), 500.0)  # simulated minutes per real second
        res = simulate(generate_customers(p), p, strategy, timeline=True)
        frames, idx = res.timeline, 0
        for minute in range(int(res.metrics["makespan"]) + 2):
            while idx + 1 < len(frames) and frames[idx + 1]["t"] <= minute:
                idx += 1
            await ws.send_json({"type": "frame", "minute": minute, **frames[idx]})
            await asyncio.sleep(1 / speed)
        await ws.send_json({"type": "done", "summary": {"key": res.key, "name": res.name, **res.metrics}})
    except WebSocketDisconnect:
        return
    except Exception as e:  # validation or strategy errors are sent to the client instead of crashing
        try:
            await ws.send_json({"type": "error", "detail": str(e)[:300]})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
