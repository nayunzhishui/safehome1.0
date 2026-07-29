"""Versioned content governance, release, rollback, dependency and replay services."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from flask import current_app

from database import get_connection, json_dumps, json_loads, new_id, now_iso, row_to_dict, rows_to_dicts, write_audit_log
from services.feedback_service import generate_feedback
from services.risk_service import check_text_risk


CONTENT_TARGETS = {
    "scale": ("scales_catalog.json", "scales", "id"),
    "worksheet": ("assessment_worksheets.json", "worksheets", "id"),
    "training_card": ("training_cards.json", "cards", "id"),
    "feedback_rule": ("feedback_rules.json", "rules", "id"),
    "student_profile_rule": ("student_profile_rules.json", "rules", "id"),
    "assessment_training_rule": ("assessment_training_map.json", "rules", "rule_id"),
    "diary_training_rule": ("diary_training_map.json", "rules", "rule_id"),
    "program": ("programs.json", "programs", "id"),
    "course": ("courses.json", "courses", "id"),
    "faq": ("faq.json", "items", "id"),
    "consent_text": ("consent.md", None, None),
    "privacy_text": ("privacy.md", None, None),
    "ai_safety_text": ("ai_qa_safety_responses.json", "responses", "id"),
    "therapeutic_method": (
        "therapeutic_assessment_method_library.json",
        "items",
        "id",
    ),
}
REQUIRED_METADATA = ("source", "source_version", "copyright_status", "age_scope", "audience", "change_summary")
REQUIRED_DISCIPLINES = ("research", "psychology", "ethics", "content")
DISCIPLINE_ROLES = {
    "research": {"researcher", "admin"},
    "psychology": {"supervisor", "admin"},
    "ethics": {"supervisor", "admin"},
    "content": {"admin"},
}
TERMINAL_STATUSES = {"retired"}


class GovernanceError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details or {}


@contextmanager
def _release_lock():
    """Serialize file/database release switches across local worker processes."""
    lock_path = current_app.config["CONTENT_DIR"] / ".content-governance.lock"
    descriptor = None
    for _attempt in range(2):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, now_iso().encode("utf-8"))
            break
        except FileExistsError as exc:
            try:
                stale = time.time() - lock_path.stat().st_mtime > 300
            except OSError:
                stale = False
            if stale:
                lock_path.unlink(missing_ok=True)
                continue
            raise GovernanceError("content_release_in_progress", "已有内容发布或恢复操作正在执行", 409) from exc
    if descriptor is None:
        raise GovernanceError("content_release_lock_failed", "无法取得内容发布锁", 409)
    try:
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _decode_version(row) -> dict:
    item = row_to_dict(row)
    if not item:
        return item
    item["payload"] = json_loads(item.pop("payload_json"), {})
    item["metadata"] = json_loads(item.pop("metadata_json"), {})
    return item


def _load_target(content_type: str) -> tuple[Path, str | None, str | None]:
    target = CONTENT_TARGETS.get(content_type)
    if not target:
        raise GovernanceError("unsupported_content_type", "不支持的内容类型")
    filename, list_field, id_field = target
    return current_app.config["CONTENT_DIR"] / filename, list_field, id_field


def _load_active_item(content_type: str, item_id: str):
    path, list_field, id_field = _load_target(content_type)
    if not path.exists():
        raise GovernanceError("content_source_missing", f"内容源不存在：{path.name}", 404)
    if list_field is None:
        return path.read_text(encoding="utf-8"), path
    content = json.loads(path.read_text(encoding="utf-8"))
    item = next((entry for entry in content.get(list_field, []) if str(entry.get(id_field)) == item_id), None)
    if item is None:
        raise GovernanceError("not_found", "未找到对应内容项", 404)
    return item, path


def list_inventory() -> dict:
    manifest_path = current_app.config["CONTENT_DIR"] / "content_governance_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"sources": []}
    manifest_by_file = {item.get("filename"): item for item in manifest.get("sources", [])}
    items = []
    missing_sources = []
    for content_type, (filename, list_field, id_field) in CONTENT_TARGETS.items():
        path = current_app.config["CONTENT_DIR"] / filename
        if not path.exists():
            missing_sources.append(filename)
            continue
        if list_field is None:
            entries = [(content_type.removesuffix("_text"), path.read_text(encoding="utf-8"))]
            source_version = path.stat().st_mtime_ns
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            entries = [(str(item.get(id_field)), item) for item in payload.get(list_field, []) if item.get(id_field)]
            source_version = payload.get("version") or payload.get("updated_at") or "unknown"
        with get_connection() as conn:
            for item_id, entry in entries:
                row = conn.execute(
                    "SELECT id, version, status, payload_hash FROM content_governance_versions WHERE content_type = ? AND item_id = ? ORDER BY created_at DESC LIMIT 1",
                    (content_type, item_id),
                ).fetchone()
                items.append({
                    "content_type": content_type,
                    "item_id": item_id,
                    "source_file": filename,
                    "source_version": str(source_version),
                    "active_hash": _hash(entry),
                    "governed_version": dict(row) if row else None,
                    "source_metadata": manifest_by_file.get(filename, {}),
                })
    return {"items": items, "missing_sources": sorted(set(missing_sources)), "manifest_version": manifest.get("version"), "import_policy": "register_only_never_auto_approve"}


def register_inventory(actor: dict) -> dict:
    inventory = list_inventory()
    created = 0
    with get_connection() as conn:
        for item in inventory["items"]:
            if item["governed_version"]:
                continue
            payload, _path = _load_active_item(item["content_type"], item["item_id"])
            version_id = new_id("cgv")
            timestamp = now_iso()
            source_metadata = item.get("source_metadata") or {}
            metadata = {
                "source": source_metadata.get("source") or item["source_file"],
                "source_version": source_metadata.get("source_version") or item["source_version"],
                "copyright_status": source_metadata.get("copyright_status") or "unverified",
                "age_scope": source_metadata.get("age_scope") or "unverified",
                "audience": payload.get("audience", source_metadata.get("audience", "unverified")) if isinstance(payload, dict) else source_metadata.get("audience", "all"),
                "change_summary": "旧内容登记；未自动批准或发布",
                "governance_status": source_metadata.get("governance_status") or "registered",
            }
            conn.execute(
                "INSERT INTO content_governance_versions (id, content_type, item_id, version, payload_json, payload_hash, metadata_json, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'registered', ?, ?, ?)",
                (version_id, item["content_type"], item["item_id"], f"legacy-{item['source_version']}", json_dumps(payload), item["active_hash"], json_dumps(metadata), actor["id"], timestamp, timestamp),
            )
            created += 1
        write_audit_log(conn, "content_inventory_registered", actor["id"], "content_inventory", "all", {"created": created, "missing_sources": inventory["missing_sources"], "auto_approved": False})
        conn.commit()
    return {"created": created, "skipped": len(inventory["items"]) - created, "missing_sources": inventory["missing_sources"], "auto_approved": False}


def create_draft(actor: dict, payload: dict) -> dict:
    content_type = str(payload.get("content_type") or "").strip()
    item_id = str(payload.get("item_id") or "").strip()
    version = str(payload.get("version") or "").strip()
    content_payload = payload.get("payload")
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    if not content_type or not item_id or not version or content_payload is None:
        raise GovernanceError("validation_error", "content_type、item_id、version 和 payload 为必填项")
    _load_target(content_type)
    if content_type.endswith("_text") and not isinstance(content_payload, str):
        raise GovernanceError("validation_error", "边界文本 payload 必须是字符串")
    if not content_type.endswith("_text") and not isinstance(content_payload, dict):
        raise GovernanceError("validation_error", "结构化内容 payload 必须是对象")
    missing = [field for field in REQUIRED_METADATA if not str(metadata.get(field) or "").strip()]
    if missing:
        raise GovernanceError("content_metadata_incomplete", "内容元数据不完整", details={"missing_fields": missing})
    parent_version_id = str(payload.get("parent_version_id") or "").strip() or None
    version_id = new_id("cgv")
    timestamp = now_iso()
    digest = _hash(content_payload)
    with get_connection() as conn:
        if parent_version_id:
            parent = conn.execute("SELECT id FROM content_governance_versions WHERE id = ?", (parent_version_id,)).fetchone()
            if not parent:
                raise GovernanceError("parent_version_not_found", "父版本不存在", 404)
        try:
            conn.execute(
                "INSERT INTO content_governance_versions (id, content_type, item_id, version, parent_version_id, payload_json, payload_hash, metadata_json, status, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)",
                (version_id, content_type, item_id, version, parent_version_id, json_dumps(content_payload), digest, json_dumps({**metadata, "governance_status": "draft"}), actor["id"], timestamp, timestamp),
            )
        except Exception as exc:
            if "UNIQUE" in str(exc).upper() or "duplicate" in str(exc).lower():
                raise GovernanceError("content_version_exists", "同一内容版本已存在", 409) from exc
            raise
        write_audit_log(conn, "content_draft_created", actor["id"], "content_version", version_id, {"content_type": content_type, "item_id": item_id, "version": version, "payload_hash": digest})
        conn.commit()
    return get_version(version_id)


def get_version(version_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM content_governance_versions WHERE id = ?", (version_id,)).fetchone()
        if not row:
            raise GovernanceError("not_found", "内容版本不存在", 404)
        item = _decode_version(row)
        item["reviews"] = rows_to_dicts(conn.execute("SELECT * FROM content_governance_reviews WHERE version_id = ? ORDER BY created_at", (version_id,)).fetchall())
        item["releases"] = rows_to_dicts(conn.execute("SELECT * FROM content_governance_releases WHERE version_id = ? ORDER BY created_at", (version_id,)).fetchall())
    item["validation"] = validate_version_payload(item)
    item["dependency_impact"] = dependency_impact(item["content_type"], item["item_id"])
    return item


def list_versions(content_type: str | None = None, item_id: str | None = None) -> list[dict]:
    where, params = [], []
    if content_type:
        where.append("content_type = ?")
        params.append(content_type)
    if item_id:
        where.append("item_id = ?")
        params.append(item_id)
    clause = f" WHERE {' AND '.join(where)}" if where else ""
    with get_connection() as conn:
        rows = conn.execute(f"SELECT * FROM content_governance_versions{clause} ORDER BY created_at DESC LIMIT 500", tuple(params)).fetchall()
    return [_decode_version(row) for row in rows]


def get_active_descriptor(content_type: str, item_id: str) -> dict:
    active_payload, path = _load_active_item(content_type, item_id)
    active_hash = _hash(active_payload)
    with get_connection() as conn:
        release = conn.execute(
            "SELECT id, version_id, payload_hash, created_at FROM content_governance_releases WHERE content_type = ? AND item_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (content_type, item_id),
        ).fetchone()
    if release and release["payload_hash"] != active_hash:
        raise GovernanceError("active_content_integrity_failed", "运行内容与受控发布哈希不一致", 503)
    return {
        "content_type": content_type,
        "item_id": item_id,
        "source_file": path.name,
        "payload_hash": active_hash,
        "release_id": release["id"] if release else None,
        "version_id": release["version_id"] if release else None,
        "governance_status": "published" if release else "legacy_active_unregistered",
    }


def validate_version_payload(version: dict) -> dict:
    errors, warnings = [], []
    payload = version.get("payload")
    metadata = version.get("metadata") or {}
    for field in REQUIRED_METADATA:
        if not str(metadata.get(field) or "").strip():
            errors.append({"code": "metadata_missing", "field": field})
    if metadata.get("copyright_status") not in {"owned", "licensed", "public_domain", "permission_recorded"}:
        errors.append({"code": "copyright_unverified", "field": "copyright_status"})
    if str(metadata.get("age_scope") or "").strip().lower() in {"", "unverified", "unknown"}:
        errors.append({"code": "age_scope_unverified", "field": "age_scope"})
    if isinstance(payload, dict):
        if not (payload.get("id") or payload.get("rule_id")):
            warnings.append({"code": "payload_id_missing"})
        serialized = _canonical(payload)
    elif isinstance(payload, str):
        serialized = payload
        if len(payload.strip()) < 20:
            errors.append({"code": "boundary_text_too_short"})
    else:
        serialized = ""
        errors.append({"code": "payload_type_invalid"})
    prohibited = [term for term in ("确诊", "人格障碍", "一定是", "保证治愈") if term in serialized]
    if prohibited:
        errors.append({"code": "diagnostic_or_promissory_copy", "terms": prohibited})
    return {"ok": not errors, "errors": errors, "warnings": warnings, "payload_hash_valid": version.get("payload_hash") == _hash(payload)}


def diff_version(version_id: str) -> dict:
    version = get_version(version_id)
    if version.get("parent_version_id"):
        parent = get_version(version["parent_version_id"])
        baseline = parent["payload"]
        baseline_ref = parent["id"]
    else:
        try:
            baseline, _path = _load_active_item(version["content_type"], version["item_id"])
            baseline_ref = "active_content"
        except GovernanceError:
            baseline, baseline_ref = {}, "empty"
    before = json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    after = json.dumps(version["payload"], ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    lines = list(difflib.unified_diff(before, after, fromfile=baseline_ref, tofile=version["id"], lineterm=""))
    return {"version_id": version_id, "baseline": baseline_ref, "changed": bool(lines), "diff": lines[:2000], "truncated": len(lines) > 2000}


def submit_version(actor: dict, version_id: str) -> dict:
    version = get_version(version_id)
    if version["status"] not in {"draft", "rejected"}:
        raise GovernanceError("invalid_content_transition", "只有草稿或被驳回版本可以送审", 409)
    validation = version["validation"]
    if not validation["ok"] or not validation["payload_hash_valid"]:
        raise GovernanceError("content_validation_failed", "内容校验未通过", 409, validation)
    _set_status(actor, version_id, "pending_review", "content_submitted", submitted=True)
    return get_version(version_id)


def review_version(actor: dict, version_id: str, payload: dict) -> dict:
    discipline = str(payload.get("discipline") or "").strip()
    decision = str(payload.get("decision") or "").strip()
    evidence_path = str(payload.get("evidence_path") or "").strip()
    if discipline not in REQUIRED_DISCIPLINES or decision not in {"approved", "rejected"}:
        raise GovernanceError("validation_error", "discipline 或 decision 无效")
    if actor.get("role") not in DISCIPLINE_ROLES[discipline]:
        raise GovernanceError("review_discipline_forbidden", "当前角色不能执行该专业审核", 403)
    if not evidence_path:
        raise GovernanceError("review_evidence_required", "审核证据路径不能为空")
    version = get_version(version_id)
    if version["status"] not in {"pending_review", "approved", "rejected"}:
        raise GovernanceError("invalid_content_transition", "当前版本不在可审核状态", 409)
    review_id = new_id("cgr")
    with get_connection() as conn:
        other_approval = conn.execute(
            "SELECT discipline FROM content_governance_reviews WHERE version_id = ? AND reviewer_id = ? AND discipline <> ? AND decision = 'approved' LIMIT 1",
            (version_id, actor["id"], discipline),
        ).fetchone()
        if decision == "approved" and other_approval:
            raise GovernanceError("reviewer_independence_required", "同一人不能代表多个专业责任完成批准", 409, {"existing_discipline": other_approval["discipline"]})
        conn.execute("DELETE FROM content_governance_reviews WHERE version_id = ? AND discipline = ? AND reviewer_id = ?", (version_id, discipline, actor["id"]))
        conn.execute(
            "INSERT INTO content_governance_reviews (id, version_id, discipline, decision, reviewer_id, reviewer_role, evidence_path, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (review_id, version_id, discipline, decision, actor["id"], actor["role"], evidence_path, str(payload.get("note") or "").strip() or None, now_iso()),
        )
        reviews = conn.execute("SELECT discipline, decision FROM content_governance_reviews WHERE version_id = ?", (version_id,)).fetchall()
        latest = {row["discipline"]: row["decision"] for row in reviews}
        status = "rejected" if "rejected" in latest.values() else ("approved" if all(latest.get(item) == "approved" for item in REQUIRED_DISCIPLINES) else "pending_review")
        conn.execute("UPDATE content_governance_versions SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso(), version_id))
        write_audit_log(conn, "content_review_recorded", actor["id"], "content_version", version_id, {"discipline": discipline, "decision": decision, "evidence_path": evidence_path, "resulting_status": status})
        conn.commit()
    return get_version(version_id)


def _set_status(actor: dict, version_id: str, status: str, action: str, submitted: bool = False, retired: bool = False) -> None:
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            "UPDATE content_governance_versions SET status = ?, updated_at = ?, submitted_at = CASE WHEN ? THEN ? ELSE submitted_at END, retired_at = CASE WHEN ? THEN ? ELSE retired_at END WHERE id = ?",
            (status, timestamp, 1 if submitted else 0, timestamp, 1 if retired else 0, timestamp, version_id),
        )
        write_audit_log(conn, action, actor["id"], "content_version", version_id, {"status": status})
        conn.commit()


def dependency_impact(content_type: str, item_id: str) -> dict:
    impacts = []
    scans = {
        "assessment_training_map.json": ("recommendation_rule", "rules"),
        "diary_training_map.json": ("recommendation_rule", "rules"),
        "courses.json": ("course", "courses"),
        "programs.json": ("program", "programs"),
    }
    for filename, (kind, list_field) in scans.items():
        path = current_app.config["CONTENT_DIR"] / filename
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload.get(list_field, []):
            if item_id in _canonical(entry):
                impacts.append({"source_file": filename, "dependency_type": kind, "dependency_id": entry.get("id") or entry.get("rule_id")})
    with get_connection() as conn:
        try:
            count = conn.execute("SELECT COUNT(*) AS count FROM training_plan_items WHERE card_id = ?", (item_id,)).fetchone()
            if count and int(count["count"]):
                impacts.append({"source_file": "database", "dependency_type": "training_plan", "count": int(count["count"])})
        except Exception:
            pass
    return {"content_type": content_type, "item_id": item_id, "has_dependencies": bool(impacts), "impacts": impacts}


def _replace_active_item(content_type: str, item_id: str, payload) -> tuple[Path, bytes | None]:
    path, list_field, id_field = _load_target(content_type)
    old_bytes = path.read_bytes() if path.exists() else None
    if list_field is None:
        rendered = str(payload)
    else:
        root = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": "governed", list_field: []}
        items = root.setdefault(list_field, [])
        index = next((idx for idx, item in enumerate(items) if str(item.get(id_field)) == item_id), None)
        if index is None:
            items.append(payload)
        else:
            items[index] = payload
        root["updated_at"] = now_iso()
        rendered = json.dumps(root, ensure_ascii=False, indent=2) + "\n"
    temp = path.with_suffix(path.suffix + f".{new_id('tmp')}")
    temp.write_text(rendered, encoding="utf-8")
    os.replace(temp, path)
    return path, old_bytes


def publish_version(actor: dict, version_id: str, payload: dict) -> dict:
    with _release_lock():
        return _publish_version_locked(actor, version_id, payload)


def _publish_version_locked(actor: dict, version_id: str, payload: dict) -> dict:
    if actor.get("role") != "admin":
        raise GovernanceError("publish_forbidden", "只有内容发布责任人可以发布", 403)
    if not current_app.config.get("CONTENT_GOVERNANCE_PUBLISH_ENABLED", False):
        raise GovernanceError("content_publish_disabled", "当前环境未开启内容发布开关", 409)
    if payload.get("confirm_publish") is not True:
        raise GovernanceError("manual_confirmation_required", "发布需要独立人工确认", 409)
    version = get_version(version_id)
    if version["status"] != "approved":
        raise GovernanceError("content_not_approved", "内容未完成全部专业审核", 409)
    if str(payload.get("expected_hash") or "") != version["payload_hash"]:
        raise GovernanceError("content_hash_mismatch", "发布哈希与已审核版本不一致", 409)
    if version["dependency_impact"]["has_dependencies"] and payload.get("dependency_impact_confirmed") is not True:
        raise GovernanceError("dependency_confirmation_required", "内容存在依赖，发布前需要确认影响范围", 409, version["dependency_impact"])
    package = {
        "schema": "safehome.content-release.v1",
        "version_id": version_id,
        "content_type": version["content_type"],
        "item_id": version["item_id"],
        "payload_hash": version["payload_hash"],
        "metadata": version["metadata"],
        "released_at": now_iso(),
    }
    package["package_hash"] = _hash(package)
    release_id = new_id("cgrls")
    path = None
    old_bytes = None
    try:
        path, old_bytes = _replace_active_item(version["content_type"], version["item_id"], version["payload"])
        with get_connection() as conn:
            previous = conn.execute("SELECT id FROM content_governance_releases WHERE content_type = ? AND item_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1", (version["content_type"], version["item_id"])).fetchone()
            previous_id = previous["id"] if previous else None
            conn.execute("UPDATE content_governance_releases SET status = 'superseded' WHERE content_type = ? AND item_id = ? AND status = 'active'", (version["content_type"], version["item_id"]))
            conn.execute("INSERT INTO content_governance_releases (id, version_id, content_type, item_id, payload_hash, package_json, previous_release_id, release_reason, status, released_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)", (release_id, version_id, version["content_type"], version["item_id"], version["payload_hash"], json_dumps(package), previous_id, str(payload.get("release_reason") or "受控发布"), actor["id"], now_iso()))
            conn.execute("UPDATE content_governance_versions SET status = 'published', published_at = ?, updated_at = ? WHERE id = ?", (now_iso(), now_iso(), version_id))
            write_audit_log(conn, "content_version_published", actor["id"], "content_release", release_id, {"version_id": version_id, "package_hash": package["package_hash"], "previous_release_id": previous_id})
            conn.commit()
    except Exception:
        if path is not None:
            if old_bytes is None:
                path.unlink(missing_ok=True)
            else:
                restore = path.with_suffix(path.suffix + ".restore")
                restore.write_bytes(old_bytes)
                os.replace(restore, path)
        raise
    return {"release_id": release_id, "version_id": version_id, "package": package, "status": "active", "rollback_available": True}


def change_release_state(actor: dict, release_id: str, action: str, payload: dict) -> dict:
    with _release_lock():
        return _change_release_state_locked(actor, release_id, action, payload)


def _change_release_state_locked(actor: dict, release_id: str, action: str, payload: dict) -> dict:
    if actor.get("role") != "admin":
        raise GovernanceError("publish_forbidden", "只有内容发布责任人可以变更发布状态", 403)
    if payload.get("confirm_action") is not True:
        raise GovernanceError("manual_confirmation_required", "该操作需要独立人工确认", 409)
    with get_connection() as conn:
        release_row = conn.execute("SELECT * FROM content_governance_releases WHERE id = ?", (release_id,)).fetchone()
        if not release_row:
            raise GovernanceError("not_found", "发布记录不存在", 404)
    release = dict(release_row)
    version = get_version(release["version_id"])
    if action in {"pause", "retire"}:
        impact = dependency_impact(version["content_type"], version["item_id"])
        if impact["has_dependencies"] and payload.get("dependency_impact_confirmed") is not True:
            raise GovernanceError("dependency_confirmation_required", "暂停或退役前需要确认依赖影响", 409, impact)
        next_status = "paused" if action == "pause" else "retired"
        inactive_payload = version["payload"]
        if isinstance(inactive_payload, dict):
            inactive_payload = {**inactive_payload, "enabled": False, "enabled_for_user": False, "governance_status": next_status}
        path, old_bytes = _replace_active_item(version["content_type"], version["item_id"], inactive_payload)
        try:
            with get_connection() as conn:
                timestamp = now_iso()
                conn.execute("UPDATE content_governance_versions SET status = ?, updated_at = ?, retired_at = CASE WHEN ? THEN ? ELSE retired_at END WHERE id = ?", (next_status, timestamp, 1 if action == "retire" else 0, timestamp, version["id"]))
                conn.execute("UPDATE content_governance_releases SET status = ? WHERE id = ?", (next_status, release_id))
                write_audit_log(conn, f"content_release_{action}d", actor["id"], "content_release", release_id, {"version_id": version["id"], "impact_count": len(impact["impacts"])})
                conn.commit()
        except Exception:
            if old_bytes is None:
                path.unlink(missing_ok=True)
            else:
                restore_path = path.with_suffix(path.suffix + ".restore")
                restore_path.write_bytes(old_bytes)
                os.replace(restore_path, path)
            raise
        return {"release_id": release_id, "status": next_status, "dependency_impact": impact}
    if action == "restore":
        if release["status"] not in {"paused", "superseded"}:
            raise GovernanceError("invalid_content_transition", "只有暂停或已替代发布可以恢复", 409)
        package = json_loads(release["package_json"], {})
        package_hash = package.pop("package_hash", None)
        if not package_hash or package_hash != _hash(package) or release["payload_hash"] != version["payload_hash"]:
            raise GovernanceError("release_package_integrity_failed", "不可变发布包校验失败", 409)
        path, old_bytes = _replace_active_item(version["content_type"], version["item_id"], version["payload"])
        try:
            with get_connection() as conn:
                conn.execute("UPDATE content_governance_releases SET status = 'superseded' WHERE content_type = ? AND item_id = ? AND status = 'active'", (version["content_type"], version["item_id"]))
                conn.execute("UPDATE content_governance_releases SET status = 'active' WHERE id = ?", (release_id,))
                conn.execute("UPDATE content_governance_versions SET status = 'published', updated_at = ?, retired_at = NULL WHERE id = ?", (now_iso(), version["id"]))
                write_audit_log(conn, "content_release_restored", actor["id"], "content_release", release_id, {"version_id": version["id"], "payload_hash": version["payload_hash"]})
                conn.commit()
        except Exception:
            if old_bytes is None:
                path.unlink(missing_ok=True)
            else:
                restore_path = path.with_suffix(path.suffix + ".restore")
                restore_path.write_bytes(old_bytes)
                os.replace(restore_path, path)
            raise
        return {"release_id": release_id, "version_id": version["id"], "status": "active", "restored": True}
    raise GovernanceError("validation_error", "不支持的发布操作")


def run_synthetic_replay(actor: dict, cases: list[dict]) -> dict:
    if cases is None:
        fixture_path = current_app.config["CONTENT_DIR"] / "synthetic_content_replay_cases.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        if fixture.get("contains_real_data") is not False:
            raise GovernanceError("replay_fixture_privacy_invalid", "固定回放集必须明确标记不含真实数据", 409)
        cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases or len(cases) > 200:
        raise GovernanceError("validation_error", "cases 必须包含 1 至 200 个合成案例")
    results = []
    for index, case in enumerate(cases):
        text = str(case.get("text") or "")
        risk = check_text_risk(text, source="content_governance_replay")
        feedback = None if not risk["allow_auto_feedback"] else generate_feedback({"scene": "合成回放", "raw_text": text, "parent_emotion": case.get("emotion", ""), "behavior": case.get("behavior", "")})
        actual = {
            "risk_level": risk["risk_level"],
            "auto_feedback_allowed": risk["allow_auto_feedback"],
            "recommendation_allowed": risk["allow_recommended_training_cards"],
            "recommended_card_ids": (feedback or {}).get("recommended_card_ids", []),
            "boundary_notice_present": bool(risk.get("boundary_notice")),
        }
        expected = case.get("expected") if isinstance(case.get("expected"), dict) else {}
        mismatches = [{"field": field, "expected": value, "actual": actual.get(field)} for field, value in expected.items() if actual.get(field) != value]
        results.append({"case_id": str(case.get("case_id") or f"case-{index + 1}"), "passed": not mismatches, "actual": actual, "mismatches": mismatches})
    summary = {"total": len(results), "passed": sum(1 for item in results if item["passed"]), "failed": sum(1 for item in results if not item["passed"])}
    replay_hash = _hash({"cases": cases, "results": results})
    with get_connection() as conn:
        write_audit_log(conn, "content_synthetic_replay_run", actor["id"], "content_replay", replay_hash, {**summary, "contains_real_data": False})
        conn.commit()
    return {"summary": summary, "replay_hash": replay_hash, "results": results, "evidence_level": "synthetic_only", "contains_real_data": False}
