"""
Receipt Sorter — Guided wizard GUI.
Detects what step you're on and only shows the right action. Just hit play.
"""
import asyncio
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import config
from analyzer import analyze_batch, file_hash
from main import scan_image_paths, already_analyzed_hashes, run_signature
from sorter import execute

INPUT_DIR = Path(config.INPUT_DIR).resolve()
RUNS_DIR = Path(config.RUNS_DIR).resolve()
OUTPUT_DIR = Path(config.OUTPUT_DIR).resolve()
BUCKETS = list(config.BUCKETS)
CATEGORIES = ["receipt", "invoice", "document", "photo", "screenshot", "unknown"]


# ── helpers ──────────────────────────────────────────────────────────────────

def list_runs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted(
        (f for f in RUNS_DIR.glob("*.json")
         if not f.name.endswith("_errors.json")
         and not f.name.endswith("_sorted_manifest.json")),
        key=lambda p: p.name,
        reverse=True,
    )


def load_manifest(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_manifest(manifest: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def flag_duplicates(images: list[dict]) -> None:
    seen: dict[str, str] = {}
    for img in images:
        h = img.get("file_hash")
        if not h:
            continue
        if h in seen:
            img["duplicate_of"] = seen[h]
        else:
            seen[h] = img["filename"]
            img.pop("duplicate_of", None)


def resolve_path(img: dict) -> Path:
    p = Path(img["original_path"])
    return p if p.is_absolute() else INPUT_DIR / p


def detect_step():
    """
    Figure out where the user is in the workflow.
    Returns one of: 'no_images', 'no_api_key', 'ready_to_analyze', 'analyzing',
                     'incomplete_run', 'review', 'sorted'
    """
    if st.session_state.get("analyzing"):
        return "analyzing"

    if not INPUT_DIR.exists() or not any(
        INPUT_DIR.rglob(f"*{ext}") for ext in config.SUPPORTED_EXTENSIONS
    ):
        return "no_images"

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "no_api_key"

    runs = list_runs()
    # Check for incomplete runs first
    for r in runs:
        m = load_manifest(r)
        if m and m.get("status") == "incomplete":
            return "incomplete_run"

    if not runs:
        return "ready_to_analyze"

    # Check if there are NEW images not yet analyzed
    known = already_analyzed_hashes(RUNS_DIR)
    all_paths = scan_image_paths(INPUT_DIR)
    new_count = sum(1 for p in all_paths if file_hash(p) not in known)
    if new_count > 0 and not runs:
        return "ready_to_analyze"

    # There are complete runs — go to review
    return "review"


# ── analysis engine (runs inside Streamlit) ──────────────────────────────────

def run_analysis_in_gui(test_mode: bool = False, resume_path: Path | None = None):
    """Kick off analysis from within the GUI. Sets session_state flags."""
    st.session_state.analyzing = True
    st.session_state.analysis_log = []
    st.session_state.analysis_error = None
    st.session_state.analysis_done = False

    all_paths = scan_image_paths(INPUT_DIR)
    if not all_paths:
        st.session_state.analysis_error = "No images found."
        st.session_state.analyzing = False
        return

    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    # Resume or fresh
    if resume_path:
        manifest = json.loads(resume_path.read_text(encoding="utf-8"))
        manifest_path = resume_path
        done_hashes = {img["file_hash"] for img in manifest.get("images", []) if img.get("file_hash")}
        paths = [p for p in all_paths if file_hash(p) not in done_hashes]
        st.session_state.analysis_log.append(f"Resuming: {len(paths)} remaining, {len(manifest.get('images',[]))} already done")
    else:
        known = already_analyzed_hashes(RUNS_DIR)
        paths = [p for p in all_paths if file_hash(p) not in known]
        skipped = len(all_paths) - len(paths)
        if skipped:
            st.session_state.analysis_log.append(f"Skipping {skipped} image(s) already analyzed")

        if test_mode:
            paths = paths[: config.TEST_SAMPLE_SIZE]
            st.session_state.analysis_log.append(f"Test mode: analyzing {len(paths)} images only")

        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        manifest_path = RUNS_DIR / f"{ts}.json"
        manifest = {
            "run_id": ts,
            "processed_files_hash": run_signature(all_paths, INPUT_DIR),
            "processed_file_list": sorted(str(p.relative_to(INPUT_DIR)) for p in all_paths if p.is_relative_to(INPUT_DIR)),
            "input_dir": str(INPUT_DIR),
            "status": "incomplete",
            "test_mode": test_mode,
            "images": [],
            "errors": [],
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        save_manifest(manifest, manifest_path)

    if not paths:
        manifest["status"] = "complete"
        save_manifest(manifest, manifest_path)
        st.session_state.analysis_log.append("All images already analyzed.")
        st.session_state.analyzing = False
        st.session_state.analysis_done = True
        return

    total = len(paths)
    batch_size = config.BATCH_SIZE
    batches = [paths[i:i + batch_size] for i in range(0, total, batch_size)]
    st.session_state.analysis_log.append(f"Analyzing {total} images in {len(batches)} batch(es) of up to {batch_size}")

    for batch_num, batch in enumerate(batches, 1):
        st.session_state.analysis_log.append(f"Batch {batch_num}/{len(batches)}: {len(batch)} images…")

        try:
            results, errors, usage = asyncio.run(
                analyze_batch(batch)
            )
        except Exception as e:
            st.session_state.analysis_log.append(f"Error in batch {batch_num}: {e}")
            save_manifest(manifest, manifest_path)
            st.session_state.analysis_error = str(e)
            st.session_state.analyzing = False
            return

        manifest["images"].extend(results)
        manifest["errors"].extend(errors)
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            manifest["token_usage"][k] += usage.get(k, 0)
        save_manifest(manifest, manifest_path)
        st.session_state.analysis_log.append(f"  Batch {batch_num} done: {len(results)} OK, {len(errors)} errors")

    manifest["status"] = "complete"
    save_manifest(manifest, manifest_path)

    tok = manifest["token_usage"]
    est = (tok["prompt_tokens"] * 0.10 + tok["completion_tokens"] * 0.40) / 1_000_000
    st.session_state.analysis_log.append(f"Done! {len(manifest['images'])} images, {len(manifest['errors'])} errors")
    st.session_state.analysis_log.append(f"Tokens: {tok['total_tokens']:,} | Est. cost: ${est:.4f}")
    st.session_state.analyzing = False
    st.session_state.analysis_done = True


# ── GUI ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Receipt Sorter", layout="wide")

    # Detect step
    step = detect_step()

    # ═══════════════════════════════════════════════════════════════════════
    # STEP: No images
    # ═══════════════════════════════════════════════════════════════════════
    if step == "no_images":
        st.title("Step 1: Add your images")
        st.markdown(f"""
        Put your receipt and document images into the **`{config.INPUT_DIR}`** folder.

        Supported formats: `{', '.join(sorted(config.SUPPORTED_EXTENSIONS))}`

        Once you've added images, **refresh this page**.
        """)
        st.info(f"Looking for images in: `{INPUT_DIR}`")
        if st.button("I've added images — refresh"):
            st.rerun()
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP: No API key
    # ═══════════════════════════════════════════════════════════════════════
    if step == "no_api_key":
        st.title("Step 1b: Set your API key")
        st.markdown("""
        Create a `.env` file in the project root with:

        ```
        GEMINI_API_KEY=your_key_here
        ```

        Then **refresh this page**.
        """)
        if st.button("I've added my key — refresh"):
            st.rerun()
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP: Analyzing (in progress)
    # ═══════════════════════════════════════════════════════════════════════
    if step == "analyzing":
        st.title("Analyzing images…")
        st.info("Analysis is running. Please wait.")
        for line in st.session_state.get("analysis_log", []):
            st.text(line)
        if st.session_state.get("analysis_error"):
            st.error(f"Error: {st.session_state.analysis_error}")
            if st.button("Try resuming"):
                st.session_state.analyzing = False
                st.rerun()
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP: Incomplete run — offer resume
    # ═══════════════════════════════════════════════════════════════════════
    if step == "incomplete_run":
        st.title("Resume incomplete analysis")
        runs = list_runs()
        incomplete = None
        for r in runs:
            m = load_manifest(r)
            if m and m.get("status") == "incomplete":
                incomplete = r
                break
        if incomplete:
            m = load_manifest(incomplete)
            done = len(m.get("images", []))
            total_files = len(scan_image_paths(INPUT_DIR))
            st.warning(f"A previous run crashed or was interrupted. **{done}** of ~{total_files} images were analyzed.")
            st.caption(f"Run file: `{incomplete.name}`")
            if st.button("Resume analysis", type="primary"):
                run_analysis_in_gui(resume_path=incomplete)
                st.rerun()
            st.divider()
            if st.button("Discard and start fresh"):
                incomplete.unlink(missing_ok=True)
                st.rerun()
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP: Ready to analyze (images present, no runs yet or new images)
    # ═══════════════════════════════════════════════════════════════════════
    if step == "ready_to_analyze":
        all_paths = scan_image_paths(INPUT_DIR)
        known = already_analyzed_hashes(RUNS_DIR)
        new_count = sum(1 for p in all_paths if file_hash(p) not in known)
        total = len(all_paths)

        st.title("Step 2: Analyze your images")
        st.markdown(f"Found **{total}** images in `{config.INPUT_DIR}`. **{new_count}** are new (not yet analyzed).")
        st.caption(f"Images will be processed in batches of {config.BATCH_SIZE}, saving progress after each batch.")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Recommended: test first**")
            st.caption(f"Analyze just {config.TEST_SAMPLE_SIZE} images to check quality before committing to all {new_count}.")
            if st.button("Test on a small sample", type="primary"):
                run_analysis_in_gui(test_mode=True)
                st.rerun()
        with col2:
            st.markdown("**Full analysis**")
            st.caption(f"Analyze all {new_count} new images. Progress is saved after every batch of {config.BATCH_SIZE}.")
            if st.button("Analyze all new images"):
                run_analysis_in_gui(test_mode=False)
                st.rerun()
        return

    # ═══════════════════════════════════════════════════════════════════════
    # STEP: Review
    # ═══════════════════════════════════════════════════════════════════════
    # If we just finished analysis, show a brief transition
    if st.session_state.get("analysis_done"):
        st.balloons()
        del st.session_state["analysis_done"]

    render_review()


# ── review screen ────────────────────────────────────────────────────────────

def render_review():
    runs = list_runs()
    if not runs:
        st.info("No runs found.")
        return

    # Bootstrap session state
    if "manifest_path" not in st.session_state:
        st.session_state.manifest_path = str(runs[0])
    if "manifest" not in st.session_state:
        st.session_state.manifest = load_manifest(Path(st.session_state.manifest_path))
    if "images" not in st.session_state:
        st.session_state.images = list((st.session_state.manifest or {}).get("images", []))
        flag_duplicates(st.session_state.images)

    manifest = st.session_state.manifest or {}
    images = st.session_state.images
    input_dir = Path(manifest.get("input_dir", config.INPUT_DIR)).resolve()

    # Check for new unanalyzed images
    all_paths = scan_image_paths(INPUT_DIR)
    known = already_analyzed_hashes(RUNS_DIR)
    new_count = sum(1 for p in all_paths if file_hash(p) not in known)

    # ── Sidebar ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Receipt Sorter")

        # Run selector
        run_options = [f.name for f in runs]
        run_paths = {f.name: f for f in runs}
        current = Path(st.session_state.manifest_path).name
        selected = st.selectbox("Run", run_options, index=run_options.index(current) if current in run_options else 0)
        if run_paths.get(selected) and str(run_paths[selected]) != st.session_state.manifest_path:
            st.session_state.manifest_path = str(run_paths[selected])
            st.session_state.manifest = load_manifest(run_paths[selected])
            st.session_state.images = list((st.session_state.manifest or {}).get("images", []))
            flag_duplicates(st.session_state.images)
            for k in ("sort_result", "confirm_pending"):
                st.session_state.pop(k, None)
            st.rerun()

        if manifest.get("test_mode"):
            st.info("Test mode run")

        st.divider()

        # Dashboard
        n = len(images)
        approved_n = sum(1 for r in images if r.get("approved"))
        st.metric("Images", n)
        progress_pct = approved_n / n if n else 0
        st.progress(progress_pct, text=f"Reviewed: {approved_n}/{n}")

        folder_counts = Counter(
            (r.get("user_folder") or r.get("suggested_folder") or "unknown").strip()
            for r in images
        )
        for b in BUCKETS:
            cnt = folder_counts.get(b, 0)
            if cnt:
                st.caption(f"**{b}**: {cnt}")

        dup_count = sum(1 for r in images if r.get("duplicate_of"))
        if dup_count:
            st.warning(f"{dup_count} duplicate(s)")

        error_count = len(manifest.get("errors", []))
        if error_count:
            st.error(f"{error_count} error(s)")

        tok = manifest.get("token_usage")
        if tok and tok.get("total_tokens"):
            st.divider()
            est = (tok["prompt_tokens"] * 0.10 + tok["completion_tokens"] * 0.40) / 1_000_000
            st.caption(f"Tokens: {tok['total_tokens']:,} | Cost: ${est:.4f}")

        if new_count:
            st.divider()
            st.info(f"{new_count} new image(s) not yet analyzed")
            if st.button("Analyze new images"):
                run_analysis_in_gui(test_mode=False)
                st.rerun()

    # ── Main area ────────────────────────────────────────────────────────
    if not images:
        st.info("This run has no images.")
        return

    # Guide the user with a clear heading
    sort_result = st.session_state.get("sort_result")
    confirm_pending = st.session_state.get("confirm_pending", False)

    if sort_result is not None:
        _render_sort_complete(sort_result)
        return

    if confirm_pending:
        _render_confirm(images, manifest)
        return

    # Normal review
    st.title("Step 3: Review results")
    st.caption("Check the AI's classifications. Fix anything wrong, then approve rows you're happy with.")

    # Filters
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        f_cat = st.multiselect("Category", CATEGORIES, key="f_cat")
    with fc2:
        f_conf = st.multiselect("Confidence", ["high", "medium", "low"], key="f_conf")
    with fc3:
        f_unapp = st.checkbox("Unapproved only", key="f_unapp")
    with fc4:
        f_dup = st.checkbox("Duplicates only", key="f_dup")

    filtered = list(images)
    if f_cat:
        filtered = [r for r in filtered if (r.get("category") or "unknown") in f_cat]
    if f_conf:
        filtered = [r for r in filtered if (r.get("confidence") or "low") in f_conf]
    if f_unapp:
        filtered = [r for r in filtered if not r.get("approved")]
    if f_dup:
        filtered = [r for r in filtered if r.get("duplicate_of")]

    if not filtered:
        st.success("All rows approved! You can proceed to sort.")
    else:
        rows = []
        for r in filtered:
            rows.append({
                "filename": r["filename"],
                "description": r.get("description") or "",
                "category": r.get("category") or "unknown",
                "folder": (r.get("user_folder") or r.get("suggested_folder") or "unknown").strip(),
                "date": r.get("date") or "",
                "vendor": r.get("vendor") or "",
                "total": str(r.get("total") or ""),
                "confidence": r.get("confidence") or "low",
                "duplicate": r.get("duplicate_of") or "",
                "delete": bool(r.get("delete_candidate")),
                "approved": bool(r.get("approved")),
                "_idx": images.index(r),
            })

        edited = st.data_editor(
            pd.DataFrame(rows)[["filename", "description", "category", "folder", "date", "vendor", "total", "confidence", "duplicate", "delete", "approved"]],
            column_config={
                "filename": st.column_config.TextColumn("File", width="medium", disabled=True),
                "description": st.column_config.TextColumn("Description", width="large", disabled=True),
                "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, width="small"),
                "folder": st.column_config.SelectboxColumn("Folder", options=BUCKETS, width="medium"),
                "date": st.column_config.TextColumn("Date", width="small"),
                "vendor": st.column_config.TextColumn("Vendor", width="small"),
                "total": st.column_config.TextColumn("Total", width="small", disabled=True),
                "confidence": st.column_config.TextColumn("Conf.", width="small", disabled=True),
                "duplicate": st.column_config.TextColumn("Dup. of", width="small", disabled=True),
                "delete": st.column_config.CheckboxColumn("Del?", width="small"),
                "approved": st.column_config.CheckboxColumn("OK", width="small"),
            },
            key="editor",
            num_rows="fixed",
            use_container_width=True,
        )

        for i in range(len(edited)):
            row = edited.iloc[i]
            idx = rows[i]["_idx"]
            images[idx]["category"] = str(row["category"]) if pd.notna(row["category"]) else "unknown"
            images[idx]["user_folder"] = str(row["folder"]) if pd.notna(row["folder"]) else None
            images[idx]["delete_candidate"] = bool(row["delete"])
            images[idx]["approved"] = bool(row["approved"])

    # Image preview (expandable)
    with st.expander("Preview an image", expanded=False):
        filenames = [r["filename"] for r in images]
        sel = st.selectbox("Image", filenames, key="img_sel")
        if sel:
            img_data = next((r for r in images if r["filename"] == sel), None)
            if img_data:
                path = resolve_path(img_data)
                left, right = st.columns([2, 1])
                with left:
                    if path.exists():
                        try:
                            from PIL import Image as PILImage
                            st.image(PILImage.open(path), caption=sel, use_container_width=True)
                        except Exception:
                            st.error(f"Cannot load: {path}")
                    else:
                        st.error(f"File not found: {path}")
                with right:
                    for k in ("category", "description", "date", "vendor", "total", "confidence", "suggested_folder", "duplicate_of", "notes"):
                        v = img_data.get(k)
                        if v is not None and v != "" and v is not False:
                            st.markdown(f"**{k}:** {v}")

    # Errors
    errs = manifest.get("errors", [])
    if errs:
        with st.expander(f"Errors ({len(errs)})", expanded=False):
            for e in errs:
                st.text(f"{e.get('filename', e.get('path', '?'))}: {e.get('error', '?')}")

    # Actions
    st.divider()
    approved_n = sum(1 for r in images if r.get("approved"))

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Approve all"):
            for r in images:
                r["approved"] = True
            st.rerun()
    with col2:
        if st.button("Reset approvals"):
            for r in images:
                r["approved"] = False
            st.rerun()
    with col3:
        if st.button("Save edits"):
            manifest["images"] = images
            save_manifest(manifest, Path(st.session_state.manifest_path))
            st.toast("Saved to run file!")

    st.divider()

    if approved_n == 0:
        st.caption("Approve at least one image to proceed.")
        st.button("Confirm & Sort", type="primary", disabled=True)
    else:
        st.caption(f"**{approved_n}** of {len(images)} approved and ready to sort.")
        if st.button(f"Confirm & Sort {approved_n} images", type="primary"):
            st.session_state.confirm_pending = True
            st.rerun()


def _render_confirm(images, manifest):
    """Confirmation screen — last chance before files move."""
    approved_n = sum(1 for r in images if r.get("approved"))
    st.title("Step 4: Confirm")
    st.warning(f"You are about to **move {approved_n} files** into sorted folders. This cannot be undone.")

    # Show summary of what will go where
    folder_counts = Counter()
    for r in images:
        if r.get("approved"):
            f = (r.get("user_folder") or r.get("suggested_folder") or "unknown").strip()
            folder_counts[f] += 1
    for b in BUCKETS:
        if folder_counts.get(b):
            st.caption(f"**{b}**: {folder_counts[b]} files")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes, move them now", type="primary"):
            st.session_state.confirm_pending = False
            m = dict(manifest)
            m["images"] = images
            result = execute(m, OUTPUT_DIR, RUNS_DIR)
            st.session_state.sort_result = result
            st.rerun()
    with c2:
        if st.button("Go back"):
            st.session_state.confirm_pending = False
            st.rerun()


def _render_sort_complete(sort_result):
    """Post-sort summary."""
    st.title("Done!")
    st.success(f"**{sort_result['moved']}** files moved into sorted folders.")

    for folder, cnt in sort_result.get("per_folder", {}).items():
        if cnt:
            st.caption(f"**{folder}**: {cnt}")

    if sort_result.get("errors"):
        st.error(f"{len(sort_result['errors'])} file(s) could not be moved")
        for e in sort_result["errors"]:
            st.text(e)

    if sort_result.get("sorted_manifest_path"):
        st.caption(f"Manifest saved: `{sort_result['sorted_manifest_path']}`")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start a new analysis"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    with c2:
        if st.button("Back to review"):
            del st.session_state["sort_result"]
            st.rerun()


if __name__ == "__main__":
    main()
