"""
Tests simples y robustos para Shub Pro
Enfoque: validación de estructura sin dependencias complejas
"""

import pytest
import numpy as np
from pathlib import Path
from shubniggurath.pro.dsp_fx import (
    FXChain,
    EffectConfig,
    EffectType,
    GainEffect,
    LimiterEffect,
    DistortionEffect,
)
from shubniggurath.pro.mode_c_pipeline import (
    create_mode_c_pipeline,
    ProcessingMode,
    StreamBuffer,
)
from shubniggurath.pro.virtual_engineer import VirtualEngineer
from shubniggurath.pro.shub_core_init import ShubProInitializer


# ============================================================================
# FIXTURE: Audio
# ============================================================================

@pytest.fixture
def sample_audio():
    """Audio de prueba: 1 segundo @ 48kHz"""
    sr = 48000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), False)
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    return audio, sr


# ============================================================================
# TESTS: EFFECTS (No requieren librosa/scipy)
# ============================================================================

class TestEffectsSimple:
    """Tests simples de efectos sin dependencias"""
    
    def test_gain_effect_positive(self, sample_audio):
        """Test: ganancia positiva"""
        audio, sr = sample_audio
        config = EffectConfig(
            type=EffectType.GAIN,
            params={"gain_db": 6},
        )
        effect = GainEffect(config, sr)
        output = effect.process(audio)
        
        # Amplitud debe aumentar
        assert np.mean(np.abs(output)) > np.mean(np.abs(audio))
    
    def test_gain_effect_negative(self, sample_audio):
        """Test: ganancia negativa"""
        audio, sr = sample_audio
        config = EffectConfig(
            type=EffectType.GAIN,
            params={"gain_db": -6},
        )
        effect = GainEffect(config, sr)
        output = effect.process(audio)
        
        # Amplitud debe disminuir
        assert np.mean(np.abs(output)) < np.mean(np.abs(audio))
    
    def test_limiter_effect(self, sample_audio):
        """Test: limitador previene clipping"""
        audio, sr = sample_audio
        # Audio con amplitud > 1
        loud_audio = audio * 2.0
        
        config = EffectConfig(
            type=EffectType.LIMITER,
            params={"threshold_db": -3},
        )
        effect = LimiterEffect(config, sr)
        output = effect.process(loud_audio)
        
        # No debe haber clipping
        assert np.max(np.abs(output)) <= 1.0 + 0.01
    
    def test_distortion_effect(self, sample_audio):
        """Test: distorsión modifica audio"""
        audio, sr = sample_audio
        config = EffectConfig(
            type=EffectType.DISTORTION,
            params={"drive": 2.0, "mix": 0.5},
        )
        effect = DistortionEffect(config, sr)
        output = effect.process(audio)
        
        # Output diferente pero válido
        assert not np.allclose(output, audio)
        assert np.max(np.abs(output)) <= 1.0 + 0.01
    
    def test_fx_chain_empty(self, sample_audio):
        """Test: cadena vacía (pass-through)"""
        audio, sr = sample_audio
        chain = FXChain(sample_rate=sr)
        
        output = chain.process(audio)
        
        # Debe ser idéntico
        assert np.allclose(output, audio)
    
    def test_fx_chain_single_effect(self, sample_audio):
        """Test: cadena con un efecto"""
        audio, sr = sample_audio
        chain = FXChain(sample_rate=sr)
        chain.add_effect_config(EffectConfig(
            type=EffectType.GAIN,
            params={"gain_db": -6},
        ))
        
        output = chain.process(audio)
        
        # Debe reducir amplitud
        assert np.mean(np.abs(output)) < np.mean(np.abs(audio))
    
    def test_fx_chain_cascade(self, sample_audio):
        """Test: cadena en cascada"""
        audio, sr = sample_audio
        chain = FXChain(sample_rate=sr)
        chain.add_effect_config(EffectConfig(
            type=EffectType.GAIN,
            params={"gain_db": -6},
        ))
        chain.add_effect_config(EffectConfig(
            type=EffectType.GAIN,
            params={"gain_db": 6},
        ))
        
        output = chain.process(audio)
        
        # Ganancia neta ≈ 0
        assert np.allclose(output, audio, atol=0.01)
    
    def test_fx_chain_preset_save(self, sample_audio):
        """Test: guardar preset"""
        audio, sr = sample_audio
        chain = FXChain(sample_rate=sr)
        chain.add_effect_config(EffectConfig(
            type=EffectType.LIMITER,
            params={"threshold_db": -3},
        ))
        
        preset = chain.save_preset()
        
        assert "sample_rate" in preset
        assert "effects" in preset
        assert len(preset["effects"]) == 1
    
    def test_fx_chain_preset_load(self, sample_audio):
        """Test: cargar y verificar preset"""
        audio, sr = sample_audio
        chain1 = FXChain(sample_rate=sr)
        chain1.add_effect_config(EffectConfig(
            type=EffectType.GAIN,
            params={"gain_db": -6},
        ))
        
        output1 = chain1.process(audio)
        preset = chain1.save_preset()
        
        # Nueva cadena
        chain2 = FXChain(sample_rate=sr)
        chain2.load_preset(preset)
        output2 = chain2.process(audio)
        
        assert np.allclose(output1, output2)
    
    def test_effect_disabled(self, sample_audio):
        """Test: efecto deshabilitado (pass-through)"""
        audio, sr = sample_audio
        chain = FXChain(sample_rate=sr)
        chain.add_effect_config(EffectConfig(
            type=EffectType.GAIN,
            params={"gain_db": -20},
            enabled=False,  # Deshabilitado
        ))
        
        output = chain.process(audio)
        
        # Debe ser idéntico (efecto no aplicado)
        assert np.allclose(output, audio)


# ============================================================================
# TESTS: MODE C PIPELINE
# ============================================================================

class TestModeCSimple:
    """Tests simples de Mode C sin dependencias complejas"""
    
    def test_mode_c_batch_config(self):
        """Test: configuración Mode C Batch"""
        pipeline = create_mode_c_pipeline(ProcessingMode.BATCH)
        
        assert pipeline.config.mode == ProcessingMode.BATCH
        assert pipeline.config.chunk_size == 4096
        assert pipeline.config.max_workers == 4
    
    def test_mode_c_streaming_config(self):
        """Test: configuración Mode C Streaming"""
        pipeline = create_mode_c_pipeline(ProcessingMode.STREAMING)
        
        assert pipeline.config.mode == ProcessingMode.STREAMING
        assert pipeline.config.chunk_size == 2048
        assert pipeline.config.analysis_skip_percent == 20
    
    def test_mode_c_realtime_config(self):
        """Test: configuración Mode C Realtime"""
        pipeline = create_mode_c_pipeline(ProcessingMode.REALTIME)
        
        assert pipeline.config.mode == ProcessingMode.REALTIME
        assert pipeline.config.chunk_size == 512
        assert pipeline.config.analysis_skip_percent == 100
    
    @pytest.mark.asyncio
    async def test_stream_buffer_push_pop(self):
        """Test: operaciones buffer streaming"""
        buffer = StreamBuffer(size=10, channels=1)
        
        chunk = np.ones(100, dtype=np.float32)
        await buffer.push(chunk)
        
        size = await buffer.get_size()
        assert size == 1
        
        popped = await buffer.pop(1)
        assert popped is not None
        assert len(popped) == 100
        
        size_after = await buffer.get_size()
        assert size_after == 0
    
    @pytest.mark.asyncio
    async def test_stream_buffer_peek(self):
        """Test: peek en buffer sin extraer"""
        buffer = StreamBuffer(size=10, channels=1)
        
        chunk1 = np.ones(50, dtype=np.float32)
        chunk2 = np.ones(50, dtype=np.float32) * 2
        
        await buffer.push(chunk1)
        await buffer.push(chunk2)
        
        peeked = await buffer.peek(2)
        assert peeked is not None
        
        size = await buffer.get_size()
        assert size == 2  # No debe cambiar
    
    def test_mode_c_stats(self):
        """Test: estadísticas"""
        pipeline = create_mode_c_pipeline(ProcessingMode.BATCH)
        stats = pipeline.get_stats()
        
        assert "mode" in stats
        assert "chunks_processed" in stats
        assert "sample_rate" in stats
        assert stats["mode"] == "batch"


# ============================================================================
# TESTS: VIRTUAL ENGINEER
# ============================================================================

class TestVirtualEngineerSimple:
    """Tests simples del Ingeniero Virtual"""
    
    def test_get_available_presets(self):
        """Test: listar presets disponibles"""
        engineer = VirtualEngineer()
        presets = engineer.get_available_presets()
        
        assert "presets" in presets
        assert isinstance(presets["presets"], list)
        assert len(presets["presets"]) > 0
        assert "mastering" in presets["presets"]
        assert "clean_voice" in presets["presets"]
        assert "bright" in presets["presets"]
    
    @pytest.mark.asyncio
    async def test_get_preset_recommendation(self):
        """Test: obtener preset por nombre"""
        engineer = VirtualEngineer()
        preset = await engineer.get_preset_recommendation("mastering")
        
        assert preset is not None
        assert "effects" in preset


# ============================================================================
# TESTS: CORE INITIALIZER
# ============================================================================

class TestShubCoreInitSimple:
    """Tests simples del inicializador"""
    
    def test_initializer_creation(self):
        """Test: crear inicializador"""
        init = ShubProInitializer()
        
        assert not init.ready
        assert isinstance(init.components, dict)
    
    @pytest.mark.asyncio
    async def test_dsp_init(self):
        """Test: inicialización DSP"""
        init = ShubProInitializer()
        result = await init._init_dsp_engine()
        
        assert result["success"]
        assert "time_ms" in result
    
    @pytest.mark.asyncio
    async def test_fx_init(self):
        """Test: inicialización FX"""
        init = ShubProInitializer()
        result = await init._init_fx_chains()
        
        assert result["success"]
        assert "presets" in result
        assert len(result["presets"]) >= 3
    
    def test_health_status(self):
        """Test: estado de salud"""
        init = ShubProInitializer()
        status = init.get_health_status()
        
        assert "ready" in status
        assert "components" in status
        assert status["ready"] == False


# ============================================================================
# TESTS: IMPORTS (Validar que módulos importan correctamente)
# ============================================================================

class TestImports:
    """Validar que todos los módulos importan sin errores"""
    
    def test_import_dsp_engine(self):
        """Test: importar dsp_engine"""
        from shubniggurath.pro import dsp_engine
        assert hasattr(dsp_engine, 'DSPEngine')
    
    def test_import_dsp_fx(self):
        """Test: importar dsp_fx"""
        from shubniggurath.pro import dsp_fx
        assert hasattr(dsp_fx, 'FXChain')
        assert hasattr(dsp_fx, 'EffectType')
    
    def test_import_dsp_pipeline(self):
        """Test: importar dsp_pipeline_full"""
        from shubniggurath.pro import dsp_pipeline_full
        assert hasattr(dsp_pipeline_full, 'DSPPipeline')
    
    def test_import_mode_c(self):
        """Test: importar mode_c_pipeline"""
        from shubniggurath.pro import mode_c_pipeline
        assert hasattr(mode_c_pipeline, 'ModeCPipeline')
    
    def test_import_virtual_engineer(self):
        """Test: importar virtual_engineer"""
        from shubniggurath.pro import virtual_engineer
        assert hasattr(virtual_engineer, 'VirtualEngineer')
    
    def test_import_core_init(self):
        """Test: importar shub_core_init"""
        from shubniggurath.pro import shub_core_init
        assert hasattr(shub_core_init, 'ShubProInitializer')

    def test_import_shub_db(self):
        """Test: importar shub_db"""
        from shubniggurath.pro import shub_db
        assert hasattr(shub_db, 'ShubSession')
        assert hasattr(shub_db, 'AdvancedAnalysis')
        assert hasattr(shub_db, 'ShubJob')


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
