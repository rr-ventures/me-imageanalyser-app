"""
Parse and validate Gemini's metadata response.

Gemini returns JSON text. This module:
1. Extracts JSON from the response (handling markdown fences if present)
2. Validates every field against the expected types and allowed values
3. Returns None if validation fails (strict mode)
"""
import json
import re

VALID_SCENE_TYPES = {"outdoor", "indoor", "urban", "nightlife", "unknown"}
VALID_LIGHTING = {"natural_warm", "natural_cool", "golden_hour", "artificial", "mixed", "unknown"}
VALID_FACE_VISIBLE = {"yes", "partial", "no"}
VALID_EXPRESSION = {"warm", "neutral", "serious", "unknown"}
VALID_COLOR_QUALITY = {"good", "flat", "bad_mix", "unknown"}


def _extract_json(text: str) -> str | None:
    """Pull JSON from response text, handling markdown fences."""
    text = text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            return match.group(1).strip()
    if text.startswith("{"):
        return text
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    return None


def parse_metadata_response(text: str) -> dict | None:
    """
    Parse Gemini's response into validated metadata.

    Returns a dict with all 6 fields if valid, or None if anything is wrong.
    This is strict: if Gemini returns garbage, we reject the whole response
    rather than guessing.
    """
    json_str = _extract_json(text)
    if not json_str:
        return None

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    scene_type = data.get("scene_type")
    lighting = data.get("lighting")
    face_visible = data.get("face_visible")
    expression = data.get("expression")
    color_quality = data.get("color_quality")
    photo_quality = data.get("photo_quality")

    if scene_type not in VALID_SCENE_TYPES:
        return None
    if lighting not in VALID_LIGHTING:
        return None
    if face_visible not in VALID_FACE_VISIBLE:
        return None
    if expression not in VALID_EXPRESSION:
        return None
    if color_quality not in VALID_COLOR_QUALITY:
        return None

    if not isinstance(photo_quality, (int, float)):
        return None
    photo_quality = int(round(photo_quality))
    if photo_quality < 0:
        photo_quality = 0
    if photo_quality > 10:
        photo_quality = 10

    return {
        "scene_type": scene_type,
        "lighting": lighting,
        "photo_quality": photo_quality,
        "face_visible": face_visible,
        "expression": expression,
        "color_quality": color_quality,
    }
