"""Chart utilities (placeholder for plotly/altair)."""

import streamlit as st


def bar_chart(data: dict):
    import plotly.express as px
    import pandas as pd
    df = pd.DataFrame(list(data.items()), columns=["Category", "Value"])
    fig = px.bar(df, x="Category", y="Value", title="Bar Chart")
    st.plotly_chart(fig)
