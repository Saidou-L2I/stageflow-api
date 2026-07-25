from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleEnum
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    #recuperation en utilisant username
    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def set_role(self, user_id: int, role: RoleEnum) -> User | None:
        return await self.update_fields(user_id, role=role)
