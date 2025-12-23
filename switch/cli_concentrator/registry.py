"""
Registry of available CLI providers.
Reads from DB and introspects local environment.
"""

import os
import subprocess
import shutil
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from .schemas import ProviderConfig


class CLIRegistry:
    """Manages available CLI providers."""

    def __init__(self, db_session=None):
        """Initialize registry, optionally with DB session."""
        self.db_session = db_session
        self.providers: Dict[str, ProviderConfig] = {}
        self._load_providers()

    def _load_providers(self):
        """Load providers from environment and (optionally) DB."""
        # Default builtin providers
        copilot_enabled = os.getenv("VX11_COPILOT_CLI_ENABLED", "1") == "1"
        copilot_cmd = self._detect_copilot_command()
        copilot_auth_ok = self._check_copilot_auth(copilot_cmd)

        builtin = {
            "copilot_cli": ProviderConfig(
                provider_id="copilot_cli",
                kind="copilot_cli",
                priority=1,
                enabled=copilot_enabled and bool(copilot_cmd),
                command=copilot_cmd.get("command", "") if copilot_cmd else "",
                args_template=copilot_cmd.get("args_template", "") if copilot_cmd else "",
                auth_state="ok" if copilot_auth_ok else "needs_login",
                tags=["language", "general"],
            ),
            "generic_shell": ProviderConfig(
                provider_id="generic_shell",
                kind="generic_shell",
                priority=10,
                enabled=True,
                command="sh -c",
                auth_state="ok",
                tags=["general", "cli"],
            ),
        }

        # Load from DB if session provided
        if self.db_session:
            try:
                from config.db_schema import CLIProvider as CLIProviderModel
                db_providers = self.db_session.query(CLIProviderModel).filter_by(enabled=True).all()
                for db_p in db_providers:
                    if db_p.name not in builtin:
                        builtin[db_p.name] = ProviderConfig(
                            provider_id=db_p.name,
                            kind=db_p.kind,
                            priority=db_p.priority or 50,
                            enabled=True,
                            command=db_p.command or "",
                            auth_state=db_p.auth_state or "ok",
                            tags=(db_p.tags or "").split(","),
                        )
            except Exception:
                pass  # DB not available; use builtins only

        self.providers = builtin

    def _detect_copilot_command(self) -> Optional[Dict[str, str]]:
        """Detect available Copilot CLI command and default args template."""
        if shutil.which("copilot-cli"):
            args_template = self._guess_copilot_args(["copilot-cli", "--help"])
            return {"command": "copilot-cli", "args_template": args_template}

        if shutil.which("gh"):
            gh_help = self._run_help(["gh", "copilot", "--help"])
            if gh_help:
                args_template = self._guess_gh_copilot_args(gh_help)
                return {"command": "gh", "args_template": args_template}
        return None

    def _run_help(self, cmd: List[str]) -> Optional[str]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return (result.stdout or "") + (result.stderr or "")
        except Exception:
            return None
        return None

    def _guess_copilot_args(self, help_cmd: List[str]) -> str:
        """Return args_template for copilot-cli based on help output."""
        help_text = self._run_help(help_cmd) or ""
        if "chat" in help_text:
            return "chat {prompt}"
        if "ask" in help_text:
            return "ask {prompt}"
        return "{prompt}"

    def _guess_gh_copilot_args(self, help_text: str) -> str:
        """Return args_template for gh copilot based on help output."""
        if "chat" in help_text:
            return "copilot chat {prompt}"
        if "explain" in help_text:
            return "copilot explain {prompt}"
        return "copilot suggest -t shell {prompt}"

    def _check_copilot_auth(self, command_meta: Optional[Dict[str, str]]) -> bool:
        """Check if Copilot CLI is authenticated (non-interactive)."""
        if not command_meta:
            return False
        cmd = command_meta.get("command") or ""
        if not cmd:
            return False
        try:
            if cmd == "gh":
                result = subprocess.run(
                    ["gh", "auth", "status"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                return result.returncode == 0
            if cmd == "copilot-cli":
                result = subprocess.run(
                    ["copilot-cli", "auth", "status"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                return result.returncode == 0
        except Exception:
            return False
        return False

    def get_provider(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get a single provider by ID."""
        return self.providers.get(provider_id)

    def list_providers(self, filter_tags: List[str] = None) -> List[ProviderConfig]:
        """List providers, optionally filtered by tags."""
        providers = list(self.providers.values())
        if filter_tags:
            providers = [p for p in providers if any(tag in p.tags for tag in filter_tags)]
        return sorted(providers, key=lambda p: p.priority)

    def get_by_priority(self) -> List[ProviderConfig]:
        """Get all enabled providers sorted by priority (ascending)."""
        return sorted(
            [p for p in self.providers.values() if p.enabled],
            key=lambda p: p.priority,
        )


# Singleton
_registry: Optional[CLIRegistry] = None


def get_cli_registry(db_session=None) -> CLIRegistry:
    """Get or create CLI registry singleton."""
    global _registry
    if _registry is None:
        _registry = CLIRegistry(db_session)
    return _registry
