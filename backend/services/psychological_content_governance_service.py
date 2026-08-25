"""Fail-closed psychological content version, rights and copy governance."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from flask import current_app

from database import load_content_json


SNAPSHOT_SCHEMA_VERSION = "safehome.assessment-content-snapshot.v1"
POLICY_FILENAME = "psychological_content_governance.json"


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_hash(value) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def describe_payload(content_type: str, item_id: str, payload, version: str | None) -> dict:
    return {
        "content_type": content_type,
        "item_id": str(item_id),
        "version": str(version or "unversioned"),
        "payload_hash": payload_hash(payload),
        "hash_algorithm": "sha256",
    }


def load_policy(content_dir: Path | None = None) -> dict:
    if content_dir is None:
        return load_content_json(POLICY_FILENAME)
    return json.loads((Path(content_dir) / POLICY_FILENAME).read_text(encoding="utf-8"))


def build_assessment_snapshot(
    worksheet: dict,
    *,
    result_summary: str,
    recommended_card_ids: list[str] | None = None,
    recommendation_rules: list[dict] | None = None,
    interpretation_payload: dict | None = None,
) -> dict:
    worksheet_payload = deepcopy(worksheet)
    worksheet_version = str(worksheet.get("source_version") or "unversioned")
    interpretation_payload = deepcopy(interpretation_payload) if interpretation_payload else {
        "result_summary": result_summary,
        "boundary_notice": worksheet.get("boundary_notice"),
        "result_disclaimer": worksheet.get("result_disclaimer"),
        "scoring": worksheet.get("scoring"),
        "scoring_notes": worksheet.get("scoring_notes") or {},
    }
    related_payloads = []
    card_ids = set(recommended_card_ids or [])
    if card_ids:
        cards_root = load_content_json("training_cards.json")
        card_version = cards_root.get("version") or "unversioned"
        for card in cards_root.get("cards", []):
            if card.get("id") in card_ids:
                related_payloads.append(
                    describe_payload("training_card", card["id"], card, card_version)
                )
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "worksheet": describe_payload(
            "worksheet", worksheet["id"], worksheet_payload, worksheet_version
        ),
        "worksheet_payload": worksheet_payload,
        "interpretation": describe_payload(
            "interpretation",
            worksheet["id"],
            interpretation_payload,
            f"{worksheet_version}::interpretation-v1",
        ),
        "interpretation_payload": interpretation_payload,
        "related_payloads": related_payloads,
        "recommendation": {
            "card_ids": list(recommended_card_ids or []),
            "rules": deepcopy(recommendation_rules or []),
        },
    }


def verify_snapshot(snapshot: dict, expected_hash: str | None) -> dict:
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        return {"valid": False, "reason": "snapshot_schema_invalid"}
    if not expected_hash or payload_hash(snapshot) != expected_hash:
        return {"valid": False, "reason": "snapshot_hash_mismatch"}
    worksheet = snapshot.get("worksheet") or {}
    worksheet_payload = snapshot.get("worksheet_payload")
    if worksheet.get("payload_hash") != payload_hash(worksheet_payload):
        return {"valid": False, "reason": "worksheet_payload_hash_mismatch"}
    interpretation = snapshot.get("interpretation") or {}
    interpretation_payload = snapshot.get("interpretation_payload")
    if interpretation.get("payload_hash") != payload_hash(interpretation_payload):
        return {"valid": False, "reason": "interpretation_payload_hash_mismatch"}
    return {"valid": True, "reason": "verified"}


def production_eligibility(worksheet: dict, rights: dict | None) -> dict:
    rights = rights or {}
    blockers = []
    required = {
        "source_file": "source_file_missing",
        "source_version": "source_version_missing",
        "questions": "questions_missing",
        "scoring": "scoring_missing",
        "boundary_notice": "boundary_notice_missing",
        "result_disclaimer": "result_disclaimer_missing",
    }
    for field, code in required.items():
        value = worksheet.get(field)
        if not value:
            blockers.append(code)
    if rights.get("copyright_status") not in {
        "owned",
        "licensed",
        "public_domain",
        "permission_recorded",
    }:
        blockers.append("copyright_not_approved")
    if rights.get("production_approval") != "approved":
        blockers.append("production_approval_missing")
    return {"eligible": not blockers, "blockers": blockers}


def _iter_payload_texts(content_dir: Path, policy: dict):
    for source in policy.get("governed_sources", []):
        payload = json.loads((content_dir / source["filename"]).read_text(encoding="utf-8"))
        root_version = payload.get("version") or "unversioned"
        for item in payload.get(source["list_field"], []):
            item_id = item.get(source["id_field"])
            version_field = source.get("version_field")
            version = root_version if version_field == "root.version" else item.get(version_field)
            yield source["content_type"], str(item_id), item, str(version or root_version)


def _long_payload_strings(value, minimum: int):
    found = set()
    if isinstance(value, dict):
        for nested in value.values():
            found.update(_long_payload_strings(nested, minimum))
    elif isinstance(value, list):
        for nested in value:
            found.update(_long_payload_strings(nested, minimum))
    elif isinstance(value, str) and len(value.strip()) >= minimum:
        found.add(value.strip())
    return found


def _user_copy_payload(content_type: str, payload: dict) -> dict:
    fields = {
        "worksheet": (
            "instructions",
            "questions",
            "scoring",
            "boundary_notice",
            "result_disclaimer",
        ),
        "training_card": (
            "title",
            "user_facing_title",
            "purpose",
            "steps",
            "reflection_questions",
            "stop_rules",
        ),
        "feedback_rule": (
            "supportive_feedback",
            "alternative_response",
            "boundary_note",
            "positive_examples",
            "negative_examples",
        ),
    }
    return {field: payload.get(field) for field in fields.get(content_type, ())}


def _participant_miniprogram_files(repo_root: Path) -> list[Path]:
    policy_path = repo_root / "config" / "rc0810" / "miniprogram_page_policy.json"
    page_policy = json.loads(policy_path.read_text(encoding="utf-8"))
    files = []
    for entry in page_policy.get("pages", []):
        if entry.get("classification") != "participant":
            continue
        base = repo_root / "apps" / "miniprogram" / entry["page"]
        files.extend(base.parent.glob(f"{base.name}.*"))
    return sorted({item for item in files if item.is_file()})


def _participant_copy_files(repo_root: Path) -> list[Path]:
    web_files = (repo_root / "apps" / "web" / "src").rglob("*.tsx")
    return sorted({*_participant_miniprogram_files(repo_root), *web_files})


def _frontend_files(repo_root: Path, extensions: set[str]) -> list[Path]:
    roots = [repo_root / "apps" / "miniprogram", repo_root / "apps" / "web" / "src"]
    return sorted(
        item
        for root in roots
        for item in root.rglob("*")
        if item.is_file() and item.suffix in extensions
    )


def _contains_unsafe_term(text: str, term: str) -> bool:
    start = 0
    safe_prefixes = ("不", "不能", "不可", "不得", "不会", "并非", "不能够")
    while True:
        index = text.find(term, start)
        if index < 0:
            return False
        prefix = text[max(0, index - 4) : index]
        if not any(prefix.endswith(item) for item in safe_prefixes):
            return True
        start = index + len(term)


def build_content_audit(repo_root: Path) -> dict:
    repo_root = Path(repo_root)
    content_dir = repo_root / "content"
    policy = load_policy(content_dir)
    governed = list(_iter_payload_texts(content_dir, policy))
    descriptors = [
        describe_payload(content_type, item_id, payload, version)
        for content_type, item_id, payload, version in governed
    ]

    scale_catalog = json.loads((content_dir / "scales_catalog.json").read_text(encoding="utf-8"))
    worksheets_root = json.loads(
        (content_dir / "assessment_worksheets.json").read_text(encoding="utf-8")
    )
    worksheets = {item.get("id"): item for item in worksheets_root.get("worksheets", [])}
    rights_overrides = policy.get("rights_overrides") or {}
    rights_list = []
    for scale in scale_catalog.get("scales", []):
        rights = rights_overrides.get(scale.get("id"), {})
        eligibility = production_eligibility(worksheets.get(scale.get("id"), {}), rights)
        rights_list.append(
            {
                "scale_id": scale.get("id"),
                "source_files": scale.get("source_files") or [],
                "source_type": scale.get("source_type") or "missing",
                "copyright_status": rights.get("copyright_status") or "pending_external_review",
                "audience": scale.get("audience") or "unverified",
                "purpose": "支持性测评、自我观察与练习推荐",
                "prohibited_interpretation": "不得用于诊断、人格定性、责任归因或疗效证明",
                "launch_status": scale.get("review_status") or "unreviewed",
                "production_eligible": eligibility["eligible"],
                "production_blockers": eligibility["blockers"],
            }
        )

    production_ids = []
    for worksheet_id in policy["production_manifest"].get("worksheet_ids", []):
        worksheet = worksheets.get(worksheet_id)
        rights = rights_overrides.get(worksheet_id)
        if worksheet and production_eligibility(worksheet, rights)["eligible"]:
            production_ids.append(worksheet_id)

    extensions = set(policy["copy_audit"]["frontend_extensions"])
    frontend_files = _frontend_files(repo_root, extensions)
    minimum = int(policy["copy_audit"]["min_payload_text_length"])
    payload_strings = set()
    for content_type, _item_id, payload, _version in governed:
        payload_strings.update(
            _long_payload_strings(_user_copy_payload(content_type, payload), minimum)
        )
    hardcoded = []
    allowlist = set(policy["copy_audit"].get("safe_fallback_allowlist") or [])
    for path in frontend_files:
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for literal in payload_strings:
            if literal in text and f"{relative}::{literal}" not in allowlist:
                hardcoded.append({"file": relative, "literal": literal})

    participant_findings = []
    internal_allowlist = policy["terminology"].get("internal_term_file_allowlist") or {}
    for path in _participant_copy_files(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for term in policy["terminology"]["participant_prohibited"]:
            if relative in set(internal_allowlist.get(term) or []):
                continue
            if _contains_unsafe_term(text, term):
                participant_findings.append({"file": relative, "term": term})

    return {
        "schema_version": "safehome.rc0810-f20-content-audit.v1",
        "policy_version": policy["version"],
        "governed_payloads": descriptors,
        "scale_rights_and_use": rights_list,
        "production_manifest": {
            "worksheet_ids": production_ids,
            "status": policy["production_manifest"]["status"],
        },
        "legacy_content_tracks": policy.get("legacy_content_tracks") or [],
        "external_gates": policy["external_gates"],
        "dual_track_audit": {"hardcoded_payload_matches": hardcoded},
        "copy_audit": {"participant_findings": participant_findings},
        "terminology": policy["terminology"],
    }


def production_legacy_profile_allowed() -> bool:
    policy = load_policy()
    track = next(
        (
            item
            for item in policy.get("legacy_content_tracks", [])
            if item.get("endpoint") == "/api/profile"
        ),
        None,
    )
    return bool(track and track.get("production_enabled") is True)


def production_worksheet_allowed(worksheet_id: str) -> bool:
    policy = load_policy()
    if worksheet_id not in policy["production_manifest"].get("worksheet_ids", []):
        return False
    worksheets = load_content_json("assessment_worksheets.json").get("worksheets", [])
    worksheet = next((item for item in worksheets if item.get("id") == worksheet_id), None)
    rights = (policy.get("rights_overrides") or {}).get(worksheet_id)
    return bool(worksheet and production_eligibility(worksheet, rights)["eligible"])
