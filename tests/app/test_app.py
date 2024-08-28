"""Test FastAPI app."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hub_api.main import app


def test_plugin_index(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test app."""
    monkeypatch.setenv("PLUGINS_FILES_PATH", "tests/fixtures/plugins")
    client = TestClient(app)
    response = client.get("/meltano/api/v1/plugins/extractors/index")
    assert response.status_code == 200
    assert response.json()


def test_plugin_details(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test app."""
    monkeypatch.setenv("PLUGINS_FILES_PATH", "tests/fixtures/plugins")
    client = TestClient(app)
    response = client.get("/meltano/api/v1/plugins/extractors/tap-github--singer-io")
    assert response.status_code == 200

    plugin = response.json()
    assert plugin["name"] == "tap-github"


def test_hub_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test app."""
    monkeypatch.setenv("PLUGINS_FILES_PATH", "tests/fixtures/plugins")
    client = TestClient(app)
    response = client.get("/meltano/api/v1/plugins/stats")
    assert response.status_code == 200

    stats = response.json()
    assert isinstance(stats["extractors"], int)
