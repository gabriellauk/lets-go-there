from typing import Literal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.models.travel_idea_group import TravelIdeaGroup
from tests.factory import create_user_accounts


async def _create_travel_idea_group(
    db_session: AsyncSession,
    current_user: models.UserAccount,
    current_user_role: Literal["owner", "member"] | None = None,
    name_prefix: str = "default",
) -> tuple[models.TravelIdeaGroup, list[models.UserAccount], models.UserAccount]:
    users = await create_user_accounts(db_session, 3, name_prefix)

    if current_user_role == "owner":
        owner = current_user
        users_to_make_members = [users[0], users[2]]
    elif current_user_role == "member":
        owner = users[1]
        users_to_make_members = [current_user, users[2]]
    else:
        owner = users[1]
        users_to_make_members = [users[0], users[2]]

    travel_idea_group = models.TravelIdeaGroup(
        name=f"{name_prefix} Our travel bucket list",
        owned_by=owner,
    )
    db_session.add(travel_idea_group)

    members = [
        models.TravelIdeaGroupMember(travel_idea_group=travel_idea_group, user_account=user)
        for user in users_to_make_members
    ]
    db_session.add(members[0])
    db_session.add(members[1])

    await db_session.commit()
    return travel_idea_group, users_to_make_members, owner


@pytest.mark.asyncio
async def test_create_travel_idea_group_fails_mandatory_field_missing(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/travel-idea-group/")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_travel_idea_group(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    response = await authenticated_client.post("/travel-idea-group/", json={"name": "Our travel bucket list"})

    assert response.status_code == 201

    response_json = response.json()
    assert response_json.pop("id") is not None

    assert response_json == {
        "name": "Our travel bucket list",
        "ownedBy": {"email": user.email, "name": user.name},
        "sharedWith": [],
    }

    result = await db_session.execute(select(TravelIdeaGroup))
    travel_idea_group = result.scalars().all()

    assert len(travel_idea_group) == 1
    assert travel_idea_group[0].name == "Our travel bucket list"


@pytest.mark.asyncio
async def test_get_travel_idea_group_fails_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/travel-idea-group/4")

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_get_travel_idea_group_fails_no_access(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(db_session, user)

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to access this travel idea group"


@pytest.mark.asyncio
async def test_get_travel_idea_group(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, members, owner = await _create_travel_idea_group(db_session, user, current_user_role="member")

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": travel_idea_group.id,
        "name": travel_idea_group.name,
        "ownedBy": {"email": owner.email, "name": owner.name},
        "sharedWith": [
            {"email": user.email, "name": user.name},
            {"email": members[1].email, "name": members[1].name},
        ],
    }


@pytest.mark.asyncio
async def test_get_travel_idea_groups_none_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/travel-idea-group/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_travel_idea_groups(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    shared_travel_idea_group, shared_group_members, shared_group_owner = await _create_travel_idea_group(
        db_session, user, current_user_role="member", name_prefix="shared"
    )

    owned_travel_idea_group, owned_group_members, owned_group_owner = await _create_travel_idea_group(
        db_session, user, current_user_role="owner", name_prefix="owned"
    )

    assert user in shared_group_members
    assert user == owned_group_owner

    # As the user has no role on it, we expect the below group not to appear in the response
    await _create_travel_idea_group(db_session, user, current_user_role=None, name_prefix="other")

    response = await authenticated_client.get("/travel-idea-group/")

    assert response.status_code == 200

    assert len(response.json()) == 2
    assert response.json() == [
        {
            "id": owned_travel_idea_group.id,
            "name": owned_travel_idea_group.name,
            "ownedBy": {"email": owned_group_owner.email, "name": owned_group_owner.name},
            "sharedWith": [
                {"email": owned_group_members[0].email, "name": owned_group_members[0].name},
                {"email": owned_group_members[1].email, "name": owned_group_members[1].name},
            ],
        },
        {
            "id": shared_travel_idea_group.id,
            "name": shared_travel_idea_group.name,
            "ownedBy": {"email": shared_group_owner.email, "name": shared_group_owner.name},
            "sharedWith": [
                {"email": shared_group_members[0].email, "name": shared_group_members[0].name},
                {"email": shared_group_members[1].email, "name": shared_group_members[1].name},
            ],
        },
    ]


@pytest.mark.asyncio
async def test_update_travel_idea_group_fails_mandatory_field_missing(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(db_session, user, current_user_role="owner")

    response = await authenticated_client.put(f"/travel-idea-group/{travel_idea_group.id}")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_travel_idea_group_fails_not_owner(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(db_session, user, current_user_role="member")

    response = await authenticated_client.put(f"/travel-idea-group/{travel_idea_group.id}", json={"name": "A new name"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to perform this action"


@pytest.mark.asyncio
async def test_update_travel_idea_group(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, members, _ = await _create_travel_idea_group(db_session, user, current_user_role="owner")
    travel_idea_group_id = travel_idea_group.id

    response = await authenticated_client.put(f"/travel-idea-group/{travel_idea_group.id}", json={"name": "A new name"})

    assert response.status_code == 200

    response_json = response.json()
    assert response_json.pop("id") is not None

    assert response_json == {
        "name": "A new name",
        "ownedBy": {"email": user.email, "name": user.name},
        "sharedWith": [
            {"email": members[0].email, "name": members[0].name},
            {"email": members[1].email, "name": members[1].name},
        ],
    }

    db_session.expire_all()
    updated_db_object = await db_session.get(TravelIdeaGroup, travel_idea_group_id)
    assert updated_db_object.name == "A new name"


@pytest.mark.asyncio
async def test_delete_travel_idea_group_fails_not_owner(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(db_session, user, current_user_role="member")

    response = await authenticated_client.delete(f"/travel-idea-group/{travel_idea_group.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to perform this action"


@pytest.mark.asyncio
async def test_delete_travel_idea_group(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(db_session, user, current_user_role="owner")
    travel_idea_group_id = travel_idea_group.id

    response = await authenticated_client.delete(f"/travel-idea-group/{travel_idea_group_id}")

    assert response.status_code == 204

    db_session.expire_all()
    updated_db_object = await db_session.get(TravelIdeaGroup, travel_idea_group_id)
    assert updated_db_object is None
