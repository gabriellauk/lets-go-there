from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.validation import validate_existence_and_ownership_of_travel_idea_group
from app.database.init_db import get_db
from app.models.user_account import UserAccount
from app.schemas.travel_idea_group import (
    TravelIdeaGroupCreate,
    TravelIdeaGroupRead,
    TravelIdeaGroupUpdate,
    construct_travel_idea_group,
)
from app.schemas.travel_idea_group_invitation import TravelIdeaGroupInvitationCreateOrDelete
from app.services.travel_idea_group import (
    create_new_travel_idea_group,
    delete_travel_idea_group_and_members,
    get_travel_idea_group_by_id,
    get_travel_idea_groups,
    update_existing_travel_idea_group,
)
from app.services.travel_idea_group_invitation import (
    create_new_travel_idea_group_invitation,
    delete_travel_idea_group_invitation,
    get_outstanding_invitations_for_travel_idea_group,
    get_travel_idea_group_invitation_for_travel_idea_group,
)

router = APIRouter(prefix="/travel-idea-group", tags=["travel-idea-group"])


@router.post("/", response_model=TravelIdeaGroupRead, status_code=status.HTTP_201_CREATED)
async def create_travel_idea_group(
    request_body: TravelIdeaGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> TravelIdeaGroupRead:
    travel_idea_group = await create_new_travel_idea_group(db, request_body, current_user)

    return construct_travel_idea_group(travel_idea_group, [])


@router.post("/{travel_idea_group_id}/invitation", status_code=status.HTTP_201_CREATED)
async def create_travel_idea_group_invitation(
    travel_idea_group_id: int,
    body: TravelIdeaGroupInvitationCreateOrDelete,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> None:
    travel_idea_group = await validate_existence_and_ownership_of_travel_idea_group(
        db, travel_idea_group_id, current_user
    )

    owner = travel_idea_group.owned_by
    members_user_accounts = [member.user_account for member in travel_idea_group.members]

    if body.email == owner.email or body.email in [user.email for user in members_user_accounts]:
        raise HTTPException(status_code=400, detail="User can already access this travel idea group")

    await create_new_travel_idea_group_invitation(db, current_user, travel_idea_group, body.email)

    return 201


@router.get("/", response_model=list[TravelIdeaGroupRead])
async def get_travel_idea_groups_for_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> list[TravelIdeaGroupRead]:
    travel_idea_groups_from_db = await get_travel_idea_groups(db, current_user.id)

    return [construct_travel_idea_group(travel_idea_group) for travel_idea_group in travel_idea_groups_from_db]


@router.get("/{travel_idea_group_id}", response_model=TravelIdeaGroupRead)
async def get_travel_idea_group(
    travel_idea_group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> TravelIdeaGroupRead:
    travel_idea_group = await get_travel_idea_group_by_id(db, travel_idea_group_id)
    if travel_idea_group is None:
        raise HTTPException(status_code=404, detail="Travel idea group not found")

    members_user_accounts = [member.user_account for member in travel_idea_group.members]

    if current_user not in members_user_accounts and current_user != travel_idea_group.owned_by:
        raise HTTPException(status_code=403, detail="Not authorised to access this travel idea group")

    return construct_travel_idea_group(travel_idea_group, members_user_accounts)


@router.get("/{travel_idea_group_id}/invitation", response_model=list[str])
async def get_travel_idea_group_invitations(
    travel_idea_group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> TravelIdeaGroupRead:
    await validate_existence_and_ownership_of_travel_idea_group(db, travel_idea_group_id, current_user)

    invitations = await get_outstanding_invitations_for_travel_idea_group(db, travel_idea_group_id)

    return [invitation.email for invitation in invitations]


@router.put("/{travel_idea_group_id}", response_model=TravelIdeaGroupRead)
async def update_travel_idea_group(
    travel_idea_group_id: int,
    request_body: TravelIdeaGroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> TravelIdeaGroupRead:
    travel_idea_group = await validate_existence_and_ownership_of_travel_idea_group(
        db, travel_idea_group_id, current_user
    )

    await update_existing_travel_idea_group(db, request_body, travel_idea_group)

    return construct_travel_idea_group(travel_idea_group)


@router.delete("/{travel_idea_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel_idea_group(
    travel_idea_group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> None:
    travel_idea_group = await validate_existence_and_ownership_of_travel_idea_group(
        db, travel_idea_group_id, current_user
    )

    await delete_travel_idea_group_and_members(db, travel_idea_group)


@router.delete("/{travel_idea_group_id}/invitation", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_travel_idea_group_invitation(
    travel_idea_group_id: int,
    body: TravelIdeaGroupInvitationCreateOrDelete,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> None:
    await validate_existence_and_ownership_of_travel_idea_group(db, travel_idea_group_id, current_user)

    invitation = await get_travel_idea_group_invitation_for_travel_idea_group(db, travel_idea_group_id, body.email)
    if not invitation:
        raise HTTPException(status_code=404, detail="Valid invitation not found")

    await delete_travel_idea_group_invitation(db, invitation)
    return 204
