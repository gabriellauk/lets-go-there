from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import TravelIdeaGroup, UserAccount
from app.models.travel_idea_group_member import TravelIdeaGroupMember
from app.schemas.travel_idea_group import TravelIdeaGroupCreate, TravelIdeaGroupUpdate


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


def select_travel_idea_group() -> Select:
    return select(TravelIdeaGroup).options(
        selectinload(TravelIdeaGroup.members).joinedload(TravelIdeaGroupMember.user_account),
        joinedload(TravelIdeaGroup.owned_by),
    )


async def get_travel_idea_group_by_id(db: AsyncSession, travel_idea_group_id: int) -> TravelIdeaGroup | None:
    result = await db.execute(select_travel_idea_group().where(TravelIdeaGroup.id == travel_idea_group_id))
    travel_idea_group = result.scalars().one_or_none()
    return travel_idea_group


async def get_travel_idea_groups(db: AsyncSession, user_account_id: int) -> list[TravelIdeaGroup]:
    result = await db.execute(
        select_travel_idea_group()
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


async def delete_travel_idea_group_from_db(db: AsyncSession, travel_idea_group: TravelIdeaGroup) -> None:
    await db.delete(travel_idea_group)
    await db.commit()
