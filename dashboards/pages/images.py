"""Image analysis page – 04_images."""

import streamlit as st
from dashboards.utils import api_get


def render():
    st.title("Image Analysis (YOLO)")
    try:
        data = api_get("/yolo/results", {"limit": 20})
        if isinstance(data, list):
            for item in data:
                st.write("Image:", item.get("image_path"), "| Detections:", len(item.get("detections", [])))
        else:
            st.json(data)
    except Exception as e:
        st.error(f"API error: {e}")
