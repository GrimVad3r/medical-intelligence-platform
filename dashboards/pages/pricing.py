"""Pricing analysis page – 03_pricing."""

import streamlit as st


def render():
    st.title("Pricing Analysis")
    st.markdown("Pricing trends and comparisons (from dbt marts).")
    st.info("Configure dbt and run models to populate pricing data.")
