from pydantic import BaseModel


class ResearchCreate(BaseModel):
    title: str
    description: str
    document_path: str
    creator: str