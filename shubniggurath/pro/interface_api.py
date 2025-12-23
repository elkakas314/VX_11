"""
API REST para Shub Pro (FastAPI).
No cambia puertos de VX11; este módulo se puede montar dentro de un servicio existente.
"""
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
from config.settings import settings
from config.tokens import get_token
from .pipeline import run_pipeline, ingest_track
from .project_db import get_session, Project, Track, Analysis, Preset, init_db

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token


def check_token(x_vx11_token: str = Header(None)):
    if settings.enable_auth and x_vx11_token != VX11_TOKEN:
        raise HTTPException(status_code=401, detail="auth_required")
    return True


app = FastAPI(title="Shub Pro", dependencies=[Depends(check_token)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app.router.lifespan_context = lifespan


@app.get("/health")
def health():
    return {"status": "ok", "module": "shub_pro"}


@app.post("/ingest")
def ingest(payload: Dict[str, Any]):
    project = payload.get("project", "demo")
    track = payload.get("track", "track")
    path = payload.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="path_required")
    return ingest_track(project, track, path)


@app.post("/pipeline")
def pipeline(payload: Dict[str, Any]):
    project = payload.get("project", "demo")
    track = payload.get("track", "track")
    path = payload.get("path")
    out = payload.get("output_dir")
    if not path:
        raise HTTPException(status_code=400, detail="path_required")
    return run_pipeline(project, track, path, output_dir=out)


@app.get("/projects")
def list_projects():
    session = get_session()
    try:
        data = session.query(Project).all()
        return [{"id": p.id, "name": p.name, "sample_rate": p.sample_rate} for p in data]
    finally:
        session.close()


@app.get("/tracks/{project_id}")
def list_tracks(project_id: int):
    session = get_session()
    try:
        data = session.query(Track).filter_by(project_id=project_id).all()
        return [{"id": t.id, "name": t.name, "peak": t.peak, "rms": t.rms, "lufs": t.lufs} for t in data]
    finally:
        session.close()


@app.get("/analysis/{track_id}")
def get_analysis(track_id: int):
    session = get_session()
    try:
        data = session.query(Analysis).filter_by(track_id=track_id).all()
        return [{"id": a.id, "dr": a.dynamic_range, "noise_floor": a.noise_floor, "clipping": a.clipping_events} for a in data]
    finally:
        session.close()


@app.get("/presets/{track_id}")
def get_presets(track_id: int):
    session = get_session()
    try:
        data = session.query(Preset).filter_by(track_id=track_id).all()
        return [{"id": p.id, "name": p.name, "settings": p.settings_json} for p in data]
    finally:
        session.close()
