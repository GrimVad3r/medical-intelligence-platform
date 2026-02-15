"""Pydantic request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)


class AnalyzeTextResponse(BaseModel):
    entities: dict[str, Any] = Field(default_factory=dict)
    category: str | None = None
    confidence: float | None = None
    linked_entities: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    database: str | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str | None = None


class TrendPoint(BaseModel):
    date: str
    value: float
