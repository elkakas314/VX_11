"""
Executor for CLI providers.
Runs CLI commands with timeouts and logging.
"""

import subprocess
import shlex
import time
from typing import Optional, Dict, Any
from datetime import datetime

from .schemas import ProviderConfig, CLIUsageStat


class CLIExecutor:
    """Executes CLI commands safely."""

    def __init__(self, timeout_s: int = 30):
        """Initialize executor."""
        self.timeout_s = timeout_s

    def execute(
        self,
        provider: ProviderConfig,
        prompt: str,
        env_override: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute CLI command.

        Returns:
            {
                "success": bool,
                "reply": str,
                "latency_ms": int,
                "error_class": Optional[str],
                "tokens_estimated": int,
                "cost_estimated": float,
            }
        """
        start = time.time()
        try:
            # Simple execution: pass prompt to CLI
            cmd = shlex.split(provider.command or "")
            if not cmd:
                return {
                    "success": False,
                    "reply": "",
                    "latency_ms": int((time.time() - start) * 1000),
                    "error_class": "command_missing",
                    "tokens_estimated": 0,
                    "cost_estimated": 0.0,
                }
            cmd.append(prompt)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                env=env_override,
            )

            latency_ms = int((time.time() - start) * 1000)

            if result.returncode == 0:
                return {
                    "success": True,
                    "reply": result.stdout.strip(),
                    "latency_ms": latency_ms,
                    "error_class": None,
                    "tokens_estimated": len(prompt.split())
                    + len(result.stdout.split()),
                    "cost_estimated": 0.0,
                }
            else:
                return {
                    "success": False,
                    "reply": "",
                    "latency_ms": latency_ms,
                    "error_class": "command_failed",
                    "tokens_estimated": 0,
                    "cost_estimated": 0.0,
                }

        except subprocess.TimeoutExpired:
            latency_ms = int((time.time() - start) * 1000)
            return {
                "success": False,
                "reply": "",
                "latency_ms": latency_ms,
                "error_class": "timeout",
                "tokens_estimated": 0,
                "cost_estimated": 0.0,
            }

        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            return {
                "success": False,
                "reply": "",
                "latency_ms": latency_ms,
                "error_class": type(e).__name__,
                "tokens_estimated": 0,
                "cost_estimated": 0.0,
            }
