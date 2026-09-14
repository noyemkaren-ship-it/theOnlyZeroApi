from models import Book
from db import Session
from schemas.book import BookSchemas

class StaticBookRepository:
    
    @staticmethod
    def get_all_books():
        session = Session()
        try:
            books = session.query(Book).all()
            return books
        finally:
            session.close()

    @staticmethod
    def get_book_by_title(title: str):
        session = Session()
        try:
            book = session.query(Book).filter(Book.title == title).first()
            return book
        finally:
            session.close()

    @staticmethod
    def add_book(book: BookSchemas):
        session = Session()
        try:
            new_book = Book(
                title=book.title,
                description=book.description,
                classmets=book.classmets,
                review=book.review,
                author=book.author,
                creators=book.creators,
                file_name=book.file_name
            )
            session.add(new_book)
            session.commit()
            return new_book
        finally:
            session.close()

    @staticmethod
    def get_book_by_creators(creators: str):
        session = Session()
        try:
            book = session.query(Book).filter(Book.creators == creators).first()
            return book
        finally:
            session.close()

    @staticmethod
    def get_all_authors():
        session = Session()
        try:
            authors = session.query(Book.author).distinct().all()
            return [author[0] for author in authors]
        finally:
            session.close()

    @staticmethod
    def get_all_creators():
        session = Session()
        try:
            creators = session.query(Book.creators).distinct().all()
            return [creator[0] for creator in creators]
        finally:
            session.close()

    @staticmethod
    def get_books_by_author(author: str):
        session = Session()
        try:
            books = session.query(Book).filter(Book.author == author).all()
            return books
        finally:
            session.close()
