"""NLP analysis endpoints."""

from typing import Any

from fastapi import APIRouter, Query

from src.api.schemas import AnalyzeTextRequest, AnalyzeTextResponse
from src.nlp.message_processor import MessageProcessor
from src.nlp.model_manager import ModelManager

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeTextResponse)
def analyze_text(body: AnalyzeTextRequest):
    manager = ModelManager()
    processor = MessageProcessor(model_manager=manager)
    result = processor.process(body.text, include_explanations=False)
    return AnalyzeTextResponse(
        entities=result.get("entities", {}),
        category=result.get("category"),
        confidence=result.get("confidence"),
        linked_entities=result.get("linked_entities", {}),
    )


@router.get("/insights")
def nlp_insights(since: str | None = None, limit: int = Query(100, le=500)):
    from src.database.connection import get_session_factory
    from src.database.models import NLPResult
    from sqlalchemy import select, func
    from src.transformation.aggregator import aggregate_entities

    factory = get_session_factory()
    with factory() as session:
        stmt = select(NLPResult).limit(limit)
        rows = session.scalars(stmt).all()
    results = [{"entities": r.entities, "category": r.category} for r in rows]
    agg = aggregate_entities(results)
    return {"entity_counts": agg, "total": len(results)}
