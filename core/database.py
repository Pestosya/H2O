# database.py

import os
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    select,
    update,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from config import DATABASE_URL

# 1. Создаём асинхронный движок и сессию
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 2. Базовый класс для моделей
class Base(DeclarativeBase):
    pass


# 3. Модель пользователя
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    trial_config_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    trial_expiration_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)

    config_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expiration_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    config_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    notified: Mapped[bool] = mapped_column(Boolean, default=False)


# 4. Инициализация БД (создаёт таблицы, если их нет)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 5. Отключение от БД
async def shutdown_db():
    await engine.dispose()


# 6. Добавить пользователя (если нет) или просто вернуть существующего
async def add_user(telegram_id: int, username: Optional[str] = None) -> None:
    async with AsyncSessionLocal() as session:
        new = User(telegram_id=str(telegram_id), username=username)
        session.add(new)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        # Не обязательно возвращать объект


# 7. Обновить или установить username
async def add_username(telegram_id: int, username: Optional[str]) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(username=username)
        )
        await session.commit()


# 8. Получить все данные пользователя как dict или None
async def get_user(telegram_id: int) -> Optional[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == str(telegram_id))
        )
        user_obj = result.scalars().first()
        if not user_obj:
            return None

        return {
            "id": user_obj.id,
            "telegram_id": user_obj.telegram_id,
            "username": user_obj.username,
            "trial_config_id": user_obj.trial_config_id,
            "trial_expiration_time": user_obj.trial_expiration_time,
            "trial_used": user_obj.trial_used,
            "config_id": user_obj.config_id,
            "expiration_time": user_obj.expiration_time,
            "config_status": user_obj.config_status,
            "notified": user_obj.notified,
        }


# 9. Получить только config_id
async def get_conf_id(telegram_id: int) -> Optional[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.config_id).where(User.telegram_id == str(telegram_id))
        )
        row = result.scalar_one_or_none()
        return row


# 10. Сохранить config_id (платный или пробный)
async def save_config_id(telegram_id: int, config_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(config_id=config_id)
        )
        await session.commit()


# 11. Сохранить trial_config_id
async def save_trial_config_id(telegram_id: int, config_id: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(trial_config_id=config_id)
        )
        await session.commit()


# 12. Установить время окончания для платного конфига
async def set_expiration_time(telegram_id: int, expiration_time: datetime) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(expiration_time=expiration_time)
        )
        await session.commit()


# 13. Установить время окончания для trial
async def set_trial_expiration_time(telegram_id: int, expiration_time: datetime) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(trial_expiration_time=expiration_time)
        )
        await session.commit()


# 14. Получить expiration_time (платный)
async def get_expiration_time(telegram_id: int) -> Optional[datetime]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.expiration_time).where(User.telegram_id == str(telegram_id))
        )
        row = result.scalar_one_or_none()
        return row


# 15. Проверить, использовал ли пользователь trial
async def has_used_trial(telegram_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.trial_used).where(User.telegram_id == str(telegram_id))
        )
        row = result.scalar_one_or_none()
        return bool(row) if row is not None else False


# 16. Пометить, что trial использован
async def set_trial_used(telegram_id: int, used: bool = True) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(trial_used=used)
        )
        await session.commit()


# 17. Включить платный конфиг (пометить статус=active)
async def enable_config(telegram_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(config_status="active")
        )
        await session.commit()


# 18. Отключить конфиг (config_status = 'disabled')
async def disable_config(telegram_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(config_status="disabled")
        )
        await session.commit()


# 19. Получить всех пользователей (возвращает список dict)
async def get_all_users() -> List[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "trial_used": u.trial_used,
                "trial_expiration_time": u.trial_expiration_time,
                "config_id": u.config_id,
                "expiration_time": u.expiration_time,
                "config_status": u.config_status,
                "notified": u.notified,
            }
            for u in users
        ]


# 20. Пометить, что пользователю отправили уведомление
async def mark_as_notified(telegram_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == str(telegram_id))
            .values(notified=True)
        )
        await session.commit()
