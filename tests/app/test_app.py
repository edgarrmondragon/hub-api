"""Test FastAPI app."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from hub_api.main import app


@pytest.fixture(scope="session")
def api() -> AsyncClient:
    """Create app."""
    return AsyncClient(base_url="http://test", transport=ASGITransport(app=app))


@pytest.mark.asyncio
async def test_plugin_index(api: AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/extractors/index."""
    response = await api.get("/meltano/api/v1/plugins/extractors/index")
    assert response.status_code == 200
    assert response.json()


@pytest.mark.asyncio
async def test_plugin_details(api: AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/extractors/<plugin>--<variant>."""
    response = await api.get("/meltano/api/v1/plugins/extractors/tap-github--singer-io")
    assert response.status_code == 200

    plugin = response.json()
    assert plugin["name"] == "tap-github"


@pytest.mark.asyncio
async def test_hub_stats(api: AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/stats."""
    response = await api.get("/meltano/api/v1/plugins/stats")
    assert response.status_code == 200

    stats = response.json()
    assert isinstance(stats["extractors"], int)
