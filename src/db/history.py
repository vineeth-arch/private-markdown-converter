from typing import Any


def insert_conversion(
    original_file_name: str,
    original_file_extension: str,
    file_size_bytes: int,
    conversion_engine: str,
    conversion_status: str,
    output_file_name: str | None,
    conversion_duration_seconds: float | None,
    error_message: str | None,
) -> None:
    """Insert a conversion event into the history table."""
    raise NotImplementedError("History DB not implemented until Phase 5")


def get_history(limit: int = 100) -> list[dict[str, Any]]:
    """Return recent conversion history records."""
    raise NotImplementedError("History DB not implemented until Phase 5")


def clear_history() -> None:
    """Delete all conversion history records."""
    raise NotImplementedError("History DB not implemented until Phase 5")
