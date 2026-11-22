from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database.connection import Base, engine
from backend.app.models.lead import Lead
from backend.app.api.leads import (
    router as leads_router,
    search_router
)
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI/ML Lead Generation & Opportunity Scoring System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router)

app.include_router(search_router)

@app.get("/")
def root():
    return {
        "message": "AI/ML Lead Generation System is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }