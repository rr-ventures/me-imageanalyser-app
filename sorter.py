"""
Receipt Sorter — Move approved images into bucket folders. No action until explicitly executed.
"""
import json
import shutil
from pathlib import Path

import config


def execute(
    manifest_path_or_data: str | Path | dict,
    output_dir: str | Path,
    runs_dir: str | Path,
) -> dict:
    """
    Move only rows where approved is True. Destination: user_folder if set, else suggested_folder.
    Creates bucket folders under output_dir. On filename collision appends _1, _2, etc.
    Saves final state to runs/{run_id}_sorted_manifest.json and returns summary.
    """
    output_dir = Path(output_dir).resolve()
    runs_dir = Path(runs_dir).resolve()

    if isinstance(manifest_path_or_data, dict):
        manifest = manifest_path_or_data
        run_id = manifest.get("run_id", "unknown")
    else:
        path = Path(manifest_path_or_data).resolve()
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
        run_id = manifest.get("run_id", path.stem)

    images = manifest.get("images", [])
    approved = [row for row in images if row.get("approved")]
    if not approved:
        return {"moved": 0, "per_folder": {}, "errors": [], "sorted_manifest_path": None}

    for bucket in config.BUCKETS:
        (output_dir / bucket).mkdir(parents=True, exist_ok=True)

    per_folder: dict[str, int] = {b: 0 for b in config.BUCKETS}
    errors: list[str] = []
    used_names: dict[str, set[str]] = {b: set() for b in config.BUCKETS}

    for row in approved:
        folder = (row.get("user_folder") or row.get("suggested_folder") or "unknown").strip()
        if folder not in config.BUCKETS:
            folder = "unknown"
        src = Path(row["original_path"])
        if not src.exists():
            errors.append(f"Missing file: {src}")
            continue
        dest_dir = output_dir / folder
        base_name = src.name
        stem = src.stem
        suffix = src.suffix
        dest_name = base_name
        while (dest_dir / dest_name).exists() or dest_name in used_names[folder]:
            # Collision: append _1, _2, ...
            if dest_name == base_name:
                next_num = 1
            else:
                try:
                    next_num = int(dest_name.rsplit("_", 1)[-1]) + 1
                except (ValueError, IndexError):
                    next_num = 1
            dest_name = f"{stem}_{next_num}{suffix}"
        try:
            shutil.move(str(src), str(dest_dir / dest_name))
            used_names[folder].add(dest_name)
            per_folder[folder] = per_folder.get(folder, 0) + 1
        except OSError as e:
            errors.append(f"{src}: {e}")

    # Build sorted manifest (same structure + sorted metadata)
    sorted_manifest = dict(manifest)
    sorted_manifest["sorted_at"] = __import__("datetime").datetime.now().isoformat()
    sorted_manifest["output_dir"] = str(output_dir)
    sorted_manifest["moved_per_folder"] = per_folder
    sorted_manifest["errors"] = errors
    # Mark moved rows (optional: add destination path to each image)
    for row in sorted_manifest.get("images", []):
        if row.get("approved"):
            folder = (row.get("user_folder") or row.get("suggested_folder") or "unknown").strip()
            if folder not in config.BUCKETS:
                folder = "unknown"
            row["moved_to_folder"] = folder

    sorted_path = runs_dir / f"{run_id}_sorted_manifest.json"
    with open(sorted_path, "w", encoding="utf-8") as f:
        json.dump(sorted_manifest, f, indent=2)

    return {
        "moved": sum(per_folder.values()),
        "per_folder": per_folder,
        "errors": errors,
        "sorted_manifest_path": str(sorted_path),
    }
