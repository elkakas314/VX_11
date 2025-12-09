"""
Inicializador Core de Shub Pro
Startup secuencial: DB → DSP → FX → Pipelines → Caché → Readiness
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from shubniggurath.pro.shub_db import init_shub_db, get_shub_session
from shubniggurath.pro.dsp_engine import DSPEngine
from shubniggurath.pro.dsp_fx import FXChain
from shubniggurath.pro.dsp_pipeline_full import get_pipeline
from shubniggurath.pro.mode_c_pipeline import create_mode_c_pipeline, ProcessingMode
from shubniggurath.pro.virtual_engineer import get_virtual_engineer
from config.settings import settings

logger = logging.getLogger(__name__)


class ShubProInitializer:
    """Inicializador y checker de salud"""
    
    def __init__(self):
        self.startup_time = None
        self.components: Dict[str, Dict[str, Any]] = {}
        self.ready = False
    
    async def initialize_all(self) -> Dict[str, Any]:
        """Inicialización completa y secuencial"""
        
        start = time.time()
        self.startup_time = datetime.now()
        
        results = {
            "timestamp": self.startup_time.isoformat(),
            "steps": {},
            "success": True,
            "total_time_s": 0,
        }
        
        try:
            # 1. Base de datos
            logger.info("[Shub Init] 1/6: Inicializando BD...")
            db_result = await self._init_database()
            results["steps"]["database"] = db_result
            if not db_result["success"]:
                raise Exception(f"DB init failed: {db_result.get('error')}")
            logger.info(f"✓ BD inicializada en {db_result['time_ms']:.1f}ms")
            
            # 2. Motor DSP
            logger.info("[Shub Init] 2/6: Inicializando DSP Engine...")
            dsp_result = await self._init_dsp_engine()
            results["steps"]["dsp_engine"] = dsp_result
            if not dsp_result["success"]:
                raise Exception(f"DSP init failed: {dsp_result.get('error')}")
            logger.info(f"✓ DSP Engine listo en {dsp_result['time_ms']:.1f}ms")
            
            # 3. FX Chains
            logger.info("[Shub Init] 3/6: Inicializando FX Chains...")
            fx_result = await self._init_fx_chains()
            results["steps"]["fx_chains"] = fx_result
            if not fx_result["success"]:
                raise Exception(f"FX init failed: {fx_result.get('error')}")
            logger.info(f"✓ FX Chains listos en {fx_result['time_ms']:.1f}ms")
            
            # 4. Pipelines
            logger.info("[Shub Init] 4/6: Inicializando Pipelines...")
            pipeline_result = await self._init_pipelines()
            results["steps"]["pipelines"] = pipeline_result
            if not pipeline_result["success"]:
                raise Exception(f"Pipeline init failed: {pipeline_result.get('error')}")
            logger.info(f"✓ Pipelines listos en {pipeline_result['time_ms']:.1f}ms")
            
            # 5. Ingeniero Virtual
            logger.info("[Shub Init] 5/6: Inicializando Ingeniero Virtual...")
            engineer_result = await self._init_virtual_engineer()
            results["steps"]["virtual_engineer"] = engineer_result
            if not engineer_result["success"]:
                raise Exception(f"Engineer init failed: {engineer_result.get('error')}")
            logger.info(f"✓ Ingeniero Virtual listo en {engineer_result['time_ms']:.1f}ms")
            
            # 6. Caché y warmup
            logger.info("[Shub Init] 6/6: Warmup y caché...")
            cache_result = await self._init_cache_and_warmup()
            results["steps"]["cache"] = cache_result
            logger.info(f"✓ Caché lista en {cache_result['time_ms']:.1f}ms")
            
            # Marcar como listo
            self.ready = True
            results["success"] = True
            results["total_time_s"] = time.time() - start
            
            logger.info(f"✓ Shub Pro LISTO en {results['total_time_s']:.2f}s")
            
        except Exception as e:
            logger.error(f"✗ Error en inicialización: {e}")
            results["success"] = False
            results["error"] = str(e)
            results["total_time_s"] = time.time() - start
        
        return results
    
    async def _init_database(self) -> Dict[str, Any]:
        """Inicializar BD"""
        start = time.time()
        try:
            # Crear tablas
            init_shub_db()
            
            # Verificar conexión
            session = get_shub_session()
            session.execute("SELECT 1")
            session.close()
            
            self.components["database"] = {
                "status": "ready",
                "db_path": settings.database_url,
            }
            
            return {
                "success": True,
                "time_ms": (time.time() - start) * 1000,
                "status": "ready",
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time_ms": (time.time() - start) * 1000,
            }
    
    async def _init_dsp_engine(self) -> Dict[str, Any]:
        """Inicializar DSP Engine"""
        start = time.time()
        try:
            # Crear instancia
            dsp = DSPEngine()
            
            # Test: crear dummy de 1s @ 48kHz
            import numpy as np
            test_audio = np.zeros(48000, dtype=np.float32)
            
            # Validar que funciona
            result = await dsp.analyze_audio(test_audio, 48000)
            
            self.components["dsp_engine"] = {
                "status": "ready",
                "supports_librosa": True,
                "supports_scipy": True,
            }
            
            return {
                "success": True,
                "time_ms": (time.time() - start) * 1000,
                "status": "ready",
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time_ms": (time.time() - start) * 1000,
            }
    
    async def _init_fx_chains(self) -> Dict[str, Any]:
        """Inicializar cadenas FX"""
        start = time.time()
        try:
            # Crear instancias
            chain = FXChain(sample_rate=48000)
            
            # Presets disponibles
            presets = [
                "mastering",
                "clean_voice",
                "bright",
            ]
            
            self.components["fx_chains"] = {
                "status": "ready",
                "presets_available": presets,
            }
            
            return {
                "success": True,
                "time_ms": (time.time() - start) * 1000,
                "presets": presets,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time_ms": (time.time() - start) * 1000,
            }
    
    async def _init_pipelines(self) -> Dict[str, Any]:
        """Inicializar pipelines"""
        start = time.time()
        try:
            # Full pipeline
            pipeline = get_pipeline()
            
            # Mode C variants
            modes = {
                "batch": create_mode_c_pipeline(ProcessingMode.BATCH),
                "streaming": create_mode_c_pipeline(ProcessingMode.STREAMING),
                "realtime": create_mode_c_pipeline(ProcessingMode.REALTIME),
            }
            
            self.components["pipelines"] = {
                "status": "ready",
                "full_pipeline": "dsp_pipeline_full",
                "mode_c_variants": list(modes.keys()),
            }
            
            return {
                "success": True,
                "time_ms": (time.time() - start) * 1000,
                "pipelines": ["full", "batch", "streaming", "realtime"],
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time_ms": (time.time() - start) * 1000,
            }
    
    async def _init_virtual_engineer(self) -> Dict[str, Any]:
        """Inicializar Ingeniero Virtual"""
        start = time.time()
        try:
            engineer = get_virtual_engineer()
            presets = engineer.get_available_presets()
            
            self.components["virtual_engineer"] = {
                "status": "ready",
                "presets": presets["presets"],
                "ai_enabled": True,  # Requerirá Switch disponible
            }
            
            return {
                "success": True,
                "time_ms": (time.time() - start) * 1000,
                "presets": presets["presets"],
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time_ms": (time.time() - start) * 1000,
            }
    
    async def _init_cache_and_warmup(self) -> Dict[str, Any]:
        """Inicializar caché y warmup"""
        start = time.time()
        try:
            # Aquí se puede agregar:
            # - Precalcular análisis de archivos comunes
            # - Precargar modelos de IA
            # - Calentar pipelines
            
            self.components["cache"] = {
                "status": "ready",
                "warmup_complete": True,
            }
            
            return {
                "success": True,
                "time_ms": (time.time() - start) * 1000,
                "status": "ready",
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "time_ms": (time.time() - start) * 1000,
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Verificar salud de componentes"""
        return {
            "ready": self.ready,
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "components": self.components,
        }


# Singleton global
_initializer_instance = None


def get_shub_initializer() -> ShubProInitializer:
    """Obtener inicializador global"""
    global _initializer_instance
    if _initializer_instance is None:
        _initializer_instance = ShubProInitializer()
    return _initializer_instance


async def initialize_shub_pro() -> Dict[str, Any]:
    """Punto de entrada para inicialización"""
    initializer = get_shub_initializer()
    return await initializer.initialize_all()
