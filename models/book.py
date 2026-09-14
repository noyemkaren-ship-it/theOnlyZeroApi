from db.base import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

class Book(Base):
    __tablename__ = 'books'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    description = Column(Text, default="")
    classmets = Column(String, default="")
    review = Column(Integer, default=0)
    author = Column(String, index=True)  # Пользователь, который выложил книгу
    creators = Column(String, default="")  # Авторы самой книги
    file_name = Column(String)  # Имя файла в uploads
    created_at = Column(DateTime, default=datetime.utcnow)