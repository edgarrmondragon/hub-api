"""Plugin endpoints."""

from __future__ import annotations

import fastapi

from hub_api import dependencies, enums, schemas  # noqa: TCH001

router = fastapi.APIRouter()


@router.get(
    "/index",
    summary="Get plugin index",
    response_model_exclude_none=True,
)
async def get_index(hub: dependencies.Hub) -> schemas.PluginIndex:
    """Retrieve global index of plugins."""
    return await hub.get_plugin_index()


@router.get(
    "/{plugin_type}/index",
    summary="Get plugin type index",
    response_model_exclude_none=True,
)
async def get_type_index(hub: dependencies.Hub, plugin_type: enums.PluginTypeEnum) -> schemas.PluginTypeIndex:
    """Retrieve index of plugins of a given type."""
    return await hub.get_plugin_type_index(plugin_type=plugin_type)


@router.get(
    "/{plugin_type}/{plugin_name}--{plugin_variant}",
    response_model_exclude_none=True,
    summary="Get plugin variant",
)
async def get_plugin_variant(
    hub: dependencies.Hub,
    plugin_type: enums.PluginTypeEnum,
    plugin_name: str,
    plugin_variant: str,
) -> schemas.PluginDetails:
    """Retrieve details of a plugin variant."""
    plugin_id = f"{plugin_type.value}.{plugin_name}"
    variant_id = f"{plugin_id}.{plugin_variant}"
    return await hub.get_plugin_details(variant_id)


@router.get("/made-with-sdk", summary="Get SDK plugins")
async def sdk(
    hub: dependencies.Hub,
    *,
    limit: int = 100,
    plugin_type: enums.PluginTypeEnum | None = None,
) -> list[dict[str, str]]:
    """Retrieve plugins made with the Singer SDK."""
    return await hub.get_sdk_plugins(limit=limit, plugin_type=plugin_type)


@router.get("/stats", summary="Hub statistics")
async def stats(hub: dependencies.Hub) -> dict[enums.PluginTypeEnum, int]:
    """Retrieve Hub plugin statistics."""
    return await hub.get_plugin_stats()


__all__ = ["router"]
