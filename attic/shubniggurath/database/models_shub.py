"""Database Models para Shub-Niggurath - Análisis, presets, REAPER cache."""

from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class AnalysisHistory(Base):
    """Historial de análisis de audio realizados."""
    __tablename__ = "shub_analysis_history"

    id = Column(Integer, primary_key=True)
    audio_file = Column(String, nullable=False)
    file_hash = Column(String)  # SHA256 para deduplicación
    analysis_json = Column(JSON)  # 40+ métricas en JSON
    style_detected = Column(String)  # rock, pop, electronic, acoustic
    recommendations = Column(JSON)  # Lista de recomendaciones
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float)
    sample_rate = Column(Integer)
    created_by = Column(String, default="shub")  # módulo que ejecutó

    def __repr__(self):
        return f"<AnalysisHistory {self.id} {self.audio_file}>"


class PresetLibrary(Base):
    """Librería de presets de FX."""
    __tablename__ = "shub_preset_library"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)  # eq, compressor, master, reverb, custom
    style = Column(String)  # rock, pop, electronic, acoustic
    parameters = Column(JSON)  # Parámetros del preset
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0)  # Cuántas veces se usó

    def __repr__(self):
        return f"<PresetLibrary {self.id} {self.name}>"


class REAPERProjectCache(Base):
    """Caché de proyectos REAPER analizados."""
    __tablename__ = "shub_reaper_project_cache"

    id = Column(Integer, primary_key=True)
    project_path = Column(String, nullable=False, unique=True)
    project_name = Column(String)
    last_analyzed = Column(DateTime)
    analysis_result = Column(JSON)  # Resultado del análisis
    status = Column(String)  # loaded, rendering, ready, error
    tracks_count = Column(Integer)
    bpm = Column(Float)
    duration_seconds = Column(Float)
    cached_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<REAPERProjectCache {self.id} {self.project_path}>"


class FXChainRecipe(Base):
    """Recetas de cadenas FX generadas."""
    __tablename__ = "shub_fx_chain_recipes"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    style = Column(String)  # rock, pop, electronic, acoustic
    target_lufs = Column(Float)
    plugins = Column(JSON)  # Lista de plugins en la cadena
    parameters_override = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<FXChainRecipe {self.id} {self.name}>"
