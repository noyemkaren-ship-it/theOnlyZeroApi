from pydantic import BaseModel
from typing import Optional

class ArticleShemas(BaseModel):
    title: str
    text: str
    classmates: str = ""  
    creator_name: str