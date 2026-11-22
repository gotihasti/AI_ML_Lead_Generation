from fastapi import APIRouter, Depends, HTTPException , Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.connection import get_db
from backend.app.models.lead import Lead
from backend.app.schemas.lead import LeadCreate, LeadResponse , LeadUpdate
from backend.app.services.lead_source import search_businesses

from backend.app.services.data_cleaner import clean_lead_data

from backend.app.services.opportunity_scorer import score_lead

router = APIRouter(
    prefix="/leads",
    tags=["Leads"]
)


search_router = APIRouter(
    prefix="/search",
    tags=["Lead Search"]
)


@router.post("/", response_model=LeadResponse)
def create_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db)
):
    new_lead = Lead(**lead.model_dump())

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    return new_lead


@router.get("/", response_model=list[LeadResponse])
def get_leads(
    db: Session = Depends(get_db)
):
    return db.query(Lead).all()

#prioritizing

@router.get("/prioritized")
def get_prioritized_leads(db: Session = Depends(get_db)):
    leads = (
        db.query(Lead)
        .filter(Lead.ai_opportunity_score.isnot(None))
        .order_by(Lead.ai_opportunity_score.desc())
        .all()
    )

    return leads


@router.get("/filter")
def filter_leads(
    industry: str | None = None,
    location: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Lead)

    if industry:
        query = query.filter(
            Lead.industry.ilike(f"%{industry.strip()}%")
        )

    if location:
        query = query.filter(
            Lead.location.ilike(f"%{location.strip()}%")
        )

    return (
        query.order_by(Lead.business_name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

#stats


@router.get("/stats")
def get_lead_stats(db: Session = Depends(get_db)):
    total_leads = db.query(Lead).count()

    industry_results = (
        db.query(Lead.industry, func.count(Lead.id))
        .group_by(Lead.industry)
        .all()
    )

    priority_results = (
        db.query(Lead.opportunity_level, func.count(Lead.id))
        .group_by(Lead.opportunity_level)
        .all()
    )

    average_score = (
        db.query(func.avg(Lead.ai_opportunity_score)).scalar()
    )

    return {
        "total_leads": total_leads,
        "leads_by_industry": {
            industry or "Unknown": count
            for industry, count in industry_results
        },
        "leads_by_priority": {
            level or "Unscored": count
            for level, count in priority_results
        },
        "average_opportunity_score": round(average_score, 2)
        if average_score is not None else 0,
    }

#search by name


@router.get("/search")
def search_leads(
    business_name: str,
    db: Session = Depends(get_db),
):
    search_term = business_name.strip()

    if not search_term:
        raise HTTPException(
            status_code=400,
            detail="Business name cannot be empty.",
        )

    leads = (
        db.query(Lead)
        .filter(Lead.business_name.ilike(f"%{search_term}%"))
        .order_by(Lead.business_name.asc())
        .all()
    )

    return {
        "count": len(leads),
        "leads": leads,
    }

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    return lead



@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    update_data = lead_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    return lead



@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    db.delete(lead)
    db.commit()

    return {
        "message": "Lead deleted successfully"
    }

#Search api


@search_router.get("/leads")
def search_leads(
    industry: str = Query(...),
    location: str = Query(...)
):

    try:

        leads = search_businesses(
            industry=industry,
            location=location
        )

        return {
            "count": len(leads),
            "results": leads
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lead search failed: {str(e)}"
        )
    

@search_router.post("/leads/save")
def search_and_save_leads(
    industry: str,
    location: str,
    db: Session = Depends(get_db)
):
    try:
        businesses = search_businesses(
            industry=industry,
            location=location
        )

        saved_count = 0
        skipped_count = 0

        for business in businesses:
            business = clean_lead_data(business)
            
            existing_lead = db.query(Lead).filter(
                Lead.business_name.ilike(business["business_name"].strip()),
                Lead.location.ilike(business["location"].strip())
            ).first()

            if existing_lead:
                skipped_count += 1
                continue

            new_lead = Lead(**business)
            db.add(new_lead)
            saved_count += 1

        db.commit()

        return {
            "message": "Lead collection completed",
            "found": len(businesses),
            "saved": saved_count,
            "skipped_duplicates": skipped_count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Could not collect and save leads: {str(e)}"
        )  

#score saved leads


@router.post("/score")
def score_saved_leads(db: Session = Depends(get_db)):
    leads = db.query(Lead).all()

    updated_count = 0

    for lead in leads:
        lead_data = {
            "business_name": lead.business_name,
            "industry": lead.industry,
            "website": lead.website,
            "email": lead.email,
            "phone": lead.phone,
            "description": lead.description,
        }

        result = score_lead(lead_data)

        lead.ai_opportunity = result["ai_opportunity"]
        lead.ai_opportunity_score = result["ai_opportunity_score"]
        lead.opportunity_level = result["opportunity_level"]

        updated_count += 1

    db.commit()

    return {
        "message": "Lead scoring completed",
        "total_leads": len(leads),
        "updated": updated_count,
    }

#level of priority


@router.get("/priority/{level}")
def get_leads_by_priority(
    level: str,
    db: Session = Depends(get_db),
):
    level = level.strip().capitalize()

    if level not in ["High", "Medium", "Low"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid priority level. Use High, Medium, or Low.",
        )

    leads = (
        db.query(Lead)
        .filter(Lead.opportunity_level == level)
        .order_by(Lead.ai_opportunity_score.desc())
        .all()
    )

    return leads


