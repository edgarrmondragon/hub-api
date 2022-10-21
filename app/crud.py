from sqlalchemy import and_, select
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
    def __init__(self, session: AsyncSession):
        self.db_session = session

    async def get_plugin_type_index(self, plugin_type: PluginType):
        """Get all plugins of a given type.

        Args:
            plugin_type: Plugin type.

        Returns:
            Mapping of plugin name to variants.
        """
        AliasedPlugin = aliased(PluginVariant, name="default_variant")
        q = (
            select(
                Plugin.name,
                PluginVariant.name.label("variant"),
                AliasedPlugin.name.label("default_variant"),
            )
            .join(Plugin, Plugin.id == PluginVariant.plugin_id)
            .join(
                AliasedPlugin,
                and_(
                    Plugin.default_variant_id == AliasedPlugin.id,
                    Plugin.id == AliasedPlugin.plugin_id,
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
                        )
                    }
                },
            }
            for row in result.all()
        }

    async def get_plugin_variant(self, variant_id: str):
        """Get a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            Plugin variant.
        """
        q = (
            select(
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

    async def get_plugin_settings(self, variant_id: str):
        """Get all settings for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of settings.
        """
        q = select(
            Setting.name,
            Setting.value,
            Setting.description,
            Setting.kind,
        ).where(Setting.variant_id == variant_id)

        result = await self.db_session.execute(q)
        return [row._asdict() for row in result.all()]

    async def get_plugin_capabilities(self, variant_id: str):
        """Get all capabilities for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of capabilities.
        """
        q = select(Capability.name).where(Capability.variant_id == variant_id)
        result = await self.db_session.execute(q)
        return result.scalars().all()

    async def get_plugin_keywords(self, variant_id: str):
        """Get all keywords for a plugin variant.

        Args:
            variant_id: Plugin variant ID.

        Returns:
            List of keywords.
        """
        q = select(Keyword.name).where(Keyword.variant_id == variant_id)
        result = await self.db_session.execute(q)
        return result.scalars().all()

    async def get_sdk_plugins(self):
        """Get all plugins with the sdk keyword.

        Returns:
            List of plugins.
        """
        q = (
            select(
                Plugin.id,
                Plugin.name,
            )
            .join(
                PluginVariant,
                PluginVariant.plugin_id == Plugin.id,
            )
            .join(
                Keyword,
                and_(
                    Keyword.variant_id == PluginVariant.id,
                    Keyword.name == "meltano_sdk",
                ),
            )
            .limit(100)
        )

        result = await self.db_session.execute(q)
        return [row._asdict() for row in result.all()]
