from sqlalchemy.ext.asyncio import AsyncSession

from app import models


def create_user_account(name_prefix: str = "default", number: int = 1) -> models.UserAccount:
    name = f"user_{name_prefix}_{number}"
    email = name + "@email.com"
    password_hash = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
    user_account = models.UserAccount(email=email, password_hash=password_hash, name=name)
    return user_account


async def create_user_accounts(
    db_session: AsyncSession, number: int, name_prefix: str = "default"
) -> list[models.UserAccount]:
    user_accounts = []
    for i in range(number):
        user_account = create_user_account(name_prefix, number=i)
        user_accounts.append(user_account)

    db_session.add_all(user_accounts)
    await db_session.commit()
    return user_accounts
