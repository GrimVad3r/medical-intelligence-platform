"""SHAP / explainability endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.nlp.shap_explainer import explain as nlp_explain

router = APIRouter()


class ExplainNLPRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)


@router.post("/nlp")
def explain_nlp(body: ExplainNLPRequest):
    return nlp_explain(body.text)
