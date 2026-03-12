"""
Analysis endpoints — run Gemini analysis and style selection.

These endpoints handle:
- Analyzing single photos or batches
- Retrieving past analysis results (runs)
- Listing past runs
"""
import asyncio
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend import config
from backend.gemini.client import analyze_photo, estimate_cost
from backend.analysis.selector import select_styles_from_dict
from backend.analysis.preset_matcher import get_recommendation
from backend.images.scanner import scan_image_paths

router = APIRouter(tags=["analysis"])


def _photo_id(path: Path) -> str:
    return hashlib.md5(str(path.resolve()).encode()).hexdigest()[:12]


def _find_photo_by_id(photo_id: str) -> Path | None:
    for path in scan_image_paths():
        if _photo_id(path) == photo_id:
            return path
    return None


def _sanitize_filename(name: str) -> str:
    """Convert a filename to profile_photo_style_name format."""
    stem = Path(name).stem.lower()
    stem = "".join(c if c.isalnum() or c == "_" else "_" for c in stem)
    stem = "_".join(part for part in stem.split("_") if part)
    return stem


@router.post("/analyze/single")
async def analyze_single(
    photo_id: str,
    model: Optional[str] = Query(default=None, description="Gemini model to use"),
):
    """Analyze a single photo: extract metadata via Gemini, then select styles."""
    path = _find_photo_by_id(photo_id)
    if not path:
        raise HTTPException(status_code=404, detail="Photo not found")

    result = await analyze_photo(path, model_name=model)

    if result["error"]:
        raise HTTPException(status_code=500, detail=result["error"])

    metadata = result["metadata"]
    style_result = select_styles_from_dict(metadata)
    preset_rec = get_recommendation(metadata)

    output_name = f"profile_photo_{_sanitize_filename(path.name)}"

    return {
        "image_id": photo_id,
        "filename": path.name,
        "output_name": output_name,
        **style_result,
        "preset_recommendation": preset_rec,
        "token_usage": result["token_usage"],
    }


@router.post("/analyze/batch")
async def analyze_batch(
    model: Optional[str] = Query(default=None, description="Gemini model to use"),
    limit: Optional[int] = Query(default=None, description="Max photos to analyze"),
):
    """
    Analyze all photos in to_process/ (or up to limit).

    Creates a run file in data/runs/ with all results.
    Returns the run_id so the frontend can poll for results.
    """
    paths = scan_image_paths()
    if not paths:
        raise HTTPException(status_code=400, detail="No photos found in to_process/")

    if limit and limit > 0:
        paths = paths[:limit]

    model_name = model or config.DEFAULT_ANALYSIS_MODEL
    semaphore = asyncio.Semaphore(config.ANALYSIS_CONCURRENCY)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_path = config.RUNS_DIR / f"{ts}.json"

    results = []
    errors = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    tasks = []
    for path in paths:
        tasks.append(_analyze_one(path, model_name, semaphore))

    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    for i, outcome in enumerate(outcomes):
        path = paths[i]
        photo_id = _photo_id(path)

        if isinstance(outcome, Exception):
            errors.append({
                "image_id": photo_id,
                "filename": path.name,
                "error": str(outcome),
            })
            continue

        result, usage = outcome

        for k in total_usage:
            total_usage[k] += usage.get(k, 0)

        if result.get("error"):
            errors.append({
                "image_id": photo_id,
                "filename": path.name,
                "error": result["error"],
            })
            continue

        metadata = result["metadata"]
        style_result = select_styles_from_dict(metadata)
        preset_rec = get_recommendation(metadata)
        output_name = f"profile_photo_{_sanitize_filename(path.name)}"

        results.append({
            "image_id": photo_id,
            "filename": path.name,
            "output_name": output_name,
            **style_result,
            "preset_recommendation": preset_rec,
        })

    run_data = {
        "run_id": ts,
        "model": model_name,
        "total_photos": len(paths),
        "total_analyzed": len(results),
        "total_errors": len(errors),
        "token_usage": total_usage,
        "estimated_cost_usd": estimate_cost(model_name, len(paths))["estimated_cost_usd"],
        "results": results,
        "errors": errors,
    }

    with open(run_path, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2)

    return run_data


async def _analyze_one(
    path: Path,
    model_name: str,
    semaphore: asyncio.Semaphore,
) -> tuple[dict, dict]:
    result = await analyze_photo(path, model_name=model_name, semaphore=semaphore)
    return result, result.get("token_usage", {})


@router.get("/runs")
async def list_runs():
    """List all past analysis runs."""
    config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_files = sorted(
        config.RUNS_DIR.glob("*.json"),
        key=lambda p: p.name,
        reverse=True,
    )

    runs = []
    for f in run_files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            runs.append({
                "run_id": data.get("run_id", f.stem),
                "model": data.get("model", "unknown"),
                "total_photos": data.get("total_photos", 0),
                "total_analyzed": data.get("total_analyzed", 0),
                "total_errors": data.get("total_errors", 0),
                "estimated_cost_usd": data.get("estimated_cost_usd", 0),
            })
        except (json.JSONDecodeError, OSError):
            continue

    return {"runs": runs}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get the full results of a specific run."""
    run_path = config.RUNS_DIR / f"{run_id}.json"
    if not run_path.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    with open(run_path, encoding="utf-8") as f:
        return json.load(f)
