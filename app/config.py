from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Todo API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database (None = SQLite fallback)
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    
    # Direct DATABASE_URL override
    DATABASE_URL: Optional[str] = None

    def get_database_url(self) -> str:
        """Возвращает URL БД (SQLite для локалки, PostgreSQL для продакшена)"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Если DB_HOST установлен — используем PostgreSQL
        if self.DB_HOST and self.DB_USER:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
        # SQLite fallback для локальной разработки (без БД)
        return "sqlite+aiosqlite:///./todo.db"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        url = self.get_database_url()
        # Для SQLite не нужен asyncpg
        if url.startswith("sqlite"):
            return url.replace("sqlite+aiosqlite", "sqlite")
        return url.replace("postgresql+asyncpg", "postgresql")

    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
