from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import uuid
from datetime import datetime
from utils import JwtTokenOperation
from repository import UserRepository, ResearchRepository
from schemas.resaerch import ResearchCreate

router = APIRouter(tags=["research"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

@router.get("/research")
async def get_all_research():
    return ResearchRepository.get_all()

@router.get("/research/{title}")
async def get_research_by_title(title: str):
    research = ResearchRepository.get_by_title(title)
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    return research

@router.get("/research/creator/{creator}")
async def get_research_by_creator(creator: str):
    return ResearchRepository.get_by_creator(creator)

@router.post("/research/upload")
async def upload_research(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    user = get_current_user_required(request)
    
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        file.file.close()
    
    research_data = ResearchCreate(
        title=title,
        description=description,
        document_path=unique_filename,
        creator=user.name
    )
    
    research = ResearchRepository.create(research_data)
    
    return {
        "message": "Research uploaded successfully",
        "research_id": research.id,
        "filename": unique_filename,
        "original_name": file.filename,
        "size": file_path.stat().st_size,
        "uploaded_by": user.name,
        "uploaded_at": datetime.now().isoformat()
    }

@router.get("/research/{title}/download")
async def download_research(request: Request, title: str):
    user = get_current_user_required(request)
    
    research = ResearchRepository.get_by_title(title)
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    file_path = UPLOAD_DIR / research.document_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=research.document_path)

@router.delete("/research/{title}")
async def delete_research(title: str, request: Request):
    user = get_current_user_required(request)
    
    research = ResearchRepository.get_by_title(title)
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    if user.name != "admin" and research.creator != user.name:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    file_path = UPLOAD_DIR / research.document_path
    if file_path.exists():
        file_path.unlink()
    
    success = ResearchRepository.delete_by_title(title)
    if success:
        return {"message": "Research deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete research")