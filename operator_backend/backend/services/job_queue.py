import asyncio
import uuid
from typing import Dict, Optional, Any
from pydantic import BaseModel


class JobStatus(BaseModel):
    job_id: str
    intent: str
    payload: Dict[str, Any]
    context: Dict[str, Any]
    status: str = "queued"


class JobQueue:
    """In-memory lightweight queue for operator intents."""

    def __init__(self):
        self._jobs: Dict[str, JobStatus] = {}
        self._lock = asyncio.Lock()

    def size(self) -> int:
        return len(self._jobs)

    def enqueue(self, intent: str, payload: Dict[str, Any], context: Dict[str, Any]) -> JobStatus:
        job_id = str(uuid.uuid4())
        job = JobStatus(job_id=job_id, intent=intent, payload=payload, context=context)
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[JobStatus]:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None
