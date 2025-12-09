"""Configuration additions for Shubniggurath"""

import os

# Shub-Niggurath settings
SHUBNIGGURATH_PORT = int(os.getenv("SHUBNIGGURATH_PORT", 8007))
SHUBNIGGURATH_HOST = os.getenv("SHUBNIGGURATH_HOST", "0.0.0.0")

# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "shubniggurath")
POSTGRES_USER = os.getenv("POSTGRES_USER", "shubniggurath")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# REAPER RPC
REAPER_HOST = os.getenv("REAPER_HOST", "localhost")
REAPER_PORT = int(os.getenv("REAPER_PORT", 7899))

# Audio processing
DEFAULT_SAMPLE_RATE = int(os.getenv("DEFAULT_SAMPLE_RATE", 48000))
DEFAULT_BIT_DEPTH = int(os.getenv("DEFAULT_BIT_DEPTH", 24))
DEFAULT_CHANNELS = int(os.getenv("DEFAULT_CHANNELS", 2))

# Engine configuration
ENABLED_ENGINES = [
    "analyzer",
    "transient_detector",
    "eq_generator",
    "dynamics_processor",
    "stereo_processor",
    "fx_engine",
    "ai_recommender",
    "ai_mastering",
    "preset_generator",
    "batch_processor",
]

# Multi-tenancy
DEFAULT_TENANT_QUOTA_GB = int(os.getenv("TENANT_QUOTA_GB", 500))
DEFAULT_TENANT_TIER = os.getenv("TENANT_TIER", "pro")
