"""NLP insights + word cloud – 05_nlp_insights."""

import streamlit as st
from dashboards.utils import api_get


def render():
    st.title("NLP Insights")
    try:
        data = api_get("/nlp/insights")
        st.json(data)
        # Generate word cloud if entity counts available
        entity_counts = data.get("entity_counts") if data else None
        if entity_counts:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            wc = WordCloud(width=800, height=400).generate_from_frequencies(entity_counts)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.info("No entity counts available for word cloud.")
    except Exception as e:
        st.error(f"API error: {e}")
