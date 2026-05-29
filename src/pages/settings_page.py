import os
import streamlit as st


MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))


_ROW_STYLE = (
    "display: flex; align-items: baseline; gap: 16px; padding: 14px 0;"
    " border-bottom: 2px solid #F0EBE3;"
)
_LABEL_STYLE = (
    "font-family: 'Plus Jakarta Sans', sans-serif; font-size: 14px; font-weight: 700;"
    " color: #1E1E1E; min-width: 180px; flex-shrink: 0;"
)
_VALUE_STYLE = (
    "font-family: 'JetBrains Mono', monospace; font-size: 14px; color: #4A4A4A;"
)
_BADGE_BASE = (
    "display: inline-block; padding: 3px 12px; border: 2px solid #1E1E1E;"
    " border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 12px;"
    " font-weight: 600; margin-right: 8px;"
)


def _setting_row(label: str, value: str, accent: str = "#00CFE8") -> str:
    return f"""
    <div style="{_ROW_STYLE}">
        <div style="width: 4px; min-height: 32px; background: {accent}; border-radius: 2px; flex-shrink: 0;"></div>
        <div style="{_LABEL_STYLE}">{label}</div>
        <div style="{_VALUE_STYLE}">{value}</div>
    </div>
    """


def render(page_header) -> None:
    """Settings page — app configuration."""
    page_header("SETTINGS", "#00CFE8")

    # Card 1 — App Configuration
    _html1 = f"""
        <div style="background:#FFFFFF;border:3px solid #1E1E1E;border-radius:12px;box-shadow:5px 5px 0 #1E1E1E;padding:28px 32px;margin-top:24px;">
            <p style="font-family:'Archivo Black',sans-serif;font-size:18px;color:#1E1E1E;margin:0 0 4px 0;">App Configuration</p>
            {_setting_row("Max file size", f"{MAX_FILE_SIZE_MB} MB")}
            {_setting_row("Storage mode", "Local only — nothing leaves this machine")}
            {_setting_row("Password storage", "macOS Keychain (via keyring)")}
            {_setting_row("Conversion engine", "MarkItDown (default)")}
            <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#888;margin:16px 0 0 0;">
                To change <code>MAX_FILE_SIZE_MB</code>, edit <code>.env</code> and restart the app.
            </p>
        </div>
        """
    st.markdown("\n".join(l for l in _html1.splitlines() if l.strip()), unsafe_allow_html=True)

    # Card 2 — Conversion Engines
    markitdown_badge = f'<span style="{_BADGE_BASE} background: #7B61FF; color: white;">MarkItDown</span>'
    h2md_badge = f'<span style="{_BADGE_BASE} background: #FF6B35; color: white;">h2md (built-in)</span>'

    _html2 = f"""
        <div style="background:#FFFFFF;border:3px solid #1E1E1E;border-radius:12px;box-shadow:5px 5px 0 #1E1E1E;padding:28px 32px;margin-top:24px;">
            <p style="font-family:'Archivo Black',sans-serif;font-size:18px;color:#1E1E1E;margin:0 0 4px 0;">Conversion Engines</p>
            <div style="{_ROW_STYLE}">
                <div style="width:4px;min-height:40px;background:#7B61FF;border-radius:2px;flex-shrink:0;"></div>
                <div style="flex:1;">
                    <div style="margin-bottom:6px;">{markitdown_badge}</div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:14px;color:#4A4A4A;">All document types: PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, EPUB, images, ZIP</div>
                </div>
            </div>
            <div style="{_ROW_STYLE} border-bottom:none;">
                <div style="width:4px;min-height:40px;background:#FF6B35;border-radius:2px;flex-shrink:0;"></div>
                <div style="flex:1;">
                    <div style="margin-bottom:6px;">{h2md_badge}</div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:14px;color:#4A4A4A;">C/C++ source &amp; headers: <code>.h .hpp .hh .hxx .cpp .cc .cxx .c</code> — extracts <code>/** */</code> doc comments; falls back to fenced code block</div>
                </div>
            </div>
        </div>
        """
    st.markdown("\n".join(l for l in _html2.splitlines() if l.strip()), unsafe_allow_html=True)
