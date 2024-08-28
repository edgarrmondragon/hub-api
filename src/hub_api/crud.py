from __future__ import annotations

import typing as t

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from hub_api import models

BASE_URL = "http://localhost:8000"


class PluginVariantNotFoundError(Exception):
    """Plugin variant not found error."""

    pass


def build_variant_url(
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


class MeltanoHub:
    def __init__(self: MeltanoHub, db: AsyncSession) -> None:
        self.db = db

    async def get_plugin_details(self, variant_id: str) -> dict[str, t.Any]:
        v = await self.db.get(models.PluginVariant, variant_id)
        plugin: models.Plugin = await self.db.get(models.Plugin, v.plugin_id)
        settings: list[models.Setting] = await v.awaitable_attrs.settings
        capabilities: list[models.Capability] = await v.awaitable_attrs.capabilities
        keywords: list[models.Keyword] = await v.awaitable_attrs.keywords

        return {
            "name": plugin.name,
            "variant": v.name,
            "namespace": v.namespace,
            "repo": v.repo,
            "pip_url": v.pip_url,
            "settings": [
                {
                    "name": s.name,
                    "label": s.label,
                    "value": s.value,
                    "description": s.description,
                    "kind": s.kind,
                    "options": s.options,
                    "sensitive": s.sensitive,
                }
                for s in settings
            ],
            "capabilities": [c.name for c in capabilities],
            "keywords": [k.name for k in keywords],
        }

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
            row.name: {
                "default_variant": row.default_variant,
                "variants": {
                    row.variant: {
                        "ref": build_variant_url(
                            BASE_URL,
                            plugin_type,
                            row.name,
                            row.variant,
                        ),
                    },
                },
            }
            for row in result.all()
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
