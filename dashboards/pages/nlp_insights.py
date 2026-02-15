"""NLP insights + word cloud – 05_nlp_insights."""

import streamlit as st
from dashboards.utils import api_get


def render():
    st.title("NLP Insights")
    try:
        data = api_get("/nlp/insights")
        st.json(data)
        st.markdown("Word cloud placeholder – add wordcloud library and entity counts.")
    except Exception as e:
        st.error(f"API error: {e}")
