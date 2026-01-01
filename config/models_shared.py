from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class SpawnCallbackRequest(BaseModel):
    correlation_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)  # DONE|ERROR|...
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SpawnCallbackResponse(BaseModel):
    ok: bool = True
    correlation_id: str
