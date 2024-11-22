"""Plugin endpoints."""

from __future__ import annotations

import typing as t

import fastapi
import fastapi.responses

from hub_api import dependencies, enums  # noqa: TC001
from hub_api.schemas import api as api_schemas  # noqa: TC001

router = fastapi.APIRouter()


@router.get(
    "/index",
    summary="Get plugin index",
    response_model_exclude_none=True,
)
async def get_index(hub: dependencies.Hub) -> api_schemas.PluginIndex:
    """Retrieve global index of plugins."""
    return await hub.get_plugin_index()


@router.get(
    "/{plugin_type}/index",
    summary="Get plugin type index",
    response_model_exclude_none=True,
)
async def get_type_index(
    hub: dependencies.Hub,
    plugin_type: t.Annotated[
        enums.PluginTypeEnum,
        fastapi.Path(
            ...,
            description="The plugin type",
        ),
    ],
) -> api_schemas.PluginTypeIndex:
    """Retrieve index of plugins of a given type."""
    return await hub.get_plugin_type_index(plugin_type=plugin_type)


@router.get(
    "/{plugin_type}/{plugin_name}/default",
    status_code=fastapi.status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Get the default plugin variant",
    responses={
        404: {"description": "Plugin not found"},
    },
)
async def get_default_plugin(
    hub: dependencies.Hub,
    plugin_type: t.Annotated[
        enums.PluginTypeEnum,
        fastapi.Path(
            ...,
            description="The plugin type",
        ),
    ],
    plugin_name: t.Annotated[
        str,
        fastapi.Path(
            ...,
            description="The plugin name",
            pattern=r"^[A-Za-z0-9-]+$",
        ),
    ],
) -> fastapi.responses.RedirectResponse:
    """Retrieve details of a plugin variant."""
    plugin_id = f"{plugin_type.value}.{plugin_name}"
    return fastapi.responses.RedirectResponse(url=str(await hub.get_default_variant_url(plugin_id)))


@router.get(
    "/{plugin_type}/{plugin_name}--{plugin_variant}",
    response_model_exclude_none=True,
    summary="Get plugin variant",
    responses={
        404: {"description": "Plugin variant not found"},
    },
)
async def get_plugin_variant(
    hub: dependencies.Hub,
    plugin_type: enums.PluginTypeEnum,
    plugin_name: t.Annotated[
        str,
        fastapi.Path(
            ...,
            description="The plugin name",
            pattern=r"^[A-Za-z0-9-]+$",
        ),
    ],
    plugin_variant: t.Annotated[
        str,
        fastapi.Path(
            ...,
            description="The plugin variant",
            pattern=r"^[A-Za-z0-9-]+$",
        ),
    ],
) -> api_schemas.PluginResponse:
    """Retrieve details of a plugin variant."""
    plugin_id = f"{plugin_type.value}.{plugin_name}"
    variant_id = f"{plugin_id}.{plugin_variant}"
    return await hub.get_plugin_details(variant_id)


@router.get("/made-with-sdk", summary="Get SDK plugins")
async def sdk(
    hub: dependencies.Hub,
    *,
    limit: t.Annotated[
        int,
        fastapi.Query(
            ...,
            ge=1,
            le=100,
            description="The number of plugins to return",
        ),
    ] = 25,
    plugin_type: enums.PluginTypeEnum | None = None,
) -> list[dict[str, str]]:
    """Retrieve plugins made with the Singer SDK."""
    return await hub.get_sdk_plugins(limit=limit, plugin_type=plugin_type)


@router.get("/stats", summary="Hub statistics")
async def stats(hub: dependencies.Hub) -> dict[enums.PluginTypeEnum, int]:
    """Retrieve Hub plugin statistics."""
    return await hub.get_plugin_stats()


__all__ = ["router"]
