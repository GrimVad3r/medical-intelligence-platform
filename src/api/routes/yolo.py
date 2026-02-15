"""YOLO image analysis endpoints."""

from typing import Any, List

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from src.yolo.inference import run_inference
from src.yolo.model import YOLOModelManager
from src.yolo.config import get_yolo_config

router = APIRouter()


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    import tempfile
    import os
    config = get_yolo_config()
    manager = YOLOModelManager(config)
    suffix = os.path.splitext(file.filename or "")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        path = tmp.name
    try:
        out = run_inference(manager, [path], include_explanations=False)
        return out.get("results", [{}])[0] if out.get("results") else {}
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


@router.get("/results")
def list_yolo_results(limit: int = 50):
    from src.database.connection import get_session_factory
    from src.database.models import YOLOResult
    from sqlalchemy import select

    factory = get_session_factory()
    with factory() as session:
        stmt = select(YOLOResult).order_by(YOLOResult.created_at.desc()).limit(limit)
        rows = session.scalars(stmt).all()
    return [{"id": r.id, "image_path": r.image_path, "detections": r.detections} for r in rows]
