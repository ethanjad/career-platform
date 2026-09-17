from dataclasses import dataclass
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    app_name: str = "Career Platform"
    database_path: Path = ROOT_DIR / "data" / "resume.db"
    templates_dir: Path = ROOT_DIR / "templates"
    static_dir: Path = ROOT_DIR / "static"
    admin_secret: str = "change-me"
    enable_fallback: bool = True
    host: str = "127.0.0.1"
    port: int = 8000

def get_settings() -> Settings:
    database_path = Path(os.getenv("DATABASE_PATH", str(Settings.database_path)))
    if not database_path.is_absolute():
        database_path = ROOT_DIR / database_path
    return Settings(
        database_path=database_path,
        admin_secret=os.getenv("ADMIN_SECRET", "change-me"),
        enable_fallback=os.getenv("ENABLE_FALLBACK", "true").lower() not in {"0", "false", "no"},
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
    )
