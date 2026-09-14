from fastapi import APIRouter, Depends, HTTPException, Response, Request
from typing import Optional
from utils import JwtTokenOperation
from repository import UserRepository
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["user"])


def get_current_user(request: Request):
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
            return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_admin_user(current_user=Depends(get_current_user)):
    if current_user.name != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def set_auth_cookie(response: Response, user):
    role = "admin" if user.name == "admin" else "user"
    token = JwtTokenOperation.create_jwt_token({
        "user_id": user.id,
        "email": user.email,
        "role": role
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=1800,
        expires=1800,
        samesite="lax"
    )


# Authentication endpoints with rate limiting
@router.post("/register")
@limiter.limit("5/minute")  # Максимум 5 регистраций в минуту с одного IP
async def register(request: Request, name: str, email: str, password: str, description: str = "", response: Response = None):
    with UserRepository() as repo:
        try:
            user = repo.create_user(name=name, email=email, password=password, description=description)
            set_auth_cookie(response, user)
            return {"message": "User created successfully", "user_id": user.id}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
@limiter.limit("10/minute")  # Максимум 10 попыток входа в минуту
async def login(request: Request, email: str, password: str, response: Response):
    with UserRepository() as repo:
        user = repo.get_user_by_email_and_password(email, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if user.banned:
            raise HTTPException(status_code=403, detail="User is banned")

        set_auth_cookie(response, user)
        return {"message": "Login successful", "user_id": user.id}


@router.post("/logout")
@limiter.limit("20/minute")
async def logout(request: Request, response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logout successful"}


# User endpoints with rate limiting
@router.get("/me")
@limiter.limit("30/minute")  # Максимум 30 запросов в минуту
async def get_me(request: Request, current_user=Depends(get_current_user)):
    role = "admin" if current_user.name == "admin" else "user"
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "description": current_user.description,
        "banned": current_user.banned,
        "role": role,
        "created_at": current_user.created_at
    }


@router.put("/me")
@limiter.limit("10/minute")
async def update_me(
        request: Request,
        name: Optional[str] = None,
        description: Optional[str] = None,
        current_user=Depends(get_current_user)
):
    with UserRepository() as repo:
        update_data = {}
        if name:
            update_data['name'] = name
        if description:
            update_data['description'] = description

        if update_data:
            updated_user = repo.update_user(current_user.id, **update_data)
            return {"message": "User updated successfully"}
        return {"message": "Nothing to update"}


@router.put("/me/password")
@limiter.limit("3/minute")  # Строгое ограничение для смены пароля
async def change_password(
        request: Request,
        old_password: str,
        new_password: str,
        current_user=Depends(get_current_user)
):
    with UserRepository() as repo:
        success = repo.update_password(current_user.id, old_password, new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid old password")
        return {"message": "Password updated successfully"}


@router.delete("/me")
@limiter.limit("5/minute")
async def delete_me(
        request: Request,
        response: Response,
        current_user=Depends(get_current_user)
):
    with UserRepository() as repo:
        success = repo.delete_user(current_user.id)
        if success:
            response.delete_cookie(key="access_token")
            return {"message": "User deleted successfully"}
        raise HTTPException(status_code=400, detail="Failed to delete user")


# Admin endpoints with stricter rate limiting
@router.get("/users")
@limiter.limit("20/minute")  # Админ-эндпоинты имеют более строгие ограничения
async def get_all_users(
        request: Request,
        page: int = 1,
        per_page: int = 10,
        current_user=Depends(get_current_admin_user)
):
    with UserRepository() as repo:
        result = repo.get_users_paginated(page=page, per_page=per_page)
        users = [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "description": user.description,
                "banned": user.banned,
                "role": "admin" if user.name == "admin" else "user"
            }
            for user in result['users']
        ]
        return {
            "users": users,
            "total": result['total'],
            "pages": result['pages'],
            "current_page": result['current_page']
        }


@router.get("/users/search")
@limiter.limit("15/minute")
async def search_users(
        request: Request,
        search_term: str,
        current_user=Depends(get_current_user)
):
    with UserRepository() as repo:
        users = repo.search_users(search_term)
        return [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "description": user.description,
                "banned": user.banned,
                "role": "admin" if user.name == "admin" else "user"
            }
            for user in users
        ]


@router.get("/users/banned")
@limiter.limit("10/minute")
async def get_banned_users(request: Request, current_user=Depends(get_current_admin_user)):
    with UserRepository() as repo:
        users = repo.get_banned_users()
        return [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
            for user in users
        ]


@router.get("/users/{user_id}")
@limiter.limit("20/minute")
async def get_user(request: Request, user_id: int, current_user=Depends(get_current_user)):
    if current_user.name != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    with UserRepository() as repo:
        user = repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "description": user.description,
            "banned": user.banned,
            "role": "admin" if user.name == "admin" else "user"
        }


@router.put("/users/{user_id}")
@limiter.limit("10/minute")
async def update_user(
        request: Request,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        banned: Optional[bool] = None,
        current_user=Depends(get_current_user)
):
    if current_user.name != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if current_user.name != "admin" and banned is not None:
        raise HTTPException(status_code=403, detail="Only admin can ban/unban users")

    with UserRepository() as repo:
        update_data = {}
        if name:
            update_data['name'] = name
        if description:
            update_data['description'] = description
        if banned is not None and current_user.name == "admin":
            update_data['banned'] = banned

        if update_data:
            try:
                updated_user = repo.update_user(user_id, **update_data)
                return {"message": "User updated successfully"}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
        return {"message": "Nothing to update"}


@router.delete("/users/{user_id}")
@limiter.limit("5/minute")
async def delete_user(
        request: Request,
        user_id: int,
        response: Response,
        current_user=Depends(get_current_user)
):
    if current_user.name != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    with UserRepository() as repo:
        success = repo.delete_user(user_id)
        if success:
            if current_user.id == user_id:
                response.delete_cookie(key="access_token")
            return {"message": "User deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/users/{user_id}/ban")
@limiter.limit("10/minute")
async def ban_user(request: Request, user_id: int, current_user=Depends(get_current_admin_user)):
    with UserRepository() as repo:
        try:
            user = repo.ban_user(user_id)
            return {"message": "User banned successfully"}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/{user_id}/unban")
@limiter.limit("10/minute")
async def unban_user(request: Request, user_id: int, current_user=Depends(get_current_admin_user)):
    with UserRepository() as repo:
        try:
            user = repo.unban_user(user_id)
            return {"message": "User unbanned successfully"}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))