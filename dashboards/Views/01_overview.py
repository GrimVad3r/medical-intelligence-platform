"""Overview page."""
import streamlit as st
st.title("Overview")
st.markdown("Medical Intelligence Platform – NLP & YOLO powered analytics.")
c1, c2, c3 = st.columns(3)
with c1: st.metric("Messages", "—")
with c2: st.metric("Products", "—")
with c3: st.metric("NLP Runs", "—")
st.info("Connect to API and DB to see live metrics.")
