import uuid
from pathlib import Path

import msoffcrypto


OFFICE_EXTENSIONS = {".docx", ".xlsx", ".pptx"}


def is_office_file_encrypted(filepath: Path) -> bool:
    """Return True when an Office Open XML file requires a password to open."""
    if filepath.suffix.lower() not in OFFICE_EXTENSIONS:
        return False

    try:
        with filepath.open("rb") as source:
            office_file = msoffcrypto.OfficeFile(source)
            return bool(office_file.is_encrypted())
    except Exception:
        return False


def unlock_office_file(filepath: Path, password: str, temp_dir: Path) -> Path:
    """Decrypt a password-protected Office file into a UUID temp file."""
    temp_path = temp_dir / f"{uuid.uuid4().hex}{filepath.suffix.lower()}"
    try:
        with filepath.open("rb") as source:
            office_file = msoffcrypto.OfficeFile(source)
            office_file.load_key(password=password)
            with temp_path.open("wb") as target:
                office_file.decrypt(target)
        return temp_path
    except msoffcrypto.exceptions.InvalidKeyError as exc:
        raise ValueError("The password appears to be incorrect.") from exc
    except msoffcrypto.exceptions.DecryptionError as exc:
        raise ValueError("The password appears to be incorrect.") from exc
    except msoffcrypto.exceptions.FileFormatError as exc:
        raise RuntimeError("This password-protected Office file could not be processed.") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to process Office file: {type(exc).__name__}") from exc
