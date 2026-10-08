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
