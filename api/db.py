"""SQLite persistence (member 4). Parameterised queries only."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config

SCHEMA = Path(__file__).resolve().parent.parent / "db" / "schema.sql"


@contextmanager
def connect():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with connect() as con:
        con.executescript(SCHEMA.read_text())
        if con.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0:
            seed_demo(con)


def seed_demo(con):
    demos = [
        ("Demo: normal day with an arrival surge", dict(n=150, rate=40, svc=6, cv=0.8, c=5, flex=1, prio=15, mult=2, s0=40, sl=30, seed=7, dist="lognormal")),
        ("Demo: heavy surge, tight staffing", dict(n=200, rate=45, svc=6, cv=1.0, c=5, flex=2, prio=20, mult=2.5, s0=30, sl=40, seed=11, dist="lognormal")),
        ("Demo: quiet clinic", dict(n=120, rate=25, svc=8, cv=0.6, c=4, flex=1, prio=25, mult=1.5, s0=50, sl=20, seed=3, dist="lognormal")),
    ]
    for name, params in demos:
        con.execute("INSERT INTO scenarios(name, params_json) VALUES (?, ?)", (name, json.dumps(params)))


def save_scenario(name: str, params: dict) -> int:
    with connect() as con:
        cur = con.execute("INSERT INTO scenarios(name, params_json) VALUES (?, ?)", (name, json.dumps(params)))
        return cur.lastrowid


def _scenario_row(r):
    return {"id": r["id"], "name": r["name"], "params": json.loads(r["params_json"]), "created_at": r["created_at"]}


def list_scenarios():
    with connect() as con:
        return [_scenario_row(r) for r in con.execute("SELECT * FROM scenarios ORDER BY id DESC")]


def get_scenario(sid: int):
    with connect() as con:
        r = con.execute("SELECT * FROM scenarios WHERE id = ?", (sid,)).fetchone()
        return _scenario_row(r) if r else None


def delete_scenario(sid: int) -> bool:
    with connect() as con:
        return con.execute("DELETE FROM scenarios WHERE id = ?", (sid,)).rowcount > 0


def save_run(scenario_id: int, strategy: str, m: dict, series, util: list, busy: list) -> int:
    with connect() as con:
        cur = con.execute(
            """INSERT INTO runs(scenario_id, strategy, avg_wait, p90_wait, max_wait, avg_queue,
               peak_queue, utilisation, staff_minutes, est_error) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (scenario_id, strategy, m["avg_wait"], m["p90_wait"], m["max_wait"], m["avg_queue"],
             m["peak_queue"], m["utilisation"], m["staff_minutes"], m["est_error"]))
        rid = cur.lastrowid
        con.executemany("INSERT INTO run_series(run_id, t, queue_length) VALUES (?,?,?)", [(rid, t, q) for t, q in series])
        con.executemany("INSERT INTO counter_stats(run_id, counter_no, utilisation, busy_minutes) VALUES (?,?,?,?)",
                        [(rid, i, u, b) for i, (u, b) in enumerate(zip(util, busy))])
        return rid


def list_runs(scenario_id: int):
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM runs WHERE scenario_id = ? ORDER BY id", (scenario_id,))]


def get_run(rid: int):
    with connect() as con:
        r = con.execute("SELECT * FROM runs WHERE id = ?", (rid,)).fetchone()
        if not r:
            return None
        out = dict(r)
        out["series"] = [[x["t"], x["queue_length"]] for x in con.execute("SELECT t, queue_length FROM run_series WHERE run_id = ? ORDER BY rowid", (rid,))]
        out["counters"] = [dict(x) for x in con.execute("SELECT counter_no, utilisation, busy_minutes FROM counter_stats WHERE run_id = ? ORDER BY counter_no", (rid,))]
        return out


def save_validation(scenario_id, rows, runs):
    with connect() as con:
        con.executemany("INSERT INTO validations(scenario_id, strategy, mean_wait, ci95, win_rate, runs) VALUES (?,?,?,?,?,?)",
                        [(scenario_id, r["key"], r["mean_wait"], r["ci95"], r["win_rate"], runs) for r in rows])
