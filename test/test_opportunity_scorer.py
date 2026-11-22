
from backend.app.services.opportunity_scorer import score_lead


def test_lead_with_missing_website():
    lead = {
        "business_name": "Example Restaurant",
        "industry": "restaurant",
        "website": None,
        "email": "example@test.com",
        "phone": "1234567890",
        "description": "A local restaurant",
    }

    result = score_lead(lead)

    assert result["ai_opportunity_score"] == 40
    assert "Website development" in result["ai_opportunity"]
    assert result["opportunity_level"] == "Medium"


def test_score_never_exceeds_100():
    lead = {
        "business_name": "Example Cafe",
        "industry": "cafe",
        "website": None,
        "email": None,
        "phone": None,
        "description": None,
    }

    result = score_lead(lead)

    assert 0 <= result["ai_opportunity_score"] <= 100
