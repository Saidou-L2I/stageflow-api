import datetime
from app.utils.time import utcnow
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.role import RoleEnum

if TYPE_CHECKING:
    from app.models.stage import Offer, Application


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    #rajoute de username
    username: Mapped[str] = mapped_column(String(150),unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="role_enum", native_enum=False, length=30),
        default=RoleEnum.STUDENT,
        nullable=False,
    )
    # Nom de l'entreprise, uniquement pertinent pour les comptes "company"
    company_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=utcnow#datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        nullable=True, onupdate=utcnow#datetime.datetime.utcnow
    )

    offers: Mapped[list["Offer"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
