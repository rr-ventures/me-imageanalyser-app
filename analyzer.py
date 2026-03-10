"""
Receipt Sorter — Gemini-based image analysis.
Classifies images into buckets; computes suggested_folder from category + date.
Supports incremental save (each result written as it completes) and token tracking.
"""
import asyncio
import hashlib
import io
import json
import os
import re
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

import config

load_dotenv()


def suggested_folder_from_category_date(category: str, date: str | None) -> str:
    cat = (category or "").strip().lower()
    if cat == "receipt":
        if date and date >= config.CUTOFF_DATE:
            return "receipts_keep"
        return "receipts_old"
    if cat in ("invoice", "document"):
        return "invoices_docs"
    if cat in ("photo", "screenshot"):
        return "photos_screenshots"
    return "unknown"


def file_hash(path: Path) -> str:
    """SHA-256 of file contents for duplicate detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_and_prepare_image(path: Path) -> tuple[bytes, str] | None:
    """Load image, resize longest edge to MAX_IMAGE_SIZE_PX, return (jpeg_bytes, mime) or None."""
    try:
        ext = path.suffix.lower()
        if ext == ".heic":
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except Exception:
                pass
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if max(w, h) > config.MAX_IMAGE_SIZE_PX:
            ratio = config.MAX_IMAGE_SIZE_PX / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return None


CLASSIFY_PROMPT = """You are classifying an image of a document or photo for filing.

Respond with ONLY a single JSON object (no markdown, no extra text) with these exact keys:
- "category": one of: receipt, invoice, document, photo, screenshot, unknown
- "description": one sentence describing what is in this image
- "date": date on the document in YYYY-MM-DD if visible, else null
- "vendor": short vendor or source name if visible, else null
- "total": total amount if financial (number or string), else null
- "is_financial": true if receipt/invoice/statement, else false
- "delete_candidate": true only if clearly junk (e.g. blank, duplicate, screenshot of nothing), else false
- "confidence": one of: high, medium, low
- "notes": brief note if useful, else null
"""


def parse_classification_response(text: str) -> dict:
    """Parse model JSON; on failure set confidence=low, category=unknown, notes with error."""
    text = (text or "").strip()
    if "```" in text:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {
            "category": "unknown",
            "description": None,
            "date": None,
            "vendor": None,
            "total": None,
            "is_financial": False,
            "delete_candidate": False,
            "confidence": "low",
            "notes": f"Parse error: {e}",
        }
    category = (data.get("category") or "unknown").strip().lower()
    if category not in ("receipt", "invoice", "document", "photo", "screenshot", "unknown"):
        category = "unknown"
    date_val = data.get("date")
    if date_val and not isinstance(date_val, str):
        date_val = str(date_val)
    return {
        "category": category,
        "description": data.get("description"),
        "date": date_val,
        "vendor": data.get("vendor"),
        "total": data.get("total"),
        "is_financial": bool(data.get("is_financial")),
        "delete_candidate": bool(data.get("delete_candidate")),
        "confidence": (data.get("confidence") or "low").strip().lower(),
        "notes": data.get("notes"),
    }


def _extract_token_usage(response) -> dict:
    """Pull token counts from the Gemini response if available."""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    try:
        meta = response.usage_metadata
        if meta:
            usage["prompt_tokens"] = getattr(meta, "prompt_token_count", 0) or 0
            usage["completion_tokens"] = getattr(meta, "candidates_token_count", 0) or 0
            usage["total_tokens"] = getattr(meta, "total_token_count", 0) or 0
    except Exception:
        pass
    return usage


async def analyze_one(
    aclient,
    path: Path,
    semaphore: asyncio.Semaphore,
) -> tuple[dict | None, str | None, dict]:
    """
    Returns (result_dict, error_message, token_usage).
    result_dict includes suggested_folder, file_hash, and all model fields.
    """
    empty_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    async with semaphore:
        prepared = load_and_prepare_image(path)
        if prepared is None:
            return None, f"Could not load or decode image: {path}", empty_usage
        image_bytes, mime_type = prepared
        path_str = str(path)
        for attempt in range(3):
            try:
                contents = [
                    types.Part.from_text(text=CLASSIFY_PROMPT),
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ]
                response = await aclient.models.generate_content(
                    model=config.MODEL,
                    contents=contents,
                )
                usage = _extract_token_usage(response)
                text = response.text if response else None
                if not text:
                    return None, f"No response from model: {path_str}", usage
                parsed = parse_classification_response(text)
                parsed["suggested_folder"] = suggested_folder_from_category_date(
                    parsed["category"], parsed.get("date")
                )
                return parsed, None, usage
            except Exception as e:
                err_str = str(e).lower()
                retryable = "429" in err_str or "500" in err_str or "resource_exhausted" in err_str or "internal" in err_str
                if retryable and attempt < 2:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                return None, f"{path_str}: {e}", empty_usage
        return None, f"Max retries exceeded: {path_str}", empty_usage


async def analyze_batch(
    paths: list[Path],
    on_result: Callable[[Path, dict | None, str | None, dict], None] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[list[dict], list[dict], dict]:
    """
    Analyze a batch of images. Returns (results, errors, total_token_usage).
    Calls on_result(path, result, error, usage) after each image completes for incremental save.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) not set in environment or .env")
    client = genai.Client(api_key=api_key)
    semaphore = asyncio.Semaphore(config.CONCURRENCY)
    results: list[dict] = []
    errors: list[dict] = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    completed = [0]
    total = len(paths)

    async def task(p: Path):
        fhash = file_hash(p)
        res, err, usage = await analyze_one(aclient, p, semaphore)
        completed[0] += 1
        if progress_callback:
            progress_callback(completed[0], total)
        if res:
            res["filename"] = p.name
            res["original_path"] = str(p)
            res["file_hash"] = fhash
            res["user_folder"] = None
            res["approved"] = False
        if on_result:
            on_result(p, res, err, usage)
        return p, res, err, usage, fhash

    async with client.aio as aclient:
        tasks = [task(p) for p in paths]
        done = await asyncio.gather(*tasks, return_exceptions=True)

    for outcome in done:
        if isinstance(outcome, BaseException):
            errors.append({"path": "?", "error": str(outcome)})
            continue
        path, res, err, usage, fhash = outcome
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            total_usage[k] += usage.get(k, 0)
        if err:
            errors.append({"path": str(path), "filename": path.name, "file_hash": fhash, "error": err})
            continue
        results.append(res)

    return results, errors, total_usage
