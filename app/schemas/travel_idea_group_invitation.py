from enum import Enum

from pydantic import EmailStr

from app.schemas.shared import BaseSchema
from app.schemas.travel_idea_group import TravelIdeaGroupUser


class TravelIdeaGroupInvitationCreateOrDelete(BaseSchema):
    email: EmailStr


class TravelIdeaGroupInvitationResponseStatus(Enum):
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class TravelIdeaGroupInvitationStatus(Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

    @classmethod
    def from_response(cls, response: TravelIdeaGroupInvitationResponseStatus) -> "TravelIdeaGroupInvitationStatus":
        return cls(response.value)


class TravelIdeaGroupInvitationRead(BaseSchema):
    invitation_code: str
    travel_idea_group_name: str
    invited_by: TravelIdeaGroupUser


class TravelIdeaGroupInvitationUpdate(BaseSchema):
    status: TravelIdeaGroupInvitationResponseStatus


class TravelIdeaGroupInvitationResponseRead(BaseSchema):
    invitation_code: str
    status: TravelIdeaGroupInvitationStatus
