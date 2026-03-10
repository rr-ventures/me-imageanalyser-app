"""
Receipt Sorter — user config.
Paths are relative to project root (cwd when running main.py / app.py).
"""

# Input: folder to scan for images (recursive)
INPUT_DIR = "./to_process"

# Output: folder where sorted subfolders are created after GUI confirm
OUTPUT_DIR = "./sorted"

# Run history: one manifest + one errors file per analysis run
RUNS_DIR = "./runs"

# Receipts with date >= CUTOFF_DATE go to receipts_keep; older → receipts_old
CUTOFF_DATE = "2025-03-01"

# Gemini model and analysis settings
MODEL = "gemini-2.0-flash"
CONCURRENCY = 10
MAX_IMAGE_SIZE_PX = 1024
BATCH_SIZE = 50

# Test mode: only analyze this many images (used with --test flag)
TEST_SAMPLE_SIZE = 10

# Supported image extensions (lowercase)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tiff", ".bmp"}

# Bucket names (must match sorter.py folder creation)
BUCKETS = (
    "receipts_keep",
    "receipts_old",
    "invoices_docs",
    "photos_screenshots",
    "unknown",
)
