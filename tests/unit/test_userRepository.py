import pytest

from app.models.role import RoleEnum
from app.repositories.user_repository import UserRepository

pytestmark = pytest.mark.asyncio


async def test_set_role(db_session, student_user):
    repo = UserRepository(db_session)

    updated_user = await repo.set_role(student_user.id, RoleEnum.COMPANY)

    assert updated_user is not None
    assert updated_user.role == RoleEnum.COMPANY

    user = await repo.get(student_user.id)
    assert user.role == RoleEnum.COMPANY