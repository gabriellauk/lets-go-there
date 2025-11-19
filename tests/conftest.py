from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.database.init_db import Base
from app.main import app
from app.models.user_account import UserAccount

# Async engine and sessionmaker using in-memory SQLite for tests
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    echo=False,
)

TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_db() -> AsyncGenerator[AsyncSession]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    # Provide a clean session for each test

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    # Override dependency to use test session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    # Remove the override after test completes
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def user(db_session: AsyncSession) -> None:
    password_hash = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
    user_account = UserAccount(email="somebody@somewhere.com", password_hash=password_hash, name="Somebody")
    db_session.add(user_account)
    await db_session.commit()
    return user_account


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(db_session: AsyncSession, user: UserAccount) -> AsyncGenerator[AsyncClient]:
    # Override dependency to use test session
    app.dependency_overrides[get_db] = override_get_db

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", headers={"authorization": f"Bearer {access_token}"}
    ) as client:
        yield client

    # Remove the override after test completes
    app.dependency_overrides.clear()
