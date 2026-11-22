from sqlalchemy import Column, Integer, String, Text
from backend.app.database.connection import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    business_name = Column(String(255), nullable=False)
    industry = Column(String(100))
    location = Column(String(255))

    website = Column(String(500))
    email = Column(String(255))
    phone = Column(String(50))

    description = Column(Text)

    ai_opportunity = Column(String(255))
    ai_opportunity_score = Column(Integer)
    opportunity_level = Column(String(20))

    status = Column(String(50), default="new")


    