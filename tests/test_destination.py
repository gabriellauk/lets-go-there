import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


@pytest.mark.asyncio
async def test_create_destination(client: AsyncClient, db_session: AsyncSession) -> None:
    request_body = {
        "name": "Alhambra",
        "description": "Granada, Spain",
        "imageId": "img_123",
        "notes": "A beautiful palace",
    }

    response = await client.post("/destination/", json=request_body)

    assert response.status_code == 200
    response_json = response.json()

    assert response_json.pop("id") is not None
    assert response_json == request_body

    db_objects = await db_session.execute(select(func.count()).select_from(models.Destination))
    assert db_objects.scalar() == 1


@pytest.mark.asyncio
async def test_get_destination(client: AsyncClient, db_session: AsyncSession) -> None:
    destination = models.Destination(
        name="Alhambra", description="Granada, Spain", image_id="img_123", notes="A beautiful palace"
    )
    db_session.add(destination)
    await db_session.commit()

    response = await client.get(f"/destination/{destination.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": destination.id,
        "name": destination.name,
        "description": destination.description,
        "imageId": destination.image_id,
        "notes": destination.notes,
    }

    db_objects = await db_session.execute(select(func.count()).select_from(models.Destination))
    assert db_objects.scalar() == 1


@pytest.mark.asyncio
async def test_get_destination_fails_doesnt_exist(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.get("/destination/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Destination not found"
