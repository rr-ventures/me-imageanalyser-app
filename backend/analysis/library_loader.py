"""
Load and cache the YAML style library.

The library is loaded once on first use and cached in memory.
This is a "lazy singleton" pattern — the file is only read when
something actually needs it, and then it stays in memory so we
don't re-read the file on every request.
"""
import yaml

from backend import config

_cached_library: dict | None = None


def load_library() -> dict:
    """
    Load the YAML style library. Cached after first call.

    Returns the full library dict with styles, routing rules, etc.
    """
    global _cached_library
    if _cached_library is not None:
        return _cached_library

    with open(config.LIBRARY_PATH, "r", encoding="utf-8") as f:
        _cached_library = yaml.safe_load(f)

    return _cached_library


def get_styles() -> dict:
    """Get just the styles section of the library."""
    return load_library().get("styles", {})


def get_routing_rules() -> list[dict]:
    """Get the primary routing rules."""
    lib = load_library()
    return lib.get("selection_logic", {}).get("primary_routing", [])


def get_secondary_pairing() -> dict:
    """Get the secondary style pairing map."""
    lib = load_library()
    return lib.get("selection_logic", {}).get("secondary_pairing", {})


def get_style_plans(style_name: str) -> dict | None:
    """
    Get the Lightroom plans for a specific style.

    Returns a dict with 'lightroom' key, or None if the style doesn't exist.
    """
    styles = get_styles()
    style = styles.get(style_name)
    if not style:
        return None
    return {
        "display_name": style.get("display_name", style_name),
        "description": style.get("description", ""),
        "when_to_use": style.get("when_to_use", ""),
        "dating_impact": style.get("dating_impact", ""),
        "lightroom": style.get("lightroom", {}),
    }


def reload_library() -> dict:
    """Force reload the library from disk (useful after edits)."""
    global _cached_library
    _cached_library = None
    return load_library()
