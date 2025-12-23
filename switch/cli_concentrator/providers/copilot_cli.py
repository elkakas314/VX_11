"""
Copilot CLI provider wrapper (real exec with test-safe mock).
"""

from typing import Dict, Any, Optional, List
import os
import shlex
import subprocess
import time

from ..schemas import ProviderConfig


CLIResponse = Dict[str, Any]


class CopilotCLIProvider:
    """Wrapper for Copilot CLI provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize provider."""
        self.config = config

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.config.auth_state == "ok" and bool(self.config.command)

    def _mock_enabled(self) -> bool:
        return os.getenv("VX11_MOCK_PROVIDERS", "0") == "1" or os.getenv(
            "VX11_TESTING_MODE", "0"
        ) == "1"

    def _build_command(self, prompt: str) -> List[str]:
        cmd = shlex.split(self.config.command or "")
        if not cmd:
            return []
        if self.config.args_template:
            formatted = self.config.args_template.format(prompt=prompt)
            cmd += shlex.split(formatted)
        else:
            cmd.append(prompt)
        return cmd

    def call(
        self, prompt: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Copilot CLI.

        Returns:
            {
                "success": bool,
                "reply": str,
                "latency_ms": int,
                "tokens_estimated": int,
                "cost_estimated": float,
                "error_class": Optional[str],
                "engine": str,
                "ok": bool,
            }
        """
        if self._mock_enabled():
            return {
                "success": self.is_available(),
                "ok": self.is_available(),
                "engine": self.config.provider_id,
                "reply": (
                    f"[Copilot CLI mock] {prompt[:50]}..."
                    if self.is_available()
                    else ""
                ),
                "latency_ms": 1,
                "tokens_estimated": len(prompt.split()),
                "cost_estimated": 0.0,
                "error_class": None if self.is_available() else "not_available",
            }

        if not self.is_available():
            return {
                "success": False,
                "ok": False,
                "engine": self.config.provider_id,
                "reply": "",
                "latency_ms": 0,
                "tokens_estimated": 0,
                "cost_estimated": 0.0,
                "error_class": "not_available",
            }

        cmd = self._build_command(prompt)
        if not cmd:
            return {
                "success": False,
                "ok": False,
                "engine": self.config.provider_id,
                "reply": "",
                "latency_ms": 0,
                "tokens_estimated": 0,
                "cost_estimated": 0.0,
                "error_class": "command_missing",
            }

        start = time.monotonic()
        try:
            timeout_s = int(os.getenv("VX11_CLI_TIMEOUT", "30"))
            result = subprocess.run(
                cmd,
                input=None,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            if result.returncode == 0:
                output = (result.stdout or "").strip()
                return {
                    "success": True,
                    "ok": True,
                    "engine": self.config.provider_id,
                    "reply": output,
                    "latency_ms": latency_ms,
                    "tokens_estimated": len(prompt.split()) + len(output.split()),
                    "cost_estimated": 0.0,
                    "error_class": None,
                }
            return {
                "success": False,
                "ok": False,
                "engine": self.config.provider_id,
                "reply": "",
                "latency_ms": latency_ms,
                "tokens_estimated": 0,
                "cost_estimated": 0.0,
                "error_class": "command_failed",
            }
        except subprocess.TimeoutExpired:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "success": False,
                "ok": False,
                "engine": self.config.provider_id,
                "reply": "",
                "latency_ms": latency_ms,
                "tokens_estimated": 0,
                "cost_estimated": 0.0,
                "error_class": "timeout",
            }
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "success": False,
                "ok": False,
                "engine": self.config.provider_id,
                "reply": "",
                "latency_ms": latency_ms,
                "tokens_estimated": 0,
                "cost_estimated": 0.0,
                "error_class": type(exc).__name__,
            }
