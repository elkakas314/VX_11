"""Madre DB Repository: encapsulates all BD operations."""

from config.db_schema import (
    get_session,
    Task,
    Context,
    IntentLog,
    MadreAction,
    MadrePolicy,
    DaughterTask,
)
from datetime import datetime
import json
import logging
from typing import Optional, Dict, Any, List

log = logging.getLogger("madre.db")


class MadreDB:
    """Repository pattern: encapsulates all Madre DB writes/reads."""

    @staticmethod
    def create_intent_log(
        source: str,
        payload: Dict[str, Any],
        result_status: str = "planned",
        notes: Optional[str] = None,
    ) -> int:
        """Insert row in intents_log. Returns ID."""
        db = get_session("vx11")
        try:
            entry = IntentLog(
                source=source,
                payload_json=json.dumps(payload),
                result_status=result_status,
                notes=notes or "",
            )
            db.add(entry)
            db.commit()
            return entry.id
        except Exception as e:
            log.error(f"create_intent_log failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def close_intent_log(
        intent_log_id: int,
        result_status: str,
        notes: Optional[str] = None,
    ) -> None:
        """Update intents_log row with final status."""
        db = get_session("vx11")
        try:
            entry = db.query(IntentLog).filter_by(id=intent_log_id).first()
            if entry:
                entry.processed_by_madre_at = datetime.utcnow()
                entry.result_status = result_status
                if notes:
                    entry.notes = notes
                db.commit()
        except Exception as e:
            log.error(f"close_intent_log failed: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def create_task(
        task_id: str,
        name: str,
        module: str,
        action: str,
        status: str = "pending",
    ) -> None:
        """Insert or update task row."""
        db = get_session("vx11")
        try:
            task = Task(
                uuid=task_id,
                name=name,
                module=module,
                action=action,
                status=status,
            )
            db.add(task)
            db.commit()
        except Exception as e:
            log.error(f"create_task failed: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def update_task(
        task_id: str,
        status: Optional[str] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task row."""
        db = get_session("vx11")
        try:
            task = db.query(Task).filter_by(uuid=task_id).first()
            if task:
                if status:
                    task.status = status
                if result:
                    task.result = result
                if error:
                    task.error = error
                task.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            log.error(f"update_task failed: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def set_context(
        task_id: str,
        key: str,
        value: Any,
        scope: str = "global",
    ) -> None:
        """Set context key-value pair."""
        db = get_session("vx11")
        try:
            entry = Context(
                task_id=task_id,
                key=key,
                value=json.dumps(value) if not isinstance(value, str) else value,
                scope=scope,
            )
            db.add(entry)
            db.commit()
        except Exception as e:
            log.error(f"set_context failed: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def get_context(task_id: str, key: str) -> Optional[str]:
        """Retrieve context value."""
        db = get_session("vx11")
        try:
            entry = db.query(Context).filter_by(task_id=task_id, key=key).first()
            return entry.value if entry else None
        finally:
            db.close()

    @staticmethod
    def record_action(
        module: str,
        action: str,
        reason: Optional[str] = None,
    ) -> int:
        """Record an action in madre_actions."""
        db = get_session("vx11")
        try:
            entry = MadreAction(
                module=module,
                action=action,
                reason=reason or "",
            )
            db.add(entry)
            db.commit()
            return entry.id
        except Exception as e:
            log.error(f"record_action failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def request_spawner_task(
        intent_id: str,
        task_type: str,
        description: str,
        metadata: Dict[str, Any],
        plan_json: Dict[str, Any],
        priority: int = 3,
    ) -> int:
        """Insert daughter_tasks request. Returns daughter_task ID."""
        db = get_session("vx11")
        try:
            entry = DaughterTask(
                intent_id=intent_id,
                source="madre",
                priority=priority,
                status="pending",
                task_type=task_type,
                description=description,
                metadata_json=json.dumps(metadata),
                plan_json=json.dumps(plan_json),
            )
            db.add(entry)
            db.commit()
            return entry.id
        except Exception as e:
            log.error(f"request_spawner_task failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def get_policy(module: str) -> Optional[Dict[str, Any]]:
        """Retrieve policy for module."""
        db = get_session("vx11")
        try:
            entry = db.query(MadrePolicy).filter_by(module=module).first()
            if entry:
                return {
                    "error_threshold": entry.error_threshold,
                    "idle_seconds": entry.idle_seconds,
                    "enable_autosuspend": entry.enable_autosuspend,
                }
            return None
        finally:
            db.close()

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task."""
        db = get_session("vx11")
        try:
            task = db.query(Task).filter_by(uuid=task_id).first()
            if task:
                return {
                    "uuid": task.uuid,
                    "name": task.name,
                    "module": task.module,
                    "action": task.action,
                    "status": task.status,
                    "result": task.result,
                    "error": task.error,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
            return None
        finally:
            db.close()
