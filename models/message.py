from db import Base
from sqlalchemy import Column, Integer, String


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    getter_name = Column(String, nullable=False)