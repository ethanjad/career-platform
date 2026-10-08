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
