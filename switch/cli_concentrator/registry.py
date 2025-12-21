"""
Registry of available CLI providers.
Reads from DB and introspects local environment.
"""

import os
import subprocess
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
        builtin = {
            "copilot_cli": ProviderConfig(
                provider_id="copilot_cli",
                kind="copilot_cli",
                priority=1,
                enabled=os.getenv("VX11_COPILOT_CLI_ENABLED", "1") == "1",
                command="copilot-cli",
                auth_state="ok" if self._check_copilot_cli() else "needs_login",
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

    def _check_copilot_cli(self) -> bool:
        """Check if copilot-cli is available."""
        try:
            result = subprocess.run(
                ["copilot-cli", "--version"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
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
