"""Минимальные smoke-тесты приложения."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_unauthenticated_root_redirects_to_auth():
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("location") == "/auth"


def test_static_mount_exists():
    # без сессии главная страница недоступна; /static/... разрешён middleware
    r = client.get("/static/css/styles.css", follow_redirects=False)
    assert r.status_code == 200
