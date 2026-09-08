import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import async_session_factory, engine, get_db_session


def test_async_session_factory_creates_async_session() -> None:
    session = async_session_factory()

    assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_get_db_session_yields_async_session() -> None:
    session_generator = get_db_session()
    session = await anext(session_generator)

    assert isinstance(session, AsyncSession)

    await session_generator.aclose()


@pytest.mark.asyncio
async def test_database_session_can_execute_query() -> None:
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError) as exc:
        pytest.skip(f"PostgreSQL is not available: {exc}")

    assert result.scalar_one() == 1
    await engine.dispose()