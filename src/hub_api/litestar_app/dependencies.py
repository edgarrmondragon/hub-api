"""Litestar app dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hub_api import client, database

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def get_hub() -> AsyncGenerator[client.MeltanoHub]:
    """Get a Meltano hub instance."""
    session_maker = database.get_session_maker()
    async with session_maker() as db:
        yield client.MeltanoHub(db=db)
