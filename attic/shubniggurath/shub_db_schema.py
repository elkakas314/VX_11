"""
Shub-Niggurath BD Schema — Tablas, Vistas, Índices
SQLite con migraciones correctas
"""

from typing import List, Dict, Any

SQL_SCHEMA = """
-- ============================================================================
-- PROYECTO DE AUDIO
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_audio_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- ============================================================================
-- REAPER INTEGRATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS reaper_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    track_index INTEGER NOT NULL,
    track_name TEXT,
    track_guid TEXT UNIQUE,
    volume_db REAL DEFAULT 0.0,
    pan_percent REAL DEFAULT 0.0,
    mute INTEGER DEFAULT 0,
    solo INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES project_audio_state(project_id),
    UNIQUE(project_id, track_index)
);

CREATE TABLE IF NOT EXISTS reaper_track_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    state_type TEXT,
    state_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(track_id) REFERENCES reaper_tracks(id)
);

CREATE TABLE IF NOT EXISTS reaper_item_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    item_index INTEGER NOT NULL,
    duration_seconds REAL,
    analysis_result JSON,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(track_id) REFERENCES reaper_tracks(id)
);

-- ============================================================================
-- ANÁLISIS Y CACHÉ
-- ============================================================================

CREATE TABLE IF NOT EXISTS analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    analysis_data JSON NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES project_audio_state(project_id),
    UNIQUE(project_id, analysis_type)
);

CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT,
    content TEXT,
    context_state JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES assistant_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS assistant_sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT,
    mode TEXT DEFAULT 'conversational',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_state JSON,
    FOREIGN KEY(project_id) REFERENCES project_audio_state(project_id)
);

CREATE TABLE IF NOT EXISTS mixing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    project_id TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_data JSON,
    FOREIGN KEY(project_id) REFERENCES project_audio_state(project_id)
);

CREATE TABLE IF NOT EXISTS mastering_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    mix_id TEXT,
    target_loudness REAL,
    status TEXT DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_data JSON
);

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_project_audio_state_project_id 
    ON project_audio_state(project_id);

CREATE INDEX IF NOT EXISTS idx_reaper_tracks_project_id 
    ON reaper_tracks(project_id);

CREATE INDEX IF NOT EXISTS idx_reaper_item_analysis_track_id 
    ON reaper_item_analysis(track_id);

CREATE INDEX IF NOT EXISTS idx_analysis_cache_project_type 
    ON analysis_cache(project_id, analysis_type);

CREATE INDEX IF NOT EXISTS idx_conversation_history_session 
    ON conversation_history(session_id);

CREATE INDEX IF NOT EXISTS idx_mixing_sessions_project 
    ON mixing_sessions(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mastering_sessions_created 
    ON mastering_sessions(created_at DESC);

-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_project_status AS
SELECT 
    p.project_id,
    p.name,
    p.status,
    COUNT(DISTINCT rt.id) as track_count,
    MAX(rt.updated_at) as last_track_update,
    p.updated_at
FROM project_audio_state p
LEFT JOIN reaper_tracks rt ON p.project_id = rt.project_id
GROUP BY p.project_id;

CREATE VIEW IF NOT EXISTS v_active_sessions AS
SELECT 
    s.session_id,
    s.project_id,
    s.mode,
    COUNT(ch.id) as message_count,
    s.last_activity
FROM assistant_sessions s
LEFT JOIN conversation_history ch ON s.session_id = ch.session_id
WHERE datetime(s.last_activity) > datetime('now', '-24 hours')
GROUP BY s.session_id;

-- ============================================================================
-- TRIGGERS PARA TIMESTAMPS
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS update_project_timestamp
AFTER UPDATE ON project_audio_state
FOR EACH ROW
BEGIN
    UPDATE project_audio_state SET updated_at = CURRENT_TIMESTAMP 
    WHERE project_id = NEW.project_id;
END;

CREATE TRIGGER IF NOT EXISTS update_track_timestamp
AFTER UPDATE ON reaper_tracks
FOR EACH ROW
BEGIN
    UPDATE reaper_tracks SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;
"""

# ============================================================================
# MIGRATION FUNCTIONS
# ============================================================================

def get_migrations() -> List[tuple]:
    """
    Retorna lista de (version, sql_statements)
    Para aplicarse en orden
    """
    return [
        ("1.0.0", SQL_SCHEMA),
    ]


__all__ = [
    "SQL_SCHEMA",
    "get_migrations",
]
