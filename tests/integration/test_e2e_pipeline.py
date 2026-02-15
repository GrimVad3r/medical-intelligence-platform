"""E2E placeholder: full pipeline (scrape -> nlp -> db) requires live services."""
import pytest


@pytest.mark.e2e
@pytest.mark.skip(reason="Requires Telegram and DB")
def test_e2e_pipeline():
    pass
