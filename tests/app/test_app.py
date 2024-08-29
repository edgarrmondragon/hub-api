"""Test FastAPI app."""

from __future__ import annotations

import httpx
import pytest

from hub_api import enums, main


@pytest.fixture(scope="session")
def api() -> httpx.AsyncClient:
    """Create app."""
    return httpx.AsyncClient(base_url="http://test", transport=httpx.ASGITransport(app=main.app))


@pytest.mark.asyncio
async def test_plugin_index(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/extractors/index."""
    response = await api.get("/meltano/api/v1/plugins/extractors/index")
    assert response.status_code == 200
    assert response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("plugin", "plugin_type", "variant"),
    [
        ("tap-github", enums.PluginTypeEnum.extractors, "singer-io"),
        ("tap-mssql", enums.PluginTypeEnum.extractors, "wintersrd"),
        ("tap-mssql", enums.PluginTypeEnum.extractors, "airbyte"),
        ("target-postgres", enums.PluginTypeEnum.loaders, "meltanolabs"),
        ("dbt-postgres", enums.PluginTypeEnum.utilities, "dbt-labs"),
    ],
)
async def test_plugin_details(
    api: httpx.AsyncClient,
    plugin: str,
    plugin_type: enums.PluginTypeEnum,
    variant: str,
) -> None:
    """Test /meltano/api/v1/plugins/extractors/<plugin>--<variant>."""
    path = f"/meltano/api/v1/plugins/{plugin_type}/{plugin}--{variant}"
    response = await api.get(path)
    assert response.status_code == 200

    details = response.json()
    assert details["name"] == plugin


@pytest.mark.asyncio
async def test_hub_stats(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/stats."""
    response = await api.get("/meltano/api/v1/plugins/stats")
    assert response.status_code == 200

    stats = response.json()
    assert isinstance(stats["extractors"], int)
