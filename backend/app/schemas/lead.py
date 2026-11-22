from pydantic import BaseModel, ConfigDict , Field


class LeadCreate(BaseModel):
    business_name: str = Field(
        ...,
        min_length=2,
        max_length=255
    )
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    description: str | None = None

class LeadUpdate(BaseModel):
    
    business_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255  
    )

    industry: str | None = None
    location: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    description: str | None = None
    ai_opportunity: str | None = None
    ai_opportunity_score: int | None = Field(
    default=None,
    ge=0,
    le=100
)
    opportunity_level: str | None = None
    status: str | None = None

class LeadResponse(LeadCreate):
    id: int
    ai_opportunity: str | None = None
    ai_opportunity_score: int | None = None
    opportunity_level: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)