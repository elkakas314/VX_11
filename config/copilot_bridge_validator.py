"""
FASE 9: Copilot Bridge Validation v6.2
Validación de integración MCP entre VX11 y Copilot
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime


class CopilotBridgeValidator:
    """Validador de puente Copilot-VX11"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    async def validate_mcp_protocol(self, endpoint: str = "http://127.0.0.1:52116") -> Dict[str, Any]:
        """Valida que MCP protocol esté implementado correctamente"""
        try:
            import httpx
            
            tests = []
            
            # Test 1: LIST_TOOLS
            async with httpx.AsyncClient() as client:
                payload = {
                    "method": "LIST_TOOLS",
                    "resource": "/mcp/tools",
                    "context7": self._default_ctx7(),
                }
                resp = await client.post(f"{endpoint}/mcp/copilot-bridge", json=payload, timeout=5)
                
                if resp.status_code == 200:
                    data = resp.json()
                    tests.append({
                        "test": "LIST_TOOLS",
                        "status": "PASS" if data.get("status") == "ok" else "FAIL",
                        "tools_count": len(data.get("tools", [])) if data.get("status") == "ok" else 0,
                    })
                else:
                    tests.append({
                        "test": "LIST_TOOLS",
                        "status": "FAIL",
                        "error": f"HTTP {resp.status_code}",
                    })
            
            # Test 2: CALL_TOOL
            async with httpx.AsyncClient() as client:
                payload = {
                    "method": "CALL_TOOL",
                    "resource": "/mcp/tools",
                    "params": {
                        "tool_name": "context7",
                        "method": "validate",
                        "args": {"ctx": self._default_ctx7()},
                    },
                    "context7": self._default_ctx7(),
                }
                resp = await client.post(f"{endpoint}/mcp/copilot-bridge", json=payload, timeout=5)
                
                if resp.status_code == 200:
                    data = resp.json()
                    tests.append({
                        "test": "CALL_TOOL",
                        "status": "PASS" if data.get("status") == "ok" else "FAIL",
                    })
                else:
                    tests.append({
                        "test": "CALL_TOOL",
                        "status": "FAIL",
                        "error": f"HTTP {resp.status_code}",
                    })
            
            # Test 3: POST /chat
            async with httpx.AsyncClient() as client:
                payload = {
                    "method": "POST",
                    "resource": "/mcp/chat",
                    "params": {
                        "message": "Test message",
                        "session_id": "test-session",
                    },
                    "context7": self._default_ctx7(),
                }
                resp = await client.post(f"{endpoint}/mcp/copilot-bridge", json=payload, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    tests.append({
                        "test": "POST_CHAT",
                        "status": "PASS" if data.get("status") == "ok" else "FAIL",
                    })
                else:
                    tests.append({
                        "test": "POST_CHAT",
                        "status": "FAIL",
                        "error": f"HTTP {resp.status_code}",
                    })
            
            passed = sum(1 for t in tests if t["status"] == "PASS")
            total = len(tests)
            
            return {
                "validation": "MCP_PROTOCOL",
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
                "tests": tests,
                "summary": {
                    "passed": passed,
                    "total": total,
                    "success_rate": f"{(passed/total)*100:.1f}%" if total > 0 else "0%",
                }
            }
        
        except Exception as e:
            return {
                "validation": "MCP_PROTOCOL",
                "status": "ERROR",
                "error": str(e),
            }
    
    async def validate_context7_propagation(self, endpoint: str = "http://127.0.0.1:52116") -> Dict[str, Any]:
        """Valida que context-7 se propague correctamente"""
        try:
            import httpx
            
            ctx7 = self._default_ctx7()
            ctx7["layer7_meta"]["trace_id"] = "validation-trace-123"
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "method": "POST",
                    "resource": "/mcp/chat",
                    "params": {
                        "message": "Echo test",
                        "session_id": "ctx7-test",
                    },
                    "context7": ctx7,
                }
                resp = await client.post(f"{endpoint}/mcp/copilot-bridge", json=payload, timeout=10)
                
                if resp.status_code == 200:
                    return {
                        "validation": "CONTEXT7_PROPAGATION",
                        "status": "PASS",
                        "trace_id": ctx7["layer7_meta"]["trace_id"],
                        "response_status": resp.json().get("status"),
                    }
                else:
                    return {
                        "validation": "CONTEXT7_PROPAGATION",
                        "status": "FAIL",
                        "error": f"HTTP {resp.status_code}",
                    }
        
        except Exception as e:
            return {
                "validation": "CONTEXT7_PROPAGATION",
                "status": "ERROR",
                "error": str(e),
            }
    
    async def validate_orchestration_integration(self, gateway_endpoint: str = "http://tentaculo_link:8000") -> Dict[str, Any]:
        """Valida que la orquestación completa funcione via Tentaculo Link"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "query": "List recent tasks",
                    "context7": self._default_ctx7(),
                    "pipeline_type": "quick",
                }
                resp = await client.post(
                    f"{gateway_endpoint}/vx11/orchestrate",
                    json=payload,
                    timeout=20
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "validation": "ORCHESTRATION_INTEGRATION",
                        "status": "PASS" if data.get("status") == "ok" else "FAIL",
                        "pipeline_executed": True,
                    }
                else:
                    return {
                        "validation": "ORCHESTRATION_INTEGRATION",
                        "status": "FAIL",
                        "error": f"HTTP {resp.status_code}",
                    }
        
        except Exception as e:
            return {
                "validation": "ORCHESTRATION_INTEGRATION",
                "status": "ERROR",
                "error": str(e),
            }
    
    def _default_ctx7(self) -> Dict[str, Any]:
        """Retorna contexto-7 por defecto para validación"""
        return {
            "layer1_user": {
                "user_id": "copilot-validator",
                "language": "es",
                "verbosity": "normal",
            },
            "layer2_session": {
                "session_id": "validator-session",
                "channel": "copilot",
                "start_time": datetime.utcnow().isoformat(),
            },
            "layer3_task": {
                "task_id": "validation-task",
                "task_type": "validation",
                "priority": "high",
            },
            "layer4_environment": {
                "os": "linux",
                "vx_version": "6.2",
                "cpu_load": 0.5,
            },
            "layer5_security": {
                "auth_level": "admin",
                "sandbox": False,
            },
            "layer6_history": {
                "recent_commands": [],
                "successes_count": 0,
            },
            "layer7_meta": {
                "explain_mode": True,
                "debug_trace": True,
                "mode": "balanced",
            },
        }
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Ejecuta todas las validaciones"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "validations": [],
        }
        
        # MCP Protocol
        mcp_result = await self.validate_mcp_protocol()
        results["validations"].append(mcp_result)
        
        # Context-7 Propagation
        ctx7_result = await self.validate_context7_propagation()
        results["validations"].append(ctx7_result)
        
        # Orchestration
        orch_result = await self.validate_orchestration_integration()
        results["validations"].append(orch_result)
        
        # Summary
        passed = sum(1 for v in results["validations"] if v.get("status") == "PASS")
        total = len(results["validations"])
        
        results["summary"] = {
            "total_validations": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed/total)*100:.1f}%" if total > 0 else "0%",
        }
        
        return results


# Singleton
_validator = None


def get_copilot_validator() -> CopilotBridgeValidator:
    global _validator
    if _validator is None:
        _validator = CopilotBridgeValidator()
    return _validator
