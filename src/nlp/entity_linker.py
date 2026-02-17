"""
Entity Linking to Knowledge Base.

Links extracted entities to structured knowledge bases (UMLS, RxNorm, etc.)
using fuzzy matching and normalization techniques.
"""

import json
from pathlib import Path
from typing import Any

from src.logger import get_logger
from src.nlp.exceptions import EntityLinkingError, KnowledgeBaseNotFoundError
from src.nlp.config import get_config

logger = get_logger(__name__)


# Cache for loaded knowledge bases
_KB_CACHE: dict[str, dict] = {}


def load_kb(path: Path, kb_name: str = "unknown") -> dict:
    """
    Load knowledge base from JSON file with caching.
    
    Args:
        path: Path to KB JSON file
        kb_name: Name of the KB for logging
        
    Returns:
        Dictionary containing KB data
        
    Raises:
        KnowledgeBaseNotFoundError: If KB file doesn't exist
        EntityLinkingError: If KB file is invalid
    """
    # Check cache first
    cache_key = str(path.absolute())
    if cache_key in _KB_CACHE:
        logger.debug(f"Using cached KB: {kb_name}")
        return _KB_CACHE[cache_key]
    
    if not path.exists():
        logger.error(f"Knowledge base not found: {path}")
        raise KnowledgeBaseNotFoundError(kb_name, str(path))
    
    try:
        logger.info(f"Loading knowledge base: {kb_name} from {path}")
        with open(path, encoding="utf-8") as f:
            kb_data = json.load(f)
        
        # Validate KB structure
        if not isinstance(kb_data, dict):
            raise EntityLinkingError(
                f"Invalid KB format: expected dict, got {type(kb_data).__name__}",
                kb_name
            )
        
        # Cache the KB
        _KB_CACHE[cache_key] = kb_data
        logger.info(f"Loaded {len(kb_data)} entries from {kb_name}")
        
        return kb_data
        
    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse KB JSON: {e}")
        raise EntityLinkingError(f"Invalid JSON in KB file: {str(e)}", kb_name) from e
    except Exception as e:
        logger.exception(f"Failed to load KB: {e}")
        raise EntityLinkingError(f"Failed to load KB: {str(e)}", kb_name) from e


def clear_kb_cache() -> None:
    """Clear the knowledge base cache (useful for testing/updates)."""
    global _KB_CACHE
    count = len(_KB_CACHE)
    _KB_CACHE.clear()
    logger.info(f"Cleared {count} knowledge bases from cache")


def link_entities(
    entities: dict[str, list],
    base_dir: Path | None = None,
    threshold: float | None = None
) -> dict[str, list[dict[str, Any]]]:
    """
    Link extracted entities to knowledge base IDs using fuzzy matching.
    
    Args:
        entities: Dictionary of entities from extract_entities()
        base_dir: Base directory containing KB files
        threshold: Minimum similarity score (0-100). Uses config default if None
        
    Returns:
        Dictionary mapping labels to lists of linked entity dicts.
        Each dict contains: text, kb_id, match_score, canonical_name
        
    Raises:
        EntityLinkingError: If linking fails
        
    Example:
        >>> entities = {"DRUG": [{"text": "asprin", ...}]}
        >>> linked = link_entities(entities)
        >>> print(linked)
        {
            "DRUG": [{
                "text": "asprin",
                "kb_id": "RxNorm:1191",
                "match_score": 95.2,
                "canonical_name": "aspirin"
            }]
        }
    """
    if not entities:
        return {}
    
    # Get configuration
    config = get_config()
    base_dir = base_dir or Path("data/kb")
    threshold = threshold if threshold is not None else config.entity_link_threshold
    
    # Define KB mappings
    kb_configs = {
        "DRUG": {
            "path": config.drug_kb_path if config.drug_kb_path.is_absolute() 
                   else base_dir / config.drug_kb_path,
            "name": "drug_database"
        },
        "CONDITION": {
            "path": config.condition_kb_path if config.condition_kb_path.is_absolute()
                   else base_dir / config.condition_kb_path,
            "name": "medical_terms"
        },
        "PROCEDURE": {
            "path": config.procedure_kb_path if config.procedure_kb_path.is_absolute()
                   else base_dir / config.procedure_kb_path,
            "name": "procedures"
        }
    }
    
    # Load knowledge bases
    kbs = {}
    for label, kb_config in kb_configs.items():
        if label in entities and len(entities[label]) > 0:
            try:
                kbs[label] = load_kb(kb_config["path"], kb_config["name"])
            except KnowledgeBaseNotFoundError:
                logger.warning(f"KB not found for {label}, entities will not be linked")
                kbs[label] = {}
            except Exception as e:
                logger.warning(f"Failed to load KB for {label}: {e}")
                kbs[label] = {}
    
    # Link entities
    linked = {}
    
    try:
        for label, items in entities.items():
            linked[label] = []
            kb = kbs.get(label, {})
            
            for item in items:
                # Extract text
                text = item.get("text", "") if isinstance(item, dict) else str(item)
                
                if not text or not kb:
                    # No text or no KB available
                    linked[label].append({
                        "text": text,
                        "kb_id": None,
                        "match_score": 0.0,
                        "canonical_name": None,
                        **({k: v for k, v in item.items() if k != "text"} if isinstance(item, dict) else {})
                    })
                    continue
                
                # Perform fuzzy matching
                match_result = _fuzzy_match(text, kb, threshold)
                
                # Build linked entity
                linked_entity = {
                    "text": text,
                    "kb_id": match_result["kb_id"],
                    "match_score": match_result["score"],
                    "canonical_name": match_result["canonical_name"],
                    **({k: v for k, v in item.items() if k != "text"} if isinstance(item, dict) else {})
                }
                
                linked[label].append(linked_entity)
        
        # Log linking summary
        total_linked = sum(
            1 for label_entities in linked.values()
            for entity in label_entities
            if entity.get("kb_id") is not None
        )
        total_entities = sum(len(label_entities) for label_entities in linked.values())
        
        logger.debug(f"Linked {total_linked}/{total_entities} entities to KB")
        
        return linked
        
    except Exception as e:
        logger.exception(f"Entity linking failed: {e}")
        raise EntityLinkingError(f"Failed to link entities: {str(e)}") from e


    def link_entities(
        entities: list[dict],
        kb: dict,
        threshold: float = 0.8
    ) -> list[dict]:
        """
        Link extracted entities to KB using fuzzy matching and normalization.
        Args:
            entities: List of entity dicts (text, label, etc.)
            kb: Knowledge base dict
            threshold: Minimum similarity score for linking
        Returns:
            List of linked entity dicts with KB IDs
        """
        from rapidfuzz import process, fuzz
        linked_entities = []
        for entity in entities:
            text = entity.get("text", "")
            label = entity.get("label", "")
            kb_entries = kb.get(label, [])
            if not kb_entries:
                entity["kb_id"] = None
                entity["kb_match"] = None
                entity["kb_score"] = 0.0
                linked_entities.append(entity)
                continue
            # Normalize text for matching
            norm_text = text.lower().strip()
            norm_kb_entries = [e["name"].lower().strip() if isinstance(e, dict) and "name" in e else str(e).lower().strip() for e in kb_entries]
            # Fuzzy match
            match, score, idx = process.extractOne(norm_text, norm_kb_entries, scorer=fuzz.ratio)
            if score >= threshold * 100:
                kb_entry = kb_entries[idx]
                entity["kb_id"] = kb_entry.get("id") if isinstance(kb_entry, dict) else kb_entry
                entity["kb_match"] = kb_entry
                entity["kb_score"] = score / 100.0
            else:
                entity["kb_id"] = None
                entity["kb_match"] = None
                entity["kb_score"] = score / 100.0
            linked_entities.append(entity)
        return linked_entities
def _fuzzy_match(
    text: str,
    kb: dict,
    threshold: float
) -> dict[str, Any]:
    """
    Perform fuzzy matching of text against knowledge base.
    
    Args:
        text: Entity text to match
        kb: Knowledge base dictionary
        threshold: Minimum similarity score (0-100)
        
    Returns:
        Dict with kb_id, score, and canonical_name
    """
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        logger.warning("rapidfuzz not installed, using exact matching only")
        return _exact_match(text, kb)
    
    # Normalize text for matching
    normalized_text = text.lower().strip()
    
    # Try exact match first (fastest)
    if normalized_text in kb:
        entry = kb[normalized_text]
        return {
            "kb_id": entry.get("id") or entry.get("kb_id"),
            "score": 100.0,
            "canonical_name": entry.get("canonical_name") or entry.get("name") or text
        }
    
    # Fuzzy match against all KB keys
    match = process.extractOne(
        normalized_text,
        kb.keys(),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold
    )
    
    if match:
        matched_key, score, _ = match
        entry = kb[matched_key]
        
        return {
            "kb_id": entry.get("id") or entry.get("kb_id"),
            "score": float(score),
            "canonical_name": entry.get("canonical_name") or entry.get("name") or matched_key
        }
    
    # No match found
    return {
        "kb_id": None,
        "score": 0.0,
        "canonical_name": None
    }


def _exact_match(text: str, kb: dict) -> dict[str, Any]:
    """
    Perform exact matching (fallback when rapidfuzz not available).
    
    Args:
        text: Entity text to match
        kb: Knowledge base dictionary
        
    Returns:
        Dict with kb_id, score, and canonical_name
    """
    normalized_text = text.lower().strip()
    
    if normalized_text in kb:
        entry = kb[normalized_text]
        return {
            "kb_id": entry.get("id") or entry.get("kb_id"),
            "score": 100.0,
            "canonical_name": entry.get("canonical_name") or entry.get("name") or text
        }
    
    return {
        "kb_id": None,
        "score": 0.0,
        "canonical_name": None
    }


def create_kb_index(kb_path: Path, output_path: Path | None = None) -> None:
    """
    Create an optimized index for faster KB lookups.
    
    Args:
        kb_path: Path to source KB JSON file
        output_path: Path for output index file (defaults to kb_path + .index)
    """
    output_path = output_path or Path(str(kb_path) + ".index")
    
    try:
        logger.info(f"Creating KB index: {kb_path} -> {output_path}")
        
        # Load KB
        with open(kb_path, encoding="utf-8") as f:
            kb_data = json.load(f)
        
        # Create index with normalized keys
        index = {}
        for key, value in kb_data.items():
            normalized = key.lower().strip()
            index[normalized] = value
            
            # Add aliases if present
            if "aliases" in value:
                for alias in value["aliases"]:
                    normalized_alias = alias.lower().strip()
                    if normalized_alias not in index:
                        index[normalized_alias] = value
        
        # Save index
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
        
        logger.info(f"Created index with {len(index)} entries")
        
    except Exception as e:
        logger.exception(f"Failed to create KB index: {e}")
        raise EntityLinkingError(f"Failed to create index: {str(e)}") from e


def get_linking_stats(linked_entities: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """
    Get statistics about entity linking results.
    
    Args:
        linked_entities: Result from link_entities()
        
    Returns:
        Dictionary with linking statistics
    """
    stats = {
        "total_entities": 0,
        "linked_entities": 0,
        "unlinked_entities": 0,
        "avg_match_score": 0.0,
        "by_label": {}
    }
    
    scores = []
    
    for label, entities in linked_entities.items():
        label_stats = {
            "total": len(entities),
            "linked": 0,
            "unlinked": 0,
            "avg_score": 0.0
        }
        
        label_scores = []
        
        for entity in entities:
            stats["total_entities"] += 1
            label_stats["total"] += 1
            
            if entity.get("kb_id"):
                stats["linked_entities"] += 1
                label_stats["linked"] += 1
                score = entity.get("match_score", 0.0)
                scores.append(score)
                label_scores.append(score)
            else:
                stats["unlinked_entities"] += 1
                label_stats["unlinked"] += 1
        
        if label_scores:
            label_stats["avg_score"] = sum(label_scores) / len(label_scores)
        
        stats["by_label"][label] = label_stats
    
    if scores:
        stats["avg_match_score"] = sum(scores) / len(scores)
    
    return stats