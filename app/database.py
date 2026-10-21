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
    "name": "Ethan Jad",
    "headline": (
        "BBA in Finance and Information Systems & Business Analytics (ISBA) · Loyola Marymount University"
        " · Class of 2027 · GPA 3.62 · Dean's List 4×"
    ),
    "summary": (
        "A highly-driven Finance and ISBA student with strong analytical and problem-solving skills"
        " with a passion for business development."
    ),
    "email": "ethanjad@gmail.com",
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
            "title": "Financial Budgeting Intern",
            "company": "Student Housing Office, Loyola Marymount University",
            "details": (
                "Jun 2026 – Present. Conduct expense and inventory management representative of the LMU"
                " housing department."
            ),
        },
        {
            "title": "Front Office Assistant",
            "company": "Student Housing Office, Loyola Marymount University",
            "details": (
                "Aug 2025 – May 2026. First point of contact for students, parents, and staff by providing"
                " information and resolving inquiries. Manage high volume of emails, phone calls, and"
                " interactions with professionalism and efficiency."
            ),
        },
        {
            "title": "International Consulting Intern",
            "company": "Lorawine Startup, Los Angeles, California",
            "details": (
                "Aug 2025 – Dec 2025. Creating data-based strategy for Lorawine, an Italian-based startup, in the"
                " expansion to Napa, California, specialized in environmental and strategic positioning for entry"
                " into the US market. Worked alongside Buonquillo International to seek competitive advantages"
                " through the use of AI."
            ),
        },
        {
            "title": "Mentee",
            "company": "Remote Job Shadowing Program, San Mateo, California",
            "details": (
                "May 2025 – Aug 2025. Paired with a finance professional through LMU's alumni network for"
                " one-on-one mentorship. Engaged in biweekly, hour-long phone calls discussing industry insights"
                " and professional development."
            ),
        },
    ],
    "education": [
        {
            "school": "Loyola Marymount University",
            "degree": "Bachelor of Business Administration",
            "field": "ISBA and Finance",
            "details": "Aug 2023 – Present · Los Angeles, California · GPA 3.62 · Dean's List (4x)",
        },
        {
            "school": "Junipero Serra High School",
            "degree": "High School Diploma",
            "field": "CSF Seal Bearer",
            "details": "Aug 2019 – May 2023 · San Mateo, California · GPA 3.87",
        },
    ],
    "skills": [
        {"name": name, "category": "technical"}
        for name in ("Microsoft Office", "Google Suite", "MySQL Workbench", "Python")
    ],
    "projects": [
        {"title": "Sports Business Association", "summary": "Active club member."},
        {"title": "Finance Society", "summary": "Active club member."},
        {"title": "Hoops Recap", "summary": "Co-founder & content creator of a basketball media platform."},
        {
            "title": "Friends of Ballona Wetlands",
            "summary": "Volunteer and active member of the environmentalist group (Aug 2025 – Present).",
        },
        {
            "title": "Nikkei Student Union",
            "summary": "Active club member and travel basketball player representing LMU.",
        },
        {"title": "ISBA Student Society", "summary": "Active club member."},
    ],
    "links": [
        {"label": "LinkedIn", "url": "https://www.linkedin.com/in/ethanjad"},
        {"label": "GitHub", "url": "https://github.com/ethanjad"},
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
    """Return live profile data, or the last known good snapshot without its projects when the database is down.

    `database_available` tells the page which one it got, so it can answer 503 and say projects are unavailable.
    """
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
        return {**profile, "database_available": True}
    except (SQLAlchemyError, OSError, RuntimeError):
        # Projects come only from the live database; the snapshot keeps the rest of the profile visible.
        return {**read_profile_snapshot(), "projects": [], "database_available": False}


def get_profile() -> dict[str, Any]:
    return load_public_profile()
