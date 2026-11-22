from types import SimpleNamespace

from backend.app.services.data_cleaner import clean_lead_data

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))



def test_clean_lead_data():
    lead = SimpleNamespace(
        business_name="  Example   Restaurant ",
        industry=" restaurant ",
        location=" Surat ",
        website="www.example.com",
        email=" TEST@EXAMPLE.COM ",
        phone="+91 98765 43210",
        description=" A sample business "
    )

    result = clean_lead_data(lead)

    assert result["business_name"] == "Example Restaurant"
    assert result["industry"] == "restaurant"
    assert result["location"] == "Surat"
    assert result["website"] == "https://www.example.com"
    assert result["email"] == "test@example.com"
    assert result["phone"] == "+919876543210"
    assert result["description"] == "A sample business"

    print("Data cleaning test passed!")


if __name__ == "__main__":
    test_clean_lead_data()