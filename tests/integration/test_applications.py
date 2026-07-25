import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def _create_published_offer(client: AsyncClient, company_headers, manager_headers) -> int:
    create = await client.post(
        "/offers",
        json={"title": "Stage Data", "mission": "Analyse", "skills": "Python"},
        headers=company_headers,
    )
    offer_id = create.json()["id"]
    await client.patch(f"/offers/{offer_id}/submit", headers=company_headers)
    await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "publish"},
        headers=manager_headers,
    )
    return offer_id


async def test_student_can_apply_to_published_offer(
    client: AsyncClient, company_user, manager_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)#utilisation de username
    manager_headers = await auth_headers(client, manager_user.username)#utilisation de username
    student_headers = await auth_headers(client, student_user.username)#utilisation de username

    offer_id = await _create_published_offer(client, company_headers, manager_headers)

    response = await client.post(
        f"/offers/{offer_id}/applications",
        json={"cover_letter": "Motive !"},
        headers=student_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


async def test_cannot_apply_twice_actively_to_same_offer(
    client: AsyncClient, company_user, manager_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)
    student_headers = await auth_headers(client, student_user.username)

    offer_id = await _create_published_offer(client, company_headers, manager_headers)

    first = await client.post(
        f"/offers/{offer_id}/applications", json={}, headers=student_headers
    )
    assert first.status_code == 201

    second = await client.post(
        f"/offers/{offer_id}/applications", json={}, headers=student_headers
    )
    assert second.status_code == 400


async def test_cannot_apply_to_draft_offer(
    client: AsyncClient, company_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)
    student_headers = await auth_headers(client, student_user.username)

    create = await client.post(
        "/offers",
        json={"title": "Stage brouillon", "mission": "Mission", "skills": "Python"},
        headers=company_headers,
    )
    offer_id = create.json()["id"]

    response = await client.post(
        f"/offers/{offer_id}/applications", json={}, headers=student_headers
    )
    assert response.status_code == 404


async def test_manager_can_accept_application(
    client: AsyncClient, company_user, manager_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)
    student_headers = await auth_headers(client, student_user.username)

    offer_id = await _create_published_offer(client, company_headers, manager_headers)
    application = await client.post(
        f"/offers/{offer_id}/applications", json={}, headers=student_headers
    )
    application_id = application.json()["id"]

    response = await client.patch(
        f"/applications/{application_id}/decision",
        json={"decision": "accepted"},
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


async def test_student_cannot_withdraw_accepted_application(
    client: AsyncClient, company_user, manager_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)
    student_headers = await auth_headers(client, student_user.username)

    offer_id = await _create_published_offer(client, company_headers, manager_headers)
    application = await client.post(
        f"/offers/{offer_id}/applications", json={}, headers=student_headers
    )
    application_id = application.json()["id"]

    await client.patch(
        f"/applications/{application_id}/decision",
        json={"decision": "accepted"},
        headers=manager_headers,
    )

    response = await client.delete(
        f"/applications/{application_id}", headers=student_headers
    )
    assert response.status_code == 400


async def test_student_can_withdraw_pending_application(
    client: AsyncClient, company_user, manager_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)
    student_headers = await auth_headers(client, student_user.username)

    offer_id = await _create_published_offer(client, company_headers, manager_headers)
    application = await client.post(
        f"/offers/{offer_id}/applications", json={}, headers=student_headers
    )
    application_id = application.json()["id"]

    response = await client.delete(
        f"/applications/{application_id}", headers=student_headers
    )
    assert response.status_code == 204


async def test_another_student_cannot_withdraw_application(
    client: AsyncClient, company_user, manager_user, student_user, db_session
):
    from app.models.role import RoleEnum
    from app.utils.hashing import hash_password
    from app.models.user import User

    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)
    student_headers = await auth_headers(client, student_user.username)

    other_student = User(
        email="autre-etudiant@example.com",
        #username ajoute
        username="autre_etudiant_new",
        full_name="Autre Etudiant",
        hashed_password=hash_password("password123"),
        role=RoleEnum.STUDENT,
    )
    db_session.add(other_student)
    await db_session.commit()
    other_headers = await auth_headers(client, "autre_etudiant_new")

    offer_id = await _create_published_offer(client, company_headers, manager_headers)
    application = await client.post(
        f"/offers/{offer_id}/applications", json={}, headers=student_headers
    )
    application_id = application.json()["id"]

    response = await client.delete(
        f"/applications/{application_id}", headers=other_headers
    )
    assert response.status_code == 403
