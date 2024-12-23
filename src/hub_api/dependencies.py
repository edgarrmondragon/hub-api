"""Generic FastAPI dependencies for the Meltano hub API."""

from __future__ import annotations

import typing as t

import fastapi

from hub_api import crud, models


async def get_hub() -> t.AsyncGenerator[crud.MeltanoHub]:
    """Get a Meltano hub instance."""
    async with models.SessionLocal() as db:
        yield crud.MeltanoHub(db=db)


Hub = t.Annotated[crud.MeltanoHub, fastapi.Depends(get_hub)]
