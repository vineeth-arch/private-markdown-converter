from html import escape
from pathlib import Path
import re
import uuid

from src.converters import audio_engine, cpp_engine, markitdown_engine, youtube_engine
from src.security.temp_cleanup import cleanup_temp_file

YOUTUBE_PREFIXES = ("https://youtube.com", "https://youtu.be", "https://www.youtube.com")
YOUTUBE_EXTENSION = "youtube"
YOUTUBE_ENGINE = "youtube"
YOUTUBE_HISTORY_FILENAME_LIMIT = 200
YOUTUBE_DOWNLOAD_FILENAME = "youtube-transcript.md"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
CPP_EXTENSIONS = {".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc", ".cxx", ".c"}
TEMP_DIR = Path("temp")


def is_youtube_input(value: object) -> bool:
    """Return True when value is a supported YouTube URL string."""
    return isinstance(value, str) and value.strip().startswith(YOUTUBE_PREFIXES)


def route_youtube(url: str) -> tuple[bool, str]:
    """Route a YouTube URL through the YouTube conversion engine."""
    markdown, status, error_message = youtube_engine.convert_youtube(url)
    if status == "success":
        return True, markdown
    if status == "partial" and markdown:
        return True, markdown
    return False, error_message


def route_file(file_path: Path | str, engine: str = "markitdown") -> tuple[bool, str]:
    """Route file to the appropriate conversion engine.

    Returns (True, markdown) on success or (False, error_message) on failure.
    The engine parameter is a forward-compatibility hook for Phase 7/8 engines.
    """
    if is_youtube_input(file_path):
        return route_youtube(str(file_path))

    file_path = Path(file_path)
    if file_path.suffix.lower() in CPP_EXTENSIONS:
        content = cpp_engine.convert_file(file_path)
    elif file_path.suffix.lower() in AUDIO_EXTENSIONS:
        markdown, status, error_message = audio_engine.convert_audio(file_path)
        if status == "success":
            return True, markdown
        if status == "partial" and markdown:
            return True, markdown
        return False, error_message
    else:
        content = markitdown_engine.convert_file(file_path)
    if content.startswith("[ERROR]"):
        return False, content.removeprefix("[ERROR] ")
    return True, content


def _build_html_document(body: str) -> str:
    normalized_body = body.lstrip()
    if normalized_body.lower().startswith("<!doctype html") or "<html" in normalized_body[:200].lower():
        return body

    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        '<meta charset="utf-8">\n'
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


def _plain_text_to_html(text: str) -> str:
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized_text:
        return ""

    paragraphs = re.split(r"\n\s*\n", normalized_text)
    html_paragraphs = [
        "<p>" + escape(paragraph).replace("\n", "<br>\n") + "</p>"
        for paragraph in paragraphs
        if paragraph.strip()
    ]
    return "\n".join(html_paragraphs)


def route_rich_text(html: str | None, text: str | None) -> tuple[bool, str]:
    """Convert pasted rich text or plain text to Markdown via the HTML pipeline."""
    html_content = (html or "").strip()
    text_content = text or ""

    if not html_content:
        html_content = _plain_text_to_html(text_content)

    if not html_content:
        return False, "Paste some text before converting."

    TEMP_DIR.mkdir(exist_ok=True)
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}.html"
    try:
        temp_path.write_text(_build_html_document(html_content), encoding="utf-8")
        return route_file(temp_path, engine="markitdown")
    finally:
        cleanup_temp_file(temp_path)
