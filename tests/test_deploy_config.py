from pathlib import Path

from fastapi.testclient import TestClient

from app.database import initialize_database
from app.main import app

DEPLOY = Path(__file__).resolve().parents[1] / "deploy"


def test_service_binds_loopback_with_one_worker_and_reads_the_env_file():
    unit = (DEPLOY / "career-platform.service").read_text()
    assert "--host 127.0.0.1 --port 8000" in unit
    assert "EnvironmentFile=/etc/career-platform/env" in unit
    assert "--workers" not in unit and "start.sh" not in unit


def test_service_refuses_to_start_without_required_secrets():
    unit = (DEPLOY / "career-platform.service").read_text()
    assert 'test -n "$$DATABASE_URL"' in unit and 'test -n "$$ADMIN_SECRET"' in unit


def test_nginx_forwards_scheme_and_redirects_http():
    conf = (DEPLOY / "nginx-career-platform.conf").read_text()
    assert "X-Forwarded-Proto $scheme" in conf
    assert "proxy_pass http://127.0.0.1:8000" in conf
    assert "return 301 https://ethanjad.me$request_uri" in conf


def test_nginx_serves_aws_name_over_https_and_redirects_its_http():
    conf = (DEPLOY / "nginx-career-platform.conf").read_text()
    assert "return 301 https://aws.ethanjad.me$request_uri" in conf
    assert "ssl_certificate /etc/letsencrypt/live/aws.ethanjad.me/fullchain.pem" in conf
    assert "ssl_certificate_key /etc/letsencrypt/live/aws.ethanjad.me/privkey.pem" in conf
    assert conf.count("proxy_pass http://127.0.0.1:8000") == 2


def test_nginx_rejects_unknown_hosts():
    conf = (DEPLOY / "nginx-career-platform.conf").read_text()
    assert "return 444" in conf and "ssl_reject_handshake on" in conf


def test_deploy_script_finds_uv_over_a_plain_ssh_command():
    script = (DEPLOY / "deploy.sh").read_text()
    assert 'export PATH="$HOME/.local/bin:$PATH"' in script


def test_privacy_page_names_aws_not_railway():
    initialize_database()
    page = TestClient(app).get("/privacy").text
    assert "Amazon Web Services" in page and "Railway" not in page
