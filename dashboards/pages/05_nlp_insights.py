"""NLP insights page."""
import streamlit as st
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from dashboards.utils import api_get
st.title("NLP Insights")
try:
    data = api_get("/nlp/insights")
    if not data:
        st.warning("No NLP insights available.")
    else:
        st.json(data)
        # Display entity counts if present
        entity_counts = data.get("entity_counts")
        if entity_counts:
            st.subheader("Entity Counts")
            for entity, count in entity_counts.items():
                st.write(f"{entity}: {count}")
        # Display word cloud if available
        if "wordcloud" in data:
            import matplotlib.pyplot as plt
            import io
            from PIL import Image
            img_bytes = data["wordcloud"]
            image = Image.open(io.BytesIO(img_bytes))
            st.image(image, caption="NLP Word Cloud")
except Exception as e:
    st.error(f"API error: {e}")
