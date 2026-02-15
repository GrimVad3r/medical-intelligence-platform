"""NLP visualizations (entity highlights, word cloud)."""

import streamlit as st


def entity_highlights(text: str, entities: list):
    st.markdown(f"**Text:** {text}")
    st.json(entities)
