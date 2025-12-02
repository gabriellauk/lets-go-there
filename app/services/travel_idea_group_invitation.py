import random
import string
from datetime import UTC, datetime, timedelta

from pydantic import EmailStr
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import TravelIdeaGroup, UserAccount
from app.models.travel_idea_group_invitation import TravelIdeaGroupInvitation
from app.schemas.travel_idea_group_invitation import TravelIdeaGroupInvitationStatus


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


def select_travel_idea_group_invitation(db: AsyncSession) -> Select:
    return select(TravelIdeaGroupInvitation).options(
        joinedload(TravelIdeaGroupInvitation.created_by),
        joinedload(TravelIdeaGroupInvitation.travel_idea_group),
    )


async def get_travel_idea_group_invitations(db: AsyncSession, email: str) -> list[TravelIdeaGroup]:
    result = await db.execute(
        (
            select_travel_idea_group_invitation(db).where(
                TravelIdeaGroupInvitation.email == email,
                TravelIdeaGroupInvitation.status == TravelIdeaGroupInvitationStatus.PENDING,
                TravelIdeaGroupInvitation.expires_at >= datetime.now(UTC),
            )
        ).order_by(TravelIdeaGroupInvitation.created_at)
    )

    travel_idea_group_invitations = result.scalars().all()
    return travel_idea_group_invitations
