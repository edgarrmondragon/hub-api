"""Test FastAPI app."""

from fastapi.testclient import TestClient

from app.main import app


def test_plugin_index():
    """Test app."""
    client = TestClient(app)
    response = client.get("/meltano/api/v1/plugins/extractors/index")
    assert response.status_code == 200
    assert response.json()


def test_plugin_details():
    """Test app."""
    client = TestClient(app)
    response = client.get("/meltano/api/v1/plugins/extractors/tap-github--singer-io")
    assert response.status_code == 200
    assert response.json()


def test_app_sqlite():
    """Test app."""
    client = TestClient(app)
    response = client.get("/meltano/api/v1/plugins/test-sqlite")
    assert response.status_code == 200
    assert response.json() == [{"bar": 42, "baz": "hello"}]
