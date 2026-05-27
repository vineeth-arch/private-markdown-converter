import os
import uuid
import logging
from pathlib import Path
from typing import Optional

import streamlit as st

from src.converters.router import route_file
from src.security.pdf_unlock import is_pdf_encrypted, unlock_pdf
from src.security.temp_cleanup import cleanup_temp_file

logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

ACCEPTED_EXTENSIONS = [
    "pdf", "docx", "pptx", "xlsx", "html", "csv",
    "json", "xml", "epub", "png", "jpg", "jpeg", "gif", "zip",
]


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


def _render_result(filename: str, ok: bool, content: str) -> None:
    stem = Path(filename).stem
    if ok:
        st.success(f"Converted: {filename}")
        with st.expander("Rendered preview", expanded=True):
            st.markdown(content)
        st.text_area("Raw Markdown", content, height=300, key=f"raw_{filename}")
        st.download_button(
            label="DOWNLOAD .MD",
            data=content,
            file_name=f"{stem}.md",
            mime="text/markdown",
            key=f"dl_{filename}",
        )
    else:
        st.error(f"Failed to convert {filename}: {content}")


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


def _render_password_fields(uploaded_files: list, encrypted_flags: list[bool]) -> dict[int, str]:
    passwords: dict[int, str] = {}
    encrypted_count = sum(encrypted_flags)
    if encrypted_count == 0:
        return passwords

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
                Enter a password only for the protected PDFs below. Unlocked files are created in temp, converted, and deleted immediately.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, uploaded_file in enumerate(uploaded_files):
        if not encrypted_flags[index]:
            continue

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

        st.selectbox(
            f"Saved Profiles for {uploaded_file.name}",
            options=["Coming in Phase 4"],
            index=0,
            disabled=True,
            key=f"saved_profile_{index}",
        )
        passwords[index] = st.text_input(
            f"PDF Password for {uploaded_file.name}",
            type="password",
            key=f"pdf_password_{index}",
            autocomplete="off",
        )

    return passwords


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
        if "conversion_results" in st.session_state:
            del st.session_state["conversion_results"]
        _render_empty_state()
        return

    _render_file_list(uploaded_files)
    encrypted_flags = [_is_encrypted_pdf(uploaded_file) for uploaded_file in uploaded_files]
    pdf_passwords = _render_password_fields(uploaded_files, encrypted_flags)

    if st.button("CONVERT", use_container_width=True):
        results: dict[str, tuple[bool, str]] = {}
        with st.spinner("Converting files…"):
            TEMP_DIR.mkdir(exist_ok=True)
            for index, uploaded_file in enumerate(uploaded_files):
                if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    results[uploaded_file.name] = (
                        False,
                        f"File exceeds the {MAX_FILE_SIZE_MB}MB limit.",
                    )
                    continue

                suffix = Path(uploaded_file.name).suffix
                temp_path = TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"
                unlocked_temp_path: Optional[Path] = None
                try:
                    temp_path.write_bytes(uploaded_file.getvalue())

                    file_to_convert = temp_path
                    if encrypted_flags[index]:
                        password = pdf_passwords.get(index, "")
                        if not password:
                            results[uploaded_file.name] = (
                                False,
                                "This PDF is password protected. Enter a password to convert it.",
                            )
                            continue

                        try:
                            unlocked_temp_path = unlock_pdf(temp_path, password, TEMP_DIR)
                        except ValueError:
                            results[uploaded_file.name] = (
                                False,
                                "The password appears to be incorrect. Please check and try again.",
                            )
                            continue
                        except RuntimeError as exc:
                            results[uploaded_file.name] = (False, str(exc))
                            continue

                        file_to_convert = unlocked_temp_path

                    ok, content = route_file(file_to_convert)
                    results[uploaded_file.name] = (ok, content)
                    logger.info(
                        "Conversion %s: %s (%s)",
                        "success" if ok else "failed",
                        uploaded_file.name,
                        suffix,
                    )
                finally:
                    if unlocked_temp_path is not None:
                        cleanup_temp_file(unlocked_temp_path)
                    cleanup_temp_file(temp_path)

        st.session_state["conversion_results"] = results

    if "conversion_results" not in st.session_state:
        return

    results = st.session_state["conversion_results"]

    if len(results) == 1:
        filename, (ok, content) = next(iter(results.items()))
        _render_result(filename, ok, content)
    else:
        for filename, (ok, content) in results.items():
            label = f"✓ {filename}" if ok else f"✗ {filename}"
            with st.expander(label, expanded=ok):
                _render_result(filename, ok, content)
