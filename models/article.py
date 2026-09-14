from db.base import Base
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    text = Column(Text)
    classmates = Column(String, default="")
    creator_name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)