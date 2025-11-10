
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_health(client: AsyncClient, session: AsyncSession) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
