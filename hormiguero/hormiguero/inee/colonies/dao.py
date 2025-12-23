"""INEE colonies DAO (stub for now, full impl in db/dao.py)."""

from typing import List


class INEERegistryDAO:
    """
    DAO for persisting INEE colonies/agents.
    Stub: returns empty lists (real DB integration in db/dao.py).
    """

    def get_colonies(self) -> List:
        """Get all colonies from DB."""
        return []

    def get_agents(self) -> List:
        """Get all agents from DB."""
        return []

    def save_colony(self, colony) -> bool:
        """Persist colony to DB."""
        return True

    def save_agent(self, agent) -> bool:
        """Persist agent to DB."""
        return True
