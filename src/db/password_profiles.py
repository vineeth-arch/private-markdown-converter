from typing import Any


def insert_profile(
    profile_name: str,
    filename_match_pattern: str | None,
    keychain_service_name: str,
    keychain_account_name: str,
) -> int:
    """Insert a password profile and return its new ID."""
    raise NotImplementedError("Password profiles DB not implemented until Phase 4")


def get_all_profiles() -> list[dict[str, Any]]:
    """Return all saved password profiles (metadata only, no passwords)."""
    raise NotImplementedError("Password profiles DB not implemented until Phase 4")


def delete_profile(profile_id: int) -> None:
    """Delete a password profile by ID."""
    raise NotImplementedError("Password profiles DB not implemented until Phase 4")


def update_last_used(profile_id: int) -> None:
    """Update the last_used_at timestamp for a profile."""
    raise NotImplementedError("Password profiles DB not implemented until Phase 4")
