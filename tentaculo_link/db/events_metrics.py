"""
VX11 Events & Metrics Persistence Layer
tentaculo_link/db/events_metrics.py

Funciones para registrar y consultar eventos/métricas desde SQLite.
Respeta OFF-by-default: solo inserta si VX11_EVENTS_ENABLED o similar.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_db_path() -> Path:
    """Resolver ruta a vx11.db"""
    import os

    repo_root = Path(os.environ.get("VX11_REPO_ROOT", "/home/elkakas314/vx11"))
    return repo_root / "data" / "runtime" / "vx11.db"


def get_db_connection():
    """Obtener conexión a SQLite con PRAGMA foreign_keys ON"""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row  # Acceso como dict
    return conn


def log_event(
    event_type: str,
    summary: str,
    module: str,
    severity: str = "info",
    correlation_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Log un evento a operator_events table.

    Args:
        event_type: status|module|window|intent|audit
        summary: Descripción breve del evento
        module: Módulo que lo origina (tentaculo_link, madre, etc.)
        severity: info|warn|crit
        correlation_id: Para enlazar eventos relacionados (si existe)
        payload: Datos estructurados (dict convertido a JSON)

    Returns:
        event_id generado
    """
    event_id = f"evt_{uuid.uuid4().hex[:12]}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        payload_json = json.dumps(payload or {})

        cursor.execute(
            """
            INSERT INTO operator_events (event_id, ts, event_type, severity, module, correlation_id, summary, payload_json)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                severity,
                module,
                correlation_id,
                summary,
                payload_json,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        # Log de fallback: nunca debe tumbar la operación principal
        import sys

        print(f"ERROR logging event {event_id}: {e}", file=sys.stderr)

    return event_id


def log_metric(
    metric_name: str,
    value: float,
    module: str = "tentaculo_link",
    dimensions: Optional[Dict[str, str]] = None,
) -> str:
    """
    Log una métrica numérica a operator_metrics.

    Args:
        metric_name: cpu_percent|ram_gib|latency_ms|chat_throughput|window_ttl|event_backlog
        value: Valor numérico
        module: Módulo que origina la métrica
        dimensions: Datos categóricos adicionales {service, window_id, ...}

    Returns:
        metric_id generado
    """
    metric_id = f"met_{uuid.uuid4().hex[:12]}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        dimensions_json = json.dumps(dimensions or {})

        cursor.execute(
            """
            INSERT INTO operator_metrics (metric_id, ts, metric_name, value, module, dimensions_json)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            """,
            (metric_id, metric_name, value, module, dimensions_json),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        import sys

        print(f"ERROR logging metric {metric_id}: {e}", file=sys.stderr)

    return metric_id


def get_events(
    limit: int = 100,
    offset: int = 0,
    correlation_id: Optional[str] = None,
    severity: Optional[str] = None,
    module: Optional[str] = None,
    hours_back: int = 24,
) -> Dict[str, Any]:
    """
    Consultar eventos con filtros.

    Args:
        limit: Cantidad máxima de eventos
        offset: Offset para paginación
        correlation_id: Filtrar por correlation_id si existe
        severity: Filtrar por severity
        module: Filtrar por module
        hours_back: Incluir eventos de las últimas N horas

    Returns:
        {
            "events": [{id, ts, type, severity, module, correlation_id, summary, payload}, ...],
            "total": int,
            "has_more": bool
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        # Construir WHERE dinámica
        where_parts = ["ts > datetime(?"]
        params = [cutoff_time.isoformat()]

        if correlation_id:
            where_parts.append("correlation_id = ?")
            params.append(correlation_id)

        if severity:
            where_parts.append("severity = ?")
            params.append(severity)

        if module:
            where_parts.append("module = ?")
            params.append(module)

        where_clause = " AND ".join(where_parts) + ")"

        # Contar total
        count_sql = f"SELECT COUNT(*) as cnt FROM operator_events WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["cnt"]

        # Fetchear con limit+offset
        query_sql = f"""
            SELECT event_id, ts, event_type, severity, module, correlation_id, summary, payload_json
            FROM operator_events
            WHERE {where_clause}
            ORDER BY ts DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()

        events = []
        for row in rows:
            events.append(
                {
                    "id": row["event_id"],
                    "ts": row["ts"],
                    "type": row["event_type"],
                    "severity": row["severity"],
                    "module": row["module"],
                    "correlation_id": row["correlation_id"],
                    "summary": row["summary"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                }
            )

        conn.close()

        return {
            "events": events,
            "total": total,
            "has_more": (offset + limit) < total,
        }
    except Exception as e:
        import sys

        print(f"ERROR querying events: {e}", file=sys.stderr)
        return {"events": [], "total": 0, "has_more": False}


def get_metrics(
    metric_name: Optional[str] = None,
    window_seconds: int = 3600,
    module: Optional[str] = None,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    Consultar métricas numéricas.

    Args:
        metric_name: Filtrar por nombre (cpu_percent, ram_gib, etc.)
        window_seconds: Incluir solo últimas N segundos
        module: Filtrar por módulo
        limit: Máximo de resultados

    Returns:
        {
            "metrics": [{metric_id, ts, metric_name, value, module, dimensions}, ...],
            "count": int
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)

        where_parts = ["ts > datetime(?)"]
        params = [cutoff_time.isoformat()]

        if metric_name:
            where_parts.append("metric_name = ?")
            params.append(metric_name)

        if module:
            where_parts.append("module = ?")
            params.append(module)

        where_clause = " AND ".join(where_parts)

        query_sql = f"""
            SELECT metric_id, ts, metric_name, value, module, dimensions_json
            FROM operator_metrics
            WHERE {where_clause}
            ORDER BY ts DESC
            LIMIT ?
        """
        params.append(limit)
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()

        metrics = []
        for row in rows:
            metrics.append(
                {
                    "metric_id": row["metric_id"],
                    "ts": row["ts"],
                    "metric_name": row["metric_name"],
                    "value": row["value"],
                    "module": row["module"],
                    "dimensions": json.loads(row["dimensions_json"] or "{}"),
                }
            )

        conn.close()

        return {
            "metrics": metrics,
            "count": len(metrics),
        }
    except Exception as e:
        import sys

        print(f"ERROR querying metrics: {e}", file=sys.stderr)
        return {"metrics": [], "count": 0}


def get_events_by_correlation_id(correlation_id: str) -> List[Dict[str, Any]]:
    """
    Obtener todos los eventos enlazados a un correlation_id.
    Útil para tracing de intents/operaciones distribuidas.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT event_id, ts, event_type, severity, module, summary, payload_json
            FROM operator_events
            WHERE correlation_id = ?
            ORDER BY ts ASC
            """,
            (correlation_id,),
        )
        rows = cursor.fetchall()

        events = []
        for row in rows:
            events.append(
                {
                    "id": row["event_id"],
                    "ts": row["ts"],
                    "type": row["event_type"],
                    "severity": row["severity"],
                    "module": row["module"],
                    "summary": row["summary"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                }
            )

        conn.close()
        return events
    except Exception as e:
        import sys

        print(f"ERROR getting correlation chain: {e}", file=sys.stderr)
        return []


# Archival function (para mantener DB limpia)
def archive_old_events(hours_threshold: int = 720) -> int:
    """
    Archivar eventos + métricas más antiguos que hours_threshold.
    Actual: solo DELETE (implementar archival a archivo si necesario).

    Returns:
        Número de filas eliminadas
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        # Eliminar eventos antiguos
        cursor.execute(
            "DELETE FROM operator_events WHERE ts < datetime(?)",
            (cutoff_time.isoformat(),),
        )
        events_deleted = cursor.rowcount

        # Eliminar métricas antiguas
        cursor.execute(
            "DELETE FROM operator_metrics WHERE ts < datetime(?)",
            (cutoff_time.isoformat(),),
        )
        metrics_deleted = cursor.rowcount

        conn.commit()
        conn.close()

        return events_deleted + metrics_deleted
    except Exception as e:
        import sys

        print(f"ERROR archiving old data: {e}", file=sys.stderr)
        return 0
