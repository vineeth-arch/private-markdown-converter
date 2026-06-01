from contextlib import redirect_stderr, redirect_stdout
import io
import logging
from pathlib import Path
import re
import shutil
import subprocess
import uuid
from urllib.parse import parse_qs, urlparse

from markitdown import MarkItDown

logger = logging.getLogger(__name__)

YTDLP_MISSING_MESSAGE = "yt-dlp is not installed. Run: brew install yt-dlp"
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be"}
TEMP_DIR = Path("temp")


def is_youtube_url(url: str) -> bool:
    """Return True when the URL is an accepted YouTube URL."""
    parsed = urlparse(url.strip())
    return parsed.scheme == "https" and parsed.netloc.lower() in YOUTUBE_HOSTS


def _extract_video_id(url: str) -> str | None:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
        parts = parsed.path.strip("/").split("/")
        video_id = parts[1] if len(parts) > 1 else ""
    else:
        video_id = parse_qs(parsed.query).get("v", [""])[0]

    return video_id or None


def _normalize_youtube_url(url: str) -> str | None:
    video_id = _extract_video_id(url)
    if video_id is None:
        return None
    return f"https://www.youtube.com/watch?v={video_id}"


def _format_transcript_markdown(lines: list[str], source_url: str) -> str:
    transcript = "\n".join(line.strip() for line in lines if line.strip())
    return f"# YouTube Transcript\n\nSource: {source_url}\n\n## Transcript\n\n{transcript}"


def _convert_with_transcript_api(video_id: str, source_url: str) -> str | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ModuleNotFoundError:
        return None

    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as exc:
        logger.info("youtube_transcript_api failed: %s", type(exc).__name__)
        return None

    lines = [str(item.get("text", "")) for item in transcript if isinstance(item, dict)]
    if not lines:
        return None
    return _format_transcript_markdown(lines, source_url)


def _convert_with_markitdown(normalized_url: str) -> str | None:
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = MarkItDown().convert(normalized_url)
    except Exception as exc:
        logger.info("MarkItDown YouTube conversion failed: %s", type(exc).__name__)
        return None

    markdown = result.text_content
    if "### Transcript" not in markdown:
        return None
    return markdown


def _subtitle_text_from_vtt(content: str) -> list[str]:
    lines: list[str] = []
    previous = ""

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line or line.isdigit():
            continue

        line = re.sub(r"<[^>]+>", "", line)
        line = line.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        line = line.strip()
        if line and line != previous:
            lines.append(line)
            previous = line

    return lines


def _convert_with_ytdlp(normalized_url: str, source_url: str) -> str | None:
    if shutil.which("yt-dlp") is None:
        return None

    TEMP_DIR.mkdir(exist_ok=True)
    output_stem = TEMP_DIR / uuid.uuid4().hex
    try:
        subprocess.run(
            [
                "yt-dlp",
                "--skip-download",
                "--write-subs",
                "--write-auto-subs",
                "--sub-langs",
                "en.*",
                "--sub-format",
                "vtt",
                "--output",
                str(output_stem),
                normalized_url,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )

        for subtitle_file in sorted(TEMP_DIR.glob(f"{output_stem.name}*.vtt")):
            lines = _subtitle_text_from_vtt(subtitle_file.read_text(encoding="utf-8", errors="ignore"))
            if lines:
                return _format_transcript_markdown(lines, source_url)
        return None
    except Exception as exc:
        logger.info("yt-dlp subtitle fallback failed: %s", type(exc).__name__)
        return None
    finally:
        for temp_file in TEMP_DIR.glob(f"{output_stem.name}*"):
            try:
                temp_file.unlink()
            except OSError:
                pass


def convert_youtube(url: str) -> tuple[str, str, str]:
    """Convert a YouTube transcript URL to Markdown."""
    clean_url = url.strip()
    if not is_youtube_url(clean_url):
        return "", "failed", "Enter a valid YouTube URL starting with https://youtube.com, https://www.youtube.com, or https://youtu.be."

    video_id = _extract_video_id(clean_url)
    normalized_url = _normalize_youtube_url(clean_url)
    if video_id is None or normalized_url is None:
        return "", "failed", "Enter a valid YouTube video URL."

    converters = (
        lambda: _convert_with_transcript_api(video_id, normalized_url),
        lambda: _convert_with_markitdown(normalized_url),
        lambda: _convert_with_ytdlp(normalized_url, normalized_url),
    )
    for converter in converters:
        markdown = converter()
        if markdown:
            return markdown, "success", ""

    if shutil.which("yt-dlp") is None:
        return "", "failed", f"Could not extract a transcript with the installed Python transcript tools. {YTDLP_MISSING_MESSAGE}"

    return "", "failed", "Could not extract a transcript for this YouTube URL. Make sure the video has captions available."
