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

    async def get_plugin_variant(self: MeltanoHub, variant_id: str) -> dict[str, t.Any]:
        """Get a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            Plugin variant.
        """
        q = (
            sa.select(
                models.Plugin.name,
                models.PluginVariant.name.label("variant"),
                models.PluginVariant.repo,
                models.PluginVariant.pip_url,
                models.PluginVariant.namespace,
            )
            .join(models.Plugin, models.Plugin.id == models.PluginVariant.plugin_id)
            .where(models.PluginVariant.id == variant_id)
        )

        result = await self.db.execute(q)
        variant = result.one_or_none()

        if not variant:
            raise PluginVariantNotFoundError("Plugin variant not found")

        return variant._asdict()

    async def get_plugin_settings(
        self: MeltanoHub,
        variant_id: str,
    ) -> list[dict[str, t.Any]]:
        """Get all settings for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of settings.
        """
        q = sa.select(
            models.Setting.name,
            models.Setting.label,
            models.Setting.value,
            models.Setting.description,
            models.Setting.kind,
            models.Setting.options,
            models.Setting.sensitive,
        ).where(models.Setting.variant_id == variant_id)

        result = await self.db.execute(q)
        return [row._asdict() for row in result.all()]

    async def get_plugin_capabilities(self: MeltanoHub, variant_id: str) -> list[str]:
        """Get all capabilities for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of capabilities.
        """
        q = sa.select(models.Capability.name).where(
            models.Capability.variant_id == variant_id
        )
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_plugin_keywords(self: MeltanoHub, variant_id: str) -> list[str]:
        """Get all keywords for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of keywords.
        """
        q = sa.select(models.Keyword.name).where(
            models.Keyword.variant_id == variant_id
        )
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_sdk_plugins(
        self: MeltanoHub,
        *,
        plugin_type: models.PluginType | None = None,
        limit: int = 100,
    ) -> list[dict[str, t.Any]]:
        """Get all plugins with the sdk keyword.

        Returns:
            List of plugins.
        """
        q = sa.select(models.Plugin.id, models.Plugin.name)

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
