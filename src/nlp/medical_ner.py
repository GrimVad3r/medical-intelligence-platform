"""
Medical Named Entity Recognition.

Extracts medical entities (drugs, conditions, dosages, procedures) from text
using spaCy models trained on medical literature.
"""

import re
from typing import Any

from src.logger import get_logger
from src.nlp.exceptions import EntityExtractionError, TextValidationError
from src.nlp.config import get_config

logger = get_logger(__name__)


# Entity label mappings from spaCy/scispaCy to our schema
ENTITY_LABEL_MAP = {
    "CHEMICAL": "DRUG",
    "DRUG": "DRUG",
    "DISEASE": "CONDITION",
    "CONDITION": "CONDITION",
    "SYMPTOM": "CONDITION",
    "DIAGNOSTIC_PROCEDURE": "PROCEDURE",
    "THERAPEUTIC_PROCEDURE": "PROCEDURE",
    "PROCEDURE": "PROCEDURE",
}

# Dosage patterns for rule-based extraction
DOSAGE_PATTERNS = [
    re.compile(r'\b(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|µg|ug|cc|units?)\b', re.IGNORECASE),
    re.compile(r'\b(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|µg|ug|cc|units?)\b', re.IGNORECASE),
    re.compile(r'\b(\d+)\s*(tablet|capsule|pill)s?\b', re.IGNORECASE),
]


def extract_entities(
    text: str,
    model: Any = None,
    include_dosage: bool = True
) -> dict[str, list[dict[str, Any]]]:
    """
    Extract medical entities from text.
    
    Args:
        text: Input text to process
        model: Optional pre-loaded spaCy model. If None, loads from model manager
        include_dosage: Whether to include rule-based dosage extraction
        
    Returns:
        Dictionary mapping entity labels to lists of entity dictionaries.
        Each entity dict contains: text, start, end, label, confidence (optional)
        
    Raises:
        TextValidationError: If text is invalid
        EntityExtractionError: If extraction fails
        
    Example:
        >>> entities = extract_entities("Patient prescribed 20mg Lisinopril for hypertension")
        >>> print(entities)
        {
            "DRUG": [{"text": "Lisinopril", "start": 27, "end": 37, "label": "DRUG"}],
            "CONDITION": [{"text": "hypertension", "start": 42, "end": 54, "label": "CONDITION"}],
            "DOSAGE": [{"text": "20mg", "start": 20, "end": 24, "label": "DOSAGE"}]
        }
    """
    # Initialize entity structure
    entities: dict[str, list[dict[str, Any]]] = {
        "DRUG": [],
        "CONDITION": [],
        "DOSAGE": [],
        "PROCEDURE": []
    }
    
    # Validate input
    if not text:
        logger.debug("Empty text provided for entity extraction")
        return entities
    
    if not isinstance(text, str):
        raise TextValidationError(f"Text must be string, got {type(text).__name__}")
    
    text = text.strip()
    if not text:
        logger.debug("Text contains only whitespace")
        return entities
    
    config = get_config()
    if len(text) < config.min_text_length:
        logger.debug(f"Text too short for entity extraction: {len(text)} chars")
        return entities
    
    try:
        # Load model if not provided
        if model is None:
            from src.nlp.model_manager import get_model_manager
            manager = get_model_manager()
            model = manager.get_ner_model()
        
        # Process text with spaCy
        logger.debug(f"Extracting entities from text of length {len(text)}")
        doc = model(text)
        
        # Extract entities from spaCy
        for ent in doc.ents:
            # Map spaCy label to our schema
            label = ENTITY_LABEL_MAP.get(ent.label_, None)
            
            if label is None:
                logger.debug(f"Ignoring unmatched entity label: {ent.label_}")
                continue
            
            entity_data = {
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "label": label,
                "original_label": ent.label_,
            }
            
            # Add confidence if available (some models provide this)
            if hasattr(ent, 'confidence'):
                entity_data["confidence"] = float(ent.confidence)
            
            entities[label].append(entity_data)
        
        # Rule-based dosage extraction
        if include_dosage:
            dosage_entities = _extract_dosages(text)
            entities["DOSAGE"].extend(dosage_entities)
        
        # Remove duplicates and sort by position
        for label in entities:
            entities[label] = _deduplicate_entities(entities[label])
            entities[label] = sorted(entities[label], key=lambda x: x["start"])
        
        # Log extraction summary
        total_entities = sum(len(ents) for ents in entities.values())
        logger.debug(
            f"Extracted {total_entities} entities: "
            f"DRUG={len(entities['DRUG'])}, "
            f"CONDITION={len(entities['CONDITION'])}, "
            f"DOSAGE={len(entities['DOSAGE'])}, "
            f"PROCEDURE={len(entities['PROCEDURE'])}"
        )
        
        return entities
        
    except Exception as e:
        logger.exception(f"Entity extraction failed: {e}")
        raise EntityExtractionError(
            f"Failed to extract entities: {str(e)}",
            text[:100]
        ) from e


def _extract_dosages(text: str) -> list[dict[str, Any]]:
    """
    Extract dosage information using rule-based patterns.
    
    Args:
        text: Input text
        
    Returns:
        List of dosage entity dictionaries
    """
    dosages = []
    
    for pattern in DOSAGE_PATTERNS:
        for match in pattern.finditer(text):
            dosage_data = {
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "label": "DOSAGE",
                "confidence": 0.9  # Rule-based extractions have high confidence
            }
            dosages.append(dosage_data)
    
    return dosages


def _deduplicate_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Remove duplicate entities based on overlapping text spans.
    
    Keeps the longer span when entities overlap.
    
    Args:
        entities: List of entity dictionaries
        
    Returns:
        Deduplicated list of entities
    """
    if not entities:
        return []
    
    # Sort by start position, then by length (descending)
    sorted_entities = sorted(
        entities,
        key=lambda x: (x["start"], -(x["end"] - x["start"]))
    )
    
    deduplicated = []
    last_end = -1
    
    for entity in sorted_entities:
        # If this entity doesn't overlap with the last kept entity, keep it
        if entity["start"] >= last_end:
            deduplicated.append(entity)
            last_end = entity["end"]
        # If it overlaps but is longer, replace the last one
        elif entity["end"] > last_end:
            # Check if we should replace based on confidence
            if deduplicated and entity.get("confidence", 0) > deduplicated[-1].get("confidence", 0):
                deduplicated[-1] = entity
                last_end = entity["end"]
    
    return deduplicated


def extract_entities_batch(
    texts: list[str],
    model: Any = None,
    include_dosage: bool = True
) -> list[dict[str, list[dict[str, Any]]]]:
    """
    Extract entities from multiple texts efficiently.
    
    Args:
        texts: List of input texts
        model: Optional pre-loaded spaCy model
        include_dosage: Whether to include dosage extraction
        
    Returns:
        List of entity dictionaries, one per input text
        
    Raises:
        EntityExtractionError: If batch extraction fails
    """
    if not texts:
        return []
    
    try:
        # Load model once for all texts
        if model is None:
            from src.nlp.model_manager import get_model_manager
            manager = get_model_manager()
            model = manager.get_ner_model()
        
        results = []
        for text in texts:
            try:
                entities = extract_entities(text, model=model, include_dosage=include_dosage)
                results.append(entities)
            except Exception as e:
                logger.warning(f"Failed to extract entities from one text: {e}")
                # Return empty result for failed text
                results.append({
                    "DRUG": [],
                    "CONDITION": [],
                    "DOSAGE": [],
                    "PROCEDURE": []
                })
        
        return results
        
    except Exception as e:
        logger.exception(f"Batch entity extraction failed: {e}")
        raise EntityExtractionError(f"Batch extraction failed: {str(e)}") from e


def get_entity_count(entities: dict[str, list]) -> dict[str, int]:
    """
    Get count of entities by label.
    
    Args:
        entities: Entity dictionary from extract_entities
        
    Returns:
        Dictionary mapping labels to counts
    """
    return {label: len(ent_list) for label, ent_list in entities.items()}


def filter_entities_by_confidence(
    entities: dict[str, list[dict[str, Any]]],
    min_confidence: float = 0.5
) -> dict[str, list[dict[str, Any]]]:
    """
    Filter entities by confidence threshold.
    
    Args:
        entities: Entity dictionary from extract_entities
        min_confidence: Minimum confidence score (0.0 to 1.0)
        
    Returns:
        Filtered entity dictionary
    """
    filtered = {}
    for label, ent_list in entities.items():
        filtered[label] = [
            ent for ent in ent_list
            if ent.get("confidence", 1.0) >= min_confidence
        ]
    return filtered


def merge_overlapping_entities(
    entities: dict[str, list[dict[str, Any]]]
) -> dict[str, list[dict[str, Any]]]:
    """
    Merge overlapping entities across all labels.
    
    Args:
        entities: Entity dictionary from extract_entities
        
    Returns:
        Entity dictionary with overlaps resolved
    """
    # Flatten all entities with their labels
    all_entities = []
    for label, ent_list in entities.items():
        for ent in ent_list:
            ent_copy = ent.copy()
            ent_copy["_label"] = label
            all_entities.append(ent_copy)
    
    # Deduplicate across all labels
    deduplicated = _deduplicate_entities(all_entities)
    
    # Group back by label
    result = {"DRUG": [], "CONDITION": [], "DOSAGE": [], "PROCEDURE": []}
    for ent in deduplicated:
        label = ent.pop("_label")
        result[label].append(ent)
    
    return result