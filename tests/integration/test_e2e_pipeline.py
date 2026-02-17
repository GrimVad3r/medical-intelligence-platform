"""E2E placeholder: full pipeline (scrape -> nlp -> db) requires live services."""
import pytest


@pytest.mark.e2e
def test_e2e_pipeline():
    """Test full pipeline: scrape -> nlp -> db -> dashboard."""
    from scripts.scrape_telegram import main as scrape_main
    from scripts.analyze_nlp import main as nlp_main
    from scripts.analyze_yolo import main as yolo_main
    from src.database.connection import get_session_factory
    session_factory = get_session_factory()
    # Scrape messages
    scrape_main()
    # Run NLP
    nlp_main()
    # Run YOLO
    yolo_main()
    # Validate DB
    with session_factory() as session:
        result = session.execute("SELECT COUNT(*) FROM messages").scalar()
        assert result > 0, "No messages found after pipeline run"
