from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotAuthenticatedError
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, Token
from app.schemas.user import UserResponse
from app.utils.hashing import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentification"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Creer un compte (etudiant, entreprise ou responsable pedagogique)",
)
async def register(payload: RegisterRequest, db: DBSession) -> User:
    repo = UserRepository(db)
    existing = await repo.get_by_email(payload.email)
    if existing is not None:
        raise BusinessRuleError("Un compte existe deja avec cet email.")

    user = User(
        email=payload.email,
        #nouvellement ajoute
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        company_name=payload.company_name,
    )
    return await repo.create(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Authentification OAuth2 password flow, retourne un JWT",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
) -> Token:
    repo = UserRepository(db)
    user = await repo.get_by_username(form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise NotAuthenticatedError("Email ou mot de passe incorrect.")
    if not user.is_active:
        raise NotAuthenticatedError("Compte desactive.")

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)
