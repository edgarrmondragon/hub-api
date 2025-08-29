"""Test Hub data access."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hub_api import client, database, enums, ids, models
from hub_api.helpers import compatibility
from hub_api.schemas import api as api_schemas

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@pytest_asyncio.fixture
async def hub() -> AsyncGenerator[client.MeltanoHub]:
    """Get a Meltano hub instance."""
    session_maker = database.get_session_maker()
    async with session_maker() as db:
        yield client.MeltanoHub(db=db)


def test_plugin_id() -> None:
    """Test plugin ID."""
    plugin_id = ids.PluginID.from_params(plugin_type="extractors", plugin_name="tap-github")
    assert plugin_id.as_db_id() == "extractors.tap-github"


def test_plugin_id_invalid_type() -> None:
    """Test plugin ID."""
    with pytest.raises(ids.InvalidPluginTypeError):
        ids.PluginID.from_params(plugin_type="unknown", plugin_name="tap-github")


def test_variant_id() -> None:
    """Test variant ID."""
    variant_id = ids.VariantID.from_params(
        plugin_type="extractors",
        plugin_name="tap-github",
        plugin_variant="singer-io",
    )
    assert variant_id.as_db_id() == "extractors.tap-github.singer-io"


def test_variant_id_invalid_type() -> None:
    """Test variant ID."""
    with pytest.raises(ids.InvalidPluginTypeError):
        ids.VariantID.from_params(plugin_type="unknown", plugin_name="tap-github", plugin_variant="singer-io")


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
async def test_get_plugin_type_index_type_not_valid(hub: client.MeltanoHub) -> None:
    """Test get_plugin_type_index."""
    with pytest.raises(ids.InvalidPluginTypeError):
        await hub.get_plugin_type_index(plugin_type="unknown")


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
    variant_id = ids.VariantID.from_params(plugin_type=plugin_type, plugin_name=plugin, plugin_variant=variant)
    details = await hub.get_plugin_details(variant_id=variant_id)
    assert details.name == plugin
    assert details.variant == variant


@pytest.mark.asyncio
async def test_get_plugin_variant_not_found(hub: client.MeltanoHub) -> None:
    """Test get_plugin_details."""
    with pytest.raises(client.PluginVariantNotFoundError):
        await hub.get_plugin_details(
            variant_id=ids.VariantID.from_params(
                plugin_type="extractors",
                plugin_name="tap-github",
                plugin_variant="unknown",
            )
        )


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
    with pytest.raises(client.MaintainerNotFoundError):
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
    good_plugin_id = ids.PluginID.from_params(plugin_type="extractors", plugin_name="tap-github")
    url = await hub.get_default_variant_url(good_plugin_id)
    assert str(url).endswith("extractors/tap-github--meltanolabs")

    bad_plugin_id = ids.PluginID.from_params(plugin_type="extractors", plugin_name="unknown")
    with pytest.raises(client.PluginNotFoundError):
        await hub.get_default_variant_url(bad_plugin_id)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    """Get a database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
    async with session_maker() as session:
        conn = await session.connection()
        await conn.run_sync(models.EntityBase.metadata.create_all)
        session.add(
            models.Plugin(
                id="extractors.tap-mock",
                plugin_type="extractors",
                name="tap-mock",
                default_variant_id="tap-mock.singer",
            )
        )
        session.add(
            models.PluginVariant(
                id="extractors.tap-mock.singer",
                plugin_id="extractors.tap-mock",
                name="singer",
                namespace="tap_mock",
                repo="https://github.com/singer-io/tap-mock",
            ),
        )
        session.add_all([
            models.Setting(
                id="extractors.tap-mock.singer.setting_mock_string",
                variant_id="extractors.tap-mock.singer",
                name="mock_string",
                kind="string",
                sensitive=True,
            ),
            models.Setting(
                id="extractors.tap-mock.singer.setting_mock_integer",
                variant_id="extractors.tap-mock.singer",
                name="mock_integer",
                kind="integer",
            ),
            models.Setting(
                id="extractors.tap-mock.singer.setting_mock_decimal",
                variant_id="extractors.tap-mock.singer",
                name="mock_decimal",
                kind="decimal",
            ),
        ])
        session.add(
            models.SettingAlias(
                id="extractors.tap-mock.singer.setting_mock_string.alias_mock_string_alias",
                setting_id="extractors.tap-mock.singer.setting_mock_string",
                name="mock_string_alias",
            ),
        )
        await session.commit()
        yield session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("meltano_version", "settings_dict"),
    [
        pytest.param(
            compatibility.LATEST,
            {
                "mock_string": {
                    "aliases": ["mock_string_alias"],
                    "name": "mock_string",
                    "sensitive": True,
                    "kind": "string",
                },
                "mock_integer": {
                    "name": "mock_integer",
                    "kind": "integer",
                },
                "mock_decimal": {
                    "name": "mock_decimal",
                    "kind": "decimal",
                },
            },
            id="latest",
        ),
        pytest.param(
            (3, 2),
            {
                "mock_string": {
                    "aliases": ["mock_string_alias"],
                    "name": "mock_string",
                    "kind": "string",
                },
                "mock_integer": {
                    "name": "mock_integer",
                    "kind": "integer",
                },
                "mock_decimal": {
                    "name": "mock_decimal",
                    "kind": "integer",
                },
            },
            id="<3.3",
        ),
        pytest.param(
            (3, 5),
            {
                "mock_string": {
                    "aliases": ["mock_string_alias"],
                    "name": "mock_string",
                    "sensitive": True,
                    "kind": "string",
                },
                "mock_integer": {
                    "name": "mock_integer",
                    "kind": "integer",
                },
                "mock_decimal": {
                    "name": "mock_decimal",
                    "kind": "integer",
                },
            },
            id=">=3.3,<3.9",
        ),
        pytest.param(
            (3, 9),
            {
                "mock_string": {
                    "aliases": ["mock_string_alias"],
                    "name": "mock_string",
                    "sensitive": True,
                    "kind": "string",
                },
                "mock_integer": {
                    "name": "mock_integer",
                    "kind": "integer",
                },
                "mock_decimal": {
                    "name": "mock_decimal",
                    "kind": "decimal",
                },
            },
            id=">=3.9",
        ),
    ],
)
async def test_get_plugin_details_meltano_version(
    db: AsyncSession,
    meltano_version: tuple[int, int],
    settings_dict: dict[str, dict[str, Any]],
) -> None:
    """Test get_plugin_details."""
    hub = client.MeltanoHub(db=db)
    details = await hub.get_plugin_details(
        variant_id=ids.VariantID.from_params(
            plugin_type="extractors",
            plugin_name="tap-mock",
            plugin_variant="singer",
        ),
        meltano_version=meltano_version,
    )
    settings = {s.root.name: s.model_dump(exclude_none=True) for s in details.settings}
    checks = [settings[name] == s for name, s in settings_dict.items()]
    assert all(checks)
