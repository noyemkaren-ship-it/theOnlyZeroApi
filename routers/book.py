from fastapi import APIRouter, Request, HTTPException
from repository import StaticBookRepository
from schemas.book import BookSchemas
from typing import Optional
from utils import JwtTokenOperation
from repository import UserRepository

router = APIRouter(tags=["Books"])

@router.get("/books")
def get_all_books():
    return StaticBookRepository.get_all_books()

@router.get("/books/{title}")
def get_book_by_title(title: str):
    return StaticBookRepository.get_book_by_title(title)

@router.post("/books")
def add_book(book: BookSchemas, request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = JwtTokenOperation.get_data_by_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        with UserRepository() as repo:
            user = repo.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            result = StaticBookRepository.add_book(book)
            return result
    except Exception as e:
        print(f"Error in add_book: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
@router.get("/book_by_creator/{creator}")
def get_book_by_creator(creator: str):
    return StaticBookRepository.get_book_by_creator(creator)

@router.get("/authors")
def get_all_authors():
    return StaticBookRepository.get_all_authors()