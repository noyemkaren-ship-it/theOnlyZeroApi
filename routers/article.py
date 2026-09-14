from fastapi import APIRouter, Request, HTTPException, Form
from repository import ArticleRepository, UserRepository
from schemas.article import ArticleShemas
from utils import JwtTokenOperation

router = APIRouter(tags=["article"])

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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in auth: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/all_articles")
async def get_all_articles():
    articles = ArticleRepository.get_all()
    return articles


@router.get("/articles/{creator_name}")
async def get_articles_by_creator_name(creator_name: str):
    articles = ArticleRepository.get_by_creator_name(creator_name=creator_name)
    if not articles:
        raise HTTPException(status_code=404, detail="Articles not found")
    return articles


@router.get("/article/{title}")
async def get_article_by_title(title: str):
    article = ArticleRepository.get_by_title(title=title)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/create_article")
async def create_article(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    classmates: str = Form(""),
):
    user = get_current_user(request)
    
    article_data = ArticleShemas(
        title=title,
        text=text,
        classmates=classmates,
        creator_name=user.name
    )
    
    try:
        new_article = ArticleRepository.create(article_data)
        return {"message": "Article created successfully", "article_id": new_article.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete_article/{title}")
async def delete_article(title: str, request: Request):
    user = get_current_user(request)
    
    article = ArticleRepository.get_by_title(title=title)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Проверяем права на удаление
    if user.name != "admin" and article.creator_name != user.name:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        result = ArticleRepository.delete_by_title(title=title)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update_article/{title}")
async def update_article(
    title: str,
    request: Request,
    new_title: str = Form(None),
    text: str = Form(None),
    classmates: str = Form(None)
):
    user = get_current_user(request)
    
    article = ArticleRepository.get_by_title(title=title)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Проверяем права на редактирование
    if user.name != "admin" and article.creator_name != user.name:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = ArticleRepository.update_by_title(
        title=title,
        new_title=new_title,
        text=text,
        classmates=classmates
    )
    return result