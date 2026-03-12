"""
Matches photo metadata to Lightroom preset recommendations.

Loads the preset recommendations artifact and finds the best
matching scenario for a given set of photo metadata.
"""
import yaml
from backend import config

_cached: dict | None = None


def _load():
    global _cached
    if _cached is not None:
        return _cached
    path = config.PRESET_RECOMMENDATIONS_PATH
    if not path.exists():
        _cached = {"scenarios": [], "danger_zones": []}
        return _cached
    with open(path, "r", encoding="utf-8") as f:
        _cached = yaml.safe_load(f) or {}
    return _cached


def reload():
    global _cached
    _cached = None
    return _load()


def _matches(conditions: dict, metadata: dict) -> int:
    """Return match score (higher = more specific match). 0 = no match."""
    if not conditions:
        return 0
    score = 0
    for key, expected in conditions.items():
        actual = metadata.get(key)
        if actual is None:
            continue
        if isinstance(expected, list):
            if isinstance(actual, int):
                if actual >= expected[0] and actual <= expected[-1]:
                    score += 1
                else:
                    return 0
            elif actual in expected:
                score += 1
            else:
                return 0
        else:
            if actual == expected:
                score += 1
            else:
                return 0
    return score


def get_recommendation(metadata: dict) -> dict | None:
    """
    Given photo metadata, find the best matching preset recommendation.
    Returns the scenario dict with preset info, or None.
    """
    data = _load()
    scenarios = data.get("scenarios", [])

    best = None
    best_score = 0

    for scenario in scenarios:
        conditions = scenario.get("conditions", {})
        score = _matches(conditions, metadata)
        if score > best_score:
            best_score = score
            best = scenario

    if best and best_score > 0:
        return best

    fallback = next(
        (s for s in scenarios if s.get("id") == "outdoor_overcast"),
        scenarios[0] if scenarios else None,
    )
    return fallback


def get_danger_zones() -> list:
    data = _load()
    return data.get("danger_zones", [])
