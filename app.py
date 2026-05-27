from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.security.temp_cleanup import cleanup_temp_dir
from src.pages import (
    convert_page,
    history_page,
    password_profiles_page,
    settings_page,
    help_page,
)

load_dotenv()

st.set_page_config(
    page_title="Private Markdown Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_custom_css() -> None:
    css_path = Path("src/styles/theme.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def page_header(title: str, color: str) -> None:
    st.markdown(
        f"""
        <div style="
            background: {color};
            border: 3px solid #1E1E1E;
            border-radius: 12px;
            box-shadow: 5px 5px 0 #1E1E1E;
            padding: 20px 28px;
            margin-bottom: 24px;
        ">
            <h1 style="
                font-family: 'Archivo Black', sans-serif;
                color: white;
                margin: 0;
                font-size: 28px;
                text-shadow: 2px 2px 0 rgba(0,0,0,0.2);
            ">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_custom_css()

if "startup_done" not in st.session_state:
    cleanup_temp_dir()
    st.session_state["startup_done"] = True

NAV_ITEMS = [
    "Convert",
    "History",
    "Password Profiles",
    "Settings",
    "Help",
]

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 16px 0 24px 0;">
            <p style="
                font-family: 'Archivo Black', sans-serif;
                font-size: 18px;
                color: white;
                margin: 0;
                line-height: 1.2;
            ">Private Markdown<br>Converter</p>
            <p style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: #888;
                margin: 6px 0 0 0;
            ">Local · Private · Secure</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected = st.radio(
        "Navigation",
        NAV_ITEMS,
        label_visibility="collapsed",
    )

PAGE_MAP = {
    "Convert": convert_page,
    "History": history_page,
    "Password Profiles": password_profiles_page,
    "Settings": settings_page,
    "Help": help_page,
}

PAGE_MAP[selected].render(page_header)
