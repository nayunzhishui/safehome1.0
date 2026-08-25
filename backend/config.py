"""Configuration for the SafeHome MVP backend."""

import os
from pathlib import Path

from services.database_profile_service import startup_profile_errors
from services.database_recovery_service import tls_contract_errors


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_CONTENT_DIR = BASE_DIR / "content" if (BASE_DIR / "content").exists() else PROJECT_ROOT / "content"
DEFAULT_ADMIN_EXPORT_TOKEN = "safehome-local-admin-token"
DEFAULT_SECRET_KEY = "safehome-local-dev-secret"
DB_PROVIDER_ENV_VALUE = os.environ.get("DB_PROVIDER")
DATABASE_PATH_ENV_VALUE = os.environ.get("DATABASE_PATH")


class Config:
    APP_NAME = "safehome"
    APP_ENV = os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "development"))
    DB_PROVIDER = (DB_PROVIDER_ENV_VALUE or "sqlite").strip().lower()
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "safehome.sqlite3"))
    DATABASE_PATH_EXPLICIT = bool(DATABASE_PATH_ENV_VALUE)
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "")
    MYSQL_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("MYSQL_CONNECT_TIMEOUT_SECONDS", "5"))
    MYSQL_READ_TIMEOUT_SECONDS = int(os.environ.get("MYSQL_READ_TIMEOUT_SECONDS", "10"))
    MYSQL_WRITE_TIMEOUT_SECONDS = int(os.environ.get("MYSQL_WRITE_TIMEOUT_SECONDS", "10"))
    MYSQL_SSL_CA = os.environ.get("MYSQL_SSL_CA", "").strip()
    MYSQL_SSL_VERIFY_IDENTITY = os.environ.get(
        "MYSQL_SSL_VERIFY_IDENTITY", "1"
    ).strip().lower() in {"1", "true", "yes", "on"}
    MYSQL_TLS_MIN_VERSION = os.environ.get("MYSQL_TLS_MIN_VERSION", "TLSv1.2").strip()
    DB_PROFILE_CONTRACT_PATH = Path(
        os.environ.get(
            "DB_PROFILE_CONTRACT_PATH",
            PROJECT_ROOT / "config" / "rc0810" / "database_profiles.json",
        )
    )
    DATABASE_DATA_WATERMARK = os.environ.get(
        "DATABASE_DATA_WATERMARK",
        "participant_production"
        if str(APP_ENV).lower() == "production"
        else (
            "synthetic_validation_only"
            if str(APP_ENV).lower() == "validation"
            else "local_fake_only"
        ),
    ).strip()
    DB_PROFILE_APPROVAL_ID = os.environ.get("DB_PROFILE_APPROVAL_ID", "").strip()
    DB_APPROVED_HOST_SHA256 = os.environ.get("DB_APPROVED_HOST_SHA256", "").strip().lower()
    DB_APPROVED_DATABASE = os.environ.get("DB_APPROVED_DATABASE", "").strip()
    DB_APPROVED_PORT = int(os.environ.get("DB_APPROVED_PORT", "0"))
    DB_APPROVED_MIGRATION_HEAD = os.environ.get("DB_APPROVED_MIGRATION_HEAD", "").strip()
    CONTENT_DIR = Path(os.environ.get("CONTENT_DIR", DEFAULT_CONTENT_DIR))
    SECRET_KEY = os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)
    ADMIN_EXPORT_TOKEN = os.environ.get("ADMIN_EXPORT_TOKEN", DEFAULT_ADMIN_EXPORT_TOKEN)
    DEPLOYMENT_CLOUDBASE_ENV_ID = os.environ.get("DEPLOYMENT_CLOUDBASE_ENV_ID", "").strip()
    DEPLOYMENT_CLOUDBASE_SERVICE = os.environ.get("DEPLOYMENT_CLOUDBASE_SERVICE", "").strip()
    DEPLOYMENT_PUBLIC_BASE_URL = os.environ.get("DEPLOYMENT_PUBLIC_BASE_URL", "").strip().rstrip("/")
    DEPLOYMENT_TARGET_ENVIRONMENT = os.environ.get("DEPLOYMENT_TARGET_ENVIRONMENT", "").strip()
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
    AI_QA_REQUESTED_ENABLED = os.environ.get("AI_QA_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
    AI_QA_ENABLED = AI_QA_REQUESTED_ENABLED and str(APP_ENV).lower() != "production"
    AI_QA_SANDBOX_REQUESTED_ENABLED = os.environ.get(
        "AI_QA_SANDBOX_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    AI_QA_SANDBOX_ENABLED = AI_QA_SANDBOX_REQUESTED_ENABLED and str(APP_ENV).lower() != "production"
    AI_QA_PROVIDER = os.environ.get("AI_QA_PROVIDER", "fake").strip().lower()
    AI_QA_REAL_PROVIDER_REQUESTED_ENABLED = os.environ.get(
        "AI_QA_REAL_PROVIDER_ENABLED", "0"
    ).strip().lower() in {"1", "true", "yes"}
    AI_QA_REAL_PROVIDER_ENABLED = AI_QA_REAL_PROVIDER_REQUESTED_ENABLED and str(APP_ENV).lower() != "production"
    AI_QA_REQUESTS_PER_HOUR = int(os.environ.get("AI_QA_REQUESTS_PER_HOUR", "30"))
    AI_QA_DAILY_BUDGET_MICROS = int(os.environ.get("AI_QA_DAILY_BUDGET_MICROS", "0"))
    AI_QA_TIMEOUT_MS = int(os.environ.get("AI_QA_TIMEOUT_MS", "3000"))
    AI_QA_CONNECT_TIMEOUT_MS = int(
        os.environ.get("AI_QA_CONNECT_TIMEOUT_MS", "1000")
    )
    AI_QA_READ_TIMEOUT_MS = int(
        os.environ.get("AI_QA_READ_TIMEOUT_MS", "2000")
    )
    AI_QA_PROVIDER_RETRIES = int(os.environ.get("AI_QA_PROVIDER_RETRIES", "1"))
    AI_QA_SYNTHETIC_RETENTION_DAYS = int(os.environ.get("AI_QA_SYNTHETIC_RETENTION_DAYS", "7"))
    OFFLINE_BENCHMARK_ENABLED = os.environ.get(
        "OFFLINE_BENCHMARK_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    OFFLINE_EXTERNAL_INGEST_ENABLED = os.environ.get("OFFLINE_EXTERNAL_INGEST_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
    OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED = os.environ.get("OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED", "0").strip().lower() in {"1", "true", "yes"}
    RESEARCH_METHODOLOGY_WORKBENCH_ENABLED = os.environ.get(
        "RESEARCH_METHODOLOGY_WORKBENCH_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED = os.environ.get("RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED", "0").strip().lower() in {"1", "true", "yes"}
    RESEARCH_OUTCOME_ANALYSIS_ALLOWED = os.environ.get("RESEARCH_OUTCOME_ANALYSIS_ALLOWED", "0").strip().lower() in {"1", "true", "yes"}
    RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED = os.environ.get(
        "RESEARCH_ANALYSIS_JOB_EXECUTION_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    SECURITY_SCAN_EXECUTION_ENABLED = os.environ.get(
        "SECURITY_SCAN_EXECUTION_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    RELIABILITY_WORKBENCH_ENABLED = os.environ.get(
        "RELIABILITY_WORKBENCH_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    RELIABILITY_JOB_EXECUTION_ENABLED = os.environ.get(
        "RELIABILITY_JOB_EXECUTION_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    RELIABILITY_FAULT_INJECTION_ENABLED = os.environ.get(
        "RELIABILITY_FAULT_INJECTION_ENABLED", "0"
    ).strip().lower() in {"1", "true", "yes"}
    RELIABILITY_GRADUAL_RELEASE_ENABLED = os.environ.get(
        "RELIABILITY_GRADUAL_RELEASE_ENABLED", "0"
    ).strip().lower() in {"1", "true", "yes"}
    RELIABILITY_PRODUCTION_SLO_FROZEN = os.environ.get(
        "RELIABILITY_PRODUCTION_SLO_FROZEN", "0"
    ).strip().lower() in {"1", "true", "yes"}
    OPERATIONS_HEALTH_TOKEN = os.environ.get("OPERATIONS_HEALTH_TOKEN", "").strip()
    UX_GOVERNANCE_WORKBENCH_ENABLED = os.environ.get(
        "UX_GOVERNANCE_WORKBENCH_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED = os.environ.get(
        "OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    OPERATIONS_LOCAL_RELEASE_ENABLED = os.environ.get(
        "OPERATIONS_LOCAL_RELEASE_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    OPERATIONS_PRODUCTION_RELEASE_ENABLED = os.environ.get(
        "OPERATIONS_PRODUCTION_RELEASE_ENABLED", "0"
    ).strip().lower() in {"1", "true", "yes"}
    PRODUCTION_FEATURES_UNLOCKED = os.environ.get(
        "PRODUCTION_FEATURES_UNLOCKED", "0"
    ).strip().lower() in {"1", "true", "yes"}
    THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED = os.environ.get(
        "THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    SAFETY_SCHEDULER_ENABLED = os.environ.get(
        "SAFETY_SCHEDULER_ENABLED",
        "1" if str(APP_ENV).lower() in {"development", "testing"} else "0",
    ).strip().lower() in {"1", "true", "yes"}
    SAFETY_SCHEDULER_LEASE_SECONDS = int(os.environ.get("SAFETY_SCHEDULER_LEASE_SECONDS", "120"))
    SAFETY_SCHEDULER_MAX_ATTEMPTS = int(os.environ.get("SAFETY_SCHEDULER_MAX_ATTEMPTS", "3"))

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
        if min(
            cls.MYSQL_CONNECT_TIMEOUT_SECONDS,
            cls.MYSQL_READ_TIMEOUT_SECONDS,
            cls.MYSQL_WRITE_TIMEOUT_SECONDS,
        ) <= 0:
            raise RuntimeError("MySQL 连接、读取和写入超时必须为正整数")
        tls_errors = tls_contract_errors(cls)
        if tls_errors:
            messages = {
                "mysql_tls_ca_required": "生产 MySQL 必须配置有效 TLS CA 文件",
                "mysql_tls_identity_verification_required": "生产 MySQL 必须启用主机身份校验",
                "mysql_tls_minimum_version_too_low": "生产 MySQL 最低 TLS 版本必须为 TLSv1.2 或 TLSv1.3",
            }
            raise RuntimeError(messages[tls_errors[0]])
        if cls.SAFETY_SCHEDULER_LEASE_SECONDS < 30 or cls.SAFETY_SCHEDULER_MAX_ATTEMPTS not in range(1, 11):
            raise RuntimeError("安全调度器租约必须不少于30秒，最大尝试次数必须为1至10")
        if str(cls.APP_ENV).lower() == "production" and cls.SAFETY_SCHEDULER_ENABLED:
            raise RuntimeError("F15 人工容量与值守证据未批准前禁止生产启用安全调度器")
        if str(cls.APP_ENV).lower() == "production" and not DB_PROVIDER_ENV_VALUE:
            raise RuntimeError("生产环境必须显式配置 DB_PROVIDER")
        profile_errors = startup_profile_errors(cls)
        if profile_errors:
            messages = {
                "database_provider_not_allowed": "production 数据库只允许 MySQL",
                "production_sqlite_override_forbidden": "生产环境禁止 ALLOW_PRODUCTION_SQLITE",
                "production_database_approval_missing": "生产数据库缺少批准摘要",
                "production_database_host_not_approved": "生产数据库主机不匹配批准摘要",
                "production_database_name_not_approved": "生产数据库名不匹配批准摘要",
                "production_database_port_not_approved": "生产数据库端口不匹配批准摘要",
                "production_database_migration_head_not_approved": "生产数据库 migration head 不匹配批准摘要",
                "database_data_watermark_mismatch": "数据库数据水印与 profile 不一致",
                "validation_sqlite_path_not_explicit": "validation SQLite 必须显式配置 DATABASE_PATH",
                "database_profile_unknown_environment": "APP_ENV 没有对应数据库 profile",
            }
            raise RuntimeError(messages.get(profile_errors[0], profile_errors[0]))
        if cls.WECHAT_SUBSCRIBE_MODE not in {"once", "long_term"}:
            raise RuntimeError("WECHAT_SUBSCRIBE_MODE 只能是 once 或 long_term")
        if cls.AI_QA_PROVIDER not in {"fake", "deepseek", "openai"}:
            raise RuntimeError("AI_QA_PROVIDER 只能是 fake、deepseek 或 openai")
        if cls.AI_QA_PROVIDER != "fake" and not cls.AI_QA_REAL_PROVIDER_ENABLED:
            raise RuntimeError(
                "真实供应商必须由服务端显式开启 AI_QA_REAL_PROVIDER_ENABLED"
            )
        if min(
            cls.AI_QA_TIMEOUT_MS,
            cls.AI_QA_CONNECT_TIMEOUT_MS,
            cls.AI_QA_READ_TIMEOUT_MS,
        ) <= 0:
            raise RuntimeError("AI供应商连接、读取和总超时必须为正整数")
        guarded_production_features = [
            name
            for name in (
                "AI_QA_ENABLED",
                "OFFLINE_EXTERNAL_INGEST_ENABLED",
                "OFFLINE_PRODUCTION_REPLACEMENT_ALLOWED",
                "RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED",
                "RESEARCH_OUTCOME_ANALYSIS_ALLOWED",
                "RELIABILITY_GRADUAL_RELEASE_ENABLED",
                "RELIABILITY_PRODUCTION_SLO_FROZEN",
                "OPERATIONS_PRODUCTION_RELEASE_ENABLED",
            )
            if getattr(cls, name)
        ]
        if guarded_production_features and not cls.PRODUCTION_FEATURES_UNLOCKED:
            raise RuntimeError(
                "受控生产功能必须先显式设置 PRODUCTION_FEATURES_UNLOCKED=1："
                + ", ".join(guarded_production_features)
            )
        if str(cls.APP_ENV).lower() == "production" and cls.RELIABILITY_FAULT_INJECTION_ENABLED:
            raise RuntimeError("生产环境禁止启用 RELIABILITY_FAULT_INJECTION_ENABLED")
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
            if "*" in cls.ALLOWED_ORIGINS:
                raise RuntimeError("生产环境 ALLOWED_ORIGINS 禁止使用通配符")
            if cls.PRIVACY_PRODUCTION_EXECUTION_ENABLED and not cls.PRIVACY_EXECUTION_ENABLED:
                raise RuntimeError("启用生产隐私执行前必须同时开启 PRIVACY_EXECUTION_ENABLED")
            if cls.PRIVACY_PRODUCTION_EXECUTION_ENABLED and not cls.PRIVACY_RETENTION_POLICY_APPROVED:
                raise RuntimeError("启用生产隐私执行前必须确认数据保存矩阵")
            if cls.PRIVACY_PRODUCTION_EXECUTION_ENABLED and len(str(cls.PRIVACY_TOMBSTONE_SECRET)) < 32:
                raise RuntimeError("启用生产隐私执行前墓碑密钥长度不能少于32个字符")
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
