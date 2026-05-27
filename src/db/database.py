import sqlite3


def get_connection() -> sqlite3.Connection:
    """Return a WAL-mode SQLite connection to data/app.db."""
    raise NotImplementedError("Database not implemented until Phase 5")
