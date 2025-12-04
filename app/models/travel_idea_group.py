from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.init_db import Base

from .travel_idea_group_member import TravelIdeaGroupMember
from .user_account import UserAccount

if TYPE_CHECKING:
    from .travel_idea import TravelIdea
    from .travel_idea_group_invitation import TravelIdeaGroupInvitation


class TravelIdeaGroup(Base):
    __tablename__ = "travel_idea_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    owned_by_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)

    owned_by: Mapped[UserAccount] = relationship("UserAccount")
    members: Mapped[list[TravelIdeaGroupMember]] = relationship(
        "TravelIdeaGroupMember",
        back_populates="travel_idea_group",
        order_by="TravelIdeaGroupMember.id",
        cascade="all, delete",
    )
    invitations: Mapped[list["TravelIdeaGroupInvitation"]] = relationship(
        "TravelIdeaGroupInvitation", back_populates="travel_idea_group", cascade="all, delete"
    )
    travel_ideas: Mapped[list["TravelIdea"]] = relationship(
        "TravelIdea", back_populates="travel_idea_group", order_by="TravelIdea.id", cascade="all, delete"
    )
