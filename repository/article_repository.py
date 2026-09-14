from db import Session
from models import Article
from schemas.article import ArticleShemas
from fastapi import HTTPException

class ArticleRepository:

    @staticmethod
    def get_all():
        session = Session()
        try:
            return session.query(Article).all()
        finally:
            session.close()

    @staticmethod
    def get_by_creator_name(creator_name):
        session = Session()
        try:
            return session.query(Article).filter_by(creator_name=creator_name).all()
        finally:
            session.close()

    @staticmethod
    def get_by_id(article_id):
        session = Session()
        try:
            return session.query(Article).filter_by(id=article_id).first()
        finally:
            session.close()

    @staticmethod
    def get_by_title(title: str):
        session = Session()
        try:
            return session.query(Article).filter_by(title=title).first()
        finally:
            session.close()

    @staticmethod
    def create(art: ArticleShemas):
        session = Session()
        try:
            new_article = Article(
                title=art.title,
                text=art.text,
                classmates=art.classmates,
                creator_name=art.creator_name
            )
            session.add(new_article)
            session.commit()
            session.refresh(new_article)
            return new_article
        except Exception as e:
            session.rollback()
            print(f"Error: {e}")
            raise HTTPException(500, detail="Произошла ошибка при создании статьи")
        finally:
            session.close()

    @staticmethod
    def delete_by_title(title: str):
        session = Session()
        try:
            article = session.query(Article).filter_by(title=title).first()
            if not article:
                raise HTTPException(404, detail="Статья не найдена")
            
            session.delete(article)
            session.commit()
            return {"message": "Successfully deleted"}
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            print(f"Error: {e}")
            raise HTTPException(500, detail="Ошибка при удалении статьи")
        finally:
            session.close()

    @staticmethod
    def update_by_title(title: str, new_title: str = None, text: str = None, classmates: str = None):
        session = Session()
        try:
            article = session.query(Article).filter_by(title=title).first()
            if not article:
                raise HTTPException(404, detail="Статья не найдена")
            
            if new_title:
                article.title = new_title
            if text:
                article.text = text
            if classmates:
                article.classmates = classmates
            
            session.commit()
            session.refresh(article)
            return article
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            print(f"Error: {e}")
            raise HTTPException(500, detail="Ошибка при обновлении статьи")
        finally:
            session.close()