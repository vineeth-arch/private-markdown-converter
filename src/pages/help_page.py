import streamlit as st


# (type_name, extension_string, note, engine)
SUPPORTED_FILE_TYPES = [
    ("PDF", ".pdf", "Encrypted PDFs supported with password profiles", "markitdown"),
    ("Word", ".docx", "Microsoft Word documents", "markitdown"),
    ("PowerPoint", ".pptx", "Microsoft PowerPoint presentations", "markitdown"),
    ("Excel", ".xlsx", "Microsoft Excel spreadsheets", "markitdown"),
    ("HTML", ".html / .htm", "Web pages", "markitdown"),
    ("CSV", ".csv", "Comma-separated values", "markitdown"),
    ("JSON", ".json", "JSON data files", "markitdown"),
    ("XML", ".xml", "XML documents", "markitdown"),
    ("EPUB", ".epub", "E-book format", "markitdown"),
    ("Images", ".jpg / .jpeg / .png / .gif", "Image files", "markitdown"),
    ("ZIP", ".zip", "Archives (contents converted individually)", "markitdown"),
    ("C/C++ Headers", ".h / .hpp / .hh / .hxx", "Extracts /** */ doc comments to Markdown", "h2md"),
    ("C/C++ Source", ".cpp / .cc / .cxx / .c", "Doc comments or full fenced code block fallback", "h2md"),
]

_ENGINE_BADGE = {
    "markitdown": (
        "background: #7B61FF; color: white; display: inline-block; padding: 2px 10px;"
        " border: 2px solid #1E1E1E; border-radius: 6px; font-family: 'JetBrains Mono', monospace;"
        " font-size: 11px; font-weight: 600;"
    ),
    "h2md": (
        "background: #FF6B35; color: white; display: inline-block; padding: 2px 10px;"
        " border: 2px solid #1E1E1E; border-radius: 6px; font-family: 'JetBrains Mono', monospace;"
        " font-size: 11px; font-weight: 600;"
    ),
}


def render(page_header) -> None:
    """Help page — supported file types and usage guide."""
    page_header("HELP", "#06D6A0")

    st.markdown(
        """
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 32px;
            margin-top: 24px;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 18px;
                color: #1E1E1E;
                margin: 0 0 20px 0;
            ">Supported File Types</p>
        """,
        unsafe_allow_html=True,
    )

    rows_html = ""
    for i, (name, ext, note, engine) in enumerate(SUPPORTED_FILE_TYPES):
        bg = "#FFFFFF" if i % 2 == 0 else "#FFF8F0"
        engine_label = "MarkItDown" if engine == "markitdown" else "h2md"
        rows_html += f"""
        <tr style="background: {bg}; border-bottom: 2px solid #1E1E1E;">
            <td style="padding: 10px 16px; font-family: 'Archivo Black', sans-serif; font-size: 14px;">{name}</td>
            <td style="padding: 10px 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #7B61FF;">{ext}</td>
            <td style="padding: 10px 16px; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 14px; color: #4A4A4A;">{note}</td>
            <td style="padding: 10px 16px;"><span style="{_ENGINE_BADGE[engine]}">{engine_label}</span></td>
        </tr>
        """

    st.markdown(
        f"""
            <table style="width: 100%; border-collapse: collapse; border: 2px solid #1E1E1E; border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background: #1E1E1E;">
                        <th style="padding: 12px 16px; font-family: 'Archivo Black', sans-serif; font-size: 13px; color: white; text-align: left;">TYPE</th>
                        <th style="padding: 12px 16px; font-family: 'Archivo Black', sans-serif; font-size: 13px; color: white; text-align: left;">EXTENSION</th>
                        <th style="padding: 12px 16px; font-family: 'Archivo Black', sans-serif; font-size: 13px; color: white; text-align: left;">NOTES</th>
                        <th style="padding: 12px 16px; font-family: 'Archivo Black', sans-serif; font-size: 13px; color: white; text-align: left;">ENGINE</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _PRIVACY_ITEMS = [
        ("#3A86FF", "No Cloud Upload", "Everything stays on your machine. No files are sent anywhere."),
        ("#06D6A0", "Temp Files Deleted", "Files are processed in memory and removed from temp/ immediately after conversion."),
        ("#FF6B35", "Markdown Not Stored", "Converted Markdown is never saved. Download it or it is gone."),
        ("#7B61FF", "Passwords in Keychain", "PDF passwords live only in macOS Keychain — never in the app database."),
        ("#00CFE8", "Metadata-Only History", "The history log stores filenames and timestamps only. No document content."),
    ]

    cards_html = "".join(
        f'<div style="background:#FFFFFF;border:3px solid #1E1E1E;border-radius:10px;border-left:6px solid {color};box-shadow:3px 3px 0 #1E1E1E;padding:16px 20px;">'
        f'<p style="font-family:\'Archivo Black\',sans-serif;font-size:14px;color:#1E1E1E;margin:0 0 6px 0;">{title}</p>'
        f'<p style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:13px;color:#4A4A4A;margin:0;line-height:1.6;">{desc}</p>'
        f'</div>'
        for color, title, desc in _PRIVACY_ITEMS
    )

    _html = f"""
        <div style="background:#FFFFFF;border:3px solid #1E1E1E;border-radius:12px;box-shadow:5px 5px 0 #1E1E1E;padding:32px;margin-top:24px;">
            <p style="font-family:'Archivo Black',sans-serif;font-size:18px;color:#1E1E1E;margin:0 0 20px 0;">Privacy Principles</p>
            <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;">{cards_html}</div>
        </div>
        """
    st.markdown("\n".join(l for l in _html.splitlines() if l.strip()), unsafe_allow_html=True)
