"""
Scan folders for image files.

Finds all supported image files in a directory, deduplicates them,
and returns sorted paths.
"""
import hashlib
from pathlib import Path

from backend import config


def scan_image_paths(input_dir: Path | None = None) -> list[Path]:
    """
    Find all supported image files in the input directory.

    Returns deduplicated, sorted list of image paths.
    """
    folder = input_dir or config.INPUT_DIR
    if not folder.exists():
        return []

    exts = {e.lower() for e in config.SUPPORTED_EXTENSIONS}
    paths = [
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in exts
    ]

    seen: set[Path] = set()
    unique: list[Path] = []
    for p in sorted(paths, key=lambda x: str(x).lower()):
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(p)

    return unique


def file_hash(path: Path) -> str:
    """SHA-256 hash of a file's contents. Used to detect duplicates."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_exif_orientation(img) -> int:
    """Read EXIF orientation tag. Returns 1 (normal) if not found."""
    try:
        from PIL.ExifTags import Base as ExifBase
        exif = img.getexif()
        return exif.get(ExifBase.Orientation, 1)
    except Exception:
        return 1


def _orientation_to_rotation(orientation: int) -> int:
    """Map EXIF orientation value to degrees of rotation needed."""
    return {3: 180, 6: 270, 8: 90}.get(orientation, 0)


def get_image_info(path: Path) -> dict:
    """Basic info about an image file including rotation and upscale needs."""
    try:
        from PIL import Image
        from backend import config
        img = Image.open(path)
        try:
            w, h = img.size
            orientation = _get_exif_orientation(img)
            rotation_needed = _orientation_to_rotation(orientation)
            short_side = min(w, h)
            needs_upscale = short_side < config.MIN_RESOLUTION_SHORT_SIDE

            return {
                "filename": path.name,
                "path": str(path),
                "width": w,
                "height": h,
                "size_kb": round(path.stat().st_size / 1024, 1),
                "format": img.format or path.suffix.upper().strip("."),
                "needs_rotation": rotation_needed != 0,
                "rotation_degrees": rotation_needed,
                "needs_upscale": needs_upscale,
                "short_side": short_side,
            }
        finally:
            img.close()
    except Exception as e:
        return {
            "filename": path.name,
            "path": str(path),
            "width": 0,
            "height": 0,
            "size_kb": round(path.stat().st_size / 1024, 1) if path.exists() else 0,
            "format": "unknown",
            "needs_rotation": False,
            "rotation_degrees": 0,
            "needs_upscale": False,
            "short_side": 0,
            "error": str(e),
        }
