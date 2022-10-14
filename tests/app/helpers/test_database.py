"""Test database helper functions."""

import pytest

from app.helpers.database import get_db


@pytest.mark.asyncio
async def test_get_db():
    """Test get_db."""
    db = yield await get_db()
    async with db.execute("SELECT * FROM foo") as cursor:
        assert await cursor.fetchall() == [{"bar": 42, "baz": "hello"}]
