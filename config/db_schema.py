"""
DB Schema para VX11: define tablas para tasks, context, reports, spawns.
Compatible con SQLAlchemy 2.0 (uses declarative_base desde orm).
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    create_engine,
    text,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
import hashlib

# Usar declarative_base desde sqlalchemy.orm (SQLAlchemy 2.0 compatible)
Base = declarative_base()


class Task(Base):
    """Tareas orquestadas por madre."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    module = Column(String(50), nullable=False)  # madre, spawner, hermes, etc.
    action = Column(String(100), nullable=False)  # start, stop, exec, etc.
    status = Column(
        String(20), default="pending"
    )  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)


class Context(Base):
    """Contexto global y específico de la ejecución."""

    __tablename__ = "context"

    id = Column(Integer, primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.uuid"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    scope = Column(String(50), default="global")  # global, module, spawn
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    """Reportes de ejecución (métricas, logs, forensics)."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.uuid"), nullable=False)
    report_type = Column(String(50), nullable=False)  # metrics, forensics, health
    summary = Column(Text)
    details = Column(Text)
    metrics = Column(Text)  # JSON serializado
    created_at = Column(DateTime, default=datetime.utcnow)


class Spawn(Base):
    """Procesos efímeros spawneados."""

    __tablename__ = "spawns"

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    cmd = Column(String(500), nullable=False)
    pid = Column(Integer, nullable=True)
    status = Column(
        String(20), default="pending"
    )  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    parent_task_id = Column(String(36), ForeignKey("tasks.uuid"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IADecision(Base):
    """Decisiones y rutas IA (persistence para learner)."""

    __tablename__ = "ia_decisions"

    id = Column(Integer, primary_key=True)
    prompt_hash = Column(String(64), nullable=False)
    provider = Column(String(50), nullable=False)  # deepseek, local, hermes, etc.
    task_type = Column(
        String(50), nullable=True
    )  # chat, code, reasoning, cli, embedding
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    latency_ms = Column(Integer, nullable=True)  # Track provider latency for scoring
    success = Column(Boolean, default=False)  # Track provider success rate
    confidence = Column(Float, default=0.5)
    meta_json = Column(
        Text, nullable=True
    )  # JSON metadata (renamed from metadata to avoid SQLAlchemy reserved word)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModuleHealth(Base):
    """Estado de salud de módulos."""

    __tablename__ = "module_health"

    id = Column(Integer, primary_key=True)
    module = Column(String(50), nullable=False)
    status = Column(String(20), default="unknown")
    last_ping = Column(DateTime, default=datetime.utcnow)
    error_count = Column(Integer, default=0)
    uptime_seconds = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelRegistry(Base):
    """Registro centralizado de modelos locales (HF, GGUF, llama.cpp, etc)."""

    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    path = Column(String(500), nullable=False)
    provider = Column(String(50), nullable=False)  # huggingface, gguf, ollama, llamacpp
    type = Column(String(50), nullable=False)  # chat, instruct, code, embedding
    size_bytes = Column(Integer, nullable=False)
    tags = Column(Text, nullable=True)  # JSON: ["multilang", "fast"]
    last_used = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, default=0.5)  # Learner score (0-1)
    available = Column(Boolean, default=True)
    meta_json = Column(
        Text, nullable=True
    )  # JSON (renamed from metadata to avoid SQLAlchemy reserved word)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CLIRegistry(Base):
    """Registro centralizado de CLIs disponibles."""

    __tablename__ = "cli_registry"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    bin_path = Column(String(500), nullable=True)
    available = Column(Boolean, default=True)
    last_checked = Column(DateTime, default=datetime.utcnow)
    cli_type = Column(String(50), nullable=False)  # devops, vcs, search, infra, cloud
    token_config_key = Column(String(100), nullable=True)  # GH_TOKEN, DOCKER_TOKEN, etc
    rate_limit_daily = Column(Integer, nullable=True)
    used_today = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== UNIFIED VX11 TABLES (v6.3) ==========


class ModelsLocal(Base):
    __tablename__ = "models_local"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    path = Column(String(512), nullable=False)
    size_mb = Column(Integer, default=0)
    hash = Column(String(128), nullable=True)
    category = Column(String(64), default="general")
    status = Column(String(32), default="available")  # available|active|warm|deprecated
    compatibility = Column(String(64), default="cpu")
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelsRemoteCLI(Base):
    __tablename__ = "models_remote_cli"
    id = Column(Integer, primary_key=True)
    provider = Column(String(128), nullable=False)
    token = Column(String(256), unique=True, nullable=False)
    limit_daily = Column(Integer, default=0)
    limit_weekly = Column(Integer, default=0)
    renew_at = Column(DateTime, nullable=True)
    task_type = Column(String(64), default="general")
    status = Column(String(32), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TokensUsage(Base):
    __tablename__ = "tokens_usage"
    id = Column(Integer, primary_key=True)
    token_id = Column(String(256), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    used_count = Column(Integer, default=0)
    source = Column(String(64), default="unknown")


class TaskQueue(Base):
    __tablename__ = "task_queue"
    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False)
    priority = Column(Integer, default=5)
    payload = Column(Text, nullable=False)
    status = Column(String(32), default="queued")
    result = Column(Text, nullable=True)
    enqueued_at = Column(DateTime, default=datetime.utcnow)
    dequeued_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Events(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class HijasRuntime(Base):
    __tablename__ = "hijas_runtime"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    state = Column(String(32), default="standby")
    pid = Column(Integer, nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    meta_json = Column(Text, nullable=True)
    birth_context = Column(Text, nullable=True)
    death_context = Column(Text, nullable=True)
    intent_type = Column(String(64), nullable=True)
    ttl = Column(Integer, default=60)
    killed_by = Column(String(128), nullable=True)
    purpose = Column(String(256), nullable=True)
    module_creator = Column(String(64), nullable=True)
    born_at = Column(DateTime, default=datetime.utcnow)
    died_at = Column(DateTime, nullable=True)


class SystemState(Base):
    __tablename__ = "system_state"
    id = Column(Integer, primary_key=True)
    key = Column(String(128), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    memory_pressure = Column(Float, default=0.0)
    cpu_pressure = Column(Float, default=0.0)
    switch_queue_level = Column(Float, default=0.0)
    hermes_update_required = Column(Boolean, default=False)
    shub_pipeline_state = Column(String(64), default="idle")
    operator_active = Column(Boolean, default=False)
    system_load_score = Column(Float, default=0.0)
    model_rotation_state = Column(String(128), default="stable")
    audio_pipeline_state = Column(String(128), default="idle")
    pending_tasks = Column(Integer, default=0)
    active_children = Column(Integer, default=0)
    last_operator_activity = Column(DateTime, nullable=True)
    power_mode = Column(String(32), default="balanced")


class AuditLogs(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    component = Column(String(64), nullable=False)
    level = Column(String(16), default="INFO")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SandboxExec(Base):
    __tablename__ = "sandbox_exec"
    id = Column(Integer, primary_key=True)
    action = Column(String(128), nullable=False)
    status = Column(String(32), default="pending")
    duration_ms = Column(Float, default=0.0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemEvents(Base):
    __tablename__ = "system_events"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload = Column(Text, nullable=True)
    severity = Column(String(16), default="info")


class SchedulerHistory(Base):
    __tablename__ = "scheduler_history"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(64), nullable=False)  # spawn, kill, delay
    reason = Column(Text, nullable=True)
    metrics = Column(Text, nullable=True)


class Engine(Base):
    """Registro centralizado de motores (modelos locales, CLI, LLM remotos)."""

    __tablename__ = "engines"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    engine_type = Column(
        String(32), nullable=False
    )  # "local_model" | "cli" | "remote_llm"
    domain = Column(
        String(64), nullable=False
    )  # "reasoning" | "code" | "infrastructure" | etc.
    endpoint = Column(String(256), nullable=False)  # URL (local/remote) ó command path
    version = Column(String(32), default="latest")

    # Quota management
    quota_tokens_per_day = Column(Integer, default=-1)  # -1 = unlimited
    quota_used_today = Column(Integer, default=0)
    quota_reset_at = Column(DateTime, default=datetime.utcnow)

    # Performance hints
    latency_ms = Column(Float, default=0.0)  # Avg latency
    cost_per_call = Column(Float, default=0.0)  # For remote engines

    # Status
    enabled = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Engine {self.name} ({self.engine_type}|{self.domain})>"


# ========== SHUB TABLAS ==========


class ShubProject(Base):
    __tablename__ = "shub_projects"
    id = Column(Integer, primary_key=True)
    project_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    sample_rate = Column(Integer, default=48000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ShubTrack(Base):
    __tablename__ = "shub_tracks"
    id = Column(Integer, primary_key=True)
    project_id = Column(
        String(64), ForeignKey("shub_projects.project_id"), nullable=False
    )
    name = Column(String(255), nullable=False)
    role = Column(String(64), default="unknown")  # vocal, drum, bass, etc.
    file_path = Column(String(512), nullable=True)
    duration_sec = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ShubAnalysis(Base):
    __tablename__ = "shub_analysis"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("shub_tracks.id"), nullable=False)
    rms = Column(Float, default=0.0)
    peak = Column(Float, default=0.0)
    lufs = Column(Float, default=0.0)
    noise_floor = Column(Float, default=0.0)
    dynamic_range = Column(Float, default=0.0)
    clipping = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ShubFXChain(Base):
    __tablename__ = "shub_fx_chains"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("shub_tracks.id"), nullable=False)
    chain_name = Column(String(255), nullable=False)
    steps_json = Column(Text, nullable=False)  # JSON steps
    created_at = Column(DateTime, default=datetime.utcnow)


class ShubPreset(Base):
    __tablename__ = "shub_presets"
    id = Column(Integer, primary_key=True)
    fx_chain_id = Column(Integer, ForeignKey("shub_fx_chains.id"), nullable=False)
    rpp_snippet = Column(Text, nullable=True)
    version = Column(String(32), default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== OPERATOR / JOBS ==========


class OperatorJob(Base):
    __tablename__ = "operator_jobs"
    id = Column(Integer, primary_key=True)
    job_id = Column(String(64), unique=True, nullable=False)
    intent = Column(String(64), nullable=False)
    status = Column(String(32), default="queued")
    payload = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== HERMES INGEST ==========


class HermesIngest(Base):
    __tablename__ = "hermes_ingest"
    id = Column(Integer, primary_key=True)
    path = Column(String(512), nullable=False)
    size_bytes = Column(Integer, default=0)
    duration_sec = Column(Float, default=0.0)
    status = Column(String(32), default="ingested")
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== MADRE POLICIES ==========


class MadrePolicy(Base):
    __tablename__ = "madre_policies"
    id = Column(Integer, primary_key=True)
    module = Column(String(64), nullable=False)
    error_threshold = Column(Integer, default=3)
    idle_seconds = Column(Integer, default=300)
    enable_autosuspend = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MadreAction(Base):
    __tablename__ = "madre_actions"
    id = Column(Integer, primary_key=True)
    module = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)  # off/standby/active
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== FORENSIC LEDGER ==========


class ForensicLedger(Base):
    __tablename__ = "forensic_ledger"
    id = Column(Integer, primary_key=True)
    event = Column(String(255), nullable=False)
    payload = Column(Text, nullable=True)
    hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def compute_hash(event: str, payload: str) -> str:
        raw = f"{event}:{payload or ''}".encode()
        return hashlib.sha256(raw).hexdigest()


# ========== NUEVAS TABLAS v6.7 ==========


class PowerEvent(Base):
    __tablename__ = "power_events"
    id = Column(Integer, primary_key=True)
    module = Column(String(64), nullable=False)
    action = Column(String(32), nullable=False)  # on, off, standby
    reason = Column(String(255), nullable=True)
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Float, default=0.0)
    activity_score = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)


class FeromonaEvent(Base):
    __tablename__ = "feromona_events"
    id = Column(Integer, primary_key=True)
    type = Column(String(64), nullable=False)  # system, audio, anomaly, mutation
    intensity = Column(Integer, default=0)
    module = Column(String(64), nullable=False)
    payload = Column(Text, nullable=True)  # JSON
    timestamp = Column(DateTime, default=datetime.utcnow)


class HijasState(Base):
    __tablename__ = "hijas_state"
    id = Column(Integer, primary_key=True)
    hija_id = Column(String(64), unique=True, nullable=False)
    module = Column(String(64), nullable=False)
    status = Column(String(32), default="running")  # running, stopped, terminated
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Float, default=0.0)
    pid = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DriftReport(Base):
    __tablename__ = "drift_reports"
    id = Column(Integer, primary_key=True)
    module = Column(String(64), nullable=False)
    details = Column(
        Text, nullable=False
    )  # JSON: {files_missing: [...], extra_files: [...], ...}
    severity = Column(String(32), default="low")  # low, medium, high, critical
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)


# ========== NUEVAS TABLAS v7.0 para SWITCH/HERMES ==========


class CLIProvider(Base):
    """Registro de proveedores CLI (DeepSeek R1, etc.) con límites de tokens."""

    __tablename__ = "cli_providers"

    id = Column(Integer, primary_key=True)
    name = Column(
        String(100), unique=True, nullable=False
    )  # e.g., "deepseek_r1", "openrouter"
    base_url = Column(String(500), nullable=True)  # e.g., "https://api.deepseek.com/v1"
    api_key_env = Column(String(100), nullable=False)  # e.g., "DEEPSEEK_API_KEY"
    task_types = Column(String(255), default="chat")  # CSV: "chat,audio,tools"
    daily_limit_tokens = Column(Integer, default=100000)
    monthly_limit_tokens = Column(Integer, default=3000000)
    tokens_used_today = Column(Integer, default=0)
    tokens_used_month = Column(Integer, default=0)
    reset_hour_utc = Column(Integer, default=0)  # Cuando resetear contadores
    enabled = Column(Boolean, default=True)
    last_reset_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LocalModelV2(Base):
    """Modelo local mejorado con engine, max_context y categorización explícita."""

    __tablename__ = "local_models_v2"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    engine = Column(
        String(50), nullable=False
    )  # "llama.cpp", "gguf", "ollama", "transformers"
    path = Column(String(512), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    task_type = Column(
        String(50), nullable=False
    )  # "chat", "audio-engineer", "summarization", "audio-analysis"
    max_context = Column(Integer, default=2048)  # Tamaño máximo contexto
    enabled = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    compatibility = Column(String(64), default="cpu")  # "cpu", "gpu", "gpu-cuda"
    meta_info = Column(Text, nullable=True)  # JSON: tags, version, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelUsageStat(Base):
    """Registro detallado de uso de modelos/CLI para análisis y feedback."""

    __tablename__ = "model_usage_stats"

    id = Column(Integer, primary_key=True)
    model_or_cli_name = Column(String(255), nullable=False)
    kind = Column(String(20), nullable=False)  # "cli" | "local"
    task_type = Column(String(50), nullable=False)  # "chat", "audio-engineer", etc.
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=False)
    error_message = Column(String(500), nullable=True)
    user_id = Column(String(100), nullable=True)  # Para multi-tenancy futura
    created_at = Column(DateTime, default=datetime.utcnow)


class SwitchQueueV2(Base):
    """Cola de Switch mejorada con tracking de task_type y payload hash."""

    __tablename__ = "switch_queue_v2"

    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False)  # "shub", "operator", "madre", "hija"
    priority = Column(Integer, default=5)  # Menor número = mayor prioridad
    task_type = Column(
        String(50), nullable=False
    )  # "chat", "audio-engineer", "code", etc.
    payload_hash = Column(String(64), nullable=False)  # SHA256 del payload para dedup
    status = Column(
        String(32), default="queued"
    )  # "queued", "running", "done", "error"
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    result_size = Column(Integer, default=0)
    error_message = Column(String(500), nullable=True)


# Ensure data directory
os.makedirs("./data/runtime", exist_ok=True)

# VX11 v6.0: BD unificada
# Todos los módulos comparten vx11.db con namespaces de tablas
# (madre_tasks, hermes_tasks, hive_tasks, etc.)
UNIFIED_DB_URL = "sqlite:///./data/runtime/vx11.db"

# Mantener compatibilidad con código legado que pide get_session("madre")
# Todos retornan la misma sesión de vx11.db
DATABASES = {
    "madre": UNIFIED_DB_URL,
    "hermes": UNIFIED_DB_URL,
    "hive": UNIFIED_DB_URL,
    "vx11": UNIFIED_DB_URL,  # BD unificada
}

# Engine único, shared por todos
unified_engine = create_engine(
    UNIFIED_DB_URL, connect_args={"check_same_thread": False}
)
unified_session_maker = sessionmaker(
    autocommit=False, autoflush=False, bind=unified_engine
)


@event.listens_for(unified_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()
    except Exception:
        pass


# ========== NUEVA TABLAS v7.0 para MADRE/SPAWNER/HIJAS EFÍMERAS ==========


class DaughterTask(Base):
    """Tarea tentacular que genera hijas efímeras."""

    __tablename__ = "daughter_tasks"

    id = Column(Integer, primary_key=True)
    intent_id = Column(String(36), nullable=True)  # Enlace opcional con INTENT original
    source = Column(
        String(64), nullable=False
    )  # "operator", "hormiguero", "system", "shub", etc.
    priority = Column(Integer, default=3)  # shub(0)>operator(1)>madre(2)>hijas(3)
    status = Column(
        String(32), default="pending"
    )  # pending|planning|running|retrying|completed|failed|expired|cancelled
    task_type = Column(String(50), nullable=False)  # "short"|"long"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    max_retries = Column(Integer, default=2)  # Número máximo de reintentos
    current_retry = Column(Integer, default=0)  # Intento actual
    metadata_json = Column(Text, nullable=True)  # JSON con parámetros específicos
    plan_json = Column(Text, nullable=True)  # Plan generado por Madre


class Daughter(Base):
    """Instancia de hija efímera."""

    __tablename__ = "daughters"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("daughter_tasks.id"), nullable=False)
    name = Column(String(128), nullable=False)  # Ej: "hija-task-1-mut0"
    purpose = Column(Text, nullable=True)  # Descripción del objetivo
    tools_json = Column(Text, nullable=True)  # JSON: lista de herramientas disponibles
    ttl_seconds = Column(Integer, default=300)  # Time-to-live
    started_at = Column(DateTime, nullable=True)
    last_heartbeat_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    status = Column(
        String(32), default="spawned"
    )  # spawned|running|restarting|finished|failed|killed|expired|mutated
    mutation_level = Column(Integer, default=0)  # Nivel de mutación/adaptación
    error_last = Column(Text, nullable=True)  # Último error
    spawn_uuid = Column(
        String(36), unique=True, nullable=True
    )  # UUID único de spawn para genealogía
    parent_id = Column(
        Integer, ForeignKey("daughters.id"), nullable=True
    )  # Daughter padre (si aplica)
    spawner_service = Column(
        String(64), nullable=True
    )  # Servicio spawner que creó ésta (ej. "spawner")


class DaughterAttempt(Base):
    """Intento/reintento de ejecución de hija."""

    __tablename__ = "daughter_attempts"

    id = Column(Integer, primary_key=True)
    daughter_id = Column(Integer, ForeignKey("daughters.id"), nullable=False)
    attempt_number = Column(Integer, default=1)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(
        String(32), default="running"
    )  # running|success|error|timeout|cancelled
    error_message = Column(String(500), nullable=True)
    tokens_used_cli = Column(Integer, default=0)
    tokens_used_local = Column(Integer, default=0)
    switch_model_used = Column(
        String(128), nullable=True
    )  # Nombre del modelo del Switch
    cli_provider_used = Column(
        String(128), nullable=True
    )  # Nombre del CLI (ej. "deepseek_r1")
    created_at = Column(DateTime, default=datetime.utcnow)


class IntentLog(Base):
    """Registro de INTENTs procesados."""

    __tablename__ = "intents_log"

    id = Column(Integer, primary_key=True)
    source = Column(
        String(64), nullable=False
    )  # "operator"|"hormiguero"|"system"|"shub"|etc.
    payload_json = Column(Text, nullable=False)  # JSON del INTENT completo
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_by_madre_at = Column(DateTime, nullable=True)
    result_status = Column(String(32), default="planned")  # planned|rejected|error
    notes = Column(Text, nullable=True)


def _table_exists(engine, name: str) -> bool:
    with engine.connect() as conn:
        res = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": name},
        )
        return res.fetchone() is not None


def _columns(engine, table: str):
    with engine.connect() as conn:
        res = conn.execute(text(f"PRAGMA table_info('{table}')"))
        return [row[1] for row in res.fetchall()]


def _copy_table(engine, legacy: str, unified: str):
    """
    Copia datos desde tablas legacy (madre_*, hermes_*, hive_*)
    hacia las tablas unificadas. Solo copia columnas en común
    y usa INSERT OR IGNORE para evitar duplicados.
    """
    if not (_table_exists(engine, legacy) and _table_exists(engine, unified)):
        return

    legacy_cols = _columns(engine, legacy)
    unified_cols = _columns(engine, unified)
    common = [c for c in legacy_cols if c in unified_cols]
    if not common:
        return

    col_csv = ",".join(common)
    placeholders = ",".join([f":{c}" for c in common])

    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT {col_csv} FROM {legacy}")).fetchall()
        for row in rows:
            conn.execute(
                text(
                    f"INSERT OR IGNORE INTO {unified} ({col_csv}) VALUES ({placeholders})"
                ),
                {k: row[idx] for idx, k in enumerate(common)},
            )
        conn.commit()


# ========== HORMIGUERO v7.0 TABLES ==========


class HormigaState(Base):
    """Estado de hormigas individuales (scanners de bajo consumo)."""

    __tablename__ = "hormiga_state"

    id = Column(Integer, primary_key=True)
    ant_id = Column(String(64), unique=True, nullable=False)
    role = Column(
        String(32), nullable=False
    )  # scanner_drift, scanner_memory, scanner_imports, etc.
    status = Column(String(20), default="idle")  # idle, scanning, reporting
    last_scan_at = Column(DateTime, nullable=True)
    mutation_level = Column(Integer, default=0)
    cpu_percent = Column(Float, default=0.0)
    ram_percent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Incident(Base):
    """Incidencias detectadas por hormigas (reportes de anomalías)."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    ant_id = Column(String(64), nullable=False)  # Hormiga que reportó
    incident_type = Column(
        String(64), nullable=False
    )  # drift, memory_leak, broken_import, orphan_log, orphan_db, orphan_module, zombie_process, blocked_port
    severity = Column(String(20), default="info")  # info, warning, error, critical
    location = Column(String(255), nullable=True)  # Ruta o módulo afectado
    details = Column(Text, nullable=True)  # JSON con detalles
    status = Column(String(20), default="open")  # open, acknowledged, resolved
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    queen_decision = Column(
        String(255), nullable=True
    )  # direct_action | spawn_hija | switch_strategy


class PheromoneLog(Base):
    """Log de feromonas emitidas por la Reina (comunicación del Hormiguero)."""

    __tablename__ = "pheromone_log"

    id = Column(Integer, primary_key=True)
    pheromone_type = Column(
        String(64), nullable=False
    )  # alert, task, cleanup, optimize, investigate
    intensity = Column(Integer, default=1)  # 1-10
    source_incident_ids = Column(
        Text, nullable=True
    )  # JSON array de IDs de incidencias
    madre_intent_id = Column(String(64), nullable=True)  # INTENT enviado a Madre
    switch_consultation_id = Column(String(64), nullable=True)  # Request a Switch
    payload = Column(Text, nullable=True)  # JSON con detalles de feromona
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)


# ========== OPERATOR v7.0 TABLES ==========


class OperatorSession(Base):
    """Sesión de operador (conversación)."""

    __tablename__ = "operator_session"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False)
    user_id = Column(String(64), nullable=False, default="local")
    source = Column(String(50), nullable=False, default="web")  # web, cli, api
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperatorMessage(Base):
    """Mensaje en sesión de operador."""

    __tablename__ = "operator_message"

    id = Column(Integer, primary_key=True)
    session_id = Column(
        String(64), ForeignKey("operator_session.session_id"), nullable=False
    )
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    message_metadata = Column(Text, nullable=True)  # JSON con tool_calls, etc.
    created_at = Column(DateTime, default=datetime.utcnow)


class OperatorToolCall(Base):
    """Llamada a herramienta desde mensajes de operador."""

    __tablename__ = "operator_tool_call"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("operator_message.id"), nullable=False)
    tool_name = Column(String(100), nullable=False)  # switch, hermes, browser, etc.
    status = Column(String(50), default="pending")  # pending, ok, error
    duration_ms = Column(Integer, nullable=True)
    result = Column(Text, nullable=True)  # JSON
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OperatorBrowserTask(Base):
    """Tarea de navegación (Playwright)."""

    __tablename__ = "operator_browser_task"

    id = Column(Integer, primary_key=True)
    session_id = Column(
        String(64), ForeignKey("operator_session.session_id"), nullable=False
    )
    url = Column(String(500), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, done, error
    snapshot_path = Column(String(255), nullable=True)
    result = Column(Text, nullable=True)  # JSON con resultado
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)


class OperatorSwitchAdjustment(Base):
    """Ajustes dinámicos del switch según histórico de operador."""

    __tablename__ = "operator_switch_adjustment"

    id = Column(Integer, primary_key=True)
    session_id = Column(
        String(64), ForeignKey("operator_session.session_id"), nullable=False
    )
    message_id = Column(Integer, ForeignKey("operator_message.id"), nullable=True)
    before_config = Column(Text, nullable=False)  # JSON: modelo activo, CLI prioridades
    after_config = Column(Text, nullable=False)  # JSON: nueva config
    reason = Column(Text, nullable=False)  # Por qué se ajustó
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)


def migrate_legacy_tables(engine=unified_engine):
    """
    Migra datos desde prefijos legacy (madre_, hermes_, hive_) a tablas
    unificadas para v6.4. No elimina las tablas legacy, solo consolida.
    """
    mapping = {
        "tasks": ["madre_tasks", "hermes_tasks", "hive_tasks"],
        "context": ["madre_context", "hermes_context", "hive_context"],
        "reports": ["madre_reports", "hermes_reports", "hive_reports"],
        "spawns": ["madre_spawns", "hermes_spawns", "hive_spawns"],
        "ia_decisions": [
            "madre_ia_decisions",
            "hermes_ia_decisions",
            "hive_ia_decisions",
        ],
        "module_health": [
            "madre_module_health",
            "hermes_module_health",
            "hive_module_health",
        ],
        "model_registry": [
            "madre_model_registry",
            "hermes_model_registry",
            "hive_model_registry",
        ],
        "cli_registry": [
            "madre_cli_registry",
            "hermes_cli_registry",
            "hive_cli_registry",
        ],
        "engines": ["madre_engines", "hermes_engines", "hive_engines"],
    }

    for unified_table, legacy_tables in mapping.items():
        for legacy in legacy_tables:
            _copy_table(engine, legacy, unified_table)


# ========== PHASE 3: CLI CONCENTRATOR + FLUZO TABLES ==========


class CLIUsageStat(Base):
    """Usage statistics for CLI calls (Phase 3)."""

    __tablename__ = "cli_usage_stats"

    id = Column(Integer, primary_key=True)
    provider_id = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
    latency_ms = Column(Integer, default=0)
    cost_estimated = Column(Float, default=0.0)
    tokens_estimated = Column(Integer, default=0)
    error_class = Column(String(100), nullable=True)


class CLIOnboardingState(Base):
    """Onboarding state for CLI providers (Phase 3)."""

    __tablename__ = "cli_onboarding_state"

    id = Column(Integer, primary_key=True)
    provider_id = Column(String(128), unique=True, nullable=False)
    state = Column(
        String(50), default="discovery"
    )  # discovery | pending | verified | failed
    notes = Column(Text, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FluzoSignal(Base):
    """FLUZO telemetry signals (Phase 3)."""

    __tablename__ = "fluzo_signals"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_load_1m = Column(Float, default=0.0)
    mem_pct = Column(Float, default=0.0)
    on_ac = Column(Boolean, default=True)
    battery_pct = Column(Integer, nullable=True)
    profile = Column(
        String(32), default="balanced"
    )  # low_power | balanced | performance


class RoutingEvent(Base):
    """Routing decision events (Phase 3)."""

    __tablename__ = "routing_events"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    trace_id = Column(String(36), nullable=False)
    route_type = Column(String(50), nullable=False)  # cli | local_model
    provider_id = Column(String(128), nullable=False)
    score = Column(Float, default=0.0)
    reasoning_short = Column(String(255), nullable=True)


class CopilotRuntimeServices(Base):
    """Copilot runtime services status tracking (for vx11_runtime_truth.py).

    Additive schema: service_name, host, port, health_url, status, last_check exist in legacy.
    New columns (http_code, latency_ms, endpoint_ok, snippet, checked_at) are added
    for enhanced monitoring without breaking existing schema.
    """

    __tablename__ = "copilot_runtime_services"

    id = Column(Integer, primary_key=True)
    service_name = Column(String(128), unique=True, nullable=False)
    host = Column(String(128), default="localhost")
    port = Column(Integer, nullable=False)
    health_url = Column(String(256), nullable=True)
    status = Column(String(32), default="unknown")  # OK, BROKEN, UNKNOWN
    http_code = Column(Integer, nullable=True)  # Last HTTP response code
    latency_ms = Column(Integer, nullable=True)  # Last latency in ms
    endpoint_ok = Column(String(128), nullable=True)  # Which endpoint responded
    snippet = Column(Text, nullable=True)  # Response snippet
    last_check = Column(DateTime, nullable=True)
    checked_at = Column(DateTime, nullable=True)  # Alternative timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


# Create all tables (solo una vez) y migrar legacy → unificada
if os.environ.get("VX11_TEST_IMPORT_SAFE", "0") in ("0", "false", "False", ""):
    # Normal runtime: crear tablas y migrar legacy -> unified
    Base.metadata.create_all(unified_engine)
    migrate_legacy_tables(unified_engine)
else:
    # En modo de import seguro para tests, evitamos crear/migrar tablas
    # para que los tests controlen la sesión/engine y no se poluyan datos en disco.
    pass

# Keep old engines dict for compatibility
engines = {db_name: unified_engine for db_name in DATABASES.keys()}
sessions = {db_name: unified_session_maker for db_name in DATABASES.keys()}


def get_session(db_name="madre"):
    """
    Get DB session for a module.
    En VX11 v6.0, todos los módulos usan la misma BD unificada (vx11.db).
    El parámetro db_name se mantiene por compatibilidad.
    """
    # Retornar sesión de la BD unificada
    return unified_session_maker()
