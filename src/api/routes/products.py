"""Product endpoints."""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import ProductResponse
from src.database.models import Product

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    category: str | None = None,
):
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    stmt = stmt.offset(offset).limit(limit)
    rows = db.scalars(stmt).all()
    return [ProductResponse(id=r.id, name=r.name, category=r.category) for r in rows]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    from src.api.exceptions import not_found
    row = db.get(Product, product_id)
    if not row:
        raise not_found("Product not found")
    return ProductResponse(id=row.id, name=row.name, category=row.category)
