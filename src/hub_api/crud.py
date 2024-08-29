from __future__ import annotations

import collections
import typing as t
import urllib.parse

import sqlalchemy as sa
from sqlalchemy.orm import aliased

from . import enums, models, schemas

if t.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

BASE_API_URL = "http://localhost:8000"
BASE_HUB_URL = "https://hub.meltano.com"


class NotFoundError(Exception):
    """Not found error."""


class PluginVariantNotFoundError(NotFoundError):
    """Plugin variant not found error."""

    pass


def build_variant_url(
    *,
    base_url: str,
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
    return f"{base_url}{prefix}/{plugin_type.value}/{plugin_name}--{plugin_variant}"


def build_hub_url(
    *,
    base_url: str,
    plugin_type: enums.PluginTypeEnum,
    plugin_name: str,
    plugin_variant: str,
) -> str:
    """Build hub URL.

    Args:
        base_url: Base API URL.
        plugin_type: Plugin type.
        plugin_name: Plugin name.
        plugin_variant: Plugin variant

    Returns:
        Hub URL for the plugin.
    """
    return f"{base_url}/{plugin_type.value}/{plugin_name}--{plugin_variant}"


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

    async def get_plugin_details(self, variant_id: str) -> schemas.PluginDetails:  # noqa: C901
        v = await self.db.get(models.PluginVariant, variant_id)

        if not v:
            raise PluginVariantNotFoundError(f"Plugin variant {variant_id} not found")

        settings: list[models.Setting] = await v.awaitable_attrs.settings
        capabilities: list[models.Capability] = await v.awaitable_attrs.capabilities
        commands: list[models.Command] = await v.awaitable_attrs.commands

        settings_groups = collections.defaultdict(list)
        required_settings: list[models.RequiredSetting] = await v.awaitable_attrs.required_settings

        for required in required_settings:
            settings_groups[required.group_id].append(required.setting_name)

        result: dict[str, t.Any] = {
            "capabilities": [c.name for c in capabilities],
            "description": v.description,
            "executable": v.executable,
            "docs": build_hub_url(
                base_url=self.base_hub_url,
                plugin_type=v.plugin.plugin_type,
                plugin_name=v.plugin.name,
                plugin_variant=v.name,
            ),
            "label": v.label,
            "logo_url": urllib.parse.urljoin(self.base_hub_url, v.logo_url),
            "name": v.plugin.name,
            "namespace": v.namespace,
            "pip_url": v.pip_url,
            "repo": v.repo,
            "ext_repo": v.ext_repo,
            "settings": [schemas.PluginSetting.model_validate(s) for s in settings],
            "settings_group_validation": list(settings_groups.values()),
            "variant": v.name,
        }

        if commands:
            result["commands"] = {cmd.name: schemas.Command.model_validate(cmd) for cmd in commands}

        match v.plugin.plugin_type:
            case enums.PluginTypeEnum.extractors:
                if select := await v.awaitable_attrs.select:
                    result["select"] = select
                if metadata := await v.awaitable_attrs.extractor_metadata:
                    result["metadata"] = {m.key: m.value for m in metadata}
                return schemas.ExtractorDetails.model_validate(result)
            case enums.PluginTypeEnum.loaders:
                return schemas.LoaderDetails.model_validate(result)
            case enums.PluginTypeEnum.utilities:
                return schemas.UtilityDetails.model_validate(result)
            case enums.PluginTypeEnum.orchestrators:
                return schemas.OrchestrationDetails.model_validate(result)
            case enums.PluginTypeEnum.transforms:
                return schemas.TransformDetails.model_validate(result)
            case enums.PluginTypeEnum.transformers:
                return schemas.TransformerDetails.model_validate(result)
            case enums.PluginTypeEnum.mappers:
                return schemas.MapperDetails.model_validate(result)
            case enums.PluginTypeEnum.files:
                return schemas.FileDetails.model_validate(result)
            case _:
                raise ValueError(f"Unknown plugin type: {v.plugin.plugin_type}")

    async def _get_all_plugins(
        self: MeltanoHub,
        *,
        plugin_type: enums.PluginTypeEnum | None,
    ) -> t.Sequence[sa.Row[tuple[str, enums.PluginTypeEnum, str, str]]]:
        aliased_plugin = aliased(models.PluginVariant, name="default_variant")
        q = (
            sa.select(
                models.Plugin.name,
                models.Plugin.plugin_type,
                models.PluginVariant.name.label("variant"),
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

    async def get_plugin_index(self: MeltanoHub) -> schemas.PluginIndex:
        """Get all plugins.

        Returns:
            Mapping of plugin name to variants.
        """
        # plugins: dict[enums.PluginTypeEnum, dict[str, dict[str, t.Any]]] = collections.defaultdict(dict)
        plugins = schemas.PluginIndex(dict.fromkeys(enums.PluginTypeEnum, schemas.PluginTypeIndex({})))

        for row in await self._get_all_plugins(plugin_type=None):
            plugin_name, plugin_type, variant_name, default_variant = row._tuple()  # noqa: SLF001
            if plugin_name not in plugins[plugin_type]:
                plugins[plugin_type][plugin_name] = schemas.Plugin(default_variant=default_variant)

            plugins[plugin_type][plugin_name].variants[variant_name] = schemas.VariantReference(
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
    ) -> schemas.PluginTypeIndex:
        """Get all plugins of a given type.

        Args:
            plugin_type: Plugin type.

        Returns:
            Mapping of plugin name to variants.
        """
        plugins = schemas.PluginTypeIndex({})

        for row in await self._get_all_plugins(plugin_type=plugin_type):
            plugin_name, _, variant_name, default_variant = row._tuple()  # noqa: SLF001
            if plugin_name not in plugins:
                plugins[plugin_name] = schemas.Plugin(default_variant=default_variant)

            plugins[plugin_name].variants[variant_name] = schemas.VariantReference(
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
        plugin_type: enums.PluginTypeEnum | None,
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

        if plugin_type:
            q = q.where(models.Plugin.plugin_type == plugin_type)

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
