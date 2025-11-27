from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.init_db import Base
from app.schemas.travel_idea_group import TravelIdeaGroupInvitationStatus

from .travel_idea_group import TravelIdeaGroup
from .user_account import UserAccount


def get_enum_values(enum_class: type[Enum]) -> list[str]:
    return [member.value for member in enum_class]


class TravelIdeaGroupInvitation(Base):
    __tablename__ = "travel_idea_group_invitation"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    invitation_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    status: Mapped[TravelIdeaGroupInvitationStatus] = mapped_column(
        Enum(TravelIdeaGroupInvitationStatus, values_callable=get_enum_values), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    travel_idea_group_id: Mapped[int] = mapped_column(ForeignKey("travel_idea_group.id"), nullable=False)

    created_by: Mapped[UserAccount] = relationship("UserAccount")
    travel_idea_group: Mapped[TravelIdeaGroup] = relationship("TravelIdeaGroup")
