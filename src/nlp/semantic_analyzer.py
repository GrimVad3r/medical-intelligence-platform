"""
Semantic Relationship Analysis.

Analyzes relationships between extracted entities using rule-based and
model-based approaches.
"""

import re
from typing import Any

from src.logger import get_logger

logger = get_logger(__name__)


# Relationship patterns (drug-condition relationships)
RELATIONSHIP_PATTERNS = [
    # Drug treats condition
    (r'(\w+)\s+(?:for|treats?|treating|manages?|managing)\s+(\w+)', 'TREATS'),
    (r'(\w+)\s+(?:to treat|to manage)\s+(\w+)', 'TREATS'),
    
    # Drug causes condition (side effect)
    (r'(\w+)\s+(?:causes?|caused|causing)\s+(\w+)', 'CAUSES'),
    (r'(\w+)\s+(?:may cause|can cause)\s+(\w+)', 'CAUSES'),
    (r'side effects?\s+(?:of\s+)?(\w+).*?(\w+)', 'CAUSES'),
    
    # Drug prevents condition
    (r'(\w+)\s+(?:prevents?|preventing|prevention of)\s+(\w+)', 'PREVENTS'),
    (r'(\w+)\s+(?:to prevent)\s+(\w+)', 'PREVENTS'),
    
    # Condition requires drug
    (r'(\w+)\s+(?:requires?|requiring|needs?)\s+(\w+)', 'REQUIRES'),
    (r'(\w+)\s+(?:is treated with)\s+(\w+)', 'REQUIRES'),
    
    # Dosage relationship
    (r'(\d+\s*(?:mg|g|ml))\s+(?:of\s+)?(\w+)', 'DOSAGE_OF'),
]


def analyze_relationships(
    entities: dict[str, list],
    text: str,
    use_rules: bool = True,
    use_model: bool = False
) -> list[dict[str, Any]]:
    """
    Extract relationships between entities in text.
    
    Args:
        entities: Dictionary of extracted entities from medical_ner
        text: Original text that was analyzed
        use_rules: Whether to use rule-based extraction
        use_model: Whether to use model-based extraction (not yet implemented)
        
    Returns:
        List of relationship dictionaries, each containing:
        - head: Source entity text
        - head_type: Type of head entity (DRUG, CONDITION, etc.)
        - tail: Target entity text
        - tail_type: Type of tail entity
        - relation: Relationship type (TREATS, CAUSES, etc.)
        - confidence: Confidence score (0.0-1.0)
        - evidence: Text span supporting the relationship
        
    Example:
        >>> entities = {
        ...     "DRUG": [{"text": "Lisinopril", "start": 20, "end": 30}],
        ...     "CONDITION": [{"text": "hypertension", "start": 35, "end": 47}]
        ... }
        >>> text = "Patient prescribed Lisinopril for hypertension"
        >>> relationships = analyze_relationships(entities, text)
        >>> print(relationships)
        [{
            "head": "Lisinopril",
            "head_type": "DRUG",
            "tail": "hypertension",
            "tail_type": "CONDITION",
            "relation": "TREATS",
            "confidence": 0.85,
            "evidence": "Lisinopril for hypertension"
        }]
    """
    relationships = []
    
    if not entities or not text:
        return relationships
    
    # Rule-based extraction
    if use_rules:
        relationships.extend(_extract_relationships_rules(entities, text))
    
    # Model-based extraction (placeholder for future implementation)
    if use_model:
        try:
            relationships.extend(_extract_relationships_model(entities, text))
        except Exception as e:
            logger.warning(f"Model-based relationship extraction failed: {e}")
    
    # Deduplicate relationships
    relationships = _deduplicate_relationships(relationships)
    
    logger.debug(f"Extracted {len(relationships)} relationships")
    
    return relationships


def _extract_relationships_rules(
    entities: dict[str, list],
    text: str
) -> list[dict[str, Any]]:
    """
    Extract relationships using rule-based patterns.
    
    Args:
        entities: Extracted entities
        text: Original text
        
    Returns:
        List of relationship dictionaries
    """
    relationships = []
    text_lower = text.lower()
    
    # Build entity position index for quick lookup
    entity_positions = {}
    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            entity_text = entity.get("text", "")
            if entity_text:
                entity_positions[entity_text.lower()] = {
                    "text": entity_text,
                    "type": entity_type,
                    "start": entity.get("start", 0),
                    "end": entity.get("end", 0)
                }
    
    # Apply pattern matching
    for pattern, relation_type in RELATIONSHIP_PATTERNS:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            head_text = match.group(1).strip()
            tail_text = match.group(2).strip()
            
            # Look up entities
            head_entity = entity_positions.get(head_text)
            tail_entity = entity_positions.get(tail_text)
            
            # Only create relationship if both entities exist
            if head_entity and tail_entity:
                relationship = {
                    "head": head_entity["text"],
                    "head_type": head_entity["type"],
                    "tail": tail_entity["text"],
                    "tail_type": tail_entity["type"],
                    "relation": relation_type,
                    "confidence": 0.75,  # Rule-based confidence
                    "evidence": match.group(0),
                    "method": "rule-based"
                }
                relationships.append(relationship)
    
    # Extract proximity-based relationships
    relationships.extend(_extract_proximity_relationships(entities, text))
    
    return relationships


def _extract_proximity_relationships(
    entities: dict[str, list],
    text: str
) -> list[dict[str, Any]]:
    """
    Extract relationships based on entity proximity in text.
    
    Entities that appear close together are likely to be related.
    
    Args:
        entities: Extracted entities
        text: Original text
        
    Returns:
        List of relationship dictionaries
    """
    relationships = []
    proximity_threshold = 50  # characters
    
    # Get all entities with positions
    all_entities = []
    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            if "start" in entity and "end" in entity:
                all_entities.append({
                    "text": entity.get("text", ""),
                    "type": entity_type,
                    "start": entity["start"],
                    "end": entity["end"]
                })
    
    # Sort by position
    all_entities.sort(key=lambda x: x["start"])
    
    # Find nearby entity pairs
    for i, entity1 in enumerate(all_entities):
        for entity2 in all_entities[i+1:]:
            # Calculate distance
            distance = entity2["start"] - entity1["end"]
            
            if distance > proximity_threshold:
                break  # Too far, no need to check further
            
            if distance < 0:
                continue  # Overlapping, skip
            
            # Create proximity-based relationship
            # Confidence decreases with distance
            confidence = max(0.3, 1.0 - (distance / proximity_threshold) * 0.5)
            
            # Infer likely relationship type based on entity types
            relation_type = _infer_relation_type(entity1["type"], entity2["type"])
            
            if relation_type:
                relationship = {
                    "head": entity1["text"],
                    "head_type": entity1["type"],
                    "tail": entity2["text"],
                    "tail_type": entity2["type"],
                    "relation": relation_type,
                    "confidence": confidence,
                    "evidence": text[entity1["start"]:entity2["end"]],
                    "method": "proximity"
                }
                relationships.append(relationship)
    
    return relationships


def _infer_relation_type(head_type: str, tail_type: str) -> str | None:
    """
    Infer relationship type based on entity types.
    
    Args:
        head_type: Type of head entity
        tail_type: Type of tail entity
        
    Returns:
        Inferred relation type or None
    """
    # Common patterns
    if head_type == "DRUG" and tail_type == "CONDITION":
        return "TREATS"
    elif head_type == "DRUG" and tail_type == "DOSAGE":
        return "HAS_DOSAGE"
    elif head_type == "CONDITION" and tail_type == "PROCEDURE":
        return "REQUIRES"
    elif head_type == "DOSAGE" and tail_type == "DRUG":
        return "DOSAGE_OF"
    
    return "RELATED_TO"  # Generic relationship


def _extract_relationships_model(
    entities: dict[str, list],
    text: str
) -> list[dict[str, Any]]:
    """
    Extract relationships using a trained model.
    
    This is a placeholder for future implementation using models like:
    - BioBERT for relation extraction
    - SpanBERT
    - Custom trained models
    
    Args:
        entities: Extracted entities
        text: Original text
        
    Returns:
        List of relationship dictionaries
    """
    # Placeholder - to be implemented
    logger.debug("Model-based relationship extraction not yet implemented")
    return []


def _deduplicate_relationships(
    relationships: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Remove duplicate relationships, keeping the one with highest confidence.
    
    Args:
        relationships: List of relationship dictionaries
        
    Returns:
        Deduplicated list
    """
    if not relationships:
        return []
    
    # Create unique key for each relationship
    unique_rels = {}
    
    for rel in relationships:
        key = (
            rel["head"].lower(),
            rel["tail"].lower(),
            rel["relation"]
        )
        
        # Keep the relationship with highest confidence
        if key not in unique_rels or rel["confidence"] > unique_rels[key]["confidence"]:
            unique_rels[key] = rel
    
    return list(unique_rels.values())


def get_relationship_graph(
    relationships: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Convert relationships to a graph structure.
    
    Args:
        relationships: List of relationship dictionaries
        
    Returns:
        Graph dictionary with nodes and edges
    """
    nodes = set()
    edges = []
    
    for rel in relationships:
        # Add nodes
        nodes.add((rel["head"], rel["head_type"]))
        nodes.add((rel["tail"], rel["tail_type"]))
        
        # Add edge
        edges.append({
            "source": rel["head"],
            "target": rel["tail"],
            "relation": rel["relation"],
            "confidence": rel["confidence"]
        })
    
    return {
        "nodes": [{"id": node[0], "type": node[1]} for node in nodes],
        "edges": edges
    }


def filter_relationships_by_type(
    relationships: list[dict[str, Any]],
    relation_types: list[str]
) -> list[dict[str, Any]]:
    """
    Filter relationships by relation type.
    
    Args:
        relationships: List of relationship dictionaries
        relation_types: List of relation types to keep
        
    Returns:
        Filtered list of relationships
    """
    return [
        rel for rel in relationships
        if rel["relation"] in relation_types
    ]


def filter_relationships_by_confidence(
    relationships: list[dict[str, Any]],
    min_confidence: float = 0.5
) -> list[dict[str, Any]]:
    """
    Filter relationships by minimum confidence.
    
    Args:
        relationships: List of relationship dictionaries
        min_confidence: Minimum confidence threshold
        
    Returns:
        Filtered list of relationships
    """
    return [
        rel for rel in relationships
        if rel["confidence"] >= min_confidence
    ]