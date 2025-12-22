"""
ORM ligero para Shub Pro (SQLite unificada).
Usa env SHUB_PRO_DB_URL si está definida, en caso contrario data/runtime/vx11.db.
"""

import os
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship


DB_URL = os.getenv("SHUB_PRO_DB_URL", "sqlite:///./data/runtime/vx11.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Project(Base):
    __tablename__ = "shubpro_projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    sample_rate = Column(Integer, default=48000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tracks = relationship("Track", back_populates="project")


class Track(Base):
    __tablename__ = "shubpro_tracks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("shubpro_projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(64), default="unknown")
    file_path = Column(String(512), nullable=True)
    peak = Column(Float, default=0.0)
    rms = Column(Float, default=0.0)
    lufs = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="tracks")
    analyses = relationship("Analysis", back_populates="track")
    presets = relationship("Preset", back_populates="track")


class Analysis(Base):
    __tablename__ = "shubpro_analysis"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("shubpro_tracks.id"), nullable=False)
    dynamic_range = Column(Float, default=0.0)
    noise_floor = Column(Float, default=0.0)
    clipping_events = Column(Integer, default=0)
    spectral_centroid = Column(Float, default=0.0)
    tempo = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    track = relationship("Track", back_populates="analyses")


class Preset(Base):
    __tablename__ = "shubpro_presets"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("shubpro_tracks.id"), nullable=False)
    name = Column(String(255), nullable=False)
    settings_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    track = relationship("Track", back_populates="presets")


class History(Base):
    __tablename__ = "shubpro_history"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("shubpro_projects.id"), nullable=False)
    event = Column(String(255), nullable=False)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
