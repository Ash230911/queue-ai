from fastapi.testclient import TestClient

from api.main import app


def test_health_and_defaults():
    with TestClient(app) as c:
        assert c.get("/api/health").json() == {"status": "ok"}
        assert c.get("/api/defaults").json()["c"] == 5


def test_simulate_returns_four_strategies_and_baseline_first():
    with TestClient(app) as c:
        r = c.post("/api/simulate", json={}).json()
        assert [s["key"] for s in r["summary"]][0] == "baseline"
        assert len(r["summary"]) == 4 and r["recommendation"]


def test_same_seed_same_result():
    with TestClient(app) as c:
        body = {"params": {"seed": 42}}
        assert c.post("/api/simulate", json=body).json()["summary"] == c.post("/api/simulate", json=body).json()["summary"]


def test_invalid_input_is_rejected_with_422():
    with TestClient(app) as c:
        assert c.post("/api/simulate", json={"params": {"c": 0}}).status_code == 422
        assert c.post("/api/simulate", json={"params": {"rate": -5}}).status_code == 422


def test_unknown_strategy_is_400():
    with TestClient(app) as c:
        assert c.post("/api/simulate", json={"strategies": ["nope"]}).status_code == 400


def test_overload_gives_warning_not_crash():
    with TestClient(app) as c:
        r = c.post("/api/simulate", json={"params": {"c": 1, "rate": 100}}).json()
        assert r["warnings"]


def test_save_and_reload_scenario_and_run():
    with TestClient(app) as c:
        r = c.post("/api/simulate", json={"save": True, "scenario_name": "t"}).json()
        sid = r["scenario_id"]
        s = c.get(f"/api/scenarios/{sid}").json()
        assert s["name"] == "t" and len(s["runs"]) == 4
        run = c.get(f"/api/runs/{s['runs'][0]['id']}").json()
        assert run["series"] and run["counters"]
        assert c.get("/api/scenarios/999999").status_code == 404


def test_demo_scenarios_seeded():
    with TestClient(app) as c:
        assert len(c.get("/api/scenarios").json()) >= 3


def test_forecast_optimise_validate():
    with TestClient(app) as c:
        f = c.post("/api/forecast", json={}).json()
        assert f["windows"]
        o = c.post("/api/optimise", json={"target_wait": 6, "max_counters": 8, "runs": 3}).json()
        assert len(o["options"]) == 8
        v = c.post("/api/validate", json={"runs": 5}).json()
        assert v["strategies"][0]["key"] == "baseline"


def test_websocket_streams_frames_and_finishes():
    with TestClient(app) as c:
        with c.websocket_connect("/ws/live") as ws:
            ws.send_json({"params": {"n": 30}, "strategy": "shared", "speed": 500})
            types = []
            while True:
                m = ws.receive_json()
                types.append(m["type"])
                if m["type"] in ("done", "error"):
                    break
            assert types[0] == "frame" and types[-1] == "done"
