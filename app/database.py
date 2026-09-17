import json
import sqlite3
from copy import deepcopy
from pathlib import Path
from typing import Any

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

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    details TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS education (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school TEXT NOT NULL,
    degree TEXT NOT NULL,
    field TEXT NOT NULL,
    details TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    site_title TEXT NOT NULL,
    profile_visible INTEGER NOT NULL DEFAULT 1
);
"""


def _snapshot_path_for(database_path: Path | None = None) -> Path:
    path = database_path or get_settings().database_path
    return path.parent / "profile_snapshot.json"


def _default_profile() -> dict[str, Any]:
    return deepcopy(DEFAULT_PUBLIC_PROFILE)


def read_profile_snapshot(database_path: Path | None = None) -> dict[str, Any]:
    snapshot_path = _snapshot_path_for(database_path)
    if not snapshot_path.exists():
        return write_profile_snapshot(_default_profile(), database_path)

    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return write_profile_snapshot(_default_profile(), database_path)

    if not isinstance(data, dict):
        return write_profile_snapshot(_default_profile(), database_path)

    merged = _default_profile()
    for key, value in data.items():
        if key in {"experience", "education", "skills", "projects", "links"}:
            merged[key] = value if isinstance(value, list) else []
        elif key == "settings":
            merged[key] = value if isinstance(value, dict) else merged["settings"]
        else:
            merged[str(key)] = str(value)
    return merged


def write_profile_snapshot(profile: dict[str, Any], database_path: Path | None = None) -> dict[str, Any]:
    snapshot_path = _snapshot_path_for(database_path)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    payload = profile
    snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def initialize_database(database_path: Path | None = None) -> None:
    path = database_path or get_settings().database_path
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT OR IGNORE INTO profile (id, name, headline, summary, email) VALUES (1, ?, ?, ?, ?)",
            (
                "Alex Carter",
                "Senior Business Analytics Student",
                (
                    "Business analytics student focused on turning complex data into clear decisions,"
                    " actionable insights, and measurable outcomes for organizations."
                ),
                "alex.carter@example.com",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO experience (id, title, company, details) VALUES (1, ?, ?, ?)",
            (
                "Data Analyst Intern",
                "Northwind Retail",
                "Built SQL-based dashboards and KPI tracking for customer and merchandising data.",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO experience (id, title, company, details) VALUES (2, ?, ?, ?)",
            (
                "Business Operations Assistant",
                "Civic Insights Group",
                "Supported forecasting, process improvement, and cross-functional reporting projects.",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO education (id, school, degree, field, details) VALUES (1, ?, ?, ?, ?)",
            (
                "Rensselaer Polytechnic Institute",
                "Bachelor of Science",
                "Business Analytics",
                "Focus on data analysis, forecasting, and decision support systems.",
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO education (id, school, degree, field, details) VALUES (2, ?, ?, ?, ?)",
            (
                "University of Washington",
                "Certificate",
                "Business Intelligence",
                "Completed coursework in SQL, Excel analytics, and data storytelling.",
            ),
        )
        for name, category in (
            ("SQL", "technical"),
            ("Python", "technical"),
            ("Excel", "technical"),
            ("Power BI", "technical"),
            ("Forecasting", "analytical"),
            ("Data Visualization", "analytical"),
            ("Stakeholder Communication", "business"),
            ("Project Management", "business"),
        ):
            connection.execute(
                "INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)",
                (name, category),
            )
        for title, summary in (
            ("Revenue Trend Dashboard", "Built an executive dashboard tracking revenue and funnel metrics."),
            ("Customer Retention Study", "Analyzed churn drivers and recommended actions for loyalty programs."),
        ):
            connection.execute(
                "INSERT OR IGNORE INTO projects (title, summary) VALUES (?, ?)",
                (title, summary),
            )
        for label, url in (
            ("LinkedIn", "https://www.linkedin.com"),
            ("GitHub", "https://github.com"),
            ("Portfolio", "https://example.com"),
        ):
            connection.execute(
                "INSERT OR IGNORE INTO links (label, url) VALUES (?, ?)",
                (label, url),
            )
        connection.execute(
            "INSERT OR IGNORE INTO settings (id, site_title, profile_visible) VALUES (1, ?, ?)",
            ("Career Platform", 1),
        )


def load_public_profile(database_path: Path | None = None) -> dict[str, Any]:
    """Return live profile data when available, else the last known good snapshot."""
    path = database_path or get_settings().database_path
    try:
        initialize_database(path)
        with sqlite3.connect(path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute("SELECT * FROM profile WHERE id = 1").fetchone()
            if row is None:
                raise RuntimeError("The resume profile is not initialized")
            profile = dict(row)
            for table, order_by in (
                ("experience", "id"),
                ("education", "id"),
                ("skills", "category, id"),
                ("projects", "id"),
                ("links", "id"),
            ):
                profile[table] = [
                    dict(item)
                    for item in connection.execute(f"SELECT * FROM {table} ORDER BY {order_by}").fetchall()
                ]
            settings_row = connection.execute("SELECT * FROM settings WHERE id = 1").fetchone()
            profile["settings"] = dict(settings_row) if settings_row else deepcopy(DEFAULT_PUBLIC_PROFILE["settings"])
        write_profile_snapshot(profile, path)
        return profile
    except (sqlite3.Error, OSError, RuntimeError):
        return read_profile_snapshot(path)


def get_profile(database_path: Path | None = None) -> dict[str, str]:
    return load_public_profile(database_path)
