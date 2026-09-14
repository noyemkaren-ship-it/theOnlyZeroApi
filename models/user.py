from db import Base
from sqlalchemy import (
    Column,
    Integer,
    String, Boolean
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    hesh_password = Column(String)
    banned = Column(Boolean, default=False)
    description = Column(String)