from pydantic import BaseModel, EmailStr, Field

from app.models.role import RoleEnum


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=150)#RAJOUT
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: RoleEnum = RoleEnum.STUDENT
    company_name: str | None = Field(default=None, max_length=150)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
