from __future__ import annotations

import typing as t
import urllib.parse

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from hub_api import models
from hub_api.api.api_v1.schemas import PluginSetting

BASE_API_URL = "http://localhost:8000"
BASE_HUB_URL = "https://hub.meltano.com"


class PluginVariantNotFoundError(Exception):
    """Plugin variant not found error."""

    pass


def build_variant_url(
    *,
    base_url: str,
    plugin_type: models.PluginType,
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
    plugin_type: models.PluginType,
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

    async def get_plugin_details(self, variant_id: str) -> dict[str, t.Any]:
        v = await self.db.get(models.PluginVariant, variant_id)
        plugin: models.Plugin = await self.db.get(models.Plugin, v.plugin_id)
        settings: list[models.Setting] = await v.awaitable_attrs.settings
        capabilities: list[models.Capability] = await v.awaitable_attrs.capabilities

        result = {
            "capabilities": [c.name for c in capabilities],
            "description": v.description,
            "docs": build_hub_url(
                base_url=self.base_hub_url,
                plugin_type=plugin.plugin_type,
                plugin_name=plugin.name,
                plugin_variant=v.name,
            ),
            "label": v.label,
            "logo_url": urllib.parse.urljoin(self.base_hub_url, v.logo_url),
            "name": plugin.name,
            "namespace": v.namespace,
            "pip_url": v.pip_url,
            "repo": v.repo,
            "settings": [PluginSetting.model_validate(s, from_attributes=True) for s in settings],
            "settings_group_validation": [],  # TODO: Implement
            "variant": v.name,
        }

        match plugin.plugin_type:
            case models.PluginType.extractors:
                if select := await v.awaitable_attrs.select:
                    result["select"] = select
            case _:
                pass

        return result

    async def get_plugin_type_index(
        self: MeltanoHub,
        plugin_type: models.PluginType,
    ) -> dict[str, dict[str, t.Any]]:
        """Get all plugins of a given type.

        Args:
            plugin_type: Plugin type.

        Returns:
            Mapping of plugin name to variants.
        """
        aliased_plugin = aliased(models.PluginVariant, name="default_variant")
        q = (
            sa.select(
                models.Plugin.name,
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
            .where(models.Plugin.plugin_type == plugin_type)
        )

        result = await self.db.execute(q)
        return {
            plugin_name: {
                "default_variant": default_variant,
                "variants": {
                    variant_name: {
                        "ref": build_variant_url(
                            base_url=self.base_api_url,
                            plugin_type=plugin_type,
                            plugin_name=plugin_name,
                            plugin_variant=variant_name,
                        ),
                    },
                },
            }
            for plugin_name, variant_name, default_variant in result.all()
        }

    async def get_sdk_plugins(
        self: MeltanoHub,
        *,
        limit: int,
        plugin_type: models.PluginType | None,
    ) -> list[dict[str, t.Any]]:
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
        return result.mappings().all()

    async def get_plugin_stats(self: MeltanoHub) -> dict[models.PluginType, int]:
        """Get plugin statistics.

        Returns:
            Plugin statistics.
        """
        q = sa.select(
            models.Plugin.plugin_type,
            sa.func.count(models.Plugin.id),
        ).group_by(models.Plugin.plugin_type)

        result = await self.db.execute(q)
        return dict(result.all())
