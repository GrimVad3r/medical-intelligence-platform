"""
Integrated NLP Pipeline Processor.

Orchestrates the complete NLP workflow: entity extraction, classification,
entity linking, relationship analysis, and optional SHAP explanations.
"""

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.logger import get_logger
from src.nlp.config import get_config
from src.nlp.exceptions import (
    NLPError,
    TextValidationError,
    TextTooShortError,
    TextTooLongError,
    EntityExtractionError,
    ClassificationError,
    EntityLinkingError
)
from src.nlp.medical_ner import extract_entities
from src.nlp.text_classifier import classify
from src.nlp.entity_linker import link_entities
from src.nlp.semantic_analyzer import analyze_relationships

logger = get_logger(__name__)


class MessageProcessor:
    """
    Main NLP pipeline processor.
    
    Coordinates all NLP operations with proper error handling, caching,
    and retry logic.
    """
    
    def __init__(
        self,
        model_manager: Any = None,
        base_dir: Path | None = None,
        use_cache: bool | None = None
    ):
        """
        Initialize message processor.
        
        Args:
            model_manager: Optional ModelManager instance
            base_dir: Base directory for knowledge bases
            use_cache: Whether to enable caching (uses config default if None)
        """
        self.model_manager = model_manager
        self.base_dir = base_dir or Path("data/kb")
        
        config = get_config()
        self.use_cache = use_cache if use_cache is not None else config.cache_enabled
        self._cache: dict[str, dict[str, Any]] = {} if self.use_cache else None
        
        self.config = config
        
        # Statistics
        self._stats = {
            "total_processed": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_time": 0.0
        }
        
        logger.info(
            f"MessageProcessor initialized (cache={'enabled' if self.use_cache else 'disabled'})"
        )
    
    def process(
        self,
        text: str,
        include_explanations: bool = False,
        include_relationships: bool = False
    ) -> dict[str, Any]:
        """
        Run full NLP pipeline on text.
        
        Args:
            text: Input text to process
            include_explanations: Whether to include SHAP explanations
            include_relationships: Whether to analyze entity relationships
            
        Returns:
            Dictionary containing:
            - entities: Extracted entities by type
            - category: Text classification category
            - confidence: Classification confidence
            - linked_entities: Entities linked to knowledge base
            - relationships: Entity relationships (if enabled)
            - explanations: SHAP explanations (if enabled)
            - metadata: Processing metadata (timestamps, versions, etc.)
            
        Raises:
            TextValidationError: If text is invalid
            NLPError: If processing fails after retries
            
        Example:
            >>> processor = MessageProcessor()
            >>> result = processor.process("Patient prescribed 20mg Lisinopril for hypertension")
            >>> print(result["category"])
            "clinical"
        """
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_text(text)
            
            # Check cache
            if self._cache is not None:
                cache_key = self._get_cache_key(text, include_explanations, include_relationships)
                if cache_key in self._cache:
                    logger.debug(f"Cache hit for text hash {cache_key[:8]}")
                    self._stats["cache_hits"] += 1
                    return self._cache[cache_key]
            
            # Process with retry logic
            result = self._process_with_retry(
                text,
                include_explanations,
                include_relationships
            )
            
            # Add metadata
            result["metadata"] = {
                "processed_at": datetime.utcnow().isoformat(),
                "processing_time": time.time() - start_time,
                "model_version": self._get_model_version(),
                "cached": False
            }
            
            # Cache result
            if self._cache is not None:
                self._cache[cache_key] = result
            
            # Update statistics
            self._stats["total_processed"] += 1
            self._stats["total_time"] += time.time() - start_time
            
            logger.info(
                f"Processed text successfully in {time.time() - start_time:.3f}s "
                f"(category={result['category']}, entities={sum(len(v) for v in result['entities'].values())})"
            )
            
            return result
            
        except TextValidationError:
            # Don't retry validation errors
            raise
        except Exception as e:
            self._stats["errors"] += 1
            logger.exception(f"Processing failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((EntityExtractionError, ClassificationError, EntityLinkingError)),
        reraise=True
    )
    def _process_with_retry(
        self,
        text: str,
        include_explanations: bool,
        include_relationships: bool
    ) -> dict[str, Any]:
        """
        Process text with automatic retry on transient errors.
        
        Args:
            text: Input text
            include_explanations: Whether to include SHAP explanations
            include_relationships: Whether to analyze relationships
            
        Returns:
            Processing results dictionary
        """
        logger.debug(f"Processing text of length {len(text)}")
        
        # Step 1: Entity Extraction
        try:
            entities = extract_entities(text, model=self._get_ner_model())
            logger.debug(f"Extracted {sum(len(v) for v in entities.values())} entities")
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            raise EntityExtractionError(f"Entity extraction failed: {str(e)}") from e
        
        # Step 2: Text Classification
        try:
            classification = classify(text, model=self._get_classifier_model())
            logger.debug(f"Classified as {classification['category']} (confidence={classification['confidence']:.3f})")
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise ClassificationError(f"Classification failed: {str(e)}") from e
        
        # Step 3: Entity Linking
        try:
            linked = link_entities(entities, self.base_dir)
            linked_count = sum(
                1 for label_entities in linked.values()
                for entity in label_entities
                if entity.get("kb_id") is not None
            )
            logger.debug(f"Linked {linked_count} entities to knowledge base")
        except Exception as e:
            logger.error(f"Entity linking failed: {e}")
            # Entity linking failure is not critical, continue with unlinked entities
            linked = entities
        
        # Build base result
        result = {
            "entities": entities,
            "category": classification.get("category"),
            "confidence": classification.get("confidence"),
            "linked_entities": linked,
        }
        
        # Step 4: Relationship Analysis (optional)
        if include_relationships:
            try:
                relationships = analyze_relationships(entities, text)
                result["relationships"] = relationships
                logger.debug(f"Extracted {len(relationships)} relationships")
            except Exception as e:
                logger.warning(f"Relationship analysis failed: {e}")
                result["relationships"] = []
        
        # Step 5: SHAP Explanations (optional)
        if include_explanations and self.config.enable_shap:
            try:
                from src.nlp.shap_explainer import explain
                result["explanations"] = explain(text, model=self._get_classifier_model())
                logger.debug("Generated SHAP explanations")
            except Exception as e:
                logger.warning(f"SHAP explanation skipped: {e}")
                result["explanations"] = None
        
        return result
    
    def process_batch(
        self,
        texts: list[str],
        include_explanations: bool = False,
        include_relationships: bool = False,
        fail_fast: bool = False
    ) -> list[dict[str, Any]]:
        """
        Process multiple texts efficiently.
        
        Args:
            texts: List of input texts
            include_explanations: Whether to include SHAP explanations
            include_relationships: Whether to analyze relationships
            fail_fast: If True, stop on first error; if False, continue and collect errors
            
        Returns:
            List of processing results (None for failed items if fail_fast=False)
            
        Raises:
            NLPError: If fail_fast=True and any processing fails
        """
        if not texts:
            return []
        
        logger.info(f"Processing batch of {len(texts)} texts")
        start_time = time.time()
        
        results = []
        errors = []
        
        for i, text in enumerate(texts):
            try:
                result = self.process(
                    text,
                    include_explanations=include_explanations,
                    include_relationships=include_relationships
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process text {i+1}/{len(texts)}: {e}")
                
                if fail_fast:
                    raise
                
                errors.append((i, text[:100], str(e)))
                results.append(None)
        
        elapsed = time.time() - start_time
        success_count = len([r for r in results if r is not None])
        
        logger.info(
            f"Batch processing complete: {success_count}/{len(texts)} successful "
            f"in {elapsed:.2f}s ({len(texts)/elapsed:.1f} texts/sec)"
        )
        
        if errors:
            logger.warning(f"{len(errors)} texts failed processing")
        
        return results
    
    def _validate_text(self, text: str) -> None:
        """
        Validate input text.
        
        Args:
            text: Text to validate
            
        Raises:
            TextValidationError: If text is invalid
            TextTooShortError: If text is too short
            TextTooLongError: If text is too long
        """
        if not text:
            raise TextValidationError("Empty text provided")
        
        if not isinstance(text, str):
            raise TextValidationError(f"Text must be string, got {type(text).__name__}")
        
        text = text.strip()
        if not text:
            raise TextValidationError("Text contains only whitespace")
        
        if len(text) < self.config.min_text_length:
            raise TextTooShortError(len(text), self.config.min_text_length)
        
        if len(text) > self.config.max_text_length:
            raise TextTooLongError(len(text), self.config.max_text_length)
    
    def _get_cache_key(
        self,
        text: str,
        include_explanations: bool,
        include_relationships: bool
    ) -> str:
        """
        Generate cache key for text and processing options.
        
        Args:
            text: Input text
            include_explanations: Explanations flag
            include_relationships: Relationships flag
            
        Returns:
            Cache key string
        """
        key_data = f"{text}|{include_explanations}|{include_relationships}|{self._get_model_version()}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_ner_model(self) -> Any:
        """Get NER model from model manager."""
        if self.model_manager is None:
            from src.nlp.model_manager import get_model_manager
            self.model_manager = get_model_manager()
        return self.model_manager.get_ner_model()
    
    def _get_classifier_model(self) -> Any:
        """Get classifier model from model manager."""
        if self.model_manager is None:
            from src.nlp.model_manager import get_model_manager
            self.model_manager = get_model_manager()
        return self.model_manager.get_classifier_model()
    
    def _get_model_version(self) -> str:
        """Get current model version string."""
        if self.model_manager:
            return self.model_manager.get_version_string()
        return self.config.get_model_version_string()
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Get processor statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        stats = self._stats.copy()
        
        if stats["total_processed"] > 0:
            stats["avg_time"] = stats["total_time"] / stats["total_processed"]
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_processed"]
            stats["error_rate"] = stats["errors"] / (stats["total_processed"] + stats["errors"])
        else:
            stats["avg_time"] = 0.0
            stats["cache_hit_rate"] = 0.0
            stats["error_rate"] = 0.0
        
        return stats
    
    def clear_cache(self) -> int:
        """
        Clear the processing cache.
        
        Returns:
            Number of cache entries cleared
        """
        if self._cache is None:
            return 0
        
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def reset_statistics(self) -> None:
        """Reset processor statistics."""
        self._stats = {
            "total_processed": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_time": 0.0
        }
        logger.info("Statistics reset")