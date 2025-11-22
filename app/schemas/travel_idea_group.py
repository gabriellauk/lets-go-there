from pydantic import EmailStr

from app.models.travel_idea_group import TravelIdeaGroup
from app.models.user_account import UserAccount
from app.schemas.shared import BaseSchema


class TravelIdeaGroupUser(BaseSchema):
    email: str
    name: str


class TravelIdeaGroupBase(BaseSchema):
    name: str


class TravelIdeaGroupCreate(TravelIdeaGroupBase):
    shared_with: list[EmailStr] | None


class TravelIdeaGroupUpdate(TravelIdeaGroupBase):
    name: str | None
    shared_with: list[EmailStr] | None


class TravelIdeaGroupRead(TravelIdeaGroupBase):
    id: int
    owned_by: TravelIdeaGroupUser
    shared_with: list[TravelIdeaGroupUser]


def construct_travel_idea_group(
    travel_idea_group: TravelIdeaGroup, members_user_accounts: list[UserAccount] | None = None
) -> TravelIdeaGroupRead:
    if members_user_accounts is None:
        members_user_accounts = [member.user_account for member in travel_idea_group.members]

    shared_with = [
        TravelIdeaGroupUser(email=user_account.email, name=user_account.name) for user_account in members_user_accounts
    ]
    owned_by = TravelIdeaGroupUser(email=travel_idea_group.owned_by.email, name=travel_idea_group.owned_by.name)

    return TravelIdeaGroupRead(
        id=travel_idea_group.id, name=travel_idea_group.name, shared_with=shared_with, owned_by=owned_by
    )
