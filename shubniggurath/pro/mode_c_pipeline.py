"""
Pipeline Mode C: Variante especializada para streaming, batch y realtime
Optimizado para baja latencia y recursos limitados.
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from collections import deque
import numpy as np

from shubniggurath.pro.dsp_engine import DSPEngine
from shubniggurath.pro.dsp_fx import FXChain, EffectConfig, EffectType


class ProcessingMode(Enum):
    """Modos de procesamiento"""
    STREAMING = "streaming"      # Bajo buffer, baja latencia
    BATCH = "batch"              # Buffer grande, máxima calidad
    REALTIME = "realtime"        # Ultra-bajo buffer, máxima prioridad


@dataclass
class ModeCConfig:
    """Configuración del Mode C"""
    mode: ProcessingMode
    
    # Buffers
    chunk_size: int = 2048      # muestras por chunk
    buffer_size: int = 65536    # máximo buffer
    
    # Latencia/Calidad
    target_latency_ms: float = 50  # Objetivo de latencia (streaming)
    analysis_skip_percent: int = 0 # % de chunks a skipear análisis
    
    # Recursos
    max_workers: int = 1
    use_precomputed: bool = True
    
    # FX
    max_parallel_effects: int = 2


class StreamBuffer:
    """Buffer circular para streaming"""
    
    def __init__(self, size: int, channels: int = 1):
        self.size = size
        self.channels = channels
        self.buffer = deque(maxlen=size)
        self.lock = asyncio.Lock()
    
    async def push(self, chunk: np.ndarray) -> None:
        """Agregar chunk"""
        async with self.lock:
            self.buffer.append(chunk)
    
    async def pop(self, num_chunks: int = 1) -> Optional[np.ndarray]:
        """Extraer chunks"""
        async with self.lock:
            if len(self.buffer) < num_chunks:
                return None
            
            result = []
            for _ in range(num_chunks):
                if self.buffer:
                    result.append(self.buffer.popleft())
            
            return np.concatenate(result) if result else None
    
    async def peek(self, num_chunks: int = 1) -> Optional[np.ndarray]:
        """Ver sin extraer"""
        async with self.lock:
            if len(self.buffer) < num_chunks:
                return None
            
            result = list(self.buffer)[:num_chunks]
            return np.concatenate(result) if result else None
    
    async def get_size(self) -> int:
        """Obtener tamaño actual"""
        async with self.lock:
            return len(self.buffer)


class ModeCPipeline:
    """Pipeline especializado Mode C"""
    
    def __init__(self, config: Optional[ModeCConfig] = None):
        self.config = config or ModeCConfig(mode=ProcessingMode.BATCH)
        self.dsp_engine = DSPEngine()
        self.fx_chain: Optional[FXChain] = None
        
        # Buffers por modo
        if self.config.mode == ProcessingMode.STREAMING:
            self.input_buffer = StreamBuffer(self.config.buffer_size)
            self.output_buffer = StreamBuffer(self.config.buffer_size)
        
        # Estado
        self.sample_rate = 48000
        self.chunk_counter = 0
        self.analysis_cache = {}
    
    def configure_fx_chain(self, configs: List[Dict[str, Any]]) -> None:
        """Configurar cadena de efectos"""
        self.fx_chain = FXChain(sample_rate=self.sample_rate)
        
        for fx_config in configs:
            effect_config = EffectConfig(
                type=EffectType(fx_config.get("type")),
                enabled=fx_config.get("enabled", True),
                params=fx_config.get("params", {}),
            )
            self.fx_chain.add_effect_config(effect_config)
    
    async def process_chunk(
        self,
        chunk: np.ndarray,
        skip_analysis: bool = False,
    ) -> np.ndarray:
        """Procesar un chunk de audio"""
        
        output = chunk.copy()
        
        # Análisis (opcional)
        if not skip_analysis and self.config.mode != ProcessingMode.REALTIME:
            if self.chunk_counter not in self.analysis_cache:
                # Análisis básico (no computacionalmente pesado)
                try:
                    analysis = await self.dsp_engine.analyze_audio(chunk, self.sample_rate)
                    self.analysis_cache[self.chunk_counter] = analysis
                except Exception as e:
                    pass  # Silent fail en streaming
        
        # Efectos
        if self.fx_chain:
            output = await self.fx_chain.process_async(output)
        
        self.chunk_counter += 1
        
        # Limpiar cache viejo
        if len(self.analysis_cache) > 100:
            oldest_key = min(self.analysis_cache.keys())
            del self.analysis_cache[oldest_key]
        
        return output
    
    async def process_streaming(
        self,
        input_stream,  # async generator o callable
        output_callback,  # async callable
        duration_chunks: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Procesamiento en streaming (bajo buffer)"""
        
        if self.config.mode != ProcessingMode.STREAMING:
            raise ValueError("Este método requiere mode=STREAMING")
        
        chunks_processed = 0
        errors = 0
        
        try:
            async for chunk in input_stream:
                # Skip análisis según configuración
                skip = (self.chunk_counter % 100) < self.config.analysis_skip_percent
                
                output_chunk = await self.process_chunk(chunk, skip_analysis=skip)
                await output_callback(output_chunk)
                
                chunks_processed += 1
                
                if duration_chunks and chunks_processed >= duration_chunks:
                    break
            
            return {
                "success": True,
                "chunks_processed": chunks_processed,
                "errors": errors,
                "mode": "streaming",
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks_processed": chunks_processed,
                "errors": errors + 1,
            }
    
    async def process_batch(
        self,
        audio: np.ndarray,
        sample_rate: int = 48000,
    ) -> Dict[str, Any]:
        """Procesamiento en batch (máxima calidad)"""
        
        if self.config.mode != ProcessingMode.BATCH:
            raise ValueError("Este método requiere mode=BATCH")
        
        self.sample_rate = sample_rate
        
        try:
            # Dividir en chunks
            num_chunks = (len(audio) + self.config.chunk_size - 1) // self.config.chunk_size
            output_audio = np.zeros_like(audio)
            
            analysis_results = []
            
            for i in range(num_chunks):
                start = i * self.config.chunk_size
                end = min(start + self.config.chunk_size, len(audio))
                chunk = audio[start:end]
                
                # Procesar
                output_chunk = await self.process_chunk(chunk, skip_analysis=False)
                output_audio[start:end] = output_chunk[:len(chunk)]
                
                # Análisis (completo en batch)
                if i % max(1, num_chunks // 10) == 0:
                    analysis = await self.dsp_engine.analyze_audio(chunk, sample_rate)
                    analysis_results.append({
                        "chunk_idx": i,
                        "peak_db": analysis.peak_db,
                        "lufs": analysis.lufs,
                    })
            
            return {
                "success": True,
                "output_audio": output_audio,
                "analysis": analysis_results,
                "mode": "batch",
                "chunks_processed": num_chunks,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode": "batch",
            }
    
    async def process_realtime(
        self,
        get_input_chunk,  # async callable que retorna chunk
        put_output_chunk,  # async callable para enviar chunk
        duration_ms: float = 1000,
        target_latency_ms: float = 20,
    ) -> Dict[str, Any]:
        """Procesamiento realtime (ultra-baja latencia)"""
        
        if self.config.mode != ProcessingMode.REALTIME:
            raise ValueError("Este método requiere mode=REALTIME")
        
        import time
        
        start_time = time.time()
        chunks_processed = 0
        total_latency_ms = 0
        underruns = 0
        
        try:
            while (time.time() - start_time) * 1000 < duration_ms:
                chunk_start = time.time()
                
                # Input
                chunk = await asyncio.wait_for(
                    get_input_chunk(),
                    timeout=target_latency_ms / 1000,
                )
                
                if chunk is None:
                    underruns += 1
                    await asyncio.sleep(self.config.chunk_size / self.sample_rate / 2)
                    continue
                
                # Process (sin análisis)
                output = await self.process_chunk(chunk, skip_analysis=True)
                
                # Output
                await put_output_chunk(output)
                
                chunk_latency = (time.time() - chunk_start) * 1000
                total_latency_ms += chunk_latency
                chunks_processed += 1
                
                # Mantener latencia objetivo
                if chunk_latency < target_latency_ms:
                    await asyncio.sleep(
                        (target_latency_ms - chunk_latency) / 1000
                    )
            
            avg_latency = total_latency_ms / chunks_processed if chunks_processed > 0 else 0
            
            return {
                "success": True,
                "chunks_processed": chunks_processed,
                "avg_latency_ms": avg_latency,
                "underruns": underruns,
                "mode": "realtime",
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks_processed": chunks_processed,
                "mode": "realtime",
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {
            "mode": self.config.mode.value,
            "chunks_processed": self.chunk_counter,
            "cache_size": len(self.analysis_cache),
            "fx_enabled": self.fx_chain is not None,
            "sample_rate": self.sample_rate,
        }


# Factory para crear pipelines según modo
def create_mode_c_pipeline(mode: ProcessingMode) -> ModeCPipeline:
    """Crear pipeline Mode C con configuración óptima para el modo"""
    
    if mode == ProcessingMode.STREAMING:
        config = ModeCConfig(
            mode=mode,
            chunk_size=2048,
            buffer_size=32768,
            target_latency_ms=50,
            analysis_skip_percent=20,  # Skip 20% de análisis
            max_workers=2,
        )
    elif mode == ProcessingMode.REALTIME:
        config = ModeCConfig(
            mode=mode,
            chunk_size=512,
            buffer_size=8192,
            target_latency_ms=20,
            analysis_skip_percent=100,  # Sin análisis
            max_workers=1,
        )
    else:  # BATCH
        config = ModeCConfig(
            mode=mode,
            chunk_size=4096,
            buffer_size=131072,
            target_latency_ms=500,
            analysis_skip_percent=0,  # Análisis completo
            max_workers=4,
        )
    
    return ModeCPipeline(config)
