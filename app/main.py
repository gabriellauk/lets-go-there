from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import travel_idea as travel_idea_router
from app.api.routes import user as user_router
from app.database.init_db import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Starting up...")
    print("Run Alembic upgrade head...")
    await run_migrations()
    print("Migrations successful!")
    yield
    print("Application shutting down!")


app = FastAPI(lifespan=lifespan)
app.include_router(travel_idea_router.router)
app.include_router(user_router.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
