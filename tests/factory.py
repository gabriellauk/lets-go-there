from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.models.user_account import UserAccount
from app.schemas.travel_idea_group_invitation import TravelIdeaGroupInvitationStatus


def create_user_account(name_prefix: str = "default", number: int = 1) -> models.UserAccount:
    name = f"user_{name_prefix}_{number}"
    email = name + "@email.com"
    password_hash = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
    user_account = models.UserAccount(email=email, password_hash=password_hash, name=name)
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
