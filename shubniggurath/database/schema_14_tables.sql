-- Shub-Niggurath PostgreSQL Schema v1.0
-- 14 Tablas profesionales para Produccion Audio Estudio AAA
-- Generado: 2025-12-09

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Tipos enumerados
CREATE TYPE tenant_tier AS ENUM ('free', 'pro', 'enterprise', 'studio_aaa');
CREATE TYPE project_complexity AS ENUM ('simple', 'medium', 'complex', 'epic', 'cinematic');
CREATE TYPE audio_quality AS ENUM ('draft', 'good', 'professional', 'broadcast', 'master');
CREATE TYPE asset_type AS ENUM ('source', 'stem', 'mix', 'master', 'reference', 'sample', 'loop', 'impulse_response', 'amp_profile', 'noise_profile', 'ambience', 'foley', 'dialogue', 'music');
CREATE TYPE project_status AS ENUM ('draft', 'recording', 'editing', 'mixing', 'mastering', 'review', 'completed', 'archived');
CREATE TYPE storage_tier AS ENUM ('hot', 'warm', 'cold');

-- Tabla 1: Tenants (multi-tenancy)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    studio_name VARCHAR(500),
    tier tenant_tier NOT NULL DEFAULT 'pro',
    storage_quota_gb INTEGER DEFAULT 500 CHECK (storage_quota_gb >= 1),
    monthly_render_minutes INTEGER DEFAULT 5000,
    max_concurrent_jobs INTEGER DEFAULT 10 CHECK (max_concurrent_jobs >= 1),
    gpu_access BOOLEAN DEFAULT FALSE,
    max_audio_quality audio_quality DEFAULT 'professional',
    audio_retention_days INTEGER DEFAULT 730,
    project_retention_days INTEGER DEFAULT 1825,
    analysis_retention_days INTEGER DEFAULT 365,
    log_retention_days INTEGER DEFAULT 180,
    default_sample_rate INTEGER DEFAULT 48000,
    default_bit_depth INTEGER DEFAULT 24,
    default_format VARCHAR(10) DEFAULT 'wav',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla 2: Studio Profiles
CREATE TABLE IF NOT EXISTS studio_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    studio_type VARCHAR(50) NOT NULL,
    room_dimensions JSONB,
    acoustic_treatment JSONB,
    rt60_targets JSONB,
    rt60_measured JSONB,
    background_noise_nc INTEGER,
    monitor_system JSONB,
    monitor_calibration JSONB,
    room_correction_system VARCHAR(100),
    audio_interface JSONB,
    outboard_gear JSONB,
    microphone_collection JSONB,
    preamp_collection JSONB,
    reaper_config_path VARCHAR(1024),
    custom_actions JSONB,
    color_themes JSONB,
    template_projects JSONB,
    hardware_routing JSONB,
    monitor_setups JSONB,
    headphone_mixes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

-- Tabla 3: Audio Projects
CREATE TABLE IF NOT EXISTS audio_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    studio_profile_id UUID REFERENCES studio_profiles(id),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    client_name VARCHAR(300),
    project_code VARCHAR(100),
    project_type VARCHAR(50) NOT NULL,
    genre_main VARCHAR(100) NOT NULL,
    genre_sub VARCHAR(100)[],
    mood_tags VARCHAR(50)[],
    intensity_level INTEGER CHECK (intensity_level BETWEEN 1 AND 10),
    bpm DECIMAL(6,3),
    key_detected VARCHAR(10),
    key_user_selected VARCHAR(10),
    time_signature VARCHAR(10) DEFAULT '4/4',
    project_complexity project_complexity DEFAULT 'medium',
    target_audio_quality audio_quality DEFAULT 'professional',
    reaper_project_path VARCHAR(1024),
    reaper_project_hash BYTEA,
    ai_quality_score DECIMAL(4,3),
    ai_confidence_score DECIMAL(4,3),
    reference_tracks UUID[],
    estimated_duration INTERVAL,
    total_processing_time INTERVAL DEFAULT '0 seconds',
    peak_memory_mb INTEGER DEFAULT 0,
    total_storage_bytes BIGINT DEFAULT 0,
    total_plugin_count INTEGER DEFAULT 0,
    parent_version_id UUID,
    version_description TEXT,
    version_notes JSONB,
    is_master_version BOOLEAN DEFAULT FALSE,
    project_status project_status DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE (tenant_id, project_code)
);

-- Tabla 4: Audio Assets
CREATE TABLE IF NOT EXISTS audio_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES audio_projects(id) ON DELETE CASCADE,
    asset_type asset_type NOT NULL,
    instrument_category VARCHAR(100),
    performance_style VARCHAR(100),
    source_instrument VARCHAR(100),
    recording_environment VARCHAR(100),
    file_path VARCHAR(1024) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_hash_sha256 BYTEA NOT NULL,
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes > 0),
    storage_tier storage_tier DEFAULT 'hot',
    duration_ms BIGINT,
    sample_rate INTEGER CHECK (sample_rate IN (44100, 48000, 88200, 96000, 176400, 192000)),
    bit_depth INTEGER CHECK (bit_depth IN (16, 24, 32)),
    channels INTEGER CHECK (channels BETWEEN 1 AND 8),
    file_format VARCHAR(10),
    loudness_integrated_lufs DECIMAL(6,2),
    loudness_range_lu DECIMAL(6,2),
    loudness_max_momentary_lufs DECIMAL(6,2),
    loudness_max_short_term_lufs DECIMAL(6,2),
    true_peak_dbfs DECIMAL(6,2),
    dynamic_range_dr DECIMAL(6,2),
    crest_factor DECIMAL(6,2),
    spectral_centroid DECIMAL(8,4),
    spectral_rolloff DECIMAL(8,4),
    spectral_flux DECIMAL(8,4),
    zero_crossing_rate DECIMAL(8,4),
    mfcc_features JSONB,
    chroma_features JSONB,
    spectral_contrast JSONB,
    spectral_flatness DECIMAL(8,6),
    bpm_detected DECIMAL(6,3),
    bpm_confidence DECIMAL(4,3),
    key_detected VARCHAR(10),
    key_confidence DECIMAL(4,3),
    scale_type VARCHAR(20),
    harmonic_complexity DECIMAL(4,3),
    percussiveness DECIMAL(4,3),
    onset_strength DECIMAL(6,4),
    acoustic_fingerprint BYTEA,
    musical_fingerprint BYTEA,
    noise_floor_dbfs DECIMAL(6,2),
    clipping_count INTEGER DEFAULT 0,
    dc_offset DECIMAL(8,6),
    phase_correlation DECIMAL(4,3),
    transient_sharpness DECIMAL(6,4),
    signal_to_noise_ratio DECIMAL(6,2),
    ai_model_used VARCHAR(200),
    generation_parameters JSONB,
    processing_history JSONB,
    source_asset_id UUID REFERENCES audio_assets(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, file_hash_sha256)
);

-- Tabla 5: Plugin Registry
CREATE TABLE IF NOT EXISTS plugin_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    vendor VARCHAR(200) NOT NULL,
    version VARCHAR(50) NOT NULL,
    plugin_type VARCHAR(10) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(100),
    file_path VARCHAR(1024) NOT NULL,
    unique_id VARCHAR(100) NOT NULL,
    sdk_version VARCHAR(50),
    format_version VARCHAR(50),
    architecture VARCHAR(10),
    cpu_usage_baseline DECIMAL(5,2),
    latency_samples INTEGER DEFAULT 0,
    memory_usage_mb INTEGER DEFAULT 0,
    real_time_safe BOOLEAN DEFAULT TRUE,
    oversampling_capable BOOLEAN DEFAULT FALSE,
    multichannel_capable BOOLEAN DEFAULT FALSE,
    parameters JSONB NOT NULL,
    factory_presets JSONB,
    user_presets JSONB,
    parameter_groups JSONB,
    parameter_importance_scores JSONB,
    style_preset_mappings JSONB,
    neural_parameter_estimation BOOLEAN DEFAULT FALSE,
    ai_recommended_settings JSONB,
    signal_to_noise_ratio DECIMAL(6,2),
    total_harmonic_distortion DECIMAL(6,3),
    frequency_response_range JSONB,
    impulse_response_analysis JSONB,
    aliasing_performance DECIMAL(5,3),
    operating_systems VARCHAR(10)[] DEFAULT '{windows,linux,macos}',
    sample_rate_support INTEGER[] DEFAULT '{44100,48000,88200,96000,192000}',
    channel_configs VARCHAR(20)[] DEFAULT '{mono,stereo}',
    daw_compatibility VARCHAR(50)[],
    total_usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(4,3),
    average_rating DECIMAL(3,2),
    common_use_cases JSONB,
    scan_version INTEGER DEFAULT 1,
    last_validated TIMESTAMPTZ DEFAULT NOW(),
    validation_errors TEXT[],
    blacklisted BOOLEAN DEFAULT FALSE,
    blacklist_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, unique_id, version)
);

-- Tabla 6: Impulse Response Library
CREATE TABLE IF NOT EXISTS impulse_response_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amplifier_model VARCHAR(200),
    speaker_model VARCHAR(200),
    microphone_model VARCHAR(200),
    microphone_position VARCHAR(100),
    room_size VARCHAR(50),
    sample_rate INTEGER NOT NULL CHECK (sample_rate IN (44100, 48000, 96000, 192000)),
    length_samples INTEGER NOT NULL CHECK (length_samples > 0),
    format VARCHAR(10),
    bit_depth INTEGER CHECK (bit_depth IN (16, 24, 32)),
    rt60_measurements JSONB,
    frequency_response JSONB,
    early_reflections_analysis JSONB,
    direct_to_reverb_ratio DECIMAL(5,3),
    capture_environment VARCHAR(100),
    capture_equipment JSONB,
    capture_methodology VARCHAR(200),
    file_path VARCHAR(1024) NOT NULL,
    file_hash_sha256 BYTEA NOT NULL,
    file_size_bytes BIGINT,
    usage_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    common_pairings JSONB,
    user_tags VARCHAR(50)[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, file_hash_sha256)
);

-- Tabla 7: Amp Profiles
CREATE TABLE IF NOT EXISTS amp_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    amplifier_model VARCHAR(200) NOT NULL,
    microphone_model VARCHAR(200),
    microphone_distance DECIMAL(4,2),
    microphone_angle DECIMAL(5,2),
    recording_level DECIMAL(5,2),
    cabinet_type VARCHAR(100),
    cabinet_size VARCHAR(100),
    mic_preamp JSONB,
    compressor_settings JSONB,
    eq_settings JSONB,
    profile_data BYTEA NOT NULL,
    frequency_response JSONB,
    harmonic_analysis JSONB,
    noise_floor DECIMAL(6,2),
    file_path VARCHAR(1024) NOT NULL,
    file_hash_sha256 BYTEA NOT NULL,
    usage_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, file_hash_sha256)
);

-- Tabla 8: Mixing Sessions
CREATE TABLE IF NOT EXISTS mixing_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES audio_projects(id) ON DELETE CASCADE,
    engineer_id VARCHAR(100),
    session_name VARCHAR(300) NOT NULL,
    mix_version INTEGER DEFAULT 1,
    target_loudness_lufs DECIMAL(6,2),
    target_true_peak DECIMAL(6,2),
    reference_track_id UUID REFERENCES audio_assets(id),
    mixing_style VARCHAR(100),
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    total_duration INTERVAL,
    mix_bus_chain JSONB,
    track_count INTEGER,
    plugin_count INTEGER,
    automation_points INTEGER DEFAULT 0,
    estimated_delivery_lufs DECIMAL(6,2),
    estimated_delivery_true_peak DECIMAL(6,2),
    notes TEXT,
    session_state JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla 9: Mastering Sessions
CREATE TABLE IF NOT EXISTS mastering_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES audio_projects(id) ON DELETE CASCADE,
    mix_session_id UUID REFERENCES mixing_sessions(id),
    engineer_id VARCHAR(100),
    session_name VARCHAR(300) NOT NULL,
    mastering_chain JSONB,
    target_loudness_lufs DECIMAL(6,2),
    target_true_peak DECIMAL(6,2),
    target_format VARCHAR(50),
    linear_phase_eq BOOLEAN DEFAULT TRUE,
    multiband_compression JSONB,
    reference_loudness_lufs DECIMAL(6,2),
    metering_type VARCHAR(50),
    output_specs JSONB,
    delivery_format VARCHAR(50)[],
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    total_duration INTERVAL,
    notes TEXT,
    session_state JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla 10: Audio Analysis Cache
CREATE TABLE IF NOT EXISTS audio_analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES audio_assets(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_version VARCHAR(50),
    analysis_data JSONB NOT NULL,
    processing_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    UNIQUE (tenant_id, asset_id, analysis_type, analysis_version)
);

-- Tabla 11: Preset Library
CREATE TABLE IF NOT EXISTS preset_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(300) NOT NULL,
    plugin_id UUID REFERENCES plugin_registry(id),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    preset_data JSONB NOT NULL,
    tags VARCHAR(50)[],
    description TEXT,
    author VARCHAR(200),
    ai_generated BOOLEAN DEFAULT FALSE,
    ai_confidence DECIMAL(4,3),
    style_match JSONB,
    usage_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2),
    suitable_for JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, name, plugin_id)
);

-- Tabla 12: Audio Problems Detected
CREATE TABLE IF NOT EXISTS audio_problems_detected (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES audio_assets(id) ON DELETE CASCADE,
    problem_type VARCHAR(50) NOT NULL,
    severity DECIMAL(4,3),
    description TEXT NOT NULL,
    location_ms BIGINT,
    duration_ms BIGINT,
    suggested_fix TEXT,
    auto_correctable BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla 13: VX11 Integration Log
CREATE TABLE IF NOT EXISTS vx11_integration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    vx11_task_id UUID,
    vx11_spawn_id UUID,
    shub_asset_id UUID REFERENCES audio_assets(id),
    shub_session_id UUID,
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50),
    sync_direction VARCHAR(20),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB
);

-- Tabla 14: AI Training Data
CREATE TABLE IF NOT EXISTS ai_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES audio_assets(id),
    session_id UUID,
    input_parameters JSONB NOT NULL,
    output_result JSONB NOT NULL,
    feedback_score DECIMAL(4,3),
    model_version VARCHAR(50),
    training_epoch INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    used_in_training BOOLEAN DEFAULT FALSE
);

-- Índices
CREATE INDEX idx_projects_tenant_created ON audio_projects(tenant_id, created_at DESC);
CREATE INDEX idx_projects_status ON audio_projects(project_status, updated_at);
CREATE INDEX idx_assets_project ON audio_assets(tenant_id, project_id, created_at);
CREATE INDEX idx_assets_loudness ON audio_assets(loudness_integrated_lufs, loudness_range_lu);
CREATE INDEX idx_plugins_category ON plugin_registry(category, vendor);
CREATE INDEX idx_sessions_project ON mixing_sessions(project_id, created_at DESC);
CREATE INDEX idx_mastering_project ON mastering_sessions(project_id, created_at DESC);
CREATE INDEX idx_analysis_cache_asset ON audio_analysis_cache(asset_id, analysis_type);
CREATE INDEX idx_problems_asset ON audio_problems_detected(asset_id, severity DESC);
CREATE INDEX idx_vx11_log_task ON vx11_integration_log(vx11_task_id, timestamp DESC);

-- Comentarios
COMMENT ON TABLE tenants IS 'Multi-tenancy: Studios y usuarios';
COMMENT ON TABLE audio_projects IS 'Proyectos de audio con versionado';
COMMENT ON TABLE audio_assets IS 'Assets con análisis DSP completo';
COMMENT ON TABLE plugin_registry IS 'Registro de plugins VST/AU/CLAP';
COMMENT ON TABLE mixing_sessions IS 'Sesiones de mezcla con estado';
COMMENT ON TABLE mastering_sessions IS 'Sesiones de mastering profesional';
COMMENT ON TABLE vx11_integration_log IS 'Log de sincronización con VX11';
