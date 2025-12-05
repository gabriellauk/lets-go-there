from enum import Enum


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


class TravelIdeaGroupRole(Enum):
    OWNER = "owner"
    MEMBER = "member"
