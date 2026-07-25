import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_creates_user(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "nouveau@example.com",
            #ajouter nouvellement
            "username" : "autre_etudiant",
            "full_name": "Nouvel Etudiant",
            "password": "password123",
            "role": "student",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "autre_etudiant"
    assert data["role"] == "student"
    assert "hashed_password" not in data  # le schema de sortie ne doit jamais l'exposer


async def test_register_duplicate_email_returns_400(client: AsyncClient):
    payload = {
        "email": "duplique@example.com",
        "username": "autre_etudiant",
        "full_name": "Duplicate",
        "password": "password123",
        "role": "student",
    }
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 400


async def test_login_success_returns_token(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
             "username": "autre_etudiant",
            "full_name": "Login User",
            "password": "password123",
            "role": "student",
        },
    )
    #remplacement de uername par le vrai nom
    response = await client.post(
        "/auth/login",
        data={"username": "autre_etudiant", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "username": "autre_etudiant",
            "full_name": "User",
            "password": "password123",
            "role": "student",
        },
    )
    response = await client.post(
        "/auth/login",
        data={"username": "mauvais non d'utilsateur", "password": "incorrect"},
    )
    assert response.status_code == 401


async def test_get_me_requires_authentication(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_get_me_returns_current_user(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "username": "autre_etudiant",
            "full_name": "Me User",
            "password": "password123",
            "role": "student",
        },
    )
    login = await client.post(
        "/auth/login",
        data={"username": "autre_etudiant", "password": "password123"},
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    #utilistion du username
    assert response.status_code == 200
    assert response.json()["username"] == "autre_etudiant"
