from __future__ import annotations

import collections
import typing as t
import urllib.parse

import pydantic
import sqlalchemy as sa
from sqlalchemy.orm import aliased

from hub_api import enums, exceptions, models
from hub_api.schemas import api as api_schemas
from hub_api.schemas import meltano

if t.TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

BASE_API_URL = "http://127.0.0.1:8000"
BASE_HUB_URL = "https://hub.meltano.com"


class PluginVariantNotFoundError(exceptions.NotFoundError):
    """Plugin variant not found error."""

    pass


def _build_variant_path(
    *,
    plugin_type: enums.PluginTypeEnum,
    plugin_name: str,
    plugin_variant: str,
) -> str:
    """Build variant URL.

    Args:
        base_url: Base API URL.
        plugin_type: Plugin type.
        plugin_name: Plugin name.
        plugin_variant: Plugin variant.

    Returns:
        Variant URL.
    """
    prefix = "/meltano/api/v1/plugins"
    return f"{prefix}/{plugin_type.value}/{plugin_name}--{plugin_variant}"


def build_variant_url(
    *,
    base_url: str,
    plugin_type: enums.PluginTypeEnum,
    plugin_name: str,
    plugin_variant: str,
) -> pydantic.HttpUrl:
    """Build variant URL.

    Args:
        base_url: Base API URL.
        plugin_type: Plugin type.
        plugin_name: Plugin name.
        plugin_variant: Plugin variant.

    Returns:
        Variant URL.
    """
    path = _build_variant_path(
        plugin_type=plugin_type,
        plugin_name=plugin_name,
        plugin_variant=plugin_variant,
    )
    return pydantic.HttpUrl(f"{base_url}{path}")


def build_hub_url(
    *,
    base_url: str,
    plugin_type: enums.PluginTypeEnum,
    plugin_name: str,
    plugin_variant: str,
) -> pydantic.HttpUrl:
    """Build hub URL.

    Args:
        base_url: Base Hub URL.
        plugin_type: Plugin type.
        plugin_name: Plugin name.
        plugin_variant: Plugin variant

    Returns:
        Hub URL for the plugin.
    """
    return pydantic.HttpUrl(f"{base_url}/{plugin_type.value}/{plugin_name}--{plugin_variant}")


class MeltanoHub:
    def __init__(
        self: MeltanoHub,
        *,
        db: AsyncSession,
        base_api_url: str = BASE_API_URL,
        base_hub_url: str = BASE_HUB_URL,
    ) -> None:
        self.db = db
        self.base_api_url = base_api_url
        self.base_hub_url = base_hub_url

    async def _variant_details(  # noqa: C901, PLR0911, PLR0912
        self: MeltanoHub, variant: models.PluginVariant
    ) -> (
        api_schemas.ExtractorResponse
        | api_schemas.LoaderResponse
        | api_schemas.UtilityResponse
        | api_schemas.OrchestratorResponse
        | api_schemas.TransformResponse
        | api_schemas.TransformerResponse
        | api_schemas.MapperResponse
        | api_schemas.FileResponse
    ):
        settings: list[models.Setting] = await variant.awaitable_attrs.settings
        capabilities: list[models.Capability] = await variant.awaitable_attrs.capabilities
        commands: list[models.Command] = await variant.awaitable_attrs.commands

        settings_groups = collections.defaultdict(list)
        required_settings: list[models.RequiredSetting] = await variant.awaitable_attrs.required_settings

        for required in required_settings:
            settings_groups[required.group_id].append(required.setting_name)

        result: dict[str, t.Any] = {
            "description": variant.description,
            "executable": variant.executable,
            "docs": build_hub_url(
                base_url=self.base_hub_url,
                plugin_type=variant.plugin.plugin_type,
                plugin_name=variant.plugin.name,
                plugin_variant=variant.name,
            ),
            "label": variant.label,
            "logo_url": urllib.parse.urljoin(self.base_hub_url, variant.logo_url),
            "documentation": variant.docs,
            "name": variant.plugin.name,
            "namespace": variant.namespace,
            "pip_url": variant.pip_url,
            "repo": variant.repo,
            "ext_repo": variant.ext_repo,
            "settings": [meltano.PluginSetting.model_validate(s) for s in settings],
            "settings_group_validation": list(settings_groups.values()),
            "variant": variant.name,
        }

        if commands:
            result["commands"] = {cmd.name: meltano.Command.model_validate(cmd) for cmd in commands}

        match variant.plugin.plugin_type:
            case enums.PluginTypeEnum.extractors:
                result["capabilities"] = [c.name for c in capabilities]
                if select := await variant.awaitable_attrs.select:
                    result["select"] = [s.expression for s in select]
                if metadata := await variant.awaitable_attrs.extractor_metadata:
                    result["metadata"] = {m.key: m.value for m in metadata}
                return api_schemas.ExtractorResponse.model_validate(result)
            case enums.PluginTypeEnum.loaders:
                result["capabilities"] = [c.name for c in capabilities]
                return api_schemas.LoaderResponse.model_validate(result)
            case enums.PluginTypeEnum.utilities:
                return api_schemas.UtilityResponse.model_validate(result)
            case enums.PluginTypeEnum.orchestrators:
                return api_schemas.OrchestratorResponse.model_validate(result)
            case enums.PluginTypeEnum.transforms:
                return api_schemas.TransformResponse.model_validate(result)
            case enums.PluginTypeEnum.transformers:
                return api_schemas.TransformerResponse.model_validate(result)
            case enums.PluginTypeEnum.mappers:
                return api_schemas.MapperResponse.model_validate(result)
            case enums.PluginTypeEnum.files:
                return api_schemas.FileResponse.model_validate(result)
            case _:  # pragma: no cover
                raise ValueError(f"Unknown plugin type: {variant.plugin.plugin_type}")

    async def get_plugin_details(
        self, variant_id: str
    ) -> (
        api_schemas.ExtractorResponse
        | api_schemas.LoaderResponse
        | api_schemas.UtilityResponse
        | api_schemas.OrchestratorResponse
        | api_schemas.TransformResponse
        | api_schemas.TransformerResponse
        | api_schemas.MapperResponse
        | api_schemas.FileResponse
    ):
        variant = await self.db.get(models.PluginVariant, variant_id)

        if not variant:
            raise PluginVariantNotFoundError("Plugin variant not found")

        return await self._variant_details(variant)

    async def get_default_variant_url(self, plugin_id: str) -> str:
        q = (
            sa.select(
                models.Plugin,
                models.PluginVariant.name.label("variant"),
            )
            .join(
                models.PluginVariant,
                models.PluginVariant.id == models.Plugin.default_variant_id,
            )
            .where(models.PluginVariant.plugin_id == plugin_id)
        )
        if result := (await self.db.execute(q)).first():
            plugin, variant = result
            return _build_variant_path(
                plugin_type=plugin.plugin_type,
                plugin_name=plugin.name,
                plugin_variant=variant,
            )

        raise exceptions.NotFoundError("Plugin not found")

    async def _get_all_plugins(
        self: MeltanoHub,
        *,
        plugin_type: enums.PluginTypeEnum | None,
    ) -> Sequence[sa.Row[tuple[str, enums.PluginTypeEnum, str, str | None, str]]]:
        aliased_plugin = aliased(models.PluginVariant, name="default_variant")
        q = (
            sa.select(
                models.Plugin.name,
                models.Plugin.plugin_type,
                models.PluginVariant.name.label("variant"),
                models.PluginVariant.logo_url,
                aliased_plugin.name.label("default_variant"),
            )
            .join(models.Plugin, models.Plugin.id == models.PluginVariant.plugin_id)
            .join(
                aliased_plugin,
                sa.and_(
                    models.Plugin.default_variant_id == aliased_plugin.id,
                    models.Plugin.id == aliased_plugin.plugin_id,
                ),
            )
        )

        if plugin_type:
            q = q.where(models.Plugin.plugin_type == plugin_type)

        return (await self.db.execute(q)).all()

    async def get_plugin_index(self: MeltanoHub) -> api_schemas.PluginIndex:
        """Get all plugins.

        Returns:
            Mapping of plugin name to variants.
        """
        plugins: api_schemas.PluginIndex = {key: {} for key in enums.PluginTypeEnum}

        for row in await self._get_all_plugins(plugin_type=None):
            plugin_name, plugin_type, variant_name, logo_url, default_variant = row._tuple()  # noqa: SLF001
            logo_http_url = pydantic.HttpUrl(f"{self.base_hub_url}/assets{logo_url}") if logo_url else None
            if plugin_name not in plugins[plugin_type]:
                plugins[plugin_type][plugin_name] = api_schemas.PluginRef(
                    default_variant=default_variant,
                    logo_url=logo_http_url,
                )

            plugins[plugin_type][plugin_name].variants[variant_name] = api_schemas.VariantReference(
                ref=build_variant_url(
                    base_url=self.base_api_url,
                    plugin_type=plugin_type,
                    plugin_name=plugin_name,
                    plugin_variant=variant_name,
                ),
            )

        return plugins

    async def get_plugin_type_index(
        self: MeltanoHub,
        *,
        plugin_type: enums.PluginTypeEnum,
    ) -> api_schemas.PluginTypeIndex:
        """Get all plugins of a given type.

        Args:
            plugin_type: Plugin type.

        Returns:
            Mapping of plugin name to variants.
        """
        plugins: api_schemas.PluginTypeIndex = {}

        for row in await self._get_all_plugins(plugin_type=plugin_type):
            plugin_name, _, variant_name, logo_url, default_variant = row._tuple()  # noqa: SLF001
            logo_http_url = pydantic.HttpUrl(f"{self.base_hub_url}/assets{logo_url}") if logo_url else None
            if plugin_name not in plugins:
                plugins[plugin_name] = api_schemas.PluginRef(
                    default_variant=default_variant,
                    logo_url=logo_http_url,
                )

            plugins[plugin_name].variants[variant_name] = api_schemas.VariantReference(
                ref=build_variant_url(
                    base_url=self.base_api_url,
                    plugin_type=plugin_type,
                    plugin_name=plugin_name,
                    plugin_variant=variant_name,
                ),
            )

        return plugins

    async def get_sdk_plugins(
        self: MeltanoHub,
        *,
        limit: int,
        plugin_type: api_schemas.PluginTypeOrAnyEnum,
    ) -> list[dict[str, str]]:
        """Get all plugins with the sdk keyword.

        Returns:
            List of plugins.
        """
        q = sa.select(
            models.Plugin.id.label("plugin_id"),
            models.PluginVariant.id.label("variant_id"),
            models.PluginVariant.name.label("variant"),
        )

        if plugin_type != api_schemas.PluginTypeOrAnyEnum.any:
            q = q.where(models.Plugin.plugin_type == enums.PluginTypeEnum(plugin_type))

        q = (
            q.join(
                models.PluginVariant,
                models.PluginVariant.plugin_id == models.Plugin.id,
            )
            .join(
                models.Keyword,
                sa.and_(
                    models.Keyword.variant_id == models.PluginVariant.id,
                    models.Keyword.name == "meltano_sdk",
                ),
            )
            .limit(limit)
        )

        result = await self.db.execute(q)
        return [dict(row) for row in result.mappings().all()]

    async def get_plugin_stats(self: MeltanoHub) -> dict[enums.PluginTypeEnum, int]:
        """Get plugin statistics.

        Returns:
            Plugin statistics.
        """
        q = sa.select(
            models.Plugin.plugin_type,
            sa.func.count(models.Plugin.id),
        ).group_by(models.Plugin.plugin_type)

        result = await self.db.execute(q)
        return dict(row._tuple() for row in result.all())  # noqa: SLF001

    async def get_maintainers(self: MeltanoHub) -> api_schemas.MaintainersList:
        """Get maintainers.

        Returns:
            List of maintainers.
        """
        result = await self.db.execute(sa.select(models.Maintainer))
        return api_schemas.MaintainersList(
            maintainers=[api_schemas.Maintainer.model_validate(row) for row in result.scalars().all()],
        )

    async def get_maintainer(self: MeltanoHub, maintainer_id: str) -> api_schemas.MaintainerDetails:
        """Get maintainer, with links to plugins.

        Args:
            maintainer: Maintainer ID.

        Returns:
            Maintainer.
        """
        maintainer = await self.db.get(models.Maintainer, maintainer_id)
        if not maintainer:
            raise exceptions.NotFoundError(f"Maintainer {maintainer_id} not found")

        variants: list[models.PluginVariant] = await maintainer.awaitable_attrs.plugins

        return api_schemas.MaintainerDetails(
            id=maintainer.id,
            label=maintainer.label,
            url=pydantic.HttpUrl(maintainer.url) if maintainer.url else None,
            links={
                v.plugin.name: _build_variant_path(
                    plugin_type=v.plugin.plugin_type,
                    plugin_name=v.plugin.name,
                    plugin_variant=v.name,
                )
                for v in variants
            },
        )

    async def get_top_maintainers(self: MeltanoHub, n: int) -> list[api_schemas.MaintainerPluginCount]:
        """Get top maintainers.

        Returns:
            List of top maintainers.
        """
        q = (
            sa.select(
                models.Maintainer.id,
                models.Maintainer.label,
                models.Maintainer.url,
                sa.func.count(models.PluginVariant.id).label("plugin_count"),
            )
            .join(models.PluginVariant, models.PluginVariant.name == models.Maintainer.id)
            .group_by(models.Maintainer.id)
            .order_by(sa.desc("plugin_count"))
            .limit(n)
        )

        result = await self.db.execute(q)
        return [api_schemas.MaintainerPluginCount.model_validate(row) for row in result.all()]
