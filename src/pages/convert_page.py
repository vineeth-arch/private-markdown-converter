import os
import sqlite3
import uuid
import logging
from datetime import date
from pathlib import Path
from time import perf_counter
from typing import Optional

import streamlit as st

from src.converters.router import route_file
from src.db.history import add_record
from src.db.password_profiles import (
    delete_profile,
    get_all_profiles,
    get_matching_profiles,
    insert_profile,
    update_last_used,
)
from src.export.zip_export import cleanup_zip, create_zip, merge_to_markdown
from src.security.password_vault import get_password, save_password
from src.security.pdf_unlock import is_pdf_encrypted, unlock_pdf
from src.security.temp_cleanup import cleanup_temp_file

logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ENGINE_NAME = "markitdown"
CONVERSION_RESULTS_KEY = "conversion_results"

ACCEPTED_EXTENSIONS = [
    "pdf", "docx", "pptx", "xlsx", "html", "csv",
    "json", "xml", "epub", "png", "jpg", "jpeg", "gif", "zip",
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
    st.markdown(
        """
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 48px 32px;
            text-align: center;
            margin-top: 24px;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 22px;
                color: #FF6B35;
                margin: 0 0 12px 0;
            ">DROP YOUR FILES ABOVE</p>
            <p style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 15px;
                color: #4A4A4A;
                margin: 0;
            ">
                PDF · DOCX · PPTX · XLSX · HTML · CSV · JSON · XML · EPUB · PNG · JPG · GIF · ZIP
                <br><br>
                Up to <strong style="font-family: 'JetBrains Mono', monospace;">{max_mb}MB</strong> per file.
                Converted Markdown stays on your machine — nothing is uploaded anywhere.
            </p>
        </div>
        """.format(max_mb=MAX_FILE_SIZE_MB),
        unsafe_allow_html=True,
    )


def _render_file_list(uploaded_files: list) -> None:
    items_html = "".join(
        f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid #E0E0E0;
        ">
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                background: #7B61FF;
                color: white;
                border: 2px solid #1E1E1E;
                border-radius: 6px;
                padding: 2px 10px;
            ">{Path(f.name).suffix.lstrip('.').upper() or 'FILE'}</span>
            <span style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 14px;
                color: #1E1E1E;
                flex: 1;
            ">{f.name}</span>
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                color: #4A4A4A;
            ">{f.size / 1024:.1f} KB</span>
        </div>
        """
        for f in uploaded_files
    )
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
                margin: 0 0 8px 0;
            ">{len(uploaded_files)} FILE{'S' if len(uploaded_files) != 1 else ''} READY</p>
            {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def _profile_option_label(profile: dict) -> str:
    pattern = profile["filename_match_pattern"] or "No pattern"
    return f"{profile['profile_name']} ({pattern})"


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


def _render_password_fields(uploaded_files: list, encrypted_flags: list[bool]) -> dict[int, dict[str, str | bool | int | None]]:
    password_inputs: dict[int, dict[str, str | bool | int | None]] = {}
    encrypted_count = sum(encrypted_flags)
    if encrypted_count == 0:
        return password_inputs

    all_profiles = get_all_profiles()

    st.markdown(
        f"""
        <div style="
            background: #FFD23F;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 20px 24px;
            margin: 16px 0 20px 0;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 16px;
                color: #1E1E1E;
                margin: 0 0 8px 0;
            ">{encrypted_count} ENCRYPTED PDF{'S' if encrypted_count != 1 else ''} DETECTED</p>
            <p style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 14px;
                color: #1E1E1E;
                margin: 0;
            ">
                Use a saved profile or enter a manual password for each protected PDF. Unlocked files are created in temp, converted, and deleted immediately.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, uploaded_file in enumerate(uploaded_files):
        if not encrypted_flags[index]:
            continue

        matching_profiles = get_matching_profiles(uploaded_file.name)
        suggested_profile = matching_profiles[0] if matching_profiles else None
        options: list[tuple[str, int | None]] = [("Manual password", None)]
        options.extend((_profile_option_label(profile), profile["id"]) for profile in all_profiles)
        default_option_index = 0
        if suggested_profile is not None:
            for option_index, (_, profile_id) in enumerate(options):
                if profile_id == suggested_profile["id"]:
                    default_option_index = option_index
                    break

        st.markdown(
            f"""
            <div style="
                background: #FFFFFF;
                border: 3px solid #1E1E1E;
                border-radius: 12px;
                box-shadow: 5px 5px 0 #1E1E1E;
                padding: 20px 24px;
                margin: 12px 0;
            ">
                <p style="
                    font-family: 'Archivo Black', sans-serif;
                    font-size: 14px;
                    color: #1E1E1E;
                    margin: 0 0 12px 0;
                ">{uploaded_file.name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_label = st.selectbox(
            f"Saved Profiles for {uploaded_file.name}",
            options=[label for label, _ in options],
            index=default_option_index,
            key=f"saved_profile_{index}",
        )
        selected_profile_id = next(
            profile_id for label, profile_id in options if label == selected_label
        )

        if suggested_profile is not None:
            st.caption(
                f"Suggested profile based on filename pattern: {suggested_profile['profile_name']}"
            )

        if selected_profile_id is None:
            manual_password = st.text_input(
                f"PDF Password for {uploaded_file.name}",
                type="password",
                autocomplete="off",
            )
            save_after_success = st.checkbox(
                f"Save this password if conversion succeeds for {uploaded_file.name}",
                key=f"save_password_{index}",
            )
            new_profile_name = ""
            new_profile_pattern = ""
            if save_after_success:
                new_profile_name = st.text_input(
                    f"New profile name for {uploaded_file.name}",
                    value=Path(uploaded_file.name).stem,
                )
                new_profile_pattern = st.text_input(
                    f"Filename pattern for {uploaded_file.name}",
                    value=f"*{Path(uploaded_file.name).stem}*",
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

    _render_file_list(uploaded_files)
    encrypted_flags = [_is_encrypted_pdf(uploaded_file) for uploaded_file in uploaded_files]
    password_inputs = _render_password_fields(uploaded_files, encrypted_flags)

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

                    file_to_convert = temp_path
                    if encrypted_flags[index]:
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
                            error_message = "This PDF is password protected. Enter a password to convert it."
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
                            unlocked_temp_path = unlock_pdf(temp_path, password, TEMP_DIR)
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
                    if ok and encrypted_flags[index]:
                        password_input = password_inputs.get(index, {})
                        selected_profile_id = password_input.get("profile_id")
                        if selected_profile_id is not None:
                            update_last_used(int(selected_profile_id))
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
