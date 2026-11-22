def score_lead(lead):
    """
    Calculate a rule-based opportunity score from 0 to 100.
    Higher scores indicate more potential opportunities to investigate.
    """

    def get_value(field):
        if isinstance(lead, dict):
            return lead.get(field)
        return getattr(lead, field, None)

    score = 0
    opportunities = []

    # Website
    website = get_value("website")
    if not website or not str(website).strip():
        score += 25
        opportunities.append("Website development")

    # Email
    email = get_value("email")
    if not email or not str(email).strip():
        score += 10
        opportunities.append("Email contact information missing")

    # Phone
    phone = get_value("phone")
    if not phone or not str(phone).strip():
        score += 10
        opportunities.append("Phone contact information missing")

    # Business description
    description = get_value("description")
    if not description or not str(description).strip():
        score += 5
        opportunities.append("Business profile could be improved")

    # Industry
    industry = (get_value("industry") or "").strip().lower()

    if industry in ["restaurant", "cafe", "hotel"]:
        score += 15
        opportunities.append("Potential digital marketing opportunity")
    elif industry:
        score += 5
        opportunities.append("General digital improvement opportunity")

    # Keep the score between 0 and 100
    score = max(0, min(score, 100))

    # Assign priority
    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    opportunity = ", ".join(opportunities) if opportunities else (
        "No obvious opportunity identified by current rules"
    )

    return {
        "ai_opportunity": opportunity,
        "ai_opportunity_score": score,
        "opportunity_level": level,
    }
