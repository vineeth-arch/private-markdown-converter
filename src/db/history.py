from datetime import date, datetime, time
from typing import Any

from src.db.database import get_connection


def _normalize_range_bound(value: date | datetime, *, end_of_day: bool) -> datetime:
    """Convert date-like inputs into concrete datetime bounds."""
    if isinstance(value, datetime):
        return value
    bound_time = time.max if end_of_day else time.min
    return datetime.combine(value, bound_time)


def add_record(
    filename: str,
    extension: str,
    engine: str,
    status: str,
    output_name: str | None,
    file_size: int | None,
    duration: float | None,
    error_msg: str | None,
) -> None:
    """Insert a metadata-only conversion history record."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversion_history (
                original_file_name,
                original_file_extension,
                file_size_bytes,
                conversion_engine,
                conversion_status,
                output_file_name,
                conversion_duration_seconds,
                error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                extension,
                file_size,
                engine,
                status,
                output_name,
                duration,
                error_msg,
            ),
        )
        connection.commit()


def get_all_records() -> list[dict[str, Any]]:
    """Return all conversion history rows ordered by newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                original_file_name,
                original_file_extension,
                file_size_bytes,
                conversion_engine,
                conversion_status,
                output_file_name,
                conversion_duration_seconds,
                error_message,
                converted_at
            FROM conversion_history
            ORDER BY converted_at DESC, id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def clear_history() -> None:
    """Delete all conversion history records."""
    with get_connection() as connection:
        connection.execute("DELETE FROM conversion_history")
        connection.commit()


def get_records_by_date_range(
    start: date | datetime,
    end: date | datetime,
) -> list[dict[str, Any]]:
    """Return conversion history rows within an inclusive date range."""
    start_bound = _normalize_range_bound(start, end_of_day=False)
    end_bound = _normalize_range_bound(end, end_of_day=True)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                original_file_name,
                original_file_extension,
                file_size_bytes,
                conversion_engine,
                conversion_status,
                output_file_name,
                conversion_duration_seconds,
                error_message,
                converted_at
            FROM conversion_history
            WHERE converted_at BETWEEN ? AND ?
            ORDER BY converted_at DESC, id DESC
            """,
            (
                start_bound.isoformat(sep=" ", timespec="microseconds"),
                end_bound.isoformat(sep=" ", timespec="microseconds"),
            ),
        ).fetchall()
    return [dict(row) for row in rows]
