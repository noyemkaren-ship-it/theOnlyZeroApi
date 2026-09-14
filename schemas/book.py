from pydantic import BaseModel

class BookSchemas(BaseModel):
    title: str
    description: str
    classmets: str
    review: int
    author: str
    creators: str
    file_name: str
