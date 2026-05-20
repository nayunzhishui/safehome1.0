"""Configuration placeholders for the SafeHome MVP backend."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Config:
    APP_NAME = "safehome"
    DATABASE_PATH = BASE_DIR / "safehome.sqlite3"
    CONTENT_DIR = PROJECT_ROOT / "content"
    JSON_AS_ASCII = False
