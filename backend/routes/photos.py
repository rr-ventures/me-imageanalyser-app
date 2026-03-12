"""
Photo endpoints — scanning, listing, serving, rotating, cropping, editing, and upscaling.
"""
import hashlib
import io
import os
import shutil
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

from backend import config
from backend.images.scanner import scan_image_paths, get_image_info
from backend.images.thumbnails import get_or_create_thumbnail
from backend.images.processor import fix_orientation
from backend.images.editor import apply_adjustments, crop_image, parse_all_sliders

load_dotenv(config.PROJECT_ROOT / ".env")

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

router = APIRouter(tags=["photos"])


def _photo_id(path: Path) -> str:
    return hashlib.md5(str(path.resolve()).encode()).hexdigest()[:12]


def _find_photo(photo_id: str) -> Path | None:
    for path in scan_image_paths():
        if _photo_id(path) == photo_id:
            return path
    return None


MEDIA_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".webp": "image/webp",
    ".heic": "image/heic", ".tiff": "image/tiff",
    ".bmp": "image/bmp",
}


@router.get("/photos")
async def list_photos():
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = scan_image_paths()
    photos = []

    for path in paths:
        photo_id = _photo_id(path)
        info = get_image_info(path)
        try:
            get_or_create_thumbnail(path)
            thumbnail_url = f"/thumbnails/{photo_id}.jpg"
        except Exception:
            thumbnail_url = None

        photos.append({
            "id": photo_id,
            "filename": path.name,
            "path": str(path),
            "width": info.get("width", 0),
            "height": info.get("height", 0),
            "size_kb": info.get("size_kb", 0),
            "format": info.get("format", "unknown"),
            "thumbnail_url": thumbnail_url,
            "needs_rotation": info.get("needs_rotation", False),
            "rotation_degrees": info.get("rotation_degrees", 0),
            "needs_upscale": info.get("needs_upscale", False),
            "short_side": info.get("short_side", 0),
        })

    return {"photos": photos, "total": len(photos)}


@router.get("/photos/{photo_id}/full")
async def get_full_photo(photo_id: str):
    """Serve the full image with EXIF rotation already applied."""
    from fastapi.responses import Response as RawResponse
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    info = get_image_info(path)
    if not info.get("needs_rotation"):
        media_type = MEDIA_TYPES.get(path.suffix.lower(), "image/jpeg")
        return FileResponse(str(path), media_type=media_type)

    img = Image.open(path)
    img = fix_orientation(img)
    img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    img.close()
    return RawResponse(content=buf.getvalue(), media_type="image/jpeg")


@router.get("/photos/count")
async def photo_count():
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    return {"count": len(scan_image_paths())}


@router.post("/photos/{photo_id}/rotate")
async def rotate_photo(photo_id: str):
    """Apply EXIF rotation fix and save to processed/ folder."""
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    info = get_image_info(path)
    if not info.get("needs_rotation"):
        raise HTTPException(status_code=400, detail="Photo does not need rotation")

    try:
        img = Image.open(path)
        img = fix_orientation(img)
        img = img.convert("RGB")

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = config.OUTPUT_DIR / f"{path.stem}_rotated.jpg"
        img.save(str(out_path), format="JPEG", quality=95)
        img.close()

        return {
            "status": "ok",
            "output_path": str(out_path),
            "filename": out_path.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rotation failed: {e}")


@router.post("/photos/{photo_id}/upscale")
async def upscale_photo(photo_id: str):
    """Upscale a photo using the Gemini image generation API."""
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="No API key configured")

        client = genai.Client(api_key=api_key)

        img = Image.open(path)
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        image_bytes = buf.getvalue()
        img.close()

        prompt = (
            "Upscale and enhance this photo to higher resolution. "
            "Preserve all original details, colors, and composition exactly. "
            "Increase clarity and sharpness while maintaining a natural look. "
            "Do not alter the content, style, or mood of the photo in any way."
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=prompt),
                ],
            )
        ]

        response = client.models.generate_content(
            model=config.EDIT_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        image_data = None
        try:
            if response.candidates:
                parts = response.candidates[0].content.parts
                for part in parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = part.inline_data.data
                        break
        except (IndexError, AttributeError):
            pass

        if not image_data:
            raise HTTPException(status_code=500, detail="Upscale API returned no image")

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = config.OUTPUT_DIR / f"{path.stem}_upscaled.jpg"
        with open(out_path, "wb") as f:
            f.write(image_data)

        return {
            "status": "ok",
            "output_path": str(out_path),
            "filename": out_path.name,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upscale failed: {e}")


@router.post("/photos/{photo_id}/save")
async def save_photo(photo_id: str):
    """Copy a photo to the processed/ folder as-is."""
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.OUTPUT_DIR / path.name

    counter = 1
    while out_path.exists():
        out_path = config.OUTPUT_DIR / f"{path.stem}_{counter}{path.suffix}"
        counter += 1

    shutil.copy2(str(path), str(out_path))
    return {
        "status": "ok",
        "output_path": str(out_path),
        "filename": out_path.name,
    }


class CropRequest(BaseModel):
    x: float
    y: float
    w: float
    h: float


@router.post("/photos/{photo_id}/crop")
async def crop_photo(photo_id: str, crop: CropRequest):
    """Crop a photo using percentage coordinates and save to processed/."""
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        img = Image.open(path)
        img = fix_orientation(img)
        img = img.convert("RGB")
        img = crop_image(img, crop.x, crop.y, crop.w, crop.h)

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = config.OUTPUT_DIR / f"{path.stem}_cropped.jpg"
        img.save(str(out_path), format="JPEG", quality=95)
        img.close()

        return {
            "status": "ok",
            "output_path": str(out_path),
            "filename": out_path.name,
            "width": img.size[0] if hasattr(img, 'size') else 0,
            "height": img.size[1] if hasattr(img, 'size') else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crop failed: {e}")


class ApplyEditsRequest(BaseModel):
    adjustments: dict


@router.post("/photos/{photo_id}/apply-edits")
async def apply_edits_to_photo(photo_id: str, req: ApplyEditsRequest):
    """Apply Lightroom-style slider adjustments to a photo using Pillow."""
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        img = Image.open(path)
        img = fix_orientation(img)
        img = img.convert("RGB")
        img = apply_adjustments(img, req.adjustments)

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = config.OUTPUT_DIR / f"{path.stem}_edited.jpg"
        img.save(str(out_path), format="JPEG", quality=95)
        w, h = img.size
        img.close()

        return {
            "status": "ok",
            "output_path": str(out_path),
            "filename": out_path.name,
            "width": w,
            "height": h,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edit failed: {e}")


class PreviewRequest(BaseModel):
    crop: Optional[dict] = None
    adjustments: Optional[dict] = None


@router.post("/photos/{photo_id}/preview")
async def preview_photo(photo_id: str, req: PreviewRequest):
    """Apply crop and/or adjustments and return a preview JPEG (not saved)."""
    from fastapi.responses import Response as RawResponse
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        img = Image.open(path)
        img = fix_orientation(img)
        img = img.convert("RGB")

        if req.crop:
            img = crop_image(
                img,
                req.crop.get("x", 0),
                req.crop.get("y", 0),
                req.crop.get("w", 100),
                req.crop.get("h", 100),
            )

        w, h = img.size
        max_preview = 900
        if max(w, h) > max_preview:
            ratio = max_preview / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)

        if req.adjustments and len(req.adjustments) > 0:
            img = apply_adjustments(img, req.adjustments)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        img.close()
        return RawResponse(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {e}")


@router.post("/photos/{photo_id}/preview-edits")
async def preview_edits(photo_id: str, req: ApplyEditsRequest):
    """Apply edits and return a preview JPEG (not saved to processed/)."""
    from fastapi.responses import Response as RawResponse
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        img = Image.open(path)
        img = fix_orientation(img)
        img = img.convert("RGB")

        w, h = img.size
        max_preview = 800
        if max(w, h) > max_preview:
            ratio = max_preview / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)

        img = apply_adjustments(img, req.adjustments)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        img.close()
        return RawResponse(content=buf.getvalue(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {e}")


@router.get("/photos/{photo_id}/slider-ranges")
async def get_slider_ranges(photo_id: str, style: Optional[str] = None):
    """
    Get slider ranges + preset info for a given style.
    Each preset has a slider_position (min/mid/max) that maps to where
    in the slider range it emulates.
    """
    from backend.analysis.library_loader import get_style_plans

    if not style:
        raise HTTPException(status_code=400, detail="style parameter required")

    plans = get_style_plans(style)
    if not plans or "lightroom" not in plans:
        raise HTTPException(status_code=404, detail=f"No plans for style: {style}")

    lr = plans["lightroom"]
    manual_sliders = lr.get("manual_sliders", {})
    parsed = parse_all_sliders(manual_sliders)

    presets_raw = lr.get("presets", {})
    presets_out = []
    for key in ["free_1", "free_2", "free_3", "paid_1", "paid_2"]:
        p = presets_raw.get(key)
        if not p:
            continue
        pos = p.get("slider_position", "mid")
        slider_values = {}
        for skey, sinfo in parsed.items():
            if sinfo.get("is_bool"):
                slider_values[skey] = sinfo.get("raw", False)
            elif pos == "min":
                slider_values[skey] = sinfo["min"]
            elif pos == "max":
                slider_values[skey] = sinfo["max"]
            else:
                slider_values[skey] = round((sinfo["min"] + sinfo["max"]) / 2, 2)

        presets_out.append({
            "key": key,
            "name": p.get("name", key),
            "price": p.get("price"),
            "notes": p.get("notes", ""),
            "justification": p.get("justification", ""),
            "is_free": key.startswith("free"),
            "slider_values": slider_values,
        })

    return {
        "style": style,
        "display_name": plans.get("display_name", style),
        "dating_impact": plans.get("dating_impact", ""),
        "sliders": parsed,
        "presets": presets_out,
    }


class ProcessPhotoRequest(BaseModel):
    rotate: bool = False
    crop: Optional[dict] = None
    adjustments: Optional[dict] = None
    upscale: bool = False
    output_filename: Optional[str] = None


@router.post("/photos/{photo_id}/process")
async def process_photo(photo_id: str, req: ProcessPhotoRequest):
    """
    Apply all selected operations to a photo and save to processed/.

    Operations are applied in order: rotate -> crop -> adjustments -> upscale.
    The result is a single output file.
    """
    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        img = Image.open(path)
        img = fix_orientation(img)
        img = img.convert("RGB")
        ops_applied = []

        if req.rotate:
            ops_applied.append("rotated")

        if req.crop:
            img = crop_image(
                img,
                req.crop.get("x", 0),
                req.crop.get("y", 0),
                req.crop.get("w", 100),
                req.crop.get("h", 100),
            )
            ops_applied.append("cropped")

        if req.adjustments and len(req.adjustments) > 0:
            img = apply_adjustments(img, req.adjustments)
            ops_applied.append("edited")

        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        def _make_out_path(base_name: str) -> Path:
            if req.output_filename:
                fn = req.output_filename
                if not fn.lower().endswith(".jpg"):
                    fn += ".jpg"
                return config.OUTPUT_DIR / fn
            return config.OUTPUT_DIR / base_name

        if req.upscale:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            img.close()

            from google import genai
            from google.genai import types

            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="No API key for upscale")

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=config.EDIT_MODEL,
                contents=[types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"),
                        types.Part.from_text(
                            text="Upscale and enhance this photo to higher resolution. "
                            "Preserve all details, colors, and composition exactly."
                        ),
                    ],
                )],
                config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
            )

            image_data = None
            try:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        image_data = part.inline_data.data
                        break
            except (IndexError, AttributeError):
                pass

            if not image_data:
                raise HTTPException(status_code=500, detail="Upscale API returned no image")

            suffix = "_".join(ops_applied + ["upscaled"])
            out_path = _make_out_path(f"{path.stem}_{suffix}.jpg")
            with open(out_path, "wb") as f:
                f.write(image_data)
            ops_applied.append("upscaled")
        else:
            suffix = "_".join(ops_applied) if ops_applied else "processed"
            out_path = _make_out_path(f"{path.stem}_{suffix}.jpg")
            img.save(str(out_path), format="JPEG", quality=95)
            img.close()

        return {
            "status": "ok",
            "output_path": str(out_path),
            "filename": out_path.name,
            "operations": ops_applied,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")


class BatchProcessRequest(BaseModel):
    photo_ids: list[str]
    actions: list[str]


@router.post("/photos/batch-process")
async def batch_process(req: BatchProcessRequest):
    """Process multiple photos in batch: rotate, upscale, and/or save."""
    results = []
    errors = []

    for pid in req.photo_ids:
        path = _find_photo(pid)
        if not path or not path.exists():
            errors.append({"photo_id": pid, "error": "Photo not found"})
            continue

        info = get_image_info(path)
        photo_results = {"photo_id": pid, "filename": path.name, "actions": []}

        for action in req.actions:
            try:
                if action == "rotate" and info.get("needs_rotation"):
                    img = Image.open(path)
                    img = fix_orientation(img)
                    img = img.convert("RGB")
                    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    out_path = config.OUTPUT_DIR / f"{path.stem}_rotated.jpg"
                    img.save(str(out_path), format="JPEG", quality=95)
                    img.close()
                    photo_results["actions"].append({
                        "action": "rotate",
                        "status": "ok",
                        "filename": out_path.name,
                    })

                elif action == "upscale" and info.get("needs_upscale"):
                    from google import genai
                    from google.genai import types

                    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                    if not api_key:
                        photo_results["actions"].append({
                            "action": "upscale",
                            "status": "error",
                            "error": "No API key",
                        })
                        continue

                    client = genai.Client(api_key=api_key)
                    img = Image.open(path).convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=95)
                    img.close()

                    response = client.models.generate_content(
                        model=config.EDIT_MODEL,
                        contents=[types.Content(
                            role="user",
                            parts=[
                                types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"),
                                types.Part.from_text(
                                    text="Upscale and enhance this photo to higher resolution. "
                                    "Preserve all details, colors, and composition exactly."
                                ),
                            ],
                        )],
                        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
                    )

                    image_data = None
                    try:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                image_data = part.inline_data.data
                                break
                    except (IndexError, AttributeError):
                        pass

                    if image_data:
                        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                        out_path = config.OUTPUT_DIR / f"{path.stem}_upscaled.jpg"
                        with open(out_path, "wb") as f:
                            f.write(image_data)
                        photo_results["actions"].append({
                            "action": "upscale",
                            "status": "ok",
                            "filename": out_path.name,
                        })
                    else:
                        photo_results["actions"].append({
                            "action": "upscale",
                            "status": "error",
                            "error": "API returned no image",
                        })

                elif action == "save":
                    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    out_path = config.OUTPUT_DIR / path.name
                    counter = 1
                    while out_path.exists():
                        out_path = config.OUTPUT_DIR / f"{path.stem}_{counter}{path.suffix}"
                        counter += 1
                    shutil.copy2(str(path), str(out_path))
                    photo_results["actions"].append({
                        "action": "save",
                        "status": "ok",
                        "filename": out_path.name,
                    })

            except Exception as e:
                photo_results["actions"].append({
                    "action": action,
                    "status": "error",
                    "error": str(e),
                })

        results.append(photo_results)

    return {"results": results, "errors": errors}


class UpscalePreviewRequest(BaseModel):
    crop: Optional[dict] = None
    adjustments: Optional[dict] = None


@router.post("/photos/{photo_id}/upscale-preview")
async def upscale_preview(photo_id: str, req: UpscalePreviewRequest = None):
    """
    Upscale a photo (with optional crop/adjustments applied first) and return
    the result as JPEG bytes for preview. Does NOT save to disk.
    """
    from fastapi.responses import Response as RawResponse

    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        img = Image.open(path)
        img = fix_orientation(img)
        img = img.convert("RGB")

        if req and req.crop:
            img = crop_image(
                img,
                req.crop.get("x", 0),
                req.crop.get("y", 0),
                req.crop.get("w", 100),
                req.crop.get("h", 100),
            )

        if req and req.adjustments and len(req.adjustments) > 0:
            img = apply_adjustments(img, req.adjustments)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        img.close()

        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="No API key configured")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=config.EDIT_MODEL,
            contents=[types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"),
                    types.Part.from_text(
                        text="Upscale and enhance this photo to higher resolution. "
                        "Preserve all details, colors, and composition exactly."
                    ),
                ],
            )],
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )

        image_data = None
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_data = part.inline_data.data
                    break
        except (IndexError, AttributeError):
            pass

        if not image_data:
            raise HTTPException(status_code=500, detail="Upscale API returned no image")

        return RawResponse(content=image_data, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upscale preview failed: {e}")


@router.get("/photos/{photo_id}/crop-recommendation")
async def get_crop_recommendation_endpoint(photo_id: str, run_id: str = None):
    """Return 2-3 crop options for a photo based on its analysis metadata."""
    import json
    from backend.analysis.crop_matcher import get_crop_options

    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    info = get_image_info(path)
    metadata = {}
    if run_id:
        run_path = config.RUNS_DIR / f"{run_id}.json"
        if run_path.exists():
            with open(run_path, "r") as f:
                run_data = json.load(f)
            for r in run_data.get("results", []):
                if r.get("image_id") == photo_id:
                    metadata = r.get("metadata", {})
                    break

    options = get_crop_options(
        metadata,
        info.get("width", 0),
        info.get("height", 0),
        max_options=3,
    )
    return {
        "photo_id": photo_id,
        "crop_options": options,
    }


@router.get("/photos/{photo_id}/preset-recommendation")
async def get_preset_recommendation(photo_id: str, run_id: str = None):
    """
    Return the preset recommendation for a photo based on its analysis metadata.
    Needs the run_id to look up metadata, or metadata can be passed.
    """
    import json
    from backend.analysis.preset_matcher import get_recommendation, get_danger_zones

    path = _find_photo(photo_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    metadata = None
    if run_id:
        run_path = config.RUNS_DIR / f"{run_id}.json"
        if run_path.exists():
            with open(run_path, "r") as f:
                run_data = json.load(f)
            for r in run_data.get("results", []):
                if r.get("image_id") == photo_id:
                    metadata = r.get("metadata")
                    break

    rec = get_recommendation(metadata or {})
    dangers = get_danger_zones()

    return {
        "photo_id": photo_id,
        "recommendation": rec,
        "danger_zones": dangers,
    }


@router.get("/processed")
async def list_processed():
    """List all photos in the processed/ folder."""
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exts = {e.lower() for e in config.SUPPORTED_EXTENSIONS}
    files = [
        p for p in sorted(config.OUTPUT_DIR.iterdir())
        if p.is_file() and p.suffix.lower() in exts
    ]
    return {
        "files": [{"filename": f.name, "size_kb": round(f.stat().st_size / 1024, 1)} for f in files],
        "total": len(files),
        "folder": str(config.OUTPUT_DIR),
    }
