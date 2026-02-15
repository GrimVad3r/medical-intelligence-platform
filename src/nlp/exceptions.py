"""NLP-specific exceptions."""


class NLPError(Exception):
    """Base for NLP errors."""


class ModelLoadError(NLPError):
    """Failed to load model."""
