"""Maintainer endpoints."""

from __future__ import annotations

import typing as t

import fastapi

from hub_api import crud, models, schemas

if t.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = fastapi.APIRouter()


@router.get(
    "/",
    name="Get maintainers list",
    response_model_exclude_none=True,
)
async def get_maintainers() -> list[schemas.Maintainer]:
    """Retrieve global index of plugins."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_maintainers()


@router.get(
    "/top/{count}",
    name="Get top plugin maintainers",
    response_model_exclude_none=True,
)
async def get_top_maintainers(count: int) -> list[schemas.MaintainerPluginCount]:
    """Retrieve top maintainers."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_top_maintainers(count)


@router.get(
    "/{maintainer}",
    name="Get maintainer details",
    response_model_exclude_none=True,
)
async def get_maintainer(maintainer: str) -> schemas.MaintainerDetails:
    """Retrieve maintainer details."""
    db: AsyncSession
    async with models.SessionLocal() as db:
        hub = crud.MeltanoHub(db=db)
        return await hub.get_maintainer(maintainer)
