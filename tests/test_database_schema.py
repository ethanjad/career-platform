from fastapi.testclient import TestClient
from sqlalchemy import delete, func, inspect, select

from app.admin import save_record
from app.database import CONTENT_TABLES, get_engine, initialize_database, load_public_profile, metadata
from app.main import app


def _row_counts():
    with get_engine().connect() as connection:
        return {
            name: connection.execute(select(func.count()).select_from(metadata.tables[name])).scalar_one()
            for name in CONTENT_TABLES
        }


def test_database_initializes_expected_tables():
    initialize_database()

    expected_tables = {"profile", "experience", "education", "skills", "projects", "links", "settings"}
    assert expected_tables.issubset(inspect(get_engine()).get_table_names())

    profile = load_public_profile()
    assert profile["name"]
    assert profile["headline"]


def test_seeded_records_are_the_real_public_profile():
    initialize_database()

    profile = load_public_profile()

    assert profile["name"] == "Ethan Jad"
    assert profile["email"] == "ethanjad@gmail.com"
    assert len(profile["experience"]) == 4
    assert len(profile["education"]) == 2
    assert len(profile["skills"]) == 4
    assert len(profile["projects"]) == 6
    assert [link["label"] for link in profile["links"]] == ["LinkedIn", "GitHub"]
    assert profile["settings"]["site_title"] == "Career Platform"


def test_profile_falls_back_to_snapshot_when_database_is_unavailable(monkeypatch):
    initialize_database()
    load_public_profile()  # a successful read writes the snapshot
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody@127.0.0.1:1/missing")

    profile = load_public_profile()

    assert profile["name"] == "Ethan Jad"
    assert profile["experience"]
    assert profile["database_available"] is False


def test_no_invented_placeholder_content_in_defaults_or_tracked_snapshot():
    from app.config import ROOT_DIR
    from app.database import DEFAULT_PUBLIC_PROFILE, SEED_ROWS

    tracked_snapshot = (ROOT_DIR / "data" / "profile_snapshot.json").read_text(encoding="utf-8")
    for source in (repr(DEFAULT_PUBLIC_PROFILE), repr(SEED_ROWS), tracked_snapshot):
        for invented in ("Alex Carter", "Northwind", "Civic Insights", "Rensselaer", "example.com"):
            assert invented not in source


def test_reinitializing_database_does_not_duplicate_seed_rows():
    initialize_database()
    first_counts = _row_counts()

    initialize_database()

    assert _row_counts() == first_counts


def test_deleted_seed_record_is_not_restored_on_next_load():
    initialize_database()
    experience = metadata.tables["experience"]
    with get_engine().begin() as connection:
        connection.execute(delete(experience).where(experience.c.id == 1))
    initialize_database()

    profile = load_public_profile()

    assert [item["id"] for item in profile["experience"]] == [2, 3, 4]


def test_admin_insert_on_seeded_database_gets_next_id():
    initialize_database()

    save_record("experience", {"title": "Analyst", "company": "Acme", "details": "Did things."})

    assert [item["id"] for item in load_public_profile()["experience"]] == [1, 2, 3, 4, 5]
