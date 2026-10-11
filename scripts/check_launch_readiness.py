"""Read-only launch inventory and deterministic mini-program privacy text sync."""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_COPY = ROOT / "apps/miniprogram/utils/privacy-policy.json"

def privacy_notice(text: str) -> dict:
    sections = []
    current = None
    title = "隐私政策"
    version = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            continue
        if line.startswith("版本："):
            version = line[3:].strip()
        if line.startswith("## "):
            current = {"title": line[3:].strip(), "items": []}
            sections.append(current)
        else:
            if current is None:
                current = {"title": "版本与适用范围", "items": []}
                sections.append(current)
            current["items"].append(re.sub(r"^[-*]\s+", "", line))
    return {"kicker": "隐私说明", "title": title, "version": version,
            "status": "draft" if "[待填写：" in text else "text_complete",
            "sections": sections}

def _read(root: Path, filename: str):
    return json.loads((root / "content" / filename).read_text(encoding="utf-8"))

def report(root: Path = ROOT) -> dict:
    # Import existing pure eligibility logic; never create an app or connect a DB.
    sys.path.insert(0, str(ROOT / "backend"))
    from services.psychological_content_governance_service import production_eligibility
    from services.card_service import APPROVED_REVIEW_STATUSES
    policy = _read(root, "psychological_content_governance.json")
    allowed = set(policy["production_manifest"].get("worksheet_ids", []))
    rights = policy.get("rights_overrides", {})
    worksheets = []
    for row in _read(root, "assessment_worksheets.json").get("worksheets", []):
        reasons = production_eligibility(row, rights.get(row["id"]))["blockers"]
        if row["id"] not in allowed:
            reasons = ["not_in_production_manifest", *reasons]
        if not row.get("enabled_for_user", True):
            reasons = [*reasons, "disabled"]
        worksheets.append({"id": row["id"], "title": row.get("display_title", row["id"]),
                           "eligible_in_source": not reasons, "blockers": reasons})
    cards = []
    for row in _read(root, "training_cards.json").get("cards", []):
        reasons = []
        if not row.get("enabled", True): reasons.append("disabled")
        if row.get("review_status") not in APPROVED_REVIEW_STATUSES: reasons.append("production_review_missing")
        cards.append({"id": row["id"], "title": row.get("title", row["id"]),
                      "eligible_in_source": not reasons, "blockers": reasons})
    programs = []
    for row in _read(root, "programs.json").get("programs", []):
        reasons = []
        if not row.get("enabled", True): reasons.append("disabled")
        if row.get("review_status") != "pilot_approved": reasons.append("program_review_pending")
        for role in ("research", "psychology", "ethics"):
            approval = row.get("approval", {}).get(role, {})
            if approval.get("status") != "approved" or not all(approval.get(k) for k in ("reviewer", "reviewed_at", "evidence_path")):
                reasons.append(role + "_evidence_missing")
        programs.append({"id": row["id"], "title": row.get("title", row["id"]),
                         "eligible_in_source": not reasons, "blockers": reasons})
    text = (root / "content/privacy.md").read_text(encoding="utf-8")
    pending = sorted(set(re.findall(r"\[待填写：[^\]]+\]", text)))
    retention = _read(root, "privacy_retention_policy.json")
    copy_path = root / "apps/miniprogram/utils/privacy-policy.json"
    synchronized = copy_path.exists() and json.loads(copy_path.read_text(encoding="utf-8")) == privacy_notice(text)
    groups = {"worksheets": worksheets, "training_cards": cards, "programs": programs}
    summary = {key: {"total": len(rows), "eligible_in_source": sum(row["eligible_in_source"] for row in rows)} for key, rows in groups.items()}
    ready = not pending and synchronized and retention.get("approval_status") == "approved" and all(x["eligible_in_source"] for x in summary.values())
    return {"status": "source_ready_requires_human_release_review" if ready else "pending_required_evidence",
            "note": "仅列正式批准清单，不包含TEMPORARY_*临时开放；不连接生产，不验证真人资质，也不授予发布批准。",
            "summary": summary, "privacy_pending_fields": pending,
            "privacy_retention_approval": retention.get("approval_status"),
            "privacy_copy_synchronized": synchronized, "items": groups}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync-privacy", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.sync_privacy:
        POLICY_COPY.parent.mkdir(parents=True, exist_ok=True)
        POLICY_COPY.write_text(json.dumps(privacy_notice((ROOT / "content/privacy.md").read_text(encoding="utf-8")), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("隐私全文已同步到小程序；同步不代表正式文本或内容已获批准。")
        return 0
    result = report()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for name, counts in result["summary"].items():
            print(f"{name}: 正式批准清单（不含临时开关） {counts['eligible_in_source']} / {counts['total']}")
        print("隐私副本同步:", result["privacy_copy_synchronized"])
        print("隐私待填字段:", "、".join(result["privacy_pending_fields"]) or "无占位字段（仍需负责人审核）")
        print("保存策略:", result["privacy_retention_approval"])
        print("结果:", result["status"], "；", result["note"])
    return 0 if result["status"].startswith("source_ready") else 2

if __name__ == "__main__":
    raise SystemExit(main())
