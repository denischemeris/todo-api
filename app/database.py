from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


# Для SQLite серверный режим не нужен
is_sqlite = settings.get_database_url().startswith("sqlite")

engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.DEBUG,
    # SQLite-specific settings
    pool_pre_ping=is_sqlite
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """Dependency для получения сессии БД"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables():
    """Создание таблиц (для разработки)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
