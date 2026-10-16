
from typing import Literal

from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    name: str
    status: Literal["success", "failed"]
    duration_ms: float = Field(ge=0)
    error: str | None = None


class TraceCreate(BaseModel):
    trace_id: str
    question: str
    status: Literal["success", "failed"]
    steps: list[TraceStep]
    latency_ms: float = Field(ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    model: str = "simulated-model"
