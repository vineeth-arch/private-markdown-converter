# CLAUDE.md -- Project Instructions

## Project identity

**Name:** Private Markdown Converter
**Repo:** private-markdown-converter (GitHub, private)
**Type:** Local-only Streamlit web app for macOS
**Builder:** Solo developer using Claude Code + Cursor + Codex
**Status:** Pre-build, architecture finalized

## What this app does

Converts documents, PDFs (including password-protected ones), and structured files into clean Markdown. Runs entirely locally. No cloud uploads, no document storage, no content logging. Designed for privacy-sensitive document workflows like bank statements.

## Tech stack

- Python 3.11+
- Streamlit (UI framework)
- SQLite (metadata-only history)
- MarkItDown (default conversion engine, Microsoft)
- pikepdf (PDF password unlock)
- keyring (macOS Keychain integration for saved passwords)
- PyMuPDF4LLM, Docling, Marker (optional advanced PDF engines, added later)

## Critical rules for every prompt and every phase

Repeat these in your working memory before writing any code:

1. **Never store original documents** anywhere permanently. Temp files only, deleted after conversion.
2. **Never store decrypted PDFs** permanently. Unlock into temp, convert, delete immediately.
3. **Never store Markdown content** in the database. The user downloads it or it's gone.
4. **Never store passwords in SQLite.** Saved passwords go through `keyring` to macOS Keychain only.
5. **Never log, print, or display passwords** in any output, error message, or debug trace.
6. **Wipe the temp directory on every app startup** as a crash-recovery safety net.
7. **Single-user local app.** No auth system, no user accounts, no login flow. macOS login is the access gate.
8. **No user_id foreign keys** in any table. All tables are single-user by design.
9. **Metadata-only history.** The conversion_history table stores filenames, timestamps, engine used, status, duration. Nothing else.
10. **Graceful engine degradation.** If an optional PDF engine isn't installed, show a friendly message. Never crash. Never break MarkItDown fallback.

## Architecture principles

- Flat-ish file structure. No more than 2 levels of nesting under src/.
- Every file has one clear job.
- Conversion engine logic stays isolated from UI code.
- Password/security logic stays isolated from everything except the unlock step.
- Streamlit session state for in-session data only. No persistent state outside SQLite metadata.
- All temporary files go into the `temp/` directory with cleanup on startup and after each conversion.
- File size limit: 50MB default, configurable in settings.
- Progress indication required for any operation that takes more than 2 seconds.

## File structure

```
private-markdown-converter/
├── app.py                          # Entry point, nav routing, temp cleanup on startup
├── requirements.txt
├── requirements-optional.txt       # PyMuPDF4LLM, Docling, Marker
├── README.md
├── .gitignore
├── .env.example
├── src/
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── router.py               # Routes file type to correct engine
│   │   ├── markitdown_engine.py    # Default engine
│   │   ├── pymupdf4llm_engine.py   # Optional
│   │   ├── docling_engine.py       # Optional
│   │   └── marker_engine.py        # Optional
│   ├── security/
│   │   ├── __init__.py
│   │   ├── pdf_unlock.py           # pikepdf unlock logic
│   │   ├── password_vault.py       # keyring read/write
│   │   └── temp_cleanup.py         # Startup + post-conversion cleanup
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py             # SQLite connection, table creation
│   │   ├── history.py              # Conversion history CRUD
│   │   └── password_profiles.py    # Profile metadata CRUD (passwords in keychain)
│   ├── export/
│   │   ├── __init__.py
│   │   └── zip_export.py           # Batch ZIP download
│   └── pages/
│       ├── __init__.py
│       ├── convert_page.py
│       ├── history_page.py
│       ├── password_profiles_page.py
│       ├── settings_page.py
│       └── help_page.py
├── data/
│   └── .gitkeep
├── temp/
│   └── .gitkeep
└── tests/
    └── .gitkeep
```

## Coding standards

- Python 3.11+ syntax
- Type hints on all function signatures
- Docstrings on all public functions (one-liner is fine if the function is simple)
- No wildcard imports
- No print() for debugging in committed code; use logging module
- Error messages shown to user must be non-technical and helpful
- All file paths use pathlib, not os.path string concatenation
- Constants in UPPER_SNAKE_CASE at module level
- No global mutable state outside Streamlit session_state

## Streamlit conventions

- Use `st.sidebar` for navigation only
- Use `st.spinner()` for any operation over 2 seconds
- Use `st.progress()` for batch operations
- Use `st.error()`, `st.warning()`, `st.success()` for user feedback
- Use `st.session_state` for in-session data (converted files, current selections)
- Never store sensitive data in session_state (passwords, decrypted content)
- File uploader max size: 50MB default

## SQLite schema

```sql
-- No users table. Single-user local app.

CREATE TABLE IF NOT EXISTS conversion_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_file_name TEXT NOT NULL,
    original_file_extension TEXT NOT NULL,
    file_size_bytes INTEGER,
    conversion_engine TEXT NOT NULL,
    conversion_status TEXT NOT NULL,  -- 'success', 'failed', 'partial'
    output_file_name TEXT,
    conversion_duration_seconds REAL,
    error_message TEXT,
    converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name TEXT NOT NULL UNIQUE,
    filename_match_pattern TEXT,       -- glob pattern, e.g. *HDFC*statement*
    keychain_service_name TEXT NOT NULL,
    keychain_account_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);
```

## Commit convention

```
chore: description    -- setup, config, structure
feat: description     -- new feature
fix: description      -- bug fix
refactor: description -- code improvement, no behavior change
docs: description     -- documentation only
```

## What NOT to build

- User authentication / login system
- Cloud sync or cloud storage
- AI cleanup or summarization of converted content
- OCR (unless a PDF engine provides it natively)
- RAG or search over converted documents
- Billing, subscription, or team features
- Document storage or content database
- Electron/Tauri wrapper (too early)
- API endpoints (this is a local UI app)
