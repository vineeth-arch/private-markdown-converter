import logging
from pathlib import Path

from markitdown import MarkItDown

logger = logging.getLogger(__name__)

_md = MarkItDown()


def convert_file(filepath: Path) -> str:
    """Convert a file to Markdown. Returns Markdown string, or '[ERROR] ...' on failure."""
    try:
        result = _md.convert(str(filepath))
        return result.text_content
    except Exception as e:
        logger.error("MarkItDown conversion failed: %s", type(e).__name__)
        return f"[ERROR] Could not convert this file ({type(e).__name__})."
