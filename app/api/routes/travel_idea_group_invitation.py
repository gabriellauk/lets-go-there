
from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentUser
from app.database.dependencies import DBSession
from app.schemas.travel_idea_group import TravelIdeaGroupUser
from app.schemas.travel_idea_group_invitation import (
    TravelIdeaGroupInvitationRead,
    TravelIdeaGroupInvitationResponseRead,
    TravelIdeaGroupInvitationStatus,
    TravelIdeaGroupInvitationUpdate,
)
from app.services.travel_idea_group_invitation import (
    accept_or_reject_travel_idea_group_invitation,
    get_travel_idea_group_invitation_for_invitation_code,
    get_travel_idea_group_invitations,
)

router = APIRouter(prefix="/invitation", tags=["invitation"])


@router.get("/", response_model=list[TravelIdeaGroupInvitationRead])
async def get_invitations(db: DBSession, current_user: CurrentUser) -> list[TravelIdeaGroupInvitationRead]:
    travel_idea_group_invitations = await get_travel_idea_group_invitations(db, current_user.email)

    return [
        TravelIdeaGroupInvitationRead(
            invitation_code=invitation.invitation_code,
            travel_idea_group_name=invitation.travel_idea_group.name,
            invited_by=TravelIdeaGroupUser(name=invitation.created_by.name, email=invitation.created_by.email),
        )
        for invitation in travel_idea_group_invitations
    ]


@router.patch("/{invitation_code}", response_model=TravelIdeaGroupInvitationResponseRead)
async def update_invitation(
    invitation_code: str,
    request_body: TravelIdeaGroupInvitationUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaGroupInvitationResponseRead:
    invitation = await get_travel_idea_group_invitation_for_invitation_code(db, current_user.email, invitation_code)
    if not invitation:
        raise HTTPException(status_code=404, detail="Valid invitation not found")

    updated_invitation = await accept_or_reject_travel_idea_group_invitation(
        db, invitation, current_user, TravelIdeaGroupInvitationStatus.from_response(request_body.status)
    )

    return TravelIdeaGroupInvitationResponseRead(
        invitation_code=updated_invitation.invitation_code, status=updated_invitation.status
    )
