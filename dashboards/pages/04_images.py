"""Image analysis (YOLO) page."""
import streamlit as st
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboards.utils import api_get
st.title("Image Analysis (YOLO)")
try:
    data = api_get("/yolo/results", {"limit": 20})
    for item in (data if isinstance(data, list) else [data]):
        st.write("Image:", item.get("image_path"), "| Detections:", len(item.get("detections", [])))
except Exception as e:
    st.error(f"API error: {e}")
