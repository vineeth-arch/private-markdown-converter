import os
import sqlite3
import uuid
import logging
import zipfile
from datetime import date
from pathlib import Path
from time import perf_counter
from typing import Optional

import streamlit as st

from src.converters.router import route_file, route_rich_text
from src.db.history import add_record
from src.db.password_profiles import (
    delete_profile,
    get_all_profiles,
    get_matching_profiles,
    insert_profile,
    update_last_used,
)
from src.export.zip_export import cleanup_zip, create_zip, merge_to_markdown
from src.security.office_unlock import is_office_file_encrypted, unlock_office_file
from src.security.password_vault import get_password, save_password
from src.security.pdf_unlock import is_pdf_encrypted, unlock_pdf
from src.security.temp_cleanup import cleanup_temp_file
from src.pages.rich_text_paste_input import render_rich_text_paste_input

logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
ENGINE_NAME = "markitdown"
CONVERSION_RESULTS_KEY = "conversion_results"
LAST_PASSWORD_PROFILE_KEY = "last_password_profile_id"
INPUT_MODE_KEY = "convert_input_mode"
PREVIOUS_INPUT_MODE_KEY = "previous_convert_input_mode"
PASTE_RESET_NONCE_KEY = "paste_input_reset_nonce"
PROTECTED_KIND_PDF = "pdf"
PROTECTED_KIND_OFFICE = "office"
PROTECTED_KIND_UNSUPPORTED = "unsupported"
SUPPORTED_PROTECTED_KINDS = {PROTECTED_KIND_PDF, PROTECTED_KIND_OFFICE}
FILES_MODE = "Files"
PASTE_MODE = "Paste rich text"
PASTED_FILENAME = "pasted-rich-text.html"

ACCEPTED_EXTENSIONS = [
    "pdf", "docx", "pptx", "xlsx", "html", "csv",
    "json", "xml", "epub", "png", "jpg", "jpeg", "gif", "zip",
    "h", "hpp", "hh", "hxx", "cpp", "cc", "cxx", "c",
]


def _store_history_record(
    filename: str,
    extension: str,
    ok: bool,
    duration_seconds: float,
    file_size: int,
    message: str,
) -> None:
    """Persist metadata-only conversion history without affecting the UI flow."""
    safe_extension = extension.lstrip(".").lower() or "file"
    output_name = f"{Path(filename).stem}.md" if ok else None
    error_message = None if ok else message

    try:
        add_record(
            filename=filename,
            extension=safe_extension,
            engine=ENGINE_NAME,
            status="success" if ok else "failed",
            output_name=output_name,
            file_size=file_size,
            duration=round(duration_seconds, 3),
            error_msg=error_message,
        )
    except sqlite3.Error as exc:
        logger.error("Failed to write conversion history: %s", type(exc).__name__)


def _render_empty_state() -> None:
    badge = (
        "display: inline-block; border: 2px solid #1E1E1E; border-radius: 6px;"
        " font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 500;"
        " padding: 3px 10px; background: white; margin: 3px 2px; color: #1E1E1E;"
    )
    col_label = (
        "font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700;"
        " color: #FF6B35; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 8px 0;"
    )

    def badges(exts: list[str]) -> str:
        return "".join(f'<span style="{badge}">{e}</span>' for e in exts)

    _html = f"""
        <div style="background:#FFFFFF;border:3px solid #1E1E1E;border-radius:12px;box-shadow:5px 5px 0 #1E1E1E;padding:36px 32px 28px;margin-top:24px;">
            <p style="font-family:'Archivo Black',sans-serif;font-size:22px;color:#FF6B35;margin:0 0 24px 0;text-align:center;">DROP YOUR FILES ABOVE</p>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:24px;">
                <div><p style="{col_label}">Documents</p>{badges(["PDF","DOCX","PPTX","XLSX","EPUB"])}</div>
                <div><p style="{col_label}">Web &amp; Data</p>{badges(["HTML","CSV","JSON","XML"])}</div>
                <div><p style="{col_label}">Images</p>{badges(["PNG","JPG","JPEG","GIF"])}</div>
                <div><p style="{col_label}">Code &amp; Archives</p>{badges(["H","HPP","HXX","CPP","CXX","C","ZIP"])}</div>
            </div>
            <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#4A4A4A;margin:0;text-align:center;border-top:2px solid #1E1E1E;padding-top:16px;">
                Up to <strong style="font-family:'JetBrains Mono',monospace;">{MAX_FILE_SIZE_MB}MB</strong> per file.
                Converted Markdown stays on your machine — nothing is uploaded anywhere.
            </p>
        </div>
        """
    st.markdown("\n".join(l for l in _html.splitlines() if l.strip()), unsafe_allow_html=True)


def _protection_status_label(protection_kind: str | None) -> tuple[str, str, str]:
    if protection_kind == PROTECTED_KIND_PDF:
        return ("PROTECTED PDF", "#FFD23F", "#1E1E1E")
    if protection_kind == PROTECTED_KIND_OFFICE:
        return ("PROTECTED OFFICE", "#7B61FF", "#FFFFFF")
    if protection_kind == PROTECTED_KIND_UNSUPPORTED:
        return ("UNSUPPORTED PROTECTED", "#EF476F", "#FFFFFF")
    return ("READY", "#06D6A0", "#1E1E1E")


def _render_file_card(uploaded_file, protection_kind: str | None) -> None:
    extension = Path(uploaded_file.name).suffix.lstrip(".").upper() or "FILE"
    status_label, status_bg, status_fg = _protection_status_label(protection_kind)
    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 18px 20px;
            margin: 10px 0;
            min-height: 132px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
                <span style="
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 13px;
                    background: #1E1E1E;
                    color: white;
                    border: 2px solid #1E1E1E;
                    border-radius: 6px;
                    padding: 2px 10px;
                ">{extension}</span>
                <span style="
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 11px;
                    background: {status_bg};
                    color: {status_fg};
                    border: 2px solid #1E1E1E;
                    border-radius: 6px;
                    padding: 3px 8px;
                    text-align: center;
                ">{status_label}</span>
            </div>
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 16px;
                color: #1E1E1E;
                margin: 14px 0 10px 0;
                line-height: 1.35;
                word-break: break-word;
            ">{uploaded_file.name}</p>
            <p style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                color: #4A4A4A;
                margin: 0;
            ">{uploaded_file.size / 1024:.1f} KB</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_file_list(uploaded_files: list, protection_kinds: dict[int, str | None]) -> None:
    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 20px 24px;
            margin: 16px 0;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 16px;
                color: #1E1E1E;
                margin: 0;
            ">{len(uploaded_files)} FILE{'S' if len(uploaded_files) != 1 else ''} IN QUEUE</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_columns = None
    for index, uploaded_file in enumerate(uploaded_files):
        if index % 2 == 0:
            current_columns = st.columns(2, gap="medium")
        with current_columns[index % 2]:
            _render_file_card(uploaded_file, protection_kinds.get(index))


def _render_result(filename: str, ok: bool, content: str, show_download: bool = True) -> None:
    stem = Path(filename).stem
    if ok:
        st.success(f"Converted: {filename}")
        with st.expander("Rendered preview", expanded=True):
            st.markdown(content)
        st.text_area("Raw Markdown", content, height=300, key=f"raw_{filename}")
        if show_download:
            st.download_button(
                label="DOWNLOAD .MD",
                data=content,
                file_name=f"{stem}.md",
                mime="text/markdown",
                key=f"dl_{filename}",
            )
    else:
        st.error(f"Failed to convert {filename}: {content}")


def _render_mode_switch() -> str:
    selected_mode = st.radio(
        "Input mode",
        [FILES_MODE, PASTE_MODE],
        key=INPUT_MODE_KEY,
        horizontal=True,
        label_visibility="collapsed",
    )
    previous_mode = st.session_state.get(PREVIOUS_INPUT_MODE_KEY)
    if previous_mode is None:
        st.session_state[PREVIOUS_INPUT_MODE_KEY] = selected_mode
    elif previous_mode != selected_mode:
        clear_session_state()
        st.session_state[PREVIOUS_INPUT_MODE_KEY] = selected_mode
        st.session_state[PASTE_RESET_NONCE_KEY] = st.session_state.get(PASTE_RESET_NONCE_KEY, 0) + 1

    return selected_mode


def clear_session_state() -> None:
    """Clear Convert-page session data when uploads reset or the user navigates away."""
    st.session_state.pop(CONVERSION_RESULTS_KEY, None)


def _build_successful_files(results: dict[str, tuple[bool, str]]) -> dict[str, str]:
    successful_files: dict[str, str] = {}
    used_names: set[str] = set()

    for filename, (ok, content) in results.items():
        if not ok:
            continue

        stem = Path(filename).stem or "output"
        archive_name = f"{stem}.md"
        counter = 2
        while archive_name in used_names:
            archive_name = f"{stem}-{counter}.md"
            counter += 1

        used_names.add(archive_name)
        successful_files[archive_name] = content

    return successful_files


def _render_batch_downloads(results: dict[str, tuple[bool, str]]) -> None:
    successful_files = _build_successful_files(results)
    file_count = len(successful_files)
    if file_count < 2:
        return

    today = date.today().isoformat()
    zip_label = f"Download all as ZIP ({file_count} files)"
    zip_filename = f"converted-{today}.zip"
    merged_filename = f"merged-{today}.md"

    zip_path: Optional[Path] = None
    try:
        zip_path = create_zip(successful_files, TEMP_DIR)
        zip_bytes = zip_path.read_bytes()
    finally:
        if zip_path is not None:
            cleanup_zip(zip_path)

    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.download_button(
            label=zip_label,
            data=zip_bytes,
            file_name=zip_filename,
            mime="application/zip",
            use_container_width=True,
            key="download_zip_export",
        )

    with right_col:
        st.download_button(
            label="Download as single .md",
            data=merge_to_markdown(successful_files),
            file_name=merged_filename,
            mime="text/markdown",
            use_container_width=True,
            key="download_merged_markdown",
        )


def _render_paste_mode_intro() -> None:
    st.markdown(
        """
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 20px 24px;
            margin: 16px 0;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 16px;
                color: #1E1E1E;
                margin: 0 0 8px 0;
            ">PASTE RICH TEXT</p>
            <p style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 14px;
                color: #4A4A4A;
                margin: 0;
                line-height: 1.5;
            ">
                Paste formatted text from Google Docs, Word, email, or a web page.
                The app will keep rich HTML when the browser exposes it, then convert locally to Markdown.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_paste_mode() -> None:
    _render_paste_mode_intro()
    payload = render_rich_text_paste_input(
        key=f"rich_text_paste_input_{st.session_state.get(PASTE_RESET_NONCE_KEY, 0)}",
        placeholder="Paste formatted content here",
        reset_nonce=st.session_state.get(PASTE_RESET_NONCE_KEY, 0),
    )
    has_content = payload["has_content"]

    if not has_content:
        st.caption("Paste content into the editor above to enable conversion.")

    if st.button("CONVERT", use_container_width=True, key="convert_pasted_rich_text", disabled=not has_content):
        html_content = payload["html"]
        text_content = payload["text"]
        started_at = perf_counter()
        ok, content = route_rich_text(html_content, text_content)
        file_size = len((html_content or text_content or "").encode("utf-8"))
        _store_history_record(
            filename=PASTED_FILENAME,
            extension="html",
            ok=ok,
            duration_seconds=perf_counter() - started_at,
            file_size=file_size,
            message=content,
        )
        st.session_state[CONVERSION_RESULTS_KEY] = {PASTED_FILENAME: (ok, content)}

    if CONVERSION_RESULTS_KEY not in st.session_state:
        return

    results = st.session_state[CONVERSION_RESULTS_KEY]
    filename, (ok, content) = next(iter(results.items()))
    _render_result(filename, ok, content)


def _render_file_mode() -> None:
    uploaded_files = st.file_uploader(
        "Upload documents to convert",
        type=ACCEPTED_EXTENSIONS,
        accept_multiple_files=True,
        help=f"Max {MAX_FILE_SIZE_MB}MB per file. All processing happens locally.",
        label_visibility="collapsed",
    )

    if not uploaded_files:
        clear_session_state()
        _render_empty_state()
        return

    protection_kinds = {
        index: _get_file_protection_kind(uploaded_file)
        for index, uploaded_file in enumerate(uploaded_files)
    }
    _render_file_list(uploaded_files, protection_kinds)
    password_inputs = _render_protected_files_section(uploaded_files, protection_kinds)

    if st.button("CONVERT", use_container_width=True):
        results: dict[str, tuple[bool, str]] = {}
        with st.spinner("Converting files…"):
            TEMP_DIR.mkdir(exist_ok=True)
            for index, uploaded_file in enumerate(uploaded_files):
                started_at = perf_counter()
                suffix = Path(uploaded_file.name).suffix

                if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    error_message = f"File exceeds the {MAX_FILE_SIZE_MB}MB limit."
                    results[uploaded_file.name] = (
                        False,
                        error_message,
                    )
                    _store_history_record(
                        filename=uploaded_file.name,
                        extension=suffix,
                        ok=False,
                        duration_seconds=perf_counter() - started_at,
                        file_size=uploaded_file.size,
                        message=error_message,
                    )
                    continue

                temp_path = TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"
                unlocked_temp_path: Optional[Path] = None
                try:
                    temp_path.write_bytes(uploaded_file.getvalue())

                    protection_kind = protection_kinds.get(index)
                    if protection_kind == PROTECTED_KIND_UNSUPPORTED:
                        error_message = "This password-protected file type is not supported yet. Please unlock it before upload."
                        results[uploaded_file.name] = (False, error_message)
                        _store_history_record(
                            filename=uploaded_file.name,
                            extension=suffix,
                            ok=False,
                            duration_seconds=perf_counter() - started_at,
                            file_size=uploaded_file.size,
                            message=error_message,
                        )
                        continue

                    file_to_convert = temp_path
                    if protection_kind in SUPPORTED_PROTECTED_KINDS:
                        password_input = password_inputs.get(index, {})
                        selected_profile_id = password_input.get("profile_id")
                        password = ""
                        if selected_profile_id is not None:
                            stored_password = get_password(selected_profile_id)
                            if stored_password is None:
                                error_message = (
                                    "The selected saved profile could not be read from the secure credential store."
                                )
                                results[uploaded_file.name] = (
                                    False,
                                    error_message,
                                )
                                _store_history_record(
                                    filename=uploaded_file.name,
                                    extension=suffix,
                                    ok=False,
                                    duration_seconds=perf_counter() - started_at,
                                    file_size=uploaded_file.size,
                                    message=error_message,
                                )
                                continue
                            password = stored_password
                        else:
                            password = str(password_input.get("password") or "")

                        if not password:
                            error_message = "This file is password protected. Enter a password to convert it."
                            results[uploaded_file.name] = (
                                False,
                                error_message,
                            )
                            _store_history_record(
                                filename=uploaded_file.name,
                                extension=suffix,
                                ok=False,
                                duration_seconds=perf_counter() - started_at,
                                file_size=uploaded_file.size,
                                message=error_message,
                            )
                            continue

                        try:
                            if protection_kind == PROTECTED_KIND_PDF:
                                unlocked_temp_path = unlock_pdf(temp_path, password, TEMP_DIR)
                            else:
                                unlocked_temp_path = unlock_office_file(temp_path, password, TEMP_DIR)
                        except ValueError:
                            error_message = "The password appears to be incorrect. Please check and try again."
                            results[uploaded_file.name] = (
                                False,
                                error_message,
                            )
                            _store_history_record(
                                filename=uploaded_file.name,
                                extension=suffix,
                                ok=False,
                                duration_seconds=perf_counter() - started_at,
                                file_size=uploaded_file.size,
                                message=error_message,
                            )
                            continue
                        except RuntimeError as exc:
                            error_message = str(exc)
                            results[uploaded_file.name] = (False, error_message)
                            _store_history_record(
                                filename=uploaded_file.name,
                                extension=suffix,
                                ok=False,
                                duration_seconds=perf_counter() - started_at,
                                file_size=uploaded_file.size,
                                message=error_message,
                            )
                            continue

                        file_to_convert = unlocked_temp_path

                    ok, content = route_file(file_to_convert, engine=ENGINE_NAME)
                    results[uploaded_file.name] = (ok, content)
                    if ok and protection_kind in SUPPORTED_PROTECTED_KINDS:
                        password_input = password_inputs.get(index, {})
                        selected_profile_id = password_input.get("profile_id")
                        if selected_profile_id is not None:
                            selected_profile_id = int(selected_profile_id)
                            update_last_used(selected_profile_id)
                            st.session_state[LAST_PASSWORD_PROFILE_KEY] = selected_profile_id
                        elif password_input.get("save_after_success"):
                            new_profile_name = str(password_input.get("new_profile_name") or "").strip()
                            new_profile_pattern = str(password_input.get("new_profile_pattern") or "").strip()
                            if new_profile_name:
                                profile_id: int | None = None
                                try:
                                    profile_id = insert_profile(
                                        new_profile_name,
                                        new_profile_pattern or None,
                                        "pending",
                                        "pending",
                                    )
                                    save_password(profile_id, password)
                                    st.session_state[LAST_PASSWORD_PROFILE_KEY] = profile_id
                                except sqlite3.IntegrityError:
                                    st.warning(
                                        f"Converted {uploaded_file.name}, but the new profile name already exists."
                                    )
                                except Exception:
                                    if profile_id is not None:
                                        try:
                                            delete_profile(profile_id)
                                        except Exception:
                                            pass
                                    st.warning(
                                        f"Converted {uploaded_file.name}, but the password profile could not be saved."
                                    )

                    logger.info(
                        "Conversion %s: %s (%s)",
                        "success" if ok else "failed",
                        uploaded_file.name,
                        suffix,
                    )
                    _store_history_record(
                        filename=uploaded_file.name,
                        extension=suffix,
                        ok=ok,
                        duration_seconds=perf_counter() - started_at,
                        file_size=uploaded_file.size,
                        message=content,
                    )
                finally:
                    if unlocked_temp_path is not None:
                        cleanup_temp_file(unlocked_temp_path)
                    cleanup_temp_file(temp_path)

        st.session_state[CONVERSION_RESULTS_KEY] = results

    if CONVERSION_RESULTS_KEY not in st.session_state:
        return

    results = st.session_state[CONVERSION_RESULTS_KEY]
    successful_files = _build_successful_files(results)
    _render_batch_downloads(results)

    if len(results) == 1:
        filename, (ok, content) = next(iter(results.items()))
        _render_result(filename, ok, content)
    else:
        show_individual_downloads = len(successful_files) < 2
        for filename, (ok, content) in results.items():
            label = f"✓ {filename}" if ok else f"✗ {filename}"
            with st.expander(label, expanded=ok):
                _render_result(filename, ok, content, show_download=show_individual_downloads)


def _profile_option_label(profile: dict) -> str:
    pattern = profile["filename_match_pattern"] or "No pattern"
    return f"{profile['profile_name']} ({pattern})"


def _build_profile_options(profiles: list[dict]) -> list[tuple[str, int | None]]:
    return [("Manual password", None)] + [
        (_profile_option_label(profile), profile["id"]) for profile in profiles
    ]


def _find_option_index(options: list[tuple[str, int | None]], profile_id: int | None) -> int:
    for index, (_, option_profile_id) in enumerate(options):
        if option_profile_id == profile_id:
            return index
    return 0


def _get_selected_profile_id(selected_label: str, options: list[tuple[str, int | None]]) -> int | None:
    return next(profile_id for label, profile_id in options if label == selected_label)


def _common_matching_profile_id(
    protected_indices: list[int],
    matching_profiles_by_index: dict[int, list[dict]],
) -> int | None:
    matching_profile_ids: list[int] = []
    for index in protected_indices:
        matches = matching_profiles_by_index.get(index, [])
        if not matches:
            return None
        matching_profile_ids.append(matches[0]["id"])

    if matching_profile_ids and len(set(matching_profile_ids)) == 1:
        return matching_profile_ids[0]
    return None


def _is_encrypted_pdf(uploaded_file) -> bool:
    if Path(uploaded_file.name).suffix.lower() != ".pdf":
        return False
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False

    TEMP_DIR.mkdir(exist_ok=True)
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}.pdf"
    try:
        temp_path.write_bytes(uploaded_file.getvalue())
        return is_pdf_encrypted(temp_path)
    finally:
        cleanup_temp_file(temp_path)


def _is_zip_encrypted(filepath: Path) -> bool:
    try:
        with zipfile.ZipFile(filepath) as archive:
            return any(info.flag_bits & 0x1 for info in archive.infolist())
    except Exception:
        return False


def _get_file_protection_kind(uploaded_file) -> str | None:
    suffix = Path(uploaded_file.name).suffix.lower()
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return None

    TEMP_DIR.mkdir(exist_ok=True)
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"
    try:
        temp_path.write_bytes(uploaded_file.getvalue())
        if suffix == ".pdf" and is_pdf_encrypted(temp_path):
            return PROTECTED_KIND_PDF
        if suffix in {".docx", ".xlsx", ".pptx"} and is_office_file_encrypted(temp_path):
            return PROTECTED_KIND_OFFICE
        if suffix == ".zip" and _is_zip_encrypted(temp_path):
            return PROTECTED_KIND_UNSUPPORTED
        return None
    finally:
        cleanup_temp_file(temp_path)


def _render_protected_file_intro(protected_count: int, unsupported_count: int) -> None:
    unsupported_text = ""
    if unsupported_count:
        unsupported_text = (
            f"<br><br><strong>{unsupported_count} protected file"
            f"{'s are' if unsupported_count != 1 else ' is'} not supported yet.</strong>"
        )

    st.markdown(
        f"""
        <div style="
            background: #FFD23F;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 22px 24px;
            margin: 20px 0 12px 0;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 18px;
                color: #1E1E1E;
                margin: 0 0 8px 0;
            ">PROTECTED FILES</p>
            <p style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 14px;
                color: #1E1E1E;
                margin: 0;
                line-height: 1.5;
            ">
                {protected_count} password-protected file{'s need' if protected_count != 1 else ' needs'} setup before conversion.
                Saved profiles and manual passwords live here so the main conversion flow stays clean.
                {unsupported_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_protected_file_card_header(uploaded_file, protection_kind: str) -> None:
    kind_label = "PDF" if protection_kind == PROTECTED_KIND_PDF else "OFFICE"
    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 18px 20px;
            margin: 10px 0 12px 0;
            min-height: 118px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px;">
                <span style="
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 12px;
                    background: #1E1E1E;
                    color: white;
                    border: 2px solid #1E1E1E;
                    border-radius: 6px;
                    padding: 2px 10px;
                ">{kind_label}</span>
                <span style="
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 11px;
                    background: #7B61FF;
                    color: white;
                    border: 2px solid #1E1E1E;
                    border-radius: 6px;
                    padding: 3px 8px;
                ">PASSWORD REQUIRED</span>
            </div>
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 15px;
                color: #1E1E1E;
                margin: 14px 0 10px 0;
                line-height: 1.35;
                word-break: break-word;
            ">{uploaded_file.name}</p>
            <p style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                color: #4A4A4A;
                margin: 0;
            ">{uploaded_file.size / 1024:.1f} KB</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_unsupported_protected_files(uploaded_files: list, unsupported_indices: list[int]) -> None:
    if not unsupported_indices:
        return

    unsupported_names = ", ".join(uploaded_files[index].name for index in unsupported_indices)
    st.warning(
        "These password-protected files are not supported yet and should be unlocked before upload: "
        f"{unsupported_names}"
    )


def _render_protected_files_section(
    uploaded_files: list,
    protection_kinds: dict[int, str | None],
) -> dict[int, dict[str, str | bool | int | None]]:
    password_inputs: dict[int, dict[str, str | bool | int | None]] = {}
    protected_indices = [
        index for index, kind in protection_kinds.items() if kind in SUPPORTED_PROTECTED_KINDS
    ]
    unsupported_indices = [
        index for index, kind in protection_kinds.items() if kind == PROTECTED_KIND_UNSUPPORTED
    ]
    if not protected_indices and not unsupported_indices:
        return password_inputs

    _render_protected_file_intro(len(protected_indices), len(unsupported_indices))
    _render_unsupported_protected_files(uploaded_files, unsupported_indices)

    if not protected_indices:
        return password_inputs

    all_profiles = get_all_profiles()
    matching_profiles_by_index = {
        index: get_matching_profiles(uploaded_files[index].name)
        for index in protected_indices
    }
    protected_signature = str(abs(hash(tuple(
        (uploaded_files[index].name, protection_kinds[index])
        for index in protected_indices
    ))))
    options = _build_profile_options(all_profiles)
    batch_profile_id: int | None = None

    if all_profiles:
        profile_ids = {profile["id"] for profile in all_profiles}
        remembered_profile_id = st.session_state.get(LAST_PASSWORD_PROFILE_KEY)
        if remembered_profile_id not in profile_ids:
            remembered_profile_id = None

        default_profile_id = remembered_profile_id
        if default_profile_id is None:
            default_profile_id = _common_matching_profile_id(
                protected_indices,
                matching_profiles_by_index,
            )

        batch_selected_label = st.selectbox(
            "Use one saved profile for all protected files",
            options=[label for label, _ in options],
            index=_find_option_index(options, default_profile_id),
            key=(
                "batch_password_profile_selector_"
                f"{protected_signature}_{default_profile_id or 'manual'}"
            ),
        )
        batch_profile_id = _get_selected_profile_id(batch_selected_label, options)
    else:
        st.caption(
            "No saved profiles yet. Enter passwords manually here or create a reusable profile on the Password Profiles page."
        )

    current_columns = None
    for card_position, index in enumerate(protected_indices):
        if card_position % 2 == 0:
            current_columns = st.columns(2, gap="medium")
        with current_columns[card_position % 2]:
            uploaded_file = uploaded_files[index]
            protection_kind = protection_kinds[index]
            _render_protected_file_card_header(uploaded_file, protection_kind)
            matching_profiles = matching_profiles_by_index.get(index, [])
            suggested_profile = matching_profiles[0] if matching_profiles else None
            default_profile_id = batch_profile_id
            if default_profile_id is None and suggested_profile is not None:
                default_profile_id = suggested_profile["id"]

            selected_label = st.selectbox(
                f"Saved profile for {uploaded_file.name}",
                options=[label for label, _ in options],
                index=_find_option_index(options, default_profile_id),
                key=f"saved_profile_{protected_signature}_{index}_{batch_profile_id or 'manual'}",
            )
            selected_profile_id = _get_selected_profile_id(selected_label, options)

            if suggested_profile is not None:
                st.caption(
                    f"Suggested profile based on filename pattern: {suggested_profile['profile_name']}"
                )

            if selected_profile_id is None:
                manual_password = st.text_input(
                    f"Password for {uploaded_file.name}",
                    type="password",
                    autocomplete="off",
                    key=f"manual_password_{protected_signature}_{index}",
                )
                save_after_success = st.checkbox(
                    f"Save this password if conversion succeeds for {uploaded_file.name}",
                    key=f"save_password_{protected_signature}_{index}",
                )
                new_profile_name = ""
                new_profile_pattern = ""
                if save_after_success:
                    new_profile_name = st.text_input(
                        f"New profile name for {uploaded_file.name}",
                        value=Path(uploaded_file.name).stem,
                        key=f"new_profile_name_{protected_signature}_{index}",
                    )
                    new_profile_pattern = st.text_input(
                        f"Filename pattern for {uploaded_file.name}",
                        value=f"*{Path(uploaded_file.name).stem}*",
                        key=f"new_profile_pattern_{protected_signature}_{index}",
                    )
                password_inputs[index] = {
                    "profile_id": None,
                    "password": manual_password,
                    "save_after_success": save_after_success,
                    "new_profile_name": new_profile_name,
                    "new_profile_pattern": new_profile_pattern,
                }
            else:
                password_inputs[index] = {
                    "profile_id": selected_profile_id,
                    "password": None,
                    "save_after_success": False,
                    "new_profile_name": "",
                    "new_profile_pattern": "",
                }

    return password_inputs


def render(page_header) -> None:
    """Convert page — document-to-Markdown conversion."""
    page_header("CONVERT", "#FF6B35")
    selected_mode = _render_mode_switch()
    if selected_mode == PASTE_MODE:
        _render_paste_mode()
        return

    _render_file_mode()
