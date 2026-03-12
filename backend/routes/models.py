"""
Model endpoints — list available Gemini models and estimate costs.

These endpoints let the frontend show model selection dropdowns
and cost estimates before the user starts an analysis.
"""
from typing import Optional

from fastapi import APIRouter, Query

from backend import config
from backend.gemini.client import estimate_cost

router = APIRouter(tags=["models"])


@router.get("/models")
async def list_models():
    """
    List all available Gemini models with their pricing.

    The frontend uses this to populate the model selection dropdown
    and show price comparisons.
    """
    models = []
    for model_id, info in config.AVAILABLE_MODELS.items():
        models.append({
            "id": model_id,
            "display_name": info["display_name"],
            "description": info["description"],
            "input_per_1m_tokens": info["input_per_1m"],
            "output_per_1m_tokens": info["output_per_1m"],
            "is_default": model_id == config.DEFAULT_ANALYSIS_MODEL,
        })
    return {"models": models, "default": config.DEFAULT_ANALYSIS_MODEL}


@router.get("/models/estimate")
async def estimate_batch_cost(
    model: Optional[str] = Query(default=None, description="Model ID"),
    num_images: int = Query(default=1, ge=1, le=10000, description="Number of images"),
):
    """
    Estimate the cost of analyzing a batch of images.

    Returns estimated token usage and USD cost before the user commits.
    """
    model_name = model or config.DEFAULT_ANALYSIS_MODEL
    if model_name not in config.AVAILABLE_MODELS:
        return {"error": f"Unknown model: {model_name}"}
    return estimate_cost(model_name, num_images)
