"""Dashboard settings page."""
import streamlit as st
import os
st.title("Settings")
st.text_input("API base URL", value=os.environ.get("API_BASE_URL", "http://localhost:8000"))
st.text_input("Dagster URL", value=os.environ.get("DAGSTER_URL", "http://localhost:3000"))
