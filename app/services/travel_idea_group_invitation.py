import random
import string
from datetime import UTC, datetime, timedelta

from pydantic import EmailStr
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import TravelIdeaGroup, UserAccount
from app.models.travel_idea_group_invitation import TravelIdeaGroupInvitation
from app.schemas.travel_idea_group_invitation import (
    TravelIdeaGroupInvitationStatus,
)
from app.services.travel_idea_group_member import create_new_travel_idea_group_member


async def create_new_travel_idea_group_invitation(
    db: AsyncSession, current_user: UserAccount, travel_idea_group: TravelIdeaGroup, email: EmailStr
) -> TravelIdeaGroupInvitation:
    invitation_code = "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    invitation = TravelIdeaGroupInvitation(
        email=email,
        invitation_code=invitation_code,
        status=TravelIdeaGroupInvitationStatus.PENDING,
        expires_at=datetime.now(UTC) + timedelta(weeks=2),
        created_by=current_user,
        travel_idea_group=travel_idea_group,
    )
    db.add(invitation)
    await db.commit()
    return invitation


def select_travel_idea_group_invitation(
    email: str, travel_idea_group_id: int | None = None, invitation_code: str | None = None
) -> Select:
    filters = [
        TravelIdeaGroupInvitation.email == email,
        TravelIdeaGroupInvitation.status == TravelIdeaGroupInvitationStatus.PENDING,
        TravelIdeaGroupInvitation.expires_at >= datetime.now(UTC),
    ]

    if travel_idea_group_id:
        filters.append(TravelIdeaGroupInvitation.travel_idea_group_id == travel_idea_group_id)

    if invitation_code:
        filters.append(TravelIdeaGroupInvitation.invitation_code == invitation_code)

    return (
        select(TravelIdeaGroupInvitation)
        .options(
            joinedload(TravelIdeaGroupInvitation.created_by), joinedload(TravelIdeaGroupInvitation.travel_idea_group)
        )
        .where(*filters)
    )


async def get_travel_idea_group_invitation_for_travel_idea_group(
    db: AsyncSession, travel_idea_group_id: int, email: str
) -> TravelIdeaGroup | None:
    result = await db.execute(select_travel_idea_group_invitation(email, travel_idea_group_id=travel_idea_group_id))
    invitation = result.scalars().one_or_none()
    return invitation


async def get_travel_idea_group_invitation_for_invitation_code(
    db: AsyncSession, email: str, invitation_code: str
) -> TravelIdeaGroup | None:
    result = await db.execute(select_travel_idea_group_invitation(email, invitation_code=invitation_code))
    invitation = result.scalars().one_or_none()
    return invitation


async def get_travel_idea_group_invitations(db: AsyncSession, email: str) -> list[TravelIdeaGroup]:
    result = await db.execute(
        (select_travel_idea_group_invitation(email)).order_by(TravelIdeaGroupInvitation.created_at)
    )

    travel_idea_group_invitations = result.scalars().all()
    return travel_idea_group_invitations


async def accept_or_reject_travel_idea_group_invitation(
    db: AsyncSession,
    invitation: TravelIdeaGroupInvitation,
    user: UserAccount,
    status: TravelIdeaGroupInvitationStatus,
) -> TravelIdeaGroupInvitation:
    invitation.status = status
    if status == TravelIdeaGroupInvitationStatus.ACCEPTED:
        await create_new_travel_idea_group_member(db, invitation.travel_idea_group, user)

    await db.commit()
    return invitation


async def delete_travel_idea_group_invitation(db: AsyncSession, invitation: TravelIdeaGroupInvitation) -> None:
    await db.delete(invitation)
    await db.commit()
