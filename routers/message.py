from fastapi import APIRouter, HTTPException, Request, Form
from utils import JwtTokenOperation
from repository import UserRepository, MessageRepository

router = APIRouter(tags=["messages"])

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        payload = JwtTokenOperation.get_data_by_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        with UserRepository() as repo:
            user = repo.get_user_by_id(user_id)
            return user
    except:
        return None

def get_current_user_required(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@router.get("/messages/inbox")
async def get_inbox(request: Request):
    user = get_current_user_required(request)
    return MessageRepository.get_inbox(user.name)

@router.get("/messages/outbox")
async def get_outbox(request: Request):
    user = get_current_user_required(request)
    return MessageRepository.get_outbox(user.name)

@router.get("/messages/conversation/{other_user}")
async def get_conversation(other_user: str, request: Request):
    user = get_current_user_required(request)
    
    with UserRepository() as repo:
        other = repo.get_user_by_name(other_user)
        if not other:
            raise HTTPException(status_code=404, detail="User not found")
    
    return MessageRepository.get_conversation(user.name, other_user)

@router.get("/messages/{message_id}")
async def get_message(message_id: int, request: Request):
    user = get_current_user_required(request)
    
    message = MessageRepository.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_name != user.name and message.getter_name != user.name and user.name != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return message

@router.post("/messages")
async def create_message(
    request: Request,
    content: str = Form(...),
    getter_name: str = Form(...)
):
    user = get_current_user_required(request)
    
    with UserRepository() as repo:
        receiver = repo.get_user_by_name(getter_name)
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")
    
    message = MessageRepository.create_message(
        content=content,
        sender_name=user.name,
        getter_name=getter_name
    )
    return message

@router.put("/messages/{message_id}")
async def update_message(
    message_id: int,
    request: Request,
    content: str = Form(...)
):
    user = get_current_user_required(request)
    
    message = MessageRepository.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_name != user.name and user.name != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    updated = MessageRepository.update_message(message_id, content)
    return updated

@router.delete("/messages/{message_id}")
async def delete_message(message_id: int, request: Request):
    user = get_current_user_required(request)
    
    message = MessageRepository.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_name != user.name and message.getter_name != user.name and user.name != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = MessageRepository.delete_message(message_id)
    if success:
        return {"message": "Message deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete message")