import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def test_company_can_create_draft_offer(client: AsyncClient, company_user):
    #company_user.email=>company_user.username
    headers = await auth_headers(client, company_user.username)
    response = await client.post(
        "/offers",
        json={"title": "Stage Data Analyst", "mission": "Analyse", "skills": "Python"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "draft"


async def test_student_cannot_create_offer(client: AsyncClient, student_user):
    #student_user.email=>student_user.username
    headers = await auth_headers(client, student_user.username)
    response = await client.post(
        "/offers",
        json={"title": "Stage", "mission": "Mission", "skills": "SQL"},
        headers=headers,
    )
    assert response.status_code == 403


async def test_submit_incomplete_offer_returns_400(client: AsyncClient, company_user):
    #company_user.email=>company_user.username
    headers = await auth_headers(client, company_user.username)
    create = await client.post(
        "/offers", json={"title": "Stage sans mission"}, headers=headers
    )
    offer_id = create.json()["id"]

    response = await client.patch(f"/offers/{offer_id}/submit", headers=headers)
    assert response.status_code == 400


async def test_full_publish_workflow(client: AsyncClient, company_user, manager_user):
    #company_user.email, manager_user.email=>company_user.username, manager_user.username
    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)

    create = await client.post(
        "/offers",
        json={"title": "Stage Data", "mission": "Analyse", "skills": "Python, SQL"},
        headers=company_headers,
    )
    offer_id = create.json()["id"]

    submit = await client.patch(f"/offers/{offer_id}/submit", headers=company_headers)
    assert submit.status_code == 200
    assert submit.json()["status"] == "submitted"

    review = await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "publish"},
        headers=manager_headers,
    )
    assert review.status_code == 200
    assert review.json()["status"] == "published"
    assert review.json()["published_at"] is not None


async def test_review_by_non_manager_is_forbidden(
    client: AsyncClient, company_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)#userame
    student_headers = await auth_headers(client, student_user.username)

    create = await client.post(
        "/offers",
        json={"title": "Stage", "mission": "Mission", "skills": "Python"},
        headers=company_headers,
    )
    offer_id = create.json()["id"]
    await client.patch(f"/offers/{offer_id}/submit", headers=company_headers)

    response = await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "publish"},
        headers=student_headers,
    )
    assert response.status_code == 403


async def test_review_invalid_transition_returns_400(client: AsyncClient, company_user, manager_user):
    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)

    create = await client.post(
        "/offers",
        json={"title": "Stage", "mission": "Mission", "skills": "Python"},
        headers=company_headers,
    )
    offer_id = create.json()["id"]
    # L'offre est encore en 'draft', pas 'submitted'
    response = await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "publish"},
        headers=manager_headers,
    )
    assert response.status_code == 400


async def test_student_sees_only_published_offers(
    client: AsyncClient, company_user, manager_user, student_user
):
    company_headers = await auth_headers(client, company_user.username)
    manager_headers = await auth_headers(client, manager_user.username)
    student_headers = await auth_headers(client, student_user.username)

    create = await client.post(
        "/offers",
        json={"title": "Stage Cache", "mission": "Mission", "skills": "Python"},
        headers=company_headers,
    )
    offer_id = create.json()["id"]

    response = await client.get("/offers", headers=student_headers)
    assert response.status_code == 200
    assert all(o["id"] != offer_id for o in response.json())

    await client.patch(f"/offers/{offer_id}/submit", headers=company_headers)
    await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "publish"},
        headers=manager_headers,
    )

    response = await client.get("/offers", headers=student_headers)
    assert any(o["id"] == offer_id for o in response.json())


async def test_company_cannot_see_applications_of_another_company(
    client: AsyncClient, company_user, other_company_user
):
    """Test d'isolation explicitement demande par le sujet."""
    own_headers = await auth_headers(client, company_user.username)
    other_headers = await auth_headers(client, other_company_user.username)

    create = await client.post(
        "/offers",
        json={"title": "Stage prive", "mission": "Mission", "skills": "Python"},
        headers=own_headers,
    )
    offer_id = create.json()["id"]

    response = await client.get(f"/offers/{offer_id}/applications", headers=other_headers)
    assert response.status_code == 404


async def test_stats_endpoint_forbidden_for_company(client: AsyncClient, company_user):
    headers = await auth_headers(client, company_user.username)
    response = await client.get("/offers/stats", headers=headers)
    assert response.status_code == 403


async def test_stats_endpoint_accessible_for_manager(client: AsyncClient, manager_user):
    headers = await auth_headers(client, manager_user.username)
    response = await client.get("/offers/stats", headers=headers)
    assert response.status_code == 200
    assert "offers_by_status" in response.json()
    assert "applications_by_status" in response.json()

#####################################
#Amelioration du test
########################################

#Offre inexistante
async def test_get_unknown_offer(client: AsyncClient, student_user):
    headers = await auth_headers(client, student_user.username)

    response = await client.get("/offers/9999", headers=headers)

    assert response.status_code == 404

#Le propriétaire peut consulter son brouillon
async def test_company_can_get_own_draft_offer(client: AsyncClient, company_user):
    headers = await auth_headers(client, company_user.username)

    create = await client.post(
        "/offers",
        json={
            "title": "Stage",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=headers,
    )

    offer_id = create.json()["id"]

    response = await client.get(f"/offers/{offer_id}", headers=headers)

    assert response.status_code == 200

#Une autre entreprise ne peut pas consulter le brouillon d'une entreprise
async def test_company_cannot_get_other_company_offer(
    client: AsyncClient,
    company_user,
    other_company_user,
):
    owner = await auth_headers(client, company_user.username)
    other = await auth_headers(client, other_company_user.username)

    create = await client.post(
        "/offers",
        json={
            "title": "Secret",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=owner,
    )

    offer_id = create.json()["id"]

    response = await client.get(f"/offers/{offer_id}", headers=other)

    assert response.status_code == 404

#Tester le rejet d'une offre
async def test_manager_can_reject_offer(
    client: AsyncClient,
    company_user,
    manager_user,
):
    company = await auth_headers(client, company_user.username)
    manager = await auth_headers(client, manager_user.username)

    create = await client.post(
        "/offers",
        json={
            "title": "Stage",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=company,
    )

    offer_id = create.json()["id"]

    await client.patch(
        f"/offers/{offer_id}/submit",
        headers=company,
    )

    response = await client.patch(
        f"/offers/{offer_id}/review",
        json={
            "decision": "reject",
            "rejection_reason": "Profil insuffisant",
        },
        headers=manager,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
#Une entreprise ne peut pas modifier l'offre d'une autre entreprise
async def test_company_cannot_update_other_company_offer(
    client: AsyncClient,
    company_user,
    other_company_user,
):
    owner = await auth_headers(client, company_user.username)
    other = await auth_headers(client, other_company_user.username)

    create = await client.post(
        "/offers",
        json={
            "title": "Stage",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=owner,
    )

    offer_id = create.json()["id"]

    response = await client.patch(
        f"/offers/{offer_id}",
        json={
            "title": "Nouveau titre",
            "mission": "Nouvelle mission",
            "skills": "SQL",
        },
        headers=other,
    )

    assert response.status_code == 403
#Modifier une offre publiée
async def test_company_cannot_update_published_offer(
    client: AsyncClient,
    company_user,
    manager_user,
):
    company = await auth_headers(client, company_user.username)
    manager = await auth_headers(client, manager_user.username)

    create = await client.post(
        "/offers",
        json={
            "title": "Stage",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=company,
    )

    offer_id = create.json()["id"]

    await client.patch(f"/offers/{offer_id}/submit", headers=company)

    await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "publish"},
        headers=manager,
    )

    response = await client.patch(
        f"/offers/{offer_id}",
        json={
            "title": "Modification",
            "mission": "Mission",
            "skills": "SQL",
        },
        headers=company,
    )

    assert response.status_code == 400
#Une entreprise voit uniquement ses offres
async def test_company_lists_only_its_offers(
    client: AsyncClient,
    company_user,
    other_company_user,
):
    company = await auth_headers(client, company_user.username)
    other = await auth_headers(client, other_company_user.username)

    await client.post(
        "/offers",
        json={
            "title": "Offre A",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=company,
    )

    await client.post(
        "/offers",
        json={
            "title": "Offre B",
            "mission": "Mission",
            "skills": "Java",
        },
        headers=other,
    )

    response = await client.get("/offers", headers=company)

    assert response.status_code == 200
    assert all(o["company_id"] == company_user.id for o in response.json())

#Le responsable voit toutes les offres
async def test_manager_lists_all_offers(
    client: AsyncClient,
    company_user,
    other_company_user,
    manager_user,
):
    company = await auth_headers(client, company_user.username)
    other = await auth_headers(client, other_company_user.username)
    manager = await auth_headers(client, manager_user.username)

    await client.post(
        "/offers",
        json={
            "title": "Offre A",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=company,
    )

    await client.post(
        "/offers",
        json={
            "title": "Offre B",
            "mission": "Mission",
            "skills": "Java",
        },
        headers=other,
    )

    response = await client.get("/offers", headers=manager)

    assert response.status_code == 200
    assert len(response.json()) >= 2

#Soumettre une offre inexistante
async def test_submit_unknown_offer(
    client: AsyncClient,
    company_user,
):
    headers = await auth_headers(client, company_user.username)

    response = await client.patch(
        "/offers/9999/submit",
        headers=headers,
    )

    assert response.status_code == 404

#une autre entreprise ne peut pas soumettre ton offre(l'offre d'une autre)
async def test_other_company_cannot_submit_offer(
    client: AsyncClient,
    company_user,
    other_company_user,
):
    owner = await auth_headers(client, company_user.username)
    other = await auth_headers(client, other_company_user.username)

    create = await client.post(
        "/offers",
        json={
            "title": "Stage",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=owner,
    )

    offer_id = create.json()["id"]

    response = await client.patch(
        f"/offers/{offer_id}/submit",
        headers=other,
    )

    assert response.status_code == 403

#Refuser une offre sans motif
async def test_manager_reject_offer_without_reason(
    client: AsyncClient,
    company_user,
    manager_user,
):
    company = await auth_headers(client, company_user.username)
    manager = await auth_headers(client, manager_user.username)

    create = await client.post(
        "/offers",
        json={
            "title": "Stage",
            "mission": "Mission",
            "skills": "Python",
        },
        headers=company,
    )

    offer_id = create.json()["id"]

    await client.patch(f"/offers/{offer_id}/submit", headers=company)

    response = await client.patch(
        f"/offers/{offer_id}/review",
        json={"decision": "reject"},
        headers=manager,
    )

    assert response.status_code == 200
    assert response.json()["rejection_reason"] == "Non precise"