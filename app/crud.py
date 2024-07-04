from __future__ import annotations

import typing as t

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models import Capability, Keyword, Plugin, PluginType, PluginVariant, Setting

BASE_URL = "http://localhost:8000"


class PluginVariantNotFoundError(Exception):
    """Plugin variant not found error."""

    pass


def build_variant_url(
    base_url: str,
    plugin_type: PluginType,
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
    def __init__(self: MeltanoHub, session: AsyncSession) -> None:
        self.db_session = session

    async def get_plugin_type_index(
        self: MeltanoHub,
        plugin_type: PluginType,
    ) -> dict[str, dict[str, str]]:
        """Get all plugins of a given type.

        Args:
            plugin_type: Plugin type.

        Returns:
            Mapping of plugin name to variants.
        """
        aliased_plugin = aliased(PluginVariant, name="default_variant")
        q = (
            sa.select(
                Plugin.name,
                PluginVariant.name.label("variant"),
                aliased_plugin.name.label("default_variant"),
            )
            .join(Plugin, Plugin.id == PluginVariant.plugin_id)
            .join(
                aliased_plugin,
                sa.and_(
                    Plugin.default_variant_id == aliased_plugin.id,
                    Plugin.id == aliased_plugin.plugin_id,
                ),
            )
            .where(Plugin.plugin_type == plugin_type)
        )

        result = await self.db_session.execute(q)
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
                Plugin.name,
                PluginVariant.name.label("variant"),
                PluginVariant.repo,
                PluginVariant.pip_url,
                PluginVariant.namespace,
            )
            .join(Plugin, Plugin.id == PluginVariant.plugin_id)
            .where(PluginVariant.id == variant_id)
        )

        result = await self.db_session.execute(q)
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
            Setting.name,
            Setting.value,
            Setting.description,
            Setting.kind,
            Setting.options,
        ).where(Setting.variant_id == variant_id)

        result = await self.db_session.execute(q)
        return [row._asdict() for row in result.all()]

    async def get_plugin_capabilities(self: MeltanoHub, variant_id: str) -> list[str]:
        """Get all capabilities for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of capabilities.
        """
        q = sa.select(Capability.name).where(Capability.variant_id == variant_id)
        result = await self.db_session.execute(q)
        return result.scalars().all()

    async def get_plugin_keywords(self: MeltanoHub, variant_id: str) -> list[str]:
        """Get all keywords for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of keywords.
        """
        q = sa.select(Keyword.name).where(Keyword.variant_id == variant_id)
        result = await self.db_session.execute(q)
        return result.scalars().all()

    async def get_sdk_plugins(self: MeltanoHub) -> list[dict[str, t.Any]]:
        """Get all plugins with the sdk keyword.

        Returns:
            List of plugins.
        """
        q = (
            sa.select(
                Plugin.id,
                Plugin.name,
            )
            .join(
                PluginVariant,
                PluginVariant.plugin_id == Plugin.id,
            )
            .join(
                Keyword,
                sa.and_(
                    Keyword.variant_id == PluginVariant.id,
                    Keyword.name == "meltano_sdk",
                ),
            )
            .limit(100)
        )

        result = await self.db_session.execute(q)
        return result.mappings().all()
