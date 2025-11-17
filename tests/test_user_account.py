import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def _create_user_account(db_session: AsyncSession) -> models.UserAccount:
    password_hash = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
    user_account = models.UserAccount(email="somebody@somewhere.com", password_hash=password_hash, name="Somebody")
    db_session.add(user_account)
    await db_session.commit()
    return user_account


@pytest.mark.asyncio
async def test_login(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user_account(db_session)

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
    await _create_user_account(db_session)

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
    user = await _create_user_account(db_session)

    form_data = {
        "username": user.email,
        "password": "wrongpassword",
    }

    response = await client.post(
        "/user/token", data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
