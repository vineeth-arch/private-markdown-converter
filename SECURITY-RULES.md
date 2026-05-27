# Security Rules

This document defines the non-negotiable security constraints for Private Markdown Converter. Every code change, feature addition, and architectural decision must comply with these rules. Reference this file in every Claude Code / Codex / Cursor prompt.

## Data classification

### Never stored (anywhere, ever)
- Original uploaded documents
- Decrypted PDF files
- Converted Markdown content
- PDF passwords in plaintext
- Audio transcripts
- YouTube video content

### Stored in macOS Keychain only (via keyring)
- Saved PDF passwords for password profiles

### Stored in SQLite (metadata only)
- Conversion history records (filename, extension, engine, status, duration, timestamp)
- Password profile metadata (profile name, filename pattern, keychain reference)

### Exists temporarily (in-session only)
- Uploaded files in temp/ directory
- Decrypted PDFs in temp/ directory
- Converted Markdown in Streamlit session_state (RAM only)
- Batch ZIP files in temp/ directory

## Temporary file rules

1. All temp files go into the `temp/` directory. No exceptions.
2. Every temp file gets a UUID-based filename. No original filenames in temp.
3. Decrypted PDFs must be deleted immediately after conversion, inside a try/finally block.
4. On app startup, `temp/` is wiped completely (crash recovery).
5. After each successful conversion, the specific temp files are deleted.
6. After batch ZIP download, the ZIP is deleted.
7. The `temp/` directory is in `.gitignore`.

### Temp cleanup implementation pattern

```python
import shutil
from pathlib import Path

TEMP_DIR = Path("temp")

def cleanup_temp_on_startup():
    """Wipe all temp files on app startup. Crash recovery safety net."""
    if TEMP_DIR.exists():
        for item in TEMP_DIR.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

def cleanup_temp_file(filepath: Path):
    """Delete a specific temp file. Call in finally block."""
    try:
        if filepath.exists():
            filepath.unlink()
    except OSError:
        pass  # Log warning but don't crash
```

## Password handling rules

1. Never store passwords in SQLite, session_state, environment variables, config files, or logs.
2. Saved passwords go through `keyring.set_password()` to macOS Keychain.
3. Retrieved passwords go through `keyring.get_password()` and are held in a local variable only for the duration of the unlock operation.
4. After the PDF is unlocked, the password variable goes out of scope. Do not assign it to any persistent object.
5. Never include passwords in error messages.
6. Never include passwords in conversion history.
7. When a password profile is deleted, call `keyring.delete_password()` to remove from Keychain.
8. The keychain service name format: `pmc.password-profile.{profile_id}`
9. The keychain account name format: `profile-{profile_id}`

### Password vault implementation pattern

```python
import keyring

SERVICE_PREFIX = "pmc.password-profile"

def save_password(profile_id: str, password: str) -> None:
    service = f"{SERVICE_PREFIX}.{profile_id}"
    account = f"profile-{profile_id}"
    keyring.set_password(service, account, password)

def get_password(profile_id: str) -> str | None:
    service = f"{SERVICE_PREFIX}.{profile_id}"
    account = f"profile-{profile_id}"
    return keyring.get_password(service, account)

def delete_password(profile_id: str) -> None:
    service = f"{SERVICE_PREFIX}.{profile_id}"
    account = f"profile-{profile_id}"
    try:
        keyring.delete_password(service, account)
    except keyring.errors.PasswordDeleteError:
        pass  # Already deleted or never existed
```

## PDF unlock rules

1. Detect encryption using pikepdf before attempting conversion.
2. If encrypted, prompt for password (manual entry or saved profile).
3. Unlock into a temp file with UUID filename.
4. Pass the temp file path to the converter.
5. Delete the temp file in a finally block, regardless of conversion success or failure.
6. If the password is wrong, show: "The password appears to be incorrect. Please check and try again."
7. Never include the actual password in the error message.
8. Never retry with modified passwords automatically.

### PDF unlock implementation pattern

```python
import pikepdf
from pathlib import Path
import uuid

def is_pdf_encrypted(filepath: Path) -> bool:
    try:
        with pikepdf.open(filepath) as pdf:
            return False
    except pikepdf.PasswordError:
        return True
    except Exception:
        return False  # Not a valid PDF or other error

def unlock_pdf(filepath: Path, password: str, temp_dir: Path) -> Path:
    temp_path = temp_dir / f"{uuid.uuid4().hex}.pdf"
    try:
        with pikepdf.open(filepath, password=password) as pdf:
            pdf.save(temp_path)
        return temp_path
    except pikepdf.PasswordError:
        raise ValueError("The password appears to be incorrect.")
    except Exception as e:
        raise RuntimeError(f"Failed to process PDF: {type(e).__name__}")
```

## SQLite rules

1. Database file lives at `data/app.db`.
2. `data/` directory is in `.gitignore`.
3. No content columns in any table. Metadata only.
4. No password columns in any table.
5. No file path columns pointing to stored documents (there are none).
6. Use parameterized queries. Never use string formatting for SQL.
7. WAL mode for better concurrent read performance with Streamlit.

## Logging rules

1. Use Python's `logging` module, not `print()`.
2. Never log file contents.
3. Never log passwords or password hints.
4. Never log decrypted file paths in production mode.
5. Log conversion events: filename, engine, status, duration.
6. Log errors: error type and safe message only.

## .gitignore requirements

```
data/*.db
data/*.db-wal
data/*.db-shm
temp/*
!temp/.gitkeep
__pycache__/
*.pyc
.env
*.pdf
*.docx
*.pptx
*.xlsx
*.md
!README.md
!CLAUDE.md
!*.project.md
.DS_Store
```

## Streamlit session_state rules

1. Converted Markdown content can live in session_state during the active session.
2. When the user navigates away from the Convert page, clear conversion results from session_state.
3. Never store passwords in session_state.
4. Never store decrypted file references in session_state.
5. Session_state is RAM-only and dies with the Streamlit session. This is acceptable.

## File upload rules

1. Maximum file size: 50MB default.
2. Uploaded files are written to temp/ with UUID filenames.
3. Original filename is preserved in metadata only (for history and display).
4. After conversion, uploaded temp files are deleted.
5. Accepted file extensions are validated before processing.
