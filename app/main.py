from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.api.routes import auth as auth_router
from app.api.routes import (
    travel_idea as travel_idea_router,
)
from app.api.routes import (
    travel_idea_group as travel_idea_group_router,
)
from app.api.routes import (
    travel_idea_group_invitation as travel_idea_group_invitation_router,
)
from app.core.config import settings
from app.database.dependencies import DBSession
from app.database.init_db import run_migrations
from app.services.user_account import get_user_by_email


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Starting up...")
    print("Run Alembic upgrade head...")
    await run_migrations()
    print("Migrations successful!")
    yield
    print("Application shutting down!")


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.include_router(auth_router.router)
app.include_router(travel_idea_router.router)
app.include_router(travel_idea_group_router.router)
app.include_router(travel_idea_group_invitation_router.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/", response_model=None)
async def homepage(request: Request, db: DBSession) -> HTMLResponse | RedirectResponse:
    """As this project doesn't have a frontend, this provides a very simple way of verifying the Google sign in flow."""
    user = request.session.get("user")
    if not user:
        return HTMLResponse('<a href="/auth/login">Sign in with Google</a>')
    user_account = await get_user_by_email(db, user["email"])
    if user_account:
        signed_in_details = f"<pre>Signed in as {user_account.email} (name: {user_account.name}).</pre>"
        sign_out_link = '<a href="/auth/logout">Sign out</a>'
        html = signed_in_details + sign_out_link
        return HTMLResponse(html)
    return HTMLResponse('<a href="/auth/login">Sign in with Google</a>')


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
