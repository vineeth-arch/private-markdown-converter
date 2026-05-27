import streamlit as st


SUPPORTED_FILE_TYPES = [
    ("PDF", ".pdf", "Encrypted PDFs supported with password profiles"),
    ("Word", ".docx", "Microsoft Word documents"),
    ("PowerPoint", ".pptx", "Microsoft PowerPoint presentations"),
    ("Excel", ".xlsx", "Microsoft Excel spreadsheets"),
    ("HTML", ".html / .htm", "Web pages"),
    ("CSV", ".csv", "Comma-separated values"),
    ("JSON", ".json", "JSON data files"),
    ("XML", ".xml", "XML documents"),
    ("EPUB", ".epub", "E-book format"),
    ("Images", ".jpg / .jpeg / .png / .gif / .bmp / .webp", "Image files"),
    ("ZIP", ".zip", "Archives (contents converted individually)"),
]


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
    for i, (name, ext, note) in enumerate(SUPPORTED_FILE_TYPES):
        bg = "#FFFFFF" if i % 2 == 0 else "#FFF8F0"
        rows_html += f"""
        <tr style="background: {bg}; border-bottom: 2px solid #1E1E1E;">
            <td style="padding: 10px 16px; font-family: 'Archivo Black', sans-serif; font-size: 14px;">{name}</td>
            <td style="padding: 10px 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #7B61FF;">{ext}</td>
            <td style="padding: 10px 16px; font-family: 'Plus Jakarta Sans', sans-serif; font-size: 14px; color: #4A4A4A;">{note}</td>
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
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
                margin: 0 0 16px 0;
            ">Privacy Principles</p>
            <ul style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 15px; color: #4A4A4A; margin: 0; padding-left: 20px; line-height: 1.8;">
                <li>No documents are uploaded to the cloud. Everything stays on your machine.</li>
                <li>Uploaded files are processed in memory and deleted from <code>temp/</code> immediately after conversion.</li>
                <li>Converted Markdown is never stored. Download it or it is gone.</li>
                <li>PDF passwords are stored only in macOS Keychain — never in the app database.</li>
                <li>The history log contains filenames and timestamps only. No document content.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
