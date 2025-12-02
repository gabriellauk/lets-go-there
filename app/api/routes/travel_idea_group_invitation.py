from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.init_db import get_db
from app.models.user_account import UserAccount
from app.schemas.travel_idea_group import TravelIdeaGroupUser
from app.schemas.travel_idea_group_invitation import TravelIdeaGroupInvitationRead
from app.services.travel_idea_group_invitation import get_travel_idea_group_invitations

router = APIRouter(prefix="/invitation", tags=["invitation"])


@router.get("/", response_model=list[TravelIdeaGroupInvitationRead])
async def get_invitations(
    db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[UserAccount, Depends(get_current_user)]
) -> list[TravelIdeaGroupInvitationRead]:
    travel_idea_group_invitations = await get_travel_idea_group_invitations(db, current_user.email)

    return [
        TravelIdeaGroupInvitationRead(
            invitation_code=invitation.invitation_code,
            travel_idea_group_name=invitation.travel_idea_group.name,
            invited_by=TravelIdeaGroupUser(name=invitation.created_by.name, email=invitation.created_by.email),
        )
        for invitation in travel_idea_group_invitations
    ]
