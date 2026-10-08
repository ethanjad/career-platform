from typing import Any

from sqlalchemy import delete, insert, update

from .database import CONTENT_TABLES, get_engine, initialize_database, load_public_profile, metadata

EDITABLE_FIELDS = {
    "experience": ("title", "company", "details"),
    "education": ("school", "degree", "field", "details"),
    "skills": ("name", "category"),
    "projects": ("title", "summary"),
    "links": ("label", "url"),
}


def create_experience_record(data: dict[str, Any]) -> dict[str, str]:
    if not data.get("company") or not data.get("title"):
        raise ValueError("company and title are required")
    return {"company": str(data["company"]), "title": str(data["title"]), "details": str(data.get("details", ""))}


def _content_table(name: str):
    if name not in CONTENT_TABLES:
        raise ValueError("unsupported table")
    return metadata.tables[name]


def save_record(table_name: str, data: dict[str, Any], record_id: int | None = None) -> None:
    table = _content_table(table_name)
    initialize_database()
    values = {field: str(data.get(field, "")) for field in EDITABLE_FIELDS[table_name]}
    with get_engine().begin() as connection:
        if record_id:
            connection.execute(update(table).where(table.c.id == record_id).values(**values))
        else:
            connection.execute(insert(table).values(**values))
    load_public_profile()  # refreshes the snapshot


def delete_record(table_name: str, record_id: int) -> None:
    table = _content_table(table_name)
    with get_engine().begin() as connection:
        connection.execute(delete(table).where(table.c.id == record_id))
    load_public_profile()  # refreshes the snapshot
