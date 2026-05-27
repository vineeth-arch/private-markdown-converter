def get_password(profile_id: int) -> str:
    """Retrieve a saved password from macOS Keychain for the given profile."""
    raise NotImplementedError("Password vault not implemented until Phase 4")


def save_password(profile_id: int, password: str) -> None:
    """Save a password to macOS Keychain for the given profile."""
    raise NotImplementedError("Password vault not implemented until Phase 4")


def delete_password(profile_id: int) -> None:
    """Remove a saved password from macOS Keychain for the given profile."""
    raise NotImplementedError("Password vault not implemented until Phase 4")
