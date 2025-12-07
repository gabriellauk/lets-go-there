import pytest
from httpx import AsyncClient
from pytest import FixtureRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.schemas.enums import TravelIdeaGroupRole
from tests.factory import create_travel_idea_group


async def _create_single_travel_idea(
    db_session: AsyncSession, user: models.UserAccount, role: TravelIdeaGroupRole | None = None
) -> tuple[models.TravelIdea, models.TravelIdeaGroup]:
    travel_idea_group, members, _ = await create_travel_idea_group(db_session, user, current_user_role=role)
    travel_idea = models.TravelIdea(
        name="Alhambra",
        image_url="img_123",
        notes="A beautiful palace",
        created_by=members[1],
        travel_idea_group=travel_idea_group,
    )
    db_session.add(travel_idea)

    await db_session.commit()
    return travel_idea, travel_idea_group


async def _create_multiple_travel_ideas(
    db_session: AsyncSession, user: models.UserAccount, role: TravelIdeaGroupRole | None = None
) -> tuple[list[models.TravelIdea], models.TravelIdeaGroup]:
    travel_idea_group, members, _ = await create_travel_idea_group(db_session, user, current_user_role=role)
    travel_idea = models.TravelIdea(
        name="Alhambra",
        image_url="img_123",
        notes="A beautiful palace",
        created_by=members[1],
        travel_idea_group=travel_idea_group,
    )
    db_session.add(travel_idea)

    extra_travel_idea = models.TravelIdea(
        name="Vancouver",
        image_url="img_456",
        created_by=members[0],
        travel_idea_group=travel_idea_group,
    )

    other_travel_idea_group, _, _ = await create_travel_idea_group(
        db_session, user, current_user_role=role, name_prefix="other"
    )
    other_travel_idea = models.TravelIdea(
        name="Vilnius",
        image_url="img_789",
        created_by=user,
        travel_idea_group=other_travel_idea_group,
    )

    db_session.add_all([extra_travel_idea, other_travel_idea_group, other_travel_idea])
    await db_session.commit()
    return [travel_idea, extra_travel_idea], travel_idea_group


@pytest.mark.asyncio
async def test_create_travel_idea_fails_travel_idea_group_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post(
        "/travel-idea-group/404/travel-idea/", json={"name": "Alhambra", "imageUrl": "img_123"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_create_travel_idea_fails_not_a_member(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await create_travel_idea_group(db_session, user)

    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/", json={"name": "Alhambra", "imageUrl": "img_123"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to access this travel idea group"


@pytest.mark.asyncio
async def test_create_travel_idea_fails_missing_mandatory_fields(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/", json={"notes": "Something noteworthy"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_travel_idea(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    request_body = {
        "name": "Alhambra",
        "imageUrl": "img_123",
        "notes": "A beautiful palace",
    }

    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/", json=request_body
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json.pop("id") is not None
    assert response_json == request_body

    result = await db_session.execute(select(models.TravelIdea))
    travel_idea = result.scalars().one()
    assert travel_idea.travel_idea_group == travel_idea_group
    assert travel_idea.created_by == user
    assert travel_idea.name == request_body["name"]
    assert travel_idea.image_url == request_body["imageUrl"]
    assert travel_idea.notes == request_body["notes"]


@pytest.mark.asyncio
async def test_get_travel_idea_fails_travel_idea_group_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/travel-idea-group/404/travel-idea/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_get_travel_idea_fails_travel_idea_doesnt_exist(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/travel-idea/404")

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea not found"


@pytest.mark.asyncio
async def test_get_travel_idea_fails_not_a_member(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    _, travel_idea_group = await _create_single_travel_idea(db_session, user)

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/travel-idea/404")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to access this travel idea group"


@pytest.mark.asyncio
async def test_get_travel_idea(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea, travel_idea_group = await _create_single_travel_idea(db_session, user, TravelIdeaGroupRole.MEMBER)

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/travel-idea/{travel_idea.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": travel_idea.id,
        "name": travel_idea.name,
        "imageUrl": travel_idea.image_url,
        "notes": travel_idea.notes,
    }


@pytest.mark.asyncio
async def test_get_travel_ideas_fails_travel_idea_group_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/travel-idea-group/404/travel-idea/")

    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_get_travel_ideas_fails_not_a_member(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    _, travel_idea_group = await _create_multiple_travel_ideas(db_session, user)

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/travel-idea/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to access this travel idea group"


@pytest.mark.asyncio
async def test_get_travel_ideas_empty_list(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/travel-idea/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_travel_ideas(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_ideas, travel_idea_group = await _create_multiple_travel_ideas(db_session, user, TravelIdeaGroupRole.MEMBER)

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/travel-idea/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": travel_ideas[0].id,
            "name": travel_ideas[0].name,
            "imageUrl": travel_ideas[0].image_url,
            "notes": travel_ideas[0].notes,
        },
        {
            "id": travel_ideas[1].id,
            "name": travel_ideas[1].name,
            "imageUrl": travel_ideas[1].image_url,
            "notes": travel_ideas[1].notes,
        },
    ]


@pytest.mark.asyncio
async def test_update_travel_idea_fails_travel_idea_group_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.patch("/travel-idea-group/404/travel-idea/1", json={"notes": "New notes"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_update_travel_idea_fails_not_a_member(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea, travel_idea_group = await _create_single_travel_idea(db_session, user)

    response = await authenticated_client.patch(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/{travel_idea.id}", json={"notes": "New notes"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to access this travel idea group"


@pytest.mark.asyncio
async def test_update_travel_idea_fails_travel_idea_doesnt_exist(
    authenticated_client: AsyncClient, db_session: AsyncSession, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.patch(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/1", json={"notes": "New notes"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea not found"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"name": None}, id="remove_name_null"),
        pytest.param({"name": ""}, id="remove_name_empty_str"),
        pytest.param({"imageUrl": None}, id="remove_image_url_null"),
        pytest.param({"imageUrl": ""}, id="remove_image_url_empty_str"),
    ],
)
@pytest.mark.asyncio
async def test_update_travel_idea_fails_mandatory_fields_unset(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
    payload: dict[str, str],
) -> None:
    travel_idea, travel_idea_group = await _create_single_travel_idea(db_session, user, TravelIdeaGroupRole.MEMBER)
    travel_idea_id = travel_idea.id

    response = await authenticated_client.patch(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/{travel_idea_id}", json=payload
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, If field is set, it cannot be null"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"notes": "New notes", "name": "new name", "imageUrl": "new URL"}, id="new_strings_all_fields"),
        pytest.param({"notes": ""}, id="remove_notes_empty_str"),
        pytest.param({"notes": None}, id="remove_notes_null"),
        pytest.param({"name": "new name"}, id="new_string_one_field"),
    ],
)
@pytest.mark.asyncio
async def test_update_travel_idea(
    request: FixtureRequest,
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
    payload: dict[str, str],
) -> None:
    travel_idea, travel_idea_group = await _create_single_travel_idea(db_session, user, TravelIdeaGroupRole.MEMBER)
    travel_idea_id = travel_idea.id

    response = await authenticated_client.patch(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/{travel_idea_id}", json=payload
    )

    assert response.status_code == 200
    response_json = response.json()
    response_json.pop("id")

    db_session.expire_all()
    await db_session.get(models.TravelIdea, travel_idea_id)

    response_when_notes_removed = {"name": "Alhambra", "imageUrl": "img_123", "notes": None}

    test_id = request.node.name.split("[")[1].rstrip("]")
    match test_id:
        case "new_strings_all_fields":
            assert response_json == payload
        case "remove_notes_empty_str":
            assert response_json == response_when_notes_removed
            assert travel_idea.notes is None
        case "remove_notes_null":
            assert response_json == response_when_notes_removed
            assert travel_idea.notes is None
        case "new_string_one_field":
            assert response_json == {"name": "new name", "imageUrl": "img_123", "notes": "A beautiful palace"}
        case _:
            pytest.fail(f"Unhandled scenario - the result of '{test_id}' should be checked")


@pytest.mark.asyncio
async def test_delete_travel_idea_fails_travel_idea_group_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.delete("/travel-idea-group/404/travel-idea/1")
    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_delete_travel_idea_fails_not_a_member(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea, travel_idea_group = await _create_single_travel_idea(db_session, user)

    response = await authenticated_client.delete(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/{travel_idea.id}"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to access this travel idea group"


@pytest.mark.asyncio
async def test_delete_travel_idea_fails_travel_idea_doesnt_exist(
    authenticated_client: AsyncClient, db_session: AsyncSession, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.delete(f"/travel-idea-group/{travel_idea_group.id}/travel-idea/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea not found"


@pytest.mark.asyncio
async def test_delete_travel_idea(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea, travel_idea_group = await _create_single_travel_idea(db_session, user, TravelIdeaGroupRole.MEMBER)
    travel_idea_id = travel_idea.id

    response = await authenticated_client.delete(
        f"/travel-idea-group/{travel_idea_group.id}/travel-idea/{travel_idea_id}"
    )

    assert response.status_code == 204
    db_session.expire_all()
    updated_travel_idea = await db_session.get(models.TravelIdea, travel_idea_id)
    assert updated_travel_idea is None
