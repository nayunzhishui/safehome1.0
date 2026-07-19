"""Configuration for the SafeHome MVP backend."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_CONTENT_DIR = BASE_DIR / "content" if (BASE_DIR / "content").exists() else PROJECT_ROOT / "content"
DEFAULT_ADMIN_EXPORT_TOKEN = "safehome-local-admin-token"
DEFAULT_SECRET_KEY = "safehome-local-dev-secret"
DB_PROVIDER_ENV_VALUE = os.environ.get("DB_PROVIDER")


class Config:
    APP_NAME = "safehome"
    APP_ENV = os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "development"))
    DB_PROVIDER = (DB_PROVIDER_ENV_VALUE or "sqlite").strip().lower()
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "safehome.sqlite3"))
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "")
    CONTENT_DIR = Path(os.environ.get("CONTENT_DIR", DEFAULT_CONTENT_DIR))
    SECRET_KEY = os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)
    ADMIN_EXPORT_TOKEN = os.environ.get("ADMIN_EXPORT_TOKEN", DEFAULT_ADMIN_EXPORT_TOKEN)
    TRUST_CLOUDBASE_IDENTITY_HEADERS = os.environ.get("TRUST_CLOUDBASE_IDENTITY_HEADERS", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    ALLOW_PRODUCTION_SQLITE = os.environ.get("ALLOW_PRODUCTION_SQLITE", "").strip().lower() in {"1", "true", "yes"}
    CONTENT_GOVERNANCE_ENFORCED = os.environ.get("CONTENT_GOVERNANCE_ENFORCED", "").strip().lower() in {
        "1",
        "true",
        "yes",
    } or str(APP_ENV).lower() == "production"
    CONTENT_GOVERNANCE_PUBLISH_ENABLED = os.environ.get(
        "CONTENT_GOVERNANCE_PUBLISH_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
        if origin.strip()
    ]
    JSON_AS_ASCII = False
    DEFAULT_PAGE_SIZE = 50
    WECHAT_APPID = os.environ.get("WECHAT_APPID", "").strip()
    WECHAT_SECRET = os.environ.get("WECHAT_SECRET", "").strip()
    WECHAT_TRAINING_DUE_TEMPLATE_ID = os.environ.get("WECHAT_TRAINING_DUE_TEMPLATE_ID", "").strip()
    WECHAT_TRAINING_DUE_TEMPLATE_FIELDS = os.environ.get("WECHAT_TRAINING_DUE_TEMPLATE_FIELDS", "").strip()
    WECHAT_TRAINING_DUE_PAGE = os.environ.get(
        "WECHAT_TRAINING_DUE_PAGE", "pages/personalized-plan/index"
    ).strip()
    WECHAT_SUBSCRIBE_MODE = os.environ.get("WECHAT_SUBSCRIBE_MODE", "once").strip().lower()
    WECHAT_SUBSCRIBE_SEND_ENABLED = os.environ.get("WECHAT_SUBSCRIBE_SEND_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    NOTIFICATION_SCHEDULER_TOKEN = os.environ.get("NOTIFICATION_SCHEDULER_TOKEN", "").strip()
    PRIVACY_EXECUTION_ENABLED = os.environ.get("PRIVACY_EXECUTION_ENABLED", "").strip().lower() in {"1", "true", "yes"}
    PRIVACY_RETENTION_POLICY_APPROVED = os.environ.get("PRIVACY_RETENTION_POLICY_APPROVED", "").strip().lower() in {"1", "true", "yes"}
    PRIVACY_PRODUCTION_EXECUTION_ENABLED = os.environ.get("PRIVACY_PRODUCTION_EXECUTION_ENABLED", "").strip().lower() in {"1", "true", "yes"}
    PRIVACY_TOMBSTONE_SECRET = os.environ.get("PRIVACY_TOMBSTONE_SECRET", SECRET_KEY)
    RESEARCH_OPERATIONS_WRITE_ENABLED = os.environ.get(
        "RESEARCH_OPERATIONS_WRITE_ENABLED",
        "1" if str(APP_ENV).lower() != "production" else "0",
    ).strip().lower() in {
        "1",
        "true",
        "yes",
    }

    @classmethod
    def validate(cls) -> None:
        if cls.DB_PROVIDER not in {"sqlite", "mysql"}:
            raise RuntimeError("DB_PROVIDER 只能是 sqlite 或 mysql")
        if cls.DB_PROVIDER == "mysql":
            missing = [
                name
                for name in ["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"]
                if not getattr(cls, name)
            ]
            if missing:
                raise RuntimeError(f"MySQL 模式缺少环境变量：{', '.join(missing)}")
        if cls.WECHAT_SUBSCRIBE_MODE not in {"once", "long_term"}:
            raise RuntimeError("WECHAT_SUBSCRIBE_MODE 只能是 once 或 long_term")
        if cls.WECHAT_SUBSCRIBE_SEND_ENABLED:
            missing = [
                name
                for name in [
                    "WECHAT_APPID",
                    "WECHAT_SECRET",
                    "WECHAT_TRAINING_DUE_TEMPLATE_ID",
                    "WECHAT_TRAINING_DUE_TEMPLATE_FIELDS",
                    "NOTIFICATION_SCHEDULER_TOKEN",
                ]
                if not getattr(cls, name)
            ]
            if missing:
                raise RuntimeError(f"启用微信订阅发送前必须配置：{', '.join(missing)}")
        if str(cls.APP_ENV).lower() == "production":
            if cls.PRIVACY_PRODUCTION_EXECUTION_ENABLED and not cls.PRIVACY_EXECUTION_ENABLED:
                raise RuntimeError("启用生产隐私执行前必须同时开启 PRIVACY_EXECUTION_ENABLED")
            if cls.PRIVACY_PRODUCTION_EXECUTION_ENABLED and not cls.PRIVACY_RETENTION_POLICY_APPROVED:
                raise RuntimeError("启用生产隐私执行前必须确认数据保存矩阵")
            if cls.PRIVACY_PRODUCTION_EXECUTION_ENABLED and len(str(cls.PRIVACY_TOMBSTONE_SECRET)) < 32:
                raise RuntimeError("启用生产隐私执行前墓碑密钥长度不能少于32个字符")
            if not DB_PROVIDER_ENV_VALUE:
                raise RuntimeError("生产环境必须显式配置 DB_PROVIDER")
            if cls.DB_PROVIDER == "sqlite" and not cls.ALLOW_PRODUCTION_SQLITE:
                raise RuntimeError("生产环境使用 sqlite 必须显式设置 ALLOW_PRODUCTION_SQLITE=1")
            if not cls.ADMIN_EXPORT_TOKEN:
                raise RuntimeError("生产环境必须配置 ADMIN_EXPORT_TOKEN")
            if cls.ADMIN_EXPORT_TOKEN == DEFAULT_ADMIN_EXPORT_TOKEN:
                raise RuntimeError("生产环境禁止使用默认 ADMIN_EXPORT_TOKEN")
            if not cls.SECRET_KEY:
                raise RuntimeError("生产环境必须配置 SECRET_KEY")
            if cls.SECRET_KEY == DEFAULT_SECRET_KEY:
                raise RuntimeError("生产环境禁止使用默认 SECRET_KEY")
            if len(cls.SECRET_KEY) < 32:
                raise RuntimeError("生产环境 SECRET_KEY 长度不能少于 32 个字符")
