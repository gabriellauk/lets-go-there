from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.init_db import Base


class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
