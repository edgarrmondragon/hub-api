"""Plugin endpoints."""

from __future__ import annotations

import enum
import json
from pathlib import Path

import aiofiles
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.api.api_v1.schemas import BasePluginDetails, PluginIndex
from app.helpers.database import get_db
from app.helpers.files import get_files


class PluginType(str, enum.Enum):
    """Plugin types."""

    EXTRACTORS = "extractors"
    LOADERS = "loaders"
    TRANSFORMERS = "transformers"
    UTILITIES = "utilities"
    TRANSFORMS = "transforms"
    ORCHESTRATORS = "orchestrators"
    MAPPERS = "mappers"
    FILES = "files"


router = APIRouter()


@router.get("/test-sqlite")
async def test_sqlite(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[aiosqlite.Row]:
    """Test sqlite."""
    async with db.execute("SELECT * FROM foo") as cursor:
        return list(await cursor.fetchall())


@router.get(
    "/{plugin_type}/index",
    summary="Get plugins",
    description="Get all plugins of a given type.",
    response_model=PluginIndex,
    responses={
        404: {
            "description": "Plugin type not found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                        },
                    },
                    "example": {
                        "detail": "Not found",
                    },
                },
            },
        },
    },
)
async def get_plugins(
    plugin_type: PluginType,
    plugin_files: Path = Depends(get_files),
) -> dict:
    """Get plugin definition."""
    filepath = plugin_files.joinpath(f"{plugin_type}/index")
    try:
        async with aiofiles.open(filepath) as f:
            return json.loads(await f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Plugin not found")


@router.get(
    "/{plugin_type}/{plugin_name}",
    summary="Get plugin definition",
    description="Get plugin settings, capabilities, and other metadata.",
    response_model=BasePluginDetails,
    responses={
        404: {
            "description": "Plugin not found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                        },
                    },
                    "example": {
                        "detail": "Not found",
                    },
                },
            },
        },
    },
)
async def get_plugin(
    plugin_type: PluginType,
    plugin_name: str,
    plugin_files: Path = Depends(get_files),
) -> dict:
    """Get plugin definition."""
    filepath = plugin_files.joinpath(f"{plugin_type}/{plugin_name}")
    try:
        async with aiofiles.open(filepath) as f:
            return json.loads(await f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Plugin not found")
