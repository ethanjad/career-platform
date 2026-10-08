# Railway + PostgreSQL Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the career-platform app onto Railway PostgreSQL. The web service in the existing Railway project reads and writes all résumé data in the project's Postgres database, the VM's live data is moved there, and https://ethanjad.me is served from Railway. The Azure VM and its SQLite file stay untouched as the fallback until the move is verified.

**Architecture:** Railway Postgres becomes the app's production database. Replace the raw `sqlite3` calls in `app/database.py` and `app/admin.py` with SQLAlchemy Core, so the app talks to Postgres through `DATABASE_URL`. SQLite is kept only as the source the data is copied from, for local development, and for the default test run. A one-off `scripts/copy_database.py` copies the VM's live rows into Railway Postgres, keeping their ids, and then resets the id sequences. The web service deploys from GitHub with `railway.json`. Its `/healthz` check fails when the database is unreachable, so Railway does not switch traffic to a deploy that cannot reach Postgres. DNS at Cloudflare is switched last, and putting the old A record back undoes the switch.

**Tech Stack:** Python 3.12, FastAPI, Jinja2, uvicorn, SQLAlchemy 2 (Core), psycopg 3, PostgreSQL 18 (Railway), Railpack builder, uv, Cloudflare DNS.

**Spec:** No separate spec. This plan is based on the 2026-10-08 request ("move the app to Railway and PostgreSQL; the Railway project already exists with Postgres and a web service") and the findings below.

## Findings from inspecting the app (2026-10-08)

1. **The live data is on the VM, not the laptop.** VM `~/career-platform/data/resume.db` (last written 2026-10-08) holds Ethan's real profile: 1 profile, 4 experience, 2 education, 4 skills, 2 projects, 1 link. The laptop's `~/Desktop/github/resume.db` is older (its headline predates the Class of 2027 edit), and `career-platform/data/` holds only the demo snapshot. **Migrate from the VM copy.**
2. **Railway Postgres is reachable and empty.** It runs PostgreSQL 18.6 and has no tables in `public`. `career-platform/.env` holds `RAILWAY_DATABASE_URL`, the public proxy URL. The app does not read that file. It is used only for laptop-side steps.
3. **The database code is tied to SQLite.** It uses `sqlite3.connect`, `?` placeholders, `INSERT OR IGNORE`, `AUTOINCREMENT` and `sqlite_master`, in `app/database.py`, `app/admin.py` and `tests/test_database_schema.py`.
4. **The seed data inserts explicit ids** (`experience` ids 1 and 2, `education` ids 1 and 2). On Postgres that leaves the id sequence at 1, so the first admin insert fails with a duplicate key. The same happens to rows copied in with their ids.
5. **`load_public_profile` runs `initialize_database` on every request.** On Postgres that means about 8 catalog queries per page view. This plan moves it to app startup.
6. **The résumé PDF is git-ignored** (`*.pdf`) and was copied to the VM by hand (`data/resume.pdf`, 80,786 bytes, the same file as `Ethan Jad - Resume (web-safe).pdf`). A Railway container has no hand-placed files. See Decision D1.
7. **The fallback snapshot is written to `data/profile_snapshot.json`.** A Railway container's disk is wiped on every deploy, so the snapshot exists only after the new container's first successful read. The `/healthz` check (Task 3) makes the database read before traffic switches.
8. **`url_for` builds absolute URLs.** Behind Railway's proxy, uvicorn sees plain HTTP from a non-local address. Unless proxy headers are trusted, the CSS and font links come out as `http://…` and the browser blocks them on the HTTPS page.
9. **DNS is on Cloudflare** (`kristin`/`scott.ns.cloudflare.com`). `ethanjad.me` is an A record pointing at the VM. Cloudflare flattens a CNAME at the apex, so Railway's CNAME target works for the bare domain.
10. **Current state:** 14 tests pass. The laptop venv is Python 3.14 and the VM runs 3.12. The `railway` CLI and `psql` are not installed. The VM runs uvicorn under systemd with `--env-file .env` (`DATABASE_PATH`, `ADMIN_SECRET`, `ENABLE_FALLBACK`, `HOST`, `PORT`).

## Decisions (confirm before Task 3)

- **D1 — Résumé PDF on Railway.** Recommended: commit the web-safe PDF as `data/resume.pdf` and add a `!data/resume.pdf` exception to `.gitignore`. Anyone can already download it at `/resume.pdf`, so committing it exposes nothing new, and every deploy then has it. The alternative is a Railway volume mounted at `/app/data`. That needs a manual upload with `railway ssh`, and a service with a volume has a short gap in service on each deploy.
- **D2 — Admin secret.** Recommended: generate a new `ADMIN_SECRET` for Railway with `openssl rand -hex 32`, keep it in a password manager, and stop using the VM's secret once the VM is retired.
- **D3 — Tests stay on SQLite by default.** The full suite also runs against Postgres when `TEST_DATABASE_URL` is set. It uses a throwaway `railway_test` database on the same Railway instance, never the `railway` database.

## Global Constraints

- The repo is **public**. Never commit IP addresses, passwords, `ADMIN_SECRET`, or any `DATABASE_URL` value. Use the placeholders `<VM_PUBLIC_IP>`, `<RAILWAY_DOMAIN>` and `<web-service>` in docs.
- Python: `requires-python = ">=3.12"`. Railway runs 3.12, pinned by `.python-version`.
- New dependencies: `sqlalchemy>=2.0,<3.0` and `psycopg[binary]>=3.2,<4.0`. Add each one to **both** `pyproject.toml`/`uv.lock` (via `uv add`) and `requirements.txt`.
- The app reads `DATABASE_URL`. When it is unset, the app uses SQLite at `DATABASE_PATH`, as today, so the VM keeps working unchanged.
- Railway's `postgresql://…` and `postgres://…` URLs must be rewritten to `postgresql+psycopg://…`.
- On Railway, `DATABASE_URL` is the reference variable `${{Postgres.DATABASE_URL}}`, which uses the private network. The public proxy URL is used only from the laptop.
- **Do not stop, deallocate, delete, or change the Azure VM `vm-career-platform`** in this plan, and don't turn on auto-shutdown. Retiring it is a separate step after the user confirms that Railway works.
- Don't make admin edits on the VM after the export in Task 6. Any such edit would be lost.
- `docs/how-this-site-is-secured.md` is in the user's own words. Don't rewrite it. List what is out of date (Task 8) and let the user update it.
- Work on branch `railway-postgres`. Commit after each task. Push and merge to `main` only with the user's go-ahead (Task 5).

## Review Focus

1. **Railway's URL scheme.** `DATABASE_URL=postgresql://…` must load psycopg 3, not crash looking for psycopg2. Tested in Task 1.
2. **Id sequences after copying or seeding.** After rows are copied with explicit ids, or after a fresh seed, an admin insert must get `max(id)+1` and must not raise a duplicate-key error. Tested in Tasks 2 and 4, and against real Postgres in Task 5.
3. **Database down at startup or at request time.** The app must still start, `/` must serve the snapshot with status 200, and `/healthz` must return 503. Tested in Task 3.
4. **Asset URLs behind the proxy.** On the Railway domain, the stylesheet, font and PDF links must be `https://`. Checked with curl in Task 6, because TestClient does not run uvicorn's proxy-header handling.
5. **Running the copy twice.** Copying into a database that already has data must refuse unless `--replace` is passed, and must never merge or duplicate rows. Tested in Task 4.

---

### Task 0: Branch

- [ ] **Step 1: Create the branch**

```bash
cd ~/Desktop/github/career-platform
git switch -c railway-postgres
```

- [ ] **Step 2: Confirm the baseline**

Run: `.venv/bin/pytest -q`
Expected: `14 passed`

---

### Task 1: Config understands `DATABASE_URL`, plus new dependencies

**Files:**
- Modify: `app/config.py`
- Modify: `pyproject.toml`, `uv.lock` (via `uv add`), `requirements.txt`
- Create: `.python-version`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `normalize_database_url(url: str) -> str`; `Settings.database_url: str` (always a SQLAlchemy URL); `Settings.snapshot_path: Path`.

- [ ] **Step 1: Add dependencies and pin Python**

```bash
echo "3.12" > .python-version
uv add 'sqlalchemy>=2.0,<3.0' 'psycopg[binary]>=3.2,<4.0'
printf 'psycopg[binary]>=3.2,<4.0\nsqlalchemy>=2.0,<3.0\n' >> requirements.txt
uv sync
```

`uv sync` rebuilds `.venv` on Python 3.12, which matches Railway and the VM. From here on, run tests with `uv run pytest`.

- [ ] **Step 2: Write the failing tests** — create `tests/test_config.py`:

```python
from app.config import ROOT_DIR, get_settings, normalize_database_url


def test_railway_postgres_url_uses_psycopg_driver():
    assert (
        normalize_database_url("postgresql://u:p@host:5432/railway")
        == "postgresql+psycopg://u:p@host:5432/railway"
    )


def test_legacy_postgres_scheme_uses_psycopg_driver():
    assert normalize_database_url("postgres://u:p@host/db") == "postgresql+psycopg://u:p@host/db"


def test_other_urls_pass_through_unchanged():
    assert normalize_database_url("sqlite:///x.db") == "sqlite:///x.db"


def test_database_url_env_is_normalized(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host:5432/railway")

    assert get_settings().database_url == "postgresql+psycopg://u:p@host:5432/railway"


def test_sqlite_path_is_used_when_database_url_is_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_PATH", "data/other.db")

    assert get_settings().database_url == f"sqlite:///{ROOT_DIR / 'data' / 'other.db'}"


def test_snapshot_path_defaults_to_data_dir_and_can_be_overridden(monkeypatch):
    monkeypatch.delenv("SNAPSHOT_PATH", raising=False)
    assert get_settings().snapshot_path == ROOT_DIR / "data" / "profile_snapshot.json"

    monkeypatch.setenv("SNAPSHOT_PATH", "/tmp/snap.json")
    assert str(get_settings().snapshot_path) == "/tmp/snap.json"
```

- [ ] **Step 3: Run to verify they fail**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `ImportError: cannot import name 'normalize_database_url'`

- [ ] **Step 4: Implement** — replace `app/config.py` with:

```python
from dataclasses import dataclass
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    app_name: str = "Career Platform"
    database_path: Path = ROOT_DIR / "data" / "resume.db"
    # SQLAlchemy URL. DATABASE_URL when set (Railway Postgres), else SQLite at database_path.
    database_url: str = ""
    snapshot_path: Path = ROOT_DIR / "data" / "profile_snapshot.json"
    # Public résumé PDF. Must be the web-safe export (no phone or street address).
    resume_pdf_path: Path = ROOT_DIR / "data" / "resume.pdf"
    templates_dir: Path = ROOT_DIR / "templates"
    static_dir: Path = ROOT_DIR / "static"
    admin_secret: str = "change-me"
    enable_fallback: bool = True
    host: str = "127.0.0.1"
    port: int = 8000


def normalize_database_url(url: str) -> str:
    """Point Railway's postgres URLs at the psycopg 3 driver SQLAlchemy would not pick by default."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def _path_from_env(name: str, default: Path) -> Path:
    path = Path(os.getenv(name, str(default)))
    return path if path.is_absolute() else ROOT_DIR / path


def get_settings() -> Settings:
    database_path = _path_from_env("DATABASE_PATH", Settings.database_path)
    database_url = os.getenv("DATABASE_URL")
    return Settings(
        database_path=database_path,
        database_url=normalize_database_url(database_url) if database_url else f"sqlite:///{database_path}",
        snapshot_path=_path_from_env("SNAPSHOT_PATH", Settings.snapshot_path),
        resume_pdf_path=_path_from_env("RESUME_PDF_PATH", Settings.resume_pdf_path),
        admin_secret=os.getenv("ADMIN_SECRET", "change-me"),
        enable_fallback=os.getenv("ENABLE_FALLBACK", "true").lower() not in {"0", "false", "no"},
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
    )
```

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: `20 passed` (14 old + 6 new). Nothing else uses the new fields yet.

- [ ] **Step 6: Commit**

```bash
git add app/config.py tests/test_config.py pyproject.toml uv.lock requirements.txt .python-version
git commit -m "feat: read DATABASE_URL and normalize Railway postgres URLs"
```

---

### Task 2: Database layer on SQLAlchemy Core

**Files:**
- Modify: `app/database.py` (full rewrite below)
- Modify: `app/admin.py` (full rewrite below)
- Create: `tests/conftest.py`
- Modify: `tests/test_database_schema.py`, `tests/test_public_profile.py` (full rewrites below)

**Interfaces:**
- Consumes: `get_settings().database_url`, `get_settings().snapshot_path`, `normalize_database_url` (Task 1).
- Produces:
  - `metadata: MetaData` holding tables `profile, experience, education, skills, projects, links, settings`
  - `CONTENT_TABLES: tuple[str, ...]` = `("experience", "education", "skills", "projects", "links")`
  - `engine_for(url: str) -> Engine` (cached per URL), `get_engine() -> Engine`
  - `initialize_database() -> None`, `load_public_profile() -> dict`, `get_profile() -> dict`
  - `read_profile_snapshot() -> dict`, `write_profile_snapshot(profile: dict) -> dict`
  - None of these take a path argument any more. They read `DATABASE_URL` and `SNAPSHOT_PATH` through `get_settings()`.
  - Test fixtures: `database_url` (autouse; yields the isolated URL) and `unreachable_database` (points `DATABASE_URL` at a closed port).

- [ ] **Step 1: Create `tests/conftest.py`**

```python
import os

import pytest

from app import database
from app.config import normalize_database_url

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://nobody@127.0.0.1:1/missing"


@pytest.fixture(autouse=True)
def database_url(tmp_path, monkeypatch):
    """Give every test an empty database and its own snapshot file, never the real ones."""
    if TEST_DATABASE_URL:
        url = normalize_database_url(TEST_DATABASE_URL)
        if "test" not in url.rsplit("/", 1)[-1]:
            pytest.exit("TEST_DATABASE_URL must name a database containing 'test'; refusing to wipe it")
    else:
        url = f"sqlite:///{tmp_path / 'resume.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SNAPSHOT_PATH", str(tmp_path / "profile_snapshot.json"))
    database.metadata.drop_all(database.engine_for(url))
    yield url


@pytest.fixture
def unreachable_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DATABASE_URL)
```

- [ ] **Step 2: Rewrite `tests/test_database_schema.py`**

```python
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
```

- [ ] **Step 3: Rewrite `tests/test_public_profile.py`**

Only the profile setup changes: `load_public_profile(tmp_path / "resume.db")` becomes `seeded_profile()`. The assertions are the same as before.

```python
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
```

- [ ] **Step 4: Run to verify they fail**

Run: `uv run pytest -q`
Expected: collection errors such as `ImportError: cannot import name 'CONTENT_TABLES'` / `'metadata'`.

- [ ] **Step 5: Rewrite `app/database.py`**

```python
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import CheckConstraint, Column, Engine, Integer, MetaData, Table, Text, create_engine, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings

DEFAULT_PROFILE = {
    "id": 1,
    "name": "Alex Carter",
    "headline": "Senior Business Analytics Student",
    "summary": (
        "Business analytics student focused on turning complex data into clear decisions,"
        " actionable insights, and measurable outcomes for organizations."
    ),
    "email": "alex.carter@example.com",
}

DEFAULT_PUBLIC_PROFILE = {
    **DEFAULT_PROFILE,
    "experience": [],
    "education": [],
    "skills": [],
    "projects": [],
    "links": [],
    "settings": {"site_title": "Career Platform", "profile_visible": 1},
}

CONTENT_TABLES = ("experience", "education", "skills", "projects", "links")

metadata = MetaData()


def _text(name: str) -> Column:
    return Column(name, Text, nullable=False)


def _single_row_id() -> Column:
    return Column("id", Integer, CheckConstraint("id = 1"), primary_key=True, autoincrement=False)


Table("profile", metadata, _single_row_id(), _text("name"), _text("headline"), _text("summary"), _text("email"))
Table("experience", metadata, Column("id", Integer, primary_key=True), _text("title"), _text("company"), _text("details"))
Table(
    "education", metadata,
    Column("id", Integer, primary_key=True), _text("school"), _text("degree"), _text("field"), _text("details"),
)
Table("skills", metadata, Column("id", Integer, primary_key=True), _text("name"), _text("category"))
Table("projects", metadata, Column("id", Integer, primary_key=True), _text("title"), _text("summary"))
Table("links", metadata, Column("id", Integer, primary_key=True), _text("label"), _text("url"))
Table(
    "settings", metadata,
    _single_row_id(), _text("site_title"), Column("profile_visible", Integer, nullable=False, server_default="1"),
)

ORDER_BY = {
    "experience": ("id",),
    "education": ("id",),
    "skills": ("category", "id"),
    "projects": ("id",),
    "links": ("id",),
}

# Content rows carry no explicit ids so Postgres sequences stay in step with the data.
SEED_ROWS: dict[str, list[dict[str, Any]]] = {
    "profile": [{key: DEFAULT_PROFILE[key] for key in ("id", "name", "headline", "summary", "email")}],
    "experience": [
        {
            "title": "Data Analyst Intern",
            "company": "Northwind Retail",
            "details": "Built SQL-based dashboards and KPI tracking for customer and merchandising data.",
        },
        {
            "title": "Business Operations Assistant",
            "company": "Civic Insights Group",
            "details": "Supported forecasting, process improvement, and cross-functional reporting projects.",
        },
    ],
    "education": [
        {
            "school": "Rensselaer Polytechnic Institute",
            "degree": "Bachelor of Science",
            "field": "Business Analytics",
            "details": "Focus on data analysis, forecasting, and decision support systems.",
        },
        {
            "school": "University of Washington",
            "degree": "Certificate",
            "field": "Business Intelligence",
            "details": "Completed coursework in SQL, Excel analytics, and data storytelling.",
        },
    ],
    "skills": [
        {"name": name, "category": category}
        for name, category in (
            ("SQL", "technical"),
            ("Python", "technical"),
            ("Excel", "technical"),
            ("Power BI", "technical"),
            ("Forecasting", "analytical"),
            ("Data Visualization", "analytical"),
            ("Stakeholder Communication", "business"),
            ("Project Management", "business"),
        )
    ],
    "projects": [
        {"title": "Revenue Trend Dashboard", "summary": "Built an executive dashboard tracking revenue and funnel metrics."},
        {"title": "Customer Retention Study", "summary": "Analyzed churn drivers and recommended actions for loyalty programs."},
    ],
    "links": [
        {"label": "LinkedIn", "url": "https://www.linkedin.com"},
        {"label": "GitHub", "url": "https://github.com"},
        {"label": "Portfolio", "url": "https://example.com"},
    ],
    "settings": [{"id": 1, "site_title": "Career Platform", "profile_visible": 1}],
}


@lru_cache
def engine_for(url: str) -> Engine:
    # A short connect timeout lets the public page fall back to the snapshot quickly.
    connect_args = {"connect_timeout": 5} if url.startswith("postgresql") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def get_engine() -> Engine:
    return engine_for(get_settings().database_url)


def _default_profile() -> dict[str, Any]:
    return deepcopy(DEFAULT_PUBLIC_PROFILE)


def read_profile_snapshot() -> dict[str, Any]:
    snapshot_path = get_settings().snapshot_path
    if not snapshot_path.exists():
        return write_profile_snapshot(_default_profile())

    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return write_profile_snapshot(_default_profile())

    if not isinstance(data, dict):
        return write_profile_snapshot(_default_profile())

    merged = _default_profile()
    for key, value in data.items():
        if key in CONTENT_TABLES:
            merged[key] = value if isinstance(value, list) else []
        elif key == "settings":
            merged[key] = value if isinstance(value, dict) else merged["settings"]
        else:
            merged[str(key)] = str(value)
    return merged


def write_profile_snapshot(profile: dict[str, Any]) -> dict[str, Any]:
    snapshot_path = get_settings().snapshot_path
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profile


def initialize_database() -> None:
    url = make_url(get_settings().database_url)
    if url.get_backend_name() == "sqlite" and url.database:
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    metadata.create_all(engine)
    with engine.begin() as connection:
        # Seed only a new database; re-seeding would duplicate rows and undo admin deletes.
        if connection.execute(select(metadata.tables["profile"].c.id)).first():
            return
        for name, rows in SEED_ROWS.items():
            connection.execute(insert(metadata.tables[name]), rows)


def load_public_profile() -> dict[str, Any]:
    """Return live profile data when available, else the last known good snapshot."""
    try:
        with get_engine().connect() as connection:
            profile_table = metadata.tables["profile"]
            row = connection.execute(select(profile_table).where(profile_table.c.id == 1)).mappings().first()
            if row is None:
                raise RuntimeError("The resume profile is not initialized")
            profile = dict(row)
            for name, order_by in ORDER_BY.items():
                table = metadata.tables[name]
                query = select(table).order_by(*(table.c[column] for column in order_by))
                profile[name] = [dict(item) for item in connection.execute(query).mappings()]
            settings_table = metadata.tables["settings"]
            settings_row = connection.execute(select(settings_table).where(settings_table.c.id == 1)).mappings().first()
            profile["settings"] = dict(settings_row) if settings_row else deepcopy(DEFAULT_PUBLIC_PROFILE["settings"])
        write_profile_snapshot(profile)
        return profile
    except (SQLAlchemyError, OSError, RuntimeError):
        return read_profile_snapshot()


def get_profile() -> dict[str, Any]:
    return load_public_profile()
```

- [ ] **Step 6: Rewrite `app/admin.py`**

```python
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
```

- [ ] **Step 7: Run the full suite**

Run: `uv run pytest -q`
Expected: all pass (`test_config` 6 + `test_database_schema` 7 + `test_public_profile` 7 + `test_project_setup` 1 = `21 passed`).

Tests now call `initialize_database()` themselves, because `load_public_profile` no longer seeds an empty database (Task 3 moves seeding to app startup).

- [ ] **Step 8: Check that no `sqlite3` import remains**

Run: `grep -rn "import sqlite3" app tests`
Expected: no output.

- [ ] **Step 9: Commit**

```bash
git add app/database.py app/admin.py tests/conftest.py tests/test_database_schema.py tests/test_public_profile.py
git commit -m "refactor: move database layer to SQLAlchemy Core for Postgres support"
```

---

### Task 3: Startup init, `/healthz`, Railway deploy config, résumé PDF

**Files:**
- Modify: `app/main.py`
- Modify: `start.sh`
- Create: `railway.json`
- Modify: `.gitignore`; Add: `data/resume.pdf` (only if D1 is confirmed)
- Test: `tests/test_health.py`

**Interfaces:**
- Consumes: `initialize_database`, `get_engine` (Task 2); `unreachable_database` fixture (Task 2).
- Produces: `GET /healthz` → `200 "ok"` or `503 "database unavailable"`; app lifespan that initializes the DB and never crashes startup.

- [ ] **Step 1: Write the failing tests** — create `tests/test_health.py`:

```python
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

    assert "Senior Business Analytics Student" in response.text


def test_app_starts_and_serves_snapshot_when_database_is_down_at_boot(monkeypatch):
    initialize_database()
    load_public_profile()  # writes the snapshot
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://nobody@127.0.0.1:1/missing")

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Senior Business Analytics Student" in response.text
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_health.py -v`
Expected: the `healthz` tests FAIL with 404, and `test_startup_seeds_an_empty_database` FAILs (no seeding).

- [ ] **Step 3: Implement** — in `app/main.py`, replace the imports and the `app = FastAPI(...)` line with the following. Leave the rest of the file as it is.

```python
import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from .database import get_engine, get_profile, initialize_database
from .admin import delete_record, save_record

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A database outage must not stop the site from serving its snapshot.
    try:
        initialize_database()
    except SQLAlchemyError:
        logger.exception("Database initialization failed; serving the snapshot until it recovers")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
```

And add this route after `resume_pdf`:

```python
@app.get("/healthz", include_in_schema=False)
def healthz():
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return PlainTextResponse("database unavailable", status_code=503)
    return PlainTextResponse("ok")
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest -q`
Expected: `25 passed`

- [ ] **Step 5: Make uvicorn trust Railway's proxy headers** — replace the last line of `start.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
# Behind Railway's proxy, trust X-Forwarded-Proto so url_for builds https:// asset links.
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips "*"
```

- [ ] **Step 6: Create `railway.json`**

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "RAILPACK"
  },
  "deploy": {
    "startCommand": "bash start.sh",
    "healthcheckPath": "/healthz",
    "healthcheckTimeout": 60,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  }
}
```

- [ ] **Step 7: Résumé PDF (only if D1 is confirmed)**

```bash
cp "Ethan Jad - Resume (web-safe).pdf" data/resume.pdf
cmp data/resume.pdf "Ethan Jad - Resume (web-safe).pdf" && echo same
printf '!data/resume.pdf\n' >> .gitignore
git check-ignore data/resume.pdf || echo "not ignored"
```

Expected: `same`, then `not ignored`. Open `data/resume.pdf` and check that it has no phone number or street address before committing.

- [ ] **Step 8: Local smoke run**

```bash
DATABASE_URL="sqlite:///$PWD/data/smoke.db" SNAPSHOT_PATH="$PWD/data/smoke.json" PORT=8011 uv run bash start.sh & PID=$!
sleep 2
curl -s localhost:8011/healthz; echo
curl -s -H 'X-Forwarded-Proto: https' localhost:8011/ | grep -o 'href="[^"]*styles.css"'
kill $PID; rm -f data/smoke.db data/smoke.json
```

Expected: `ok`, then `href="https://localhost:8011/static/styles.css"`. The `https` shows that the proxy header is trusted.

- [ ] **Step 9: Commit**

```bash
git add app/main.py start.sh railway.json tests/test_health.py .gitignore
git add data/resume.pdf   # only if D1 confirmed
git commit -m "feat: add healthz, startup DB init and Railway deploy config"
```

---

### Task 4: Copy script (SQLite → Postgres, keeping ids)

**Files:**
- Create: `scripts/copy_database.py`
- Test: `tests/test_copy_database.py`

**Interfaces:**
- Consumes: `metadata`, `CONTENT_TABLES`, `engine_for` (Task 2); `normalize_database_url` (Task 1); `database_url` fixture.
- Produces: `copy_database(source_url: str, target_url: str, replace: bool = False) -> dict[str, int]` (rows copied per table). CLI: `uv run python -m scripts.copy_database SOURCE_URL TARGET_URL [--replace]`.

- [ ] **Step 1: Write the failing tests** — create `tests/test_copy_database.py`:

```python
import pytest
from sqlalchemy import insert

from app.admin import save_record
from app.database import engine_for, initialize_database, load_public_profile, metadata
from scripts.copy_database import copy_database


@pytest.fixture
def source_url(tmp_path):
    """A SQLite database shaped like the VM's: real ids with gaps from earlier deletes."""
    url = f"sqlite:///{tmp_path / 'source.db'}"
    engine = engine_for(url)
    metadata.create_all(engine)
    tables = metadata.tables
    with engine.begin() as connection:
        connection.execute(insert(tables["profile"]), [{"id": 1, "name": "Ethan Jad", "headline": "Finance", "summary": "S", "email": "e@example.com"}])
        connection.execute(insert(tables["settings"]), [{"id": 1, "site_title": "Ethan Jad", "profile_visible": 1}])
        connection.execute(insert(tables["experience"]), [
            {"id": 3, "title": "Analyst", "company": "A", "details": "d"},
            {"id": 7, "title": "Intern", "company": "B", "details": "d"},
        ])
    return url


def test_copy_keeps_rows_and_ids(source_url, database_url):
    counts = copy_database(source_url, database_url)

    profile = load_public_profile()
    assert profile["name"] == "Ethan Jad"
    assert [item["id"] for item in profile["experience"]] == [3, 7]
    assert counts == {"profile": 1, "experience": 2, "education": 0, "skills": 0, "projects": 0, "links": 0, "settings": 1}


def test_admin_insert_after_copy_gets_next_id(source_url, database_url):
    copy_database(source_url, database_url)

    save_record("experience", {"title": "New", "company": "C", "details": "d"})

    assert [item["id"] for item in load_public_profile()["experience"]] == [3, 7, 8]


def test_copy_refuses_to_overwrite_existing_data_without_replace(source_url, database_url):
    initialize_database()  # target now holds the demo seed

    with pytest.raises(ValueError, match="--replace"):
        copy_database(source_url, database_url)

    copy_database(source_url, database_url, replace=True)
    assert [item["id"] for item in load_public_profile()["experience"]] == [3, 7]
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_copy_database.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts'`

- [ ] **Step 3: Implement** — create `scripts/copy_database.py`:

```python
"""Copy every career-platform table from one database to another, keeping row ids.

Usage: uv run python -m scripts.copy_database SOURCE_URL TARGET_URL [--replace]
"""
import argparse
import sys

from sqlalchemy import delete, func, insert, select, text

from app.config import normalize_database_url
from app.database import CONTENT_TABLES, engine_for, metadata


def copy_database(source_url: str, target_url: str, replace: bool = False) -> dict[str, int]:
    source = engine_for(normalize_database_url(source_url))
    target = engine_for(normalize_database_url(target_url))
    metadata.create_all(target)
    counts: dict[str, int] = {}
    with source.connect() as reader, target.begin() as writer:
        has_data = any(
            writer.execute(select(func.count()).select_from(table)).scalar_one() for table in metadata.sorted_tables
        )
        if has_data and not replace:
            raise ValueError("target database already has data; pass --replace to overwrite it")
        for table in metadata.sorted_tables:
            rows = [dict(row) for row in reader.execute(select(table)).mappings()]
            writer.execute(delete(table))
            if rows:
                writer.execute(insert(table), rows)
            counts[table.name] = len(rows)
        if writer.dialect.name == "postgresql":
            # Rows arrived with explicit ids, so move each sequence past the highest one.
            for name in CONTENT_TABLES:
                writer.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {name}"
                ))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source_url")
    parser.add_argument("target_url")
    parser.add_argument("--replace", action="store_true", help="overwrite a target that already has data")
    args = parser.parse_args()
    try:
        counts = copy_database(args.source_url, args.target_url, args.replace)
    except ValueError as error:
        sys.exit(str(error))
    for name, count in counts.items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest -q`
Expected: `28 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/copy_database.py tests/test_copy_database.py
git commit -m "feat: add script to copy the database to Postgres keeping ids"
```

---

### Task 5: Run the suite against real Postgres, then merge

**Files:** none (verification, then merge).

- [ ] **Step 1: Create a throwaway `railway_test` database** on the Railway Postgres instance

```bash
set -a; . ./.env; set +a
uv run python -c "
import os, psycopg
with psycopg.connect(os.environ['RAILWAY_DATABASE_URL'], autocommit=True) as c:
    c.execute('CREATE DATABASE railway_test')
print('created')"
```

Expected: `created`

- [ ] **Step 2: Run the whole suite on Postgres**

```bash
set -a; . ./.env; set +a
TEST_DATABASE_URL="${RAILWAY_DATABASE_URL%/*}/railway_test" uv run pytest -q
```

Expected: `28 passed`. These tests matter most here: `test_admin_insert_on_seeded_database_gets_next_id` and `test_admin_insert_after_copy_gets_next_id` (Review Focus 2), plus the `CheckConstraint` on `profile.id`.

- [ ] **Step 3: Drop the test database**

```bash
set -a; . ./.env; set +a
uv run python -c "
import os, psycopg
with psycopg.connect(os.environ['RAILWAY_DATABASE_URL'], autocommit=True) as c:
    c.execute('DROP DATABASE railway_test')
print('dropped')"
```

- [ ] **Step 4: Ask the user before pushing.** After they say yes:

```bash
git switch main && git merge --ff-only railway-postgres && git push origin main
```

The VM is unaffected because it does not pull automatically.

---

### Task 6: Railway setup, data copy and first deploy (user + agent)

**Files:** none in the repo. Railway and VM operations only.

- [ ] **Step 1: Install and log in to the Railway CLI**

```bash
brew install railway
```

The user runs `! railway login` (interactive), then `! railway link` in `career-platform` to choose the existing project. Check with `railway status`. Note the web service's name and use it wherever this task says `<web-service>`.

- [ ] **Step 2: Point the web service at the repo.** In the Railway dashboard, under web service → Settings → Source: repo `ethanjad/career-platform`, branch `main`, root directory empty. Railway picks up `railway.json` from the repo root.

- [ ] **Step 3: Set variables** (D2: new secret)

```bash
railway variables --service <web-service> \
  --set 'DATABASE_URL=${{Postgres.DATABASE_URL}}' \
  --set "ADMIN_SECRET=$(openssl rand -hex 32)"
railway variables --service <web-service> --kv | sed 's/=.*/=<set>/'
```

Expected: `DATABASE_URL` and `ADMIN_SECRET` are listed. **Don't** set `HOST`, `PORT` or `DATABASE_PATH`. Railway provides `PORT`. Copy `ADMIN_SECRET` from the dashboard into a password manager.

- [ ] **Step 4: Export the live data from the VM** (read-only on the VM; uses SQLite's online backup)

```bash
ssh career-vm 'sqlite3 ~/career-platform/data/resume.db ".backup /tmp/resume-export.db" && sqlite3 /tmp/resume-export.db "select count(*) from experience; select count(*) from skills;"'
scp career-vm:/tmp/resume-export.db ~/Desktop/github/resume-vm-export-$(date +%Y%m%d).db
```

Expected counts: `4` and `4`. **No admin edits on the VM from here on.**

- [ ] **Step 5: Copy into Railway Postgres**

```bash
cd ~/Desktop/github/career-platform
set -a; . ./.env; set +a
uv run python -m scripts.copy_database "sqlite:///$HOME/Desktop/github/resume-vm-export-$(date +%Y%m%d).db" "$RAILWAY_DATABASE_URL"
```

Expected: `profile: 1`, `experience: 4`, `education: 2`, `skills: 4`, `projects: 2`, `links: 1`, `settings: 1`. Copy the data **before** the first deploy, so the app's startup step finds a profile row and doesn't seed the demo data.

- [ ] **Step 6: Deploy and watch**

Run `railway redeploy --service <web-service>`, or push to `main`, then `railway logs --service <web-service>`.
Expected: the healthcheck on `/healthz` succeeds and the deploy is marked Active. If the logs show `uvicorn: command not found`, change the last line of `start.sh` to `exec python -m uvicorn …` and redeploy.

- [ ] **Step 7: Generate a Railway domain and verify on it** (Settings → Networking → Generate Domain; call it `<RAILWAY_DOMAIN>`)

```bash
D=<RAILWAY_DOMAIN>
curl -sS https://$D/healthz; echo                                       # ok
curl -sS https://$D/ | grep -c "Ethan Jad"                              # ≥ 1 (real data, not Alex Carter)
curl -sS https://$D/ | grep -o 'href="[^"]*\(styles.css\|woff2\)"'      # both start with https://
curl -sSI https://$D/resume.pdf | grep -i '^content-type'               # application/pdf
```

- [ ] **Step 8: Check that admin writes work and that the data is stored in Postgres**

```bash
S='<ADMIN_SECRET from password manager>'
curl -sS -X POST https://$D/admin/projects -H "X-Admin-Secret: $S" -H 'Content-Type: application/json' \
  -d '{"title":"Railway check","summary":"temporary"}'                  # {"ok":true}
curl -sS https://$D/ | grep -c "Railway check"                          # 1
railway redeploy --service <web-service>   # new container, empty disk
curl -sS https://$D/ | grep -c "Railway check"                          # still 1 → data lives in Postgres
```

Then delete the row. Get its id from Postgres (it should be 3):

```bash
set -a; . ./.env; set +a
uv run python -c "
import os, psycopg
with psycopg.connect(os.environ['RAILWAY_DATABASE_URL']) as c:
    print(c.execute(\"select id from projects where title='Railway check'\").fetchall())"
curl -sS -X DELETE https://$D/admin/projects/<id> -H "X-Admin-Secret: $S"
```

- [ ] **Step 9: User check in a browser.** Open `https://<RAILWAY_DOMAIN>` and compare it with https://ethanjad.me: the fonts load, every section is there, and the résumé downloads. **Don't touch DNS until the user confirms.**

---

### Task 7: DNS cutover at Cloudflare (user + agent)

- [ ] **Step 1: Add custom domains in Railway.** Under web service → Settings → Networking → Custom Domain, add `ethanjad.me` and `www.ethanjad.me`. Railway shows a CNAME target for each, and possibly a `_railway-verify` TXT record.

- [ ] **Step 2: Write down the current records** for rollback. In the Cloudflare dashboard → DNS → Records, note the `ethanjad.me` A record (`<VM_PUBLIC_IP>`) and the `www` record.

- [ ] **Step 3: Switch the records** in Cloudflare:
  - Delete the apex A record and add `CNAME @ → <Railway target>`, **proxy off (grey cloud)**. Cloudflare flattens it automatically.
  - Replace the `www` record with `CNAME www → <Railway target for www>`, proxy off.
  - Add the TXT verification records if Railway showed any.

- [ ] **Step 4: Wait for Railway to show both domains as verified** with a certificate issued. This usually takes a few minutes.

- [ ] **Step 5: Verify**

```bash
dig +short ethanjad.me                                   # Railway edge IPs, not the VM's
curl -sSI https://ethanjad.me | grep -i '^server'        # server: railway-edge
curl -sSI http://ethanjad.me | head -1                   # 301 or 308 to https
curl -sS https://www.ethanjad.me/healthz; echo           # ok
curl -sS https://ethanjad.me/ | grep -c "Ethan Jad"      # ≥ 1
echo | openssl s_client -connect ethanjad.me:443 -servername ethanjad.me 2>/dev/null | openssl x509 -noout -issuer -enddate
```

- [ ] **Step 6: Rollback, only if something is wrong.** Restore the A record `@ → <VM_PUBLIC_IP>` and the original `www` record from Step 2. The VM is still serving, so the site recovers once DNS updates.

---

### Task 8: Docs and handoff

**Files:**
- Modify: `README.md`
- Modify: `.env.example`

- [ ] **Step 1: Update `.env.example`**

```
# Leave DATABASE_URL unset to use local SQLite at DATABASE_PATH.
# DATABASE_URL=postgresql://user:password@host:5432/dbname
DATABASE_PATH=data/resume.db
ADMIN_SECRET=replace-with-a-long-random-secret
ENABLE_FALLBACK=true
HOST=127.0.0.1
PORT=8000
```

- [ ] **Step 2: Update `README.md`.** Change the first line to "A recruiter-facing FastAPI, Jinja, and PostgreSQL résumé site (SQLite for local development)." Replace the "Azure VM path" section with:

````markdown
## Deploying on Railway

The `web` service deploys `main` with `railway.json` (start: `start.sh`,
healthcheck: `/healthz`). It needs two variables:

- `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (Railway reference variable)
- `ADMIN_SECRET` = a long random string

To copy data between databases (keeps ids, refuses to overwrite unless
`--replace`):

```bash
uv run python -m scripts.copy_database SOURCE_URL TARGET_URL
```

Run the tests against Postgres by pointing `TEST_DATABASE_URL` at a
throwaway database whose name contains `test`.
````

In "Database fallback", change "If SQLite is unavailable" to "If the database is unavailable".

- [ ] **Step 3: Commit** (push only after the user says yes)

```bash
git add README.md .env.example
git commit -m "docs: describe Railway + Postgres deployment"
```

- [ ] **Step 4: Hand off to the user. Don't do these yourself:**
  - `docs/how-this-site-is-secured.md` still describes nginx, certbot and the NSG on Azure. Now HTTPS is handled by Railway's edge (automatic certificates), and HTTP→HTTPS is Railway's redirect. The user updates the doc in their own words.
  - Retiring the VM (stop, deallocate or delete `vm-career-platform`) waits for the user's explicit OK after a few days on Railway with no problems. Keep `~/Desktop/github/resume-vm-export-*.db` as an offline backup.
  - Optional: in Cloudflare, turn the proxy on (orange cloud) later with SSL mode **Full (strict)**. It isn't needed.
