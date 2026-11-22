from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.ml.lead_model import load_model, predict, train_model
from backend.app.models.lead import Lead

router = APIRouter(prefix="/ml", tags=["ML Scoring"])


@router.post("/train")
def train(db: Session = Depends(get_db)):
    """Retrain the model, using leads whose status records an outcome."""
    return train_model(db.query(Lead).all())


@router.get("/info")
def info():
    return load_model()["info"]


@router.post("/score")
def score_all(db: Session = Depends(get_db)):
    """Score every lead with the trained model and store the result."""
    bundle = load_model()
    leads = db.query(Lead).all()
    for lead in leads:
        result = predict(lead, bundle)
        lead.ai_opportunity = result["ai_opportunity"]
        lead.ai_opportunity_score = result["ai_opportunity_score"]
        lead.opportunity_level = result["opportunity_level"]
    db.commit()
    return {"message": "ML scoring completed", "total_leads": len(leads),
            "updated": len(leads), "model_source": bundle["info"]["model_source"]}
