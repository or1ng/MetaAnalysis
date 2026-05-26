from fastapi.testclient import TestClient

from config.settings import get_settings
from main import app


client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_metadata_uses_configured_version():
    settings = get_settings()
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == settings.APP_NAME
    assert body["version"] == settings.APP_VERSION
    assert body["docs"] == "/docs"


def test_openapi_version_uses_configured_version():
    assert app.version == get_settings().APP_VERSION
