"""
Tests for CONTEXT-7 Advanced
Session clustering, topic signature, metadata injection
"""

import pytest
from tentaculo_link.context7_middleware import Context7Session, Context7Manager


class TestContext7SessionAdvanced:
    """CONTEXT-7 advanced features tests."""
    
    def test_session_signature(self):
        """Test session signature generation."""
        session = Context7Session("sess-123", "test_user")
        
        # Add messages
        session.add_message("user", "Hello, can you explain async/await in Python?")
        session.add_message("assistant", "Sure! async/await is...")
        session.add_message("user", "What about error handling?")
        
        sig = session.get_session_signature()
        assert "Msgs:3" in sig
        assert "Last:" in sig
    
    def test_metadata_for_switch(self):
        """Test metadata generation for Switch integration."""
        session = Context7Session("sess-456", "test_user")
        
        session.add_message("user", "Configure VX11 modules")
        session.add_message("assistant", "I'll help configure the modules")
        session.add_message("user", "Start with Madre")
        
        metadata = session.get_metadata_for_switch()
        
        assert "context_summary" in metadata
        assert "session_signature" in metadata
        assert "last_messages" in metadata
        assert "message_count" in metadata
        assert metadata["message_count"] == 3
    
    def test_summary_with_multiple_messages(self):
        """Test summary generation with many messages."""
        session = Context7Session("sess-789", "test_user")
        
        for i in range(10):
            session.add_message("user", f"Message {i} from user")
            session.add_message("assistant", f"Response {i} from assistant")
        
        summary = session.get_summary(256)
        assert len(summary) <= 256 + 3  # +3 for "..."
        assert "response" in summary.lower()


class TestContext7ManagerAdvanced:
    """Manager advanced features tests."""
    
    def test_manager_lru_eviction(self):
        """Test LRU eviction when max sessions exceeded."""
        manager = Context7Manager(max_sessions=3)
        
        # Create 4 sessions (should evict first)
        s1 = manager.get_or_create_session("sess-1")
        s2 = manager.get_or_create_session("sess-2")
        s3 = manager.get_or_create_session("sess-3")
        s4 = manager.get_or_create_session("sess-4")
        
        # sess-1 should be evicted
        assert "sess-1" not in manager.sessions
        assert "sess-4" in manager.sessions
    
    def test_manager_access_order(self):
        """Test that accessing session updates access order."""
        manager = Context7Manager(max_sessions=3)
        
        manager.get_or_create_session("sess-1")
        manager.get_or_create_session("sess-2")
        manager.get_or_create_session("sess-3")
        
        # Access sess-1 (moves to end)
        manager.get_or_create_session("sess-1")
        
        # Create new session (sess-2 should be evicted, not sess-1)
        manager.get_or_create_session("sess-4")
        
        assert "sess-2" not in manager.sessions
        assert "sess-1" in manager.sessions
    
    def test_get_metadata_for_switch(self):
        """Test metadata generation for Switch (advanced)."""
        manager = Context7Manager()
        
        manager.add_message("sess-abc", "user", "What modules are running?")
        manager.add_message("sess-abc", "assistant", "Here are the modules...")
        manager.add_message("sess-abc", "user", "Optimize Madre")
        
        metadata = manager.get_metadata_for_switch("sess-abc")
        
        assert metadata is not None
        assert "context_summary" in metadata
        assert "message_count" in metadata
        assert metadata["message_count"] == 3
    
    def test_no_metadata_for_nonexistent_session(self):
        """Test metadata for nonexistent session."""
        manager = Context7Manager()
        metadata = manager.get_metadata_for_switch("nonexistent")
        
        assert metadata == {}


class TestContext7Integration:
    """Integration tests for CONTEXT-7 with Tentáculo."""
    
    def test_full_session_lifecycle(self):
        """Test complete session lifecycle."""
        manager = Context7Manager()
        
        # Create and populate session
        session_id = "user-xyz-session"
        
        manager.add_message(session_id, "user", "Hello Operator")
        manager.add_message(session_id, "assistant", "Hello! How can I help?")
        manager.add_message(session_id, "user", "Check system status")
        manager.add_message(session_id, "tool", "System status: OK")
        
        # Get session
        session = manager.get_session(session_id)
        assert session is not None
        assert len(session.messages) == 4
        
        # Get metadata for Switch
        metadata = manager.get_metadata_for_switch(session_id)
        assert metadata["message_count"] == 4
        
        # Get hint for LLM
        hint = manager.get_hint_for_llm(session_id)
        assert len(hint) > 0
    
    def test_hint_generation(self):
        """Test hint generation for LLM (respects max_chars)."""
        manager = Context7Manager()
        
        manager.add_message("sess-hint", "user", "This is a very long message " * 50)
        
        hint = manager.get_hint_for_llm("sess-hint")
        assert isinstance(hint, str)
        assert len(hint) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
