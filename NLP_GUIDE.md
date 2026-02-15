# NLP Guide – Medical Intelligence Platform

## Pipeline overview

1. **Input** – Raw text (from Telegram or API).
2. **NER** – Extract entities: drugs, conditions, procedures, dosages (e.g. spaCy or transformers).
3. **Classification** – Category (e.g. product, question, adverse event) and optional urgency.
4. **Entity linking** – Map spans to `data/medical_terms.json`, `data/drug_database.json`.
5. **Semantic analysis** – Relations between entities (e.g. drug–condition).
6. **Explainability** – SHAP for classifier/NER (optional).

## Modules

- **medical_ner.py** – Load NER model, run inference, return list of `{label, text, start, end}`.
- **text_classifier.py** – Load classifier, return `{category, confidence}`.
- **entity_linker.py** – Match normalized entity text to knowledge base IDs.
- **message_processor.py** – Orchestrates NER → classify → link → optional SHAP; single entry for API/scripts.
- **semantic_analyzer.py** – Rule-based or model-based relations.
- **shap_explainer.py** – Wrapper around SHAP for text (e.g. token-level).
- **model_manager.py** – Caches and loads spacy/transformers models from `data/nlp_models/`.

## Configuration

- `src/nlp/config.py` – Model paths, batch size, device (CPU/GPU).
- Env: `NLP_MODEL_PATH`, `NLP_DEVICE`, `NLP_BATCH_SIZE`.

## Usage

- **Script:** `python scripts/analyze_nlp.py --text "..."` or `--from-db --limit 100`.
- **API:** `POST /nlp/analyze` with `{"text": "..."}`.
- **Pipeline:** Telegram scraper with `--nlp` runs processor on each message before persisting.

## Data

- **medical_terms.json** – Concepts and IDs for linking.
- **drug_database.json** – Drug names and codes.
- **medical_conditions.json** – Condition ontology.
