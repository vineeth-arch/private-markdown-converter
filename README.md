# Private Markdown Converter

A local-only Streamlit app for macOS that converts documents and password-protected PDFs into clean Markdown. Nothing leaves your machine.

## Privacy principles

- No cloud uploads. All processing happens locally.
- Uploaded files are deleted from `temp/` immediately after conversion.
- Converted Markdown is never stored — download it or it is gone.
- PDF passwords are stored only in macOS Keychain, never in the app database.
- The history log contains filenames and timestamps only. No document content.

## Supported file types

| Type | Extension |
|------|-----------|
| PDF (including password-protected) | `.pdf` |
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Excel | `.xlsx` |
| HTML | `.html`, `.htm` |
| CSV | `.csv` |
| JSON | `.json` |
| XML | `.xml` |
| EPUB | `.epub` |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp` |
| ZIP | `.zip` (contents converted individually) |

## Setup

**Requirements:** Python 3.11+, macOS

```bash
# 1. Clone the repo
git clone <repo-url>
cd private-markdown-converter

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure (optional)
cp .env.example .env
# Edit .env to change MAX_FILE_SIZE_MB if needed

# 5. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

## Optional PDF engines

```bash
pip install -r requirements-optional.txt
```

Adds: PyMuPDF4LLM, Docling, Marker (Phase 7–10).

## Database

```bash
sqlite3 data/app.db   # inspect conversion history metadata
```

## Verify temp directory is clean

```bash
ls temp/
```

Only `.gitkeep` should appear. The app wipes `temp/` on every startup as a crash-recovery safety net.
