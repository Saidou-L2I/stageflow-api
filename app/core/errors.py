"""Exceptions metier centralisees et handlers associes.

Convention de statuts HTTP imposee par le sujet :
- 400 : regle metier invalide
- 401 : non authentifie
- 403 : non habilite
- 404 : ressource absente ou non visible
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Exception de base pour toutes les erreurs metier de l'application."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class BusinessRuleError(AppError):
    """400 - une regle metier (invariant) n'est pas respectee."""

    status_code = status.HTTP_400_BAD_REQUEST


class NotAuthenticatedError(AppError):
    """401 - l'utilisateur n'est pas authentifie ou le token est invalide."""

    status_code = status.HTTP_401_UNAUTHORIZED


class NotAuthorizedError(AppError):
    """403 - l'utilisateur est authentifie mais n'a pas l'habilitation requise."""

    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(AppError):
    """404 - ressource absente ou non visible pour cet utilisateur."""

    status_code = status.HTTP_404_NOT_FOUND


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
