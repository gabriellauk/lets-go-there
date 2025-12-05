from typing import Annotated

from fastapi import Depends

from app.models.user_account import UserAccount

from .auth import get_current_user

CurrentUser = Annotated[UserAccount, Depends(get_current_user)]
