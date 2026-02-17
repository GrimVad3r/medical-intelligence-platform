"""YOLO image analysis endpoints."""

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from src.yolo.inference import run_inference
from src.yolo.model import YOLOModelManager
from src.yolo.config import get_yolo_config

router = APIRouter()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="unsupported content type")
    config = get_yolo_config()
    manager = YOLOModelManager(config)
    suffix = os.path.splitext(file.filename or "")[1] or ".jpg"
    size = 0
    path = ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        path = tmp.name
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="file too large")
            tmp.write(chunk)
    try:
        out = run_inference(manager, [path], include_explanations=False)
        return out.get("results", [{}])[0] if out.get("results") else {}
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


@router.get("/results")
def list_yolo_results(limit: int = Query(50, ge=1, le=500)):
    from src.database.connection import get_session_factory
    from src.database.models import YOLOResult
    from sqlalchemy import select

    factory = get_session_factory()
    with factory() as session:
        stmt = select(YOLOResult).order_by(YOLOResult.created_at.desc()).limit(limit)
        rows = session.scalars(stmt).all()
    return [{"id": r.id, "image_path": r.image_path, "detections": r.detections} for r in rows]
