import datetime
from app.utils.time import utcnow
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
#datetime.datetime.utcnow remplacer par utcnow
if TYPE_CHECKING:
    from app.models.user import User


class OfferStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PUBLISHED = "published"
    REJECTED = "rejected"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[OfferStatus] = mapped_column(
        SAEnum(OfferStatus, name="offer_status_enum", native_enum=False, length=20),
        default=OfferStatus.DRAFT,
        nullable=False,
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        # SQLAlchemy appellera utcnow() automatiquement lors de l'insertion
        default=utcnow
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        nullable=True, onupdate=utcnow
    )
    published_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    company: Mapped["User"] = relationship(back_populates="offers")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="offer", cascade="all, delete-orphan"
    )

    @property
    def is_ready_for_publication(self) -> bool:
        """L'entreprise doit avoir renseigne titre, mission, competences (et elle existe forcement)."""
        return bool(self.title and self.mission and self.skills and self.company_id)


class Application(Base):
    """L'invariant 'un etudiant ne peut avoir qu'une candidature active par offre'
    est controle en logique metier (repository), car il porte sur un sous-ensemble
    d'etats (PENDING/ACCEPTED) et non sur l'unicite brute de la ligne."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            name="application_status_enum",
            native_enum=False,
            length=20,
        ),
        default=ApplicationStatus.PENDING,
        nullable=False,
    )
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=utcnow#datetime.datetime.utcnow()
    )
    decided_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    offer: Mapped["Offer"] = relationship(back_populates="applications")
    student: Mapped["User"] = relationship(back_populates="applications")
