import keyring


SERVICE_PREFIX = "pmc.password-profile"


def _service_name(profile_id: int | str) -> str:
    return f"{SERVICE_PREFIX}.{profile_id}"


def _account_name(profile_id: int | str) -> str:
    return f"profile-{profile_id}"


def get_password(profile_id: int | str) -> str | None:
    """Retrieve a saved password from the system credential store for a profile."""
    return keyring.get_password(_service_name(profile_id), _account_name(profile_id))


def save_password(profile_id: int | str, password: str) -> None:
    """Save a password to the system credential store for a profile."""
    keyring.set_password(_service_name(profile_id), _account_name(profile_id), password)


def delete_password(profile_id: int | str) -> None:
    """Remove a saved password from the system credential store for a profile."""
    try:
        keyring.delete_password(_service_name(profile_id), _account_name(profile_id))
    except keyring.errors.PasswordDeleteError:
        pass
