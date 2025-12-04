from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app import models
from app.schemas.travel_idea_group_invitation import (
    TravelIdeaGroupInvitationResponseStatus,
    TravelIdeaGroupInvitationStatus,
)
from tests.factory import create_travel_idea_group_invitation


@pytest.mark.asyncio
async def test_get_travel_idea_group_invitations_none_exist(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/invitation/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_travel_idea_group_invitations(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    # We expect only the pending invitations that are for this user and not yet expired to be returned
    await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.ACCEPTED,
        name_prefix="accepted",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )
    await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.REJECTED,
        name_prefix="rejected",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )
    await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="pending_expiring_soon",
        expires_at=datetime.now(UTC) + timedelta(seconds=5),
    )
    await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="pending",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )
    await create_travel_idea_group_invitation(
        db_session,
        "someotheruser@email.com",
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="other_user",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )
    await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="expired",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    response = await authenticated_client.get("/invitation/")

    assert response.status_code == 200

    assert response.json() == [
        {
            "invitationCode": "pending_expiring_soon_code",
            "travelIdeaGroupName": "Some list (pending_expiring_soon)",
            "invitedBy": {"email": "user_pending_expiring_soon_1@email.com", "name": "user_pending_expiring_soon_1"},
        },
        {
            "invitationCode": "pending_code",
            "travelIdeaGroupName": "Some list (pending)",
            "invitedBy": {"email": "user_pending_1@email.com", "name": "user_pending_1"},
        },
    ]


@pytest.mark.asyncio
async def test_accept_or_reject_travel_idea_group_invitation_fails_missing_status(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    invitation, _, _ = await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="no_status_sent",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )

    response = await authenticated_client.patch(f"/invitation/{invitation.invitation_code}")

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", [TravelIdeaGroupInvitationResponseStatus.ACCEPTED, TravelIdeaGroupInvitationResponseStatus.REJECTED]
)
async def test_accept_or_reject_travel_idea_group_invitation_invalid_code(
    db_session: AsyncSession,
    authenticated_client: AsyncClient,
    user: models.UserAccount,
    status: TravelIdeaGroupInvitationResponseStatus,
) -> None:
    _, _, _ = await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="invalid_code",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )

    response = await authenticated_client.patch("/invitation/wrong_code", json={"status": status.value})

    assert response.status_code == 404
    assert response.json()["detail"] == "Valid invitation not found"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", [TravelIdeaGroupInvitationResponseStatus.ACCEPTED, TravelIdeaGroupInvitationResponseStatus.REJECTED]
)
async def test_accept_or_reject_travel_idea_group_invitation_fails_email_doesnt_match(
    db_session: AsyncSession, authenticated_client: AsyncClient, status: TravelIdeaGroupInvitationResponseStatus
) -> None:
    invitation, _, _ = await create_travel_idea_group_invitation(
        db_session,
        "some_other@user.com",
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="email_doesnt_match",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )

    response = await authenticated_client.patch(
        f"/invitation/{invitation.invitation_code}", json={"status": status.value}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Valid invitation not found"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", [TravelIdeaGroupInvitationResponseStatus.ACCEPTED, TravelIdeaGroupInvitationResponseStatus.REJECTED]
)
async def test_accept_or_reject_travel_idea_group_invitation_fails_expired(
    db_session: AsyncSession,
    authenticated_client: AsyncClient,
    user: models.UserAccount,
    status: TravelIdeaGroupInvitationResponseStatus,
) -> None:
    invitation, _, _ = await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="expired",
        expires_at=datetime.now(UTC) - timedelta(seconds=5),
    )

    response = await authenticated_client.patch(
        f"/invitation/{invitation.invitation_code}", json={"status": status.value}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Valid invitation not found"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "old_status", [TravelIdeaGroupInvitationStatus.ACCEPTED, TravelIdeaGroupInvitationStatus.REJECTED]
)
@pytest.mark.parametrize(
    "new_status", [TravelIdeaGroupInvitationResponseStatus.ACCEPTED, TravelIdeaGroupInvitationResponseStatus.REJECTED]
)
async def test_accept_or_reject_travel_idea_group_invitation_fails_not_pending(
    db_session: AsyncSession,
    authenticated_client: AsyncClient,
    user: models.UserAccount,
    old_status: TravelIdeaGroupInvitationStatus,
    new_status: TravelIdeaGroupInvitationResponseStatus,
) -> None:
    invitation, _, _ = await create_travel_idea_group_invitation(
        db_session,
        user.email,
        old_status,
        name_prefix="not_pending",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )

    response = await authenticated_client.patch(
        f"/invitation/{invitation.invitation_code}", json={"status": new_status.value}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Valid invitation not found"


@pytest.mark.asyncio
async def test_reject_travel_idea_group_invitation(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    invitation, _, _ = await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="rejecting",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )
    invitation_id = invitation.id

    response = await authenticated_client.patch(
        f"/invitation/{invitation.invitation_code}",
        json={"status": TravelIdeaGroupInvitationResponseStatus.REJECTED.value},
    )

    assert response.json() == {
        "invitationCode": invitation.invitation_code,
        "status": TravelIdeaGroupInvitationStatus.REJECTED.value,
    }

    db_session.expire_all()
    updated_invitation = await db_session.get(models.TravelIdeaGroupInvitation, invitation_id)
    assert updated_invitation.status == TravelIdeaGroupInvitationStatus.REJECTED
    group_members = await db_session.execute(select(func.count()).select_from(models.TravelIdeaGroupMember))
    assert group_members.scalar() == 0


@pytest.mark.asyncio
async def test_accept_travel_idea_group_invitation(
    db_session: AsyncSession, authenticated_client: AsyncClient, user: models.UserAccount
) -> None:
    invitation, travel_idea_group, _ = await create_travel_idea_group_invitation(
        db_session,
        user.email,
        TravelIdeaGroupInvitationStatus.PENDING,
        name_prefix="accepting",
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
    )
    invitation_id = invitation.id

    response = await authenticated_client.patch(
        f"/invitation/{invitation.invitation_code}",
        json={"status": TravelIdeaGroupInvitationResponseStatus.ACCEPTED.value},
    )

    assert response.json() == {
        "invitationCode": invitation.invitation_code,
        "status": TravelIdeaGroupInvitationStatus.ACCEPTED.value,
    }

    db_session.expire_all()
    updated_invitation = await db_session.get(models.TravelIdeaGroupInvitation, invitation_id)
    assert updated_invitation.status == TravelIdeaGroupInvitationStatus.ACCEPTED

    result = await db_session.execute(
        select(models.TravelIdeaGroupMember).options(
            joinedload(models.TravelIdeaGroupMember.user_account),
            joinedload(models.TravelIdeaGroupMember.travel_idea_group),
        )
    )
    member = result.scalar_one()
    assert member.user_account == user
    assert member.travel_idea_group == travel_idea_group
