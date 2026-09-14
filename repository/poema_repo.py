from db import Session
from models import Poema

class PoemaRepository:
    @staticmethod
    def get_all_poemas() -> list[Poema]:
        session = Session()
        try:
            return session.query(Poema).all()
        finally:
            session.close()

    @staticmethod
    def get_poemas_by_author(author: str) -> list[Poema]:
        session = Session()
        try:
            return session.query(Poema).filter_by(author=author).all()
        finally:
            session.close()

    @staticmethod
    def get_poema_by_title(title: str) -> Poema:
        session = Session()
        try:
            return session.query(Poema).filter_by(title=title).first()
        finally:
            session.close()

    @staticmethod
    def create_poema(title: str, content: str, author: str) -> Poema:
        session = Session()
        try:
            new_poema = Poema(title=title, content=content, author=author)
            session.add(new_poema)
            session.commit()
            session.refresh(new_poema)
            return new_poema
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update_poema(poema_id: int, title: str = None, content: str = None, author: str = None) -> Poema:
        session = Session()
        try:
            poema = session.query(Poema).get(poema_id)
            if not poema:
                return None
            if title:
                poema.title = title
            if content:
                poema.content = content
            if author:
                poema.author = author
            session.commit()
            session.refresh(poema)
            return poema
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def delete_by_id(poema_id: int) -> bool:
        session = Session()
        try:
            poema = session.query(Poema).get(poema_id)
            if not poema:
                return False
            session.delete(poema)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()