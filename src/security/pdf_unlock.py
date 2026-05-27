import uuid
from pathlib import Path

import pikepdf


def is_pdf_encrypted(filepath: Path) -> bool:
    """Return True when a PDF requires a password to open."""
    try:
        with pikepdf.open(filepath):
            return False
    except pikepdf.PasswordError:
        return True
    except Exception:
        return False


def unlock_pdf(filepath: Path, password: str, temp_dir: Path) -> Path:
    """Unlock a password-protected PDF into a UUID temp file."""
    temp_path = temp_dir / f"{uuid.uuid4().hex}.pdf"
    try:
        with pikepdf.open(filepath, password=password) as pdf:
            pdf.save(temp_path)
        return temp_path
    except pikepdf.PasswordError as exc:
        raise ValueError("The password appears to be incorrect.") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to process PDF: {type(exc).__name__}") from exc
