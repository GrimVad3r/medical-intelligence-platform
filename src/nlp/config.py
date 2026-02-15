"""
NLP Configuration Management.

Provides centralized configuration for all NLP components with environment
variable support, validation, and type safety.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NLPConfig:
    """Central configuration for NLP pipeline."""
    
    # Model paths
    model_path: Path = field(
        default_factory=lambda: Path(os.environ.get("NLP_MODEL_PATH", "data/nlp_models"))
    )
    
    # Device configuration
    device: Literal["cpu", "cuda", "mps"] = field(
        default_factory=lambda: os.environ.get("NLP_DEVICE", "cpu")
    )
    
    # Processing configuration
    batch_size: int = field(
        default_factory=lambda: int(os.environ.get("NLP_BATCH_SIZE", "32"))
    )
    max_text_length: int = field(
        default_factory=lambda: int(os.environ.get("NLP_MAX_TEXT_LENGTH", "50000"))
    )
    min_text_length: int = field(
        default_factory=lambda: int(os.environ.get("NLP_MIN_TEXT_LENGTH", "3"))
    )
    
    # Model versions
    ner_model: str = field(
        default_factory=lambda: os.environ.get("NLP_NER_MODEL", "en_core_sci_md")
    )
    classifier_model: str = field(
        default_factory=lambda: os.environ.get(
            "NLP_CLASSIFIER_MODEL",
            "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
        )
    )
    
    # Feature flags
    cache_enabled: bool = field(
        default_factory=lambda: os.environ.get("NLP_CACHE_ENABLED", "true").lower() == "true"
    )
    enable_shap: bool = field(
        default_factory=lambda: os.environ.get("NLP_ENABLE_SHAP", "false").lower() == "true"
    )
    
    # Retry configuration
    retry_attempts: int = field(
        default_factory=lambda: int(os.environ.get("NLP_RETRY_ATTEMPTS", "3"))
    )
    retry_min_wait: int = field(
        default_factory=lambda: int(os.environ.get("NLP_RETRY_MIN_WAIT", "2"))
    )
    retry_max_wait: int = field(
        default_factory=lambda: int(os.environ.get("NLP_RETRY_MAX_WAIT", "10"))
    )
    
    # Entity linking configuration
    entity_link_threshold: float = field(
        default_factory=lambda: float(os.environ.get("NLP_ENTITY_LINK_THRESHOLD", "80.0"))
    )
    
    # Knowledge base paths
    drug_kb_path: Path = field(
        default_factory=lambda: Path(os.environ.get("NLP_DRUG_KB_PATH", "data/kb/drug_database.json"))
    )
    condition_kb_path: Path = field(
        default_factory=lambda: Path(os.environ.get("NLP_CONDITION_KB_PATH", "data/kb/medical_terms.json"))
    )
    procedure_kb_path: Path = field(
        default_factory=lambda: Path(os.environ.get("NLP_PROCEDURE_KB_PATH", "data/kb/procedures.json"))
    )
    
    # Performance tuning
    num_workers: int = field(
        default_factory=lambda: int(os.environ.get("NLP_NUM_WORKERS", "4"))
    )
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
        self._log_config()
    
    def _validate(self) -> None:
        """Validate configuration values."""
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        
        if self.max_text_length < self.min_text_length:
            raise ValueError(
                f"max_text_length ({self.max_text_length}) must be >= "
                f"min_text_length ({self.min_text_length})"
            )
        
        if not 0 <= self.entity_link_threshold <= 100:
            raise ValueError(
                f"entity_link_threshold must be between 0-100, got {self.entity_link_threshold}"
            )
        
        if self.device not in ["cpu", "cuda", "mps"]:
            logger.warning(f"Unknown device '{self.device}', using 'cpu'")
            self.device = "cpu"
        
        # Create model directory if it doesn't exist
        self.model_path.mkdir(parents=True, exist_ok=True)
    
    def _log_config(self) -> None:
        """Log current configuration."""
        logger.info("NLP Configuration loaded:")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  Batch size: {self.batch_size}")
        logger.info(f"  NER model: {self.ner_model}")
        logger.info(f"  Classifier model: {self.classifier_model}")
        logger.info(f"  Cache enabled: {self.cache_enabled}")
        logger.info(f"  SHAP enabled: {self.enable_shap}")
    
    @classmethod
    def from_env(cls) -> "NLPConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            NLPConfig instance with values loaded from environment
        """
        return cls()
    
    def get_model_version_string(self) -> str:
        """
        Get a string representation of all model versions.
        
        Returns:
            Version string in format "ner:model_name,clf:model_name"
        """
        return f"ner:{self.ner_model},clf:{self.classifier_model}"


# Global configuration instance
_config: NLPConfig | None = None


def get_config() -> NLPConfig:
    """
    Get or create the global configuration instance.
    
    Returns:
        Global NLPConfig instance
    """
    global _config
    if _config is None:
        _config = NLPConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset global configuration (useful for testing)."""
    global _config
    _config = None


# Legacy support - keep these for backwards compatibility
NLP_MODEL_PATH = Path(os.environ.get("NLP_MODEL_PATH", "data/nlp_models"))
NLP_DEVICE = os.environ.get("NLP_DEVICE", "cpu")
NLP_BATCH_SIZE = int(os.environ.get("NLP_BATCH_SIZE", "32"))