from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def create_user_account(db_session: AsyncSession) -> models.UserAccount:
    password_hash = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
    user_account = models.UserAccount(email="somebody@somewhere.com", password_hash=password_hash, name="Somebody")
    db_session.add(user_account)
    await db_session.commit()
    return user_account
