from contextlib import redirect_stderr, redirect_stdout
import io
import logging
from urllib.parse import parse_qs, urlparse
import shutil

from markitdown import MarkItDown

logger = logging.getLogger(__name__)

YTDLP_MISSING_MESSAGE = "yt-dlp is not installed. Run: brew install yt-dlp"
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be"}


def is_youtube_url(url: str) -> bool:
    """Return True when the URL is an accepted YouTube URL."""
    parsed = urlparse(url.strip())
    return parsed.scheme == "https" and parsed.netloc.lower() in YOUTUBE_HOSTS


def _normalize_youtube_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    else:
        video_id = parse_qs(parsed.query).get("v", [""])[0]

    if not video_id:
        return None
    return f"https://www.youtube.com/watch?v={video_id}"


def convert_youtube(url: str) -> tuple[str, str, str]:
    """Convert a YouTube transcript URL to Markdown using MarkItDown."""
    clean_url = url.strip()
    if not is_youtube_url(clean_url):
        return "", "failed", "Enter a valid YouTube URL starting with https://youtube.com, https://www.youtube.com, or https://youtu.be."

    normalized_url = _normalize_youtube_url(clean_url)
    if normalized_url is None:
        return "", "failed", "Enter a valid YouTube video URL."

    if shutil.which("yt-dlp") is None:
        return "", "failed", YTDLP_MISSING_MESSAGE

    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = MarkItDown().convert(normalized_url)
        markdown = result.text_content
        if "### Transcript" not in markdown:
            return "", "failed", "Could not extract a transcript for this YouTube URL. Make sure the video has captions available."
        return markdown, "success", ""
    except Exception as exc:
        logger.error("YouTube conversion failed: %s", type(exc).__name__)
        return "", "failed", f"Could not convert this YouTube URL ({type(exc).__name__})."
