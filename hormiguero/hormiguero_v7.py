"""
Hormiguero v7.0 - Queen + Ants Subsystem
Autoridad centralizada (Queen) que emite feromonas basadas en reportes de hormigas.
Las hormigas NUNCA generan feromonas; solo reportan incidencias.
"""

import asyncio
import json
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

import httpx
from sqlalchemy import and_

from config.settings import settings
from config.tokens import get_token, load_tokens
from config.forensics import write_log
from config.db_schema import get_session, HormigaState, Incident, PheromoneLog

load_tokens()

AUTH_HEADERS = {
    settings.token_header: (
        get_token("VX11_TENTACULO_LINK_TOKEN")
        or get_token("VX11_GATEWAY_TOKEN")
        or settings.api_token
    )
}

PRIORITY_MAP = {
    "shub": 0,
    "operator": 1,
    "madre": 2,
    "hijas": 3,
}


class AntRole(str, Enum):
    """Tipos de hormigas especializadas."""
    SCANNER_DRIFT = "scanner_drift"
    SCANNER_MEMORY = "scanner_memory"
    SCANNER_IMPORTS = "scanner_imports"
    SCANNER_LOGS = "scanner_logs"
    SCANNER_DB = "scanner_db"
    SCANNER_MODULES = "scanner_modules"
    SCANNER_PROCESSES = "scanner_processes"
    SCANNER_PORTS = "scanner_ports"


class SeverityLevel(str, Enum):
    """Niveles de severidad de incidencias."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    """Tipos de incidencias detectadas."""
    DRIFT = "drift"
    MEMORY_LEAK = "memory_leak"
    BROKEN_IMPORT = "broken_import"
    ORPHAN_LOG = "orphan_log"
    ORPHAN_DB = "orphan_db"
    ORPHAN_MODULE = "orphan_module"
    ZOMBIE_PROCESS = "zombie_process"
    BLOCKED_PORT = "blocked_port"


class PheromoneType(str, Enum):
    """Tipos de feromonas emitidas por Reina."""
    ALERT = "alert"
    TASK = "task"
    CLEANUP = "cleanup"
    OPTIMIZE = "optimize"
    INVESTIGATE = "investigate"


# ============ ANT (Hormiga) ============

class Ant:
    """
    Hormiga especializada: solo escanea y reporta.
    NUNCA emite feromonas.
    NUNCA toma acciones.
    """

    def __init__(self, ant_id: str, role: AntRole):
        self.ant_id = ant_id
        self.role = role
        self.last_scan: Optional[datetime] = None
        self.mutation_level = 0

    async def scan(self) -> List[Dict[str, Any]]:
        """Ejecuta escaneo especializado según rol."""
        try:
            if self.role == AntRole.SCANNER_DRIFT:
                return await self._scan_drift()
            elif self.role == AntRole.SCANNER_MEMORY:
                return await self._scan_memory()
            elif self.role == AntRole.SCANNER_IMPORTS:
                return await self._scan_imports()
            elif self.role == AntRole.SCANNER_LOGS:
                return await self._scan_logs()
            elif self.role == AntRole.SCANNER_DB:
                return await self._scan_db()
            elif self.role == AntRole.SCANNER_MODULES:
                return await self._scan_modules()
            elif self.role == AntRole.SCANNER_PROCESSES:
                return await self._scan_processes()
            elif self.role == AntRole.SCANNER_PORTS:
                return await self._scan_ports()
        except Exception as exc:
            write_log("hormiguero", f"ant_scan_error:{self.ant_id}:{exc}", level="ERROR")
        return []

    async def _scan_drift(self) -> List[Dict[str, Any]]:
        """Detecta cambios en archivos .py (drift estructural)."""
        # Stub: validación básica de sintaxis
        import py_compile
        issues = []
        for root, dirs, files in __import__("os").walk("/app"):
            for f in files:
                if f.endswith(".py"):
                    try:
                        py_compile.compile(f"{root}/{f}", doraise=True)
                    except py_compile.PyCompileError as e:
                        issues.append({
                            "type": IncidentType.DRIFT,
                            "location": f"{root}/{f}",
                            "details": str(e),
                            "severity": SeverityLevel.ERROR,
                        })
        return issues

    async def _scan_memory(self) -> List[Dict[str, Any]]:
        """Detecta fugas de memoria."""
        issues = []
        ram_percent = psutil.virtual_memory().percent
        if ram_percent > 85:
            issues.append({
                "type": IncidentType.MEMORY_LEAK,
                "location": "system",
                "details": f"RAM usage: {ram_percent}%",
                "severity": SeverityLevel.WARNING if ram_percent < 95 else SeverityLevel.CRITICAL,
            })
        return issues

    async def _scan_imports(self) -> List[Dict[str, Any]]:
        """Detecta imports rotos."""
        # Stub: análisis básico
        issues = []
        try:
            import ast
            import os
            for root, dirs, files in os.walk("/app"):
                for f in files:
                    if f.endswith(".py"):
                        try:
                            with open(f"{root}/{f}", "r") as fh:
                                ast.parse(fh.read())
                        except SyntaxError as e:
                            issues.append({
                                "type": IncidentType.BROKEN_IMPORT,
                                "location": f"{root}/{f}",
                                "details": str(e),
                                "severity": SeverityLevel.ERROR,
                            })
        except Exception:
            pass
        return issues

    async def _scan_logs(self) -> List[Dict[str, Any]]:
        """Detecta logs fuera de /logs."""
        import os
        issues = []
        disallowed_dirs = ["/app", "/root", "/home"]
        for dirpath in disallowed_dirs:
            if os.path.exists(dirpath):
                for root, dirs, files in os.walk(dirpath):
                    for f in files:
                        if "log" in f.lower() and not root.startswith("/app/logs"):
                            issues.append({
                                "type": IncidentType.ORPHAN_LOG,
                                "location": f"{root}/{f}",
                                "details": f"Log file outside /logs",
                                "severity": SeverityLevel.WARNING,
                            })
        return issues

    async def _scan_db(self) -> List[Dict[str, Any]]:
        """Detecta DBs fuera de /data."""
        import os
        issues = []
        disallowed_patterns = ["*.db", "*.sqlite", "*.sqlite3"]
        for root, dirs, files in os.walk("/app"):
            if "/data" not in root:
                for f in files:
                    if any(f.endswith(p.replace("*", "")) for p in disallowed_patterns):
                        issues.append({
                            "type": IncidentType.ORPHAN_DB,
                            "location": f"{root}/{f}",
                            "details": f"Database file outside /data",
                            "severity": SeverityLevel.ERROR,
                        })
        return issues

    async def _scan_modules(self) -> List[Dict[str, Any]]:
        """Detecta módulos fuera de sitio."""
        import os
        issues = []
        expected_modules = [
            "/app/madre", "/app/spawner", "/app/switch", "/app/hermes",
            "/app/hormiguero", "/app/mcp", "/app/shubniggurath", "/app/operator",
            "/app/tentaculo_link", "/app/manifestator"
        ]
        for root, dirs, files in os.walk("/app"):
            if any(expected in root for expected in expected_modules):
                continue
            for f in files:
                if f == "main.py":
                    issues.append({
                        "type": IncidentType.ORPHAN_MODULE,
                        "location": f"{root}/{f}",
                        "details": f"Unexpected module directory",
                        "severity": SeverityLevel.WARNING,
                    })
        return issues

    async def _scan_processes(self) -> List[Dict[str, Any]]:
        """Detecta procesos zombis."""
        import os
        issues = []
        try:
            import psutil as ps
            for proc in ps.process_iter(["pid", "status"]):
                try:
                    if proc.info["status"] == ps.STATUS_ZOMBIE:
                        issues.append({
                            "type": IncidentType.ZOMBIE_PROCESS,
                            "location": f"PID {proc.info['pid']}",
                            "details": "Zombie process detected",
                            "severity": SeverityLevel.WARNING,
                        })
                except (ps.NoSuchProcess, ps.AccessDenied):
                    pass
        except Exception:
            pass
        return issues

    async def _scan_ports(self) -> List[Dict[str, Any]]:
        """Detecta puertos bloqueados."""
        import socket
        issues = []
        key_ports = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008]
        for port in key_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(("127.0.0.1", port))
                sock.close()
                if result != 0:
                    issues.append({
                        "type": IncidentType.BLOCKED_PORT,
                        "location": f"127.0.0.1:{port}",
                        "details": f"Port {port} not responding",
                        "severity": SeverityLevel.WARNING,
                    })
            except Exception:
                pass
        return issues

    async def report_to_queen(self, incidents: List[Dict[str, Any]]) -> None:
        """Reporta incidencias a Reina (persiste en DB, sin feromonas)."""
        session = get_session("vx11")
        try:
            for inc in incidents:
                incident = Incident(
                    ant_id=self.ant_id,
                    incident_type=inc.get("type"),
                    severity=inc.get("severity", SeverityLevel.INFO),
                    location=inc.get("location"),
                    details=json.dumps(inc.get("details", {})),
                    status="open",
                )
                session.add(incident)
            session.commit()
            write_log("hormiguero", f"ant_reported:{self.ant_id}:{len(incidents)}_incidents")
        finally:
            session.close()

    async def update_state(self) -> None:
        """Actualiza estado en BD."""
        session = get_session("vx11")
        try:
            state = session.query(HormigaState).filter_by(ant_id=self.ant_id).first()
            if not state:
                state = HormigaState(ant_id=self.ant_id, role=self.role.value)
            state.status = "idle"
            state.last_scan_at = datetime.utcnow()
            state.cpu_percent = psutil.cpu_percent()
            state.ram_percent = psutil.virtual_memory().percent
            state.mutation_level = self.mutation_level
            session.add(state)
            session.commit()
        finally:
            session.close()


# ============ QUEEN (Reina) ============

class Queen:
    """
    Reina del Hormiguero: analiza reportes de hormigas y decide acciones.
    SOLO la Reina emite feromonas (tras consultar Switch).
    """

    def __init__(self):
        self.ants: Dict[str, Ant] = {
            role.value: Ant(f"ant_{role.value}", role)
            for role in AntRole
        }

    async def process_incidents(self) -> Dict[str, Any]:
        """
        Procesa incidencias abiertas y decide acción:
        A) direct_action: Reina ejecuta acción inmediata
        B) spawn_hija: Madre crea hijas efímeras
        C) switch_strategy: Switch proporciona estrategia
        """
        session = get_session("vx11")
        try:
            open_incidents = session.query(Incident).filter_by(status="open").all()
            decisions = []

            for incident in open_incidents:
                decision = await self._classify_and_decide(incident)
                decisions.append(decision)
                
                # Marcar incidencia como reconocida (acknowledged)
                incident.status = "acknowledged"
                incident.queen_decision = decision["route"]
                session.add(incident)

            session.commit()
            
            # Ahora ejecutar decisiones
            for decision in decisions:
                await self._execute_decision(decision)

            write_log("hormiguero", f"queen_processed:{len(open_incidents)}_incidents")
            return {"processed": len(open_incidents), "decisions": decisions}
        finally:
            session.close()

    async def _classify_and_decide(self, incident: Incident) -> Dict[str, Any]:
        """Clasifica incidencia y elige ruta de acción."""
        incident_type = incident.incident_type
        severity = incident.severity

        # Decisiones basadas en tipo/severidad
        if severity == SeverityLevel.CRITICAL:
            return {
                "incident_id": incident.id,
                "route": "spawn_hija",
                "reason": "Critical severity requires immediate ephemeral action",
                "mother_intent": {
                    "source": "hormiguero",
                    "intent_type": f"fix_{incident_type}",
                    "payload": {
                        "incident_id": incident.id,
                        "type": incident_type,
                        "location": incident.location,
                    },
                    "ttl_seconds": 120,
                }
            }
        elif severity == SeverityLevel.ERROR:
            return {
                "incident_id": incident.id,
                "route": "switch_strategy",
                "reason": "Error severity requires strategy consultation",
                "switch_request": {
                    "task_type": "incident_resolution",
                    "payload": {
                        "incident_type": incident_type,
                        "location": incident.location,
                        "severity": severity,
                    }
                }
            }
        else:
            return {
                "incident_id": incident.id,
                "route": "direct_action",
                "reason": f"{severity} severity: direct cleanup action",
                "action": f"cleanup_{incident_type}",
            }

    async def _execute_decision(self, decision: Dict[str, Any]) -> None:
        """Ejecuta decisión (crea feromona y toma acción)."""
        route = decision["route"]
        incident_id = decision["incident_id"]

        # CONSULTAR SWITCH ANTES DE CUALQUIER FEROMONA
        switch_ok = await self._consult_switch_for_approval(decision)
        if not switch_ok:
            write_log("hormiguero", f"queen_decision_vetoed_by_switch:{incident_id}")
            return

        # Emitir feromona (SOLO tras Switch approval)
        pheromone = PheromoneLog(
            pheromone_type=PheromoneType.ALERT if route == "spawn_hija" else PheromoneType.TASK,
            intensity=3 if decision.get("reason") and "Critical" in decision["reason"] else 1,
            source_incident_ids=json.dumps([incident_id]),
            payload=json.dumps(decision),
        )

        session = get_session("vx11")
        try:
            session.add(pheromone)
            session.commit()
        finally:
            session.close()

        # Ejecutar acción según ruta
        if route == "spawn_hija":
            await self._dispatch_to_madre(decision)
        elif route == "switch_strategy":
            await self._consult_switch_for_strategy(decision)
        elif route == "direct_action":
            await self._execute_direct_action(decision)

    async def _consult_switch_for_approval(self, decision: Dict[str, Any]) -> bool:
        """Consulta Switch para obtener aprobación antes de actuar."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{settings.switch_url.rstrip('/')}/switch/task",
                    json={
                        "task_type": "approval",
                        "payload": decision,
                        "source": "hormiguero",
                    },
                    headers=AUTH_HEADERS,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    approved = result.get("approved", True)
                    write_log("hormiguero", f"switch_approval:{approved}")
                    return approved
        except Exception as exc:
            write_log("hormiguero", f"switch_approval_error:{exc}", level="WARNING")
        return True  # Falto de Switch, proceder conservadoramente

    async def _consult_switch_for_strategy(self, decision: Dict[str, Any]) -> None:
        """Consulta Switch para obtener estrategia."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{settings.switch_url.rstrip('/')}/switch/task",
                    json={
                        "task_type": "strategy",
                        "payload": decision.get("switch_request", {}),
                        "source": "hormiguero",
                    },
                    headers=AUTH_HEADERS,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    write_log("hormiguero", f"switch_strategy_obtained:{result.get('provider')}")
        except Exception as exc:
            write_log("hormiguero", f"switch_strategy_error:{exc}", level="WARNING")

    async def _dispatch_to_madre(self, decision: Dict[str, Any]) -> None:
        """Envía INTENT a Madre para crear hijas."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{settings.madre_url.rstrip('/')}/madre/intent",
                    json=decision.get("mother_intent", {}),
                    headers=AUTH_HEADERS,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    write_log("hormiguero", f"madre_intent_dispatched:{result.get('daughter_task_id')}")
        except Exception as exc:
            write_log("hormiguero", f"madre_dispatch_error:{exc}", level="WARNING")

    async def _execute_direct_action(self, decision: Dict[str, Any]) -> None:
        """Ejecuta acción directa (cleanup, etc)."""
        action = decision.get("action", "unknown")
        # Stub: acciones específicas según tipo
        write_log("hormiguero", f"direct_action_executed:{action}")


# ============ COLONY ORCHESTRATOR ============

class AntColony:
    """Orquestador del Hormiguero: gestiona hormigas y Reina."""

    def __init__(self):
        self.queen = Queen()
        self.ants = self.queen.ants

    async def scan_cycle(self) -> Dict[str, Any]:
        """Ciclo de escaneo: hormigas reportan, Reina decide."""
        all_incidents = []

        # Fase 1: Hormigas escanean
        for ant_id, ant in self.ants.items():
            incidents = await ant.scan()
            all_incidents.extend(incidents)
            await ant.report_to_queen(incidents)
            await ant.update_state()

        # Fase 2: Reina procesa
        queen_result = await self.queen.process_incidents()

        write_log("hormiguero", f"scan_cycle_completed:{len(all_incidents)}_total_incidents")
        return {
            "total_incidents": len(all_incidents),
            "queen_decisions": queen_result.get("decisions", []),
        }
