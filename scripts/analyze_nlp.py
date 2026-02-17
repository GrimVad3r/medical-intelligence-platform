#!/usr/bin/env python3
"""
NLP Analysis Script.
"""

import os
import ssl
import sys
import warnings
import urllib3


# ══════════════════════════════════════════════════════════════════════
# 2. STANDARD IMPORTS
# ══════════════════════════════════════════════════════════════════════
import argparse
import json
import time
from pathlib import Path
from typing import Any
from datetime import datetime

import logging
# Silence the "Some weights were not initialized" warning
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

# Setup project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from tqdm import tqdm
    from src.logger import get_logger
    from src.nlp.message_processor import MessageProcessor
    from src.nlp.model_manager import ModelManager
    from src.nlp.config import get_config
    from src.nlp.exceptions import NLPError, TextValidationError
    from src.database.connection import get_session_factory
    from src.database.queries import get_unprocessed_messages
    from src.database.models import Message
except ImportError as e:
    print(f"Import error: {e}. Ensure 'src' is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)

# ══════════════════════════════════════════════════════════════════════
# 3. HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def update_message_object(msg: Any, nlp_result: dict[str, Any]) -> None:
    """Helper to map NLP results to a Message database object without committing."""
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

def analyze_from_db(
    processor: MessageProcessor,
    session_factory: Any,
    limit: int = 100,
    explain: bool = False,
    relationships: bool = False,
    batch_size: int = 50,
    save_plots: bool = False
) -> dict[str, Any]:
    """Process messages from database with optimized batch committing."""
    
    with session_factory() as session:
        messages = get_unprocessed_messages(session, limit=limit)
    
    if not messages:
        logger.info("No unprocessed messages found")
        return {"total": 0, "processed": 0, "errors": 0, "skipped": 0, "duration": 0.0}
    
    stats = {
        "total": len(messages),
        "processed": 0,
        "errors": 0,
        "skipped": 0,
        "start_time": time.time()
    }
    
    logger.info(f"Processing {len(messages)} messages (Batch Size: {batch_size})")
    
    shap_dir = Path("data/shap_plots")
    if save_plots:
        shap_dir.mkdir(parents=True, exist_ok=True)
    with session_factory() as session:
        for i, msg in enumerate(tqdm(messages, desc="NLP Processing", unit="msg")):
            try:
                if not getattr(msg, 'text', None):
                    stats["skipped"] += 1
                    continue
                # NLP Processing
                result = processor.process(
                    msg.text,
                    include_explanations=explain,
                    include_relationships=relationships
                )
                # Save SHAP plot for each DB message if explain enabled and save_plots
                if explain and save_plots and "shap_values" in result:
                    import shap
                    import matplotlib.pyplot as plt
                    shap_values = result["shap_values"]
                    explainer = result.get("explainer")
                    if explainer:
                        shap.summary_plot(shap_values, show=False)
                        plt.savefig(shap_dir / f"shap_plot_db_{msg.id}.png")
                        plt.close()
                # Update the object in the current session
                db_msg = session.get(Message, msg.id)
                if db_msg:
                    update_message_object(db_msg, result)
                    stats["processed"] += 1
                # Batch Commit: Every X records, save to disk
                if (i + 1) % batch_size == 0:
                    session.commit()
                    logger.debug(f"Batch commit at record {i+1}")
            except Exception as e:
                logger.error(f"Error processing message {msg.id}: {e}")
                stats["errors"] += 1
                session.rollback() # Rollback the current failed record
                # Mark error separately to avoid blocking the whole batch
                with session_factory() as err_session:
                    err_msg = err_session.get(Message, msg.id)
                    if err_msg:
                        err_msg.nlp_error = str(e)[:500]
                        err_msg.nlp_retry_count = (err_msg.nlp_retry_count or 0) + 1
                        err_session.commit()
        # Final commit for the remaining records
        session.commit()
    
    stats["duration"] = time.time() - stats["start_time"]
    stats["messages_per_second"] = stats["processed"] / stats["duration"] if stats["duration"] > 0 else 0
    return stats

# ... [Keep analyze_text, analyze_from_file, print_statistics as they were] ...

def analyze_text(processor, text, explain=False, relationships=False):
    result = processor.process(text, include_explanations=explain, include_relationships=relationships)
    # Save SHAP plot if explain enabled and SHAP values present and save_plots
    if getattr(analyze_text, "save_plots", False) and explain and "shap_values" in result:
        shap_dir = Path("data/shap_plots")
        shap_dir.mkdir(parents=True, exist_ok=True)
        import shap
        import matplotlib.pyplot as plt
        shap_values = result["shap_values"]
        explainer = result.get("explainer")
        if explainer:
            shap.summary_plot(shap_values, show=False)
            plt.savefig(shap_dir / "shap_plot_text.png")
            plt.close()
    return result

def analyze_from_file(processor, file_path, explain=False, relationships=False, output_path=None):
    if not file_path.exists(): return {"error": "File not found"}
    content = file_path.read_text(encoding="utf-8")
    texts = [line.strip() for line in content.splitlines() if line.strip()]
    results = []
    shap_dir = Path("data/shap_plots")
    stats = {"total": len(texts), "processed": 0, "errors": 0, "start_time": time.time()}
    for i, text in enumerate(tqdm(texts), 1):
        try:
            res = processor.process(text, include_explanations=explain, include_relationships=relationships)
            results.append({"index": i, "text": text, **res})
            stats["processed"] += 1
            # Save SHAP plot for each text if explain enabled and save_plots
            if getattr(analyze_from_file, "save_plots", False) and explain and "shap_values" in res:
                shap_dir.mkdir(parents=True, exist_ok=True)
                import shap
                import matplotlib.pyplot as plt
                shap_values = res["shap_values"]
                explainer = res.get("explainer")
                if explainer:
                    shap.summary_plot(shap_values, show=False)
                    plt.savefig(shap_dir / f"shap_plot_file_{i}.png")
                    plt.close()
        except Exception as e:
            stats["errors"] += 1
    stats["duration"] = time.time() - stats["start_time"]
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(results, f, indent=2)
    return stats

def print_statistics(stats):
    print("\n" + "="*40 + "\nNLP STATISTICS\n" + "="*40)
    for k, v in stats.items(): print(f"{k.capitalize()}: {v}")
    print("="*40 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Medical NLP Platform")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", type=str)
    input_group.add_argument("--file", type=Path)
    input_group.add_argument("--from-db", action="store_true")
    parser.add_argument("--explain", action="store_true", help="Include SHAP explanations")
    parser.add_argument("--save_plots", action="store_true", help="Save SHAP plots to data/shap_plots")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        logger.info("Initializing NLP Models...")
        model_manager = ModelManager()
        processor = MessageProcessor(model_manager=model_manager)

        config = get_config()
        
        # 2. Verify Local Path exists before starting
        local_model_path = Path(config.classifier_model)
        if not local_model_path.exists():
            logger.error(f"❌ Model folder NOT FOUND at: {local_model_path}")
            logger.error("Please ensure you downloaded the model manually to that location.")
            sys.exit(1)
        
        # 3. Check for the critical config.json file
        if not (local_model_path / "config.json").exists():
            logger.error(f"❌ config.json missing in {local_model_path}")
            sys.exit(1)

        logger.info(f"🚀 Initializing NLP using LOCAL model: {local_model_path}")
        
        model_manager = ModelManager()
        processor = MessageProcessor(model_manager=model_manager)
        
        if args.text:
            analyze_text.save_plots = args.save_plots
            result = analyze_text(processor, args.text, explain=args.explain)
            print(json.dumps(result, indent=2))
        elif args.file:
            analyze_from_file.save_plots = args.save_plots
            stats = analyze_from_file(processor, args.file, output_path=args.output, explain=args.explain)
            print_statistics(stats)
        elif args.from_db:
            stats = analyze_from_db(processor, get_session_factory(), limit=args.limit, explain=args.explain, batch_size=args.batch_size, save_plots=args.save_plots)
            print_statistics(stats)

    except Exception as e:
        logger.exception(f"Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()