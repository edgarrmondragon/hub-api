"""Maintainer endpoints."""

from __future__ import annotations

import fastapi

from hub_api import dependencies, schemas  # noqa: TCH001

router = fastapi.APIRouter()


@router.get(
    "/",
    summary="Get maintainers list",
    response_model_exclude_none=True,
)
async def get_maintainers(hub: dependencies.Hub) -> list[schemas.Maintainer]:
    """Retrieve global index of plugins."""
    return await hub.get_maintainers()


@router.get(
    "/top/{count}",
    summary="Get top plugin maintainers",
    response_model_exclude_none=True,
)
async def get_top_maintainers(hub: dependencies.Hub, count: int) -> list[schemas.MaintainerPluginCount]:
    """Retrieve top maintainers."""
    return await hub.get_top_maintainers(count)


@router.get(
    "/{maintainer}",
    summary="Get maintainer details",
    response_model_exclude_none=True,
)
async def get_maintainer(hub: dependencies.Hub, maintainer: str) -> schemas.MaintainerDetails:
    """Retrieve maintainer details."""
    return await hub.get_maintainer(maintainer)
