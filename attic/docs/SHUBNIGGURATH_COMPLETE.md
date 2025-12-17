# Shubniggurath v1.0 - Audio Studio AAA Platform

## Overview

Shubniggurath is a professional audio processing platform integrated with VX11 v6.7, providing:

- **10 DSP Engines**: Analyzer, Transient Detector, EQ Generator, Dynamics, Stereo, FX, AI Recommender, AI Mastering, Preset Generator, Batch Processor
- **PostgreSQL 14**: 14-table schema with multi-tenancy, versioning, and full-text search
- **REAPER DAW Integration**: HTTP RPC for seamless DAW control
- **VX11 Bridge**: Bidirectional sync with Switch, Madre, MCP, Hormiguero, Manifestator
- **Operator Dashboard**: Real-time monitoring and control UI
- **AI-Powered**: DeepSeek R1 reasoning for advanced audio analysis

## Architecture

```
User/Copilot
    ↓
Tentáculo Link (8000) [Gateway]
    ↓
Madre (8001) [Orchestration]
    ↓
Switch (8002) [Routing]
    ├→ Shub Audio Router → Shubniggurath (8007)
    └→ Hermes (8003) [Local models]
         └→ ShubAudioProvider
    
Shubniggurath (8007)
├─ 10 DSP Engines
├─ PostgreSQL 14 (Tenant DB)
├─ REAPER RPC Integration
├─ VX11 Sync (DB + APIs)
└─ Operator Dashboard (8011)
```

## Installation

### Local Development

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/vx11.git
cd vx11

# 2. Configure environment
cp tokens.env.sample tokens.env
vim tokens.env  # Set DEEPSEEK_API_KEY if using R1

# 3. Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_shub.txt

# 4. Start PostgreSQL
docker run -d \
  --name shubniggurath-pg \
  -e POSTGRES_DB=shubniggurath \
  -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 \
  postgres:14

# 5. Initialize database
python3 -c "from shubniggurath.database.models import init_db; import asyncio; asyncio.run(init_db(engine))"

# 6. Start Shub
python3 shubniggurath/main.py
```

### Docker Compose

```bash
# All services including Shub
docker-compose up -d

# Verify services
curl http://localhost:8000/vx11/status
curl http://localhost:8007/shub/health
curl http://localhost:8011/operator/shub/dashboard
```

## Core Endpoints

### Analysis & Processing

```bash
# Analyze audio file
curl -X POST http://localhost:8007/shub/analyze \
  -F "file=@audio.wav"

# List DSP engines
curl http://localhost:8007/shub/engines

# Process through specific engine
curl -X POST http://localhost:8007/shub/engines/analyzer/process \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/audio.wav"}'
```

### Project Management

```bash
# Create project
curl -X POST http://localhost:8007/shub/projects/tenant-1 \
  -H "Content-Type: application/json" \
  -d '{"name": "My Album", "client": "Artist Name"}'

# List projects
curl http://localhost:8007/shub/projects/tenant-1
```

### Operator Dashboard

```bash
# Dashboard data
curl http://localhost:8011/operator/shub/dashboard

# Engine health
curl http://localhost:8011/operator/shub/engines/health

# Processing queue
curl http://localhost:8011/operator/shub/queue

# Platform stats
curl http://localhost:8011/operator/shub/stats
```

## 10 DSP Engines

### 1. Analyzer
- Comprehensive audio analysis
- Loudness (ITU-R BS.1770), spectral, temporal features
- BPM, key detection, harmonic analysis
- Output: Full DSP metrics for decision-making

### 2. Transient Detector
- Onset detection and sharpness analysis
- Percussiveness scoring
- Transient-based routing for processing

### 3. EQ Generator
- Automatic EQ curve generation
- Genre/style-aware recommendations
- Frequency balance optimization

### 4. Dynamics Processor
- Compression, expansion, gating parameters
- Adaptive threshold detection
- Loudness-based processing chain generation

### 5. Stereo Processor
- Correlation analysis
- Width and imaging optimization
- Mono compatibility checks

### 6. FX Engine
- Reverb, delay, modulation, saturation generation
- Convolution IR-based processing
- Parallel chain creation

### 7. AI Recommender
- ML-based processing chain suggestions
- Genre/style matching
- Preset library integration

### 8. AI Mastering
- Linear phase EQ generation
- Multiband compression design
- Limiter configuration
- Target loudness normalization (-14 LUFS, -23 LUFS, etc.)

### 9. Preset Generator
- Create presets from analysis
- User preset management
- Preset library distribution

### 10. Batch Processor
- Parallel file processing
- Queue management
- Progress tracking

## Database Schema (14 Tables)

| Table | Purpose |
|-------|---------|
| tenants | Multi-tenancy support |
| studio_profiles | Studio configuration & metadata |
| audio_projects | Audio projects with versioning |
| audio_assets | Individual audio files + analysis |
| plugin_registry | VST/AU/CLAP plugins catalog |
| impulse_response_library | IR library for convolution |
| amp_profiles | Amp modeling profiles |
| mixing_sessions | Mixing session tracking |
| mastering_sessions | Mastering session metadata |
| audio_analysis_cache | Analysis result caching |
| preset_library | Preset storage & management |
| audio_problems_detected | Quality issues detection |
| vx11_integration_log | Sync log with VX11 |
| ai_training_data | ML training data collection |

## VX11 Integration

### Bidirectional Sync

```
VX11 Task Created (Madre)
    ↓
Spawn audio job (Spawner)
    ↓
Asset synced to Shub (PostgreSQL)
    ↓
Analysis executed (10 Engines)
    ↓
Results synced back to VX11 (SQLite Context)
    ↓
Dashboard updated (Operator)
```

### Module Communication

- **Switch**: Audio task routing via `ShubAudioRouter`
- **Hermes**: Audio operations via `ShubAudioProvider`
- **Madre**: Pipeline orchestration via `MadreShubOrchestrator`
- **MCP**: Conversational audio commands via `MCPShubBridge`
- **Hormiguero**: Parallel processing via `HormigueroShubIntegration`
- **Manifestator**: Drift detection via `ManifestatorShubBridge`
- **Tentáculo**: Gateway routing via `TentaculoShubGateway`

## Configuration

### Environment Variables

```bash
# Shubniggurath
SHUBNIGGURATH_PORT=8007
SHUBNIGGURATH_HOST=0.0.0.0

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=shubniggurath
POSTGRES_USER=shubniggurath
POSTGRES_PASSWORD=changeme

# REAPER
REAPER_HOST=localhost
REAPER_PORT=7899

# Audio defaults
DEFAULT_SAMPLE_RATE=48000
DEFAULT_BIT_DEPTH=24
DEFAULT_CHANNELS=2

# VX11
VX11_TOKEN=your_token_here
SWITCH_URL=http://switch:8002
MADRE_URL=http://madre:8001

# DeepSeek (optional)
DEEPSEEK_API_KEY=sk-xxx
```

## Testing

```bash
# Run all tests
pytest tests/test_shubniggurath_complete_suite.py -v

# Run specific phase tests
pytest tests/test_shubniggurath_phase1.py -v
pytest tests/test_shubniggurath_phase2.py -v
# ... etc

# With coverage
pytest tests/test_shubniggurath_complete_suite.py --cov=shubniggurath
```

## Health Checks

```bash
# Shub health
curl http://localhost:8007/health

# VX11 status
curl http://localhost:8000/vx11/status

# Engines health
curl http://localhost:8007/shub/engines

# Database connection
# (Checked automatically on startup)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| PostgreSQL connection refused | Ensure `postgres:14` is running on port 5432 |
| REAPER RPC not responding | Configure REAPER RPC server on port 7899 |
| No engines available | Check `ENABLED_ENGINES` config |
| VX11 sync failures | Verify `X-VX11-Token` header in requests |
| DeepSeek errors | Set valid `DEEPSEEK_API_KEY` if using R1 |

## Performance

- **Analyzer**: ~2-5 seconds per audio file (DSP-intensive)
- **EQ Generator**: ~500ms
- **AI Mastering**: ~1-2 seconds
- **Batch Processor**: Parallel (10+ files simultaneously)
- **Database Queries**: <100ms (indexed)

## Future Enhancements

- GPU acceleration (CUDA/Metal)
- Real-time audio streaming
- Mobile app support
- Advanced ML models (style transfer)
- Marketplace integration
- Licensing system

## Support

For issues, documentation, or contributions:
- GitHub: https://github.com/yourusername/vx11
- Issues: https://github.com/yourusername/vx11/issues
- Docs: /docs/SHUBNIGGURATH.md

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2025-12-09
