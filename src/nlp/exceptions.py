"""
NLP-specific exception hierarchy.

Provides structured exception classes for different types of NLP errors,
enabling better error handling and debugging.
"""

from typing import Any


class NLPError(Exception):
    """Base exception for all NLP-related errors."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        Initialize NLP error.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ModelLoadError(NLPError):
    """Failed to load an NLP model."""
    
    def __init__(self, model_name: str, reason: str, details: dict[str, Any] | None = None):
        """
        Initialize model load error.
        
        Args:
            model_name: Name of the model that failed to load
            reason: Reason for the failure
            details: Additional context
        """
        message = f"Failed to load model '{model_name}': {reason}"
        details = details or {}
        details["model_name"] = model_name
        super().__init__(message, details)
        self.model_name = model_name
        self.reason = reason


class ModelNotFoundError(ModelLoadError):
    """Model not found at specified path."""
    
    def __init__(self, model_name: str, path: str):
        """
        Initialize model not found error.
        
        Args:
            model_name: Name of the missing model
            path: Path where model was expected
        """
        super().__init__(
            model_name,
            f"Model not found at path: {path}",
            {"path": path}
        )


class TextValidationError(NLPError):
    """Input text failed validation."""
    
    def __init__(self, reason: str, text_preview: str | None = None):
        """
        Initialize text validation error.
        
        Args:
            reason: Why the text failed validation
            text_preview: Optional preview of the invalid text (first 100 chars)
        """
        details = {}
        if text_preview:
            details["preview"] = text_preview[:100]
        super().__init__(f"Text validation failed: {reason}", details)
        self.reason = reason


class TextTooShortError(TextValidationError):
    """Input text is too short for processing."""
    
    def __init__(self, length: int, min_length: int):
        """
        Initialize text too short error.
        
        Args:
            length: Actual text length
            min_length: Minimum required length
        """
        super().__init__(
            f"Text too short ({length} chars, minimum {min_length})"
        )
        self.length = length
        self.min_length = min_length


class TextTooLongError(TextValidationError):
    """Input text exceeds maximum length."""
    
    def __init__(self, length: int, max_length: int):
        """
        Initialize text too long error.
        
        Args:
            length: Actual text length
            max_length: Maximum allowed length
        """
        super().__init__(
            f"Text too long ({length} chars, maximum {max_length})"
        )
        self.length = length
        self.max_length = max_length


class EntityExtractionError(NLPError):
    """Error during entity extraction."""
    
    def __init__(self, reason: str, text_preview: str | None = None):
        """
        Initialize entity extraction error.
        
        Args:
            reason: Description of what went wrong
            text_preview: Optional preview of the text being processed
        """
        details = {}
        if text_preview:
            details["preview"] = text_preview[:100]
        super().__init__(f"Entity extraction failed: {reason}", details)


class ClassificationError(NLPError):
    """Error during text classification."""
    
    def __init__(self, reason: str, model_name: str | None = None):
        """
        Initialize classification error.
        
        Args:
            reason: Description of what went wrong
            model_name: Optional name of the classifier that failed
        """
        details = {}
        if model_name:
            details["model"] = model_name
        super().__init__(f"Classification failed: {reason}", details)


class EntityLinkingError(NLPError):
    """Error during entity linking to knowledge base."""
    
    def __init__(self, reason: str, entity_text: str | None = None):
        """
        Initialize entity linking error.
        
        Args:
            reason: Description of what went wrong
            entity_text: Optional text of the entity that failed to link
        """
        details = {}
        if entity_text:
            details["entity"] = entity_text
        super().__init__(f"Entity linking failed: {reason}", details)


class KnowledgeBaseError(NLPError):
    """Error related to knowledge base operations."""
    
    def __init__(self, kb_name: str, reason: str):
        """
        Initialize knowledge base error.
        
        Args:
            kb_name: Name of the knowledge base
            reason: Description of what went wrong
        """
        super().__init__(
            f"Knowledge base '{kb_name}' error: {reason}",
            {"kb_name": kb_name}
        )
        self.kb_name = kb_name


class KnowledgeBaseNotFoundError(KnowledgeBaseError):
    """Knowledge base file not found."""
    
    def __init__(self, kb_name: str, path: str):
        """
        Initialize KB not found error.
        
        Args:
            kb_name: Name of the knowledge base
            path: Path where KB was expected
        """
        super().__init__(kb_name, f"Not found at path: {path}")
        self.path = path


class ProcessingTimeoutError(NLPError):
    """Processing exceeded maximum allowed time."""
    
    def __init__(self, operation: str, timeout_seconds: float):
        """
        Initialize timeout error.
        
        Args:
            operation: Name of the operation that timed out
            timeout_seconds: Maximum allowed time that was exceeded
        """
        super().__init__(
            f"Operation '{operation}' exceeded timeout of {timeout_seconds}s",
            {"operation": operation, "timeout": timeout_seconds}
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class BatchProcessingError(NLPError):
    """Error during batch processing of multiple texts."""
    
    def __init__(self, batch_size: int, failed_count: int, errors: list[Exception]):
        """
        Initialize batch processing error.
        
        Args:
            batch_size: Total size of the batch
            failed_count: Number of items that failed
            errors: List of individual errors
        """
        super().__init__(
            f"Batch processing failed: {failed_count}/{batch_size} items failed",
            {"batch_size": batch_size, "failed_count": failed_count}
        )
        self.batch_size = batch_size
        self.failed_count = failed_count
        self.errors = errors


class ModelInferenceError(NLPError):
    """Error during model inference/prediction."""
    
    def __init__(self, model_name: str, reason: str):
        """
        Initialize model inference error.
        
        Args:
            model_name: Name of the model that failed during inference
            reason: Description of what went wrong
        """
        super().__init__(
            f"Model '{model_name}' inference failed: {reason}",
            {"model_name": model_name}
        )
        self.model_name = model_name


class ConfigurationError(NLPError):
    """Invalid configuration provided."""
    
    def __init__(self, parameter: str, value: Any, reason: str):
        """
        Initialize configuration error.
        
        Args:
            parameter: Name of the invalid configuration parameter
            value: The invalid value
            reason: Why the value is invalid
        """
        super().__init__(
            f"Invalid configuration for '{parameter}': {reason}",
            {"parameter": parameter, "value": str(value)}
        )
        self.parameter = parameter
        self.value = value