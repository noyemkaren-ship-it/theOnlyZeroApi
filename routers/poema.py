from fastapi import APIRouter, HTTPException, Request, Form
from utils import JwtTokenOperation
from repository import UserRepository, PoemaRepository

router = APIRouter(tags=["poema"])

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

@router.get("/poemas")
async def get_all_poemas():
    return PoemaRepository.get_all_poemas()

@router.get("/poemas/{title}")
async def get_poema_by_title(title: str):
    poema = PoemaRepository.get_poema_by_title(title)
    if not poema:
        raise HTTPException(status_code=404, detail="Poema not found")
    return poema

@router.get("/poemas/author/{author}")
async def get_poemas_by_author(author: str):
    return PoemaRepository.get_poemas_by_author(author)

@router.post("/poemas")
async def create_poema(
    request: Request,
    title: str = Form(...),
    content: str = Form(...)
):
    user = get_current_user_required(request)
    
    poema = PoemaRepository.create_poema(
        title=title,
        content=content,
        author=user.name
    )
    return poema

@router.put("/poemas/{poema_id}")
async def update_poema(
    poema_id: int,
    request: Request,
    title: str = Form(None),
    content: str = Form(None)
):
    user = get_current_user_required(request)
    
    poema = PoemaRepository.get_all_poemas()
    target = None
    for p in poema:
        if p.id == poema_id:
            target = p
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="Poema not found")
    
    if user.name != "admin" and target.author != user.name:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    updated = PoemaRepository.update_poema(
        poema_id=poema_id,
        title=title,
        content=content
    )
    return updated

@router.delete("/poemas/{poema_id}")
async def delete_poema(poema_id: int, request: Request):
    user = get_current_user_required(request)
    
    poema = PoemaRepository.get_all_poemas()
    target = None
    for p in poema:
        if p.id == poema_id:
            target = p
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="Poema not found")
    
    if user.name != "admin" and target.author != user.name:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = PoemaRepository.delete_by_id(poema_id)
    if success:
        return {"message": "Poema deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete poema")