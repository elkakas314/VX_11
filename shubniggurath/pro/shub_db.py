"""
Esquema extendido de BD para Shub Pro (análisis avanzado, sesiones, jobs).
Integrado con data/runtime/vx11.db o SHUB_PRO_DB_URL.
"""

import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session


DB_URL = os.getenv("SHUB_PRO_DB_URL", "sqlite:///./data/runtime/vx11.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ShubSession(Base):
    """Sesión de análisis/procesamiento"""
    __tablename__ = "shub_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(String(255), nullable=True)
    mode = Column(String(50), default="default")  # default, mode_c, streaming, batch
    status = Column(String(20), default="active")  # active, paused, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    session_metadata = Column(JSON, nullable=True)
    
    analyses = relationship("AdvancedAnalysis", back_populates="session")
    jobs = relationship("ShubJob", back_populates="session")


class AdvancedAnalysis(Base):
    """Análisis DSP avanzado con características LUFS, espectral, dinámico"""
    __tablename__ = "shub_advanced_analysis"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("shubpro_tracks.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("shub_sessions.id"), nullable=True)
    
    # Niveles
    peak_dbfs = Column(Float, default=0.0)
    rms_dbfs = Column(Float, default=0.0)
    lufs_integrated = Column(Float, default=0.0)
    lufs_range = Column(Float, default=0.0)
    true_peak_dbfs = Column(Float, default=0.0)
    
    # Espectral
    spectral_centroid = Column(Float, default=0.0)
    spectral_rolloff = Column(Float, default=0.0)
    spectral_flux = Column(Float, default=0.0)
    zero_crossing_rate = Column(Float, default=0.0)
    spectral_flatness = Column(Float, default=0.0)
    
    # Dinámico
    dynamic_range = Column(Float, default=0.0)
    crest_factor = Column(Float, default=0.0)
    transients_count = Column(Integer, default=0)
    
    # Problemas detectados
    clipping_samples = Column(Integer, default=0)
    dc_offset = Column(Float, default=0.0)
    noise_floor_dbfs = Column(Float, default=0.0)
    phase_correlation = Column(Float, default=0.0)
    
    # Musical
    estimated_bpm = Column(Float, nullable=True)
    estimated_key = Column(String(10), nullable=True)
    key_confidence = Column(Float, nullable=True)
    harmonic_complexity = Column(Float, default=0.0)
    percussiveness = Column(Float, default=0.0)
    
    # Clasificación
    instrument_class = Column(String(100), nullable=True)
    genre_predicted = Column(String(100), nullable=True)
    mood_predicted = Column(String(100), nullable=True)
    
    # JSON para datos complejos
    mfcc_vector = Column(JSON, nullable=True)  # [13 valores]
    chroma_vector = Column(JSON, nullable=True)  # [12 valores]
    spectral_contrast_vector = Column(JSON, nullable=True)
    issues = Column(JSON, nullable=True)  # Lista de problemas
    recommendations = Column(JSON, nullable=True)  # Recomendaciones
    
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("ShubSession", back_populates="analyses")


class ShubJob(Base):
    """Job de procesamiento integrado con Madre/Switch/Operator"""
    __tablename__ = "shub_jobs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), unique=True, nullable=False)
    session_id = Column(Integer, ForeignKey("shub_sessions.id"), nullable=False)
    
    # Job specification
    job_type = Column(String(50), nullable=False)  # analyze, process, export, batch
    input_path = Column(String(512), nullable=False)
    output_path = Column(String(512), nullable=True)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    error_msg = Column(Text, nullable=True)
    
    # Integration with madre/switch
    madre_task_id = Column(String(36), nullable=True)
    switch_route_id = Column(String(36), nullable=True)
    
    # Resultado
    result = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    session = relationship("ShubSession", back_populates="jobs")


class ShubSandbox(Base):
    """Entorno de sandbox para procesamiento aislado"""
    __tablename__ = "shub_sandboxes"
    
    id = Column(Integer, primary_key=True)
    sandbox_id = Column(String(36), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    session_id = Column(Integer, ForeignKey("shub_sessions.id"), nullable=True)
    
    # Configuración del sandbox
    max_memory_mb = Column(Integer, default=256)
    max_cpu_percent = Column(Float, default=80.0)
    timeout_seconds = Column(Integer, default=300)
    
    # Estado
    status = Column(String(20), default="idle")  # idle, running, error
    current_task = Column(String(255), nullable=True)
    resource_usage = Column(JSON, nullable=True)  # {cpu, memory, io}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_shub_db():
    """Crear tablas extendidas de Shub si no existen"""
    Base.metadata.create_all(engine)


def get_shub_session() -> Session:
    """Obtener sesión DB para Shub"""
    return SessionLocal()
