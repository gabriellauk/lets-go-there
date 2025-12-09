from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.models.user_account import UserAccount
from app.schemas.enums import TravelIdeaGroupInvitationStatus, TravelIdeaGroupRole


def create_user_account(name_prefix: str = "default", number: int = 1) -> models.UserAccount:
    name = f"user_{name_prefix}_{number}"
    email = name + "@email.com"
    user_account = models.UserAccount(email=email, name=name)
    return user_account


async def create_user_accounts(
    db_session: AsyncSession, number: int, name_prefix: str = "default"
) -> list[models.UserAccount]:
    user_accounts = []
    for i in range(number):
        user_account = create_user_account(name_prefix, number=i)
        user_accounts.append(user_account)

    db_session.add_all(user_accounts)
    await db_session.commit()
    return user_accounts


async def create_travel_idea_group(
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


async def create_travel_idea_group_invitation(
    db_session: AsyncSession,
    email: str,
    status: TravelIdeaGroupInvitationStatus,
    name_prefix: str,
    expires_at: datetime,
    creator: UserAccount | None = None,
) -> tuple[models.TravelIdeaGroupInvitation, models.TravelIdeaGroup, models.UserAccount]:
    if not creator:
        creator = create_user_account(name_prefix)
        db_session.add(creator)

    travel_idea_group = models.TravelIdeaGroup(
        name=f"Some list ({name_prefix})",
        owned_by=creator,
    )
    db_session.add(travel_idea_group)

    invitation = models.TravelIdeaGroupInvitation(
        email=email,
        invitation_code=f"{name_prefix}_code",
        status=status,
        expires_at=expires_at,
        created_by=creator,
        travel_idea_group=travel_idea_group,
    )
    db_session.add(invitation)

    await db_session.commit()
    return invitation, travel_idea_group, creator
