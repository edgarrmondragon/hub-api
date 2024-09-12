"""Test FastAPI app."""

from __future__ import annotations

import http

import httpx
import pytest

from hub_api import enums, etag, main


@pytest.fixture(scope="session")
def api() -> httpx.AsyncClient:
    """Create app."""
    return httpx.AsyncClient(base_url="http://test", transport=httpx.ASGITransport(app=main.app))


@pytest.mark.asyncio
async def test_plugin_index(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/extractors/index."""
    response = await api.get("/meltano/api/v1/plugins/index")
    assert response.status_code == http.HTTPStatus.OK
    assert response.json()


@pytest.mark.asyncio
async def test_plugin_type_index(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/extractors/index."""
    response = await api.get("/meltano/api/v1/plugins/extractors/index")
    assert response.status_code == http.HTTPStatus.OK
    assert response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("plugin", "plugin_type", "variant"),
    [
        ("tap-github", enums.PluginTypeEnum.extractors, "singer-io"),
        ("tap-adwords", enums.PluginTypeEnum.extractors, "meltano"),
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
    assert response.status_code == http.HTTPStatus.OK

    details = response.json()
    assert details["name"] == plugin


@pytest.mark.asyncio
async def test_plugin_details_etag_match(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/stats."""
    etag_value = etag.get_etag()
    response = await api.get(
        "/meltano/api/v1/plugins/extractors/index",
        headers={"If-None-Match": etag_value},
    )
    assert response.status_code == http.HTTPStatus.NOT_MODIFIED


@pytest.mark.asyncio
async def test_plugin_variant_not_found(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/extractors/<plugin>--<variant>."""
    response = await api.get("/meltano/api/v1/plugins/extractors/tap-github--unknown")
    assert response.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_sdk_filter(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/made-with-sdk."""
    response = await api.get("/meltano/api/v1/plugins/made-with-sdk")
    assert response.status_code == http.HTTPStatus.OK

    plugins = response.json()
    assert len(plugins) > 0


@pytest.mark.asyncio
async def test_hub_stats(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/stats."""
    response = await api.get("/meltano/api/v1/plugins/stats")
    assert response.status_code == http.HTTPStatus.OK

    stats = response.json()
    assert isinstance(stats["extractors"], int)


@pytest.mark.asyncio
async def test_maintainers(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/maintainers."""
    response = await api.get("/meltano/api/v1/maintainers", follow_redirects=True)
    assert response.status_code == http.HTTPStatus.OK

    maintainers = response.json()
    maintainer = next(filter(lambda m: m["id"] == "edgarrmondragon", maintainers))
    assert maintainer["id"] == "edgarrmondragon"
    assert maintainer["url"] == "https://github.com/edgarrmondragon"


@pytest.mark.asyncio
async def test_maintainer_details(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/maintainers."""
    response = await api.get("/meltano/api/v1/maintainers/edgarrmondragon")
    assert response.status_code == http.HTTPStatus.OK

    maintainer = response.json()
    assert maintainer["id"] == "edgarrmondragon"
    assert maintainer["url"] == "https://github.com/edgarrmondragon"
    assert isinstance(maintainer["links"], dict)
    assert len(maintainer["links"]) > 0


@pytest.mark.asyncio
async def test_top_maintainers(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/maintainers."""
    n = 3
    response = await api.get(f"/meltano/api/v1/maintainers/top/{n}")
    assert response.status_code == http.HTTPStatus.OK

    maintainers = response.json()
    assert len(maintainers) == n
