"""Pydantic schemas for Shub-Niggurath API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    audio: List[float] = Field(default_factory=list)
    sample_rate: int = 48000
    metadata: Optional[Dict[str, Any]] = None


class MixRequest(BaseModel):
    stems: Dict[str, List[float]]
    metadata: Optional[Dict[str, Any]] = None


class EventReadyRequest(BaseModel):
    payload: Optional[Dict[str, Any]] = None
