import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.models import TravelIdeaGroup


@pytest.mark.asyncio
async def test_create_travel_idea(
    authenticated_client: AsyncClient, db_session: AsyncSession, travel_idea_group: TravelIdeaGroup
) -> None:
    request_body = {
        "name": "Alhambra",
        "imageUrl": "img_123",
        "notes": "A beautiful palace",
    }

    response = await authenticated_client.post("/travel-idea/", json=request_body)

    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json.pop("id") is not None
    assert response_json == request_body

    db_objects = await db_session.execute(select(func.count()).select_from(models.TravelIdea))
    assert db_objects.scalar() == 1


@pytest.mark.asyncio
async def test_get_travel_idea(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
    travel_idea_group: TravelIdeaGroup,
) -> None:
    travel_idea = models.TravelIdea(
        name="Alhambra",
        image_url="img_123",
        notes="A beautiful palace",
        created_by=user,
        travel_idea_group=travel_idea_group,
    )
    db_session.add(travel_idea)
    await db_session.commit()

    response = await authenticated_client.get(f"/travel-idea/{travel_idea.id}")

    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": travel_idea.id,
        "name": travel_idea.name,
        "imageUrl": travel_idea.image_url,
        "notes": travel_idea.notes,
    }

    db_objects = await db_session.execute(select(func.count()).select_from(models.TravelIdea))
    assert db_objects.scalar() == 1


@pytest.mark.asyncio
async def test_get_travel_idea_fails_doesnt_exist(authenticated_client: AsyncClient, db_session: AsyncSession) -> None:
    response = await authenticated_client.get("/travel-idea/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea not found"
