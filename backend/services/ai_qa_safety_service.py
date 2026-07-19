"""Deterministic pre/post safety routing for the controlled AI QA sandbox."""

from __future__ import annotations

from database import load_content_json
from services.risk_service import check_text_risk


INJECTION_TERMS = ("忽略之前", "忽略以上", "系统提示", "扩大我的数据权限", "扮演管理员", "ignore previous", "system prompt", "developer message")
PRIVACY_TERMS = ("另一个参与者", "其他用户", "别人的日记", "内部备注", "数据库内容", "管理员密钥", "api key", "token", "cookie")
OUT_OF_SCOPE_TERMS = ("诊断", "确诊", "人格类型", "人格定性", "吃什么药", "药物剂量", "治疗方案", "法律判断", "保证治", "治好", "替我给所有", "自动修改", "自动提交")
EXTRA_HIGH_RISK_TERMS = ("正在打我", "想伤害别人", "威胁我不许告诉", "正在发生暴力", "马上伤害")
POST_BLOCK_TERMS = ("确诊", "一定会改善", "保证治愈", "人格障碍", "SYSTEM PROMPT", "system prompt", "api key", "管理员密钥")


def safety_responses() -> dict[str, dict]:
    payload = load_content_json("ai_qa_safety_responses.json")
    return {str(item.get("route")): item for item in payload.get("responses", []) if isinstance(item, dict) and item.get("route")}


def fixed_response(route: str) -> dict:
    item = safety_responses().get(route) or safety_responses()["safe_degraded"]
    return {
        "route": route,
        "title": item.get("title"),
        "answer": item.get("body"),
        "boundary_notice": item.get("boundary_notice"),
        "human_escalation": bool(item.get("human_escalation")),
        "fixed_response_id": item.get("id"),
    }


def pre_route(text: str) -> dict:
    normalized = str(text or "").strip()
    risk = check_text_risk(normalized, source="ai_qa_precheck")
    if risk.get("risk_level") == "high" or any(term.lower() in normalized.lower() for term in EXTRA_HIGH_RISK_TERMS):
        return {"allowed": False, "route": "risk_fixed", "category": "high_risk", "severity": "critical", "risk": risk}
    lowered = normalized.lower()
    if any(term.lower() in lowered for term in PRIVACY_TERMS):
        return {"allowed": False, "route": "blocked_privacy", "category": "privacy", "severity": "high", "risk": risk}
    if any(term.lower() in lowered for term in INJECTION_TERMS):
        return {"allowed": False, "route": "blocked_injection", "category": "prompt_injection", "severity": "high", "risk": risk}
    if any(term.lower() in lowered for term in OUT_OF_SCOPE_TERMS):
        return {"allowed": False, "route": "blocked_scope", "category": "out_of_scope", "severity": "high", "risk": risk}
    return {"allowed": True, "route": "generate", "category": "allowed_scope", "severity": "low", "risk": risk}


def post_check(text: str, citations: list[dict]) -> dict:
    violations = [term for term in POST_BLOCK_TERMS if term.lower() in str(text or "").lower()]
    if not citations:
        violations.append("missing_approved_citation")
    return {"ok": not violations, "violations": violations, "route": "answered" if not violations else "postcheck_degraded"}
