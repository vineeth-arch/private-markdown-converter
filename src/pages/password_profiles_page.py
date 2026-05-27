import streamlit as st


def render(page_header) -> None:
    """Password Profiles page — saved PDF password profiles (Phase 4)."""
    page_header("PASSWORD PROFILES", "#7B61FF")
    st.markdown(
        """
        <div style="
            background: #FFFFFF;
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 32px;
            text-align: center;
            margin-top: 24px;
        ">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 20px;
                color: #1E1E1E;
                margin: 0 0 12px 0;
            ">🔑 Coming in Phase 4</p>
            <p style="
                font-family: 'Plus Jakarta Sans', sans-serif;
                font-size: 15px;
                color: #4A4A4A;
                margin: 0;
            ">
                Save PDF passwords securely in macOS Keychain.<br>
                Create profiles matched by filename pattern — e.g. <code>*HDFC*statement*</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
