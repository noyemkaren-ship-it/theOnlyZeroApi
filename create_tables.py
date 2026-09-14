from db.base import Base, engine
from models import User, Book , Article, Research, Poema, Message, Teacher

def init_database():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_database()