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


def cleanup_zip(zip_path: Path) -> None:
    """Delete a temp ZIP file without surfacing cleanup failures."""
    try:
        if zip_path.exists():
            zip_path.unlink()
    except OSError:
        pass


def merge_to_markdown(files: dict[str, str]) -> str:
    """Merge Markdown outputs into a single document in insertion order."""
    sections = []

    for filename, markdown_content in files.items():
        title = Path(filename).stem or "output"
        sections.append(f"---\n\n# {title}\n\n{markdown_content}")

    return "\n\n".join(sections)
