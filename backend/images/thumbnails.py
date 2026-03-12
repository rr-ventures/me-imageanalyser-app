"""
Thumbnail generation for the photo grid UI.

Creates small preview images so the React frontend can display
a grid of 500+ photos without loading full-resolution images.
Thumbnails are always EXIF-rotation-corrected.
"""
import hashlib
from pathlib import Path

from PIL import Image

from backend import config
from backend.images.processor import fix_orientation

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def _thumbnail_path(image_path: Path) -> Path:
    path_hash = hashlib.md5(str(image_path.resolve()).encode()).hexdigest()[:12]
    return config.THUMBNAILS_DIR / f"{path_hash}.jpg"


def get_or_create_thumbnail(image_path: Path) -> Path:
    thumb_path = _thumbnail_path(image_path)

    if thumb_path.exists():
        return thumb_path

    config.THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.open(image_path)
    try:
        img = fix_orientation(img)
        img = img.convert("RGB")
        img.thumbnail(config.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        img.save(thumb_path, format="JPEG", quality=80)
    finally:
        img.close()

    return thumb_path


def clear_thumbnails() -> int:
    """Remove all cached thumbnails. Returns count of files removed."""
    if not config.THUMBNAILS_DIR.exists():
        return 0
    count = 0
    for f in config.THUMBNAILS_DIR.glob("*.jpg"):
        f.unlink()
        count += 1
    return count
