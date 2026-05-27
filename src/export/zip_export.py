import uuid
import zipfile
from pathlib import Path


def _resolve_duplicate_name(filename: str, used_names: set[str]) -> str:
    path = Path(filename)
    stem = path.stem or "output"
    suffix = path.suffix or ".md"
    candidate = f"{stem}{suffix}"
    counter = 2

    while candidate in used_names:
        candidate = f"{stem}-{counter}{suffix}"
        counter += 1

    used_names.add(candidate)
    return candidate


def create_zip(files: dict[str, str], temp_dir: Path) -> Path:
    """Create a temp ZIP archive from Markdown outputs and return its path."""
    temp_dir.mkdir(exist_ok=True)
    zip_path = temp_dir / f"{uuid.uuid4().hex}.zip"
    used_names: set[str] = set()

    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, markdown_content in files.items():
            archive_name = _resolve_duplicate_name(filename, used_names)
            archive.writestr(archive_name, markdown_content.encode("utf-8"))

    return zip_path
