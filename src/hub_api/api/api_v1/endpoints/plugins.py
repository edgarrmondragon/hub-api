"""Plugin endpoints."""

from __future__ import annotations

import typing as t

import fastapi

from hub_api import crud, enums, models, schemas

if t.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = fastapi.APIRouter()


@router.get(
    "/{plugin_type}/index",
    name="Get plugin index",
    response_model=schemas.PluginIndex,
    response_model_exclude_none=True,
)
async def get_index(plugin_type: enums.PluginTypeEnum) -> dict:
    """Retrieve index of plugins of a given type."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_plugin_type_index(plugin_type)


@router.get(
    "/{plugin_type}/{plugin_name}--{plugin_variant}",
    # response_model=BasePluginDetails,
    response_model_exclude_none=True,
)
async def get_plugin_variant(
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
        return await hub.get_plugin_details(variant_id)


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
