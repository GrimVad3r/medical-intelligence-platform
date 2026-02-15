"""CSS styling for dashboard."""

import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
    .stMetric { background: #f0f2f6; padding: 0.5rem; border-radius: 0.25rem; }
    </style>
    """, unsafe_allow_html=True)
