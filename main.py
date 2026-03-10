"""
Receipt Sorter — Phase 1: scan, batch analyze with Gemini, incremental save, resume support.

Usage:
  python main.py            # analyze all new images in batches of BATCH_SIZE
  python main.py --test     # analyze only TEST_SAMPLE_SIZE images (quick quality check)
  python main.py --resume   # resume an incomplete run
"""
import argparse
import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import config
from analyzer import analyze_batch, file_hash

load_dotenv()


def scan_image_paths(input_dir: Path) -> list[Path]:
    """Recursively find supported image files. Returns sorted list."""
    paths = []
    for ext in config.SUPPORTED_EXTENSIONS:
        paths.extend(input_dir.rglob(f"*{ext}"))
        paths.extend(input_dir.rglob(f"*{ext.upper()}"))
    # Deduplicate (upper/lower might overlap)
    seen = set()
    unique = []
    for p in sorted(paths, key=lambda p: str(p).lower()):
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def run_signature(paths: list[Path], base: Path) -> str:
    rel = sorted(str(p.relative_to(base)) for p in paths if p.is_relative_to(base))
    return hashlib.sha256("\n".join(rel).encode()).hexdigest()


def already_analyzed_hashes(runs_dir: Path) -> set[str]:
    """Collect file_hashes from all previous run manifests (for skip-already-analyzed)."""
    hashes: set[str] = set()
    if not runs_dir.exists():
        return hashes
    for f in runs_dir.glob("*.json"):
        if f.name.endswith("_errors.json") or f.name.endswith("_sorted_manifest.json"):
            continue
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            for img in data.get("images", []):
                h = img.get("file_hash")
                if h:
                    hashes.add(h)
        except (json.JSONDecodeError, OSError):
            continue
    return hashes


def find_incomplete_run(runs_dir: Path) -> Path | None:
    """Find a run manifest marked as incomplete (for resume)."""
    if not runs_dir.exists():
        return None
    for f in sorted(runs_dir.glob("*.json"), reverse=True):
        if f.name.endswith("_errors.json") or f.name.endswith("_sorted_manifest.json"):
            continue
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            if data.get("status") == "incomplete":
                return f
        except (json.JSONDecodeError, OSError):
            continue
    return None


def save_manifest(path: Path, manifest: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Receipt Sorter — Phase 1 analysis")
    parser.add_argument("--test", action="store_true", help=f"Only analyze {config.TEST_SAMPLE_SIZE} images for quality check")
    parser.add_argument("--resume", action="store_true", help="Resume an incomplete run")
    args = parser.parse_args()

    input_dir = Path(config.INPUT_DIR).resolve()
    runs_dir = Path(config.RUNS_DIR).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        sys.exit(1)

    # --- Resume mode ---
    if args.resume:
        incomplete = find_incomplete_run(runs_dir)
        if not incomplete:
            print("No incomplete run found to resume.")
            sys.exit(0)
        manifest = json.loads(incomplete.read_text(encoding="utf-8"))
        done_hashes = {img["file_hash"] for img in manifest.get("images", []) if img.get("file_hash")}
        all_paths = scan_image_paths(input_dir)
        remaining = [p for p in all_paths if file_hash(p) not in done_hashes]
        if not remaining:
            manifest["status"] = "complete"
            save_manifest(incomplete, manifest)
            print("All images already analyzed. Run marked complete.")
            print("Run: streamlit run app.py")
            return
        print(f"Resuming {incomplete.name}: {len(remaining)} images remaining ({len(manifest.get('images', []))} already done)")
        _run_batches(remaining, manifest, incomplete, runs_dir)
        return

    # --- Normal mode ---
    all_paths = scan_image_paths(input_dir)
    if not all_paths:
        print(f"No supported images found in {input_dir}.")
        sys.exit(0)

    # Skip images already analyzed in previous runs
    known = already_analyzed_hashes(runs_dir)
    if known:
        new_paths = []
        for p in all_paths:
            h = file_hash(p)
            if h not in known:
                new_paths.append(p)
        skipped = len(all_paths) - len(new_paths)
        if skipped:
            print(f"Skipping {skipped} image(s) already analyzed in previous runs.")
        paths = new_paths
    else:
        paths = all_paths

    if not paths:
        print("All images already analyzed. Nothing new to process.")
        print("Run: streamlit run app.py")
        sys.exit(0)

    # Test mode: sample
    if args.test:
        paths = paths[: config.TEST_SAMPLE_SIZE]
        print(f"TEST MODE: analyzing only {len(paths)} images")

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    manifest_path = runs_dir / f"{ts}.json"

    rel_paths = sorted(str(p.relative_to(input_dir)) for p in all_paths if p.is_relative_to(input_dir))
    manifest = {
        "run_id": ts,
        "processed_files_hash": run_signature(all_paths, input_dir),
        "processed_file_list": rel_paths,
        "input_dir": str(input_dir),
        "status": "incomplete",
        "test_mode": args.test,
        "images": [],
        "errors": [],
        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    save_manifest(manifest_path, manifest)

    _run_batches(paths, manifest, manifest_path, runs_dir)


def _run_batches(paths: list[Path], manifest: dict, manifest_path: Path, runs_dir: Path) -> None:
    """Process paths in batches of BATCH_SIZE, saving incrementally after each batch."""
    batch_size = config.BATCH_SIZE
    total = len(paths)
    batches = [paths[i : i + batch_size] for i in range(0, total, batch_size)]
    global_done = len(manifest.get("images", []))

    for batch_num, batch in enumerate(batches, 1):
        print(f"\n--- Batch {batch_num}/{len(batches)} ({len(batch)} images) ---")

        def progress(done: int, batch_total: int) -> None:
            overall = global_done + done
            print(f"  Analyzing {overall}/{global_done + batch_total} (overall {overall}/{global_done + total})…", end="\r")

        results, errors, usage = asyncio.run(
            analyze_batch(batch, progress_callback=progress)
        )
        print()

        manifest["images"].extend(results)
        manifest["errors"].extend(errors)
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            manifest["token_usage"][k] += usage.get(k, 0)
        global_done += len(batch)

        # Save after each batch so progress survives crashes
        save_manifest(manifest_path, manifest)
        print(f"  Saved: {len(results)} results, {len(errors)} errors (batch {batch_num})")

        if errors:
            errors_path = manifest_path.with_name(manifest_path.stem + "_errors.json")
            with open(errors_path, "w", encoding="utf-8") as f:
                json.dump(manifest["errors"], f, indent=2)

    manifest["status"] = "complete"
    save_manifest(manifest_path, manifest)

    tok = manifest["token_usage"]
    # Gemini 2.0 Flash pricing: ~$0.10/1M input, ~$0.40/1M output (approximate)
    est_cost = (tok["prompt_tokens"] * 0.10 + tok["completion_tokens"] * 0.40) / 1_000_000
    print(f"\nAnalysis complete.")
    print(f"  Images analyzed: {len(manifest['images'])}")
    print(f"  Errors: {len(manifest['errors'])}")
    print(f"  Tokens — prompt: {tok['prompt_tokens']:,}  completion: {tok['completion_tokens']:,}  total: {tok['total_tokens']:,}")
    print(f"  Estimated cost: ${est_cost:.4f}")
    print(f"\nRun: streamlit run app.py")


if __name__ == "__main__":
    main()
