from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_project_structure_and_config_exist():
    expected_paths = [
        "app", "templates", "static", "data", "tests",
        "app/main.py", "app/config.py", "app/database.py",
        "templates/index.html", "static/styles.css", "requirements.txt",
    ]

    for relative_path in expected_paths:
        assert (ROOT / relative_path).exists(), f"Missing {relative_path}"

    from app.main import app

    assert app.title == "Career Platform"
    assert (ROOT / "app" / "config.py").read_text()
    assert "fastapi" in (ROOT / "requirements.txt").read_text().lower()
