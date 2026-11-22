import re
from urllib.parse import urlparse


def clean_text(value):
    if not value:
        return None

    value = " ".join(value.split())

    return value or None


def clean_email(email):
    if not email:
        return None

    email = email.strip().lower()

    if "@" not in email:
        return None

    return email


def clean_phone(phone):
    if not phone:
        return None

    phone = phone.strip()

    # Keep digits and an optional leading +
    phone = re.sub(r"[^\d+]", "", phone)

    if not phone or phone == "+":
        return None

    return phone


def clean_website(website):
    if not website:
        return None

    website = website.strip()

    if not website:
        return None

    if not website.startswith(("http://", "https://")):
        website = "https://" + website

    parsed = urlparse(website)

    if not parsed.netloc or "." not in parsed.netloc:
        return None

    return website



def clean_lead_data(lead):
    # Support both dictionaries and objects
    if isinstance(lead, dict):
        cleaned_lead = lead.copy()
        get_value = lead.get
    else:
        cleaned_lead = vars(lead).copy()
        get_value = lambda key: getattr(lead, key, None)

    cleaned_lead["business_name"] = clean_text(
        get_value("business_name")
    )

    cleaned_lead["industry"] = clean_text(
        get_value("industry")
    )

    if cleaned_lead["industry"]:
        cleaned_lead["industry"] = cleaned_lead["industry"].lower()

    cleaned_lead["location"] = clean_text(
        get_value("location")
    )

    cleaned_lead["website"] = clean_website(
        get_value("website")
    )

    cleaned_lead["email"] = clean_email(
        get_value("email")
    )

    cleaned_lead["phone"] = clean_phone(
        get_value("phone")
    )

    cleaned_lead["description"] = clean_text(
        get_value("description")
    )

    return cleaned_lead   
