from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.schemas.travel_idea_group_invitation import TravelIdeaGroupInvitationStatus
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
