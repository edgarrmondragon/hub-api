"""Test Hub data access."""

from __future__ import annotations

import typing as t

import pytest
import pytest_asyncio

from hub_api import client, database, enums, exceptions
from hub_api.schemas import api as api_schemas

if t.TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest_asyncio.fixture
async def hub() -> AsyncGenerator[client.MeltanoHub]:
    """Get a Meltano hub instance."""
    session_maker = database.get_session_maker()
    async with session_maker() as db:
        yield client.MeltanoHub(db=db)


@pytest.mark.asyncio
async def test_get_plugin_index(hub: client.MeltanoHub) -> None:
    """Test get_plugin_index."""
    plugins = await hub.get_plugin_index()
    assert plugins


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "plugin_type",
    list(enums.PluginTypeEnum),
)
async def test_get_plugin_type_index(hub: client.MeltanoHub, plugin_type: enums.PluginTypeEnum) -> None:
    """Test get_plugin_type_index."""
    plugin_types = await hub.get_plugin_type_index(plugin_type=plugin_type)
    assert plugin_types


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("plugin", "plugin_type", "variant"),
    [
        pytest.param("tap-github", enums.PluginTypeEnum.extractors, "singer-io"),
        pytest.param("tap-adwords", enums.PluginTypeEnum.extractors, "meltano"),
        pytest.param("tap-mssql", enums.PluginTypeEnum.extractors, "wintersrd"),
        pytest.param("tap-mssql", enums.PluginTypeEnum.extractors, "airbyte"),
        pytest.param("target-postgres", enums.PluginTypeEnum.loaders, "meltanolabs"),
        pytest.param("target-bigquery", enums.PluginTypeEnum.loaders, "z3z1ma"),
        pytest.param("dbt-postgres", enums.PluginTypeEnum.utilities, "dbt-labs"),
        pytest.param("dbt-postgres", enums.PluginTypeEnum.transformers, "dbt-labs"),
        pytest.param("tap-gitlab", enums.PluginTypeEnum.transforms, "meltano"),
        pytest.param("files-docker", enums.PluginTypeEnum.files, "meltano"),
        pytest.param("airflow", enums.PluginTypeEnum.orchestrators, "apache"),
        pytest.param("meltano-map-transformer", enums.PluginTypeEnum.mappers, "meltano"),
    ],
)
async def test_get_plugin_details(
    hub: client.MeltanoHub,
    plugin: str,
    plugin_type: str,
    variant: str,
) -> None:
    """Test get_plugin_details."""
    variant_id = f"{plugin_type}.{plugin}.{variant}"
    details = await hub.get_plugin_details(variant_id=variant_id)
    assert details.name == plugin
    assert details.variant == variant


@pytest.mark.asyncio
async def test_get_plugin_variant_not_found(hub: client.MeltanoHub) -> None:
    """Test get_plugin_details."""
    with pytest.raises(exceptions.NotFoundError):
        await hub.get_plugin_details(variant_id="unknown")


@pytest.mark.asyncio
async def test_get_sdk_plugins(hub: client.MeltanoHub) -> None:
    """Test get_sdk_plugins."""
    n = 10
    plugins = await hub.get_sdk_plugins(limit=n, plugin_type=api_schemas.PluginTypeOrAnyEnum.any)
    assert len(plugins) == n

    extractors = await hub.get_sdk_plugins(limit=n, plugin_type=api_schemas.PluginTypeOrAnyEnum.extractors)
    assert len(extractors) == n


@pytest.mark.asyncio
async def test_get_plugin_stats(hub: client.MeltanoHub) -> None:
    """Test get_plugin_stats."""
    stats = await hub.get_plugin_stats()
    assert stats


@pytest.mark.asyncio
async def test_get_maintainers(hub: client.MeltanoHub) -> None:
    """Test get_maintainers."""
    data = await hub.get_maintainers()
    assert len(data.maintainers) > 0


@pytest.mark.asyncio
async def test_get_maintainer(hub: client.MeltanoHub) -> None:
    """Test get_maintainer."""
    maintainer = await hub.get_maintainer("meltano")
    assert maintainer.id == "meltano"
    assert maintainer.label == "Meltano"
    assert str(maintainer.url) == "https://meltano.com/"
    assert len(maintainer.links) > 0


@pytest.mark.asyncio
async def test_get_maintainer_not_found(hub: client.MeltanoHub) -> None:
    """Test get_maintainer."""
    with pytest.raises(exceptions.NotFoundError):
        await hub.get_maintainer("unknown")


@pytest.mark.asyncio
async def test_get_top_maintainers(hub: client.MeltanoHub) -> None:
    """Test get_top_maintainers."""
    n = 10
    maintainers = await hub.get_top_maintainers(n)
    assert len(maintainers) == n


@pytest.mark.asyncio
async def test_get_default_variant_url(hub: client.MeltanoHub) -> None:
    """Test get_variant_url."""
    url = await hub.get_default_variant_url("extractors.tap-github")
    assert str(url).endswith("extractors/tap-github--meltanolabs")

    with pytest.raises(exceptions.NotFoundError):
        await hub.get_default_variant_url("unknown")
