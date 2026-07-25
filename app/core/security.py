"""Authentification JWT (OAuth2 password flow) et dependances associees."""
import datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotAuthenticatedError
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )"""
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str:
    """Retourne le 'sub' (identifiant utilisateur) contenu dans le token, ou leve NotAuthenticatedError."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise NotAuthenticatedError("Token invalide")
        return subject
    except JWTError as exc:
        raise NotAuthenticatedError("Token invalide ou expire") from exc


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSession,
) -> User:
    user_id = decode_access_token(token)
    try:
        user_id_int = int(user_id)
    except ValueError as exc:
        raise NotAuthenticatedError("Token invalide") from exc

    repo = UserRepository(db)
    user = await repo.get(user_id_int)
    if user is None or not user.is_active:
        raise NotAuthenticatedError("Utilisateur introuvable ou inactif")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
