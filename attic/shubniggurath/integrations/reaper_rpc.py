"""
REAPER RPC Integration — Comunicación bidireccional con REAPER
==============================================================

Módulo canónico para integración completa VX11 ↔ REAPER:
- Control de proyectos (.RPP), pistas, items, efectos
- Aplicación de FX chains generadas por Shub DSP
- Renderización de masters
- Auto-mix y auto-master inteligentes
- Integración de status bidireccional

Protocolo: HTTP JSON RPC (puerto 8007 internamente, REAPER escucha 7899)
Auth: X-VX11-Token header
Respuestas: JSON estándar VX11 con status/success/error
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import httpx

from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log, record_crash

# =============================================================================
# LOGGING & CONSTANTS
# =============================================================================

logger = logging.getLogger(__name__)

# Configuración REAPER
REAPER_HOST = getattr(settings, 'REAPER_HOST', None) or "localhost"
REAPER_PORT = getattr(settings, 'REAPER_PORT', None) or 7899
REAPER_RPC_ENDPOINT = f"http://{REAPER_HOST}:{REAPER_PORT}/api"

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
REAPER_HEADERS = {
    settings.token_header: VX11_TOKEN,
    "Content-Type": "application/json",
}

# =============================================================================
# REAPER RPC CONTROLLER (12 Métodos Canónicos)
# =============================================================================


class REAPERController:
    """
    Controlador de REAPER canónico con 12 métodos para integración completa.
    
    Métodos:
    1. list_projects()              — Listar proyectos .RPP
    2. load_project(path)           — Cargar proyecto
    3. analyze_project()            — Análisis de proyecto completo
    4. list_tracks()                — Listar pistas
    5. list_items()                 — Listar items de audio
    6. list_fx(track)               — Listar FX en pista
    7. apply_fx_chain()             — Aplicar cadena de efectos
    8. render_master()              — Renderizar master
    9. update_project_metadata()    — Actualizar metadata
    10. send_shub_status_to_reaper() — Notificar estado Shub
    11. auto_mix()                  — Mezcla automática IA
    12. auto_master()               — Mastering automático IA
    """

    def __init__(self, reaper_host: str = None, reaper_port: int = None):
        self.reaper_host = reaper_host or REAPER_HOST
        self.reaper_port = reaper_port or REAPER_PORT
        self.endpoint = f"http://{self.reaper_host}:{self.reaper_port}/api"
        self.current_project: Optional[str] = None
        self.current_project_data: Optional[Dict] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.connected = False

    async def _ensure_client(self):
        """Asegurar cliente HTTP inicializado"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)

    async def _http_call(self, method: str, path: str, data: Dict = None) -> Dict[str, Any]:
        """
        Llamada HTTP genérica a REAPER RPC
        
        Args:
            method: GET, POST, PUT, DELETE
            path: ruta relativa (e.g., "/projects")
            data: payload JSON
            
        Returns:
            JSON response con estructura {status, data, error}
        """
        try:
            await self._ensure_client()
            url = f"{self.endpoint}{path}"
            
            if method == "GET":
                response = await self.http_client.get(url, headers=REAPER_HEADERS)
            elif method == "POST":
                response = await self.http_client.post(url, json=data, headers=REAPER_HEADERS)
            elif method == "PUT":
                response = await self.http_client.put(url, json=data, headers=REAPER_HEADERS)
            elif method == "DELETE":
                response = await self.http_client.delete(url, headers=REAPER_HEADERS)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "http_status": response.status_code, "message": response.text}
                
        except Exception as e:
            write_log("reaper_rpc", f"HTTP_CALL_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 1: list_projects
    # =========================================================================

    async def list_projects(self) -> Dict[str, Any]:
        """
        Listar proyectos REAPER disponibles.
        
        Respuesta canónica:
        {
            "status": "success",
            "projects": [
                {
                    "name": "Song01",
                    "path": "/home/user/.config/REAPER/Projects/Song01.rpp",
                    "size_bytes": 45821,
                    "modified_timestamp": 1702108800,
                    "duration_seconds": 240,
                    "bpm": 120,
                    "tracks": 8,
                    "sample_rate": 44100
                },
                ...
            ],
            "total_projects": 5,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("reaper_rpc", "LIST_PROJECTS: iniciando", level="INFO")
            result = await self._http_call("GET", "/projects")
            
            if result.get("status") == "error":
                write_log("reaper_rpc", f"LIST_PROJECTS_ERROR: {result.get('message')}", level="WARNING")
                return {
                    "status": "error",
                    "message": "Failed to list projects",
                    "projects": []
                }
            
            projects = result.get("data", [])
            write_log("reaper_rpc", f"LIST_PROJECTS: {len(projects)} proyectos encontrados", level="INFO")
            
            return {
                "status": "success",
                "projects": projects,
                "total_projects": len(projects),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e), "projects": []}

    # =========================================================================
    # MÉTODO 2: load_project
    # =========================================================================

    async def load_project(self, project_path: str) -> Dict[str, Any]:
        """
        Cargar proyecto REAPER.
        
        Args:
            project_path: Ruta completa a archivo .rpp
            
        Respuesta canónica:
        {
            "status": "success",
            "project_path": "/home/user/.config/REAPER/Projects/Song01.rpp",
            "project_name": "Song01",
            "loaded_at": "2024-12-10T15:30:00Z",
            "metadata": {
                "duration_seconds": 240,
                "bpm": 120,
                "time_signature": "4/4",
                "sample_rate": 44100,
                "tracks": 8,
                "items_count": 32
            }
        }
        """
        try:
            write_log("reaper_rpc", f"LOAD_PROJECT: {project_path}", level="INFO")
            
            result = await self._http_call("POST", "/projects/load", {
                "path": project_path
            })
            
            if result.get("status") == "success":
                self.current_project = project_path
                self.current_project_data = result.get("data", {})
                write_log("reaper_rpc", f"LOAD_PROJECT_SUCCESS: {project_path}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 3: analyze_project
    # =========================================================================

    async def analyze_project(self) -> Dict[str, Any]:
        """
        Análisis completo de proyecto cargado.
        
        Respuesta canónica:
        {
            "status": "success",
            "project": "Song01",
            "analysis": {
                "tracks_count": 8,
                "total_items": 32,
                "total_duration_seconds": 240,
                "bpm": 120,
                "time_signature": "4/4",
                "sample_rate": 44100,
                "loudness_lufs": -14.2,
                "dynamic_range_db": 12.5,
                "spectral_balance": {"low": 0.8, "mid": 1.0, "high": 0.9},
                "issues": ["high_dynamic_range", "low_high_freq"],
                "recommendations": ["add_compressor", "add_eq_high_shelf"]
            },
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if not self.current_project:
                return {"status": "error", "message": "No project loaded"}
            
            write_log("reaper_rpc", f"ANALYZE_PROJECT: {self.current_project}", level="INFO")
            
            result = await self._http_call("POST", "/projects/analyze", {
                "project_path": self.current_project
            })
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 4: list_tracks
    # =========================================================================

    async def list_tracks(self) -> Dict[str, Any]:
        """
        Listar todas las pistas del proyecto cargado.
        
        Respuesta canónica:
        {
            "status": "success",
            "tracks": [
                {
                    "index": 0,
                    "name": "Drums",
                    "volume_db": -3.0,
                    "pan": 0.0,
                    "muted": false,
                    "solo": false,
                    "armed": true,
                    "phase_reverse": false,
                    "height": 32,
                    "items_count": 4,
                    "fx_count": 2
                },
                ...
            ],
            "total_tracks": 8,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if not self.current_project:
                return {"status": "error", "message": "No project loaded", "tracks": []}
            
            write_log("reaper_rpc", "LIST_TRACKS: iniciando", level="INFO")
            
            result = await self._http_call("GET", "/tracks")
            
            if result.get("status") == "success":
                tracks = result.get("data", [])
                write_log("reaper_rpc", f"LIST_TRACKS: {len(tracks)} pistas", level="INFO")
                
                return {
                    "status": "success",
                    "tracks": tracks,
                    "total_tracks": len(tracks),
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e), "tracks": []}

    # =========================================================================
    # MÉTODO 5: list_items
    # =========================================================================

    async def list_items(self, track_index: int = None) -> Dict[str, Any]:
        """
        Listar items de audio (clips).
        
        Args:
            track_index: Opcional, índice de pista; si None, todos los items
            
        Respuesta canónica:
        {
            "status": "success",
            "items": [
                {
                    "track_index": 0,
                    "item_index": 0,
                    "name": "Kick_01",
                    "start_position": 0.0,
                    "duration_seconds": 2.5,
                    "source_file": "/audio/kick.wav",
                    "playrate": 1.0,
                    "volume": 0.0,
                    "pan": 0.0,
                    "muted": false,
                    "lock": false
                },
                ...
            ],
            "total_items": 32,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if not self.current_project:
                return {"status": "error", "message": "No project loaded", "items": []}
            
            write_log("reaper_rpc", f"LIST_ITEMS: track={track_index}", level="INFO")
            
            path = f"/items?track_index={track_index}" if track_index is not None else "/items"
            result = await self._http_call("GET", path)
            
            if result.get("status") == "success":
                items = result.get("data", [])
                write_log("reaper_rpc", f"LIST_ITEMS: {len(items)} items", level="INFO")
                
                return {
                    "status": "success",
                    "items": items,
                    "total_items": len(items),
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e), "items": []}

    # =========================================================================
    # MÉTODO 6: list_fx
    # =========================================================================

    async def list_fx(self, track_index: int) -> Dict[str, Any]:
        """
        Listar efectos en una pista.
        
        Args:
            track_index: Índice de pista
            
        Respuesta canónica:
        {
            "status": "success",
            "track_index": 0,
            "track_name": "Drums",
            "fx": [
                {
                    "fx_index": 0,
                    "name": "Compressor",
                    "plugin_name": "ReaComp",
                    "category": "dynamics",
                    "params": {
                        "threshold": -20.0,
                        "ratio": 4.0,
                        "attack_ms": 10.0,
                        "release_ms": 100.0
                    },
                    "wet_level": 0.0,
                    "bypass": false
                },
                ...
            ],
            "total_fx": 2,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("reaper_rpc", f"LIST_FX: track={track_index}", level="INFO")
            
            result = await self._http_call("GET", f"/tracks/{track_index}/fx")
            
            if result.get("status") == "success":
                fx_list = result.get("data", [])
                write_log("reaper_rpc", f"LIST_FX: {len(fx_list)} efectos en pista {track_index}", level="INFO")
                
                return {
                    "status": "success",
                    "track_index": track_index,
                    "fx": fx_list,
                    "total_fx": len(fx_list),
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e), "fx": []}

    # =========================================================================
    # MÉTODO 7: apply_fx_chain
    # =========================================================================

    async def apply_fx_chain(self, track_index: int, fx_chain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplicar cadena de efectos a una pista.
        
        Args:
            track_index: Índice de pista
            fx_chain: {name, description, plugins: [{name, params, order}, ...], routing}
            
        Respuesta canónica:
        {
            "status": "success",
            "track_index": 0,
            "track_name": "Drums",
            "fx_chain_applied": {
                "name": "Shub_Auto_Mix_Chain",
                "plugins_count": 3,
                "plugins_installed": [
                    {"name": "ReaComp", "position": 0},
                    {"name": "ReaEQ", "position": 1},
                    {"name": "ReaLimit", "position": 2}
                ]
            },
            "before": {"loudness_lufs": -18.0, "dynamic_range": 15.0},
            "after": {"loudness_lufs": -14.0, "dynamic_range": 8.0},
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("reaper_rpc", f"APPLY_FX_CHAIN: track={track_index}", level="INFO")
            
            result = await self._http_call("POST", f"/tracks/{track_index}/apply_fx_chain", {
                "fx_chain": fx_chain
            })
            
            if result.get("status") == "success":
                write_log("reaper_rpc", f"APPLY_FX_CHAIN_SUCCESS: track={track_index}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 8: render_master
    # =========================================================================

    async def render_master(self, output_path: str, format: str = "wav", sample_rate: int = 44100) -> Dict[str, Any]:
        """
        Renderizar proyecto como master.
        
        Args:
            output_path: Ruta de salida (directorio)
            format: 'wav', 'mp3', 'flac'
            sample_rate: Sample rate de salida
            
        Respuesta canónica:
        {
            "status": "success",
            "render_start": "2024-12-10T15:30:00Z",
            "render_complete": "2024-12-10T15:35:30Z",
            "output": {
                "file_path": "/audio/masters/Song01_Master_2024-12-10.wav",
                "format": "wav",
                "sample_rate": 44100,
                "duration_seconds": 240.0,
                "file_size_mb": 42.3,
                "loudness_lufs": -14.0,
                "peak_dbfs": -0.3
            },
            "render_settings": {
                "normalize": false,
                "add_metadata": true,
                "stem_export": false
            },
            "timestamp": "2024-12-10T15:35:30Z"
        }
        """
        try:
            if not self.current_project:
                return {"status": "error", "message": "No project loaded"}
            
            write_log("reaper_rpc", f"RENDER_MASTER: {output_path}", level="INFO")
            
            result = await self._http_call("POST", "/projects/render", {
                "output_path": output_path,
                "format": format,
                "sample_rate": sample_rate
            })
            
            if result.get("status") == "success":
                write_log("reaper_rpc", f"RENDER_MASTER_SUCCESS: {result.get('output', {}).get('file_path')}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 9: update_project_metadata
    # =========================================================================

    async def update_project_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar metadata del proyecto.
        
        Args:
            metadata: {artist, title, genre, bpm, description, tags, ...}
            
        Respuesta canónica:
        {
            "status": "success",
            "project": "Song01",
            "metadata_updated": {
                "artist": "The Beatles",
                "title": "Let It Be",
                "genre": "Pop/Rock",
                "bpm": 120,
                "year": 2024,
                "tags": ["vx11", "shub", "auto_master"],
                "description": "Mastered with Shub-Niggurath DSP"
            },
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if not self.current_project:
                return {"status": "error", "message": "No project loaded"}
            
            write_log("reaper_rpc", "UPDATE_PROJECT_METADATA: iniciando", level="INFO")
            
            result = await self._http_call("PUT", "/projects/metadata", {
                "metadata": metadata
            })
            
            if result.get("status") == "success":
                write_log("reaper_rpc", "UPDATE_PROJECT_METADATA_SUCCESS", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 10: send_shub_status_to_reaper
    # =========================================================================

    async def send_shub_status_to_reaper(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enviar status de Shub a REAPER (notificación bidireccional).
        
        Args:
            status: {module, version, dsp_ready, fx_ready, batch_queue_size, ...}
            
        Respuesta canónica:
        {
            "status": "success",
            "message": "Shub status received in REAPER",
            "shub_status": {
                "module": "shubniggurath",
                "version": "7.0",
                "dsp_ready": true,
                "fx_ready": true,
                "batch_queue_size": 3,
                "last_analysis": "2024-12-10T15:30:00Z"
            },
            "reaper_acknowledged": true,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("reaper_rpc", "SEND_SHUB_STATUS_TO_REAPER: iniciando", level="INFO")
            
            result = await self._http_call("POST", "/status/notify", {
                "shub_status": status
            })
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 11: auto_mix
    # =========================================================================

    async def auto_mix(self, mix_style: str = "balanced") -> Dict[str, Any]:
        """
        Mezcla automática inteligente basada en IA de Switch.
        
        Args:
            mix_style: 'balanced', 'loud', 'warm', 'dynamic', 'clean'
            
        Respuesta canónica:
        {
            "status": "success",
            "mix_style": "balanced",
            "mix_complete": true,
            "changes": {
                "tracks_adjusted": 8,
                "fx_chains_applied": 8,
                "automation_generated": true
            },
            "before": {
                "loudness_lufs": -18.0,
                "dynamic_range": 15.0,
                "spectral_balance": {"low": 0.7, "mid": 1.0, "high": 0.8}
            },
            "after": {
                "loudness_lufs": -14.0,
                "dynamic_range": 8.0,
                "spectral_balance": {"low": 0.9, "mid": 1.0, "high": 0.95}
            },
            "time_elapsed_seconds": 45.3,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if not self.current_project:
                return {"status": "error", "message": "No project loaded"}
            
            write_log("reaper_rpc", f"AUTO_MIX: style={mix_style}", level="INFO")
            
            result = await self._http_call("POST", "/mix/auto", {
                "mix_style": mix_style
            })
            
            if result.get("status") == "success":
                write_log("reaper_rpc", f"AUTO_MIX_SUCCESS: style={mix_style}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 12: auto_master
    # =========================================================================

    async def auto_master(self, master_style: str = "streaming") -> Dict[str, Any]:
        """
        Mastering automático inteligente basado en género + análisis DSP.
        
        Args:
            master_style: 'streaming', 'vinyl', 'cd', 'loudness_war', 'dynamic'
            
        Respuesta canónica:
        {
            "status": "success",
            "master_style": "streaming",
            "master_complete": true,
            "master_bus_chain": {
                "plugins": [
                    {"name": "ReaEQ", "params": {...}},
                    {"name": "ReaComp", "params": {...}},
                    {"name": "ReaLimit", "params": {...}}
                ],
                "order": 3
            },
            "before": {
                "loudness_lufs": -14.0,
                "loudness_short_term": -12.5,
                "loudness_momentary": -8.0,
                "true_peak": -0.5
            },
            "after": {
                "loudness_lufs": -13.95,
                "loudness_short_term": -13.5,
                "loudness_momentary": -9.0,
                "true_peak": -0.3
            },
            "render_recommended": true,
            "time_elapsed_seconds": 120.5,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if not self.current_project:
                return {"status": "error", "message": "No project loaded"}
            
            write_log("reaper_rpc", f"AUTO_MASTER: style={master_style}", level="INFO")
            
            result = await self._http_call("POST", "/master/auto", {
                "master_style": master_style
            })
            
            if result.get("status") == "success":
                write_log("reaper_rpc", f"AUTO_MASTER_SUCCESS: style={master_style}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("reaper_rpc", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # CLEANUP & CONNECTION
    # =========================================================================

    async def cleanup(self):
        """Cleanup: cerrar cliente HTTP"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        write_log("reaper_rpc", "CLEANUP: conexión cerrada", level="INFO")

    async def health_check(self) -> Dict[str, Any]:
        """Health check de conexión a REAPER"""
        try:
            result = await self._http_call("GET", "/health")
            self.connected = result.get("status") == "success"
            return {
                "status": "connected" if self.connected else "disconnected",
                "endpoint": self.endpoint,
                "reaper_health": result
            }
        except Exception as e:
            self.connected = False
            return {"status": "disconnected", "endpoint": self.endpoint, "error": str(e)}
