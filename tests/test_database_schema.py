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


def test_seeded_records_match_business_analytics_student_profile():
    initialize_database()

    profile = load_public_profile()

    assert profile["headline"] == "Senior Business Analytics Student"
    assert len(profile["experience"]) >= 2
    assert len(profile["education"]) >= 2
    assert len(profile["skills"]) >= 8
    assert len(profile["projects"]) >= 2
    assert len(profile["links"]) >= 3
    assert profile["settings"]["site_title"] == "Career Platform"


def test_profile_falls_back_to_snapshot_when_database_is_unavailable(monkeypatch):
    initialize_database()
    load_public_profile()  # a successful read writes the snapshot
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody@127.0.0.1:1/missing")

    profile = load_public_profile()

    assert profile["name"] == "Alex Carter"
    assert profile["headline"] == "Senior Business Analytics Student"


def test_homepage_renders_cached_profile_when_db_is_down(monkeypatch):
    initialize_database()
    load_public_profile()
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody@127.0.0.1:1/missing")

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Senior Business Analytics Student" in response.text


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

    assert [item["id"] for item in profile["experience"]] == [2]


def test_admin_insert_on_seeded_database_gets_next_id():
    initialize_database()

    save_record("experience", {"title": "Analyst", "company": "Acme", "details": "Did things."})

    assert [item["id"] for item in load_public_profile()["experience"]] == [1, 2, 3]
