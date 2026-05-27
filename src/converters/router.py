from pathlib import Path


def route_file(file_path: Path, engine: str = "markitdown") -> str:
    """Route a file to the appropriate conversion engine and return Markdown."""
    raise NotImplementedError("Conversion router not implemented until Phase 2")
