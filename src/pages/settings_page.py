import os
import streamlit as st


MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))


def render(page_header) -> None:
    """Settings page — app configuration."""
    page_header("SETTINGS", "#00CFE8")
    st.markdown(
        f"""
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
            ">Current Settings</p>
            <table style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 15px;
                color: #1E1E1E;
                border-collapse: collapse;
                width: 100%;
            ">
                <tr>
                    <td style="padding: 8px 16px 8px 0; font-weight: 600;">Max file size</td>
                    <td style="padding: 8px 0; font-family: 'JetBrains Mono', monospace;">{MAX_FILE_SIZE_MB} MB</td>
                </tr>
                <tr>
                    <td style="padding: 8px 16px 8px 0; font-weight: 600;">Storage mode</td>
                    <td style="padding: 8px 0;">Local only — nothing leaves this machine</td>
                </tr>
                <tr>
                    <td style="padding: 8px 16px 8px 0; font-weight: 600;">Password storage</td>
                    <td style="padding: 8px 0;">macOS Keychain (via keyring)</td>
                </tr>
            </table>
            <p style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 13px;
                color: #4A4A4A;
                margin: 16px 0 0 0;
            ">
                To change MAX_FILE_SIZE_MB, edit <code>.env</code> and restart the app.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
