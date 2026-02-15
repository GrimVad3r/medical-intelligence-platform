"""Dagster monitoring page."""
import streamlit as st
import os
st.title("Dagster Status")
url = os.environ.get("DAGSTER_URL", "http://localhost:3000")
st.markdown(f"Open [Dagster UI]({url}) for runs and asset status.")
