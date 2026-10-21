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
    assert "Financial Budgeting Intern" in response.text
    assert "Hoops Recap" in response.text


def test_homepage_hero_renders_headline_as_fact_row(monkeypatch):
    profile = seeded_profile()
    profile["headline"] = "BBA Finance & ISBA · Loyola Marymount University · GPA 3.62"
    profile["experience"][0]["details"] = "Jun 2026 – Present. Budgeting work."
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert 'class="eyebrow"' not in response.text
    assert "<li>Loyola Marymount University</li>" in response.text
    assert "<li>GPA 3.62</li>" in response.text
    assert '<p class="now">' in response.text
    assert "<title>Ethan Jad | BBA Finance &amp; ISBA</title>" in response.text


def test_homepage_hides_current_role_when_none_is_ongoing(monkeypatch):
    profile = seeded_profile()
    for item in profile["experience"]:
        item["details"] = item["details"].replace("Present", "Dec 2026")
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
    assert 'résumé <span class="button-note">PDF</span>' not in client.get("/").text

    pdf.write_bytes(b"%PDF-1.4 test")
    served = client.get("/resume.pdf")
    assert served.status_code == 200
    assert served.headers["content-type"] == "application/pdf"
    assert "Ethan-Jad-Resume.pdf" in served.headers["content-disposition"]
    assert 'résumé <span class="button-note">PDF</span>' in client.get("/").text


def test_empty_sections_are_hidden_instead_of_promising_content(monkeypatch):
    profile = seeded_profile()
    profile["experience"] = []
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert 'id="experience"' not in response.text
    assert 'href="#experience"' not in response.text
    assert "added soon" not in response.text


def test_empty_projects_table_shows_a_deliberate_message(monkeypatch):
    profile = seeded_profile()
    profile["projects"] = []
    monkeypatch.setattr("app.main.get_profile", lambda: profile)

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert 'id="projects"' in response.text
    assert "No projects are listed right now." in response.text
    assert "temporarily unavailable" not in response.text


def test_database_failure_returns_503_with_profile_visible_and_projects_unavailable(monkeypatch):
    profile = seeded_profile()  # a successful read writes the snapshot
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody@127.0.0.1:1/missing")

    response = TestClient(app).get("/")

    assert response.status_code == 503
    assert "Ethan Jad" in response.text
    assert "Financial Budgeting Intern" in response.text
    assert "Projects temporarily unavailable" in response.text
    for project in profile["projects"]:
        assert project["title"] not in response.text


def test_page_recovers_on_next_request_after_database_returns(monkeypatch, database_url):
    initialize_database()
    client = TestClient(app)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody@127.0.0.1:1/missing")
    assert client.get("/").status_code == 503

    monkeypatch.setenv("DATABASE_URL", database_url)
    response = client.get("/")

    assert response.status_code == 200
    assert "Hoops Recap" in response.text
    assert "temporarily unavailable" not in response.text


def test_privacy_page_is_linked_from_the_footer_and_names_google_analytics():
    initialize_database()
    client = TestClient(app)

    assert 'href="http://testserver/privacy"' in client.get("/").text
    response = client.get("/privacy")
    assert response.status_code == 200
    assert "<h1>Privacy</h1>" in response.text
    assert "Google Analytics" in response.text
    assert "_ga_1DG579DN36" in response.text


def test_google_tag_loads_exactly_once_on_every_html_page():
    initialize_database()
    client = TestClient(app)

    for path in ("/", "/privacy"):
        html = client.get(path).text
        assert html.count("googletagmanager.com/gtag/js?id=G-1DG579DN36") == 1, path
        assert html.count("gtag('config', 'G-1DG579DN36')") == 1, path
