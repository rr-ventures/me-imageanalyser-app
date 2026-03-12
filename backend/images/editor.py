"""
Photo editor — applies Lightroom-style adjustments using Pillow.

Maps Lightroom slider names to Pillow image operations. Each adjustment
is applied independently and can be toggled on/off.
"""
import re
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np


def parse_slider_range(value: str) -> tuple[float, float] | None:
    """
    Parse a YAML slider range string into (min, max) floats.

    Handles formats like:
        "+0.10 to +0.20"  →  (0.10, 0.20)
        "-20 to -10"      →  (-20.0, -10.0)
        "+5 to +12"       →  (5.0, 12.0)
        "no change"        →  None
        "slight teal"      →  None
    """
    if not isinstance(value, str):
        return None
    m = re.match(r'([+-]?\d+\.?\d*)\s*to\s*([+-]?\d+\.?\d*)', value)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    m = re.match(r'^([+-]?\d+\.?\d*)$', value.strip())
    if m:
        v = float(m.group(1))
        return (v, v)
    return None


def parse_all_sliders(manual_sliders: dict) -> dict:
    """
    Parse all slider values from the YAML into structured data.

    Returns dict of {slider_name: {min, max, label, unit}} for each
    parseable slider. Skips text-only values like "slight teal".
    """
    parsed = {}
    for key, value in manual_sliders.items():
        if isinstance(value, bool):
            parsed[key] = {"min": 0, "max": 1, "label": _format_label(key), "is_bool": True, "raw": value}
            continue
        rng = parse_slider_range(str(value))
        if rng is None:
            continue
        lo, hi = rng
        parsed[key] = {
            "min": lo,
            "max": hi,
            "label": _format_label(key),
            "is_bool": False,
            "raw": value,
        }
    return parsed


def _format_label(key: str) -> str:
    return key.replace("_", " ").title()


def apply_adjustments(img: Image.Image, adjustments: dict) -> Image.Image:
    """
    Apply a set of Lightroom-style adjustments to a PIL image.

    `adjustments` is a dict like:
        {"exposure": 0.15, "contrast": 10, "highlights": -15, ...}

    Each key maps to a Lightroom slider name and the value is the
    amount to apply (a single number within the slider's range).
    """
    img = img.convert("RGB")
    arr = np.array(img, dtype=np.float64)

    for key, value in adjustments.items():
        if value is None:
            continue
        key_lower = key.lower()

        if key_lower == "exposure":
            factor = 1.0 + float(value)
            arr = arr * factor

        elif key_lower == "contrast":
            factor = 1.0 + float(value) / 100.0
            mean = arr.mean()
            arr = (arr - mean) * factor + mean

        elif key_lower == "highlights":
            strength = float(value) / 100.0
            mask = arr / 255.0
            mask = np.clip((mask - 0.5) * 2.0, 0, 1)
            arr = arr + (strength * mask * 255.0)

        elif key_lower == "shadows":
            strength = float(value) / 100.0
            mask = 1.0 - (arr / 255.0)
            mask = np.clip((mask - 0.5) * 2.0, 0, 1)
            arr = arr + (strength * mask * 255.0)

        elif key_lower == "whites":
            strength = float(value) / 100.0
            mask = np.clip(arr / 255.0, 0.8, 1.0)
            mask = (mask - 0.8) / 0.2
            arr = arr + (strength * mask * 60.0)

        elif key_lower == "blacks":
            strength = float(value) / 100.0
            mask = 1.0 - np.clip(arr / 255.0, 0, 0.2) / 0.2
            arr = arr + (strength * mask * 60.0)

        elif key_lower in ("temp", "temperature"):
            shift = float(value)
            arr[:, :, 0] = arr[:, :, 0] + shift * 1.5
            arr[:, :, 2] = arr[:, :, 2] - shift * 1.5

        elif key_lower == "tint":
            shift = float(value)
            arr[:, :, 1] = arr[:, :, 1] + shift * 1.2

        elif key_lower in ("vibrance", "saturation"):
            factor = 1.0 + float(value) / 100.0
            gray = arr.mean(axis=2, keepdims=True)
            if key_lower == "vibrance":
                sat = np.std(arr, axis=2, keepdims=True) / 128.0
                blend = np.clip(1.0 - sat, 0.3, 1.0)
                arr = gray + (arr - gray) * (1.0 + (factor - 1.0) * blend)
            else:
                arr = gray + (arr - gray) * factor

        elif key_lower == "clarity":
            val = float(value)
            if abs(val) > 0.5:
                img_temp = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
                blurred = img_temp.filter(ImageFilter.GaussianBlur(radius=10))
                blur_arr = np.array(blurred, dtype=np.float64)
                detail = arr - blur_arr
                arr = arr + detail * (val / 50.0)

        elif key_lower == "texture":
            val = float(value)
            if abs(val) > 0.5:
                img_temp = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
                blurred = img_temp.filter(ImageFilter.GaussianBlur(radius=3))
                blur_arr = np.array(blurred, dtype=np.float64)
                detail = arr - blur_arr
                arr = arr + detail * (val / 50.0)

        elif key_lower in ("sharpening", "sharpness"):
            val = float(value)
            if val > 0:
                img_temp = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
                factor = 1.0 + val / 50.0
                img_temp = ImageEnhance.Sharpness(img_temp).enhance(factor)
                arr = np.array(img_temp, dtype=np.float64)

        elif key_lower == "dehaze":
            val = float(value) / 100.0
            arr = arr + val * 20.0
            factor = 1.0 + val * 0.1
            mean = arr.mean()
            arr = (arr - mean) * factor + mean

        elif key_lower == "noise_reduction":
            val = float(value)
            if val > 5:
                radius = max(1, int(val / 15))
                img_temp = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
                img_temp = img_temp.filter(ImageFilter.GaussianBlur(radius=radius))
                blur_arr = np.array(img_temp, dtype=np.float64)
                blend = min(val / 50.0, 0.7)
                arr = arr * (1 - blend) + blur_arr * blend

        elif key_lower == "vignette":
            val = float(value) / 100.0
            h, w = arr.shape[:2]
            y, x = np.mgrid[0:h, 0:w].astype(np.float64)
            cx, cy = w / 2.0, h / 2.0
            max_dist = np.sqrt(cx**2 + cy**2)
            dist = np.sqrt((x - cx)**2 + (y - cy)**2) / max_dist
            vignette = 1.0 + val * (dist ** 2)
            arr = arr * vignette[:, :, np.newaxis]

        elif key_lower == "convert_to_bw":
            if value:
                gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
                arr[:, :, 0] = gray
                arr[:, :, 1] = gray
                arr[:, :, 2] = gray

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def crop_image(img: Image.Image, x: float, y: float, w: float, h: float) -> Image.Image:
    """
    Crop image using percentage-based coordinates.

    x, y, w, h are all 0-100 percentages of the image dimensions.
    """
    img_w, img_h = img.size
    left = int(img_w * x / 100)
    top = int(img_h * y / 100)
    right = int(img_w * (x + w) / 100)
    bottom = int(img_h * (y + h) / 100)

    left = max(0, min(left, img_w))
    top = max(0, min(top, img_h))
    right = max(left + 1, min(right, img_w))
    bottom = max(top + 1, min(bottom, img_h))

    return img.crop((left, top, right, bottom))
