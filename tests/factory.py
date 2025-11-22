from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def create_user_accounts(
    db_session: AsyncSession, number: int, name_prefix: str = "default"
) -> list[models.UserAccount]:
    password_hash = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"

    user_accounts = []
    for i in range(number):
        name = f"user_{name_prefix}_{i}"
        email = name + "@email.com"
        user_account = models.UserAccount(email=email, password_hash=password_hash, name=name)
        user_accounts.append(user_account)

    db_session.add_all(user_accounts)
    await db_session.commit()
    return user_accounts
