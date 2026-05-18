from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """应用全局配置"""
    APP_NAME: str = "MetaAnalysis元析智能"
    DEBUG: bool = True

    # 数据库 - 默认使用SQLite便于开发，生产环境切换MySQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./metaanalysis.db"

    # JWT
    SECRET_KEY: str = "metaanalysis-dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # AI大模型
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o"

    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 52_428_800  # 50MB

    # 跨域
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
