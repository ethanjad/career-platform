import json
import sqlite3

from fastapi.testclient import TestClient

from app.database import get_profile, initialize_database, load_public_profile
from app.main import app


def test_database_initializes_expected_tables(tmp_path):
    database_path = tmp_path / "resume.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }

    expected_tables = {"profile", "experience", "education", "skills", "projects", "links", "settings"}
    assert expected_tables.issubset(tables)

    profile = get_profile(database_path)
    assert profile["name"]
    assert profile["headline"]


def test_seeded_records_match_business_analytics_student_profile(tmp_path):
    database_path = tmp_path / "resume.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row

        profile = connection.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        experience = connection.execute("SELECT COUNT(*) AS count FROM experience").fetchone()["count"]
        education = connection.execute("SELECT COUNT(*) AS count FROM education").fetchone()["count"]
        skills = connection.execute("SELECT COUNT(*) AS count FROM skills").fetchone()["count"]
        projects = connection.execute("SELECT COUNT(*) AS count FROM projects").fetchone()["count"]
        links = connection.execute("SELECT COUNT(*) AS count FROM links").fetchone()["count"]
        settings = connection.execute("SELECT COUNT(*) AS count FROM settings").fetchone()["count"]

    assert profile["headline"] == "Senior Business Analytics Student"
    assert experience >= 2
    assert education >= 2
    assert skills >= 8
    assert projects >= 2
    assert links >= 3
    assert settings >= 1


def test_profile_falls_back_to_snapshot_when_database_is_unavailable(tmp_path, monkeypatch):
    database_path = tmp_path / "resume.db"
    initialize_database(database_path)

    snapshot_path = database_path.parent / "profile_snapshot.json"
    snapshot_path.write_text(json.dumps({"name": "Alex Carter", "headline": "Senior Business Analytics Student", "summary": "Cached version", "email": "alex.carter@example.com"}), encoding="utf-8")

    def raise_operational_error(*args, **kwargs):
        raise sqlite3.OperationalError("database unavailable")

    monkeypatch.setattr("sqlite3.connect", raise_operational_error)

    profile = load_public_profile(database_path)

    assert profile["name"] == "Alex Carter"
    assert profile["headline"] == "Senior Business Analytics Student"


def test_homepage_renders_cached_profile_when_db_is_down(monkeypatch):
    def raise_operational_error(*args, **kwargs):
        raise sqlite3.OperationalError("database unavailable")

    monkeypatch.setattr("app.database.sqlite3.connect", raise_operational_error)

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "Senior Business Analytics Student" in response.text
    assert "Profile" not in response.text or "Senior Business Analytics Student" in response.text
