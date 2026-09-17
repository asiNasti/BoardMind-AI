import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


database_user = os.getenv("POSTGRES_USER", "boardmind")
database_password = os.getenv("POSTGRES_PASSWORD", "boardmind")
database_name = os.getenv("POSTGRES_DB", "boardmind")
os.environ["DATABASE_URL"] = (
    f"postgresql+asyncpg://{database_user}:{database_password}@localhost:5432/{database_name}"
)

from backend.app.db.base import Base
from backend.app.db.database import async_session_factory, engine


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
    except (SQLAlchemyError, OSError):
        pytest.skip("PostgreSQL is not available")

    try:
        async with async_session_factory() as session:
            yield session
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()
