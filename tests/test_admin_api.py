from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app import main
from app.database import initialize_database, load_public_profile
from app.main import app

SECRET = "test-admin-secret"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings, admin_secret=SECRET))
    initialize_database()
    # Report a server error as a 500, as a real visitor would see it, instead of re-raising it here.
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "method, path",
    [("POST", "/admin/nope"), ("PUT", "/admin/nope/1"), ("DELETE", "/admin/nope/1")],
)
def test_unknown_table_returns_404(client, method, path):
    response = client.request(method, path, json={}, headers={"X-Admin-Secret": SECRET})

    assert response.status_code == 404


def test_unknown_table_without_the_secret_is_still_401(client):
    response = client.post("/admin/nope", json={}, headers={"X-Admin-Secret": "wrong"})

    assert response.status_code == 401


def test_known_table_still_saves(client):
    response = client.post(
        "/admin/skills",
        json={"name": "Terraform", "category": "Cloud"},
        headers={"X-Admin-Secret": SECRET},
    )

    assert response.status_code == 200
    assert "Terraform" in [skill["name"] for skill in load_public_profile()["skills"]]
