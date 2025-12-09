from typing import Dict, Any
from config.models import QueenTask


class Queen:
    def __init__(self):
        """
        Queen heuristics for hormiguero.
        """
        from typing import Dict, Any
        import json
        import os
        from config.models import QueenTask
        from config.settings import settings


        class Queen:
            """Heurística central de la Reina.

            - Estima tiempo base por tipo/payload
            - Calcula prioridad adaptativa usando micro-aprendizaje local
            - Ajusta comportamiento en modo bajo consumo
            """

            def __init__(self, learner_path: str = ".tmp_copilot/hormiguero/learner.json"):
                self.learner_path = learner_path
                os.makedirs(os.path.dirname(self.learner_path), exist_ok=True)
                if not os.path.exists(self.learner_path):
                    with open(self.learner_path, "w") as f:
                        json.dump({}, f)

            def _load_learner(self) -> Dict[str, Any]:
                try:
                    with open(self.learner_path, "r") as f:
                        return json.load(f)
                except Exception:
                    return {}

            def _save_learner(self, data: Dict[str, Any]):
                try:
                    with open(self.learner_path, "w") as f:
                        json.dump(data, f)
                except Exception:
                    pass

            def estimate_time(self, task_type: str, payload: Dict[str, Any]) -> float:
                """Estimate tiempo en segundos usando heurística simple + aprendido.

                Base: 1.0s per small task, más por payload complexity.
                """
                base = 1.0
                complexity = 0
                if payload:
                    # contar items y profundidad aproximada
                    complexity = sum(1 for _ in payload.keys())
                    # penalizar strings largos
                    for v in payload.values():
                        if isinstance(v, str):
                            complexity += min(3, len(v) // 100)

                learned = self._load_learner().get(task_type, {}).get("avg_time", 0)
                if learned:
                    # combinado: media ponderada
                    est = 0.6 * learned + 0.4 * (base + 0.5 * complexity)
                else:
                    est = base + 0.5 * complexity

                # modo bajo consumo: estimaciones más conservadoras
                if getattr(settings, "environment", "dev") != "prod":
                    return max(0.5, est)
                return max(0.5, est)

            def compute_priority(self, task_type: str, payload: Dict[str, Any], db) -> int:
                """Computa prioridad entre 1 (baja) y 10 (alta) según tipo, payload y carga actual."""
                score = 1
                # tipos conocidos con mayor prioridad
                high = ["urgent", "inference", "pipeline"]
                if task_type in high or "urgent" in (payload or {}):
                    score += 4

                # payload complexity aumenta prioridad
                if payload:
                    size = sum(1 for _ in payload.keys())
                    score += min(3, size)

                # penalizar si sistema ocupado
                try:
                    active = db.query(QueenTask).filter(QueenTask.status != "completed").count()
                    if active > 10:
                        score = max(1, score - 2)
                    elif active > 3:
                        score = max(1, score - 1)
                except Exception:
                    pass

                # modo bajo consumo: reducir prioridad
                if getattr(settings, "reaper_enabled", False):
                    score = max(1, score - 2)

                return min(10, max(1, score))

            def learn_from_result(self, task_type: str, actual_time: float, success: bool):
                """Actualizar micro-aprendizaje local con tiempos observados."""
                data = self._load_learner()
                entry = data.get(task_type, {"count": 0, "avg_time": 0.0, "success_rate": 0.0})
                c = entry.get("count", 0)
                avg = entry.get("avg_time", 0.0)
                sr = entry.get("success_rate", 0.0)

                new_count = c + 1
                new_avg = (avg * c + actual_time) / new_count
                new_sr = (sr * c + (1 if success else 0)) / new_count

                data[task_type] = {"count": new_count, "avg_time": new_avg, "success_rate": new_sr}
                self._save_learner(data)

            async def get_active_tasks_count(self, db) -> int:
                try:
                    return db.query(QueenTask).filter(QueenTask.status != "completed").count()
                except Exception:
                    return 0
