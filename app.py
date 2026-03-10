"""
Receipt Sorter — single-page Streamlit app.
Finds images, analyzes with Gemini, shows results, approve, then move & rename.
Every screen has clear navigation. You can always get back to where you need to be.
"""
import asyncio
import json
import os
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import config
from analyzer import analyze_batch, file_hash
from main import scan_image_paths, already_analyzed_hashes, run_signature
from sorter import execute, generate_filename

INPUT_DIR = Path(config.INPUT_DIR).resolve()
RUNS_DIR = Path(config.RUNS_DIR).resolve()
OUTPUT_DIR = Path(config.OUTPUT_DIR).resolve()
BUCKETS = list(config.BUCKETS)


# ── helpers ──────────────────────────────────────────────────────────────────

def list_runs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted(
        (f for f in RUNS_DIR.glob("*.json")
         if not f.name.endswith("_errors.json")
         and not f.name.endswith("_sorted_manifest.json")),
        key=lambda p: p.name, reverse=True,
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


def preview_new_name(row: dict) -> str:
    orig = Path(row.get("original_path", "file.jpg"))
    return generate_filename(row, orig.suffix.lower())


def estimate_cost(tok: dict) -> float:
    return (tok.get("prompt_tokens", 0) * 0.10 + tok.get("completion_tokens", 0) * 0.40) / 1_000_000


def go_to(screen: str):
    """Navigate to a screen. Clears conflicting flags."""
    clear_map = {
        "dashboard": ["has_results", "analyzing", "confirm_pending", "sort_result",
                       "manifest", "images", "manifest_path", "analysis_paths"],
        "results": ["analyzing", "confirm_pending", "sort_result"],
        "analyzing": ["has_results", "confirm_pending", "sort_result"],
    }
    for k in clear_map.get(screen, []):
        st.session_state.pop(k, None)
    if screen == "dashboard":
        pass  # all flags cleared → routes to dashboard
    elif screen == "results":
        st.session_state.has_results = True


def load_run(path: Path):
    m = load_manifest(path)
    st.session_state.manifest_path = str(path)
    st.session_state.manifest = m
    st.session_state.images = list((m or {}).get("images", []))
    flag_duplicates(st.session_state.images)
    st.session_state.has_results = True
    for k in ("sort_result", "confirm_pending", "analyzing"):
        st.session_state.pop(k, None)


def auto_save():
    """Save current edits back to the run manifest file."""
    manifest = st.session_state.get("manifest")
    path = st.session_state.get("manifest_path")
    images = st.session_state.get("images")
    if manifest and path and images:
        manifest["images"] = images
        save_manifest(manifest, Path(path))


def full_reset():
    """Delete all files in to_process/ and processed/. Keeps runs/ intact."""
    for folder in (INPUT_DIR, OUTPUT_DIR):
        if folder.exists():
            shutil.rmtree(folder)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def save_uploaded_files(uploaded_files: list) -> int:
    """Save uploaded files to INPUT_DIR. Returns count saved."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for f in uploaded_files:
        dest = INPUT_DIR / f.name
        # Avoid overwriting — append number if exists
        if dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            counter = 1
            while dest.exists():
                dest = INPUT_DIR / f"{stem}-{counter}{suffix}"
                counter += 1
        dest.write_bytes(f.getbuffer())
        saved += 1
    return saved


# ── which screen are we on? ─────────────────────────────────────────────────

def current_screen() -> str:
    if st.session_state.get("sort_result"):
        return "done"
    if st.session_state.get("confirm_pending"):
        return "confirm"
    if st.session_state.get("analyzing"):
        return "analyzing"
    if st.session_state.get("has_results"):
        return "results"
    return "dashboard"


# ── main ─────────────────────────────────────────────────────────────────────

def _inject_css():
    st.markdown("""
    <style>
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #16213e 0%, #1a1a3e 100%);
        border: 1px solid #2d3a5e;
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetricValue"] {
        color: #22c55e;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.85rem;
    }

    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
    }

    /* Secondary buttons */
    .stButton > button:not([kind="primary"]) {
        border: 1px solid #2d3a5e;
        border-radius: 8px;
        transition: all 0.2s;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #22c55e;
        color: #22c55e;
    }

    /* Data editor / table */
    [data-testid="stDataFrame"], .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Expander */
    .streamlit-expanderHeader {
        border-radius: 8px;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #22c55e, #3b82f6);
        border-radius: 8px;
    }

    /* Dividers */
    hr {
        border-color: #2d3a5e !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1629 0%, #1a1a2e 100%);
        border-right: 1px solid #2d3a5e;
    }

    /* Title */
    h1 {
        background: linear-gradient(90deg, #22c55e, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* Warning / success / error banners */
    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* Danger / reset button (targeted by key) */
    [data-testid="stButton"]:has(button[key*="reset"]) button,
    .danger-btn button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 8px;
        font-weight: 600;
    }
    [data-testid="stButton"]:has(button[key*="reset"]) button:hover,
    .danger-btn button:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%) !important;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4) !important;
    }

    /* File uploader styling */
    [data-testid="stFileUploader"] {
        border: 2px dashed #2d3a5e;
        border-radius: 12px;
        padding: 8px;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #22c55e;
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Receipt Sorter", layout="wide")
    _inject_css()

    screen = current_screen()

    # ── Sidebar (always visible) ─────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Receipt Sorter")

        # Navigation — always show a way back
        if screen != "dashboard":
            if st.button("← Back to start", use_container_width=True):
                go_to("dashboard")
                st.rerun()

        if screen in ("confirm", "done") and st.session_state.get("images"):
            if st.button("← Back to results", use_container_width=True):
                go_to("results")
                st.rerun()

        st.divider()

        # Stats
        images = st.session_state.get("images", [])
        manifest = st.session_state.get("manifest") or {}

        if images:
            n = len(images)
            approved = sum(1 for r in images if r.get("approved"))
            st.metric("Images", n)
            st.metric("Approved", f"{approved} / {n}")
            errs = len(manifest.get("errors", []))
            if errs:
                st.metric("Errors", errs)
            tok = manifest.get("token_usage")
            if tok and tok.get("total_tokens"):
                cost = estimate_cost(tok)
                st.metric("API cost", f"${cost:.4f}")
                st.caption(f"{tok['total_tokens']:,} tokens")
            if manifest.get("test_mode"):
                st.warning("This was a test run (sample only)")
        else:
            if INPUT_DIR.exists():
                all_paths = scan_image_paths(INPUT_DIR)
                st.metric("Images in folder", len(all_paths))

        # Run history
        runs = list_runs()
        if runs and screen in ("dashboard", "results"):
            st.divider()
            st.caption("Previous runs")
            for r in runs[:5]:
                m = load_manifest(r)
                n_imgs = len((m or {}).get("images", [])) if m else 0
                status = (m or {}).get("status", "?")
                label = f"{r.stem} ({n_imgs} imgs, {status})"
                current = st.session_state.get("manifest_path", "")
                is_current = str(r) == current
                if is_current:
                    st.caption(f"▶ {label}")
                else:
                    if st.button(label, key=f"run_{r.name}", use_container_width=True):
                        load_run(r)
                        st.rerun()

    # ── Route to screen ──────────────────────────────────────────────────
    if screen == "done":
        _screen_done()
    elif screen == "confirm":
        _screen_confirm()
    elif screen == "results":
        _screen_results()
    elif screen == "analyzing":
        _screen_analyzing()
    else:
        _screen_dashboard()


# ── SCREEN: Dashboard ────────────────────────────────────────────────────────

def _screen_dashboard():
    st.title("Receipt Sorter")

    if not INPUT_DIR.exists():
        st.warning(f"Create the **`{config.INPUT_DIR}`** folder and drop your images in it.")
        if st.button("Refresh"):
            st.rerun()
        return

    all_paths = scan_image_paths(INPUT_DIR)
    if not all_paths:
        st.warning(f"No images found in **`{config.INPUT_DIR}`**.")
        st.caption(f"Supported formats: {', '.join(sorted(config.SUPPORTED_EXTENSIONS))}")
        if st.button("Refresh"):
            st.rerun()
        return

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("No API key. Add `GEMINI_API_KEY=your_key` to the `.env` file, then refresh.")
        if st.button("Refresh"):
            st.rerun()
        return

    total = len(all_paths)
    known = already_analyzed_hashes(RUNS_DIR)
    new_count = sum(1 for p in all_paths if file_hash(p) not in known)
    already_count = total - new_count

    st.markdown(f"Found **{total}** images in `{config.INPUT_DIR}`")
    if already_count:
        st.caption(f"{already_count} already analyzed · {new_count} new")

    # Previous complete run available
    runs = list_runs()
    if runs:
        last = load_manifest(runs[0])
        if last and last.get("status") == "complete":
            n_imgs = len(last.get("images", []))
            tok = last.get("token_usage", {})
            cost = estimate_cost(tok)
            st.success(f"Last run analyzed **{n_imgs}** images (cost: ${cost:.4f})")

    st.divider()

    # Actions — always clear what you can do
    if new_count == 0 and runs:
        st.info("All images have been analyzed. View results or add more images.")
        if st.button("View results", type="primary", use_container_width=True):
            load_run(runs[0])
            st.rerun()
        return

    if new_count == 0 and not runs:
        st.info("All images already analyzed but no run files found. Try adding new images.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Quick test** — analyze {config.TEST_SAMPLE_SIZE} images to check quality")
        if st.button(f"Test {config.TEST_SAMPLE_SIZE} images", use_container_width=True):
            _start_analysis(all_paths, known, test_mode=True)
            st.rerun()
    with col2:
        st.markdown(f"**Full run** — analyze all {new_count} new images")
        if st.button(f"Analyze {new_count} images", type="primary", use_container_width=True):
            _start_analysis(all_paths, known, test_mode=False)
            st.rerun()

    if runs:
        st.divider()
        if st.button("Or view previous results"):
            load_run(runs[0])
            st.rerun()


# ── Analysis logic ───────────────────────────────────────────────────────────

def _start_analysis(all_paths: list[Path], known: set[str], test_mode: bool):
    paths = [p for p in all_paths if file_hash(p) not in known]
    if test_mode:
        paths = paths[:config.TEST_SAMPLE_SIZE]

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    manifest_path = RUNS_DIR / f"{ts}.json"
    manifest = {
        "run_id": ts,
        "processed_files_hash": run_signature(all_paths, INPUT_DIR),
        "input_dir": str(INPUT_DIR),
        "status": "incomplete",
        "test_mode": test_mode,
        "images": [],
        "errors": [],
        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    save_manifest(manifest, manifest_path)
    st.session_state.manifest_path = str(manifest_path)
    st.session_state.manifest = manifest
    st.session_state.analysis_paths = [str(p) for p in paths]
    st.session_state.analyzing = True


# ── SCREEN: Analyzing ────────────────────────────────────────────────────────

def _screen_analyzing():
    st.title("Analyzing…")

    manifest = st.session_state.manifest
    manifest_path = Path(st.session_state.manifest_path)
    paths = [Path(p) for p in st.session_state.get("analysis_paths", [])]

    if not paths:
        manifest["status"] = "complete"
        save_manifest(manifest, manifest_path)
        st.session_state.images = list(manifest.get("images", []))
        flag_duplicates(st.session_state.images)
        st.session_state.analyzing = False
        st.session_state.has_results = True
        st.rerun()
        return

    total = len(paths)
    batch_size = min(config.BATCH_SIZE, total)
    batches = [paths[i:i + batch_size] for i in range(0, total, batch_size)]
    already_done = len(manifest.get("images", []))

    progress_bar = st.progress(0.0)
    status_area = st.empty()
    cost_area = st.empty()
    file_area = st.empty()

    global_done = 0
    for batch_num, batch in enumerate(batches, 1):
        batch_files = ", ".join(p.name for p in batch[:3])
        if len(batch) > 3:
            batch_files += f" … and {len(batch) - 3} more"
        status_area.markdown(f"Processing batch {batch_num}/{len(batches)} ({len(batch)} images)")
        file_area.caption(f"Current: {batch_files}")

        try:
            results, errors, usage = asyncio.run(analyze_batch(batch))
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            save_manifest(manifest, manifest_path)
            st.caption("Progress has been saved. You can resume from where it left off.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Try again", type="primary"):
                    st.session_state.analyzing = True
                    done_hashes = {img["file_hash"] for img in manifest.get("images", []) if img.get("file_hash")}
                    remaining = [p for p in paths if file_hash(p) not in done_hashes]
                    st.session_state.analysis_paths = [str(p) for p in remaining]
                    st.rerun()
            with c2:
                if st.button("Back to start"):
                    go_to("dashboard")
                    st.rerun()
            return

        manifest["images"].extend(results)
        manifest["errors"].extend(errors)
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            manifest["token_usage"][k] += usage.get(k, 0)
        save_manifest(manifest, manifest_path)

        global_done += len(batch)
        pct = global_done / total
        progress_bar.progress(pct, text=f"{already_done + global_done} of {already_done + total} images")
        cost = estimate_cost(manifest["token_usage"])
        cost_area.markdown(f"Cost: **${cost:.4f}** · Tokens: {manifest['token_usage']['total_tokens']:,} · Model: `{config.MODEL}`")

    # Done
    manifest["status"] = "complete"
    save_manifest(manifest, manifest_path)
    st.session_state.images = list(manifest.get("images", []))
    flag_duplicates(st.session_state.images)
    st.session_state.analyzing = False
    st.session_state.has_results = True

    progress_bar.progress(1.0, text="Complete!")
    tok = manifest["token_usage"]
    cost = estimate_cost(tok)
    n_imgs = len(manifest["images"])
    n_errs = len(manifest["errors"])
    status_area.success(f"Finished — {n_imgs} images analyzed, {n_errs} error(s)")
    cost_area.markdown(f"**Total cost: ${cost:.4f}** · {tok['total_tokens']:,} tokens")
    file_area.empty()

    if st.button("View results →", type="primary", use_container_width=True):
        st.rerun()


# ── SCREEN: Results ──────────────────────────────────────────────────────────

def _screen_results():
    images = st.session_state.get("images", [])
    manifest = st.session_state.get("manifest") or {}

    if not images:
        st.info("No results to show.")
        if st.button("Back to start"):
            go_to("dashboard")
            st.rerun()
        return

    n = len(images)
    tok = manifest.get("token_usage", {})
    cost = estimate_cost(tok)
    n_errs = len(manifest.get("errors", []))
    approved_n = sum(1 for r in images if r.get("approved"))

    folder_counts = Counter(
        (r.get("user_folder") or r.get("suggested_folder") or "unknown").strip() for r in images
    )

    # Title + test mode warning
    st.title("Results")
    if manifest.get("test_mode"):
        st.warning("This was a **test run** — only a sample of your images were analyzed. Go back and run the full analysis when ready.")

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Analyzed", n)
    c2.metric("Receipts to keep", folder_counts.get("receipts_keep", 0))
    c3.metric("API cost", f"${cost:.4f}")
    c4.metric("Errors", n_errs)

    with st.expander("Category breakdown"):
        for b in BUCKETS:
            cnt = folder_counts.get(b, 0)
            if cnt:
                st.markdown(f"**{b}**: {cnt}")

    if n_errs:
        with st.expander(f"Errors ({n_errs})"):
            for e in manifest.get("errors", []):
                st.text(f"{e.get('filename', e.get('path', '?'))}: {e.get('error', '?')}")

    st.divider()
    st.markdown("Review the table. Edit anything that looks wrong. Check **Approved** for images you want to move and rename.")

    # Build table rows
    rows = []
    for i, r in enumerate(images):
        rows.append({
            "Filename": r.get("filename", ""),
            "Description": r.get("description") or "",
            "Vendor": r.get("vendor") or "",
            "Price": str(r.get("total") or ""),
            "Date": r.get("date") or "",
            "Category": r.get("category") or "unknown",
            "Destination": (r.get("user_folder") or r.get("suggested_folder") or "unknown").strip(),
            "New Filename": preview_new_name(r),
            "Confidence": r.get("confidence") or "low",
            "Approved": bool(r.get("approved")),
            "_idx": i,
        })

    df = pd.DataFrame(rows)

    edited = st.data_editor(
        df[["Filename", "Description", "Vendor", "Price", "Date", "Category", "Destination", "New Filename", "Confidence", "Approved"]],
        column_config={
            "Filename": st.column_config.TextColumn("Filename", width="medium", disabled=True),
            "Description": st.column_config.TextColumn("Description", width="large", disabled=True),
            "Vendor": st.column_config.TextColumn("Vendor", width="small"),
            "Price": st.column_config.TextColumn("Price", width="small", disabled=True),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Category": st.column_config.SelectboxColumn("Category", options=["receipt", "invoice", "document", "photo", "screenshot", "unknown"], width="small"),
            "Destination": st.column_config.SelectboxColumn("Destination", options=BUCKETS, width="medium"),
            "New Filename": st.column_config.TextColumn("New Filename", width="medium", disabled=True),
            "Confidence": st.column_config.TextColumn("Confidence", width="small", disabled=True),
            "Approved": st.column_config.CheckboxColumn("Approved", width="small"),
        },
        key="results_editor",
        num_rows="fixed",
        use_container_width=True,
    )

    # Write edits back + auto-save
    for i in range(len(edited)):
        row = edited.iloc[i]
        idx = rows[i]["_idx"]
        images[idx]["category"] = str(row["Category"]) if pd.notna(row["Category"]) else "unknown"
        images[idx]["user_folder"] = str(row["Destination"]) if pd.notna(row["Destination"]) else None
        images[idx]["approved"] = bool(row["Approved"])
        if pd.notna(row["Vendor"]) and str(row["Vendor"]).strip():
            images[idx]["vendor"] = str(row["Vendor"])
        if pd.notna(row["Date"]) and str(row["Date"]).strip():
            images[idx]["date"] = str(row["Date"])
    auto_save()

    # Image preview
    with st.expander("Preview an image"):
        filenames = [r.get("filename", "") for r in images]
        sel = st.selectbox("Choose image", filenames, key="preview_sel")
        if sel:
            img_data = next((r for r in images if r.get("filename") == sel), None)
            if img_data:
                p = Path(img_data["original_path"])
                if not p.is_absolute():
                    p = INPUT_DIR / p
                left, right = st.columns([2, 1])
                with left:
                    if p.exists():
                        try:
                            from PIL import Image as PILImage
                            st.image(PILImage.open(p), caption=sel, use_container_width=True)
                        except Exception:
                            st.error(f"Cannot load: {p}")
                    else:
                        st.error(f"File not found: {p}")
                with right:
                    for k in ("description", "vendor", "total", "date", "category", "confidence", "suggested_folder", "notes"):
                        v = img_data.get(k)
                        if v is not None and v != "":
                            st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")

    # Actions
    st.divider()
    approved_n = sum(1 for r in images if r.get("approved"))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve all", use_container_width=True):
            for r in images:
                r["approved"] = True
            auto_save()
            st.rerun()
    with col2:
        if st.button("Reset all approvals", use_container_width=True):
            for r in images:
                r["approved"] = False
            auto_save()
            st.rerun()

    st.divider()
    st.markdown(f"**{approved_n}** of {n} images approved")

    if approved_n == 0:
        st.button("Move & Rename →", type="primary", disabled=True, use_container_width=True)
        st.caption("Check the **Approved** box on at least one image to continue.")
    else:
        if st.button(f"Move & Rename {approved_n} images →", type="primary", use_container_width=True):
            auto_save()
            st.session_state.confirm_pending = True
            st.rerun()


# ── SCREEN: Confirm ──────────────────────────────────────────────────────────

def _screen_confirm():
    images = st.session_state.get("images", [])
    manifest = st.session_state.get("manifest") or {}
    approved_n = sum(1 for r in images if r.get("approved"))

    st.title("Confirm")
    st.warning(f"This will move **{approved_n}** files into **`{config.OUTPUT_DIR}`**. "
               f"Receipts in **receipts_keep** will be renamed. This cannot be undone.")

    folder_counts = Counter()
    for r in images:
        if r.get("approved"):
            f = (r.get("user_folder") or r.get("suggested_folder") or "unknown").strip()
            folder_counts[f] += 1
    for b in BUCKETS:
        if folder_counts.get(b):
            st.markdown(f"• **{b}**: {folder_counts[b]} files")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Yes, move & rename now", type="primary", use_container_width=True):
            m = dict(manifest)
            m["images"] = images
            result = execute(m, OUTPUT_DIR, RUNS_DIR)
            st.session_state.sort_result = result
            st.session_state.confirm_pending = False
            st.rerun()
    with c2:
        if st.button("← Go back to results", use_container_width=True):
            st.session_state.confirm_pending = False
            st.rerun()


# ── SCREEN: Done ─────────────────────────────────────────────────────────────

def _screen_done():
    result = st.session_state.sort_result

    st.title("Done!")
    st.success(f"**{result['moved']}** files moved to `{config.OUTPUT_DIR}`")

    for folder, cnt in result.get("per_folder", {}).items():
        if cnt:
            st.markdown(f"• **{folder}**: {cnt} files")

    if result.get("errors"):
        st.error(f"{len(result['errors'])} file(s) could not be moved:")
        for e in result["errors"]:
            st.text(e)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start over", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    with c2:
        if st.button("← Back to results", use_container_width=True):
            st.session_state.pop("sort_result", None)
            st.rerun()


if __name__ == "__main__":
    main()
