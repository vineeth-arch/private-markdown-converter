from pathlib import Path
import sqlite3


DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "app.db"

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS conversion_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_file_name TEXT NOT NULL,
        original_file_extension TEXT NOT NULL,
        file_size_bytes INTEGER,
        conversion_engine TEXT NOT NULL,
        conversion_status TEXT NOT NULL,
        output_file_name TEXT,
        conversion_duration_seconds REAL,
        error_message TEXT,
        converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS password_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_name TEXT NOT NULL UNIQUE,
        filename_match_pattern TEXT,
        keychain_service_name TEXT NOT NULL,
        keychain_account_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP
    )
    """,
)


def _initialize_database(connection: sqlite3.Connection) -> None:
    """Enable WAL mode and create required tables when missing."""
    connection.execute("PRAGMA journal_mode=WAL")
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    connection.commit()


def get_connection() -> sqlite3.Connection:
    """Return a WAL-mode SQLite connection to data/app.db."""
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    _initialize_database(connection)
    return connection


def init_database() -> None:
    """Create the application database and required tables when missing."""
    with get_connection() as connection:
        connection.execute("SELECT 1")
