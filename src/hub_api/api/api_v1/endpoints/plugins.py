"""Plugin endpoints."""

from __future__ import annotations

from typing import Annotated

import fastapi
import fastapi.responses
from pydantic import BaseModel, ConfigDict, Field

from hub_api import dependencies, enums, ids
from hub_api.helpers import compatibility
from hub_api.schemas import api as api_schemas

router = fastapi.APIRouter()


PluginTypeParam = Annotated[
    str,
    # enums.PluginTypeEnum,  # TODO: Schemathesis doesn't like constraints on path parameters
    fastapi.Path(
        ...,
        description="The plugin type",
        examples=[
            enums.PluginTypeEnum.extractors,
        ],
    ),
]

PluginNameParam = Annotated[
    str,
    fastapi.Path(
        ...,
        description="The plugin name",
        # pattern=r"^[A-Za-z0-9-]+$",  # TODO: Schemathesis doesn't like constraints on path parameters
        examples=[
            "tap-github",
        ],
    ),
]

PluginVariantParam = Annotated[
    str,
    fastapi.Path(
        ...,
        description="The plugin variant",
        # pattern=r"^[A-Za-z0-9-]+$",  # TODO: Schemathesis doesn't like constraints on path parameters
        examples=[
            "meltanolabs",
        ],
    ),
]


MeltanoVersion = Annotated[
    tuple[int, int],
    fastapi.Depends(compatibility.get_version_tuple),
]


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
    responses={
        400: {"description": "Not a valid plugin type"},
    },
)
async def get_type_index(hub: dependencies.Hub, plugin_type: PluginTypeParam) -> api_schemas.PluginTypeIndex:
    """Retrieve index of plugins of a given type."""
    return await hub.get_plugin_type_index(plugin_type=plugin_type)


@router.get(
    "/{plugin_type}/{plugin_name}/default",
    summary="Get the default plugin variant",
    responses={
        400: {"description": "Not a valid plugin type"},
        404: {"description": "Plugin not found"},
    },
)
async def get_default_plugin(
    hub: dependencies.Hub,
    plugin_type: PluginTypeParam,
    plugin_name: PluginNameParam,
) -> fastapi.responses.RedirectResponse:
    """Retrieve details of a plugin variant."""
    plugin_id = ids.PluginID.from_params(plugin_type=plugin_type, plugin_name=plugin_name)
    return fastapi.responses.RedirectResponse(url=await hub.get_default_variant_url(plugin_id))


@router.get(
    "/{plugin_type}/{plugin_name}--{plugin_variant}",
    response_model_exclude_none=True,
    summary="Get plugin variant",
    responses={
        400: {"description": "Not a valid plugin type"},
        404: {"description": "Plugin variant not found"},
    },
)
async def get_plugin_variant(
    hub: dependencies.Hub,
    plugin_type: PluginTypeParam,
    plugin_name: PluginNameParam,
    plugin_variant: PluginVariantParam,
    meltano_version: MeltanoVersion,
) -> (
    api_schemas.ExtractorResponse
    | api_schemas.LoaderResponse
    | api_schemas.UtilityResponse
    | api_schemas.OrchestratorResponse
    | api_schemas.TransformResponse
    | api_schemas.TransformerResponse
    | api_schemas.MapperResponse
    | api_schemas.FileResponse
):
    """Retrieve details of a plugin variant."""
    variant_id = ids.VariantID.from_params(
        plugin_type=plugin_type,
        plugin_name=plugin_name,
        plugin_variant=plugin_variant,
    )
    return await hub.get_plugin_details(variant_id, meltano_version=meltano_version)


class MadeWithSDKParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(
        25,
        ge=1,
        le=100,
        description="The number of plugins to return",
    )
    plugin_type: api_schemas.PluginTypeOrAnyEnum = Field(
        api_schemas.PluginTypeOrAnyEnum.any,
        description="The plugin type",
    )


@router.get("/made-with-sdk", summary="Get SDK plugins")
async def sdk(
    hub: dependencies.Hub,
    *,
    filter_query: Annotated[MadeWithSDKParams, fastapi.Query()],
) -> list[dict[str, str]]:
    """Retrieve plugins made with the Singer SDK."""
    return await hub.get_sdk_plugins(limit=filter_query.limit, plugin_type=filter_query.plugin_type)


@router.get("/stats", summary="Hub statistics")
async def stats(hub: dependencies.Hub) -> dict[enums.PluginTypeEnum, int]:
    """Retrieve Hub plugin statistics."""
    return await hub.get_plugin_stats()


__all__ = ["router"]
