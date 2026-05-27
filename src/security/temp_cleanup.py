import logging
from pathlib import Path

TEMP_DIR = Path("temp")


def cleanup_temp_dir() -> None:
    """Wipe all files in temp/ on startup as crash-recovery safety net."""
    if not TEMP_DIR.exists():
        return
    removed = 0
    for f in TEMP_DIR.iterdir():
        if f.is_file() and f.name != ".gitkeep":
            f.unlink()
            removed += 1
    if removed:
        logging.info("Startup cleanup: removed %d file(s) from temp/", removed)


def cleanup_temp_file(filepath: Path) -> None:
    """Delete a specific temp file. Safe to call even if file doesn't exist."""
    try:
        if filepath.exists():
            filepath.unlink()
    except OSError:
        logging.warning("Could not delete temp file: %s", filepath.name)
