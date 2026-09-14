from models import Message
from db import Session


class MessageRepository:

    @staticmethod
    def get_messages_by_sender(sender_name: str):
        session = Session()
        try:
            return session.query(Message).filter(Message.sender_name == sender_name).all()
        finally:
            session.close()

    @staticmethod
    def get_messages_by_getter(getter_name: str):
        session = Session()
        try:
            return session.query(Message).filter(Message.getter_name == getter_name).all()
        finally:
            session.close()

    @staticmethod
    def get_message_by_id(message_id: int):
        session = Session()
        try:
            return session.query(Message).filter(Message.id == message_id).first()
        finally:
            session.close()

    @staticmethod
    def get_conversation(user1: str, user2: str):
        session = Session()
        try:
            return session.query(Message).filter(
                ((Message.sender_name == user1) & (Message.getter_name == user2)) |
                ((Message.sender_name == user2) & (Message.getter_name == user1))
            ).all()
        finally:
            session.close()

    @staticmethod
    def get_inbox(user_name: str):
        session = Session()
        try:
            return session.query(Message).filter(Message.getter_name == user_name).all()
        finally:
            session.close()

    @staticmethod
    def get_outbox(user_name: str):
        session = Session()
        try:
            return session.query(Message).filter(Message.sender_name == user_name).all()
        finally:
            session.close()

    @staticmethod
    def create_message(content: str, sender_name: str, getter_name: str):
        session = Session()
        try:
            new_message = Message(content=content, sender_name=sender_name, getter_name=getter_name)
            session.add(new_message)
            session.commit()
            session.refresh(new_message)
            return new_message
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def delete_message(message_id: int):
        session = Session()
        try:
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                session.delete(message)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update_message(message_id: int, new_content: str):
        session = Session()
        try:
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                message.content = new_content
                session.commit()
                session.refresh(message)
            return message
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()