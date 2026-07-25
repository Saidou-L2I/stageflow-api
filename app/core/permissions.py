"""Autorisation centralisee (RBAC) : dependances FastAPI reutilisables par les routes.

Objectif: "les routes ne doivent pas contenir de logique RBAC dispersee".
Toute la logique d'habilitation transite par les fonctions/dependances de ce module.
"""
from app.core.errors import NotAuthorizedError
from app.core.security import CurrentUser
from app.models.role import RoleEnum
from app.models.user import User


def require_roles(*allowed_roles: RoleEnum):
    """Fabrique une dependance FastAPI qui verifie que l'utilisateur courant
    possede l'un des roles autorises."""

    async def dependency(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise NotAuthorizedError(
                f"Role '{current_user.role.value}' non habilite pour cette action."
            )
        return current_user

    return dependency


# Dependances pretes a l'emploi pour les roles les plus courants
require_student = require_roles(RoleEnum.STUDENT)
require_company = require_roles(RoleEnum.COMPANY)
require_program_manager = require_roles(RoleEnum.PROGRAM_MANAGER)
require_admin = require_roles(RoleEnum.ADMIN)
require_staff = require_roles(RoleEnum.PROGRAM_MANAGER, RoleEnum.ADMIN)


"""def ensure_is_owner_or_staff(current_user: User, owner_id: int) -> None:
    #Verifie que l'utilisateur courant est le proprietaire de la ressource,
    #ou un membre du staff (program_manager / admin).
    if current_user.id == owner_id:
        return
    if current_user.role in (RoleEnum.PROGRAM_MANAGER, RoleEnum.ADMIN):
        return
    raise NotAuthorizedError("Vous n'etes pas habilite a acceder a cette ressource.")"""
