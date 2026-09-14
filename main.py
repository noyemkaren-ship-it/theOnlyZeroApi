from fastapi import FastAPI, HTTPException, Request
import uvicorn
from routers.user import router as user_router
from db import init_db
from contextlib import asynccontextmanager
from routers.page import router as page_router
from routers.files_operation import router as files_router
from routers.book import router as book_router
from routers.article import router as article_router
from routers.ai import router as ai_router
from routers.resaurch import router as research_router
from routers.poema import router as poema_router
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from routers.message import router as message_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="InovationSaitAPI", lifespan=lifespan)

app.include_router(user_router)
app.include_router(page_router)
app.include_router(files_router)
app.include_router(article_router)
app.include_router(book_router)
app.include_router(ai_router)
app.include_router(research_router)
app.include_router(poema_router)
app.include_router(message_router)


def read_404_page() -> str:
    with open("templates/f404.html", "r", encoding="utf-8") as f:
        return f.read()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Not Found",
                    "detail": exc.detail,
                    "path": request.url.path,
                },
            )
        html = read_404_page()
        return HTMLResponse(status_code=404, content=html)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)