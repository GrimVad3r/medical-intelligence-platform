"""Common database queries."""

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Message, NLPResult, YOLOResult


def get_unprocessed_messages(session: Session, limit: int = 100) -> List[Message]:
    """Return messages not yet processed by NLP."""
    stmt = select(Message).where(Message.processed_nlp == 0).limit(limit)
    return list(session.scalars(stmt).all())


def save_yolo_results(session: Session, results: dict) -> int:
    """Persist YOLO results. Expects results with keys like 'results' (list of per-image dicts)."""
    from src.database.models import YOLOResult

    rows = results.get("results", results) if isinstance(results, dict) else results
    if not isinstance(rows, list):
        rows = [{"image_path": str(results), "detections": []}]
    count = 0
    for item in rows:
        if isinstance(item, dict):
            rec = YOLOResult(
                image_path=item.get("image_path", ""),
                detections=item.get("detections", []),
                model_version=item.get("model_version"),
            )
            session.add(rec)
            count += 1
    session.commit()
    return count
