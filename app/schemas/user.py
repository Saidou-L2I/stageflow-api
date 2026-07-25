import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.role import RoleEnum


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    #rajout de username
    username: str
    full_name: str
    role: RoleEnum
    company_name: str | None
    is_active: bool
    created_at: datetime.datetime


class UserRoleUpdate(BaseModel):
    """Utilise par l'admin pour forcer le changement de role d'un utilisateur."""

    role: RoleEnum
