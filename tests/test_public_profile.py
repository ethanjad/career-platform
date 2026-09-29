from fastapi.testclient import TestClient

from app.database import initialize_database, load_public_profile
from app.main import app


def test_public_profile_exposes_all_content_sections(tmp_path):
    profile = load_public_profile(tmp_path / "resume.db")

    assert profile["experience"]
    assert profile["education"]
    assert profile["skills"]
    assert profile["projects"]
    assert profile["links"]
    assert profile["settings"]["site_title"] == "Career Platform"


def test_homepage_renders_every_recruiter_facing_section(monkeypatch, tmp_path):
    database_path = tmp_path / "resume.db"
    initialize_database(database_path)
    monkeypatch.setenv("DATABASE_PATH", str(database_path))

    # The application settings are initialized at import time, so use the
    # profile loader directly to make this test independent of the process DB.
    profile = load_public_profile(database_path)
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert response.status_code == 200
    for section in ("Experience", "Education", "Skills", "Projects", "Let’s connect"):
        assert section in response.text
    assert "Data Analyst Intern" in response.text
    assert "Revenue Trend Dashboard" in response.text


def test_homepage_eyebrow_matches_finance_and_isba_focus(monkeypatch, tmp_path):
    profile = load_public_profile(tmp_path / "resume.db")
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert '<p class="eyebrow">Finance &amp; ISBA</p>' in response.text
