from contextlib import redirect_stderr, redirect_stdout
import io
import logging
from pathlib import Path
import shutil
import uuid

from markitdown import MarkItDown

from src.security.temp_cleanup import cleanup_temp_file

logger = logging.getLogger(__name__)

FFMPEG_MISSING_MESSAGE = "ffmpeg is not installed. Run: brew install ffmpeg"
TEMP_DIR = Path("temp")


def convert_audio(filepath: Path) -> tuple[str, str, str]:
    """Convert an audio file to Markdown using MarkItDown."""
    if shutil.which("ffmpeg") is None:
        return "", "failed", FFMPEG_MISSING_MESSAGE

    TEMP_DIR.mkdir(exist_ok=True)
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}{filepath.suffix.lower()}"
    try:
        shutil.copyfile(filepath, temp_path)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = MarkItDown().convert(str(temp_path))
        return result.text_content, "success", ""
    except Exception as exc:
        logger.error("Audio conversion failed: %s", type(exc).__name__)
        return "", "failed", f"Could not convert this audio file ({type(exc).__name__})."
    finally:
        cleanup_temp_file(temp_path)
