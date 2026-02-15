"""Dashboard settings – 08_settings."""

import streamlit as st
from dashboards.config import API_BASE, DAGSTER_URL


def render():
    st.title("Settings")
    st.text_input("API base URL", value=API_BASE, key="api_base")
    st.text_input("Dagster URL", value=DAGSTER_URL, key="dagster_url")
    st.caption("Restart app or use env vars to apply.")
