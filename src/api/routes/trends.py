"""Analytics and trends endpoints."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("")
def get_trends(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    granularity: str = Query("day"),
):
    # Placeholder: query dbt marts or aggregated tables
    return {"series": [], "granularity": granularity}
