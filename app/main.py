from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import destination as destination_router
from app.database.init_db import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_tables()
    print("✅ Application started and database tables created!")
    yield
    print("🛑 Application shutting down!")


app = FastAPI(lifespan=lifespan)
app.include_router(destination_router.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
