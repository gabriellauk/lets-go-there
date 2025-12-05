from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.models.travel_idea import TravelIdea
from app.models.travel_idea_group import TravelIdeaGroup
from app.models.travel_idea_group_invitation import TravelIdeaGroupInvitation
from app.schemas.enums import TravelIdeaGroupInvitationStatus, TravelIdeaGroupRole
from tests.factory import create_travel_idea_group_invitation, create_user_accounts


async def _create_travel_idea_group(
    db_session: AsyncSession,
    current_user: models.UserAccount,
    current_user_role: TravelIdeaGroupRole | None = None,
    name_prefix: str = "default",
) -> tuple[models.TravelIdeaGroup, list[models.UserAccount], models.UserAccount]:
    users = await create_user_accounts(db_session, 3, name_prefix)

    if current_user_role == TravelIdeaGroupRole.OWNER:
        owner = current_user
        users_to_make_members = [users[0], users[2]]
    elif current_user_role == TravelIdeaGroupRole.MEMBER:
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
async def test_create_travel_idea_group_invitation_fails_not_found(
    authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    response = await authenticated_client.post("/travel-idea-group/3/invitation", json={"email": "name@website.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_create_travel_idea_group_invitation_fails_not_owner(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": "name@website.com"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to perform this action"


@pytest.mark.asyncio
async def test_create_travel_idea_group_invitation_fails_invalid_email(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )

    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": "namewebsite.com"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_travel_idea_group_invitation_fails_invitee_already_a_member(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, members, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )

    email = members[0].email
    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": email}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User can already access this travel idea group"


@pytest.mark.asyncio
async def test_create_travel_idea_group_invitation_fails_invitee_is_the_owner(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, owner = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )

    email = owner.email
    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": email}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User can already access this travel idea group"


@pytest.mark.asyncio
async def test_create_travel_idea_group_invitation(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )

    email = "name@website.com"
    response = await authenticated_client.post(
        f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": email}
    )

    assert response.status_code == 201

    result = await db_session.execute(select(TravelIdeaGroupInvitation))
    invitations = result.scalars().all()
    assert len(invitations) == 1

    invitation = invitations[0]
    assert invitation.email == email
    assert len(invitation.invitation_code) == 10
    assert invitation.status == TravelIdeaGroupInvitationStatus.PENDING
    assert invitation.created_at.date() == datetime.now(UTC).date()
    assert invitation.expires_at.date() == datetime.now(UTC).date() + timedelta(weeks=2)
    assert invitation.created_by == user
    assert invitation.travel_idea_group == travel_idea_group


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
    travel_idea_group, members, owner = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

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
async def test_get_travel_idea_group_invitations_fails_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/travel-idea-group/4/invitation")

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_get_travel_idea_group_invitations_fails_not_owner(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/invitation")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to perform this action"


@pytest.mark.asyncio
async def test_get_travel_idea_group_invitations(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, members, owner = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )
    other_travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER, name_prefix="other"
    )

    accepted_invitation = models.TravelIdeaGroupInvitation(
        email="accepted_invitation@email.com",
        invitation_code="acccepted_invitation",
        status=TravelIdeaGroupInvitationStatus.ACCEPTED,
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        created_by=user,
        travel_idea_group=travel_idea_group,
    )
    rejected_invitation = models.TravelIdeaGroupInvitation(
        email="rejected_invitation@email.com",
        invitation_code="rejected_invitation",
        status=TravelIdeaGroupInvitationStatus.REJECTED,
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        created_by=user,
        travel_idea_group=travel_idea_group,
    )
    pending_invitation = models.TravelIdeaGroupInvitation(
        email="pending_invitation@email.com",
        invitation_code="pending_invitation",
        status=TravelIdeaGroupInvitationStatus.PENDING,
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        created_by=user,
        travel_idea_group=travel_idea_group,
    )
    pending_expiring_soon_invitation = models.TravelIdeaGroupInvitation(
        email="pending_expiting_soon_invitation@email.com",
        invitation_code="pending_expiring_soon_invitation",
        status=TravelIdeaGroupInvitationStatus.PENDING,
        expires_at=datetime.now(UTC) + timedelta(seconds=5),
        created_by=user,
        travel_idea_group=travel_idea_group,
    )
    pending_expired_invitation = models.TravelIdeaGroupInvitation(
        email="pending_expired_invitation@email.com",
        invitation_code="pending_expired_invitation",
        status=TravelIdeaGroupInvitationStatus.PENDING,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        created_by=user,
        travel_idea_group=travel_idea_group,
    )
    pending_other_group_invitation = models.TravelIdeaGroupInvitation(
        email="pending_other_group_invitation@email.com",
        invitation_code="pending_other_group_invitation",
        status=TravelIdeaGroupInvitationStatus.PENDING,
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        created_by=user,
        travel_idea_group=other_travel_idea_group,
    )
    db_session.add_all(
        [
            accepted_invitation,
            rejected_invitation,
            pending_invitation,
            pending_expiring_soon_invitation,
            pending_expired_invitation,
            pending_other_group_invitation,
        ]
    )
    await db_session.commit()

    response = await authenticated_client.get(f"/travel-idea-group/{travel_idea_group.id}/invitation")

    assert response.status_code == 200
    assert response.json() == [
        rejected_invitation.email,
        pending_invitation.email,
        pending_expiring_soon_invitation.email,
    ]


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
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER, name_prefix="shared"
    )

    owned_travel_idea_group, owned_group_members, owned_group_owner = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER, name_prefix="owned"
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
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )

    response = await authenticated_client.put(f"/travel-idea-group/{travel_idea_group.id}")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_travel_idea_group_fails_not_owner(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.put(f"/travel-idea-group/{travel_idea_group.id}", json={"name": "A new name"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to perform this action"


@pytest.mark.asyncio
async def test_update_travel_idea_group(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, members, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )
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
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.MEMBER
    )

    response = await authenticated_client.delete(f"/travel-idea-group/{travel_idea_group.id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to perform this action"


@pytest.mark.asyncio
async def test_delete_travel_idea_group(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: models.UserAccount,
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )

    invitation = models.TravelIdeaGroupInvitation(
        email="pending_invitation@email.com",
        invitation_code="pending_invitation",
        status=TravelIdeaGroupInvitationStatus.PENDING,
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        created_by=user,
        travel_idea_group=travel_idea_group,
    )

    travel_idea = models.TravelIdea(
        name="Alhambra",
        image_url="img_123",
        notes="A beautiful palace",
        created_by=user,
        travel_idea_group=travel_idea_group,
    )
    db_session.add_all([invitation, travel_idea])
    await db_session.commit()

    travel_idea_group_id = travel_idea_group.id
    invitation_id = invitation.id
    travel_idea_id = travel_idea.id

    response = await authenticated_client.delete(f"/travel-idea-group/{travel_idea_group_id}")

    assert response.status_code == 204

    db_session.expire_all()
    updated_travel_idea_group = await db_session.get(TravelIdeaGroup, travel_idea_group_id)
    assert updated_travel_idea_group is None
    updated_invitation = await db_session.get(TravelIdeaGroupInvitation, invitation_id)
    assert updated_invitation is None
    updated_travel_idea = await db_session.get(TravelIdea, travel_idea_id)
    assert updated_travel_idea is None
    group_members = await db_session.execute(select(func.count()).select_from(models.TravelIdeaGroupMember))
    assert group_members.scalar() == 0


@pytest.mark.asyncio
async def test_revoke_travel_idea_group_invitation_fails_doesnt_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.request(
        "DELETE", "/travel-idea-group/404/invitation", json={"email": "somebody@company.com"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Travel idea group not found"


@pytest.mark.asyncio
async def test_revoke_travel_idea_group_invitation_fails_not_owner(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    invitation, travel_idea_group, _ = await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="pending",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )

    response = await authenticated_client.request(
        "DELETE", f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": invitation.email}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorised to perform this action"


@pytest.mark.asyncio
async def test_revoke_travel_idea_group_invitation_fails_invalid_email(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    travel_idea_group, _, _ = await _create_travel_idea_group(
        db_session, user, current_user_role=TravelIdeaGroupRole.OWNER
    )

    response = await authenticated_client.request(
        "DELETE", f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": "namewebsite.com"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_revoke_travel_idea_group_invitation_fails_email_and_travel_group_id_dont_match(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    # Matches on travel idea group ID but not email
    _, travel_idea_group, _ = await create_travel_idea_group_invitation(
        db_session,
        "email_doesnt_match@website.com",
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="email_doesnt_match",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        creator=user,
    )

    # Matches on email but not travel idea group ID
    invitation, _, _ = await create_travel_idea_group_invitation(
        db_session,
        "email_matches@website.com",
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="email_matches",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        creator=user,
    )

    response = await authenticated_client.request(
        "DELETE", f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": invitation.email}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Valid invitation not found"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [TravelIdeaGroupInvitationStatus.ACCEPTED, TravelIdeaGroupInvitationStatus.REJECTED])
async def test_revoke_travel_idea_group_invitation_fails_not_pending(
    db_session: AsyncSession,
    authenticated_client: AsyncClient,
    user: models.UserAccount,
    status: TravelIdeaGroupInvitationStatus,
) -> None:
    invitation, travel_idea_group, _ = await create_travel_idea_group_invitation(
        db_session,
        "email_matches@website.com",
        TravelIdeaGroupInvitationStatus.ACCEPTED,
        name_prefix="email_matches",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        creator=user,
    )

    response = await authenticated_client.request(
        "DELETE", f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": invitation.email}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Valid invitation not found"


@pytest.mark.asyncio
async def test_revoke_travel_idea_group_invitation_fails_expired(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    invitation, travel_idea_group, _ = await create_travel_idea_group_invitation(
        db_session,
        "email_matches@website.com",
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="email_matches",
        expires_at=datetime.now(UTC) - timedelta(seconds=5),
        creator=user,
    )

    response = await authenticated_client.request(
        "DELETE", f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": invitation.email}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Valid invitation not found"


@pytest.mark.asyncio
async def test_revoke_travel_idea_group_invitation(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    invitation, travel_idea_group, _ = await create_travel_idea_group_invitation(
        db_session,
        "email_matches@website.com",
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="email_matches",
        expires_at=datetime.now(UTC) + timedelta(seconds=5),
        creator=user,
    )
    invitation_id = invitation.id

    response = await authenticated_client.request(
        "DELETE", f"/travel-idea-group/{travel_idea_group.id}/invitation", json={"email": invitation.email}
    )

    assert response.status_code == 204
    db_session.expire_all()
    updated_db_object = await db_session.get(TravelIdeaGroupInvitation, invitation_id)
    assert updated_db_object is None
