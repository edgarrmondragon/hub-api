"""Database helper functions."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import aiosqlite


def dict_factory(cursor: aiosqlite.Cursor, row: tuple) -> dict:
    """Convert a row to a dict.

    This is used as a row_factory for aiosqlite.

    Args:
        cursor: The cursor.
        row: The row.

    Returns:
        The row as a dict.
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get a connection to the database.

    This is used as a dependency for FastAPI.

    Yields:
        A connection to the database.
    """
    database_uri = os.getenv("DATABASE_URI", ":memory:")
    db = await aiosqlite.connect(database_uri)
    db.row_factory = dict_factory  # type: ignore

    await db.commit()
    try:
        yield db
    finally:
        await db.close()
