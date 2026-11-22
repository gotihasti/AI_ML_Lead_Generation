import re
import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

INDUSTRY_QUERIES = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "hotel": "hotel",
    "hospital": "hospital",
    "pharmacy": "pharmacy",
    "school": "school",
}


def normalize_business_name(name: str) -> str:
    """Normalize a business name for duplicate comparison."""
    name = name.casefold().strip()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name


def search_businesses(industry: str, location: str):
    industry = industry.lower().strip()
    location = location.strip()

    if industry not in INDUSTRY_QUERIES:
        raise ValueError(
            f"Unsupported industry. Available: "
            f"{', '.join(INDUSTRY_QUERIES.keys())}"
        )

    search_term = INDUSTRY_QUERIES[industry]

    params = {
        "q": f"{search_term} in {location}, India",
        "format": "jsonv2",
        "limit": 40,
        "addressdetails": 1,
        "extratags": 1,
        "namedetails": 1,
        "countrycodes": "in",
        "layer": "poi",
    }

    headers = {
        "User-Agent": "AI-ML-Lead-Generation-System/1.0"
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Business search failed: {exc}"
        ) from exc

    leads = []
    seen_names = set()

    for item in data:
        extra = item.get("extratags") or {}
        names = item.get("namedetails") or {}

        business_name = (
            item.get("name")
            or names.get("name")
            or item.get("display_name", "").split(",")[0]
        )

        if not business_name or not business_name.strip():
            continue

        normalized_name = normalize_business_name(business_name)
        normalized_location = location.casefold().strip()

        unique_key = (normalized_name, normalized_location)

        if unique_key in seen_names:
            continue

        seen_names.add(unique_key)

        leads.append({
            "business_name": business_name.strip(),
            "industry": industry,
            "location": location,
            "website": (
                extra.get("website")
                or extra.get("contact:website")
            ),
            "email": (
                extra.get("email")
                or extra.get("contact:email")
            ),
            "phone": (
                extra.get("phone")
                or extra.get("contact:phone")
            ),
            "description": extra.get("description"),
        })

    return leads
