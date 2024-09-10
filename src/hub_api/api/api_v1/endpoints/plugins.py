"""Plugin endpoints."""

from __future__ import annotations

import contextlib
import logging
import typing as t

import cachetools
import fastapi

from hub_api import crud, enums, models, schemas

if t.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("uvicorn.error")
router = fastapi.APIRouter()


@router.get(
    "/index",
    name="Get plugin index",
    response_model_exclude_none=True,
)
async def get_index() -> schemas.PluginIndex:
    """Retrieve global index of plugins."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_plugin_index()


@router.get(
    "/{plugin_type}/index",
    name="Get plugin type index",
    response_model_exclude_none=True,
)
async def get_type_index(plugin_type: enums.PluginTypeEnum) -> schemas.PluginTypeIndex:
    """Retrieve index of plugins of a given type."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_plugin_type_index(plugin_type=plugin_type)


plugin_details_response: cachetools.TTLCache[str, schemas.PluginDetails] = cachetools.TTLCache(
    maxsize=10,
    ttl=30,
)


@router.get(
    "/{plugin_type}/{plugin_name}--{plugin_variant}",
    response_model_exclude_none=True,
)
async def get_plugin_variant(
    response: fastapi.Response,
    plugin_type: enums.PluginTypeEnum,
    plugin_name: str,
    plugin_variant: str,
) -> schemas.PluginDetails:
    """Retrieve details of a plugin variant."""
    plugin_id = f"{plugin_type.value}.{plugin_name}"
    variant_id = f"{plugin_id}.{plugin_variant}"

    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        plugin_details_response.expire()
        with contextlib.suppress(KeyError):
            return plugin_details_response[variant_id]

        plugin_details = await hub.get_plugin_details(variant_id)
        plugin_details_response[variant_id] = plugin_details
        response.headers["Cache-Control"] = "max-age=30"

        return plugin_details


@router.get("/made-with-sdk", name="Get SDK plugins")
async def sdk(
    *,
    limit: int = 100,
    plugin_type: enums.PluginTypeEnum | None = None,
) -> list[dict[str, str]]:
    """Retrieve plugins made with the Singer SDK."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_sdk_plugins(limit=limit, plugin_type=plugin_type)


@router.get("/stats", name="Hub statistics")
async def stats() -> dict[enums.PluginTypeEnum, int]:
    """Retrieve Hub plugin statistics."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_plugin_stats()


__all__ = ["router"]
