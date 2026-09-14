import jwt
from create_secret_key import create_secret_key

ALGORITHM = "HS256"

class JwtTokenOperation:

    @staticmethod
    def get_secret_key() -> str:
        try:
            with open("key.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            with open("key.txt", "w") as f:
                create_secret_key()
                return f.read().strip()

    @staticmethod
    def create_jwt_token(payload: dict) -> str:
        token = jwt.encode(payload, JwtTokenOperation.get_secret_key(), algorithm=ALGORITHM)
        return token

    @staticmethod
    def get_data_by_token(token: str) -> dict:
        decoded_data = jwt.decode(token, JwtTokenOperation.get_secret_key(), algorithms=[ALGORITHM])
        return decoded_data