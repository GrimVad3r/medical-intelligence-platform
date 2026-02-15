"""Metric cards component."""

import streamlit as st


def metric_card(title: str, value: str | int, delta: str | None = None):
    st.metric(title, value, delta=delta)
