# admin/app.py

import os
from datetime import datetime, timedelta
from typing import List

from fastapi import (
    FastAPI,
    Request,
    Depends,
    Form,
    HTTPException,
    status,
    Response,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Импорт модели User из core/database.py
from core.database import User

# Переменные окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/users_db"
)
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme")

# Настраиваем асинхронный движок и сессии SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

app = FastAPI()
# Шаблоны из папки admin/templates
templates = Jinja2Templates(directory="admin/templates")
# Статика из admin/static
app.mount("/static", StaticFiles(directory="admin/static"), name="static")


# Зависимость — асинхронная сессия
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# Зависимость — проверка cookie «admin_token»
async def check_admin(request: Request):
    token = request.cookies.get("admin_token")
    if token != ADMIN_SECRET:
        # Если нет или неверный токен — редиректим на /login
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"},
        )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Страница входа для администратора.
    """
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def process_login(
    request: Request,
    response: Response,
    password: str = Form(...),
):
    """
    Обработка формы логина:
    если пароль совпадает — ставим cookie и редиректим на /users,
    иначе — рендерим форму с ошибкой.
    """
    if password != ADMIN_SECRET:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный пароль"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    redirect = RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)
    # Устанавливаем httponly-cookie «admin_token»
    redirect.set_cookie(key="admin_token", value=ADMIN_SECRET, httponly=True, secure=False)
    return redirect


@app.get("/logout")
async def logout(response: Response):
    """
    Очистка cookie и редирект на страницу логина.
    """
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    redirect.delete_cookie(key="admin_token")
    return redirect


@app.get("/", dependencies=[Depends(check_admin)])
async def index():
    """
    Простое перенаправление с корня / → /users (защищено check_admin).
    """
    return RedirectResponse(url="/users")


@app.get("/users", response_class=HTMLResponse, dependencies=[Depends(check_admin)])
async def list_users(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Отображает таблицу всех пользователей.
    """
    result = await session.execute(select(User).order_by(User.id))
    users: List[User] = result.scalars().all()

    user_list = []
    for u in users:
        user_list.append({
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username or "—",
            "trial_used": "Да" if u.trial_used else "Нет",
            "trial_expiration_time": (
                u.trial_expiration_time.strftime("%Y-%m-%d %H:%M:%S")
                if u.trial_expiration_time else "—"
            ),
            "config_id": u.config_id or "—",
            "expiration_time": (
                u.expiration_time.strftime("%Y-%m-%d %H:%M:%S")
                if u.expiration_time else "—"
            ),
            "config_status": u.config_status or "—",
            "notified": "Да" if u.notified else "Нет",
        })

    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": user_list}
    )


@app.post("/users/{telegram_id}/disable", dependencies=[Depends(check_admin)])
async def disable_user(telegram_id: str, session: AsyncSession = Depends(get_session)):
    """
    Отключение платного конфига пользователя:
    config_status='disabled', сброс config_id и expiration_time.
    """
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(config_status="disabled", expiration_time=None, config_id=None)
    )
    await session.commit()
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)


@app.post("/users/{telegram_id}/enable", dependencies=[Depends(check_admin)])
async def enable_user(
    telegram_id: str,
    days: int = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Включение платного конфига на указанное количество days дней:
    config_status='active', expiration_time=now+days.
    """
    new_exp = datetime.utcnow() + timedelta(days=days)
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(config_status="active", expiration_time=new_exp)
    )
    await session.commit()
    return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)
