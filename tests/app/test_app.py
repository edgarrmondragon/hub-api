"""Test FastAPI app."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from hub_api.main import app
from hub_api.models import PluginType


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
@pytest.mark.parametrize(
    ("plugin", "plugin_type", "variant"),
    [
        ("tap-github", PluginType.extractors, "singer-io"),
        ("tap-mssql", PluginType.extractors, "wintersrd"),
        ("target-postgres", PluginType.loaders, "meltanolabs"),
        ("dbt-postgres", PluginType.utilities, "dbt-labs"),
    ],
)
async def test_plugin_details(
    api: AsyncClient,
    plugin: str,
    plugin_type: PluginType,
    variant: str,
) -> None:
    """Test /meltano/api/v1/plugins/extractors/<plugin>--<variant>."""
    path = f"/meltano/api/v1/plugins/{plugin_type}/{plugin}--{variant}"
    response = await api.get(path)
    assert response.status_code == 200

    details = response.json()
    assert details["name"] == plugin


@pytest.mark.asyncio
async def test_hub_stats(api: AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/stats."""
    response = await api.get("/meltano/api/v1/plugins/stats")
    assert response.status_code == 200

    stats = response.json()
    assert isinstance(stats["extractors"], int)
