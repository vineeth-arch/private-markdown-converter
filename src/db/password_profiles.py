from fnmatch import fnmatch
from typing import Any

from src.db.database import get_connection


def _row_to_dict(row) -> dict[str, Any]:
    return dict(row)


def insert_profile(
    profile_name: str,
    filename_match_pattern: str | None,
    keychain_service_name: str,
    keychain_account_name: str,
) -> int:
    """Insert a password profile and return its new ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO password_profiles (
                profile_name,
                filename_match_pattern,
                keychain_service_name,
                keychain_account_name
            ) VALUES (?, ?, ?, ?)
            """,
            (
                profile_name,
                filename_match_pattern,
                keychain_service_name,
                keychain_account_name,
            ),
        )
        profile_id = int(cursor.lastrowid)
        connection.execute(
            """
            UPDATE password_profiles
            SET keychain_service_name = ?, keychain_account_name = ?
            WHERE id = ?
            """,
            (
                f"pmc.password-profile.{profile_id}",
                f"profile-{profile_id}",
                profile_id,
            ),
        )
        connection.commit()
        return profile_id


def get_all_profiles() -> list[dict[str, Any]]:
    """Return all saved password profiles (metadata only, no passwords)."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                profile_name,
                filename_match_pattern,
                keychain_service_name,
                keychain_account_name,
                created_at,
                last_used_at
            FROM password_profiles
            ORDER BY profile_name COLLATE NOCASE ASC, id ASC
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_profile(profile_id: int) -> dict[str, Any] | None:
    """Return one password profile by ID."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                profile_name,
                filename_match_pattern,
                keychain_service_name,
                keychain_account_name,
                created_at,
                last_used_at
            FROM password_profiles
            WHERE id = ?
            """,
            (profile_id,),
        ).fetchone()
    return None if row is None else _row_to_dict(row)


def update_profile(profile_id: int, profile_name: str, filename_match_pattern: str | None) -> None:
    """Update a password profile's name and filename pattern."""
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE password_profiles
            SET profile_name = ?, filename_match_pattern = ?
            WHERE id = ?
            """,
            (profile_name, filename_match_pattern, profile_id),
        )
        connection.commit()


def delete_profile(profile_id: int) -> None:
    """Delete a password profile by ID."""
    with get_connection() as connection:
        connection.execute("DELETE FROM password_profiles WHERE id = ?", (profile_id,))
        connection.commit()


def update_last_used(profile_id: int) -> None:
    """Update the last_used_at timestamp for a profile."""
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE password_profiles
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (profile_id,),
        )
        connection.commit()


def get_matching_profiles(filename: str) -> list[dict[str, Any]]:
    """Return profiles whose glob pattern matches the provided filename."""
    matches = [
        profile
        for profile in get_all_profiles()
        if profile["filename_match_pattern"]
        and fnmatch(filename, profile["filename_match_pattern"])
    ]
    matches.sort(
        key=lambda profile: (
            profile["last_used_at"] is not None,
            profile["last_used_at"] or profile["created_at"] or "",
            profile["id"],
        ),
        reverse=True,
    )
    return matches
