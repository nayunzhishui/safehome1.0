"""Fail-closed input minimization and read-only tool policy for AI QA."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


INPUT_SECURITY_VERSION = "safehome-ai-qa-input-security-v1"
MAX_QUESTION_LENGTH = 2000
MAX_SOURCE_EXCERPT_LENGTH = 500
MESSAGE_FIELD_ALLOWLIST = {
    "text",
    "synthetic_data",
    "use_case_id",
    "fake_mode",
}
SOURCE_FIELD_ALLOWLIST = {
    "content_type",
    "content_id",
    "title",
    "version_id",
    "content_version",
    "release_id",
    "payload_hash",
    "excerpt",
    "governance_status",
    "package_hash",
    "document_id",
    "chunk_id",
    "location",
    "source_ref",
    "source_version",
    "rights_status",
    "review_status",
    "valid_from",
    "expires_at",
    "audiences",
    "retrieval_method",
    "scores",
}
APPROVED_RIGHTS = {
    "owned",
    "licensed",
    "public_domain",
    "permission_recorded",
}
READ_ONLY_TOOL_ALLOWLIST = {"knowledge.retrieve"}
FORBIDDEN_TOOL_ARGUMENTS = {
    "path",
    "file",
    "directory",
    "url",
    "uri",
    "host",
    "hostname",
    "domain",
    "headers",
    "authorization",
    "token",
    "cookie",
    "user_id",
    "participant_id",
}
ALLOWED_RETRIEVAL_METHODS = {"bm25", "vector", "hybrid"}
OUT_OF_DOMAIN_TERMS = (
    "sql攻击",
    "攻击服务器",
    "绕过防火墙",
    "窃取密码",
    "恶意代码",
    "预测股票",
    "股票买卖",
    "博彩",
    "下注",
    "代写论文",
)

_PII_PATTERNS = (
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[手机号已去标识]"),
    (
        "email",
        re.compile(
            r"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"
            r"(?![A-Z0-9._%+-])"
        ),
        "[邮箱已去标识]",
    ),
    (
        "identity_document",
        re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
        "[证件号已去标识]",
    ),
    (
        "ip_address",
        re.compile(
            r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)"
            r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)"
        ),
        "[网络地址已去标识]",
    ),
    (
        "wechat_id",
        re.compile(r"(?i)(微信号|wechat\s*id)\s*[:：]?\s*[a-z][-_a-z0-9]{5,19}"),
        "[微信号已去标识]",
    ),
)


class InputSecurityError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


def get_input_security_policy() -> dict[str, Any]:
    return {
        "version": INPUT_SECURITY_VERSION,
        "instruction_data_separated": True,
        "retrieved_content_trusted": False,
        "message_field_allowlist": sorted(MESSAGE_FIELD_ALLOWLIST),
        "source_field_allowlist": sorted(SOURCE_FIELD_ALLOWLIST),
        "max_question_length": MAX_QUESTION_LENGTH,
        "max_source_excerpt_length": MAX_SOURCE_EXCERPT_LENGTH,
        "deidentification_categories": [
            item[0] for item in _PII_PATTERNS
        ],
        "cross_session_memory": False,
        "raw_input_persisted": False,
        "default_mode": "deny",
        "allowlist": sorted(READ_ONLY_TOOL_ALLOWLIST),
        "write_tools_allowed": False,
        "arbitrary_paths_allowed": False,
        "arbitrary_network_hosts_allowed": False,
    }


def validate_message_payload(
    payload: dict[str, Any],
    *,
    app_env: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise InputSecurityError(
            "input_payload_invalid",
            "消息请求必须是JSON对象",
        )
    allowed = set(MESSAGE_FIELD_ALLOWLIST)
    if str(app_env).lower() not in {"development", "testing"}:
        allowed.discard("fake_mode")
    unexpected = sorted(str(key) for key in payload if key not in allowed)
    if unexpected:
        raise InputSecurityError(
            "input_fields_not_allowed",
            "消息包含服务端未允许的字段",
            details={"fields": unexpected},
        )
    return {key: deepcopy(payload[key]) for key in allowed if key in payload}


def deidentify_text(text: object, *, max_length: int) -> dict[str, Any]:
    normalized = str(text or "").strip()
    if not normalized or len(normalized) > max_length:
        raise InputSecurityError(
            "input_length_invalid",
            f"文本长度必须为1至{max_length}字",
            status=422,
        )
    counts: dict[str, int] = {}
    for category, pattern, replacement in _PII_PATTERNS:
        normalized, count = pattern.subn(replacement, normalized)
        if count:
            counts[category] = count
    return {
        "text": normalized,
        "categories": sorted(counts),
        "counts": counts,
        "deidentified_count": sum(counts.values()),
    }


def classify_input_domain(text: object) -> dict[str, Any]:
    normalized = str(text or "").strip().lower()
    hits = [term for term in OUT_OF_DOMAIN_TERMS if term.lower() in normalized]
    return {
        "allowed": not hits,
        "category": "allowed_scope" if not hits else "out_of_domain",
        "matched_rules": hits,
    }


def _source_is_authorized(source: dict[str, Any], audience: str) -> bool:
    audiences = source.get("audiences")
    audience_allowed = (
        not isinstance(audiences, list)
        or not audiences
        or audience in {str(item) for item in audiences}
    )
    return bool(
        source.get("governance_status") == "published"
        and source.get("rights_status") in APPROVED_RIGHTS
        and source.get("review_status") == "approved"
        and source.get("version_id")
        and source.get("release_id")
        and source.get("source_ref")
        and audience_allowed
    )


def prepare_provider_input(
    question: object,
    sources: list[dict[str, Any]],
    *,
    audience: str,
) -> dict[str, Any]:
    privacy = deidentify_text(question, max_length=MAX_QUESTION_LENGTH)
    citations: list[dict[str, Any]] = []
    rejected = 0
    source_deidentified = 0
    for source in sources or []:
        if not isinstance(source, dict) or not _source_is_authorized(
            source, audience
        ):
            rejected += 1
            continue
        sanitized = {
            key: deepcopy(value)
            for key, value in source.items()
            if key in SOURCE_FIELD_ALLOWLIST
        }
        excerpt = deidentify_text(
            sanitized.get("excerpt"),
            max_length=MAX_SOURCE_EXCERPT_LENGTH,
        )
        sanitized["excerpt"] = excerpt["text"]
        sanitized["untrusted_retrieved_data"] = True
        source_deidentified += int(excerpt["deidentified_count"])
        citations.append(sanitized)
    return {
        "question": privacy["text"],
        "citations": citations,
        "privacy": {
            **privacy,
            "source_deidentified_count": source_deidentified,
            "raw_input_persisted": False,
        },
        "authorization": {
            "only_authorized_sources": True,
            "accepted_source_count": len(citations),
            "rejected_source_count": rejected,
            "audience": audience,
        },
        "security_version": INPUT_SECURITY_VERSION,
    }


def validate_tool_request(
    tool_name: object,
    arguments: object,
    *,
    audience: str,
) -> dict[str, Any]:
    normalized_name = str(tool_name or "").strip()
    if normalized_name not in READ_ONLY_TOOL_ALLOWLIST:
        raise InputSecurityError(
            "tool_not_allowed",
            "工具不在服务端只读允许清单中",
            status=409,
        )
    if not isinstance(arguments, dict):
        raise InputSecurityError(
            "tool_arguments_invalid",
            "工具参数必须是JSON对象",
        )
    forbidden = sorted(
        str(key) for key in arguments if str(key) in FORBIDDEN_TOOL_ARGUMENTS
    )
    if forbidden:
        raise InputSecurityError(
            "tool_boundary_violation",
            "工具参数触发路径、身份或网络边界",
            status=409,
            details={"fields": forbidden},
        )
    allowed_keys = {"query", "method", "limit"}
    unexpected = sorted(str(key) for key in arguments if key not in allowed_keys)
    if unexpected:
        raise InputSecurityError(
            "tool_arguments_not_allowed",
            "工具包含未允许的参数",
            details={"fields": unexpected},
        )
    query = deidentify_text(
        arguments.get("query"),
        max_length=MAX_QUESTION_LENGTH,
    )["text"]
    method = str(arguments.get("method") or "hybrid")
    if method not in ALLOWED_RETRIEVAL_METHODS:
        raise InputSecurityError(
            "tool_arguments_invalid",
            "检索方式不在允许范围内",
        )
    try:
        limit = int(arguments.get("limit") or 5)
    except (TypeError, ValueError) as exc:
        raise InputSecurityError(
            "tool_arguments_invalid",
            "检索数量必须是整数",
        ) from exc
    if limit < 1 or limit > 10:
        raise InputSecurityError(
            "tool_arguments_invalid",
            "检索数量必须为1至10",
        )
    return {
        "tool_name": normalized_name,
        "read_only": True,
        "arguments": {
            "query": query,
            "method": method,
            "limit": limit,
            "audience": str(audience),
        },
    }
