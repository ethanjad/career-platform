from fastapi.testclient import TestClient

from app.database import initialize_database, load_public_profile
from app.main import app


def test_healthz_reports_ok_when_database_is_reachable():
    initialize_database()

    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    assert response.text == "ok"


def test_healthz_returns_503_when_database_is_down(unreachable_database):
    response = TestClient(app).get("/healthz")

    assert response.status_code == 503


def test_startup_seeds_an_empty_database():
    with TestClient(app) as client:  # `with` runs the lifespan
        response = client.get("/")

    # The built-in default profile has no experience rows, so this only appears if startup seeded the database.
    assert "Data Analyst Intern" in response.text


def test_app_starts_and_serves_snapshot_when_database_is_down_at_boot(monkeypatch):
    initialize_database()
    load_public_profile()  # writes the snapshot
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody@127.0.0.1:1/missing")

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Senior Business Analytics Student" in response.text
