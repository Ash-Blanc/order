"""Shared fixtures for all tests"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from order.api import app
from order.core.store import store


@pytest_asyncio.fixture(autouse=True)
async def init_db(tmp_path, monkeypatch):
    """Use a fresh in-memory SQLite DB for each test."""
    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from order.core.store import Base

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    monkeypatch.setattr(store, "engine", engine)
    monkeypatch.setattr(store, "async_session", SessionLocal)

    yield

    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    """Return an async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
