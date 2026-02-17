"""SHAP explainability – 06_explainability."""

import streamlit as st


def render():
    st.title("Explainability (SHAP)")
    text = st.text_area("Enter text for NLP explanation")
    if st.button("Explain"):
        if text:
            try:
                import requests
                api_url = "http://localhost:8000/explainability/nlp"
                response = requests.post(api_url, json={"text": text})
                if response.status_code == 200:
                    result = response.json()
                    st.success("SHAP explanation computed.")
                    st.write("Prediction:", result.get("prediction"))
                    st.write("Base value:", result.get("base_value"))
                    st.write("Explanation type:", result.get("explanation_type"))
                    st.write("Feature importance:")
                    for token, score in result.get("feature_importance", []):
                        st.write(f"{token}: {score:.4f}")
                else:
                    st.error(f"API error: {response.status_code} {response.text}")
            except Exception as e:
                st.error(f"Error calling explainability API: {e}")
        else:
            st.warning("Enter some text.")
