#!/usr/bin/env python3
"""
NLP Analysis Script for Medical Intelligence Platform.

Runs NER, classification, entity linking, and optional SHAP explainability
on text input or messages from the database with comprehensive monitoring,
progress tracking, and error handling.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
    from src.nlp.message_processor import MessageProcessor
    from src.nlp.model_manager import ModelManager
    from src.nlp.config import get_config
    from src.nlp.exceptions import NLPError, TextValidationError
    from src.database.connection import get_session_factory
    from src.database.queries import get_unprocessed_messages
except ImportError as e:
    print(f"Import error: {e}. Ensure src is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)


def analyze_text(
    processor: MessageProcessor,
    text: str,
    explain: bool = False,
    relationships: bool = False
) -> dict[str, Any]:
    """
    Run full NLP pipeline on a single text.
    
    Args:
        processor: MessageProcessor instance
        text: Text to analyze
        explain: Include SHAP explanations
        relationships: Include relationship analysis
        
    Returns:
        Processing result dictionary
        
    Raises:
        NLPError: If processing fails
    """
    result = processor.process(
        text,
        include_explanations=explain,
        include_relationships=relationships
    )
    return result


def save_nlp_results(session: Any, message_id: int, nlp_result: dict[str, Any]) -> None:
    """
    Update message record with NLP processing results.
    
    Args:
        session: Database session
        message_id: ID of the message to update
        nlp_result: NLP processing results
    """
    try:
        # Import here to avoid circular dependency
        from src.database.models import Message
        from datetime import datetime
        
        msg = session.get(Message, message_id)
        if msg:
            msg.entities = nlp_result.get("entities")
            msg.category = nlp_result.get("category")
            msg.confidence = nlp_result.get("confidence")
            msg.linked_entities = nlp_result.get("linked_entities")
            msg.relationships = nlp_result.get("relationships")
            msg.is_nlp_processed = True
            msg.nlp_processed_at = datetime.utcnow()
            msg.nlp_version = nlp_result.get("metadata", {}).get("model_version")
            msg.nlp_error = None
            msg.nlp_retry_count = 0
            
            session.commit()
            logger.debug(f"Saved NLP results for message {message_id}")
        else:
            logger.warning(f"Message {message_id} not found in database")
            
    except Exception as e:
        logger.error(f"Failed to save NLP results for message {message_id}: {e}")
        session.rollback()


def mark_nlp_error(session: Any, message_id: int, error_message: str) -> None:
    """
    Mark a message with an NLP processing error.
    
    Args:
        session: Database session
        message_id: ID of the message
        error_message: Error description
    """
    try:
        from src.database.models import Message
        from datetime import datetime
        
        msg = session.get(Message, message_id)
        if msg:
            msg.nlp_error = error_message[:500]  # Truncate long errors
            msg.nlp_retry_count = (msg.nlp_retry_count or 0) + 1
            msg.nlp_processed_at = datetime.utcnow()
            
            session.commit()
            logger.debug(f"Marked NLP error for message {message_id}")
            
    except Exception as e:
        logger.error(f"Failed to mark error for message {message_id}: {e}")
        session.rollback()


def analyze_from_db(
    processor: MessageProcessor,
    session_factory: Any,
    limit: int = 100,
    explain: bool = False,
    relationships: bool = False,
    batch_size: int = 100
) -> dict[str, Any]:
    """
    Process unprocessed messages from database.
    
    Args:
        processor: MessageProcessor instance
        session_factory: Database session factory
        limit: Maximum number of messages to process
        explain: Include SHAP explanations
        relationships: Include relationship analysis
        batch_size: Commit batch size
        
    Returns:
        Dictionary with processing statistics
    """
    with session_factory() as session:
        messages = get_unprocessed_messages(session, limit=limit)
    
    if not messages:
        logger.info("No unprocessed messages found")
        return {
            "total": 0,
            "processed": 0,
            "errors": 0,
            "skipped": 0,
            "duration": 0.0
        }
    
    stats = {
        "total": len(messages),
        "processed": 0,
        "errors": 0,
        "skipped": 0,
        "start_time": time.time()
    }
    
    logger.info(f"Processing {len(messages)} messages from database")
    
    # Process messages with progress bar
    with session_factory() as session:
        for msg in tqdm(messages, desc="Processing messages", unit="msg"):
            try:
                # Validate message has text
                if not hasattr(msg, 'text') or not msg.text:
                    logger.debug(f"Skip message {msg.id}: no text")
                    stats["skipped"] += 1
                    continue
                
                # Process message
                result = processor.process(
                    msg.text,
                    include_explanations=explain,
                    include_relationships=relationships
                )
                
                # Save results
                save_nlp_results(session, msg.id, result)
                stats["processed"] += 1
                
                # Log progress periodically
                if stats["processed"] % 100 == 0:
                    elapsed = time.time() - stats["start_time"]
                    rate = stats["processed"] / elapsed
                    logger.info(
                        f"Progress: {stats['processed']}/{len(messages)} "
                        f"({rate:.1f} msg/s)"
                    )
                
            except TextValidationError as e:
                logger.debug(f"Skip message {msg.id}: {e}")
                mark_nlp_error(session, msg.id, f"Validation error: {str(e)}")
                stats["skipped"] += 1
                
            except Exception as e:
                logger.error(f"Error processing message {msg.id}: {e}")
                mark_nlp_error(session, msg.id, str(e))
                stats["errors"] += 1
    
    stats["duration"] = time.time() - stats["start_time"]
    
    # Calculate rates
    if stats["duration"] > 0:
        stats["messages_per_second"] = stats["processed"] / stats["duration"]
    else:
        stats["messages_per_second"] = 0.0
    
    return stats


def analyze_from_file(
    processor: MessageProcessor,
    file_path: Path,
    explain: bool = False,
    relationships: bool = False,
    output_path: Path | None = None
) -> dict[str, Any]:
    """
    Process messages from a file.
    
    Args:
        processor: MessageProcessor instance
        file_path: Path to input file (text or JSON)
        explain: Include SHAP explanations
        relationships: Include relationship analysis
        output_path: Optional path to save results
        
    Returns:
        Dictionary with processing statistics
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return {"error": "File not found"}
    
    logger.info(f"Processing messages from file: {file_path}")
    
    # Read file content
    content = file_path.read_text(encoding="utf-8")
    
    # Parse content (JSON list or line-delimited text)
    try:
        if content.strip().startswith("["):
            data = json.loads(content)
            texts = [item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in data]
        else:
            texts = [line.strip() for line in content.splitlines() if line.strip()]
    except Exception as e:
        logger.error(f"Failed to parse file: {e}")
        return {"error": f"Failed to parse file: {str(e)}"}
    
    if not texts:
        logger.warning("No texts found in file")
        return {"total": 0, "processed": 0, "errors": 0}
    
    logger.info(f"Found {len(texts)} texts to process")
    
    # Process texts
    results = []
    stats = {
        "total": len(texts),
        "processed": 0,
        "errors": 0,
        "start_time": time.time()
    }
    
    for i, text in enumerate(tqdm(texts, desc="Processing texts"), 1):
        try:
            result = processor.process(
                text,
                include_explanations=explain,
                include_relationships=relationships
            )
            results.append({
                "index": i,
                "text": text,
                **result
            })
            stats["processed"] += 1
            
        except Exception as e:
            logger.error(f"Failed to process text {i}: {e}")
            results.append({
                "index": i,
                "text": text[:100],
                "error": str(e)
            })
            stats["errors"] += 1
    
    stats["duration"] = time.time() - stats["start_time"]
    
    # Save results if output path provided
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "statistics": stats,
                    "results": results
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    return stats


def print_statistics(stats: dict[str, Any]) -> None:
    """
    Print processing statistics in a formatted way.
    
    Args:
        stats: Statistics dictionary
    """
    print("\n" + "="*60)
    print("NLP PROCESSING STATISTICS")
    print("="*60)
    print(f"Total messages:      {stats.get('total', 0)}")
    print(f"Successfully processed: {stats.get('processed', 0)}")
    print(f"Errors:              {stats.get('errors', 0)}")
    print(f"Skipped:             {stats.get('skipped', 0)}")
    print(f"Duration:            {stats.get('duration', 0):.2f}s")
    
    if stats.get('messages_per_second'):
        print(f"Processing rate:     {stats['messages_per_second']:.1f} msg/s")
    
    print("="*60 + "\n")


def main():
    """Main entry point for the NLP analysis script."""
    parser = argparse.ArgumentParser(
        description="Run NLP analysis (NER, classification, entity linking) for Medical Intelligence Platform.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single text
  python scripts/analyze_nlp.py --text "Patient prescribed 20mg Lisinopril"
  
  # Process from database
  python scripts/analyze_nlp.py --from-db --limit 1000
  
  # Process from file with explanations
  python scripts/analyze_nlp.py --file messages.txt --explain --output results.json
  
  # Preload models before processing
  python scripts/analyze_nlp.py --from-db --preload-models
        """
    )
    
    # Input sources (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--text",
        type=str,
        help="Analyze this text directly"
    )
    input_group.add_argument(
        "--file",
        type=Path,
        help="Read texts from file (one per line or JSON list)"
    )
    input_group.add_argument(
        "--from-db",
        action="store_true",
        help="Process unprocessed messages from database"
    )
    
    # Processing options
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max messages when using --from-db (default: 100)"
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Include SHAP explanations (slower)"
    )
    parser.add_argument(
        "--relationships",
        action="store_true",
        help="Include relationship analysis"
    )
    parser.add_argument(
        "--preload-models",
        action="store_true",
        help="Preload all models before processing"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save results to JSON file (for --file or --text)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Database commit batch size (default: 100)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        import logging
        logging.getLogger("src.nlp").setLevel(logging.DEBUG)
    
    try:
        # Initialize model manager
        logger.info("Initializing NLP components...")
        model_manager = ModelManager()
        
        if args.preload_models:
            logger.info("Preloading models...")
            model_manager.load_all()
            logger.info("Models loaded successfully")
        
        # Initialize processor
        processor = MessageProcessor(model_manager=model_manager)
        config = get_config()
        
        logger.info(f"Processor initialized (device={config.device})")
        
    except Exception as e:
        logger.exception(f"Failed to initialize NLP components: {e}")
        sys.exit(1)
    
    # Process based on input source
    processed_count = 0
    stats = {}
    
    try:
        if args.text:
            # Single text analysis
            logger.info("Analyzing single text...")
            result = analyze_text(
                processor,
                args.text,
                explain=args.explain,
                relationships=args.relationships
            )
            
            # Print or save result
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"Result saved to {args.output}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            
            processed_count = 1
            
        elif args.file:
            # File-based processing
            stats = analyze_from_file(
                processor,
                args.file,
                explain=args.explain,
                relationships=args.relationships,
                output_path=args.output
            )
            processed_count = stats.get("processed", 0)
            
        elif args.from_db:
            # Database processing
            session_factory = get_session_factory()
            stats = analyze_from_db(
                processor,
                session_factory,
                limit=args.limit,
                explain=args.explain,
                relationships=args.relationships,
                batch_size=args.batch_size
            )
            processed_count = stats.get("processed", 0)
        
        # Print statistics if available
        if stats:
            print_statistics(stats)
        
        # Print processor statistics
        proc_stats = processor.get_statistics()
        if proc_stats["total_processed"] > 0:
            print(f"Cache hit rate: {proc_stats['cache_hit_rate']:.1%}")
            print(f"Average processing time: {proc_stats['avg_time']:.3f}s")
        
        logger.info(f"Processing complete: {processed_count} items processed")
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()