from app.models.stage import Offer


def test_offer_not_ready_when_missing_fields():
    offer = Offer(title="Stage Data", mission=None, skills="Python", company_id=1)
    assert offer.is_ready_for_publication is False


def test_offer_ready_when_all_fields_present():
    offer = Offer(
        title="Stage Data",
        mission="Analyse de donnees",
        skills="Python, SQL",
        company_id=1,
    )
    assert offer.is_ready_for_publication is True
