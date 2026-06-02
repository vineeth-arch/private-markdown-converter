import logging
import sqlite3
import uuid
from pathlib import Path
from time import perf_counter

import streamlit as st

from src.converters.ocr_formatter import format_to_markdown
from src.converters.ocr_router import SUPPORTED_IMAGE_EXTENSIONS, get_default_engine
from src.db.history import add_record
from src.export.zip_export import cleanup_zip, create_zip
from src.security.temp_cleanup import cleanup_temp_file

logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
RESULTS_KEY = "image_ocr_results"
TEMP_UPLOAD_TYPES = sorted(SUPPORTED_IMAGE_EXTENSIONS)
NO_ENGINE_MESSAGE = "No OCR engine is available. Install OCR dependencies, then try again."


def clear_session_state() -> None:
    st.session_state.pop(RESULTS_KEY, None)


def _output_name(filename: str) -> str:
    stem = Path(filename).stem or "image"
    return f"{stem}.md"


def _metadata_for(filename: str, engine_name: str, include_metadata: bool) -> dict | None:
    if not include_metadata:
        return None
    return {"source_file": filename, "ocr_engine": engine_name}


def _safe_error_message(exc: Exception, suffix: str) -> str:
    message = str(exc).strip()
    if message == "No text detected in image.":
        return message
    if message == "Unsupported image format for OCR.":
        return message
    if suffix.lower().lstrip(".") == "heic" and "read" in message.lower():
        return "Could not read this HEIC image. Try converting it to PNG or JPG first."
    if "read" in message.lower() or "valid image" in message.lower():
        return "Could not read this image. Check that the file is a valid image and try again."
    return "Could not OCR this image. Try another image and try again."


def _store_history_record(
    *,
    filename: str,
    extension: str,
    engine_name: str,
    status: str,
    output_name: str,
    file_size: int,
    duration_seconds: float,
    error_message: str | None,
) -> None:
    try:
        add_record(
            filename=filename,
            extension=extension.lstrip(".").lower() or "image",
            engine=engine_name,
            status=status,
            output_name=output_name,
            file_size=file_size,
            duration=round(duration_seconds, 3),
            error_msg=error_message,
        )
    except sqlite3.Error as exc:
        logger.error("Failed to write OCR history: %s", type(exc).__name__)


def _render_engine_badge(engine_name: str) -> None:
    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 16px 20px;
            margin-bottom: 18px;
        ">
            <span style="
                display: inline-block;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                font-weight: 700;
                background: #FFD23F;
                color: #1E1E1E;
                border: 2px solid #1E1E1E;
                border-radius: 6px;
                padding: 4px 10px;
                text-transform: uppercase;
            ">ACTIVE OCR ENGINE: {engine_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _process_image(uploaded_file, engine, include_metadata: bool, preserve_line_breaks: bool) -> dict:
    started_at = perf_counter()
    suffix = Path(uploaded_file.name).suffix.lower()
    extension = suffix.lstrip(".")
    output_name = _output_name(uploaded_file.name)
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"
    result = {
        "filename": uploaded_file.name,
        "output_name": output_name,
        "status": "failed",
        "markdown": "",
        "error": "",
        "duration": 0.0,
    }

    if extension not in SUPPORTED_IMAGE_EXTENSIONS:
        error_message = "Unsupported image format for OCR."
        result["error"] = error_message
        result["duration"] = perf_counter() - started_at
        _store_history_record(
            filename=uploaded_file.name,
            extension=extension,
            engine_name=engine.name,
            status="failed",
            output_name=output_name,
            file_size=uploaded_file.size,
            duration_seconds=result["duration"],
            error_message=error_message,
        )
        return result

    TEMP_DIR.mkdir(exist_ok=True)
    try:
        temp_path.write_bytes(uploaded_file.getvalue())
        text = engine.extract_text(temp_path)
        markdown = format_to_markdown(
            text,
            preserve_line_breaks=preserve_line_breaks,
            metadata=_metadata_for(uploaded_file.name, engine.name, include_metadata),
        )
        result["status"] = "success"
        result["markdown"] = markdown
        result["duration"] = perf_counter() - started_at
        _store_history_record(
            filename=uploaded_file.name,
            extension=extension,
            engine_name=engine.name,
            status="success",
            output_name=output_name,
            file_size=uploaded_file.size,
            duration_seconds=result["duration"],
            error_message=None,
        )
    except Exception as exc:
        error_message = _safe_error_message(exc, suffix)
        result["error"] = error_message
        result["duration"] = perf_counter() - started_at
        _store_history_record(
            filename=uploaded_file.name,
            extension=extension,
            engine_name=engine.name,
            status="failed",
            output_name=output_name,
            file_size=uploaded_file.size,
            duration_seconds=result["duration"],
            error_message=error_message,
        )
    finally:
        cleanup_temp_file(temp_path)

    return result


def _successful_files(results: list[dict]) -> dict[str, str]:
    files: dict[str, str] = {}
    used_names: set[str] = set()
    for result in results:
        if result["status"] != "success" or not result["markdown"]:
            continue
        archive_name = _unique_archive_name(result["output_name"], used_names)
        files[archive_name] = result["markdown"]
    return files


def _unique_archive_name(filename: str, used_names: set[str]) -> str:
    path = Path(filename)
    stem = path.stem or "image"
    suffix = path.suffix or ".md"
    candidate = f"{stem}{suffix}"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}-{counter}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def _render_success_result(result: dict, *, expanded: bool, show_download: bool, key_prefix: str) -> None:
    st.success(f"OCR complete: {result['filename']}")
    with st.expander("Rendered preview", expanded=expanded):
        st.markdown(result["markdown"])
    st.text_area(
        "Raw Markdown",
        result["markdown"],
        height=300,
        key=f"{key_prefix}_raw_{result['filename']}",
    )
    if show_download:
        st.download_button(
            label="DOWNLOAD .MD",
            data=result["markdown"],
            file_name=result["output_name"],
            mime="text/markdown",
            key=f"{key_prefix}_download_{result['filename']}",
            use_container_width=True,
        )


def _render_zip_download(results: list[dict]) -> None:
    files = _successful_files(results)
    if len(files) < 2:
        return

    zip_path: Path | None = None
    try:
        zip_path = create_zip(files, TEMP_DIR)
        zip_bytes = zip_path.read_bytes()
    finally:
        if zip_path is not None:
            cleanup_zip(zip_path)

    st.download_button(
        label=f"Download all as ZIP ({len(files)} files)",
        data=zip_bytes,
        file_name="image-ocr-results.zip",
        mime="application/zip",
        key="image_ocr_download_zip",
        use_container_width=True,
    )


def _render_results(results: list[dict], show_per_image_downloads: bool) -> None:
    if not results:
        return

    if len(results) == 1:
        result = results[0]
        if result["status"] == "success":
            _render_success_result(
                result,
                expanded=True,
                show_download=show_per_image_downloads,
                key_prefix="single",
            )
        else:
            st.error(f"Failed to OCR {result['filename']}: {result['error']}")
        return

    _render_zip_download(results)
    for index, result in enumerate(results):
        label_status = result["status"].upper()
        with st.expander(f"{result['filename']} - {label_status}", expanded=False):
            if result["status"] == "success":
                _render_success_result(
                    result,
                    expanded=False,
                    show_download=show_per_image_downloads,
                    key_prefix=f"batch_{index}",
                )
            else:
                st.error(result["error"])


def render(page_header) -> None:
    page_header("Image OCR", "#FFD23F", text_color="#1E1E1E")

    try:
        engine = get_default_engine()
    except RuntimeError:
        st.warning(NO_ENGINE_MESSAGE)
        return

    _render_engine_badge(engine.name)

    uploaded_files = st.file_uploader(
        "Upload images for OCR",
        type=TEMP_UPLOAD_TYPES,
        accept_multiple_files=True,
        help="Screenshots and image notes are processed locally. Temp images are deleted after OCR.",
    )

    option_cols = st.columns(3)
    with option_cols[0]:
        show_per_image_downloads = st.checkbox("Generate one markdown per image", value=True)
    with option_cols[1]:
        include_metadata = st.checkbox("Include metadata header", value=False)
    with option_cols[2]:
        preserve_line_breaks = st.checkbox("Preserve OCR line breaks", value=True)

    if not uploaded_files:
        clear_session_state()
        return

    if st.button("CONVERT IMAGES", use_container_width=True):
        results = []
        progress = st.progress(0)
        with st.spinner("Running OCR..."):
            for index, uploaded_file in enumerate(uploaded_files, start=1):
                results.append(_process_image(uploaded_file, engine, include_metadata, preserve_line_breaks))
                progress.progress(index / len(uploaded_files))
        st.session_state[RESULTS_KEY] = results

    _render_results(st.session_state.get(RESULTS_KEY, []), show_per_image_downloads)
