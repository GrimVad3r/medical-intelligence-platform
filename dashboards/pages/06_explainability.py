"""Explainability (SHAP) page."""
import streamlit as st
st.title("Explainability (SHAP)")
text = st.text_area("Enter text for NLP explanation")
if st.button("Explain") and text:
    st.info("Call POST /explainability/nlp and display SHAP values here.")
