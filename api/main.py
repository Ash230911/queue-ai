"""FastAPI entry point (member 4). Run: uvicorn api.main:app --reload   |   Docs: http://localhost:8000/docs"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routes import forecast, live, optimise, scenarios, simulate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("queue-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Queue Lab API", version="1.0.0", description="Queue simulation, prediction and service allocation. All data is simulated.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def timing(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    log.info("%s %s -> %s in %.0f ms", request.method, request.url.path, resp.status_code, (time.perf_counter() - t0) * 1000)
    return resp


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal error. Check the server log."})


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}


for r in (simulate.router, forecast.router, optimise.router, scenarios.router, live.router):
    app.include_router(r)

if config.WEB_DIST.exists():  # serve the built website from the same port
    app.mount("/", StaticFiles(directory=config.WEB_DIST, html=True), name="web")
