"""Analytics and trends endpoints."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("")
def get_trends(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    granularity: str = Query("day"),
):
    # Query dbt marts or aggregated tables for trends
    try:
        from src.database.connection import get_session_factory
        from src.database.queries import get_trends_data
        session_factory = get_session_factory()
        with session_factory() as session:
            series = get_trends_data(session, from_date, to_date, granularity)
        return {"series": series, "granularity": granularity}
    except Exception as e:
        return {"error": f"Failed to fetch trends: {e}", "series": [], "granularity": granularity}
