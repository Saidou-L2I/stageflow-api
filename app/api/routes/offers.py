#import datetime
#import du datetime du package utils
from app.utils.time import utcnow
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.errors import BusinessRuleError, NotAuthorizedError, NotFoundError
from app.core.permissions import require_company, require_program_manager, require_staff
from app.core.security import CurrentUser, DBSession
from app.models.role import RoleEnum
from app.models.stage import Offer, OfferStatus
from app.models.user import User
from app.repositories.stage_repository import ApplicationRepository, OfferRepository
from app.schemas.stage import (
    ApplicationResponse,
    OfferCreate,
    OfferResponse,
    OfferReviewDecision,
    OfferStatsResponse,
    OfferUpdate,
)
from app.utils.pagination import PageParams, pagination_params

router = APIRouter(prefix="/offers", tags=["Offres"])


def _check_offer_completeness(offer: Offer) -> None:
    if not (offer.title and offer.mission and offer.skills and offer.company_id):
        raise BusinessRuleError(
            "L'offre doit avoir un titre, une mission et des competences renseignes "
            "avant d'etre soumise ou publiee."
        )


@router.post(
    "",
    response_model=OfferResponse,
    status_code=201,
    summary="Creer une offre en brouillon (entreprise)",
)
async def create_offer(
    payload: OfferCreate,
    db: DBSession,
    company: Annotated[User, Depends(require_company)],
) -> Offer:
    repo = OfferRepository(db)
    offer = Offer(
        title=payload.title,
        mission=payload.mission,
        skills=payload.skills,
        company_id=company.id,
        status=OfferStatus.DRAFT,
    )
    return await repo.create(offer)


@router.get("", response_model=list[OfferResponse], summary="Lister les offres visibles")
async def list_offers(
    db: DBSession,
    current_user: CurrentUser,
    page: Annotated[PageParams, Depends(pagination_params)],
) -> list[Offer]:
    repo = OfferRepository(db)

    if current_user.role == RoleEnum.STUDENT:
        return await repo.get_published(skip=page.skip, limit=page.limit)
    if current_user.role == RoleEnum.COMPANY:
        return await repo.get_by_company(current_user.id, skip=page.skip, limit=page.limit)
    # program_manager / admin voient tout
    return list(await repo.get_all(skip=page.skip, limit=page.limit))


@router.get("/stats", response_model=OfferStatsResponse, summary="Statistiques globales (responsable)")
async def get_stats(
    db: DBSession,
    _staff: Annotated[User, Depends(require_staff)],
) -> OfferStatsResponse:
    offer_repo = OfferRepository(db)
    application_repo = ApplicationRepository(db)
    return OfferStatsResponse(
        offers_by_status=await offer_repo.count_by_status(),
        applications_by_status=await application_repo.count_by_status(),
    )


@router.get("/{offer_id}", response_model=OfferResponse, summary="Consulter une offre")
async def get_offer(offer_id: int, db: DBSession, current_user: CurrentUser) -> Offer:
    repo = OfferRepository(db)
    offer = await repo.get(offer_id)
    if offer is None:
        raise NotFoundError("Offre introuvable.")

    is_owner_company = current_user.role == RoleEnum.COMPANY and current_user.id == offer.company_id
    is_staff = current_user.role in (RoleEnum.PROGRAM_MANAGER, RoleEnum.ADMIN)
    is_published = offer.status == OfferStatus.PUBLISHED

    if not (is_published or is_owner_company or is_staff):
        # Une offre non publiee n'est visible que par son entreprise et le staff
        raise NotFoundError("Offre introuvable.")

    return offer


@router.patch(
    "/{offer_id}",
    response_model=OfferResponse,
    summary="Completer une offre encore en brouillon (entreprise proprietaire)",
)
async def update_offer(
    offer_id: int,
    payload: OfferUpdate,
    db: DBSession,
    company: Annotated[User, Depends(require_company)],
) -> Offer:
    repo = OfferRepository(db)
    offer = await repo.get(offer_id)
    if offer is None:
        raise NotFoundError("Offre introuvable.")
    if offer.company_id != company.id:
        raise NotAuthorizedError("Cette offre n'appartient pas a votre entreprise.")
    if offer.status != OfferStatus.DRAFT:
        raise BusinessRuleError("Seule une offre en brouillon peut etre modifiee.")

    return await repo.update_fields(
        offer_id, title=payload.title, mission=payload.mission, skills=payload.skills
    )


@router.patch(
    "/{offer_id}/submit",
    response_model=OfferResponse,
    summary="Soumettre une offre pour validation (entreprise proprietaire)",
)
async def submit_offer(
    offer_id: int,
    db: DBSession,
    company: Annotated[User, Depends(require_company)],
) -> Offer:
    repo = OfferRepository(db)
    offer = await repo.get(offer_id)
    if offer is None:
        raise NotFoundError("Offre introuvable.")
    if offer.company_id != company.id:
        raise NotAuthorizedError("Cette offre n'appartient pas a votre entreprise.")
    if offer.status != OfferStatus.DRAFT:
        raise BusinessRuleError(
            f"Transition invalide : une offre '{offer.status.value}' ne peut pas etre soumise."
        )
    _check_offer_completeness(offer)

    return await repo.update_fields(offer_id, status=OfferStatus.SUBMITTED)


@router.patch(
    "/{offer_id}/review",
    response_model=OfferResponse,
    summary="Publier ou refuser une offre soumise (responsable pedagogique)",
)
async def review_offer(
    offer_id: int,
    payload: OfferReviewDecision,
    db: DBSession,
    _manager: Annotated[User, Depends(require_program_manager)],
) -> Offer:
    repo = OfferRepository(db)
    offer = await repo.get(offer_id)
    if offer is None:
        raise NotFoundError("Offre introuvable.")
    if offer.status != OfferStatus.SUBMITTED:
        raise BusinessRuleError(
            f"Transition invalide : seule une offre 'submitted' peut etre revue "
            f"(statut actuel : '{offer.status.value}')."
        )

    if payload.decision == "publish":
        _check_offer_completeness(offer)
        return await repo.update_fields(
            offer_id,
            status=OfferStatus.PUBLISHED,
            published_at=utcnow(),
            rejection_reason=None,
        )

    return await repo.update_fields(
        offer_id,
        status=OfferStatus.REJECTED,
        rejection_reason=payload.rejection_reason or "Non precise",
    )


@router.get(
    "/{offer_id}/applications",
    response_model=list[ApplicationResponse],
    summary="Lister les candidatures d'une offre (entreprise proprietaire ou responsable)",
)
async def list_offer_applications(
    offer_id: int,
    db: DBSession,
    current_user: CurrentUser,
    page: Annotated[PageParams, Depends(pagination_params)],
) -> list:
    offer_repo = OfferRepository(db)
    offer = await offer_repo.get(offer_id)
    if offer is None:
        raise NotFoundError("Offre introuvable.")

    is_owner_company = current_user.role == RoleEnum.COMPANY and current_user.id == offer.company_id
    is_staff = current_user.role in (RoleEnum.PROGRAM_MANAGER, RoleEnum.ADMIN)

    if not (is_owner_company or is_staff):
        # Une entreprise ne peut jamais consulter les candidatures d'une autre entreprise
        raise NotFoundError("Offre introuvable.")

    application_repo = ApplicationRepository(db)
    return await application_repo.get_by_offer(offer_id, skip=page.skip, limit=page.limit)
