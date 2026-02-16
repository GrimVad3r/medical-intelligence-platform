"""Common database queries."""

from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.database.models import Message, NLPResult, YOLOResult
from src.logger import get_logger

logger = get_logger(__name__)


def _latest_nlp_result_subquery():
    """Return subquery with latest NLPResult id per message."""
    return (
        select(
            NLPResult.message_id.label("message_id"),
            func.max(NLPResult.id).label("latest_result_id"),
        )
        .group_by(NLPResult.message_id)
        .subquery()
    )


def get_unprocessed_messages(
    session: Session,
    limit: int = 1000,
    max_retries: int = 3,
) -> list[Any]:
    """
    Get messages that haven't been NLP processed yet.

    Args:
        session: Database session
        limit: Maximum number of messages to return
        max_retries: Skip messages that have failed this many times

    Returns:
        List of Message objects
    """
    try:
        stmt = (
            select(Message)
            .where(Message.processed_nlp == 0)
            .where(
                (Message.nlp_retry_count.is_(None))
                | (Message.nlp_retry_count < max_retries)
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = session.execute(stmt).scalars().all()
        logger.info("Found %d unprocessed messages", len(messages))
        return messages

    except Exception as e:
        logger.exception("Failed to get unprocessed messages: %s", e)
        return []


def save_nlp_results(
    session: Session,
    message_id: int,
    nlp_result: dict[str, Any],
) -> bool:
    """
    Persist NLP output in nlp_results and mark message as processed.

    Args:
        session: Database session
        message_id: ID of the message
        nlp_result: NLP processing results dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        msg = session.get(Message, message_id)
        if not msg:
            logger.warning("Message %s not found", message_id)
            return False

        result_row = NLPResult(
            message_id=message_id,
            entities=nlp_result.get("entities") or {},
            category=nlp_result.get("category"),
            confidence=nlp_result.get("confidence"),
            linked_entities=nlp_result.get("linked_entities") or {},
        )
        session.add(result_row)

        msg.processed_nlp = 1
        msg.nlp_retry_count = 0
        msg.last_nlp_attempt = datetime.utcnow()

        session.commit()
        logger.debug("Saved NLP results for message %s", message_id)
        return True

    except Exception as e:
        logger.exception("Failed to save NLP results for message %s: %s", message_id, e)
        session.rollback()
        return False


def mark_nlp_error(
    session: Session,
    message_id: int,
    error_message: str,
) -> bool:
    """
    Mark a message with an NLP processing error.

    Args:
        session: Database session
        message_id: ID of the message
        error_message: Error description

    Returns:
        True if successful, False otherwise
    """
    try:
        msg = session.get(Message, message_id)
        if not msg:
            logger.warning("Message %s not found", message_id)
            return False

        msg.processed_nlp = 0
        msg.nlp_retry_count = (msg.nlp_retry_count or 0) + 1
        msg.last_nlp_attempt = datetime.utcnow()

        session.commit()
        logger.debug("Marked NLP error for message %s: %s", message_id, error_message[:200])
        return True

    except Exception as e:
        logger.exception("Failed to mark error for message %s: %s", message_id, e)
        session.rollback()
        return False


def save_yolo_results(session: Session, results: dict) -> int:
    """Persist YOLO results. Expects results with key 'results' (list of per-image dicts)."""
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


def get_messages_by_category(
    session: Session,
    category: str,
    min_confidence: float = 0.0,
    limit: int = 100,
) -> list[Any]:
    """
    Get messages classified into a specific category, based on latest NLP result.

    Args:
        session: Database session
        category: Category name
        min_confidence: Minimum confidence threshold
        limit: Maximum number of messages to return

    Returns:
        List of Message objects
    """
    try:
        latest = _latest_nlp_result_subquery()
        stmt = (
            select(Message)
            .join(latest, latest.c.message_id == Message.id)
            .join(NLPResult, NLPResult.id == latest.c.latest_result_id)
            .where(NLPResult.category == category)
            .where((NLPResult.confidence.is_(None)) | (NLPResult.confidence >= min_confidence))
            .order_by(NLPResult.confidence.desc().nullslast())
            .limit(limit)
        )
        messages = session.execute(stmt).scalars().all()
        logger.debug("Found %d messages in category '%s'", len(messages), category)
        return messages
    except Exception as e:
        logger.exception("Failed to get messages by category: %s", e)
        return []


def get_messages_with_entity(
    session: Session,
    entity_text: str,
    entity_type: str | None = None,
    limit: int = 100,
) -> list[Any]:
    """
    Get messages containing a specific entity in latest NLP result.

    Args:
        session: Database session
        entity_text: Entity text to search for
        entity_type: Optional entity type filter (DRUG, CONDITION, etc.)
        limit: Maximum number of messages to return

    Returns:
        List of Message objects
    """

    def _has_entity(entities: dict[str, Any], target: str, label: str | None) -> bool:
        if not isinstance(entities, dict):
            return False
        target_l = target.lower()
        labels = [label] if label else list(entities.keys())
        for key in labels:
            values = entities.get(key, [])
            if not isinstance(values, list):
                continue
            for item in values:
                if isinstance(item, dict) and str(item.get("text", "")).lower() == target_l:
                    return True
        return False

    try:
        latest = _latest_nlp_result_subquery()
        stmt = (
            select(Message, NLPResult.entities)
            .join(latest, latest.c.message_id == Message.id)
            .join(NLPResult, NLPResult.id == latest.c.latest_result_id)
            .limit(limit * 5)
        )
        rows = session.execute(stmt).all()

        out: list[Message] = []
        for msg, entities in rows:
            if _has_entity(entities, entity_text, entity_type):
                out.append(msg)
                if len(out) >= limit:
                    break
        logger.debug("Found %d messages with entity '%s'", len(out), entity_text)
        return out
    except Exception as e:
        logger.exception("Failed to get messages with entity: %s", e)
        return []


def get_nlp_processing_stats(session: Session) -> dict[str, Any]:
    """
    Get statistics about NLP processing.

    Args:
        session: Database session

    Returns:
        Dictionary with processing statistics
    """
    try:
        total = session.query(func.count(Message.id)).scalar() or 0
        processed = (
            session.query(func.count(Message.id))
            .where(Message.processed_nlp == 1)
            .scalar()
            or 0
        )
        errors = (
            session.query(func.count(Message.id))
            .where((Message.processed_nlp == 0) & (Message.nlp_retry_count > 0))
            .scalar()
            or 0
        )

        latest = _latest_nlp_result_subquery()
        category_dist = (
            session.query(NLPResult.category, func.count(NLPResult.id))
            .join(latest, NLPResult.id == latest.c.latest_result_id)
            .group_by(NLPResult.category)
            .all()
        )
        avg_confidence = (
            session.query(NLPResult.category, func.avg(NLPResult.confidence))
            .join(latest, NLPResult.id == latest.c.latest_result_id)
            .group_by(NLPResult.category)
            .all()
        )

        stats = {
            "total_messages": total,
            "processed_messages": processed,
            "unprocessed_messages": total - processed,
            "error_messages": errors,
            "processing_rate": processed / total if total > 0 else 0.0,
            "category_distribution": {k: v for k, v in category_dist if k is not None},
            "avg_confidence_by_category": {k: float(v) for k, v in avg_confidence if k is not None and v is not None},
        }
        logger.info(
            "NLP processing stats: %s/%s processed (%.1f%%)",
            processed,
            total,
            stats["processing_rate"] * 100,
        )
        return stats
    except Exception as e:
        logger.exception("Failed to get NLP stats: %s", e)
        return {}


def retry_failed_messages(
    session: Session,
    max_retries: int = 3,
    limit: int = 100,
) -> list[Any]:
    """
    Get messages that failed processing for retry.

    Args:
        session: Database session
        max_retries: Maximum number of retries
        limit: Maximum number of messages to return

    Returns:
        List of Message objects that can be retried
    """
    try:
        stmt = (
            select(Message)
            .where(Message.processed_nlp == 0)
            .where(Message.nlp_retry_count > 0)
            .where(Message.nlp_retry_count < max_retries)
            .order_by(Message.last_nlp_attempt.asc().nullsfirst())
            .limit(limit)
        )
        messages = session.execute(stmt).scalars().all()
        logger.info("Found %d messages to retry", len(messages))
        return messages
    except Exception as e:
        logger.exception("Failed to get messages for retry: %s", e)
        return []


def bulk_update_nlp_version(
    session: Session,
    old_version: str,
    new_version: str,
) -> int:
    """
    Retained for backward compatibility.

    NLP version is not currently stored in ORM tables, so this is a no-op.
    """
    logger.warning(
        "bulk_update_nlp_version is a no-op: no nlp_version field is currently persisted "
        "(requested %s -> %s)",
        old_version,
        new_version,
    )
    return 0


def reset_processing_status(
    session: Session,
    message_ids: list[int] | None = None,
) -> int:
    """
    Reset processing status for messages (for reprocessing) and delete NLP results.

    Args:
        session: Database session
        message_ids: Optional list of specific message IDs to reset

    Returns:
        Number of messages reset
    """
    try:
        msg_stmt = update(Message).values(
            processed_nlp=0,
            nlp_retry_count=0,
            last_nlp_attempt=None,
        )
        nlp_stmt = delete(NLPResult)

        if message_ids:
            msg_stmt = msg_stmt.where(Message.id.in_(message_ids))
            nlp_stmt = nlp_stmt.where(NLPResult.message_id.in_(message_ids))

        result = session.execute(msg_stmt)
        session.execute(nlp_stmt)
        session.commit()

        count = result.rowcount or 0
        logger.info("Reset processing status for %d messages", count)
        return count
    except Exception as e:
        logger.exception("Failed to reset processing status: %s", e)
        session.rollback()
        return 0
