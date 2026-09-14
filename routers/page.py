from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from mako.lookup import TemplateLookup
from pathlib import Path
from utils import JwtTokenOperation
from repository import UserRepository
from repository import StaticBookRepository
from repository import ArticleRepository
from repository import ResearchRepository
from models import Book
from db import Session
from schemas.book import BookSchemas
from schemas.article import ArticleShemas
from schemas.resaerch import ResearchCreate
import shutil
import uuid
from datetime import datetime
from repository import PoemaRepository
from repository import MessageRepository

router = APIRouter(tags=["pages"])

TEMPLATES_DIR = Path("templates")
mako_lookup = TemplateLookup(
    directories=[str(TEMPLATES_DIR)],
    input_encoding='utf-8',
    output_encoding='utf-8'
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def render_template(template_name: str, **kwargs) -> str:
    template = mako_lookup.get_template(template_name)
    return template.render(**kwargs)

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

def get_current_admin_user(request: Request):
    user = get_current_user_required(request)
    if user.name != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return user

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    user = get_current_user(request)
    
    books = StaticBookRepository.get_all_books()
    total_books = len(books)
    
    with UserRepository() as repo:
        total_users = repo.count_users()
    
    total_files = len(list(UPLOAD_DIR.glob('*')))
    
    subjects = set()
    for book in books:
        if book.classmets:
            subjects.add(book.classmets)
    total_subjects = len(subjects)
    
    recent_books = books[-20:] if len(books) > 20 else books
    recent_books.reverse()
    
    my_books = []
    if user:
        my_books = StaticBookRepository.get_books_by_author(user.name)
    
    articles = ArticleRepository.get_all()
    recent_articles = articles[-10:] if len(articles) > 10 else articles
    recent_articles.reverse()
    
    research_list = ResearchRepository.get_all()
    recent_research = research_list[-10:] if len(research_list) > 10 else research_list
    recent_research.reverse()
    
    template = render_template(
        "home.html",
        user=user,
        request=request,
        total_books=total_books,
        total_users=total_users,
        total_files=total_files,
        total_subjects=total_subjects,
        recent_books=recent_books,
        my_books=my_books,
        recent_articles=recent_articles,
        recent_research=recent_research
    )
    return HTMLResponse(template)

@router.get("/register_page", response_class=HTMLResponse)
async def register_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/me_page", status_code=303)
    
    template = render_template(
        "register.html",
        request=request,
        error=None
    )
    return HTMLResponse(template)

@router.post("/register_page", response_class=HTMLResponse)
async def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    description: str = Form("")
):
    try:
        with UserRepository() as repo:
            user = repo.create_user(
                name=name,
                email=email,
                password=password,
                description=description
            )
            
            token = JwtTokenOperation.create_jwt_token({
                "user_id": user.id,
                "email": user.email,
                "role": "admin" if user.name == "admin" else "user"
            })
            
            response = RedirectResponse(url="/me_page", status_code=303)
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                max_age=1800,
                expires=1800,
                samesite="lax"
            )
            return response
            
    except ValueError as e:
        template = render_template(
            "register.html",
            request=request,
            error=str(e)
        )
        return HTMLResponse(template)

@router.get("/login_page", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/me_page", status_code=303)
    
    template = render_template(
        "login.html",
        request=request,
        error=None
    )
    return HTMLResponse(template)

@router.post("/login_page", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    with UserRepository() as repo:
        user = repo.get_user_by_email_and_password(email, password)
        if not user:
            template = render_template(
                "login.html",
                request=request,
                error="Неверный email или пароль"
            )
            return HTMLResponse(template)
        
        if user.banned:
            template = render_template(
                "login.html",
                request=request,
                error="Пользователь заблокирован"
            )
            return HTMLResponse(template)
        
        token = JwtTokenOperation.create_jwt_token({
            "user_id": user.id,
            "email": user.email,
            "role": "admin" if user.name == "admin" else "user"
        })
        
        response = RedirectResponse(url="/me_page", status_code=303)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=1800,
            expires=1800,
            samesite="lax"
        )
        return response

@router.get("/me_page", response_class=HTMLResponse)
async def me_page(request: Request):
    user = get_current_user_required(request)
    
    my_books = StaticBookRepository.get_books_by_author(user.name)
    my_articles = ArticleRepository.get_by_creator_name(user.name)
    my_research = ResearchRepository.get_by_creator(user.name)
    
    template = render_template(
        "me.html",
        request=request,
        user=user,
        role="admin" if user.name == "admin" else "user",
        my_books=my_books,
        my_articles=my_articles,
        my_research=my_research
    )
    return HTMLResponse(template)

@router.post("/me_page/update", response_class=HTMLResponse)
async def update_me_post(
    request: Request,
    name: str = Form(None),
    description: str = Form(None)
):
    user = get_current_user_required(request)
    
    with UserRepository() as repo:
        update_data = {}
        if name:
            update_data['name'] = name
        if description:
            update_data['description'] = description
        
        if update_data:
            repo.update_user(user.id, **update_data)
    
    return RedirectResponse(url="/me_page", status_code=303)

@router.post("/me_page/password", response_class=HTMLResponse)
async def change_password_post(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    user = get_current_user_required(request)
    
    with UserRepository() as repo:
        success = repo.update_password(user.id, old_password, new_password)
        
        if not success:
            template = render_template(
                "me.html",
                request=request,
                user=user,
                role="admin" if user.name == "admin" else "user",
                error="Неверный старый пароль",
                my_books=StaticBookRepository.get_books_by_author(user.name),
                my_articles=ArticleRepository.get_by_creator_name(user.name),
                my_research=ResearchRepository.get_by_creator(user.name)
            )
            return HTMLResponse(template)
    
    return RedirectResponse(url="/me_page?password_changed=true", status_code=303)

@router.get("/delete_me", response_class=HTMLResponse)
async def delete_me_page(request: Request):
    user = get_current_user_required(request)
    
    template = render_template(
        "delete_me.html",
        request=request,
        user=user
    )
    return HTMLResponse(template)

@router.post("/delete_me", response_class=HTMLResponse)
async def delete_me_post(request: Request):
    user = get_current_user_required(request)
    
    with UserRepository() as repo:
        success = repo.delete_user(user.id)
        
        if success:
            response = RedirectResponse(url="/", status_code=303)
            response.delete_cookie(key="access_token")
            return response
    
    return RedirectResponse(url="/me_page?error=delete_failed", status_code=303)

@router.get("/logout_page")
async def logout_page():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@router.get("/users_page", response_class=HTMLResponse)
async def users_page(request: Request):
    user = get_current_admin_user(request)
    
    with UserRepository() as repo:
        users = repo.get_all_users()
    
    template = render_template(
        "users.html",
        request=request,
        users=users,
        current_user=user
    )
    return HTMLResponse(template)

@router.get("/books_page", response_class=HTMLResponse)
async def books_page(request: Request):
    user = get_current_user(request)
    books = StaticBookRepository.get_all_books()
    
    subjects = set()
    for book in books:
        if book.classmets:
            subjects.add(book.classmets)
    
    template = render_template(
        "books.html",
        request=request,
        user=user,
        books=books,
        subjects=sorted(subjects)
    )
    return HTMLResponse(template)

@router.get("/add_book_page", response_class=HTMLResponse)
async def add_book_page(request: Request):
    user = get_current_user_required(request)
    
    template = render_template(
        "add_book.html",
        request=request,
        user=user,
        error=None
    )
    return HTMLResponse(template)

@router.post("/add_book_page", response_class=HTMLResponse)
async def add_book_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    classmets: str = Form(""),
    review: int = Form(0),
    creators: str = Form(...),
    file: UploadFile = File(...)
):
    user = get_current_user_required(request)
    
    try:
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()
        
        book_data = BookSchemas(
            title=title,
            description=description,
            classmets=classmets,
            review=review,
            author=user.name,
            creators=creators,
            file_name=unique_filename
        )
        
        StaticBookRepository.add_book(book_data)
        
        return RedirectResponse(url="/books_page", status_code=303)
    except Exception as e:
        template = render_template(
            "add_book.html",
            request=request,
            user=user,
            error=str(e)
        )
        return HTMLResponse(template)

@router.get("/book/{book_id}", response_class=HTMLResponse)
async def book_detail_page(request: Request, book_id: int):
    user = get_current_user(request)
    
    session = Session()
    try:
        book = session.query(Book).filter(Book.id == book_id).first()
    finally:
        session.close()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    template = render_template(
        "book_detail.html",
        request=request,
        user=user,
        book=book
    )
    return HTMLResponse(template)

@router.get("/my_books_page", response_class=HTMLResponse)
async def my_books_page(request: Request):
    user = get_current_user_required(request)
    
    books = StaticBookRepository.get_books_by_author(user.name)
    
    template = render_template(
        "my_books.html",
        request=request,
        user=user,
        books=books
    )
    return HTMLResponse(template)

@router.post("/book/{book_id}/delete")
async def delete_book_post(request: Request, book_id: int):
    user = get_current_user_required(request)
    
    session = Session()
    try:
        book = session.query(Book).filter(Book.id == book_id).first()
        if book and (user.name == "admin" or book.author == user.name):
            file_path = UPLOAD_DIR / book.file_name
            if file_path.exists():
                file_path.unlink()
            
            session.delete(book)
            session.commit()
    finally:
        session.close()
    
    return RedirectResponse(url="/my_books_page", status_code=303)

@router.get("/articles_page", response_class=HTMLResponse)
async def articles_page(request: Request):
    user = get_current_user(request)
    articles = ArticleRepository.get_all()
    
    template = render_template(
        "articles.html",
        request=request,
        user=user,
        articles=articles
    )
    return HTMLResponse(template)

@router.get("/add_article_page", response_class=HTMLResponse)
async def add_article_page(request: Request):
    user = get_current_user_required(request)
    
    template = render_template(
        "add_article.html",
        request=request,
        user=user,
        error=None
    )
    return HTMLResponse(template)

@router.post("/add_article_page", response_class=HTMLResponse)
async def add_article_post(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    classmates: str = Form("")
):
    user = get_current_user_required(request)
    
    try:
        article_data = ArticleShemas(
            title=title,
            text=text,
            classmates=classmates,
            creator_name=user.name
        )
        
        ArticleRepository.create(article_data)
        
        return RedirectResponse(url="/articles_page", status_code=303)
    except Exception as e:
        template = render_template(
            "add_article.html",
            request=request,
            user=user,
            error=str(e)
        )
        return HTMLResponse(template)

@router.get("/article/{title}", response_class=HTMLResponse)
async def article_detail_page(request: Request, title: str):
    user = get_current_user(request)
    
    article = ArticleRepository.get_by_title(title=title)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    template = render_template(
        "article_detail.html",
        request=request,
        user=user,
        article=article
    )
    return HTMLResponse(template)

@router.get("/my_articles_page", response_class=HTMLResponse)
async def my_articles_page(request: Request):
    user = get_current_user_required(request)
    
    articles = ArticleRepository.get_by_creator_name(user.name)
    
    template = render_template(
        "my_articles.html",
        request=request,
        user=user,
        articles=articles
    )
    return HTMLResponse(template)

@router.post("/article/{title}/delete")
async def delete_article_post(request: Request, title: str):
    user = get_current_user_required(request)
    
    article = ArticleRepository.get_by_title(title=title)
    if article and (user.name == "admin" or article.creator_name == user.name):
        ArticleRepository.delete_by_title(title=title)
    
    return RedirectResponse(url="/my_articles_page", status_code=303)

@router.get("/research_page", response_class=HTMLResponse)
async def research_page(request: Request):
    user = get_current_user(request)
    research_list = ResearchRepository.get_all()
    
    template = render_template(
        "research.html",
        request=request,
        user=user,
        research_list=research_list
    )
    return HTMLResponse(template)

@router.get("/asking", response_class=HTMLResponse)
async def askingg(request: Request):
    
    template = render_template(
        "ai_ask.html",
        request=request,
    )
    return HTMLResponse(template)


@router.get("/add_research_page", response_class=HTMLResponse)
async def add_research_page(request: Request):
    user = get_current_user_required(request)
    
    template = render_template(
        "add_research.html",
        request=request,
        user=user,
        error=None
    )
    return HTMLResponse(template)

@router.post("/add_research_page", response_class=HTMLResponse)
async def add_research_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    user = get_current_user_required(request)
    
    try:
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()
        
        research_data = ResearchCreate(
            title=title,
            description=description,
            document_path=unique_filename,
            creator=user.name
        )
        
        ResearchRepository.create(research_data)
        
        return RedirectResponse(url="/research_page", status_code=303)
    except Exception as e:
        template = render_template(
            "add_research.html",
            request=request,
            user=user,
            error=str(e)
        )
        return HTMLResponse(template)

@router.get("/research/{title}", response_class=HTMLResponse)
async def research_detail_page(request: Request, title: str):
    user = get_current_user(request)
    
    research = ResearchRepository.get_by_title(title=title)
    
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    
    template = render_template(
        "research_detail.html",
        request=request,
        user=user,
        research=research
    )
    return HTMLResponse(template)

@router.get("/my_research_page", response_class=HTMLResponse)
async def my_research_page(request: Request):
    user = get_current_user_required(request)
    
    research_list = ResearchRepository.get_by_creator(user.name)
    
    template = render_template(
        "my_research.html",
        request=request,
        user=user,
        research_list=research_list
    )
    return HTMLResponse(template)

@router.post("/research/{title}/delete")
async def delete_research_post(request: Request, title: str):
    user = get_current_user_required(request)
    
    research = ResearchRepository.get_by_title(title=title)
    if research and (user.name == "admin" or research.creator == user.name):
        file_path = UPLOAD_DIR / research.document_path
        if file_path.exists():
            file_path.unlink()
        
        ResearchRepository.delete_by_title(title=title)
    
    return RedirectResponse(url="/my_research_page", status_code=303)

@router.get("/upload_file_page", response_class=HTMLResponse)
async def upload_file_page(request: Request):
    user = get_current_user_required(request)
    
    template = render_template(
        "upload_file.html",
        request=request,
        user=user,
        error=None,
        success=None
    )
    return HTMLResponse(template)

@router.post("/upload_file_page", response_class=HTMLResponse)
async def upload_file_post(
    request: Request,
    file: UploadFile = File(...),
    description: str = Form("")
):
    user = get_current_user_required(request)
    
    try:
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()
        
        template = render_template(
            "upload_file.html",
            request=request,
            user=user,
            error=None,
            success=f"Файл успешно загружен: {unique_filename}"
        )
        return HTMLResponse(template)
    except Exception as e:
        template = render_template(
            "upload_file.html",
            request=request,
            user=user,
            error=str(e),
            success=None
        )
        return HTMLResponse(template)

@router.get("/files_page", response_class=HTMLResponse)
async def files_page(request: Request):
    user = get_current_user_required(request)
    
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            })
    
    template = render_template(
        "files.html",
        request=request,
        user=user,
        files=files
    )
    return HTMLResponse(template)

@router.post("/files_page/{filename}/delete")
async def delete_file_page_post(request: Request, filename: str):
    user = get_current_user_required(request)
    
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        file_path.unlink()
    
    return RedirectResponse(url="/files_page", status_code=303)

@router.get("/user/{user_id}/edit_page", response_class=HTMLResponse)
async def edit_user_page(request: Request, user_id: int):
    current_user = get_current_admin_user(request)
    
    with UserRepository() as repo:
        user_to_edit = repo.get_user_by_id(user_id)
        if not user_to_edit:
            raise HTTPException(status_code=404, detail="User not found")
    
    template = render_template(
        "edit_user.html",
        request=request,
        user=user_to_edit,
        current_user=current_user
    )
    return HTMLResponse(template)

@router.post("/user/{user_id}/edit_page", response_class=HTMLResponse)
async def edit_user_post(
    request: Request,
    user_id: int,
    name: str = Form(None),
    description: str = Form(None),
    banned: str = Form(None)
):
    current_user = get_current_admin_user(request)
    
    with UserRepository() as repo:
        update_data = {}
        if name:
            update_data['name'] = name
        if description:
            update_data['description'] = description
        if banned is not None:
            update_data['banned'] = banned == 'true'
        
        if update_data:
            try:
                repo.update_user(user_id, **update_data)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
    
    return RedirectResponse(url="/users_page", status_code=303)

@router.post("/user/{user_id}/delete")
async def delete_user_post(request: Request, user_id: int):
    current_user = get_current_admin_user(request)
    
    with UserRepository() as repo:
        success = repo.delete_user(user_id)
    
    return RedirectResponse(url="/users_page", status_code=303)

@router.get("/poems_page", response_class=HTMLResponse)
async def poems_page(request: Request):
    user = get_current_user(request)
    poems = PoemaRepository.get_all_poemas()
    
    template = render_template(
        "poems.html",
        request=request,
        user=user,
        poems=poems
    )
    return HTMLResponse(template)

@router.get("/add_poem_page", response_class=HTMLResponse)
async def add_poem_page(request: Request):
    user = get_current_user_required(request)
    
    template = render_template(
        "add_poem.html",
        request=request,
        user=user,
        error=None
    )
    return HTMLResponse(template)

@router.post("/add_poem_page", response_class=HTMLResponse)
async def add_poem_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...)
):
    user = get_current_user_required(request)
    
    try:
        PoemaRepository.create_poema(
            title=title,
            content=content,
            author=user.name
        )
        
        return RedirectResponse(url="/poems_page", status_code=303)
    except Exception as e:
        template = render_template(
            "add_poem.html",
            request=request,
            user=user,
            error=str(e)
        )
        return HTMLResponse(template)

@router.get("/poem/{poem_id}", response_class=HTMLResponse)
async def poem_detail_page(request: Request, poem_id: int):
    user = get_current_user(request)
    
    poems = PoemaRepository.get_all_poemas()
    poem = None
    for p in poems:
        if p.id == poem_id:
            poem = p
            break
    
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")
    
    template = render_template(
        "poem_detail.html",
        request=request,
        user=user,
        poem=poem
    )
    return HTMLResponse(template)

@router.get("/my_poems_page", response_class=HTMLResponse)
async def my_poems_page(request: Request):
    user = get_current_user_required(request)
    
    poems = PoemaRepository.get_poemas_by_author(user.name)
    
    template = render_template(
        "my_poems.html",
        request=request,
        user=user,
        poems=poems
    )
    return HTMLResponse(template)

@router.post("/poem/{poem_id}/delete")
async def delete_poem_post(request: Request, poem_id: int):
    user = get_current_user_required(request)
    
    poems = PoemaRepository.get_all_poemas()
    poem = None
    for p in poems:
        if p.id == poem_id:
            poem = p
            break
    
    if poem and (user.name == "admin" or poem.author == user.name):
        PoemaRepository.delete_by_id(poem_id)
    
    return RedirectResponse(url="/my_poems_page", status_code=303)


@router.get("/messages_page", response_class=HTMLResponse)
async def messages_page(request: Request):
    user = get_current_user_required(request)
    
    inbox = MessageRepository.get_inbox(user.name)
    outbox = MessageRepository.get_outbox(user.name)
    
    template = render_template(
        "messages.html",
        request=request,
        user=user,
        inbox=inbox,
        outbox=outbox
    )
    return HTMLResponse(template)

@router.get("/send_message_page", response_class=HTMLResponse)
async def send_message_page(request: Request, to: str = None):
    user = get_current_user_required(request)
    
    template = render_template(
        "send_message.html",
        request=request,
        user=user,
        to=to,
        error=None,
        success=None
    )
    return HTMLResponse(template)

@router.post("/send_message_page", response_class=HTMLResponse)
async def send_message_post(
    request: Request,
    content: str = Form(...),
    getter_name: str = Form(...)
):
    user = get_current_user_required(request)
    
    with UserRepository() as repo:
        receiver = repo.get_user_by_name(getter_name)
        if not receiver:
            template = render_template(
                "send_message.html",
                request=request,
                user=user,
                to=getter_name,
                error="Пользователь не найден",
                success=None
            )
            return HTMLResponse(template)
    
    try:
        MessageRepository.create_message(
            content=content,
            sender_name=user.name,
            getter_name=getter_name
        )
        
        return RedirectResponse(url="/messages_page", status_code=303)
    except Exception as e:
        template = render_template(
            "send_message.html",
            request=request,
            user=user,
            to=getter_name,
            error=str(e),
            success=None
        )
        return HTMLResponse(template)

@router.get("/conversation_page/{other_user}", response_class=HTMLResponse)
async def conversation_page(request: Request, other_user: str):
    user = get_current_user_required(request)
    
    messages = MessageRepository.get_conversation(user.name, other_user)
    
    # Сортируем по id (по порядку отправки)
    messages = sorted(messages, key=lambda m: m.id)
    
    template = render_template(
        "conversation.html",
        request=request,
        user=user,
        other_user=other_user,
        messages=messages
    )
    return HTMLResponse(template)

@router.post("/conversation_page/{other_user}", response_class=HTMLResponse)
async def conversation_post(
    request: Request,
    other_user: str,
    content: str = Form(...)
):
    user = get_current_user_required(request)
    
    MessageRepository.create_message(
        content=content,
        sender_name=user.name,
        getter_name=other_user
    )
    
    return RedirectResponse(url=f"/conversation_page/{other_user}", status_code=303)

@router.post("/message/{message_id}/delete")
async def delete_message_post(request: Request, message_id: int):
    user = get_current_user_required(request)
    
    message = MessageRepository.get_message_by_id(message_id)
    if message and (message.sender_name == user.name or message.getter_name == user.name or user.name == "admin"):
        MessageRepository.delete_message(message_id)
    
    return RedirectResponse(url="/messages_page", status_code=303)

@router.get("/message_page/{message_id}", response_class=HTMLResponse)
async def message_view_page(request: Request, message_id: int):
    user = get_current_user_required(request)
    
    message = MessageRepository.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_name != user.name and message.getter_name != user.name and user.name != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    template = render_template(
        "message_view.html",
        request=request,
        user=user,
        message=message
    )
    return HTMLResponse(template)