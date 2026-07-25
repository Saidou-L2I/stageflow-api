import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.permissions import require_admin
from app.core.security import CurrentUser
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserRoleUpdate

router = APIRouter(tags=["Utilisateurs"])
logger = logging.getLogger("stageflow.users")

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/users/me", response_model=UserResponse, summary="Profil de l'utilisateur connecte")
async def read_me(current_user: CurrentUser) -> User:
    return current_user


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Consulter un utilisateur (reserve a l'administrateur)",
)
async def get_user(
    user_id: int,
    db: DBSession,
    _admin: Annotated[User, Depends(require_admin)],
) -> User:
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if user is None:
        raise NotFoundError("Utilisateur introuvable.")
    return user


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Forcer le changement de role d'un utilisateur (admin uniquement)",
)
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: DBSession,
    admin: Annotated[User, Depends(require_admin)],
) -> User:
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if user is None:
        raise NotFoundError("Utilisateur introuvable.")

    updated = await repo.set_role(user_id, payload.role)
    logger.info(
        "user_role_changed",
        extra={
            "actor_id": admin.id,
            "target_user_id": user_id,
            "new_role": payload.role.value,
        },
    )
    return updated
