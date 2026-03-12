"""
Shared test fixtures — reusable test data.

WHAT IS A FIXTURE?
A fixture is a piece of test data that multiple tests can share.
Instead of copy-pasting the same fake metadata into every test,
we define it once here and import it.

HOW FIXTURES WORK:
pytest automatically discovers this file (conftest.py) and makes
its fixtures available to all tests in this folder.
"""
import pytest


@pytest.fixture
def golden_hour_outdoor():
    """Fake metadata for a classic golden hour outdoor photo."""
    return {
        "scene_type": "outdoor",
        "lighting": "golden_hour",
        "photo_quality": 8,
        "face_visible": "yes",
        "expression": "warm",
        "color_quality": "good",
    }


@pytest.fixture
def flat_indoor_daylight():
    """Fake metadata for a bright indoor photo that looks flat/dull."""
    return {
        "scene_type": "indoor",
        "lighting": "natural_warm",
        "photo_quality": 6,
        "face_visible": "yes",
        "expression": "neutral",
        "color_quality": "flat",
    }


@pytest.fixture
def strong_lead_photo():
    """Fake metadata for an already good lead photo — minimal editing needed."""
    return {
        "scene_type": "outdoor",
        "lighting": "natural_warm",
        "photo_quality": 9,
        "face_visible": "yes",
        "expression": "warm",
        "color_quality": "good",
    }


@pytest.fixture
def urban_portrait():
    """Fake metadata for a city/urban portrait with good quality."""
    return {
        "scene_type": "urban",
        "lighting": "natural_cool",
        "photo_quality": 7,
        "face_visible": "yes",
        "expression": "serious",
        "color_quality": "good",
    }


@pytest.fixture
def nightlife_photo():
    """Fake metadata for a bar/club photo with mixed lighting."""
    return {
        "scene_type": "nightlife",
        "lighting": "mixed",
        "photo_quality": 5,
        "face_visible": "yes",
        "expression": "warm",
        "color_quality": "bad_mix",
    }


@pytest.fixture
def bad_color_photo():
    """Fake metadata for a photo with terrible color — B&W rescue candidate."""
    return {
        "scene_type": "indoor",
        "lighting": "artificial",
        "photo_quality": 4,
        "face_visible": "yes",
        "expression": "neutral",
        "color_quality": "bad_mix",
    }


@pytest.fixture
def low_quality_photo():
    """Fake metadata for a low quality photo — should get safe default."""
    return {
        "scene_type": "unknown",
        "lighting": "unknown",
        "photo_quality": 3,
        "face_visible": "partial",
        "expression": "unknown",
        "color_quality": "unknown",
    }


@pytest.fixture
def no_face_photo():
    """Fake metadata for a photo where you can't see the face."""
    return {
        "scene_type": "outdoor",
        "lighting": "natural_warm",
        "photo_quality": 7,
        "face_visible": "no",
        "expression": "unknown",
        "color_quality": "good",
    }
