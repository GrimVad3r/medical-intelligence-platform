"""
Medical Text Classification.

Classifies medical text into categories using transformer-based models
trained on biomedical literature.
"""

from typing import Any

from src.logger import get_logger
from src.nlp.exceptions import ClassificationError, TextValidationError
from src.nlp.config import get_config

logger = get_logger(__name__)


# Category mappings - adjust based on your specific use case
CATEGORY_LABELS = {
    "LABEL_0": "general",
    "LABEL_1": "query",
    "LABEL_2": "product",
    "LABEL_3": "complaint",
    "LABEL_4": "adverse_event",
    "LABEL_5": "clinical",
}


def classify(
    text: str,
    model: Any = None,
    return_all_scores: bool = False
) -> dict[str, Any]:
    """
    Classify medical text into predefined categories.
    
    Args:
        text: Input text to classify
        model: Optional pre-loaded classifier model
        return_all_scores: If True, return scores for all categories
        
    Returns:
        Dictionary with classification results containing:
        - category: Predicted category (str)
        - confidence: Confidence score (float, 0.0-1.0)
        - all_scores: Optional list of all category scores
        
    Raises:
        TextValidationError: If text is invalid
        ClassificationError: If classification fails
        
    Example:
        >>> result = classify("Patient experiencing severe headache")
        >>> print(result)
        {"category": "clinical", "confidence": 0.92}
    """
    # Validate input
    if not text:
        logger.debug("Empty text provided for classification")
        return {"category": "unknown", "confidence": 0.0}
    
    if not isinstance(text, str):
        raise TextValidationError(f"Text must be string, got {type(text).__name__}")
    
    text = text.strip()
    if not text:
        logger.debug("Text contains only whitespace")
        return {"category": "unknown", "confidence": 0.0}
    
    config = get_config()
    if len(text) < config.min_text_length:
        logger.debug(f"Text too short for classification: {len(text)} chars")
        return {"category": "unknown", "confidence": 0.0}
    
    # Truncate if too long
    original_length = len(text)
    if len(text) > config.max_text_length:
        logger.warning(f"Text truncated from {original_length} to {config.max_text_length} chars")
        text = text[:config.max_text_length]
    
    try:
        # Load model if not provided
        if model is None:
            from src.nlp.model_manager import get_model_manager
            manager = get_model_manager()
            model = manager.get_classifier_model()
        
        # Run classification
        logger.debug(f"Classifying text of length {len(text)}")
        
        # The model expects a list for batch processing
        results = model([text], truncation=True, max_length=512)
        
        if not results or len(results) == 0:
            raise ClassificationError(
                "Model returned empty results",
                config.classifier_model
            )
        
        # Extract result (first item since we passed a single text)
        result = results[0]
        
        # Process the result
        if return_all_scores:
            # Get all scores if model supports it
            if isinstance(result, list):
                all_scores = [
                    {
                        "label": _map_label(item.get("label", "unknown")),
                        "score": float(item.get("score", 0.0))
                    }
                    for item in result
                ]
                # Sort by score descending
                all_scores = sorted(all_scores, key=lambda x: x["score"], reverse=True)
                
                classification_result = {
                    "category": all_scores[0]["label"],
                    "confidence": all_scores[0]["score"],
                    "all_scores": all_scores
                }
            else:
                # Single result
                category = _map_label(result.get("label", "unknown"))
                confidence = float(result.get("score", 0.0))
                
                classification_result = {
                    "category": category,
                    "confidence": confidence,
                    "all_scores": [{"label": category, "score": confidence}]
                }
        else:
            # Just return top prediction
            if isinstance(result, list):
                result = result[0]  # Take top prediction
            
            category = _map_label(result.get("label", "unknown"))
            confidence = float(result.get("score", 0.0))
            
            classification_result = {
                "category": category,
                "confidence": confidence
            }
        
        logger.debug(
            f"Classification complete: {classification_result['category']} "
            f"(confidence: {classification_result['confidence']:.3f})"
        )
        
        return classification_result
        
    except Exception as e:
        logger.exception(f"Classification failed: {e}")
        raise ClassificationError(
            f"Failed to classify text: {str(e)}",
            config.classifier_model
        ) from e


def _map_label(label: str) -> str:
    """
    Map model output label to human-readable category.
    
    Args:
        label: Raw label from model
        
    Returns:
        Mapped category name
    """
    # Try direct mapping first
    if label in CATEGORY_LABELS:
        return CATEGORY_LABELS[label]
    
    # Try lowercase
    label_lower = label.lower()
    if label_lower in CATEGORY_LABELS:
        return CATEGORY_LABELS[label_lower]
    
    # Try to extract LABEL_N pattern
    if label.startswith("LABEL_"):
        return CATEGORY_LABELS.get(label, "general")
    
    # Return as-is if no mapping found
    return label.lower()


def classify_batch(
    texts: list[str],
    model: Any = None,
    return_all_scores: bool = False
) -> list[dict[str, Any]]:
    """
    Classify multiple texts efficiently.
    
    Args:
        texts: List of input texts
        model: Optional pre-loaded classifier model
        return_all_scores: If True, return scores for all categories
        
    Returns:
        List of classification result dictionaries
        
    Raises:
        ClassificationError: If batch classification fails
    """
    if not texts:
        return []
    
    try:
        # Load model once for all texts
        if model is None:
            from src.nlp.model_manager import get_model_manager
            manager = get_model_manager()
            model = manager.get_classifier_model()
        
        config = get_config()
        
        # Validate and preprocess texts
        processed_texts = []
        valid_indices = []
        
        for i, text in enumerate(texts):
            if text and isinstance(text, str) and len(text.strip()) >= config.min_text_length:
                # Truncate if needed
                processed_text = text.strip()
                if len(processed_text) > config.max_text_length:
                    processed_text = processed_text[:config.max_text_length]
                processed_texts.append(processed_text)
                valid_indices.append(i)
            else:
                # Will be filled with default later
                pass
        
        # Run batch classification
        logger.debug(f"Classifying batch of {len(processed_texts)} texts")
        
        if processed_texts:
            batch_results = model(processed_texts, truncation=True, max_length=512)
        else:
            batch_results = []
        
        # Construct results array
        results = []
        valid_result_idx = 0
        
        for i in range(len(texts)):
            if i in valid_indices:
                # Process valid result
                result = batch_results[valid_result_idx]
                valid_result_idx += 1
                
                if isinstance(result, list):
                    result = result[0]  # Take top prediction
                
                category = _map_label(result.get("label", "unknown"))
                confidence = float(result.get("score", 0.0))
                
                classification_result = {
                    "category": category,
                    "confidence": confidence
                }
                
                if return_all_scores and isinstance(batch_results[valid_result_idx - 1], list):
                    all_scores = [
                        {
                            "label": _map_label(item.get("label", "unknown")),
                            "score": float(item.get("score", 0.0))
                        }
                        for item in batch_results[valid_result_idx - 1]
                    ]
                    classification_result["all_scores"] = sorted(
                        all_scores,
                        key=lambda x: x["score"],
                        reverse=True
                    )
                
                results.append(classification_result)
            else:
                # Invalid text
                results.append({"category": "unknown", "confidence": 0.0})
        
        return results
        
    except Exception as e:
        logger.exception(f"Batch classification failed: {e}")
        raise ClassificationError(f"Batch classification failed: {str(e)}") from e


def get_category_distribution(
    classification_results: list[dict[str, Any]]
) -> dict[str, int]:
    """
    Get distribution of categories from classification results.
    
    Args:
        classification_results: List of classification result dicts
        
    Returns:
        Dictionary mapping categories to counts
    """
    distribution: dict[str, int] = {}
    
    for result in classification_results:
        category = result.get("category", "unknown")
        distribution[category] = distribution.get(category, 0) + 1
    
    return distribution


def filter_by_confidence(
    classification_results: list[dict[str, Any]],
    min_confidence: float = 0.5
) -> list[dict[str, Any]]:
    """
    Filter classification results by minimum confidence.
    
    Args:
        classification_results: List of classification result dicts
        min_confidence: Minimum confidence threshold (0.0 to 1.0)
        
    Returns:
        Filtered list of results
    """
    return [
        result for result in classification_results
        if result.get("confidence", 0.0) >= min_confidence
    ]


def get_top_categories(
    classification_results: list[dict[str, Any]],
    top_n: int = 5
) -> list[tuple[str, int, float]]:
    """
    Get top N categories by frequency with average confidence.
    
    Args:
        classification_results: List of classification result dicts
        top_n: Number of top categories to return
        
    Returns:
        List of tuples (category, count, avg_confidence)
    """
    from collections import defaultdict
    
    category_stats = defaultdict(lambda: {"count": 0, "total_confidence": 0.0})
    
    for result in classification_results:
        category = result.get("category", "unknown")
        confidence = result.get("confidence", 0.0)
        
        category_stats[category]["count"] += 1
        category_stats[category]["total_confidence"] += confidence
    
    # Calculate averages and sort
    results = []
    for category, stats in category_stats.items():
        count = stats["count"]
        avg_confidence = stats["total_confidence"] / count if count > 0 else 0.0
        results.append((category, count, avg_confidence))
    
    # Sort by count (descending) then by confidence (descending)
    results.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    return results[:top_n]