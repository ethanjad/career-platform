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
