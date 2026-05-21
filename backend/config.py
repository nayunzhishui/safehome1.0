"""Configuration for the SafeHome MVP backend."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Config:
    APP_NAME = "safehome"
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "safehome.sqlite3"))
    CONTENT_DIR = PROJECT_ROOT / "content"
    ADMIN_EXPORT_TOKEN = os.environ.get("ADMIN_EXPORT_TOKEN", "safehome-local-admin-token")
    JSON_AS_ASCII = False
    DEFAULT_PAGE_SIZE = 50
