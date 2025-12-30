from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path
import os
import socket


def _resolve_docker_url(module_name: str, port: int) -> str:
    """Resolve module URL with Docker DNS fallback to localhost."""
    try:
        socket.gethostbyname(module_name)
        return f"http://{module_name}:{port}"
    except (socket.gaierror, OSError):
        # Fallback to localhost (for local dev)
        return f"http://localhost:{port}"


class VX11Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, protected_namespaces=()
    )

    # ========== CONFIGURACIÓN BASE ==========
    app_name: str = "VX11 System"
    # Canonical VX11 version
    version: str = "6.7.0"
    environment: str = Field(default="production")

    # ========== PUERTOS (Docker-based: 8000–8008) ==========
    tentaculo_link_port: int = 8000
    # Legacy alias kept for compatibility with old tooling
    gateway_port: int = 8000
    madre_port: int = 8001
    switch_port: int = 8002
    hermes_port: int = 8003
    hormiguero_port: int = 8004
    manifestator_port: int = 8005
    mcp_port: int = 8006
    shub_port: int = 8007
    spawner_port: int = 8008
    operator_port: int = 8011

    # ========== RUTAS INTERNAS (Docker /app/*) ==========
    # NO usar /home/elkakas314 dentro de contenedores
    BASE_PATH: str = "/app"
    CONFIG_PATH: str = "/app/config"
    MODELS_PATH: str = "/app/models"
    SANDBOX_PATH: str = "/app/sandbox"
    LOGS_PATH: str = "/app/logs"
    DATA_PATH: str = "/app/data"

    # ========== ULTRA-LOW-MEMORY MODE ==========
    ULTRA_LOW_MEMORY: bool = True
    max_memory_mb: int = 512  # Límite por contenedor
    max_model_size_mb: int = 256  # Límite de modelos descargados
    cache_ttl_seconds: int = 300

    # ========== URLs BASE (Docker networking con fallback a localhost) ==========
    tentaculo_link_url: str = Field(
        default_factory=lambda: _resolve_docker_url("tentaculo_link", 8000)
    )
    gateway_url: str = Field(
        default_factory=lambda: _resolve_docker_url("tentaculo_link", 8000)
    )
    madre_url: str = Field(default_factory=lambda: _resolve_docker_url("madre", 8001))
    switch_url: str = Field(default_factory=lambda: _resolve_docker_url("switch", 8002))
    hermes_url: str = Field(default_factory=lambda: _resolve_docker_url("hermes", 8003))
    hormiguero_url: str = Field(
        default_factory=lambda: _resolve_docker_url("hormiguero", 8004)
    )
    manifestator_url: str = Field(
        default_factory=lambda: _resolve_docker_url("manifestator", 8005)
    )
    mcp_url: str = Field(default_factory=lambda: _resolve_docker_url("mcp", 8006))
    shub_url: str = Field(
        default_factory=lambda: _resolve_docker_url("shubniggurath", 8007)
    )
    spawner_url: str = Field(
        default_factory=lambda: _resolve_docker_url("spawner", 8008)
    )
    operator_url: str = Field(
        default_factory=lambda: _resolve_docker_url("operator-backend", 8011)
    )

    # ========== SEGURIDAD ==========
    api_token: str = Field(default="vx11-token-production")
    enable_auth: bool = True
    token_header: str = "X-VX11-Token"
    require_https: bool = False  # En dev; activar en prod
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8011",
        "http://localhost:8020",
        "http://127.0.0.1:8011",
        "http://127.0.0.1:8020",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    testing_mode: bool = False  # Si True, puede desactivar auth en tests

    # ========== BASES DE DATOS ==========
    database_path: str = "/app/data/runtime"
    database_url: str = "sqlite:////app/data/runtime/vx11.db"

    # ========== CONFIGURACIÓN DE MODELOS IA ==========
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    local_model_endpoint: str = "http://localhost:11434"
    default_model: str = "auto"  # auto, local, deepseek

    # ========== HERMES (CLI TOOLS) ==========
    hermes_timeout: int = 30
    max_local_tokens: int = 1000

    # ========== MODELOS LOCALES Y DESCUBRIMIENTO ==========
    local_models_path: str = "/app/models"
    huggingface_cache_path: Optional[str] = "/app/models/.cache"
    max_local_models: int = 20
    max_local_models_gb: int = 2  # Ultra-low-memory: 2 GB max
    model_scan_interval_seconds: int = 300

    # ========== ENDPOINTS LOCALES ==========
    llama_cpp_endpoint: str = "http://localhost:8000"
    ollama_endpoint: str = "http://localhost:11434"
    hf_api_timeout: int = 30

    # ========== CLI REGISTRY ==========
    cli_registry_check_interval_seconds: int = 600

    # ========== PHASE 4: FLUZO INTEGRATION ==========
    enable_madre_fluzo: bool = (
        False  # Enable Madre FLUZO integration (default OFF for safety)
    )

    # ========== DEEPSEEK R1 CONFIGURATION (v7.0) ==========
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_daily_limit_tokens: int = 100000
    deepseek_monthly_limit_tokens: int = 3000000
    deepseek_reset_hour_utc: int = 0

    # ========== LEARNER (IA DECISIONES) ==========
    learner_db_name: str = "hive"
    learner_min_confidence: float = 0.5
    learner_decay_factor: float = 0.95

    # ========== AGREGADOR DE HEALTH ==========
    health_check_interval: int = 30
    health_timeout: int = 5

    @property
    def PORTS(self) -> dict:
        """Diccionario de puertos por módulo."""
        return {
            "tentaculo_link": self.tentaculo_link_port,
            "gateway": self.tentaculo_link_port,
            "madre": self.madre_port,
            "switch": self.switch_port,
            "hermes": self.hermes_port,
            "hormiguero": self.hormiguero_port,
            "manifestator": self.manifestator_port,
            "mcp": self.mcp_port,
            "shub": self.shub_port,
            "shubniggurath": self.shub_port,
            "spawner": self.spawner_port,
        }


# Instancia global (lazy)
# Avoid creating the VX11Settings() at import time because that may
# execute network/system calls (default_factory lambdas) and can
# cause language servers or import-time introspection to hang.
# We expose `settings` as a lightweight proxy that instantiates the
# real settings object on first attribute access.
from typing import Any


def _load_settings() -> VX11Settings:
    return VX11Settings()


class _SettingsProxy:
    """Lazy proxy for VX11Settings.

    Accessing any attribute will trigger real settings creation once.
    This keeps module import cheap and avoids side-effects during static
    analysis or language-server indexing.
    """

    __slots__ = ("_real",)

    def __init__(self) -> None:
        object.__setattr__(self, "_real", None)

    def _ensure(self) -> VX11Settings:
        real = object.__getattribute__(self, "_real")
        if real is None:
            real = _load_settings()
            object.__setattr__(self, "_real", real)
        return real

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ensure(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        return setattr(self._ensure(), name, value)


# Public proxy instance used across the codebase
settings: _SettingsProxy = _SettingsProxy()
