"""Test FastAPI app."""

from __future__ import annotations

import http

import httpx
import pytest

from hub_api import enums, main
from hub_api.helpers import etag


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
async def test_plugin_index_etag_match(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/stats."""
    etag_value = etag.get_etag()

    response = await api.get("/meltano/api/v1/plugins/index")
    assert response.status_code == http.HTTPStatus.OK
    assert response.headers["ETag"] == etag_value
    assert "extractors" in response.json()

    response = await api.get(
        "/meltano/api/v1/plugins/index",
        headers={"If-None-Match": etag_value},
    )
    assert response.status_code == http.HTTPStatus.NOT_MODIFIED
    assert not response.content


@pytest.mark.asyncio
async def test_plugin_type_index_type_not_valid(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/<invalid_type>/index."""
    response = await api.get("/meltano/api/v1/plugins/unknown/index")
    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == "'unknown' is not a valid plugin type"


@pytest.mark.asyncio
async def test_invalid_etag(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/stats."""
    response = await api.get(
        "/meltano/api/v1/plugins/index",
        headers={"If-None-Match": "not-a-valid-etag"},
    )
    assert response.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY


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

    data = response.json()
    maintainer = next(filter(lambda m: m["id"] == "edgarrmondragon", data["maintainers"]))
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
    response = await api.get("/meltano/api/v1/maintainers/top", params={"count": n})
    assert response.status_code == http.HTTPStatus.OK

    maintainers = response.json()
    assert len(maintainers) == n


@pytest.mark.asyncio
async def test_default_plugin(api: httpx.AsyncClient) -> None:
    """Test /meltano/api/v1/plugins/extractors/tap-github/default."""
    response = await api.get("/meltano/api/v1/plugins/extractors/tap-github/default")
    assert response.status_code == http.HTTPStatus.TEMPORARY_REDIRECT
    assert response.is_redirect
    assert response.headers["Location"].endswith("extractors/tap-github--meltanolabs")


@pytest.mark.asyncio
async def test_gzip_encoding(api: httpx.AsyncClient) -> None:
    """Test GZIP encoding."""
    # Large response should be compressed
    response = await api.get("/meltano/api/v1/plugins/index", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == http.HTTPStatus.OK
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.headers["Content-Type"] == "application/json"

    # Small response should not be compressed
    response = await api.get("/meltano/api/v1/plugins/orchestrators/index", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == http.HTTPStatus.OK
    assert "Content-Encoding" not in response.headers
    assert response.headers["Content-Type"] == "application/json"
