from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stage import Application, ApplicationStatus, Offer, OfferStatus
from app.repositories.base import BaseRepository


class OfferRepository(BaseRepository[Offer]):
    def __init__(self, db: AsyncSession):
        super().__init__(Offer, db)

    async def get_published(self, skip: int = 0, limit: int = 20) -> list[Offer]:
        result = await self.db.execute(
            select(Offer)
            .where(Offer.status == OfferStatus.PUBLISHED)
            .order_by(Offer.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_company(self, company_id: int, skip: int = 0, limit: int = 20) -> list[Offer]:
        result = await self.db.execute(
            select(Offer)
            .where(Offer.company_id == company_id)
            .order_by(Offer.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Offer.status, func.count(Offer.id)).group_by(Offer.status)
        )
        return {status.value: count for status, count in result.all()}


class ApplicationRepository(BaseRepository[Application]):
    def __init__(self, db: AsyncSession):
        super().__init__(Application, db)

    async def get_active_for_student_and_offer(
        self, student_id: int, offer_id: int
    ) -> Application | None:
        """Une candidature est 'active' si elle est en attente ou acceptee."""
        result = await self.db.execute(
            select(Application).where(
                Application.student_id == student_id,
                Application.offer_id == offer_id,
                Application.status.in_(
                    [ApplicationStatus.PENDING, ApplicationStatus.ACCEPTED]
                ),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_student(self, student_id: int, skip: int = 0, limit: int = 20) -> list[Application]:
        result = await self.db.execute(
            select(Application)
            .where(Application.student_id == student_id)
            .order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_offer(self, offer_id: int, skip: int = 0, limit: int = 20) -> list[Application]:
        result = await self.db.execute(
            select(Application)
            .where(Application.offer_id == offer_id)
            .order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Application.status, func.count(Application.id)).group_by(
                Application.status
            )
        )
        return {status.value: count for status, count in result.all()}
