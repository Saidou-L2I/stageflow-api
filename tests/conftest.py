import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.role import RoleEnum
from app.models.stage import Application, Offer  # noqa: F401  (necessaire pour Base.metadata)
from app.models.user import User
from app.utils.hashing import hash_password

# Base SQLite en memoire dediee aux tests (autorisee par la consigne)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

#username
async def _create_user(db: AsyncSession, username: str, role: RoleEnum, **kwargs) -> User:
    user = User(
        email=kwargs.get("email", f"{username}@example.com"),
        username=username,
        full_name=kwargs.get("full_name", "Test User"),
        hashed_password=hash_password(kwargs.get("password", "password123")),
        role=role,
        company_name=kwargs.get("company_name"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, "modou", RoleEnum.STUDENT)


@pytest_asyncio.fixture
async def company_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session, "expresso", RoleEnum.COMPANY, company_name="Acme Corp"
    )


@pytest_asyncio.fixture
async def other_company_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session, "autre-entreprise", RoleEnum.COMPANY, company_name="Other Corp"
    )


@pytest_asyncio.fixture
async def manager_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, "fatimatou", RoleEnum.PROGRAM_MANAGER)


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, "adminlouna", RoleEnum.ADMIN)


async def auth_headers(client: AsyncClient, username: str, password: str = "password123") -> dict:
    response = await client.post(
        "/auth/login", data={"username": username, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
