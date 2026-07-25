"""Repository CRUD generique. Aucune route ne doit appeler SQLAlchemy directement :
tout acces au domaine passe par un repository qui herite de celui-ci."""
from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> Optional[ModelType]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update_fields(self, id: int, **fields) -> Optional[ModelType]:
        clean_fields = {k: v for k, v in fields.items() if v is not None}
        if not clean_fields:
            return await self.get(id)
        await self.db.execute(
            update(self.model).where(self.model.id == id).values(**clean_fields)
        )
        await self.db.flush()
        return await self.get(id)

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(delete(self.model).where(self.model.id == id))
        return result.rowcount > 0
