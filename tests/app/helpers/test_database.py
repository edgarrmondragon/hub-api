"""Test database helper functions."""

from contextlib import asynccontextmanager

import pytest

from app.helpers.database import get_db


@pytest.mark.asyncio
async def test_db():
    """Test get_db."""
    _get_db = asynccontextmanager(get_db)
    async with _get_db() as db, db.execute("SELECT * FROM foo") as cursor:
        assert await cursor.fetchall() == [{"bar": 42, "baz": "hello"}]
