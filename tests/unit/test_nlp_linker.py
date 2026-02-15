"""Unit tests for entity linker."""
from src.nlp.entity_linker import link_entities


def test_link_entities_empty():
    assert link_entities({}) == {}


def test_link_entities_structure():
    out = link_entities({"DRUG": [{"text": "Aspirin"}]})
    assert "DRUG" in out
    assert len(out["DRUG"]) == 1
    assert out["DRUG"][0]["text"] == "Aspirin"
