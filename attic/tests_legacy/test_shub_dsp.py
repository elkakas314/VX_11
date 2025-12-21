"""
tests/test_shub_dsp.py — Tests de DSP Pipeline Shub-Niggurath

Valida:
- 8 fases del pipeline
- Análisis de audio
- Generación de FX chains
- Generación de presets REAPER
"""

import pytest
import asyncio
from pathlib import Path
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

# Importar módulos Shub
from shubniggurath.core.dsp_pipeline_full import DSPPipelineFull
from shubniggurath.engines_paso8 import AudioAnalysis, FXChain, REAPERPreset


class TestDSPPipeline:
    """Tests del pipeline DSP de 8 fases"""
    
    @pytest.fixture
    def audio_bytes(self):
        """Generar audio de prueba: 44.1kHz, 2s, 16-bit stereo"""
        sample_rate = 44100
        duration_seconds = 2.0
        samples = int(sample_rate * duration_seconds)
        
        # Generar audio sinusoidal simple
        t = np.arange(samples) / sample_rate
        left_channel = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        right_channel = 0.5 * np.sin(2 * np.pi * 880 * t)  # 880 Hz sine wave
        
        stereo = np.stack([left_channel, right_channel])
        # Convertir a 16-bit PCM
        pcm = (stereo * 32767).astype(np.int16).tobytes()
        return pcm
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        """Test: Inicialización del pipeline"""
        pipeline = DSPPipelineFull()
        assert pipeline is not None
        assert hasattr(pipeline, 'run_full_pipeline')
    
    @pytest.mark.asyncio
    async def test_run_full_pipeline_quick_mode(self, audio_bytes):
        """Test: Ejecutar pipeline en modo 'quick'"""
        pipeline = DSPPipelineFull()
        
        result = await pipeline.run_full_pipeline(
            audio_bytes=audio_bytes,
            sample_rate=44100,
            mode="quick"
        )
        
        assert result['status'] == 'success'
        assert 'audio_analysis' in result
        assert 'fx_chain' in result
        assert 'reaper_preset' in result
        assert len(result['phases_completed']) > 0
    
    @pytest.mark.asyncio
    async def test_run_full_pipeline_mode_c(self, audio_bytes):
        """Test: Ejecutar pipeline en modo 'mode_c'"""
        pipeline = DSPPipelineFull()
        
        result = await pipeline.run_full_pipeline(
            audio_bytes=audio_bytes,
            sample_rate=44100,
            mode="mode_c"
        )
        
        assert result['status'] == 'success'
        assert len(result['phases_completed']) >= 4  # At least 4 phases
    
    @pytest.mark.asyncio
    async def test_audio_analysis_structure(self, audio_bytes):
        """Test: Validar estructura de AudioAnalysis"""
        pipeline = DSPPipelineFull()
        
        result = await pipeline.run_full_pipeline(
            audio_bytes=audio_bytes,
            sample_rate=44100,
            mode="quick"
        )
        
        analysis = result['audio_analysis']
        
        # Validar campos canónicos (33 campos)
        assert hasattr(analysis, 'peak_dbfs')
        assert hasattr(analysis, 'rms_dbfs')
        assert hasattr(analysis, 'lufs_integrated')
        assert hasattr(analysis, 'spectral_centroid')
        assert hasattr(analysis, 'dynamic_range')
        assert hasattr(analysis, 'issues')
        assert hasattr(analysis, 'recommendations')
    
    @pytest.mark.asyncio
    async def test_fx_chain_generation(self, audio_bytes):
        """Test: Validar generación de FX Chain"""
        pipeline = DSPPipelineFull()
        
        result = await pipeline.run_full_pipeline(
            audio_bytes=audio_bytes,
            sample_rate=44100,
            mode="mode_c"
        )
        
        fx_chain = result['fx_chain']
        
        assert fx_chain is not None
        assert hasattr(fx_chain, 'name')
        assert hasattr(fx_chain, 'plugins')
    
    @pytest.mark.asyncio
    async def test_reaper_preset_generation(self, audio_bytes):
        """Test: Validar generación de preset REAPER"""
        pipeline = DSPPipelineFull()
        
        result = await pipeline.run_full_pipeline(
            audio_bytes=audio_bytes,
            sample_rate=44100,
            mode="quick"
        )
        
        preset = result['reaper_preset']
        
        assert preset is not None
        assert hasattr(preset, 'project_name')
        assert hasattr(preset, 'fx_chains')
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_audio(self):
        """Test: Error handling para audio inválido"""
        pipeline = DSPPipelineFull()
        
        # Audio vacío
        result = await pipeline.run_full_pipeline(
            audio_bytes=b'',
            sample_rate=44100,
            mode="quick"
        )
        
        # Debe retornar error o valor por defecto seguro
        assert result['status'] in ['success', 'error']


class TestDSPEngineIntegration:
    """Tests de integración con engines_paso8.py"""
    
    @pytest.mark.asyncio
    async def test_audio_analysis_dataclass_creation(self):
        """Test: Crear instancia de AudioAnalysis"""
        analysis = AudioAnalysis(
            peak_dbfs=-3.0,
            rms_dbfs=-20.0,
            lufs_integrated=-14.0,
            lufs_range=10.0,
            true_peak_dbfs=-0.5,
            spectral_centroid=5000.0,
            spectral_rolloff=15000.0,
            spectral_flux=0.5,
            zero_crossing_rate=0.3,
            mfcc=[1.0, 2.0, 3.0],
            chroma=[0.1, 0.2, 0.3],
            spectral_contrast=[1.0, 2.0],
            spectral_flatness=0.7,
            dynamic_range=12.0,
            crest_factor=3.5,
            transients=45,
            transients_count=45,
            clipping_samples=0,
            dc_offset=0.001,
            noise_floor_dbfs=-80.0,
            phase_correlation=0.95,
            sibilance_detected=False,
            sibilance_freq=0,
            resonances=[],
            bpm=120.0,
            key_detected="C",
            key_confidence=0.9,
            harmonic_complexity=0.6,
            percussiveness=0.4,
            instrument_prediction="piano",
            genre_prediction="classical",
            mood_prediction="calm",
            issues=[],
            recommendations=[]
        )
        
        assert analysis.peak_dbfs == -3.0
        assert analysis.instrument_prediction == "piano"
    
    @pytest.mark.asyncio
    async def test_fx_chain_dataclass_creation(self):
        """Test: Crear instancia de FXChain"""
        fx_chain = FXChain(
            name="Auto_Mix_Chain",
            description="Cadena automática de mezcla",
            plugins=[
                {"name": "ReaEQ", "params": {"freq": 5000}},
                {"name": "ReaComp", "params": {"threshold": -20}}
            ],
            routing={"master": 0, "aux1": 1},
            presets=[]
        )
        
        assert fx_chain.name == "Auto_Mix_Chain"
        assert len(fx_chain.plugins) == 2
    
    @pytest.mark.asyncio
    async def test_reaper_preset_dataclass_creation(self):
        """Test: Crear instancia de REAPERPreset"""
        preset = REAPERPreset(
            project_name="Song01",
            tracks=[
                {"name": "Drums", "volume": -3.0},
                {"name": "Bass", "volume": -6.0}
            ],
            fx_chains=[],
            routing_matrix={},
            automation=[],
            metadata={"composer": "Test"}
        )
        
        assert preset.project_name == "Song01"
        assert len(preset.tracks) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
