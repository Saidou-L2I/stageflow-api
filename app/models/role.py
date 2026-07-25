"""Roles applicatifs pour le workflow StageFlow."""
import enum


class RoleEnum(str, enum.Enum):
    STUDENT = "student"
    COMPANY = "company"
    PROGRAM_MANAGER = "program_manager"
    ADMIN = "admin"
