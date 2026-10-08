from fastapi.testclient import TestClient

from app.database import initialize_database, load_public_profile
from app.main import app


def seeded_profile():
    initialize_database()
    return load_public_profile()


def test_public_profile_exposes_all_content_sections():
    profile = seeded_profile()

    assert profile["experience"]
    assert profile["education"]
    assert profile["skills"]
    assert profile["projects"]
    assert profile["links"]
    assert profile["settings"]["site_title"] == "Career Platform"


def test_homepage_renders_every_recruiter_facing_section():
    initialize_database()

    response = TestClient(app).get("/")

    assert response.status_code == 200
    for section in ("Experience", "Education", "Skills", "Projects", 'id="contact"'):
        assert section in response.text
    assert "Data Analyst Intern" in response.text
    assert "Revenue Trend Dashboard" in response.text


def test_homepage_hero_renders_headline_as_fact_row(monkeypatch):
    profile = seeded_profile()
    profile["headline"] = "BBA Finance & ISBA · Loyola Marymount University · GPA 3.62"
    profile["experience"][0]["details"] = "Jun 2026 – Present. Budgeting work."
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert 'class="eyebrow"' not in response.text
    assert "<li>Loyola Marymount University</li>" in response.text
    assert "<li>GPA 3.62</li>" in response.text
    assert '<span class="now-label">Currently</span>' in response.text
    assert "<title>Alex Carter | BBA Finance &amp; ISBA</title>" in response.text


def test_homepage_hides_current_role_when_none_is_ongoing(monkeypatch):
    profile = seeded_profile()
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert 'class="now"' not in response.text


def test_split_dates_pulls_leading_range_out_of_details():
    from app.main import split_dates

    assert split_dates("Jun 2026 – Present. Budgeting work.") == ("Jun 2026 – Present", "Budgeting work.")
    assert split_dates("Aug 2025 – Dec 2025. One. Two.") == ("Aug 2025 – Dec 2025", "One. Two.")
    assert split_dates("Built SQL dashboards.") == ("", "Built SQL dashboards.")


def _use_resume_pdf(monkeypatch, path):
    import dataclasses
    import app.main

    monkeypatch.setattr("app.main.settings", dataclasses.replace(app.main.settings, resume_pdf_path=path))


def test_resume_button_and_route_appear_only_when_pdf_exists(monkeypatch, tmp_path):
    profile = seeded_profile()
    monkeypatch.setattr("app.main.get_profile", lambda: profile)
    pdf = tmp_path / "resume.pdf"
    _use_resume_pdf(monkeypatch, pdf)
    client = TestClient(app)

    missing = client.get("/resume.pdf")
    assert missing.status_code == 404
    assert profile["email"] in missing.text
    assert "Download résumé" not in client.get("/").text

    pdf.write_bytes(b"%PDF-1.4 test")
    served = client.get("/resume.pdf")
    assert served.status_code == 200
    assert served.headers["content-type"] == "application/pdf"
    assert "Alex-Carter-Resume.pdf" in served.headers["content-disposition"]
    assert "Download résumé" in client.get("/").text


def test_empty_sections_are_hidden_instead_of_promising_content(monkeypatch):
    profile = seeded_profile()
    profile["projects"] = []
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert 'id="projects"' not in response.text
    assert 'href="#projects"' not in response.text
    assert "added soon" not in response.text
