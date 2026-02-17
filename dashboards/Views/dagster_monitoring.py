"""Dagster monitoring – 07_dagster_monitoring."""

import streamlit as st
from dashboards.config import DAGSTER_URL


def render():
    st.title("Dagster Status")
    st.markdown(f"Open [Dagster UI]({DAGSTER_URL}) for runs and asset status.")
    st.info("Dagster runs pipeline: scrape → NLP → dbt.")
