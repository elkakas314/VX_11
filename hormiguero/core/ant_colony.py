from typing import Dict, Any
from config.models import Ant
from config.settings import settings
import asyncio


class AntColony:
    def __init__(self):
        self.ants = {}

    async def create_ants_for_task(self, task_id: int, task_type: str, payload: Dict[str, Any], db) -> int:
        """Crear ants proporcional a la prioridad y payload.

        Si el sistema está en modo bajo consumo, crear menos ants.
        """
        # prioridad heurística: más payload => más ants
        base = 1
        if payload:
            base += min(3, len(payload))

        # permitir que caller haya calculado prioridad y lo pase en payload.__priority
        priority_hint = 0
        if isinstance(payload, dict) and "__priority" in payload:
            priority_hint = int(payload.get("__priority", 0))

        ants_to_create = base + (priority_hint // 3)

        # low-resource mode reduces ants
        if getattr(settings, "reaper_enabled", False):
            ants_to_create = max(1, ants_to_create // 2)

        created = 0
        for i in range(ants_to_create):
            a = Ant(task_id=task_id, ant_type=f"worker_{i}", status="pending", payload=payload or {})
            db.add(a)
            created += 1
        db.commit()
        return created

    def scale(self, target_count: int):
        """Escala dict de ants en memoria para métricas/control."""
        current = len(self.ants)
        if target_count > current:
            for i in range(target_count - current):
                name = f"ant-{int(__import__('time').time() * 1000)}-{i}"
                self.ants[name] = {"name": name, "role": "worker", "status": "active"}
        elif target_count < current:
            to_remove = list(self.ants.keys())[target_count:]
            for name in to_remove:
                self.ants.pop(name, None)

    async def get_total_ants_count(self, db) -> int:
        return db.query(Ant).count()

    async def calculate_efficiency(self, db) -> float:
        total = db.query(Ant).count()
        completed = db.query(Ant).filter(Ant.status == "completed").count()
        if total == 0:
            return 0.0
        return completed / total

    async def optimize_colony(self, opts: Dict[str, Any], db) -> Dict[str, Any]:
        # placeholder optimizer (fast)
        await asyncio.sleep(0.01)
        return {"optimized": True, "opts": opts}
