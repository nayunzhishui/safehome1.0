"""Configuration for the SafeHome MVP backend."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_CONTENT_DIR = BASE_DIR / "content" if (BASE_DIR / "content").exists() else PROJECT_ROOT / "content"
DEFAULT_ADMIN_EXPORT_TOKEN = "safehome-local-admin-token"


class Config:
    APP_NAME = "safehome"
    APP_ENV = os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "development"))
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "safehome.sqlite3"))
    CONTENT_DIR = Path(os.environ.get("CONTENT_DIR", DEFAULT_CONTENT_DIR))
    ADMIN_EXPORT_TOKEN = os.environ.get("ADMIN_EXPORT_TOKEN", DEFAULT_ADMIN_EXPORT_TOKEN)
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
        if origin.strip()
    ]
    JSON_AS_ASCII = False
    DEFAULT_PAGE_SIZE = 50

    @classmethod
    def validate(cls) -> None:
        if str(cls.APP_ENV).lower() == "production":
            if not cls.ADMIN_EXPORT_TOKEN:
                raise RuntimeError("生产环境必须配置 ADMIN_EXPORT_TOKEN")
            if cls.ADMIN_EXPORT_TOKEN == DEFAULT_ADMIN_EXPORT_TOKEN:
                raise RuntimeError("生产环境禁止使用默认 ADMIN_EXPORT_TOKEN")
