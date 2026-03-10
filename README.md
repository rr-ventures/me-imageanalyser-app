# Receipt Sorter

Two-phase Python receipt image sorter using the Google Gemini Vision API and a Streamlit GUI. Analyzes images in a folder, saves results to a run manifest, then lets you review and confirm before any files are moved.

## Prerequisites

- Python 3.11+
- Docker (for Dev Container)

## Quick start (local or after Reopen in Container)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **API key**  
   Create a `.env` file in the project root with:
   ```
   GEMINI_API_KEY=your_key_here
   ```
   Never commit `.env` (it is in `.gitignore`).

3. **Put images to process**  
   Place receipt/document images in `./images/` (or the folder set in `config.py` as `INPUT_DIR`).

4. **Phase 1 — Analyze**
   ```bash
   python main.py
   ```
   This scans the input folder, optionally reuses a matching previous run, or calls the Gemini API and saves results to `runs/`. No files are moved.

5. **Phase 2 — Review and sort**
   ```bash
   streamlit run app.py
   ```
   Open the GUI in your browser, review and approve rows, then click **Confirm & Sort** to move files into buckets under `./sorted/`.

## Dev Container

Open this folder in VS Code or Cursor, then run **Reopen in Container** (Command Palette or status bar). The container has Python 3.11 and installs `requirements.txt` so you can run `python main.py` and `streamlit run app.py` inside the container. Streamlit is forwarded on port **8501**.

## Git

When you're ready to version control: run `git init` in the project root, then add and commit. `.gitignore` is set up so `.env`, `runs/`, `images/`, `sorted/`, and common Python/IDE artifacts are not committed.

## Plan

See [PLAN.md](PLAN.md) for the full design, buckets, run storage, reuse logic, and implementation order.
