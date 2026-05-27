from html import escape

import streamlit as st

from src.db.history import clear_history, get_all_records

CONFIRM_STATE_KEY = "history_confirm_clear"
FLASH_STATE_KEY = "history_flash_message"


def _format_timestamp(timestamp: str) -> str:
    """Render SQLite timestamps in a compact, readable format."""
    return timestamp.replace("T", " ")


def _format_duration(duration: float | None) -> str:
    """Render conversion durations for table display."""
    if duration is None:
        return "-"
    return f"{duration:.2f}s"


def _render_empty_state() -> None:
    """Show the metadata-only empty state for history."""
    st.markdown(
        """
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 40px 32px;
            text-align: center;
            margin-top: 24px;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 22px;
                color: #3A86FF;
                margin: 0 0 12px 0;
            ">NO HISTORY YET</p>
            <p style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 15px;
                color: #4A4A4A;
                margin: 0;
            ">
                Converted files will appear here as metadata-only records.<br>
                No document content, decrypted files, file paths, or passwords are stored.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _status_badge(status: str) -> str:
    """Render a styled status badge for the history table."""
    colors = {
        "success": ("#06D6A0", "#1E1E1E"),
        "failed": ("#EF476F", "#FFFFFF"),
        "partial": ("#FFD23F", "#1E1E1E"),
    }
    background, text_color = colors.get(status, ("#7B61FF", "#FFFFFF"))
    return (
        "<span style=\""
        "display: inline-block;"
        "padding: 4px 10px;"
        "border: 2px solid #1E1E1E;"
        "border-radius: 6px;"
        "font-family: 'JetBrains Mono', monospace;"
        "font-size: 12px;"
        f"background: {background};"
        f"color: {text_color};"
        "\">"
        f"{escape(status.upper())}"
        "</span>"
    )


def _render_table(records: list[dict]) -> None:
    """Render the metadata history table."""
    rows_html = "".join(
        f"""
        <tr style="border-bottom: 2px solid #1E1E1E;">
            <td style="padding: 14px 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px;">{escape(_format_timestamp(record["converted_at"]))}</td>
            <td style="padding: 14px 12px;">{escape(record["original_file_name"])}</td>
            <td style="padding: 14px 12px; font-family: 'JetBrains Mono', monospace;">{escape(record["original_file_extension"].upper())}</td>
            <td style="padding: 14px 12px; font-family: 'JetBrains Mono', monospace;">{escape(record["conversion_engine"])}</td>
            <td style="padding: 14px 12px;">{_status_badge(record["conversion_status"])}</td>
            <td style="padding: 14px 12px; font-family: 'JetBrains Mono', monospace;">{escape(_format_duration(record["conversion_duration_seconds"]))}</td>
            <td style="padding: 14px 12px; font-family: 'JetBrains Mono', monospace;">{escape(record["output_file_name"] or "-")}</td>
        </tr>
        """
        for record in records
    )

    st.markdown(
        f"""
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 0;
            margin-top: 16px;
            overflow-x: auto;
        ">
            <table style="
                width: 100%;
                border-collapse: collapse;
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 14px;
            ">
                <thead>
                    <tr style="background: #1E1E1E; color: white; text-align: left;">
                        <th style="padding: 14px 12px; font-family: 'Archivo Black', sans-serif;">DATE</th>
                        <th style="padding: 14px 12px; font-family: 'Archivo Black', sans-serif;">FILENAME</th>
                        <th style="padding: 14px 12px; font-family: 'Archivo Black', sans-serif;">FILE TYPE</th>
                        <th style="padding: 14px 12px; font-family: 'Archivo Black', sans-serif;">ENGINE</th>
                        <th style="padding: 14px 12px; font-family: 'Archivo Black', sans-serif;">STATUS</th>
                        <th style="padding: 14px 12px; font-family: 'Archivo Black', sans-serif;">DURATION</th>
                        <th style="padding: 14px 12px; font-family: 'Archivo Black', sans-serif;">OUTPUT NAME</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(page_header) -> None:
    """History page — conversion metadata log."""
    page_header("HISTORY", "#3A86FF")

    flash_message = st.session_state.pop(FLASH_STATE_KEY, None)
    if flash_message:
        st.success(flash_message)

    records = get_all_records()

    action_col, _ = st.columns([1, 3])
    with action_col:
        if records and st.button("CLEAR HISTORY", use_container_width=True):
            st.session_state[CONFIRM_STATE_KEY] = True

    if st.session_state.get(CONFIRM_STATE_KEY):
        st.warning("Clear all conversion metadata history? This removes the stored history rows only.")
        confirm_col, cancel_col, _ = st.columns([1, 1, 2])
        with confirm_col:
            if st.button("CONFIRM CLEAR", use_container_width=True):
                clear_history()
                st.session_state[CONFIRM_STATE_KEY] = False
                st.session_state[FLASH_STATE_KEY] = "Conversion history cleared."
                st.rerun()
        with cancel_col:
            if st.button("CANCEL", use_container_width=True):
                st.session_state[CONFIRM_STATE_KEY] = False
                st.rerun()

    if not records:
        _render_empty_state()
        return

    st.caption("Metadata only: filename, extension, engine, status, duration, output name, and timestamp.")
    _render_table(records)
