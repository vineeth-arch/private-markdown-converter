from pathlib import Path

from src.converters import markitdown_engine


def route_file(file_path: Path, engine: str = "markitdown") -> tuple[bool, str]:
    """Route file to the appropriate conversion engine.

    Returns (True, markdown) on success or (False, error_message) on failure.
    The engine parameter is a forward-compatibility hook for Phase 7/8 engines.
    """
    content = markitdown_engine.convert_file(file_path)
    if content.startswith("[ERROR]"):
        return False, content.removeprefix("[ERROR] ")
    return True, content
