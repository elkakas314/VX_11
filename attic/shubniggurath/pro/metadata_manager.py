"""
Gestión de metadata técnica e histórico.
"""
from datetime import datetime
from typing import Dict
from .project_db import History, get_session


def save_metadata(project_id: int, payload: Dict):
    session = get_session()
    try:
        h = History(project_id=project_id, event="metadata", payload=str(payload))
        session.add(h)
        session.commit()
        return h.id
    finally:
        session.close()


def log_event(project_id: int, event: str, payload: Dict):
    session = get_session()
    try:
        h = History(project_id=project_id, event=event, payload=str(payload), created_at=datetime.utcnow())
        session.add(h)
        session.commit()
        return h.id
    finally:
        session.close()
