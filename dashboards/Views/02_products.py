"""Products page."""
import streamlit as st
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboards.utils import api_get
st.title("Products")
try:
    data = api_get("/products", {"limit": 50})
    st.dataframe(data if isinstance(data, list) else [data])
except Exception as e:
    st.error(f"API error: {e}")
