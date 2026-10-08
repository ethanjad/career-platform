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
