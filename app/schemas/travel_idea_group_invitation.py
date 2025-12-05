from pydantic import EmailStr

from app.schemas.enums import TravelIdeaGroupInvitationResponseStatus, TravelIdeaGroupInvitationStatus
from app.schemas.shared import BaseSchema
from app.schemas.travel_idea_group import TravelIdeaGroupUser


class TravelIdeaGroupInvitationCreate(BaseSchema):
    email: EmailStr


class TravelIdeaGroupInvitationDelete(TravelIdeaGroupInvitationCreate):
    pass


class TravelIdeaGroupInvitationRead(BaseSchema):
    invitation_code: str
    travel_idea_group_name: str
    invited_by: TravelIdeaGroupUser


class TravelIdeaGroupInvitationUpdate(BaseSchema):
    status: TravelIdeaGroupInvitationResponseStatus


class TravelIdeaGroupInvitationResponseRead(BaseSchema):
    invitation_code: str
    status: TravelIdeaGroupInvitationStatus
