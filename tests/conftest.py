import asyncio
from collections.abc import AsyncGenerator, Iterator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession]:
    """Create a fresh database session for each test"""
    async for session in get_db():
        yield session


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient]:
    """Create a new client for each test"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
