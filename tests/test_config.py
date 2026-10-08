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
