"""NLP insights page."""
import streamlit as st
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboards.utils import api_get
st.title("NLP Insights")
try:
    data = api_get("/nlp/insights")
    st.json(data)
except Exception as e:
    st.error(f"API error: {e}")
