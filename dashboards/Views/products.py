"""Products page – 02_products."""

import streamlit as st
from dashboards.utils import api_get


def render():
    st.title("Products")
    try:
        data = api_get("/products", {"limit": 50})
        if isinstance(data, list):
            st.dataframe(data)
        else:
            st.json(data)
    except Exception as e:
        st.error(f"API error: {e}")
