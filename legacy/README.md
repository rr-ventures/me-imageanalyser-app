# Legacy Code

This folder contains the original ImageStudio app code, archived for reference.

The app has been rebuilt with a FastAPI backend + React frontend.

## What's here

| File | Original Purpose |
|------|-----------------|
| `app_streamlit.py` | Streamlit UI for image review and editing |
| `analyzer.py` | Gemini-based image analysis (orientation, quality, scene) |
| `config.py` | App configuration (paths, models, pricing) |
| `editor.py` | Image rotation and upscaling |
| `filter_report.py` | Hardcoded filter catalog (15 filters) |
| `main.py` | CLI entry point for batch analysis |
| `sorter.py` | File sorter for receipt/invoice categorization |
| `requirements.txt` | Original Python dependencies |
| `PLAN_receipt_sorter.md` | Original project plan (receipt sorting focus) |
| `.streamlit/` | Streamlit theme configuration |
