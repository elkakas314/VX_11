"""
Pipeline de proyecto: ingestión -> análisis -> mezcla -> export -> guardar en BD.
"""
import os
from typing import Dict, Any
from pathlib import Path
from .audio_io import load_audio
from .dsp import analyze_basic
from .analysis import feature_summary
from .mixing import auto_mix
from .project_db import init_db, get_session, Project, Track, Analysis, Preset
from .metadata_manager import log_event
from .exporter import export_mix
from config.settings import settings


def ensure_db():
    init_db()


def ingest_track(project_name: str, track_name: str, file_path: str) -> Dict[str, Any]:
    ensure_db()
    session = get_session()
    try:
        project = session.query(Project).filter_by(name=project_name).first()
        if not project:
            project = Project(name=project_name, sample_rate=48000)
            session.add(project)
            session.commit()
        track = session.query(Track).filter_by(project_id=project.id, name=track_name).first()
        if not track:
            track = Track(project_id=project.id, name=track_name, role="raw", file_path=file_path)
            session.add(track)
            session.commit()
        return {"project_id": project.id, "track_id": track.id}
    finally:
        session.close()


def run_pipeline(project_name: str, track_name: str, file_path: str, output_dir: str = None) -> Dict[str, Any]:
    ensure_db()
    data, sr = load_audio(file_path)
    metrics = analyze_basic(data)
    features = feature_summary(data, sr)
    mix = auto_mix(data, target_lufs=-16.0, pan_value=0.0)

    out_dir = output_dir or settings.SANDBOX_PATH
    exp = export_mix(out_dir, f"{project_name}_{track_name}", mix["mono"], mix["stereo"], sample_rate=sr)

    session = get_session()
    try:
        project = session.query(Project).filter_by(name=project_name).first()
        if not project:
            project = Project(name=project_name, sample_rate=sr)
            session.add(project)
            session.commit()
        track = session.query(Track).filter_by(project_id=project.id, name=track_name).first()
        if not track:
            track = Track(project_id=project.id, name=track_name, role="raw", file_path=file_path)
            session.add(track)
            session.commit()
        track.peak = metrics["peak"]
        track.rms = metrics["rms"]
        track.lufs = metrics["lufs"]
        session.commit()

        analysis = Analysis(
            track_id=track.id,
            dynamic_range=metrics["dynamic_range"],
            noise_floor=metrics["noise_floor"],
            clipping_events=metrics["clipping_events"],
            spectral_centroid=features["spectral_centroid"],
            tempo=features["tempo"],
            notes="auto_pipeline",
        )
        session.add(analysis)
        session.commit()

        preset = Preset(track_id=track.id, name="auto_mix", settings_json=str({"target_lufs": -16.0, "pan": 0.0}))
        session.add(preset)
        session.commit()

        log_event(project.id, "pipeline_complete", {"track": track.name, "files": exp})

        return {
            "status": "ok",
            "project_id": project.id,
            "track_id": track.id,
            "analysis_id": analysis.id,
            "outputs": exp,
            "metrics": metrics,
            "features": features,
        }
    finally:
        session.close()
