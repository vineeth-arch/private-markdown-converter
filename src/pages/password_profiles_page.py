import sqlite3
from datetime import datetime

import streamlit as st

from src.db.password_profiles import (
    delete_profile,
    get_all_profiles,
    update_profile,
    insert_profile,
)
from src.security.password_vault import delete_password, save_password


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "Never"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def _normalize_pattern(value: str) -> str | None:
    pattern = value.strip()
    return pattern or None


def _create_profile(profile_name: str, filename_match_pattern: str, password: str) -> None:
    normalized_name = profile_name.strip()
    normalized_pattern = _normalize_pattern(filename_match_pattern)
    profile_id: int | None = None
    if not normalized_name:
        st.error("Profile name is required.")
        return
    if not password:
        st.error("Password is required.")
        return

    try:
        profile_id = insert_profile(
            normalized_name,
            normalized_pattern,
            "pending",
            "pending",
        )
        save_password(profile_id, password)
    except sqlite3.IntegrityError:
        st.error("A profile with that name already exists.")
        return
    except Exception:
        try:
            if profile_id is not None:
                delete_profile(profile_id)
        except Exception:
            pass
        st.error("Could not save that password in the secure credential store.")
        return

    st.success("Password profile created.")


def _update_profile(profile: dict, profile_name: str, filename_match_pattern: str, password: str) -> None:
    normalized_name = profile_name.strip()
    normalized_pattern = _normalize_pattern(filename_match_pattern)
    if not normalized_name:
        st.error("Profile name is required.")
        return

    try:
        update_profile(profile["id"], normalized_name, normalized_pattern)
        if password:
            save_password(profile["id"], password)
    except sqlite3.IntegrityError:
        st.error("A profile with that name already exists.")
        return
    except Exception:
        st.error("Could not update the password in the secure credential store.")
        return

    st.success("Password profile updated.")


def _delete_profile(profile: dict) -> None:
    delete_password(profile["id"])
    delete_profile(profile["id"])
    st.success(f"Deleted profile '{profile['profile_name']}'.")


def render(page_header) -> None:
    """Password Profiles page — saved PDF password profiles."""
    page_header("PASSWORD PROFILES", "#7B61FF")

    st.info(
        "Saved passwords are stored in your system's secure credential store "
        "(Keychain on macOS, Credential Manager on Windows), not inside the app database."
    )

    with st.form("create_password_profile", clear_on_submit=True):
        st.subheader("Create New Profile")
        new_name = st.text_input("Profile name")
        new_pattern = st.text_input("Filename pattern (optional)", placeholder="*HDFC*statement*")
        new_password = st.text_input("Password", type="password", autocomplete="off")
        create_submitted = st.form_submit_button("CREATE PROFILE", use_container_width=True)

    if create_submitted:
        _create_profile(new_name, new_pattern, new_password)

    profiles = get_all_profiles()

    if not profiles:
        st.markdown(
            """
            <div style="
                background: #FFFFFF;
                border: 3px solid #1E1E1E;
                border-radius: 12px;
                box-shadow: 5px 5px 0 #1E1E1E;
                padding: 24px;
                margin-top: 16px;
            ">
                <p style="
                    font-family: 'Plus Jakarta Sans', sans-serif;
                    font-size: 15px;
                    color: #4A4A4A;
                    margin: 0;
                ">
                    No saved profiles yet. Create one above to auto-fill encrypted PDF passwords by filename pattern.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.subheader("Saved Profiles")
    for profile in profiles:
        pattern = profile["filename_match_pattern"] or "No pattern"
        created_at = _format_timestamp(profile["created_at"])
        last_used_at = _format_timestamp(profile["last_used_at"])

        with st.expander(profile["profile_name"], expanded=False):
            st.markdown(
                f"""
                <div style="
                    background: #FFF8F0;
                    border: 3px solid #1E1E1E;
                    border-radius: 12px;
                    box-shadow: 5px 5px 0 #1E1E1E;
                    padding: 18px 20px;
                    margin-bottom: 16px;
                ">
                    <p style="margin: 0 0 8px 0;"><strong>Pattern:</strong> <code>{pattern}</code></p>
                    <p style="margin: 0 0 8px 0;"><strong>Created:</strong> {created_at}</p>
                    <p style="margin: 0;"><strong>Last used:</strong> {last_used_at}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form(f"edit_profile_{profile['id']}"):
                updated_name = st.text_input("Profile name", value=profile["profile_name"])
                updated_pattern = st.text_input(
                    "Filename pattern (optional)",
                    value=profile["filename_match_pattern"] or "",
                    placeholder="*HDFC*statement*",
                )
                updated_password = st.text_input(
                    "Replace password (optional)",
                    type="password",
                    autocomplete="off",
                )
                updated = st.form_submit_button("SAVE CHANGES", use_container_width=True)

            if updated:
                _update_profile(profile, updated_name, updated_pattern, updated_password)
                st.rerun()

            if st.button(
                f"DELETE PROFILE: {profile['profile_name']}",
                key=f"delete_profile_{profile['id']}",
                use_container_width=True,
            ):
                _delete_profile(profile)
                st.rerun()
