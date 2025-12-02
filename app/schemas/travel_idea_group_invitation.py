from enum import Enum

from pydantic import EmailStr

from app.schemas.shared import BaseSchema


class TravelIdeaGroupInvitationCreateOrDelete(BaseSchema):
    email: EmailStr


class TravelIdeaGroupInvitationStatus(Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
