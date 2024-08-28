"""Plugin endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from hub_api import models
from hub_api.api.api_v1.schemas import BasePluginDetails, PluginIndex
from hub_api.crud import MeltanoHub

router = APIRouter()


@router.get(
    "/{plugin_type}/index",
    name="Get plugin index",
    response_model=PluginIndex,
    response_model_exclude_none=True,
)
async def get_index(plugin_type: models.PluginType) -> dict:
    """Retrieve index of plugins of a given type."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = MeltanoHub(db)
        return await hub.get_plugin_type_index(plugin_type)


@router.get(
    "/{plugin_type}/{plugin_name}--{plugin_variant}",
    response_model=BasePluginDetails,
    response_model_exclude_none=True,
)
async def get_plugin_variant(
    plugin_type: models.PluginType,
    plugin_name: str,
    plugin_variant: str,
) -> dict:
    """Retrieve details of a plugin variant."""
    plugin_id = f"{plugin_type.value}.{plugin_name}"
    variant_id = f"{plugin_id}.{plugin_variant}"

    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = MeltanoHub(db)
        plugin = await hub.get_plugin_variant(variant_id)
        settings = await hub.get_plugin_settings(variant_id)
        capabilities = await hub.get_plugin_capabilities(variant_id)
        keywords = await hub.get_plugin_keywords(variant_id)

        return {
            **plugin,
            "settings": settings,
            "capabilities": capabilities,
            "keywords": keywords,
        }


@router.get("/made-with-sdk", name="Get SDK plugins")
async def sdk(plugin_type: models.PluginType | None = None) -> list[dict[str, str]]:
    """Retrieve plugins made with the Singer SDK."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = MeltanoHub(db)
        return await hub.get_sdk_plugins(plugin_type=plugin_type)


@router.get("/stats", name="Hub statistics")
async def stats() -> dict[models.PluginType, int]:
    """Retrieve Hub plugin statistics."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = MeltanoHub(db)
        return await hub.get_plugin_stats()
