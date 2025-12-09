from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request

from app import models
from app.core.config import settings
from app.database.dependencies import DBSession
from app.services.user_account import get_user_by_email

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def get_current_user(request: Request, db: DBSession) -> models.UserAccount:
    session_user = request.session.get("user")
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = session_user.get("email")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=403, detail="User not found in database")
    return user
