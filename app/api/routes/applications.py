import datetime
# Fonction utilitaire qui renvoie la date et l'heure actuelles en UTC (timezone-aware)
from app.utils.time import utcnow
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.errors import BusinessRuleError, NotAuthorizedError, NotFoundError
from app.core.permissions import require_program_manager, require_student
from app.core.security import CurrentUser, DBSession
from app.models.role import RoleEnum
from app.models.stage import Application, ApplicationStatus, OfferStatus
from app.models.user import User
from app.repositories.stage_repository import ApplicationRepository, OfferRepository
from app.schemas.stage import ApplicationCreate, ApplicationDecision, ApplicationResponse
from app.utils.pagination import PageParams, pagination_params

router = APIRouter(tags=["Candidatures"])


@router.post(
    "/offers/{offer_id}/applications",
    response_model=ApplicationResponse,
    status_code=201,
    summary="Postuler a une offre publiee (etudiant)",
)
async def create_application(
    offer_id: int,
    payload: ApplicationCreate,
    db: DBSession,
    student: Annotated[User, Depends(require_student)],
) -> Application:
    offer_repo = OfferRepository(db)
    offer = await offer_repo.get(offer_id)
    if offer is None or offer.status != OfferStatus.PUBLISHED:
        # Une offre non publiee n'est pas visible/candidate-able pour un etudiant
        raise NotFoundError("Offre introuvable.")

    application_repo = ApplicationRepository(db)
    existing = await application_repo.get_active_for_student_and_offer(student.id, offer_id)
    if existing is not None:
        raise BusinessRuleError("Vous avez deja une candidature active sur cette offre.")

    application = Application(
        offer_id=offer_id,
        student_id=student.id,
        cover_letter=payload.cover_letter,
        status=ApplicationStatus.PENDING,
    )
    return await application_repo.create(application)


@router.get(
    "/applications/me",
    response_model=list[ApplicationResponse],
    summary="Lister mes candidatures (etudiant)",
)
async def list_my_applications(
    db: DBSession,
    student: Annotated[User, Depends(require_student)],
    page: Annotated[PageParams, Depends(pagination_params)],
) -> list[Application]:
    repo = ApplicationRepository(db)
    return await repo.get_by_student(student.id, skip=page.skip, limit=page.limit)


@router.patch(
    "/applications/{application_id}/decision",
    response_model=ApplicationResponse,
    summary="Accepter ou refuser une candidature (responsable pedagogique)",
)
async def decide_application(
    application_id: int,
    payload: ApplicationDecision,
    db: DBSession,
    _manager: Annotated[User, Depends(require_program_manager)],
) -> Application:
    repo = ApplicationRepository(db)
    application = await repo.get(application_id)
    if application is None:
        raise NotFoundError("Candidature introuvable.")
    if application.status != ApplicationStatus.PENDING:
        raise BusinessRuleError(
            f"Transition invalide : seule une candidature 'pending' peut etre decidee "
            f"(statut actuel : '{application.status.value}')."
        )

    new_status = (
        ApplicationStatus.ACCEPTED
        if payload.decision == "accepted"
        else ApplicationStatus.REJECTED
    )
    return await repo.update_fields(
        application_id,
        status=new_status,
        decided_at=utcnow(),
    )


@router.delete(
    "/applications/{application_id}",
    status_code=204,
    summary="Retirer sa candidature (etudiant, tant qu'elle n'est pas acceptee)",
)
async def withdraw_application(
    application_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    repo = ApplicationRepository(db)
    application = await repo.get(application_id)
    if application is None:
        raise NotFoundError("Candidature introuvable.")

    is_owner = current_user.role == RoleEnum.STUDENT and current_user.id == application.student_id
    if not is_owner:
        raise NotAuthorizedError("Vous ne pouvez retirer que vos propres candidatures.")

    if application.status == ApplicationStatus.ACCEPTED:
        raise BusinessRuleError("Une candidature acceptee ne peut plus etre retiree.")

    await repo.update_fields(
        application_id,
        status=ApplicationStatus.WITHDRAWN,
        decided_at=utcnow(),
    )
