"""SHAP / explainability endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.nlp.shap_explainer import explain as nlp_explain

router = APIRouter()


class ExplainNLPRequest(BaseModel):
    text: str


@router.post("/nlp")
def explain_nlp(body: ExplainNLPRequest):
    return nlp_explain(body.text)
