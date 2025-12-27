"""
Warm-up Engine para Switch

Precalienta modelos locales y CLIs en startup para evitar cold-starts.
Mantiene caché de modelos calientes según prioridades.
"""

import asyncio
import logging
import httpx
import os
from config.settings import settings
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

log = logging.getLogger("vx11.switch.warm_up")


class WarmUpEngine:
    """Precalienta modelos y recursos clave en startup"""

    def __init__(
        self,
        hermes_endpoint: str = "http://hermes:8003",
        config_path: str = "switch/warm_up_config.json",
    ):
        self.hermes_endpoint = hermes_endpoint
        self.config_path = config_path
        self.warm_models: Dict[str, Dict[str, Any]] = {}
        self.last_warmup: Optional[datetime] = None
        self.warmup_health: Dict[str, str] = {}

        self._load_config()
        # Modo mock para entornos de CI/local: evita llamadas de red costosas
        self.mock_providers = bool(
            os.getenv("VX11_MOCK_PROVIDERS", "0") == "1"
        ) or getattr(settings, "testing_mode", False)

    def _load_config(self):
        """Carga configuración de modelos a precalentar"""
        path = Path(self.config_path)

        # Configuración por defecto
        default_config = {
            "enabled": True,
            "startup_warmup": True,
            "periodic_warmup_minutes": 60,
            "models": [
                {
                    "name": "local_gguf_small",
                    "priority": 1,
                    "warmup_tokens": 50,
                    "timeout_seconds": 10,
                    "enabled": True,
                },
                {
                    "name": "deepseek_r1",
                    "priority": 2,
                    "warmup_tokens": 100,
                    "timeout_seconds": 30,
                    "enabled": True,
                },
                {
                    "name": "ollama_local",
                    "priority": 1,
                    "warmup_tokens": 50,
                    "timeout_seconds": 10,
                    "enabled": True,
                },
            ],
            "cli_tools": [
                {
                    "name": "cli_registry",
                    "warmup_command": "list",
                    "timeout_seconds": 5,
                    "enabled": True,
                },
            ],
        }

        if path.exists():
            try:
                with open(path, "r") as f:
                    config = json.load(f)
                    log.info(f"Warm-up config cargado desde {path}")
            except Exception as e:
                log.warning(f"Error cargando warm-up config: {e}, usando defaults")
                config = default_config
        else:
            config = default_config
            self._save_config(config)

        self.config = config

    def _save_config(self, config: Dict[str, Any]):
        """Guarda configuración a disco"""
        try:
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            log.error(f"Error guardando warm-up config: {e}")

    async def warmup_startup(self) -> Dict[str, str]:
        """
        Precalentamiento en startup.
        Calienta todos los modelos priorizados.
        """
        if not self.config.get("enabled"):
            log.info("Warm-up deshabilitado")
            return {}

        if not self.config.get("startup_warmup"):
            log.info("Warm-up en startup deshabilitado")
            return {}

        log.info("Iniciando precalentamiento de modelos (startup)...")

        self.warmup_health = {}
        results = {}

        # Precalentar modelos IA
        models = sorted(
            self.config.get("models", []), key=lambda x: x.get("priority", 999)
        )

        for model_info in models:
            if not model_info.get("enabled", True):
                continue

            model_name = model_info.get("name")
            log.info(f"  Precalentando modelo: {model_name}")

            if self.mock_providers:
                log.info(
                    f"  ~ Mock warm-up enabled: skipping network warmup for {model_info.get('name')}"
                )
                success = True
            else:
                success = await self._warmup_model(model_info)
            self.warmup_health[model_name] = "ready" if success else "failed"
            results[model_name] = "ready" if success else "failed"

        # Precalentar CLIs
        cli_tools = self.config.get("cli_tools", [])
        for cli_info in cli_tools:
            if not cli_info.get("enabled", True):
                continue

            cli_name = cli_info.get("name")
            log.info(f"  Precalentando CLI: {cli_name}")

            if self.mock_providers:
                log.info(
                    f"  ~ Mock warm-up enabled: skipping network warmup for CLI {cli_name}"
                )
                success = True
            else:
                success = await self._warmup_cli(cli_info)
            self.warmup_health[cli_name] = "ready" if success else "failed"
            results[cli_name] = "ready" if success else "failed"

        self.last_warmup = datetime.utcnow()

        log.info(f"Precalentamiento completado. Health: {self.warmup_health}")
        return results

    async def _warmup_model(self, model_info: Dict[str, Any]) -> bool:
        """Precalienta un modelo IA individual"""
        model_name = model_info.get("name")
        warmup_tokens = model_info.get("warmup_tokens", 50)
        timeout_seconds = model_info.get("timeout_seconds", 10)

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                # Consultar Hermes para obtener endpoint del modelo
                resp = await client.post(
                    f"{self.hermes_endpoint}/hermes/get-engine",
                    json={"engine_id": model_name},
                    timeout=timeout_seconds,
                )

                if resp.status_code != 200:
                    log.warning(f"Modelo {model_name} no disponible en Hermes")
                    return False

                engine_info = resp.json()
                endpoint = engine_info.get("endpoint")

                if not endpoint:
                    log.warning(f"Modelo {model_name} sin endpoint")
                    return False

                # Enviar prompt de prueba
                test_prompt = f"Eres un modelo de prueba. Responde brevemente: 1+1={warmup_tokens}"

                warmup_resp = await client.post(
                    f"{endpoint}/v1/completions",
                    json={
                        "prompt": test_prompt,
                        "max_tokens": warmup_tokens,
                        "temperature": 0.1,
                    },
                    timeout=timeout_seconds,
                )

                if warmup_resp.status_code == 200:
                    log.info(f"  ✓ {model_name} precalentado exitosamente")
                    return True
                else:
                    log.warning(
                        f"  ✗ {model_name} fallo en precalentamiento: {warmup_resp.status_code}"
                    )
                    return False

        except asyncio.TimeoutError:
            log.warning(f"  ✗ {model_name} timeout ({timeout_seconds}s)")
            return False
        except Exception as e:
            log.warning(f"  ✗ {model_name} error: {e}")
            return False

    async def _warmup_cli(self, cli_info: Dict[str, Any]) -> bool:
        """Precalienta herramientas CLI"""
        cli_name = cli_info.get("name")
        warmup_command = cli_info.get("warmup_command", "list")
        timeout_seconds = cli_info.get("timeout_seconds", 5)

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(
                    f"{self.hermes_endpoint}/hermes/execute",
                    json={
                        "command": warmup_command,
                        "tool": cli_name,
                    },
                    timeout=timeout_seconds,
                )

                if resp.status_code == 200:
                    log.info(f"  ✓ {cli_name} precalentado exitosamente")
                    return True
                else:
                    log.warning(f"  ✗ {cli_name} fallo: {resp.status_code}")
                    return False

        except asyncio.TimeoutError:
            log.warning(f"  ✗ {cli_name} timeout ({timeout_seconds}s)")
            return False
        except Exception as e:
            log.warning(f"  ✗ {cli_name} error: {e}")
            return False

    async def warmup_periodic(self):
        """
        Precalentamiento periódico en background.
        Se ejecuta cada X minutos según configuración.
        """
        if not self.config.get("enabled"):
            return

        interval_minutes = self.config.get("periodic_warmup_minutes", 60)

        log.info(f"Iniciando warmup periódico (cada {interval_minutes} minutos)...")

        while True:
            try:
                await asyncio.sleep(interval_minutes * 60)

                # Verificar si fue precalentado recientemente
                if self.last_warmup:
                    elapsed = datetime.utcnow() - self.last_warmup
                    if elapsed < timedelta(minutes=interval_minutes * 0.8):
                        # Reciente, saltear
                        continue

                log.info(f"Ejecutando warmup periódico...")
                await self.warmup_startup()

            except Exception as e:
                log.error(f"Error en warmup periódico: {e}")

    def get_health(self) -> Dict[str, Any]:
        """Retorna estado de salud de modelos precalentados"""
        return {
            "warmup_enabled": self.config.get("enabled", False),
            "last_warmup": self.last_warmup.isoformat() if self.last_warmup else None,
            "models_health": self.warmup_health,
            "total_ready": sum(1 for v in self.warmup_health.values() if v == "ready"),
            "total_failed": sum(
                1 for v in self.warmup_health.values() if v == "failed"
            ),
        }

    def reset_health(self):
        """Resetea estado de salud para re-precalentamiento"""
        self.warmup_health = {}
        self.last_warmup = None
        log.info("Health de warm-up reseteado")
