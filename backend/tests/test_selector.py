"""
=============================================================================
TEST: Style Selector
=============================================================================

WHAT THIS FILE TESTS:
    The style selector — the code that looks at photo metadata and picks
    the best 2 edit styles from the YAML library.

WHY IT MATTERS:
    If the selector picks the wrong style, your dating profile photos get
    the wrong edits. These tests make sure each type of photo gets matched
    to the correct style.

HOW TO RUN:
    cd /workspaces/me-imageanalyser-app
    python -m pytest backend/tests/test_selector.py -v

WHAT TO LOOK FOR IN OUTPUT:
    Each test name describes a scenario:
    - test_golden_hour_outdoor_gets_warm_golden
      → "If the photo is golden hour + outdoor, does it pick warm_golden?"
    - PASSED = correct, FAILED = broken

=============================================================================
"""
from backend.analysis.selector import select_styles_from_dict


# ── Test 1: Golden hour outdoor → warm_golden ─────────────────────────────

def test_golden_hour_outdoor_gets_warm_golden(golden_hour_outdoor):
    """
    SCENARIO: A beautiful sunset photo taken outdoors.
    EXPECTED: Primary style should be 'warm_golden' because golden_hour
              lighting + outdoor scene is the #1 trigger for this style.
    """
    result = select_styles_from_dict(golden_hour_outdoor)

    assert result["primary_style"] == "warm_golden", (
        f"Expected warm_golden but got {result['primary_style']}. "
        f"Golden hour + outdoor should always pick warm_golden."
    )
    assert result["secondary_style"] == "true_to_life_clean", (
        f"warm_golden's secondary should be true_to_life_clean"
    )
    print(f"  ✓ Golden hour outdoor → {result['primary_style']} + {result['secondary_style']}")


# ── Test 2: Flat daylight → bright_airy ──────────────────────────────────

def test_flat_daylight_gets_bright_airy(flat_indoor_daylight):
    """
    SCENARIO: An indoor photo with natural light but the colors look flat/dull.
    EXPECTED: Primary style should be 'bright_airy' because flat color quality
              with natural lighting triggers the brightness-lift style.
    """
    result = select_styles_from_dict(flat_indoor_daylight)

    assert result["primary_style"] == "bright_airy", (
        f"Expected bright_airy but got {result['primary_style']}. "
        f"Natural light + flat colors should pick bright_airy."
    )
    print(f"  ✓ Flat daylight → {result['primary_style']}")


# ── Test 3: Strong lead photo → true_to_life_clean ──────────────────────

def test_strong_lead_photo_gets_true_to_life(strong_lead_photo):
    """
    SCENARIO: An already great photo — good quality, good colors, warm expression.
    EXPECTED: Primary style should be 'true_to_life_clean' because a photo
              that's already good just needs a minimal polish, not a heavy style.
    """
    result = select_styles_from_dict(strong_lead_photo)

    assert result["primary_style"] == "true_to_life_clean", (
        f"Expected true_to_life_clean but got {result['primary_style']}. "
        f"High quality + good colors should default to true_to_life_clean."
    )
    print(f"  ✓ Strong lead photo → {result['primary_style']}")


# ── Test 4: Urban portrait → moody_cinematic ─────────────────────────────

def test_urban_portrait_gets_moody_cinematic(urban_portrait):
    """
    SCENARIO: A portrait taken in the city with good quality.
    EXPECTED: Primary style should be 'moody_cinematic' because urban scene
              + decent quality triggers the cinematic style.
    """
    result = select_styles_from_dict(urban_portrait)

    assert result["primary_style"] == "moody_cinematic", (
        f"Expected moody_cinematic but got {result['primary_style']}. "
        f"Urban scene + quality >= 6 should pick moody_cinematic."
    )
    print(f"  ✓ Urban portrait → {result['primary_style']}")


# ── Test 5: Nightlife photo → nightlife_contrast ─────────────────────────

def test_nightlife_gets_nightlife_contrast(nightlife_photo):
    """
    SCENARIO: A photo from a bar or club with mixed lighting.
    EXPECTED: Primary style should be 'nightlife_contrast' because
              scene_type == nightlife is the trigger.
    """
    result = select_styles_from_dict(nightlife_photo)

    assert result["primary_style"] == "nightlife_contrast", (
        f"Expected nightlife_contrast but got {result['primary_style']}. "
        f"Nightlife scene should always pick nightlife_contrast."
    )
    print(f"  ✓ Nightlife photo → {result['primary_style']}")


# ── Test 6: Bad color photo → black_white ────────────────────────────────

def test_bad_color_gets_black_white(bad_color_photo):
    """
    SCENARIO: A photo with terrible color — mixed lighting, weird color casts.
    EXPECTED: Primary style should be 'black_white' because bad_mix color
              quality triggers the B&W rescue style.
    """
    result = select_styles_from_dict(bad_color_photo)

    assert result["primary_style"] == "black_white", (
        f"Expected black_white but got {result['primary_style']}. "
        f"Bad mixed colors should trigger black_white rescue."
    )
    print(f"  ✓ Bad color photo → {result['primary_style']}")


# ── Test 7: Low quality → true_to_life_clean (safe default) ─────────────

def test_low_quality_gets_safe_default(low_quality_photo):
    """
    SCENARIO: A low quality photo where nothing is clear.
    EXPECTED: Primary style should be 'true_to_life_clean' because when
              nothing matches strongly, we fall back to the safe default.
    """
    result = select_styles_from_dict(low_quality_photo)

    assert result["primary_style"] == "true_to_life_clean", (
        f"Expected true_to_life_clean but got {result['primary_style']}. "
        f"Low quality + unknown everything should default to safe style."
    )
    print(f"  ✓ Low quality photo → {result['primary_style']}")


# ── Test 8: Every result has required fields ─────────────────────────────

def test_result_has_all_required_fields(golden_hour_outdoor):
    """
    SCENARIO: Any analysis result.
    EXPECTED: The result dict should contain all the fields the frontend needs:
              primary/secondary style, plans, reason, and metadata.
    """
    result = select_styles_from_dict(golden_hour_outdoor)

    required_fields = [
        "primary_style",
        "secondary_style",
        "selection_reason",
        "primary_lightroom_plan",
        "secondary_lightroom_plan",
        "metadata",
    ]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

    assert isinstance(result["metadata"], dict)
    assert "scene_type" in result["metadata"]
    print(f"  ✓ Result has all {len(required_fields)} required fields")


# ── Test 9: Secondary style is always different from primary ─────────────

def test_secondary_is_different_from_primary(golden_hour_outdoor, urban_portrait, nightlife_photo):
    """
    SCENARIO: Any analysis result.
    EXPECTED: The secondary style should never be the same as primary.
              Having two identical recommendations is useless.
    """
    for metadata in [golden_hour_outdoor, urban_portrait, nightlife_photo]:
        result = select_styles_from_dict(metadata)
        assert result["primary_style"] != result["secondary_style"], (
            f"Primary and secondary are both '{result['primary_style']}' — "
            f"they should be different styles."
        )
    print(f"  ✓ Secondary style is always different from primary")


# ── Test 10: Plans contain Lightroom data ─────────────────────────────

def test_plans_contain_lightroom_data(golden_hour_outdoor):
    """
    SCENARIO: Any analysis result.
    EXPECTED: The plans should include actual Lightroom presets — not empty dicts.
    """
    result = select_styles_from_dict(golden_hour_outdoor)

    lr = result["primary_lightroom_plan"]

    assert "presets" in lr, "Lightroom plan should include preset recommendations"
    assert "manual_sliders" in lr, "Lightroom plan should include manual slider values"

    print(f"  ✓ Plans contain Lightroom presets + manual sliders")
