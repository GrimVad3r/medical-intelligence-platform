"""SHAP explainability – 06_explainability."""

import streamlit as st


def render():
    st.title("Explainability (SHAP)")
    text = st.text_area("Enter text for NLP explanation")
    if st.button("Explain"):
        if text:
            st.info("Call POST /explainability/nlp and display SHAP values here.")
        else:
            st.warning("Enter some text.")
