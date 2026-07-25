import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.stage import ApplicationStatus, OfferStatus

# ---------------------------------------------------------------------------
# Offres
# ---------------------------------------------------------------------------


class OfferCreate(BaseModel):
    """Schema d'entree pour la creation d'une offre (a l'etat 'draft')."""

    title: str | None = Field(default=None, max_length=200)
    mission: str | None = None
    skills: str | None = None


class OfferUpdate(BaseModel):
    """Schema d'entree pour completer une offre encore en brouillon."""

    title: str | None = Field(default=None, max_length=200)
    mission: str | None = None
    skills: str | None = None


class OfferReviewDecision(BaseModel):
    """Decision du responsable pedagogique sur une offre soumise."""

    decision: Literal["publish", "reject"]
    rejection_reason: str | None = Field(default=None, max_length=300)


class OfferResponse(BaseModel):
    """Schema de sortie : ne renvoie que ce que l'utilisateur doit voir."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    mission: str | None
    skills: str | None
    status: OfferStatus
    rejection_reason: str | None
    company_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None
    published_at: datetime.datetime | None


class OfferStatsResponse(BaseModel):
    offers_by_status: dict[str, int]
    applications_by_status: dict[str, int]


# ---------------------------------------------------------------------------
# Candidatures
# ---------------------------------------------------------------------------


class ApplicationCreate(BaseModel):
    cover_letter: str | None = Field(default=None, max_length=2000)


class ApplicationDecision(BaseModel):
    decision: Literal["accepted", "rejected"]


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int
    student_id: int
    status: ApplicationStatus
    cover_letter: str | None
    created_at: datetime.datetime
    decided_at: datetime.datetime | None
