from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List
from pathlib import Path
import shutil
import uuid
from datetime import datetime
from utils import JwtTokenOperation
from repository import UserRepository

router = APIRouter(tags=["files"])
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

# Загрузка файла
@router.post("/files/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    description: str = Form("")
):
    user = get_current_user_required(request)
    
    # Генерируем уникальное имя файла
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Сохраняем файл
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        file.file.close()
    
    return {
        "message": "File uploaded successfully",
        "filename": unique_filename,
        "original_name": file.filename,
        "size": file_path.stat().st_size,
        "content_type": file.content_type,
        "description": description,
        "uploaded_by": user.id,
        "uploaded_at": datetime.now().isoformat()
    }

# Получение списка файлов
@router.get("/files")
async def list_files(request: Request):
    user = get_current_user_required(request)
    
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    
    return {"files": files}

# Получение файла по имени
@router.get("/files/{filename}")
async def get_file(request: Request, filename: str):
    user = get_current_user_required(request)
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    return FileResponse(file_path, filename=filename)

# Удаление файла
@router.delete("/files/{filename}")
async def delete_file(request: Request, filename: str):
    user = get_current_user_required(request)
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return {"message": "File deleted successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

# Получение информации о файле
@router.get("/files/{filename}/info")
async def get_file_info(request: Request, filename: str):
    user = get_current_user_required(request)
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "filename": file_path.name,
        "size": file_path.stat().st_size,
        "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
    }

# Переименование файла
@router.put("/files/{filename}/rename")
async def rename_file(
    request: Request,
    filename: str,
    new_name: str = Form(...)
):
    user = get_current_user_required(request)
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Проверяем, чтобы новое имя не содержало опасных символов
    if "/" in new_name or "\\" in new_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    new_file_path = UPLOAD_DIR / new_name
    
    if new_file_path.exists():
        raise HTTPException(status_code=400, detail="File with this name already exists")
    
    try:
        file_path.rename(new_file_path)
        return {"message": "File renamed successfully", "old_name": filename, "new_name": new_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename file: {str(e)}")

# Множественная загрузка файлов
@router.post("/files/upload-multiple")
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...)
):
    user = get_current_user_required(request)
    
    uploaded_files = []
    
    for file in files:
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append({
                "filename": unique_filename,
                "original_name": file.filename,
                "size": file_path.stat().st_size,
                "content_type": file.content_type
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file {file.filename}: {str(e)}")
        finally:
            file.file.close()
    
    return {
        "message": "Files uploaded successfully",
        "uploaded_files": uploaded_files,
        "uploaded_by": user.id
    }

# Скачивание файла с оригинальным именем
@router.get("/files/{filename}/download")
async def download_file(request: Request, filename: str):
    user = get_current_user_required(request)
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream"
    )