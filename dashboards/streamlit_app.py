"""Main Streamlit dashboard – Medical Intelligence Platform."""

import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="Medical Intelligence Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Medical Intelligence")
st.markdown("## Welcome")
st.markdown("Use the **sidebar** to open Overview, Products, Pricing, Images, NLP Insights, Explainability, Dagster, or Settings.")

# --- Multi-page navigation ---
import importlib

PAGES = {
    "Overview": "01_overview",
    "Products": "02_products",
    "Pricing": "03_pricing",
    "Images": "04_images",
    "NLP Insights": "05_nlp_insights",
    "Explainability": "06_explainability",
    "Dagster Monitoring": "07_dagster_monitoring",
    "Settings": "08_settings",
}

page = st.sidebar.radio("Go to", list(PAGES.keys()))

module_name = f"dashboards.Views.{PAGES[page]}"
try:
    page_module = importlib.import_module(module_name)
    if hasattr(page_module, "main"):
        page_module.main()
except Exception as e:
    st.error(f"Failed to load page: {e}")
