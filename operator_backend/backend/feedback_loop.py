"""
Switch Feedback Loop Integration
Tracks Switch performance, latency, tool failures for adaptive routing.
Persists feedback to operator_switch_adjustment table.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from config.db_schema import get_session, OperatorSwitchAdjustment
from config.forensics import write_log


class SwitchFeedback:
    """Feedback tracking for Switch adaptive routing."""
    
    @staticmethod
    async def record_feedback(
        session_id: str,
        message_id: Optional[int],
        before_config: Dict[str, Any],
        after_config: Dict[str, Any],
        reason: str,
        applied: bool = False,
    ) -> Dict[str, Any]:
        """Record Switch adjustment feedback."""
        try:
            db = get_session("vx11")
            
            adjustment = OperatorSwitchAdjustment(
                session_id=session_id,
                message_id=message_id,
                before_config=json.dumps(before_config),
                after_config=json.dumps(after_config),
                reason=reason,
                applied=applied,
            )
            
            db.add(adjustment)
            db.commit()
            
            write_log("operator_feedback", f"feedback_recorded:{session_id}:{reason}")
            
            return {"status": "ok", "feedback_id": adjustment.id}
        
        except Exception as exc:
            write_log("operator_feedback", f"feedback_error:{exc}", level="ERROR")
            return {"status": "error", "error": str(exc)}
        finally:
            db.close()
    
    @staticmethod
    async def record_tool_failure(
        session_id: str,
        message_id: int,
        tool_name: str,
        error: str,
    ) -> Dict[str, Any]:
        """Record tool failure feedback."""
        reason = f"tool_failure:{tool_name}:{error[:50]}"
        return await SwitchFeedback.record_feedback(
            session_id=session_id,
            message_id=message_id,
            before_config={"tool": tool_name, "status": "pending"},
            after_config={"tool": tool_name, "status": "failed", "error": error},
            reason=reason,
            applied=False,
        )
    
    @staticmethod
    async def record_latency_issue(
        session_id: str,
        message_id: int,
        latency_ms: int,
        threshold_ms: int = 5000,
    ) -> Optional[Dict[str, Any]]:
        """Record latency issue if exceeds threshold."""
        if latency_ms <= threshold_ms:
            return None
        
        reason = f"latency_excess:{latency_ms}ms"
        return await SwitchFeedback.record_feedback(
            session_id=session_id,
            message_id=message_id,
            before_config={"latency_ms": latency_ms, "status": "slow"},
            after_config={"latency_ms": latency_ms, "status": "flagged"},
            reason=reason,
            applied=False,
        )
    
    @staticmethod
    async def record_quality_issue(
        session_id: str,
        message_id: int,
        issue_type: str,
        details: str,
    ) -> Dict[str, Any]:
        """Record response quality issue."""
        reason = f"quality_issue:{issue_type}:{details[:30]}"
        return await SwitchFeedback.record_feedback(
            session_id=session_id,
            message_id=message_id,
            before_config={"quality_check": "pending"},
            after_config={"quality_check": "failed", "issue": issue_type},
            reason=reason,
            applied=False,
        )
