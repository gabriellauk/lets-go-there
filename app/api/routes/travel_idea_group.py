from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser
from app.core.validation import check_user_can_access_travel_idea_group
from app.database.dependencies import DBSession
from app.schemas.enums import TravelIdeaGroupRole
from app.schemas.travel_idea_group import (
    TravelIdeaGroupCreate,
    TravelIdeaGroupRead,
    TravelIdeaGroupUpdate,
    construct_travel_idea_group,
)
from app.schemas.travel_idea_group_invitation import TravelIdeaGroupInvitationCreate, TravelIdeaGroupInvitationDelete
from app.services.travel_idea_group import (
    create_new_travel_idea_group,
    delete_travel_idea_group_from_db,
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
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaGroupRead:
    travel_idea_group = await create_new_travel_idea_group(db, request_body, current_user)

    return construct_travel_idea_group(travel_idea_group, [])


@router.post("/{travel_idea_group_id}/invitation", status_code=status.HTTP_201_CREATED)
async def create_travel_idea_group_invitation(
    travel_idea_group_id: int,
    body: TravelIdeaGroupInvitationCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    travel_idea_group, members, owner = await check_user_can_access_travel_idea_group(
        db, travel_idea_group_id, current_user, TravelIdeaGroupRole.OWNER
    )

    if body.email == owner.email or body.email in [user.email for user in members]:
        raise HTTPException(status_code=400, detail="User can already access this travel idea group")

    await create_new_travel_idea_group_invitation(db, current_user, travel_idea_group, body.email)

    return 201


@router.get("/", response_model=list[TravelIdeaGroupRead])
async def get_travel_idea_groups_for_user(
    db: DBSession,
    current_user: CurrentUser,
) -> list[TravelIdeaGroupRead]:
    travel_idea_groups_from_db = await get_travel_idea_groups(db, current_user.id)

    return [construct_travel_idea_group(travel_idea_group) for travel_idea_group in travel_idea_groups_from_db]


@router.get("/{travel_idea_group_id}", response_model=TravelIdeaGroupRead)
async def get_travel_idea_group(
    travel_idea_group_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaGroupRead:
    travel_idea_group, members, _ = await check_user_can_access_travel_idea_group(
        db, travel_idea_group_id, current_user, TravelIdeaGroupRole.MEMBER
    )

    return construct_travel_idea_group(travel_idea_group, members)


@router.get("/{travel_idea_group_id}/invitation", response_model=list[str])
async def get_travel_idea_group_invitations(
    travel_idea_group_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaGroupRead:
    await check_user_can_access_travel_idea_group(db, travel_idea_group_id, current_user, TravelIdeaGroupRole.OWNER)

    invitations = await get_outstanding_invitations_for_travel_idea_group(db, travel_idea_group_id)

    return [invitation.email for invitation in invitations]


@router.put("/{travel_idea_group_id}", response_model=TravelIdeaGroupRead)
async def update_travel_idea_group(
    travel_idea_group_id: int,
    request_body: TravelIdeaGroupUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> TravelIdeaGroupRead:
    travel_idea_group, _, _ = await check_user_can_access_travel_idea_group(
        db, travel_idea_group_id, current_user, TravelIdeaGroupRole.OWNER
    )

    await update_existing_travel_idea_group(db, request_body, travel_idea_group)

    return construct_travel_idea_group(travel_idea_group)


@router.delete("/{travel_idea_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel_idea_group(
    travel_idea_group_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    travel_idea_group, _, _ = await check_user_can_access_travel_idea_group(
        db, travel_idea_group_id, current_user, TravelIdeaGroupRole.OWNER
    )

    await delete_travel_idea_group_from_db(db, travel_idea_group)


@router.delete("/{travel_idea_group_id}/invitation", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_travel_idea_group_invitation(
    travel_idea_group_id: int,
    body: TravelIdeaGroupInvitationDelete,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    await check_user_can_access_travel_idea_group(db, travel_idea_group_id, current_user, TravelIdeaGroupRole.OWNER)

    invitation = await get_travel_idea_group_invitation_for_travel_idea_group(db, travel_idea_group_id, body.email)
    if not invitation:
        raise HTTPException(status_code=404, detail="Valid invitation not found")

    await delete_travel_idea_group_invitation(db, invitation)
    return 204
