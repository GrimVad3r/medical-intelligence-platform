"""
SHAP Explainability for NLP Models.

Provides interpretability and explanations for NLP model predictions using SHAP
(SHapley Additive exPlanations) values.
"""

from typing import Any

from src.logger import get_logger
from src.nlp.exceptions import ModelLoadError
from src.nlp.config import get_config

logger = get_logger(__name__)


def explain(
    text: str,
    model: Any = None,
    max_features: int = 10
) -> dict[str, Any]:
    """
    Generate SHAP explanations for model predictions.
    
    Args:
        text: Input text to explain
        model: Optional pre-loaded model (classifier or NER)
        max_features: Maximum number of top features to return
        
    Returns:
        Dictionary containing:
        - feature_importance: List of (token, importance_score) tuples
        - base_value: Baseline prediction value
        - prediction: Model's prediction
        - explanation_type: Type of explanation (additive, etc.)
        
    Raises:
        ModelLoadError: If SHAP explainer fails to initialize
        
    Example:
        >>> explanation = explain("Patient prescribed Lisinopril for hypertension")
        >>> print(explanation["feature_importance"][:3])
        [
            ("Lisinopril", 0.45),
            ("hypertension", 0.32),
            ("prescribed", 0.18)
        ]
    """
    config = get_config()
    
    if not config.enable_shap:
        logger.debug("SHAP disabled in configuration")
        return {
            "feature_importance": [],
            "base_value": 0.0,
            "prediction": None,
            "explanation_type": "disabled"
        }
    
    if not text or not text.strip():
        return {
            "feature_importance": [],
            "base_value": 0.0,
            "prediction": None,
            "explanation_type": "empty_input"
        }
    
    try:
        # Try to import SHAP
        try:
            import shap
            import numpy as np
        except ImportError as e:
            logger.warning("SHAP not installed. Install with: pip install shap")
            raise ModelLoadError(
                "shap",
                "SHAP library not installed. Run: pip install shap"
            ) from e
        
        # Load model if not provided
        if model is None:
            from src.nlp.model_manager import get_model_manager
            manager = get_model_manager()
            
            # Try to get the explainer, or create one from classifier
            try:
                explainer = manager.get_explainer()
            except:
                # Create explainer from classifier
                classifier = manager.get_classifier_model()
                explainer = _create_explainer(classifier)
        else:
            explainer = _create_explainer(model)
        
        # Generate explanation
        logger.debug(f"Generating SHAP explanation for text of length {len(text)}")
        
        # Get SHAP values
        shap_values = explainer([text])
        
        # Process SHAP values
        if hasattr(shap_values, 'values'):
            values = shap_values.values[0]
            base_value = shap_values.base_values[0] if hasattr(shap_values, 'base_values') else 0.0
            data = shap_values.data[0] if hasattr(shap_values, 'data') else text.split()
        else:
            # Older SHAP API
            values = shap_values[0]
            base_value = 0.0
            data = text.split()
        
        # Extract feature importance
        if isinstance(values, np.ndarray):
            # Handle multi-dimensional outputs (e.g., multi-class)
            if len(values.shape) > 1:
                values = values[:, 0]  # Take first class
        
        feature_importance = []
        for token, importance in zip(data, values):
            feature_importance.append({
                "token": str(token),
                "importance": float(importance)
            })
        
        # Sort by absolute importance
        feature_importance.sort(key=lambda x: abs(x["importance"]), reverse=True)
        
        # Take top N features
        feature_importance = feature_importance[:max_features]
        
        result = {
            "feature_importance": feature_importance,
            "base_value": float(base_value),
            "explanation_type": "shap_additive",
            "num_tokens": len(data)
        }
        
        logger.debug(f"Generated explanation with {len(feature_importance)} top features")
        
        return result
        
    except ImportError as e:
        logger.warning(f"SHAP not available: {e}")
        return {
            "feature_importance": [],
            "base_value": 0.0,
            "explanation_type": "unavailable",
            "error": str(e)
        }
    except Exception as e:
        logger.exception(f"SHAP explanation failed: {e}")
        return {
            "feature_importance": [],
            "base_value": 0.0,
            "explanation_type": "error",
            "error": str(e)
        }


def _create_explainer(model: Any) -> Any:
    """
    Create a SHAP explainer for a given model.
    
    Args:
        model: Model to create explainer for
        
    Returns:
        SHAP explainer instance
        
    Raises:
        ModelLoadError: If explainer creation fails
    """
    try:
        import shap
        
        # Determine model type and create appropriate explainer
        model_type = type(model).__name__.lower()
        
        if "pipeline" in model_type or "transformers" in str(type(model).__module__):
            # Transformers pipeline
            logger.debug("Creating SHAP explainer for transformers model")
            
            # Create a wrapper function for the model
            def model_fn(texts):

                if not isinstance(texts, (list, str)):
                    texts = texts.tolist()
                
                formatted_texts = [str(t) for t in texts]

                results = model(formatted_texts)
                if isinstance(results, list):
                    # Extract scores
                    scores = []
                    for result in results:
                        if isinstance(result, list):
                            result = result[0]
                        scores.append([result.get("score", 0.5)])
                    return scores
                return results
            
            # Use Explainer with the wrapper
            explainer = shap.Explainer(model_fn, model.tokenizer)
            
        elif "spacy" in str(type(model).__module__):
            # spaCy model
            logger.debug("Creating SHAP explainer for spaCy model")
            
            # For spaCy, we'll use a simpler approach
            # This is a placeholder - full spaCy support requires more setup
            explainer = None
            
        else:
            # Generic explainer
            logger.debug(f"Creating generic SHAP explainer for {model_type}")
            explainer = shap.Explainer(model)
        
        return explainer
        
    except Exception as e:
        logger.exception(f"Failed to create SHAP explainer: {e}")
        raise ModelLoadError("shap", f"Failed to create explainer: {str(e)}") from e


def explain_batch(
    texts: list[str],
    model: Any = None,
    max_features: int = 10
) -> list[dict[str, Any]]:
    """
    Generate SHAP explanations for multiple texts.
    
    Args:
        texts: List of input texts
        model: Optional pre-loaded model
        max_features: Maximum number of features per explanation
        
    Returns:
        List of explanation dictionaries
    """
    if not texts:
        return []
    
    results = []
    
    for text in texts:
        try:
            explanation = explain(text, model=model, max_features=max_features)
            results.append(explanation)
        except Exception as e:
            logger.warning(f"Failed to explain one text: {e}")
            results.append({
                "feature_importance": [],
                "base_value": 0.0,
                "explanation_type": "error",
                "error": str(e)
            })
    
    return results


def visualize_explanation(
    text: str,
    explanation: dict[str, Any],
    output_path: str | None = None
) -> str:
    """
    Create a visualization of the SHAP explanation.
    
    Args:
        text: Original text
        explanation: Explanation dictionary from explain()
        output_path: Optional path to save visualization
        
    Returns:
        HTML string of the visualization
    """
    try:
        import shap
        
        # Create HTML visualization
        html = "<div style='font-family: monospace;'>"
        html += "<h3>SHAP Explanation</h3>"
        html += f"<p><strong>Text:</strong> {text}</p>"
        html += f"<p><strong>Base Value:</strong> {explanation['base_value']:.4f}</p>"
        html += "<h4>Top Features:</h4>"
        html += "<table style='border-collapse: collapse;'>"
        html += "<tr><th style='border: 1px solid #ddd; padding: 8px;'>Token</th>"
        html += "<th style='border: 1px solid #ddd; padding: 8px;'>Importance</th></tr>"
        
        for feature in explanation.get("feature_importance", []):
            importance = feature["importance"]
            color = "red" if importance < 0 else "green"
            html += f"<tr>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{feature['token']}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px; color: {color};'>"
            html += f"{importance:+.4f}</td>"
            html += f"</tr>"
        
        html += "</table>"
        html += "</div>"
        
        # Save if output path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"Visualization saved to {output_path}")
        
        return html
        
    except Exception as e:
        logger.exception(f"Failed to create visualization: {e}")
        return f"<p>Error creating visualization: {str(e)}</p>"


def get_top_features(
    explanation: dict[str, Any],
    n: int = 5,
    direction: str = "both"
) -> list[dict[str, Any]]:
    """
    Get top N features from explanation.
    
    Args:
        explanation: Explanation dictionary from explain()
        n: Number of features to return
        direction: "positive", "negative", or "both"
        
    Returns:
        List of top feature dictionaries
    """
    features = explanation.get("feature_importance", [])
    
    if direction == "positive":
        features = [f for f in features if f["importance"] > 0]
    elif direction == "negative":
        features = [f for f in features if f["importance"] < 0]
    
    # Already sorted by absolute importance in explain()
    return features[:n]


def aggregate_explanations(
    explanations: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Aggregate multiple explanations to find common important features.
    
    Args:
        explanations: List of explanation dictionaries
        
    Returns:
        Aggregated explanation with average feature importance
    """
    from collections import defaultdict
    
    feature_scores = defaultdict(list)
    
    for explanation in explanations:
        for feature in explanation.get("feature_importance", []):
            token = feature["token"]
            importance = feature["importance"]
            feature_scores[token].append(importance)
    
    # Calculate averages
    aggregated_features = []
    for token, scores in feature_scores.items():
        avg_importance = sum(scores) / len(scores)
        aggregated_features.append({
            "token": token,
            "importance": avg_importance,
            "frequency": len(scores)
        })
    
    # Sort by absolute importance
    aggregated_features.sort(key=lambda x: abs(x["importance"]), reverse=True)
    
    return {
        "feature_importance": aggregated_features,
        "num_explanations": len(explanations),
        "explanation_type": "aggregated"
    }