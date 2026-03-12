"""
Configuration for the Lightroom Preset Selector backend.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "to_process"
OUTPUT_DIR = DATA_DIR / "processed"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
RUNS_DIR = DATA_DIR / "runs"
LIBRARY_DIR = PROJECT_ROOT / "library"
LIBRARY_PATH = LIBRARY_DIR / "dating_profile_filter_library_v2.yml"
PRESET_RECOMMENDATIONS_PATH = LIBRARY_DIR / "lightroom_preset_recommendations.yml"

# ── Gemini Models ────────────────────────────────────────────────────────────
# Each model has a display name, ID, and pricing per 1M tokens.
# Users can pick which model to use for analysis vs editing.

AVAILABLE_MODELS = {
    "gemini-2.0-flash": {
        "display_name": "Gemini 2.0 Flash",
        "description": "Cheapest and fastest. Good enough for metadata extraction.",
        "input_per_1m": 0.10,
        "output_per_1m": 0.40,
        "supports_images": True,
    },
    "gemini-2.5-flash": {
        "display_name": "Gemini 2.5 Flash",
        "description": "Fast and affordable. Great balance of speed and accuracy.",
        "input_per_1m": 0.15,
        "output_per_1m": 0.60,
        "supports_images": True,
    },
    "gemini-2.5-pro": {
        "display_name": "Gemini 2.5 Pro",
        "description": "Most accurate for analysis. Higher cost.",
        "input_per_1m": 1.25,
        "output_per_1m": 10.00,
        "supports_images": True,
    },
}

DEFAULT_ANALYSIS_MODEL = "gemini-2.5-flash"

# ── Image Processing ─────────────────────────────────────────────────────────

MAX_ANALYSIS_SIZE_PX = 1024
THUMBNAIL_SIZE = (300, 300)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tiff", ".bmp"}
ANALYSIS_CONCURRENCY = 5
BATCH_SIZE = 20

MIN_RESOLUTION_SHORT_SIDE = 1080
TARGET_UPSCALE_RESOLUTION = 2048
EDIT_MODEL = "gemini-2.0-flash-exp"

# ── Cost Estimation ──────────────────────────────────────────────────────────
# Rough estimates for per-image token usage (varies by image size and model)

ESTIMATED_PROMPT_TOKENS_PER_IMAGE = 300
ESTIMATED_IMAGE_TOKENS_PER_IMAGE = 1200
ESTIMATED_OUTPUT_TOKENS_PER_IMAGE = 200
