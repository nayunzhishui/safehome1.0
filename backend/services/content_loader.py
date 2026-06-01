"""Safe content JSON loading helpers for profile-related services."""

from json import JSONDecodeError
from pathlib import Path

from config import Config
from database import load_content_json


class ContentLoadError(RuntimeError):
    """Raised when a required content file is missing or invalid."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(f"内容文件 {filename} 无法读取：{reason}")
        self.filename = filename
        self.reason = reason


def load_required_content(filename: str) -> dict:
    """Load one required content JSON file with a stable service-level error."""

    path = Config.CONTENT_DIR / filename
    try:
        return load_content_json(filename)
    except FileNotFoundError as exc:
        raise ContentLoadError(filename, f"文件不存在：{Path(path)}") from exc
    except JSONDecodeError as exc:
        raise ContentLoadError(filename, f"JSON 格式错误：第 {exc.lineno} 行第 {exc.colno} 列") from exc


def load_student_profile_rules() -> dict:
    return load_required_content("student_profile_rules.json")


def load_risk_keywords() -> dict:
    return load_required_content("risk_keywords.json")


def load_training_cards() -> dict:
    return load_required_content("training_cards.json")

