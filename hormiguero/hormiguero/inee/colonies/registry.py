"""
INEE colonies registry: in-memory + DAO.
Stores remote colony registration, agent status, heartbeats.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime

# Simple imports: INEE modules at same level
try:
    from ..intents.types import INEEColony, INEEAgent
    from .dao import INEERegistryDAO
except ImportError:
    # Fallback: assume imports work when package is properly installed
    raise ImportError(
        "Failed to import INEE types and DAO; ensure inee package structure is correct"
    )


class INEERegistry:
    """
    In-memory registry for INEE colonies + DAO for persistence.
    Thread-safe (basic, no lock yet; upgradeable).
    """

    def __init__(self, dao: Optional["INEERegistryDAO"] = None):
        self.dao = dao or INEERegistryDAO()
        self._colonies: Dict[str, INEEColony] = {}
        self._agents: Dict[str, INEEAgent] = {}
        self._load_from_dao()

    def _load_from_dao(self):
        """Load colonies and agents from DAO on init."""
        try:
            self._colonies = {c.colony_id: c for c in self.dao.get_colonies()}
            self._agents = {a.agent_id: a for a in self.dao.get_agents()}
        except Exception:
            # DB not initialized yet; will populate on first write
            pass

    def register_colony(self, colony: INEEColony) -> bool:
        """Register or update a remote colony."""
        self._colonies[colony.colony_id] = colony
        return self.dao.save_colony(colony)

    def get_colony(self, colony_id: str) -> Optional[INEEColony]:
        """Get colony by ID."""
        return self._colonies.get(colony_id)

    def list_colonies(self) -> List[INEEColony]:
        """List all registered colonies."""
        return list(self._colonies.values())

    def register_agent(self, agent: INEEAgent) -> bool:
        """Register or update an agent within a colony."""
        if agent.colony_id not in self._colonies:
            return False  # Colony must exist first
        self._agents[agent.agent_id] = agent
        return self.dao.save_agent(agent)

    def get_agent(self, agent_id: str) -> Optional[INEEAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def list_agents_for_colony(self, colony_id: str) -> List[INEEAgent]:
        """List agents in a colony."""
        return [a for a in self._agents.values() if a.colony_id == colony_id]

    def update_heartbeat(self, colony_id: str) -> bool:
        """Update last_heartbeat timestamp for a colony."""
        colony = self._colonies.get(colony_id)
        if not colony:
            return False
        colony.last_heartbeat = datetime.utcnow().isoformat()
        return self.dao.save_colony(colony)

    def deregister_colony(self, colony_id: str) -> bool:
        """Remove a colony (soft: mark as disabled)."""
        colony = self._colonies.get(colony_id)
        if not colony:
            return False
        colony.status = "disabled"
        return self.dao.save_colony(colony)
