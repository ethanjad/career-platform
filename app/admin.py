import sqlite3
from typing import Any

from .config import get_settings
from .database import initialize_database, load_public_profile, write_profile_snapshot

TABLES = {"experience", "education", "skills", "projects", "links"}


def create_experience_record(data: dict[str, Any]) -> dict[str, str]:
    if not data.get("company") or not data.get("title"):
        raise ValueError("company and title are required")
    return {"company": str(data["company"]), "title": str(data["title"]), "details": str(data.get("details", ""))}


def save_record(table: str, data: dict[str, Any], record_id: int | None = None) -> None:
    if table not in TABLES:
        raise ValueError("unsupported table")
    path = get_settings().database_path
    initialize_database(path)
    allowed = {
        "experience": ("title", "company", "details"),
        "education": ("school", "degree", "field", "details"),
        "skills": ("name", "category"),
        "projects": ("title", "summary"),
        "links": ("label", "url"),
    }[table]
    values = [str(data.get(field, "")) for field in allowed]
    with sqlite3.connect(path) as connection:
        if record_id:
            assignments = ", ".join(f"{field} = ?" for field in allowed)
            connection.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", (*values, record_id))
        else:
            fields = ", ".join(allowed)
            placeholders = ", ".join("?" for _ in allowed)
            connection.execute(f"INSERT INTO {table} ({fields}) VALUES ({placeholders})", values)
    write_profile_snapshot(load_public_profile(path), path)


def delete_record(table: str, record_id: int) -> None:
    if table not in TABLES:
        raise ValueError("unsupported table")
    path = get_settings().database_path
    with sqlite3.connect(path) as connection:
        connection.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    write_profile_snapshot(load_public_profile(path), path)
