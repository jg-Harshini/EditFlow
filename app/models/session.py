from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from app.models.timeline import Timeline


class ClarificationOption(BaseModel):
    id: str
    label: str
    description: Optional[str] = None
    target_data: Optional[Dict[str, Any]] = None


class StepResult(BaseModel):
    status: Literal["applied", "needs_clarification", "rejected"]
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    question: Optional[str] = None
    options: Optional[List[str]] = None
    timeline_hash: str = ""
    duration_s: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    video_url: Optional[str] = None


class StepInstruction(BaseModel):
    say: str
    answer: Optional[str] = None


class SessionScript(BaseModel):
    video: str
    steps: List[StepInstruction]


class PendingClarification(BaseModel):
    original_instruction: str
    question: str
    options: List[str]
    intent: str
    matched_candidates: List[Dict[str, Any]]


class SessionState(BaseModel):
    session_id: str
    video_uri: str
    timeline: Timeline
    history: List[Timeline] = Field(default_factory=list)
    redo_history: List[Timeline] = Field(default_factory=list)
    history_descriptions: List[str] = Field(default_factory=list)
    step_results: List[StepResult] = Field(default_factory=list)
    pending_clarification: Optional[PendingClarification] = None
