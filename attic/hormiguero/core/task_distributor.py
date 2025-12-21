import time
import asyncio
from config.db_schema import get_session
from config.models import QueenTask, Ant
from hormiguero.core.queen import Queen
from config.settings import settings

async def process_task(task_db_id: int, timeout: int = 30):
    """Process a task: simulation that respects priority and reports results to Queen learner."""
    db = get_session("hormiguero")
    queen = Queen()
    start = time.time()
    try:
        task = db.query(QueenTask).filter(QueenTask.id == task_db_id).first()
        if not task:
            return

        # Mark task as running
        task.status = "running"
        db.commit()

        # Process ants
        ants = db.query(Ant).filter(Ant.task_id == task.id).all()
        for ant in ants:
            ant.status = "running"
            db.commit()

            # simulate work with priority: higher priority -> shorter per-ant sleep
            per_ant = 0.15
            try:
                priority = int(task.priority or 1)
            except Exception:
                priority = 1

            # low-resource mode increases sleep (slower)
            if getattr(settings, "reaper_enabled", False):
                per_ant = per_ant * 1.5

            per_ant = max(0.02, per_ant / max(1, priority))
            await asyncio.sleep(per_ant)

            ant.status = "completed"
            ant.result = {"ok": True}
            db.commit()

        # finalize task
        task.status = "completed"
        task.result = {"ants_processed": len(ants)}
        db.commit()

        # report learning
        elapsed = time.time() - start
        try:
            queen.learn_from_result(task.task_type, elapsed, True)
        except Exception:
            pass

    finally:
        db.close()
