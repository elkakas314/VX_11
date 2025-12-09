"""
MCP Tools Wrappers: Context7, Playwright, and other external tools.
Optional integration for enhanced conversational capabilities.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

log = logging.getLogger("vx11.mcp.tools_wrapper")


class Context7Wrapper:
    """
    Context7: Advanced context extraction from conversations and documents.
    Extracts entities, relationships, and structured knowledge graphs.
    """
    
    def __init__(self, enable: bool = False):
        self.enable = enable
        self.extracted_contexts: Dict[str, Any] = {}
    
    async def extract_context(
        self,
        text: str,
        mode: str = "entities",  # "entities", "relationships", "knowledge_graph"
    ) -> Dict[str, Any]:
        """
        Extract structured context from text.
        
        Args:
            text: Input text to analyze
            mode: Extraction mode
        
        Returns:
            {
                "mode": str,
                "entities": List[str],
                "relationships": List[Dict],
                "knowledge_graph": Dict,
                "confidence": float,
            }
        """
        if not self.enable:
            return {
                "mode": mode,
                "entities": [],
                "relationships": [],
                "knowledge_graph": {},
                "confidence": 0.0,
                "note": "Context7 disabled",
            }
        
        result = {
            "mode": mode,
            "entities": [],
            "relationships": [],
            "knowledge_graph": {},
            "confidence": 0.7,  # Stub value
        }
        
        # Stub implementation: simple keyword extraction
        keywords = text.split()
        result["entities"] = list(set([w for w in keywords if len(w) > 3]))[:10]
        
        # Simple relationships (just pair consecutive entities)
        if len(result["entities"]) > 1:
            for i in range(len(result["entities"]) - 1):
                result["relationships"].append({
                    "from": result["entities"][i],
                    "to": result["entities"][i + 1],
                    "relation": "follows",
                })
        
        log.info(f"extract_context:mode={mode}:entities={len(result['entities'])}")
        return result
    
    async def build_knowledge_graph(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build unified knowledge graph from multiple extracted contexts."""
        if not self.enable:
            return {"nodes": [], "edges": [], "confidence": 0.0}
        
        nodes = set()
        edges = []
        
        for ctx in contexts:
            nodes.update(ctx.get("entities", []))
            edges.extend(ctx.get("relationships", []))
        
        return {
            "nodes": list(nodes),
            "edges": edges,
            "confidence": 0.7,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }


class PlaywrightWrapper:
    """
    Playwright: Browser automation for dynamic content extraction and testing.
    Optional tool for web scraping and interaction within conversations.
    """
    
    def __init__(self, enable: bool = False):
        self.enable = enable
        self.sessions: Dict[str, Any] = {}
    
    async def open_browser(
        self,
        headless: bool = True,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Open browser session (stub implementation).
        """
        if not self.enable:
            return {
                "status": "disabled",
                "note": "Playwright disabled",
            }
        
        session_id = f"pw-session-{len(self.sessions)}"
        self.sessions[session_id] = {
            "headless": headless,
            "opened_at": asyncio.get_event_loop().time(),
        }
        
        log.info(f"playwright:open_browser:session={session_id}:headless={headless}")
        
        return {
            "status": "ok",
            "session_id": session_id,
            "headless": headless,
        }
    
    async def navigate(self, session_id: str, url: str) -> Dict[str, Any]:
        """Navigate to URL (stub)."""
        if not self.enable:
            return {"status": "disabled"}
        
        if session_id not in self.sessions:
            return {"status": "error", "error": "session_not_found"}
        
        log.info(f"playwright:navigate:session={session_id}:url={url}")
        
        return {
            "status": "ok",
            "session_id": session_id,
            "url": url,
            "title": "Stub Title",
        }
    
    async def extract_content(self, session_id: str) -> Dict[str, Any]:
        """Extract page content (stub)."""
        if not self.enable:
            return {"status": "disabled"}
        
        if session_id not in self.sessions:
            return {"status": "error", "error": "session_not_found"}
        
        log.info(f"playwright:extract_content:session={session_id}")
        
        return {
            "status": "ok",
            "session_id": session_id,
            "content": "Stub page content extracted",
            "links": [],
            "images": [],
        }
    
    async def close_browser(self, session_id: str) -> Dict[str, Any]:
        """Close browser session (stub)."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            log.info(f"playwright:close_browser:session={session_id}")
        
        return {"status": "ok", "session_id": session_id}


class ToolsRegistry:
    """Registry for all available MCP tools."""
    
    def __init__(self, enable_context7: bool = False, enable_playwright: bool = False):
        self.context7 = Context7Wrapper(enable=enable_context7)
        self.playwright = PlaywrightWrapper(enable=enable_playwright)
        self.tools = {
            "context7": self.context7,
            "playwright": self.playwright,
        }
    
    async def call_tool(
        self,
        tool_name: str,
        method: str,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call a tool method dynamically.
        
        Args:
            tool_name: Name of tool ("context7", "playwright")
            method: Method name on the tool class
            args: Keyword arguments to pass
        
        Returns:
            Result from tool method
        """
        if tool_name not in self.tools:
            return {"status": "error", "error": f"tool_not_found:{tool_name}"}
        
        tool = self.tools[tool_name]
        if not hasattr(tool, method):
            return {"status": "error", "error": f"method_not_found:{tool_name}.{method}"}
        
        try:
            method_obj = getattr(tool, method)
            result = await method_obj(**args)
            return result
        except Exception as e:
            log.error(f"tool_call_error:{tool_name}.{method}:{e}")
            return {"status": "error", "error": str(e)}
    
    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get list of available tools and their methods."""
        return {
            "context7": [
                "extract_context",
                "build_knowledge_graph",
            ],
            "playwright": [
                "open_browser",
                "navigate",
                "extract_content",
                "close_browser",
            ],
        }
