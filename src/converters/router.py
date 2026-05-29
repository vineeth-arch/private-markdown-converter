from pathlib import Path

from src.converters import cpp_engine, markitdown_engine

CPP_EXTENSIONS = {".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc", ".cxx", ".c"}


def route_file(file_path: Path, engine: str = "markitdown") -> tuple[bool, str]:
    """Route file to the appropriate conversion engine.

    Returns (True, markdown) on success or (False, error_message) on failure.
    The engine parameter is a forward-compatibility hook for Phase 7/8 engines.
    """
    if file_path.suffix.lower() in CPP_EXTENSIONS:
        content = cpp_engine.convert_file(file_path)
    else:
        content = markitdown_engine.convert_file(file_path)
    if content.startswith("[ERROR]"):
        return False, content.removeprefix("[ERROR] ")
    return True, content
