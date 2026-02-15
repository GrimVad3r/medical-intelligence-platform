"""NLP-specific configuration."""

import os
from pathlib import Path

NLP_MODEL_PATH = Path(os.environ.get("NLP_MODEL_PATH", "data/nlp_models"))
NLP_DEVICE = os.environ.get("NLP_DEVICE", "cpu")
NLP_BATCH_SIZE = int(os.environ.get("NLP_BATCH_SIZE", "32"))
