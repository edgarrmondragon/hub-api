from __future__ import annotations

import os
import pathlib

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_DEFAULT_DB_PATH = "./plugins.db"


def get_db_path() -> pathlib.Path:
    """Get database path."""
    return pathlib.Path(os.getenv("DB_PATH", _DEFAULT_DB_PATH)).resolve()


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get session maker."""
    engine = create_async_engine(
        f"sqlite+aiosqlite:///file:{get_db_path()}?mode=ro&uri=true",
        connect_args={"check_same_thread": False},
    )
    return async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
