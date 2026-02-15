"""SHAP visualizations."""

import streamlit as st


def shap_bars(values: list, labels: list):
    st.bar_chart(dict(zip(labels, values)))
