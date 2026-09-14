import hashlib
from db import Session
from models import User
from sqlalchemy import or_


class UserRepository:
    def __init__(self):
        self.session = Session()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _verify_password(password: str, hashed_password: str) -> bool:
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password

    def get_all_users(self) -> list[User]:
        return self.session.query(User).all()

    def get_active_users(self) -> list[User]:
        return self.session.query(User).filter_by(banned=False).all()

    def get_user_by_id(self, user_id: int) -> User:
        return self.session.query(User).filter_by(id=user_id).first()

    def get_user_by_email(self, email: str) -> User:
        return self.session.query(User).filter_by(email=email).first()

    def get_user_by_name(self, name: str) -> User:
        return self.session.query(User).filter_by(name=name).first()

    def get_user_by_email_and_password(self, email: str, password: str) -> User:
        user = self.get_user_by_email(email)
        if user and self._verify_password(password, user.hesh_password):
            return user
        return None

    def get_banned_users(self) -> list[User]:
        return self.session.query(User).filter_by(banned=True).all()

    def search_users(self, search_term: str) -> list[User]:
        return self.session.query(User).filter(
            or_(
                User.name.ilike(f'%{search_term}%'),
                User.email.ilike(f'%{search_term}%')
            )
        ).all()

    def get_users_paginated(self, page: int = 1, per_page: int = 10) -> dict:
        total = self.session.query(User).count()
        users = self.session.query(User).offset((page - 1) * per_page).limit(per_page).all()
        
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return {
            'users': users,
            'total': total,
            'pages': total_pages,
            'current_page': page,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }

    def create_user(self, name: str, email: str, password: str, description: str = "") -> User:
        if self.get_user_by_email(email):
            raise ValueError(f"Пользователь с email {email} уже существует")
        
        hashed_password = self._hash_password(password)
        
        user = User(
            name=name,
            email=email,
            hesh_password=hashed_password,
            description=description
        )
        
        self.session.add(user)
        self.session.commit()
        return user

    def create_users_bulk(self, users_data: list[dict]) -> list[User]:
        created_users = []
        for user_data in users_data:
            user = self.create_user(**user_data)
            created_users.append(user)
        return created_users

    def update_user(self, user_id: int, **kwargs) -> User:
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")
        
        if 'password' in kwargs:
            kwargs['hesh_password'] = self._hash_password(kwargs.pop('password'))
        
        allowed_fields = ['name', 'email', 'hesh_password', 'description', 'banned']
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(user, key):
                setattr(user, key, value)
        
        self.session.commit()
        return user

    def update_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")
        
        if not self._verify_password(old_password, user.hesh_password):
            return False
        
        user.hesh_password = self._hash_password(new_password)
        self.session.commit()
        return True

    def reset_password(self, email: str, new_password: str) -> bool:
        user = self.get_user_by_email(email)
        if not user:
            return False
        
        user.hesh_password = self._hash_password(new_password)
        self.session.commit()
        return True

    def ban_user(self, user_id: int) -> User:
        return self.update_user(user_id, banned=True)

    def unban_user(self, user_id: int) -> User:
        return self.update_user(user_id, banned=False)

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.session.delete(user)
        self.session.commit()
        return True

    def delete_user_by_email(self, email: str) -> bool:
        user = self.get_user_by_email(email)
        if not user:
            return False
        
        self.session.delete(user)
        self.session.commit()
        return True

    def delete_all_banned_users(self) -> int:
        banned_users = self.get_banned_users()
        count = len(banned_users)
        
        for user in banned_users:
            self.session.delete(user)
        
        self.session.commit()
        return count

    def check_password(self, user: User, password: str) -> bool:
        return self._verify_password(password, user.hesh_password)

    def user_exists(self, email: str) -> bool:
        return self.get_user_by_email(email) is not None

    def count_users(self) -> int:
        return self.session.query(User).count()

    def count_banned_users(self) -> int:
        return self.session.query(User).filter_by(banned=True).count()

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()