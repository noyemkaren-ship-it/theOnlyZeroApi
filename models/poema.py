from db import Base
from sqlalchemy import Column, Integer, String, Text

class Poema(Base):
    __tablename__ = "poemas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    author = Column(String)