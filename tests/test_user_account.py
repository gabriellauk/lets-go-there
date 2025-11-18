import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from tests.factory import create_user_account


@pytest.mark.asyncio
async def test_login(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user_account(db_session)

    form_data = {
        "username": "somebody@somewhere.com",
        "password": "secret",
    }

    response = await client.post(
        "/user/token", data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 200
    token_response = response.json()
    assert "access_token" in token_response
    assert token_response["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_fails_wrong_email(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_user_account(db_session)

    form_data = {
        "username": "wrong@email.com",
        "password": "secret",
    }

    response = await client.post(
        "/user/token", data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_fails_wrong_password(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user_account(db_session)

    form_data = {
        "username": user.email,
        "password": "wrongpassword",
    }

    response = await client.post(
        "/user/token", data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient, db_session: AsyncSession) -> None:
    request_body = {"email": "some@email.com", "password": "mypassword", "name": "Some Name"}

    response = await client.post("/user/register", json=request_body)

    assert response.status_code == 201

    response_data = response.json()
    assert response_data == {"email": request_body["email"], "name": request_body["name"]}

    user_in_db = await db_session.execute(
        select(func.count()).select_from(models.UserAccount).where(models.UserAccount.email == request_body["email"])
    )
    assert user_in_db.scalar() == 1


@pytest.mark.asyncio
async def test_create_account_fails_user_already_exists(client: AsyncClient, db_session: AsyncSession) -> None:
    existing_user = await create_user_account(db_session)

    request_body = {"email": existing_user.email, "password": "mypassword", "name": "Some Name"}

    response = await client.post("/user/register", json=request_body)

    assert response.status_code == 400

    assert "An unexpected error occurred." in response.json()["detail"]
