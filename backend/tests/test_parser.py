"""
=============================================================================
TEST: Gemini Response Parser
=============================================================================

WHAT THIS FILE TESTS:
    The parser that reads Gemini's JSON response and validates it.
    Gemini sometimes returns unexpected formats (markdown fences, extra text,
    garbage). The parser must handle all of this gracefully.

WHY IT MATTERS:
    If the parser accepts bad data, the selector gets wrong inputs and
    recommends wrong styles. If the parser is too strict, valid responses
    get rejected. These tests find the right balance.

HOW TO RUN:
    cd /workspaces/me-imageanalyser-app
    python -m pytest backend/tests/test_parser.py -v

=============================================================================
"""
from backend.gemini.parser import parse_metadata_response


# ── Test 1: Valid clean JSON ─────────────────────────────────────────────

def test_valid_json_parses_correctly():
    """
    SCENARIO: Gemini returns perfectly formatted JSON.
    EXPECTED: Parser returns a dict with all 6 fields.
    """
    response = '''{
        "scene_type": "outdoor",
        "lighting": "golden_hour",
        "photo_quality": 8,
        "face_visible": "yes",
        "expression": "warm",
        "color_quality": "good"
    }'''

    result = parse_metadata_response(response)

    assert result is not None, "Valid JSON should parse successfully"
    assert result["scene_type"] == "outdoor"
    assert result["lighting"] == "golden_hour"
    assert result["photo_quality"] == 8
    assert result["face_visible"] == "yes"
    assert result["expression"] == "warm"
    assert result["color_quality"] == "good"
    print(f"  ✓ Valid JSON parsed: {result}")


# ── Test 2: JSON with markdown fences ────────────────────────────────────

def test_json_with_markdown_fences():
    """
    SCENARIO: Gemini wraps JSON in ```json ... ``` fences (common behavior).
    EXPECTED: Parser strips the fences and returns valid data.
    """
    response = '''```json
    {
        "scene_type": "urban",
        "lighting": "artificial",
        "photo_quality": 6,
        "face_visible": "yes",
        "expression": "serious",
        "color_quality": "flat"
    }
    ```'''

    result = parse_metadata_response(response)
    assert result is not None, "JSON in markdown fences should still parse"
    assert result["scene_type"] == "urban"
    print(f"  ✓ Markdown-fenced JSON parsed correctly")


# ── Test 3: Completely invalid response ──────────────────────────────────

def test_invalid_json_returns_none():
    """
    SCENARIO: Gemini returns random text instead of JSON.
    EXPECTED: Parser returns None (strict mode — we reject garbage).
    """
    result = parse_metadata_response("This is not JSON at all")
    assert result is None, "Non-JSON should return None"
    print(f"  ✓ Non-JSON correctly rejected")


# ── Test 4: Empty string ────────────────────────────────────────────────

def test_empty_string_returns_none():
    """
    SCENARIO: Gemini returns an empty response.
    EXPECTED: Parser returns None.
    """
    result = parse_metadata_response("")
    assert result is None, "Empty string should return None"
    print(f"  ✓ Empty string correctly rejected")


# ── Test 5: Invalid enum value ──────────────────────────────────────────

def test_invalid_enum_returns_none():
    """
    SCENARIO: Gemini returns valid JSON but with wrong enum values.
    EXPECTED: Parser returns None because strict validation rejects
              any values not in the allowed set.
    """
    response = '''{
        "scene_type": "underwater",
        "lighting": "golden_hour",
        "photo_quality": 8,
        "face_visible": "yes",
        "expression": "warm",
        "color_quality": "good"
    }'''

    result = parse_metadata_response(response)
    assert result is None, "'underwater' is not a valid scene_type — should reject"
    print(f"  ✓ Invalid enum value correctly rejected")


# ── Test 6: Missing field ───────────────────────────────────────────────

def test_missing_field_returns_none():
    """
    SCENARIO: Gemini returns JSON but omits a required field.
    EXPECTED: Parser returns None (strict — all 6 fields are required).
    """
    response = '''{
        "scene_type": "outdoor",
        "lighting": "golden_hour",
        "photo_quality": 8,
        "face_visible": "yes",
        "expression": "warm"
    }'''

    result = parse_metadata_response(response)
    assert result is None, "Missing color_quality should reject"
    print(f"  ✓ Missing field correctly rejected")


# ── Test 7: Float quality score gets rounded ────────────────────────────

def test_float_quality_gets_rounded():
    """
    SCENARIO: Gemini returns photo_quality as 7.5 instead of 7 or 8.
    EXPECTED: Parser rounds to nearest integer (8) and accepts.
    """
    response = '''{
        "scene_type": "outdoor",
        "lighting": "natural_warm",
        "photo_quality": 7.5,
        "face_visible": "yes",
        "expression": "neutral",
        "color_quality": "good"
    }'''

    result = parse_metadata_response(response)
    assert result is not None, "Float quality should be accepted and rounded"
    assert result["photo_quality"] == 8, f"7.5 should round to 8, got {result['photo_quality']}"
    print(f"  ✓ Float quality 7.5 rounded to {result['photo_quality']}")


# ── Test 8: Quality score clamped to 0-10 range ────────────────────────

def test_quality_score_clamped():
    """
    SCENARIO: Gemini returns photo_quality outside the 0-10 range.
    EXPECTED: Parser clamps to valid range (0-10).
    """
    response = '''{
        "scene_type": "outdoor",
        "lighting": "natural_warm",
        "photo_quality": 15,
        "face_visible": "yes",
        "expression": "warm",
        "color_quality": "good"
    }'''

    result = parse_metadata_response(response)
    assert result is not None
    assert result["photo_quality"] == 10, f"15 should clamp to 10, got {result['photo_quality']}"
    print(f"  ✓ Quality score 15 clamped to {result['photo_quality']}")


# ── Test 9: JSON with extra text before/after ───────────────────────────

def test_json_with_surrounding_text():
    """
    SCENARIO: Gemini adds explanatory text around the JSON.
    EXPECTED: Parser extracts the JSON from the text.
    """
    response = '''Here is the analysis:
    {"scene_type": "nightlife", "lighting": "mixed", "photo_quality": 5, "face_visible": "yes", "expression": "warm", "color_quality": "bad_mix"}
    I hope this helps!'''

    result = parse_metadata_response(response)
    assert result is not None, "JSON embedded in text should still parse"
    assert result["scene_type"] == "nightlife"
    print(f"  ✓ JSON extracted from surrounding text")


# ── Test 10: Non-numeric quality returns none ────────────────────────────

def test_string_quality_returns_none():
    """
    SCENARIO: Gemini returns photo_quality as text like "high".
    EXPECTED: Parser returns None (strict — must be a number).
    """
    response = '''{
        "scene_type": "outdoor",
        "lighting": "natural_warm",
        "photo_quality": "high",
        "face_visible": "yes",
        "expression": "warm",
        "color_quality": "good"
    }'''

    result = parse_metadata_response(response)
    assert result is None, "String quality should be rejected"
    print(f"  ✓ String quality value correctly rejected")
