from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from mako.lookup import TemplateLookup
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from ai import consultant
from utils import JwtTokenOperation
from repository import UserRepository

router = APIRouter(tags=["ai"])

TEMPLATES_DIR = Path("templates")
mako_lookup = TemplateLookup(
    directories=[str(TEMPLATES_DIR)],
    input_encoding='utf-8',
    output_encoding='utf-8',
    filesystem_checks=True
)

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str

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

@router.get("/chat_page", response_class=HTMLResponse)
async def chat_page(request: Request):
    user = get_current_user(request)
    
    template = mako_lookup.get_template("ai_chat.html")
    
    stats = consultant.get_statistics() if hasattr(consultant, 'get_statistics') else {}
    
    context = {
        'request': request,
        'user': user,
        'page_title': 'AI Консультант',
        'welcome_message': 'Здравствуйте! Я виртуальный консультант. Чем могу помочь?',
        'conversation_history': [],
        'stats': stats
    }
    
    html_content = template.render(**context)
    return HTMLResponse(content=html_content)

@router.post("/api/chat", response_model=ChatResponse)
async def chat_api(request: ChatRequest):
    try:
        user_message = request.message
        response = consultant.generate_response(user_message)
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return ChatResponse(
            response=f"Произошла ошибка: {str(e)}",
            timestamp=datetime.now().isoformat()
        )

@router.get("/api/stats")
async def get_stats():
    try:
        stats = consultant.get_statistics()
        return JSONResponse(content=stats)
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        })

@router.post("/api/reload-data")
async def reload_data():
    try:
        consultant.load_data()
        consultant.setup_vectorizer()
        return JSONResponse(content={
            "status": "success",
            "message": "Данные перезагружены"
        })
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        })

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            response = consultant.generate_response(data)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass