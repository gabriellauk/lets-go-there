import random
import string
from datetime import UTC, datetime, timedelta

from pydantic import EmailStr
from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import TravelIdeaGroup, UserAccount
from app.models.travel_idea_group_invitation import TravelIdeaGroupInvitation
from app.models.travel_idea_group_member import TravelIdeaGroupMember
from app.schemas.travel_idea_group import TravelIdeaGroupCreate, TravelIdeaGroupInvitationStatus, TravelIdeaGroupUpdate


async def create_new_travel_idea_group(
    db: AsyncSession, request_data: TravelIdeaGroupCreate, current_user: UserAccount
) -> TravelIdeaGroup:
    travel_idea_group = TravelIdeaGroup(
        name=request_data.name,
        owned_by=current_user,
    )
    db.add(travel_idea_group)
    await db.commit()
    return travel_idea_group


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


def select_travel_idea_group(db: AsyncSession) -> Select:
    return select(TravelIdeaGroup).options(
        selectinload(TravelIdeaGroup.members).joinedload(TravelIdeaGroupMember.user_account),
        joinedload(TravelIdeaGroup.owned_by),
    )


async def get_travel_idea_group_by_id(db: AsyncSession, travel_idea_group_id: int) -> TravelIdeaGroup | None:
    result = await db.execute(select_travel_idea_group(db).where(TravelIdeaGroup.id == travel_idea_group_id))
    travel_idea_group = result.scalars().first()
    return travel_idea_group


async def get_travel_idea_groups(db: AsyncSession, user_account_id: int) -> list[TravelIdeaGroup]:
    result = await db.execute(
        select_travel_idea_group(db)
        .where(
            or_(
                TravelIdeaGroup.owned_by_id == user_account_id,
                TravelIdeaGroup.members.any(TravelIdeaGroupMember.user_account_id == user_account_id),
            )
        )
        .order_by(TravelIdeaGroup.name)
    )
    travel_idea_groups = result.scalars().all()
    return travel_idea_groups


async def update_existing_travel_idea_group(
    db: AsyncSession, request_data: TravelIdeaGroupUpdate, travel_idea_group: TravelIdeaGroup
) -> TravelIdeaGroup:
    travel_idea_group.name = request_data.name
    await db.commit()
    return travel_idea_group


async def delete_travel_idea_group_and_members(db: AsyncSession, travel_idea_group: TravelIdeaGroup) -> None:
    for member in travel_idea_group.members:
        await db.delete(member)
    await db.delete(travel_idea_group)
    await db.commit()
