"""Common database queries."""

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Message, NLPResult, YOLOResult

from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.logger import get_logger

logger = get_logger(__name__)


def get_unprocessed_messages(
    session: Session,
    limit: int = 1000,
    max_retries: int = 3
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
        from src.database.models import Message
        
        stmt = (
            select(Message)
            .where(Message.processed_nlp == 0)
            .where((Message.nlp_retry_count == None) | (Message.nlp_retry_count < max_retries))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        messages = session.execute(stmt).scalars().all()
        logger.info(f"Found {len(messages)} unprocessed messages")
        return messages
        
    except Exception as e:
        logger.exception(f"Failed to get unprocessed messages: {e}")
        return []


def save_nlp_results(
    session: Session,
    message_id: int,
    nlp_result: dict[str, Any]
) -> bool:
    """
    Save NLP processing results to database.
    
    Args:
        session: Database session
        message_id: ID of the message
        nlp_result: NLP processing results dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from src.database.models import Message
        
        msg = session.get(Message, message_id)
        if not msg:
            logger.warning(f"Message {message_id} not found")
            return False
        
        # Update message with NLP results
        msg.entities = nlp_result.get("entities")
        msg.category = nlp_result.get("category")
        msg.confidence = nlp_result.get("confidence")
        msg.linked_entities = nlp_result.get("linked_entities")
        msg.relationships = nlp_result.get("relationships")
        msg.processed_nlp = True
        msg.nlp_processed_at = datetime.utcnow()
        msg.nlp_version = nlp_result.get("metadata", {}).get("model_version")
        msg.nlp_error = None
        msg.nlp_retry_count = 0
        
        session.commit()
        logger.debug(f"Saved NLP results for message {message_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to save NLP results for message {message_id}: {e}")
        session.rollback()
        return False


def mark_nlp_error(
    session: Session,
    message_id: int,
    error_message: str
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
        from src.database.models import Message
        
        msg = session.get(Message, message_id)
        if not msg:
            logger.warning(f"Message {message_id} not found")
            return False
        
        msg.nlp_error = error_message[:500]  # Truncate long errors
        msg.nlp_retry_count = (msg.nlp_retry_count or 0) + 1
        msg.nlp_processed_at = datetime.utcnow()
        
        session.commit()
        logger.debug(f"Marked NLP error for message {message_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to mark error for message {message_id}: {e}")
        session.rollback()
        return False

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

def get_messages_by_category(
    session: Session,
    category: str,
    min_confidence: float = 0.0,
    limit: int = 100
) -> list[Any]:
    """
    Get messages classified into a specific category.
    
    Args:
        session: Database session
        category: Category name
        min_confidence: Minimum confidence threshold
        limit: Maximum number of messages to return
        
    Returns:
        List of Message objects
    """
    try:
        from src.database.models import Message
        
        stmt = (
            select(Message)
            .where(Message.processed_nlp == True)
            .where(Message.category == category)
            .where(Message.confidence >= min_confidence)
            .order_by(Message.confidence.desc())
            .limit(limit)
        )
        
        messages = session.execute(stmt).scalars().all()
        logger.debug(f"Found {len(messages)} messages in category '{category}'")
        return messages
        
    except Exception as e:
        logger.exception(f"Failed to get messages by category: {e}")
        return []


def get_messages_with_entity(
    session: Session,
    entity_text: str,
    entity_type: str | None = None,
    limit: int = 100
) -> list[Any]:
    """
    Get messages containing a specific entity.
    
    Args:
        session: Database session
        entity_text: Entity text to search for
        entity_type: Optional entity type filter (DRUG, CONDITION, etc.)
        limit: Maximum number of messages to return
        
    Returns:
        List of Message objects
    """
    try:
        from src.database.models import Message
        from sqlalchemy import func
        
        stmt = select(Message).where(Message.processed_nlp == True)
        
        # Search in entities JSON
        # This is PostgreSQL-specific. Adjust for other databases.
        if entity_type:
            stmt = stmt.where(
                func.jsonb_path_exists(
                    Message.entities,
                    f'$.{entity_type}[*] ? (@.text == "{entity_text}")'
                )
            )
        else:
            # Search across all entity types
            stmt = stmt.where(
                func.jsonb_path_exists(
                    Message.entities,
                    f'$.*[*] ? (@.text == "{entity_text}")'
                )
            )
        
        stmt = stmt.limit(limit)
        
        messages = session.execute(stmt).scalars().all()
        logger.debug(f"Found {len(messages)} messages with entity '{entity_text}'")
        return messages
        
    except Exception as e:
        logger.exception(f"Failed to get messages with entity: {e}")
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
        from src.database.models import Message
        from sqlalchemy import func
        
        # Total messages
        total = session.query(func.count(Message.id)).scalar()
        
        # Processed messages
        processed = session.query(func.count(Message.id)).where(
            Message.processed_nlp == True
        ).scalar()
        
        # Messages with errors
        errors = session.query(func.count(Message.id)).where(
            Message.nlp_error != None
        ).scalar()
        
        # Category distribution
        category_dist = session.query(
            Message.category,
            func.count(Message.id)
        ).where(
            Message.processed_nlp == True
        ).group_by(Message.category).all()
        
        # Average confidence by category
        avg_confidence = session.query(
            Message.category,
            func.avg(Message.confidence)
        ).where(
            Message.processed_nlp == True
        ).group_by(Message.category).all()
        
        stats = {
            "total_messages": total,
            "processed_messages": processed,
            "unprocessed_messages": total - processed,
            "error_messages": errors,
            "processing_rate": processed / total if total > 0 else 0.0,
            "category_distribution": dict(category_dist),
            "avg_confidence_by_category": dict(avg_confidence)
        }
        
        logger.info(f"NLP processing stats: {processed}/{total} processed ({stats['processing_rate']:.1%})")
        return stats
        
    except Exception as e:
        logger.exception(f"Failed to get NLP stats: {e}")
        return {}


def retry_failed_messages(
    session: Session,
    max_retries: int = 3,
    limit: int = 100
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
        from src.database.models import Message
        
        stmt = (
            select(Message)
            .where(Message.processed_nlp == False)
            .where(Message.nlp_error != None)
            .where(Message.nlp_retry_count < max_retries)
            .order_by(Message.nlp_processed_at.asc())
            .limit(limit)
        )
        
        messages = session.execute(stmt).scalars().all()
        logger.info(f"Found {len(messages)} messages to retry")
        return messages
        
    except Exception as e:
        logger.exception(f"Failed to get messages for retry: {e}")
        return []


def bulk_update_nlp_version(
    session: Session,
    old_version: str,
    new_version: str
) -> int:
    """
    Update NLP version for reprocessing.
    
    Args:
        session: Database session
        old_version: Old version string to match
        new_version: New version string to set
        
    Returns:
        Number of messages updated
    """
    try:
        from src.database.models import Message
        
        stmt = (
            update(Message)
            .where(Message.nlp_version == old_version)
            .values(nlp_version=new_version)
        )
        
        result = session.execute(stmt)
        session.commit()
        
        count = result.rowcount
        logger.info(f"Updated {count} messages from version {old_version} to {new_version}")
        return count
        
    except Exception as e:
        logger.exception(f"Failed to bulk update NLP version: {e}")
        session.rollback()
        return 0


def reset_processing_status(
    session: Session,
    message_ids: list[int] | None = None
) -> int:
    """
    Reset processing status for messages (for reprocessing).
    
    Args:
        session: Database session
        message_ids: Optional list of specific message IDs to reset
        
    Returns:
        Number of messages reset
    """
    try:
        from src.database.models import Message
        
        stmt = update(Message).values(
            processed_nlp=False,
            nlp_error=None,
            nlp_retry_count=0
        )
        
        if message_ids:
            stmt = stmt.where(Message.id.in_(message_ids))
        
        result = session.execute(stmt)
        session.commit()
        
        count = result.rowcount
        logger.info(f"Reset processing status for {count} messages")
        return count
        
    except Exception as e:
        logger.exception(f"Failed to reset processing status: {e}")
        session.rollback()
        return 0