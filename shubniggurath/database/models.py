"""SQLAlchemy ORM Models - Shub-Niggurath Database"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Boolean, LargeBinary, ARRAY, Numeric, Interval, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    studio_name = Column(String(500))
    tier = Column(String(50), default="pro")
    storage_quota_gb = Column(Integer, default=500)
    monthly_render_minutes = Column(Integer, default=5000)
    max_concurrent_jobs = Column(Integer, default=10)
    gpu_access = Column(Boolean, default=False)
    max_audio_quality = Column(String(50), default="professional")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    projects = relationship("AudioProject", back_populates="tenant", cascade="all, delete")
    assets = relationship("AudioAsset", back_populates="tenant", cascade="all, delete")
    studio_profiles = relationship("StudioProfile", back_populates="tenant", cascade="all, delete")


class StudioProfile(Base):
    __tablename__ = "studio_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(300), nullable=False)
    studio_type = Column(String(50), nullable=False)
    room_dimensions = Column(JSON)
    acoustic_treatment = Column(JSON)
    rt60_targets = Column(JSON)
    rt60_measured = Column(JSON)
    background_noise_nc = Column(Integer)
    monitor_system = Column(JSON)
    monitor_calibration = Column(JSON)
    room_correction_system = Column(String(100))
    audio_interface = Column(JSON)
    outboard_gear = Column(JSON)
    microphone_collection = Column(JSON)
    preamp_collection = Column(JSON)
    reaper_config_path = Column(String(1024))
    custom_actions = Column(JSON)
    color_themes = Column(JSON)
    template_projects = Column(JSON)
    hardware_routing = Column(JSON)
    monitor_setups = Column(JSON)
    headphone_mixes = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_studio_profile"),
    )
    
    tenant = relationship("Tenant", back_populates="studio_profiles")


class AudioProject(Base):
    __tablename__ = "audio_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    studio_profile_id = Column(UUID(as_uuid=True), ForeignKey("studio_profiles.id"))
    name = Column(String(500), nullable=False)
    description = Column(String(2000))
    client_name = Column(String(300))
    project_code = Column(String(100))
    project_type = Column(String(50), nullable=False)
    genre_main = Column(String(100), nullable=False)
    genre_sub = Column(ARRAY(String))
    mood_tags = Column(ARRAY(String))
    intensity_level = Column(Integer)
    bpm = Column(Numeric(6, 3))
    key_detected = Column(String(10))
    key_user_selected = Column(String(10))
    time_signature = Column(String(10), default="4/4")
    project_complexity = Column(String(50), default="medium")
    target_audio_quality = Column(String(50), default="professional")
    reaper_project_path = Column(String(1024))
    reaper_project_hash = Column(LargeBinary)
    ai_quality_score = Column(Numeric(4, 3))
    ai_confidence_score = Column(Numeric(4, 3))
    reference_tracks = Column(ARRAY(UUID(as_uuid=True)))
    estimated_duration = Column(Interval)
    total_processing_time = Column(Interval, default="0 seconds")
    peak_memory_mb = Column(Integer, default=0)
    total_storage_bytes = Column(Integer, default=0)
    total_plugin_count = Column(Integer, default=0)
    parent_version_id = Column(UUID(as_uuid=True))
    version_description = Column(String(500))
    version_notes = Column(JSON)
    is_master_version = Column(Boolean, default=False)
    project_status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_code", name="uq_project_code"),
    )
    
    tenant = relationship("Tenant", back_populates="projects")
    assets = relationship("AudioAsset", back_populates="project", cascade="all, delete")


class AudioAsset(Base):
    __tablename__ = "audio_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("audio_projects.id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String(50), nullable=False)
    instrument_category = Column(String(100))
    performance_style = Column(String(100))
    source_instrument = Column(String(100))
    recording_environment = Column(String(100))
    file_path = Column(String(1024), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_hash_sha256 = Column(LargeBinary, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_tier = Column(String(10), default="hot")
    duration_ms = Column(Integer)
    sample_rate = Column(Integer)
    bit_depth = Column(Integer)
    channels = Column(Integer)
    file_format = Column(String(10))
    loudness_integrated_lufs = Column(Numeric(6, 2))
    loudness_range_lu = Column(Numeric(6, 2))
    loudness_max_momentary_lufs = Column(Numeric(6, 2))
    loudness_max_short_term_lufs = Column(Numeric(6, 2))
    true_peak_dbfs = Column(Numeric(6, 2))
    dynamic_range_dr = Column(Numeric(6, 2))
    crest_factor = Column(Numeric(6, 2))
    spectral_centroid = Column(Numeric(8, 4))
    spectral_rolloff = Column(Numeric(8, 4))
    spectral_flux = Column(Numeric(8, 4))
    zero_crossing_rate = Column(Numeric(8, 4))
    mfcc_features = Column(JSON)
    chroma_features = Column(JSON)
    spectral_contrast = Column(JSON)
    spectral_flatness = Column(Numeric(8, 6))
    bpm_detected = Column(Numeric(6, 3))
    bpm_confidence = Column(Numeric(4, 3))
    key_detected = Column(String(10))
    key_confidence = Column(Numeric(4, 3))
    scale_type = Column(String(20))
    harmonic_complexity = Column(Numeric(4, 3))
    percussiveness = Column(Numeric(4, 3))
    onset_strength = Column(Numeric(6, 4))
    acoustic_fingerprint = Column(LargeBinary)
    musical_fingerprint = Column(LargeBinary)
    noise_floor_dbfs = Column(Numeric(6, 2))
    clipping_count = Column(Integer, default=0)
    dc_offset = Column(Numeric(8, 6))
    phase_correlation = Column(Numeric(4, 3))
    transient_sharpness = Column(Numeric(6, 4))
    signal_to_noise_ratio = Column(Numeric(6, 2))
    ai_model_used = Column(String(200))
    generation_parameters = Column(JSON)
    processing_history = Column(JSON)
    source_asset_id = Column(UUID(as_uuid=True), ForeignKey("audio_assets.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_hash_sha256", name="uq_asset_hash"),
    )
    
    tenant = relationship("Tenant", back_populates="assets")
    project = relationship("AudioProject", back_populates="assets")


class PluginRegistry(Base):
    __tablename__ = "plugin_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(300), nullable=False)
    vendor = Column(String(200), nullable=False)
    version = Column(String(50), nullable=False)
    plugin_type = Column(String(10), nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(100))
    file_path = Column(String(1024), nullable=False)
    unique_id = Column(String(100), nullable=False)
    sdk_version = Column(String(50))
    format_version = Column(String(50))
    architecture = Column(String(10))
    cpu_usage_baseline = Column(Numeric(5, 2))
    latency_samples = Column(Integer, default=0)
    memory_usage_mb = Column(Integer, default=0)
    real_time_safe = Column(Boolean, default=True)
    oversampling_capable = Column(Boolean, default=False)
    multichannel_capable = Column(Boolean, default=False)
    parameters = Column(JSON, nullable=False)
    factory_presets = Column(JSON)
    user_presets = Column(JSON)
    parameter_groups = Column(JSON)
    parameter_importance_scores = Column(JSON)
    style_preset_mappings = Column(JSON)
    neural_parameter_estimation = Column(Boolean, default=False)
    ai_recommended_settings = Column(JSON)
    signal_to_noise_ratio = Column(Numeric(6, 2))
    total_harmonic_distortion = Column(Numeric(6, 3))
    frequency_response_range = Column(JSON)
    impulse_response_analysis = Column(JSON)
    aliasing_performance = Column(Numeric(5, 3))
    operating_systems = Column(ARRAY(String), default=['windows', 'linux', 'macos'])
    sample_rate_support = Column(ARRAY(Integer), default=[44100, 48000, 96000, 192000])
    channel_configs = Column(ARRAY(String), default=['mono', 'stereo'])
    daw_compatibility = Column(ARRAY(String))
    total_usage_count = Column(Integer, default=0)
    success_rate = Column(Numeric(4, 3))
    average_rating = Column(Numeric(3, 2))
    common_use_cases = Column(JSON)
    scan_version = Column(Integer, default=1)
    last_validated = Column(DateTime, default=datetime.utcnow)
    validation_errors = Column(ARRAY(String))
    blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "unique_id", "version", name="uq_plugin"),
    )


class ImpulseResponseLibrary(Base):
    __tablename__ = "impulse_response_library"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(300), nullable=False)
    category = Column(String(50), nullable=False)
    amplifier_model = Column(String(200))
    speaker_model = Column(String(200))
    microphone_model = Column(String(200))
    microphone_position = Column(String(100))
    room_size = Column(String(50))
    sample_rate = Column(Integer, nullable=False)
    length_samples = Column(Integer, nullable=False)
    format = Column(String(10))
    bit_depth = Column(Integer)
    rt60_measurements = Column(JSON)
    frequency_response = Column(JSON)
    early_reflections_analysis = Column(JSON)
    direct_to_reverb_ratio = Column(Numeric(5, 3))
    capture_environment = Column(String(100))
    capture_equipment = Column(JSON)
    capture_methodology = Column(String(200))
    file_path = Column(String(1024), nullable=False)
    file_hash_sha256 = Column(LargeBinary, nullable=False)
    file_size_bytes = Column(Integer)
    usage_count = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2))
    common_pairings = Column(JSON)
    user_tags = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_hash_sha256", name="uq_ir_hash"),
    )


class MixingSession(Base):
    __tablename__ = "mixing_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("audio_projects.id", ondelete="CASCADE"), nullable=False)
    engineer_id = Column(String(100))
    session_name = Column(String(300), nullable=False)
    mix_version = Column(Integer, default=1)
    target_loudness_lufs = Column(Numeric(6, 2))
    target_true_peak = Column(Numeric(6, 2))
    reference_track_id = Column(UUID(as_uuid=True), ForeignKey("audio_assets.id"))
    mixing_style = Column(String(100))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_duration = Column(Interval)
    mix_bus_chain = Column(JSON)
    track_count = Column(Integer)
    plugin_count = Column(Integer)
    automation_points = Column(Integer, default=0)
    estimated_delivery_lufs = Column(Numeric(6, 2))
    estimated_delivery_true_peak = Column(Numeric(6, 2))
    notes = Column(String(2000))
    session_state = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasteringSession(Base):
    __tablename__ = "mastering_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("audio_projects.id", ondelete="CASCADE"), nullable=False)
    mix_session_id = Column(UUID(as_uuid=True), ForeignKey("mixing_sessions.id"))
    engineer_id = Column(String(100))
    session_name = Column(String(300), nullable=False)
    mastering_chain = Column(JSON)
    target_loudness_lufs = Column(Numeric(6, 2))
    target_true_peak = Column(Numeric(6, 2))
    target_format = Column(String(50))
    linear_phase_eq = Column(Boolean, default=True)
    multiband_compression = Column(JSON)
    reference_loudness_lufs = Column(Numeric(6, 2))
    metering_type = Column(String(50))
    output_specs = Column(JSON)
    delivery_format = Column(ARRAY(String))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_duration = Column(Interval)
    notes = Column(String(2000))
    session_state = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AudioAnalysisCache(Base):
    __tablename__ = "audio_analysis_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("audio_assets.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    analysis_version = Column(String(50))
    analysis_data = Column(JSON, nullable=False)
    processing_time_ms = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "asset_id", "analysis_type", "analysis_version", name="uq_analysis_cache"),
    )


class PresetLibrary(Base):
    __tablename__ = "preset_library"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(300), nullable=False)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey("plugin_registry.id"))
    category = Column(String(100))
    subcategory = Column(String(100))
    preset_data = Column(JSON, nullable=False)
    tags = Column(ARRAY(String))
    description = Column(String(2000))
    author = Column(String(200))
    ai_generated = Column(Boolean, default=False)
    ai_confidence = Column(Numeric(4, 3))
    style_match = Column(JSON)
    usage_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2))
    suitable_for = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "plugin_id", name="uq_preset"),
    )


class AudioProblemDetected(Base):
    __tablename__ = "audio_problems_detected"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("audio_assets.id", ondelete="CASCADE"), nullable=False)
    problem_type = Column(String(50), nullable=False)
    severity = Column(Numeric(4, 3), nullable=False)
    description = Column(String(1000), nullable=False)
    location_ms = Column(Integer)
    duration_ms = Column(Integer)
    suggested_fix = Column(String(500))
    auto_correctable = Column(Boolean, default=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class VX11IntegrationLog(Base):
    __tablename__ = "vx11_integration_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    vx11_task_id = Column(UUID(as_uuid=True))
    vx11_spawn_id = Column(UUID(as_uuid=True))
    shub_asset_id = Column(UUID(as_uuid=True), ForeignKey("audio_assets.id"))
    shub_session_id = Column(UUID(as_uuid=True))
    action = Column(String(100), nullable=False)
    status = Column(String(50))
    sync_direction = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)
    error_message = Column(String(500))
    meta_info = Column(JSON)


class AITrainingData(Base):
    __tablename__ = "ai_training_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("audio_assets.id"))
    session_id = Column(UUID(as_uuid=True))
    input_parameters = Column(JSON, nullable=False)
    output_result = Column(JSON, nullable=False)
    feedback_score = Column(Numeric(4, 3))
    model_version = Column(String(50))
    training_epoch = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_in_training = Column(Boolean, default=False)


async def init_db(engine):
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
