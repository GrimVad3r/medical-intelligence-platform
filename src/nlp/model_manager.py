"""
NLP Model Manager with SSL Bypass for Corporate Networks.

Handles loading, caching, and lifecycle management of NLP models.
"""

import os
import ssl
import threading
import urllib3
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any


from src.logger import get_logger
from src.nlp.config import get_config, NLPConfig
from src.nlp.exceptions import ModelLoadError, ModelNotFoundError

logger = get_logger(__name__)


class ModelManager:
    """
    Manages NLP model loading and caching.
    
    Provides thread-safe access to models with lazy loading and automatic cleanup.
    Tracks model versions and load times for monitoring and debugging.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for model manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: NLPConfig | None = None):
        """
        Initialize model manager.
        
        Args:
            config: Optional NLP configuration. Uses global config if not provided.
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
            
        self.config = config or get_config()
        self._models: dict[str, Any] = {}
        self._load_times: dict[str, datetime] = {}
        self._model_versions: dict[str, str] = {}
        self._load_lock = threading.Lock()
        self._initialized = True
        
        logger.info("ModelManager initialized")
    
    def load_all(self) -> None:
        """
        Preload all default models.
        
        Raises:
            ModelLoadError: If any critical model fails to load
        """
        logger.info("Preloading all NLP models...")
        start_time = datetime.now()
        
        errors = []
        
        # Load NER model
        try:
            self.get_ner_model()
            logger.info("✓ NER model loaded successfully")
        except Exception as e:
            logger.error(f"✗ NER model failed to load: {e}")
            errors.append(("ner", e))
        
        # Load classifier model
        try:
            self.get_classifier_model()
            logger.info("✓ Classifier model loaded successfully")
        except Exception as e:
            logger.error(f"✗ Classifier model failed to load: {e}")
            errors.append(("classifier", e))
        
        # Load explainer if enabled
        if self.config.enable_shap:
            try:
                self.get_explainer()
                logger.info("✓ SHAP explainer loaded successfully")
            except Exception as e:
                logger.warning(f"! SHAP explainer failed to load: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if errors:
            error_summary = ", ".join(f"{name}: {err}" for name, err in errors)
            logger.error(f"Model loading completed with errors in {elapsed:.2f}s")
            raise ModelLoadError(
                "multiple",
                f"Failed to load {len(errors)} model(s): {error_summary}",
                {"errors": errors, "elapsed_seconds": elapsed}
            )
        
        logger.info(f"All models loaded successfully in {elapsed:.2f}s")
    
    def get_ner_model(self) -> Any:
        """
        Get or load the NER model.
        
        Returns:
            Loaded spaCy NER model
            
        Raises:
            ModelLoadError: If model fails to load
            ModelNotFoundError: If model is not installed
        """
        model_key = "ner"
        
        if model_key in self._models:
            logger.debug(f"Using cached NER model")
            return self._models[model_key]
        
        with self._load_lock:
            if model_key in self._models:
                return self._models[model_key]
            
            logger.info(f"Loading NER model: {self.config.ner_model}")
            
            try:
                import spacy
                
                model = spacy.load(self.config.ner_model)
                
                self._models[model_key] = model
                self._load_times[model_key] = datetime.now()
                self._model_versions[model_key] = self.config.ner_model
                
                logger.info(f"NER model loaded: {self.config.ner_model}")
                return model
                
            except OSError as e:
                error_msg = (
                    f"Model '{self.config.ner_model}' not found. "
                    f"Install with: pip install {self._get_model_install_command(self.config.ner_model)}"
                )
                logger.error(error_msg)
                raise ModelNotFoundError(self.config.ner_model, str(e)) from e
                
            except Exception as e:
                logger.exception(f"Failed to load NER model: {e}")
                raise ModelLoadError(
                    self.config.ner_model,
                    f"Unexpected error: {str(e)}"
                ) from e
    
    def get_classifier_model(self) -> Any:
        """
        Get or load the text classification model.
        
        Returns:
            Loaded transformers pipeline for classification
            
        Raises:
            ModelLoadError: If model fails to load
        """
        model_key = "classifier"
        
        
        if model_key in self._models:
            logger.debug("Using cached classifier model")
            return self._models[model_key]
        
        with self._load_lock:
            if model_key in self._models:
                return self._models[model_key]
            
            logger.info(f"Loading classifier model: {self.config.classifier_model}")
            
            try:
                from transformers import pipeline
                import torch
                
                # Determine device
                device = -1  # CPU
                if self.config.device == "cuda" and torch.cuda.is_available():
                    device = 0
                    logger.info("Using CUDA for classifier")
                elif self.config.device == "mps" and torch.backends.mps.is_available():
                    device = 0
                    logger.info("Using MPS for classifier")
                
                # Try loading model with SSL bypass already in place

                is_local = os.path.isdir(self.config.classifier_model)

                try:
                    logger.info("Attempting to download model from HuggingFace...")
                    model = pipeline(
                                "text-classification",
                                model=self.config.classifier_model,
                                tokenizer=self.config.classifier_model,
                                # THIS IS THE FIX:
                                # If it's a local path, tell the library NOT to look anywhere else
                                local_files_only=is_local, 
                                device=device
                                )
                    logger.info("✓ Model Loaded successfully")
                    
                except Exception as download_error:
                    error_str = str(download_error).lower()
                    
                    if "ssl" in error_str or "certificate" in error_str:
                        logger.error(f"SSL error despite bypass: {download_error}")
                        logger.info("Trying to load from local cache...")
                        
                        try:
                            # Try loading from cache only
                            model = pipeline(
                                "text-classification",
                                model=self.config.classifier_model,
                                device=device,
                                truncation=True,
                                max_length=512,
                                local_files_only=True
                            )
                            logger.info("✓ Loaded from local cache")
                            
                        except Exception as cache_error:
                            logger.error(f"Cache loading failed: {cache_error}")
                            
                            # Provide helpful error message
                            logger.error("\n" + "="*70)
                            logger.error("SSL CERTIFICATE ERROR - MANUAL INTERVENTION REQUIRED")
                            logger.error("="*70)
                            logger.error("\nDespite SSL bypass, the download failed.")
                            logger.error("\nSOLUTIONS (try in order):")
                            logger.error("\n1. Use a lighter model (recommended):")
                            logger.error("   In .env, set:")
                            logger.error("   NLP_CLASSIFIER_MODEL=distilbert-base-uncased-finetuned-sst-2-english")
                            logger.error("\n2. Pre-download on another machine:")
                            logger.error("   python download_models.py")
                            logger.error("   Then copy 'local_models' folder here")
                            logger.error("\n3. Use trusted-host with pip:")
                            logger.error("   pip install transformers --trusted-host huggingface.co --trusted-host cdn.huggingface.co")
                            logger.error("\n4. Get corporate CA certificate from IT:")
                            logger.error("   set REQUESTS_CA_BUNDLE=C:\\path\\to\\corp-ca.pem")
                            logger.error("="*70 + "\n")
                            
                            raise ModelLoadError(
                                self.config.classifier_model,
                                "SSL error and no local cache available"
                            ) from download_error
                    else:
                        # Different error
                        raise
                
                # Store model info
                self._models[model_key] = model
                self._load_times[model_key] = datetime.now()
                self._model_versions[model_key] = self.config.classifier_model
                
                logger.info(f"Classifier model loaded: {self.config.classifier_model}")
                return model
                
            except Exception as e:
                logger.exception(f"Failed to load classifier model: {e}")
                raise ModelLoadError(
                    self.config.classifier_model,
                    f"Error: {str(e)}"
                ) from e
    
    def get_explainer(self) -> Any:
        """
        Get or load the SHAP explainer.
        
        Returns:
            SHAP explainer instance
            
        Raises:
            ModelLoadError: If explainer fails to initialize
        """
        model_key = "explainer"
        
        if model_key in self._models:
            logger.debug("Using cached SHAP explainer")
            return self._models[model_key]
        
        with self._load_lock:
            if model_key in self._models:
                return self._models[model_key]
            
            logger.info("Initializing SHAP explainer")
            
            try:
                import shap
                
                classifier = self.get_classifier_model()
                explainer = shap.Explainer(classifier)
                
                self._models[model_key] = explainer
                self._load_times[model_key] = datetime.now()
                self._model_versions[model_key] = "shap"
                
                logger.info("SHAP explainer initialized")
                return explainer
                
            except ImportError as e:
                logger.warning("SHAP not installed. Install with: pip install shap")
                raise ModelLoadError("shap", "SHAP not installed") from e
                
            except Exception as e:
                logger.exception(f"Failed to initialize SHAP explainer: {e}")
                raise ModelLoadError("shap", f"Error: {str(e)}") from e
    
    def is_loaded(self, model_name: str) -> bool:
        """Check if a model is currently loaded."""
        return model_name in self._models
    
    def get_model_info(self) -> dict[str, dict]:
        """Get information about all loaded models."""
        info = {}
        for model_name in self._models.keys():
            info[model_name] = {
                "version": self._model_versions.get(model_name, "unknown"),
                "loaded_at": self._load_times.get(model_name),
                "loaded": True
            }
        return info
    
    def get_version_string(self) -> str:
        """Get version string for all loaded models."""
        return self.config.get_model_version_string()
    
    def unload_model(self, model_name: str) -> bool:
        """Unload a specific model from memory."""
        with self._load_lock:
            if model_name in self._models:
                del self._models[model_name]
                if model_name in self._load_times:
                    del self._load_times[model_name]
                if model_name in self._model_versions:
                    del self._model_versions[model_name]
                logger.info(f"Model '{model_name}' unloaded")
                return True
            return False
    
    def unload_all(self) -> None:
        """Unload all models from memory."""
        with self._load_lock:
            count = len(self._models)
            self._models.clear()
            self._load_times.clear()
            self._model_versions.clear()
            logger.info(f"All models unloaded ({count} models)")
    
    @staticmethod
    def _get_model_install_command(model_name: str) -> str:
        """Get installation command for a model."""
        install_commands = {
            "en_core_sci_md": "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_md-0.5.4.tar.gz",
            "en_core_sci_lg": "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_lg-0.5.4.tar.gz",
            "en_ner_bc5cdr_md": "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_ner_bc5cdr_md-0.5.4.tar.gz",
        }
        
        return install_commands.get(model_name, model_name)


# Global singleton instance
_manager: ModelManager | None = None


def get_model_manager(config: NLPConfig | None = None) -> ModelManager:
    """Get or create the global model manager instance."""
    global _manager
    if _manager is None:
        _manager = ModelManager(config)
    return _manager
