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
