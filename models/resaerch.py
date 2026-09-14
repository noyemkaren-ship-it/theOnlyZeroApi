from db import Base
from sqlalchemy import Column, Integer, String

class Research(Base):
    __tablename__ = "researches"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    document_path = Column(String, index=True)
    creator = Column(String, index=True)