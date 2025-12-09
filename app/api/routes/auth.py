from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.auth import oauth
from app.database.dependencies import DBSession
from app.services.user_account import create_user_account, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_model=None)
async def login(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for("authenticate")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", response_model=None)
async def authenticate(request: Request, db: DBSession) -> HTMLResponse | RedirectResponse:
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token["userinfo"]
    except OAuthError:
        return HTMLResponse("<h1>Authentication failed. Please try again.</h1>", status_code=400)
    request.session["user"] = dict(user_info)
    email = user_info["email"]
    user_account = await get_user_by_email(db, email)
    if not user_account:
        await create_user_account(db, email, user_info["given_name"])
    return RedirectResponse(url="/")


@router.get("/logout", response_model=None)
async def logout(request: Request) -> RedirectResponse:
    request.session.pop("user", None)
    return RedirectResponse(url="/")
