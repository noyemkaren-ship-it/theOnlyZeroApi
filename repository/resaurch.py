from db import Session
from models import Research
from schemas.resaerch import ResearchCreate

class ResearchRepository:
    @staticmethod
    def get_all():
        session = Session()
        try:
            return session.query(Research).all()
        finally:
            session.close()

    @staticmethod
    def create(research: ResearchCreate):
        session = Session()
        try:
            db_research = Research(
                title=research.title,
                description=research.description,
                document_path=research.document_path,
                creator=research.creator
            )
            session.add(db_research)
            session.commit()
            session.refresh(db_research)
            return db_research
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def delete_by_title(title: str):
        session = Session()
        try:
            research = session.query(Research).filter(Research.title == title).first()
            if research:
                session.delete(research)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_by_title(title: str):
        session = Session()
        try:
            return session.query(Research).filter(Research.title == title).first()
        finally:
            session.close()

    @staticmethod
    def get_by_creator(creator: str):
        session = Session()
        try:
            return session.query(Research).filter(Research.creator == creator).all()
        finally:
            session.close()