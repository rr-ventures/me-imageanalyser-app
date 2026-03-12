"""
Image processing utilities.

Handles resizing, format conversion, and EXIF orientation fixes.
"""
import io
from pathlib import Path

from PIL import Image
from PIL.ExifTags import Base as ExifBase

from backend import config

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def fix_orientation(img: Image.Image) -> Image.Image:
    """Apply EXIF orientation tag so the image displays correctly."""
    try:
        exif = img.getexif()
        orientation = exif.get(ExifBase.Orientation, 1)
        rotations = {3: 180, 6: 270, 8: 90}
        if orientation in rotations:
            img = img.rotate(rotations[orientation], expand=True)
    except Exception:
        pass
    return img


def prepare_for_analysis(path: Path) -> tuple[bytes, str]:
    """
    Load an image, fix orientation, resize for API, and return as JPEG bytes.

    This is what gets sent to Gemini — a reasonably-sized JPEG.
    """
    img = Image.open(path)
    try:
        img = fix_orientation(img)
        img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > config.MAX_ANALYSIS_SIZE_PX:
            ratio = config.MAX_ANALYSIS_SIZE_PX / max(w, h)
            img = img.resize(
                (int(w * ratio), int(h * ratio)),
                Image.Resampling.LANCZOS,
            )
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"
    finally:
        img.close()


def get_dimensions(path: Path) -> tuple[int, int]:
    """Get image dimensions without loading the full image into memory."""
    img = Image.open(path)
    try:
        return img.size
    finally:
        img.close()
