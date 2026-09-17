import sqlite3
from pathlib import Path

from .config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    email TEXT NOT NULL
);
"""

def initialize_database(database_path: Path | None = None) -> None:
    path = database_path or get_settings().database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT OR IGNORE INTO profile (id, name, headline, summary, email) "
            "VALUES (1, ?, ?, ?, ?)",
            ("Your Name", "Business Analytics Professional",
             "A concise resume and portfolio for future opportunities.", "you@example.com"),
        )

def get_profile(database_path: Path | None = None) -> dict[str, str]:
    path = database_path or get_settings().database_path
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        raise RuntimeError("The resume profile is not initialized")
    return dict(row)
