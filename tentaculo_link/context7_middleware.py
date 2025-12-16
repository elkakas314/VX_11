"""
CONTEXT-7 Gateway Middleware
Lightweight session context tracking for operator conversations
No IA (no LLM calls here), only DB + basic logic
"""

from typing import Dict, Any, Optional
from datetime import datetime
from config.db_schema import get_session
from config.forensics import write_log
import json


class Context7Session:
    """Lightweight representation of a conversation session."""

    def __init__(self, session_id: str, user_id: str = "local"):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.messages: list[Dict[str, Any]] = []
        self.max_messages = 50

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Add message to session history."""
        msg = {
            "role": role,  # user, assistant, tool, system
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.messages.append(msg)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def get_summary(self, max_chars: int = 512) -> str:
        """Generate a short text summary for LLM hints (no IA here, just text extraction)."""
        if not self.messages:
            return ""
        recent = self.messages[-3:]  # Last 3 messages
        summary_parts = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]  # First 100 chars
            summary_parts.append(f"{role}: {content}")
        summary = "\n".join(summary_parts)
        if len(summary) > max_chars:
            summary = summary[:max_chars] + "..."
        return summary

    def get_session_signature(self) -> str:
        """Generate one-line session signature for metadata."""
        if not self.messages:
            return "Empty"
        msg_count = len(self.messages)
        last_msg = self.messages[-1].get("content", "")[:30]
        return f"Msgs:{msg_count} Last:{last_msg}..."

    def get_topic_cluster(self) -> str:
        """Extract topic from recent messages (simple keyword-based)."""
        if not self.messages:
            return "general"
        recent = " ".join([msg.get("content", "") for msg in self.messages[-3:]])
        keywords = {
            "code": [
                "code",
                "python",
                "javascript",
                "function",
                "class",
                "bug",
                "debug",
            ],
            "audio": ["audio", "music", "sound", "shub", "ffmpeg", "mix", "frequency"],
            "browser": [
                "browser",
                "screenshot",
                "page",
                "playwright",
                "click",
                "navigate",
            ],
            "system": [
                "vx11",
                "module",
                "health",
                "status",
                "operator",
                "switch",
                "madre",
            ],
            "chat": ["hello", "hi", "how", "what", "question"],
        }
        recent_lower = recent.lower()
        for topic, words in keywords.items():
            if any(word in recent_lower for word in words):
                return topic
        return "general"

    def get_compressed_context(self) -> str:
        """Compress conversation into single-line summary (for token efficiency)."""
        if not self.messages:
            return "No context"
        topics = [msg.get("content", "")[:20] for msg in self.messages[-5:]]
        return " | ".join(topics)

    def get_metadata_for_switch(self) -> Dict[str, Any]:
        """Get full metadata to send to Switch (CONTEXT-7 advanced)."""
        return {
            "context_summary": self.get_summary(512),
            "session_signature": self.get_session_signature(),
            "topic_cluster": self.get_topic_cluster(),
            "compressed_context": self.get_compressed_context(),
            "last_messages": [msg.get("content") for msg in self.messages[-4:]],
            "message_count": len(self.messages),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "message_count": len(self.messages),
            "messages": self.messages,
            "summary": self.get_summary(),
        }


class Context7Manager:
    """Manages Context-7 sessions and persistence."""

    def __init__(self, max_sessions: int = 100):
        self.sessions: Dict[str, Context7Session] = {}
        self.max_sessions = max_sessions

    def get_or_create_session(
        self, session_id: str, user_id: str = "local"
    ) -> Context7Session:
        """Get existing session or create new one."""
        if session_id in self.sessions:
            # Update last_accessed on every access (LRU)
            self.sessions[session_id].last_accessed = datetime.utcnow()
            return self.sessions[session_id]
        session = Context7Session(session_id, user_id)
        self.sessions[session_id] = session
        if len(self.sessions) > self.max_sessions:
            # Remove least recently accessed session (true LRU)
            lru_id = min(
                self.sessions.keys(), key=lambda k: self.sessions[k].last_accessed
            )
            del self.sessions[lru_id]
        write_log("tentaculo_link", f"context7_session_created:{session_id}")
        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add message to session."""
        session = self.get_or_create_session(session_id)
        session.add_message(role, content, metadata)
        write_log("tentaculo_link", f"context7_message_added:{session_id}:{role}")

    def get_session(self, session_id: str) -> Optional[Context7Session]:
        """Retrieve session."""
        return self.sessions.get(session_id)

    def get_metadata_for_switch(self, session_id: str) -> Dict[str, Any]:
        """Get metadata from session to send to Switch."""
        session = self.get_session(session_id)
        if not session:
            return {}
        return session.get_metadata_for_switch()

    def get_hint_for_llm(self, session_id: str) -> str:
        """Generate a short hint to send as X-VX11-Context-Summary header."""
        session = self.get_session(session_id)
        if not session:
            return ""
        return session.get_summary(max_chars=256)

    def persist_to_db(self, session_id: str):
        """Optionally persist session to DB (for future persistence layer)."""
        # TODO: implement DB persistence when table is added
        # For now, just keep in-memory
        write_log("tentaculo_link", f"context7_session_persisted:{session_id}")


# Global instance
_context7_manager: Optional[Context7Manager] = None


def get_context7_manager() -> Context7Manager:
    """Get or create global Context-7 manager."""
    global _context7_manager
    if _context7_manager is None:
        _context7_manager = Context7Manager()
    return _context7_manager
