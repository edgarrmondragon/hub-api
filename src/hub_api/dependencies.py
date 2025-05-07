"""Generic FastAPI dependencies for the Meltano hub API."""

from __future__ import annotations

import typing as t

import fastapi

from hub_api import client, database

if t.TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def get_hub() -> AsyncGenerator[client.MeltanoHub]:
    """Get a Meltano hub instance."""
    session_maker = database.get_session_maker()
    async with session_maker() as db:
        yield client.MeltanoHub(db=db)


Hub = t.Annotated[client.MeltanoHub, fastapi.Depends(get_hub)]
