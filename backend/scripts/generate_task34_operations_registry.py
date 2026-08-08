"""Generate the Task 34 capability registry, governance cards and release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.artifact_integrity_service import artifact_sha256, artifact_size_bytes  # noqa: E402

VERSION = "2026-07-21-t34-v1"
CONTRACT_PATH = ROOT / "shared" / "contracts" / "api-contract.json"
REGISTRY_PATH = CONTENT / "operations_capability_registry.json"
CARDS_PATH = CONTENT / "operations_asset_cards.json"
KNOWLEDGE_PATH = CONTENT / "operations_knowledge_index.json"
MANIFEST_PATH = CONTENT / "operations_release_manifest.json"

TITLE_MAP = {
    "app": "运行健康与机器状态",
    "admin": "管理员数据总览",
    "ai_qa": "受控支持性问答沙盒",
    "assessments": "支持性测评",
    "auth": "身份与会话",
    "cards": "训练卡推荐与查看",
    "checkins": "练习打卡",
    "consent": "知情同意",
    "content_review": "内容版本与发布治理",
    "courses": "课程与练习节奏",
    "diaries": "情绪事件记录",
    "emotion_thermometer": "情绪温度记录",
    "family": "家庭关联",
    "feedback": "支持性反馈生成",
    "feedback_ledger": "反馈共同核对账本",
    "general_growth": "通用成长总览",
    "goals": "阶段目标",
    "journey": "今天的一小步",
    "messages": "站内消息",
    "notifications": "微信订阅通知",
    "offline_benchmarks": "离线情感与网络基准",
    "operations_governance": "内容数据模型运营治理",
    "parent_assessments": "家长支持性测评",
    "privacy": "隐私生命周期",
    "product_events": "最小化产品事件",
    "profile": "学生支持性画像",
    "programs": "项目与课程",
    "progress_summary": "成长时间线与摘要",
    "relationship_pilot_routes": "关系探索试点",
    "reliability": "可靠性与发布工程",
    "reports": "周度报告",
    "research_methodology": "研究方法冻结准备",
    "research_workspace": "研究工作台",
    "risk_review": "风险人工复核",
    "security_controls": "安全隐私与滥用控制",
    "showcase_access": "临时展示例外",
    "supervision": "人工支持",
    "text_analysis": "透明文本线索分析",
    "training_plan": "个性化练习计划",
    "ux_governance": "体验与无障碍治理",
}

FLAG_MAP = {
    "ai_qa": ["AI_QA_ENABLED", "AI_QA_SANDBOX_ENABLED"],
    "content_review": ["CONTENT_GOVERNANCE_ENFORCED", "CONTENT_GOVERNANCE_PUBLISH_ENABLED"],
    "notifications": ["WECHAT_SUBSCRIBE_SEND_ENABLED"],
    "offline_benchmarks": ["OFFLINE_BENCHMARK_ENABLED", "OFFLINE_EXTERNAL_INGEST_ENABLED"],
    "operations_governance": ["OPERATIONS_GOVERNANCE_WORKBENCH_ENABLED", "OPERATIONS_LOCAL_RELEASE_ENABLED", "OPERATIONS_PRODUCTION_RELEASE_ENABLED"],
    "reliability": ["RELIABILITY_WORKBENCH_ENABLED", "RELIABILITY_GRADUAL_RELEASE_ENABLED"],
    "research_methodology": ["RESEARCH_METHODOLOGY_WORKBENCH_ENABLED", "RESEARCH_OUTCOME_ANALYSIS_ALLOWED"],
    "security_controls": ["SECURITY_CONTROL_WORKBENCH_ENABLED"],
    "ux_governance": ["UX_GOVERNANCE_WORKBENCH_ENABLED"],
}

HIGH_SENSITIVITY = {"admin", "auth", "diaries", "family", "messages", "parent_assessments", "privacy", "profile", "relationship_pilot_routes", "research_workspace", "risk_review", "supervision"}
SYNTHETIC_ONLY = {"ai_qa", "offline_benchmarks", "research_methodology"}

ARTIFACTS = [
    ("content", "content/training_cards.json"),
    ("content", "content/courses.json"),
    ("content", "content/programs.json"),
    ("content", "content/assessment_worksheets.json"),
    ("content", "content/scales_catalog.json"),
    ("content", "content/consent.md"),
    ("content", "content/privacy.md"),
    ("rule", "content/feedback_rules.json"),
    ("rule", "content/assessment_training_map.json"),
    ("rule", "content/diary_training_map.json"),
    ("rule", "content/student_profile_rules.json"),
    ("rule", "content/task37_38_final_acceptance_policy.json"),
    ("rule", "content/readfeedback/parent_report_rules.json"),
    ("dictionary", "content/risk_keywords.json"),
    ("dictionary", "content/offline_benchmark_label_mapping.json"),
    ("model", "content/readfeedback/student_profile_model.json"),
    ("model", "content/readfeedback/student_profile_rules_kmeans.json"),
    ("model", "content/profiles/task12_micro_ysq_relationship_18_profile_model.json"),
    ("model", "content/profiles/task12_regulatory_focus_relationship_18_profile_model.json"),
    ("model", "content/profiles/task12_relationship_initiation_intention_action_profile_model.json"),
    ("prompt", "content/ai_qa_safety_responses.json"),
    ("prompt", "content/ai_qa_governance.json"),
    ("knowledge_index", "content/operations_knowledge_index.json"),
    ("governance_card", "content/operations_asset_cards.json"),
    ("capability_registry", "content/operations_capability_registry.json"),
]


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_hash(path: Path) -> str:
    return artifact_sha256(path)


def _module_key(module: str) -> str:
    return module.removeprefix("routes.")


def _owner_for(key: str) -> dict:
    if key in {"risk_review", "supervision", "profile", "parent_assessments", "relationship_pilot_routes"}:
        role = "psychology_supervisor"
    elif key in {"security_controls", "privacy", "auth", "admin"}:
        role = "security_privacy_owner"
    elif key in {"research_methodology", "offline_benchmarks", "research_workspace"}:
        role = "research_owner"
    elif key in {"content_review", "cards", "courses", "programs", "feedback"}:
        role = "content_owner"
    else:
        role = "engineering_owner"
    return {"accountable_role": role, "named_owner_status": "pending_human_assignment"}


def _governance_status(key: str) -> str:
    if key == "showcase_access":
        return "temporary_exception_formal_permission_blocked"
    if key == "ai_qa":
        return "synthetic_sandbox_only_participant_release_blocked"
    if key == "offline_benchmarks":
        return "synthetic_only_external_ingest_rights_blocked"
    if key == "research_methodology":
        return "engineering_ready_formal_freeze_pending"
    return "engineering_registered_release_approval_pending"


def build_capability_registry() -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict]] = {}
    for endpoint in contract["endpoints"]:
        grouped.setdefault(endpoint["module"], []).append(endpoint)
    capabilities = []
    for module, endpoints in sorted(grouped.items()):
        key = _module_key(module)
        operation_ids = sorted(item["operation_id"] for item in endpoints)
        roles = sorted({role for item in endpoints for role in item["access"]["roles"]})
        scopes = sorted({item["access"].get("object_scope", "unspecified") for item in endpoints})
        capabilities.append({
            "id": f"capability.{key}",
            "title": TITLE_MAP.get(key, key.replace("_", " ")),
            "intended_use": f"通过统一机器契约受控提供“{TITLE_MAP.get(key, key)}”能力；不得扩展为诊断、自动治疗决定或越权访问。",
            "owner": _owner_for(key),
            "dependencies": ["shared/contracts/api-contract.json", "content/security_privacy_abuse_registry.json"],
            "data": {"object_scopes": scopes, "sensitivity": "high" if key in HIGH_SENSITIVITY else "moderate_or_low", "participant_text_allowed_in_governance_records": False},
            "open_roles": roles,
            "feature_flags": FLAG_MAP.get(key, []),
            "version": contract["version"],
            "tests": [f"backend/tests (operation coverage: {len(operation_ids)})", "shared/contracts/api-contract.json"],
            "rollback": "关闭对应功能开关或隐藏入口；保留历史数据、审计和原核心链路。",
            "governance_status": _governance_status(key),
            "technical_implementation_complete": True,
            "production_release_approved": False,
            "operation_ids": operation_ids,
        })
    all_ids = [item for capability in capabilities for item in capability["operation_ids"]]
    return {
        "schema_version": "safehome.operations-capability-registry.v1",
        "version": VERSION,
        "status": "engineering_registry_complete_release_approval_pending",
        "generated_from_contract_version": contract["version"],
        "operation_count": len(all_ids),
        "capability_count": len(capabilities),
        "capabilities": capabilities,
        "temporary_showcase_exception": {"retained": True, "formal_permission_acceptance": False, "production_release_blocker": True},
        "treatment_assessment": {"synthetic_l0_allowed": True, "real_participant_release_allowed": False, "blocked_by": ["D01-D26", "ethics", "object_authorization", "human_responsibility_chain", "T34_release_approval"]},
        "external_gates": ["named_owners", "ethics", "privacy_security", "test_cloud", "wechat_developer_tool", "android_ios", "production_dual_control"],
        "production_release_approved": False,
        "boundary_notice": "工程登记与本地合成回放不等于人工、伦理、云、真机或生产发布批准。",
    }


def _normalized_dataset_cards() -> list[dict]:
    source = json.loads((CONTENT / "offline_benchmark_registry.json").read_text(encoding="utf-8"))
    cards = []
    for item in source.get("cards", []):
        cards.append({
            "id": item["id"],
            "card_type": "dataset",
            "source": {"url": item.get("source_url"), "version": item.get("source_version"), "population": item.get("population"), "context": item.get("context")},
            "license": {"name": item.get("license"), "rights_status": item.get("content_rights_status")},
            "metrics": {"status": "not_admitted_for_production_training", "sample_or_artifact": item.get("artifact_sha256")},
            "bias": [f"language={item.get('language')}", f"platform={item.get('platform')}", "公开或合成数据不能代表本项目参与者"],
            "failure_modes": ["许可或内容权利不足", "标签与本项目语义不一致", "把群体统计误用于个体判断"],
            "out_of_domain": ["临床诊断", "参与者或家庭质量推断", "未授权生产训练"],
            "admission_criteria": list(item.get("allowed_uses") or []),
            "disable_criteria": ["许可撤回", "敏感信息风险", "域错配", "人工权利审查未通过"],
            "current_status": item.get("ingest_status"),
        })
    return cards


def _rule_cards() -> list[dict]:
    definitions = [
        ("feedback_rules", "content/feedback_rules.json", "项目自研支持性反馈规则", ["synthetic_content_replay_cases.json"]),
        ("risk_keywords", "content/risk_keywords.json", "项目自研透明关键词分流", ["ai_qa_synthetic_safety_suite.json"]),
        ("assessment_training_map", "content/assessment_training_map.json", "项目自研测评推荐映射", ["recommendation replay"]),
        ("diary_training_map", "content/diary_training_map.json", "项目自研日记推荐映射", ["recommendation replay"]),
        ("student_profile_rules", "content/student_profile_rules.json", "项目自研学生支持性画像规则", ["profile tests"]),
        ("parent_report_rules", "content/readfeedback/parent_report_rules.json", "项目自研家长报告规则", ["parent report tests"]),
    ]
    return [{
        "id": item_id,
        "card_type": "rule",
        "source": {"path": path, "description": source},
        "license": {"name": "project-owned", "rights_status": "internal_use"},
        "metrics": {"status": "engineering_replay_required", "evidence": evidence},
        "bias": ["基于项目规则与有限合成案例", "关键词和映射可能漏掉表达差异"],
        "failure_modes": ["未知表达未覆盖", "推荐过度集中", "用户认为反馈不符合或不适"],
        "out_of_domain": ["诊断", "治疗决定", "危机评估替代", "家庭关系好坏判断"],
        "admission_criteria": ["固定合成回放通过", "无高严重度回归", "专业与伦理证据齐全"],
        "disable_criteria": ["高风险阻断失效", "诊断化文案", "严重不适集中", "越权或泄漏事件"],
        "current_status": "engineering_registered_human_review_pending",
    } for item_id, path, source, evidence in definitions]


def _model_cards() -> list[dict]:
    definitions = [
        ("student_profile_rules_v1", "content/readfeedback/student_profile_model.json", "学生支持性画像规则模型"),
        ("student_profile_kmeans_v1", "content/readfeedback/student_profile_rules_kmeans.json", "学生画像KMeans规则工件"),
        ("task12_micro_ysq_v1", "content/profiles/task12_micro_ysq_relationship_18_profile_model.json", "关系探索微型YSQ画像工件"),
        ("task12_regulatory_focus_v1", "content/profiles/task12_regulatory_focus_relationship_18_profile_model.json", "关系调节焦点画像工件"),
        ("task12_intention_action_v1", "content/profiles/task12_relationship_initiation_intention_action_profile_model.json", "关系行动意向画像工件"),
    ]
    return [{
        "id": item_id,
        "card_type": "model",
        "source": {"path": path, "description": description, "construction_data": "项目规则、量表结构与合成/历史工程工件；非临床训练集"},
        "license": {"name": "project-owned-model-artifact", "rights_status": "measurement_license_review_still_applies"},
        "metrics": {"status": "engineering_validation_only", "evidence": ["artifact hash", "fixed tests", "T30 measurement registry"]},
        "bias": ["样本代表性未建立", "语言和场景差异", "规则阈值可能产生边界不稳定"],
        "failure_modes": ["域外输入", "缺失题项", "量尺变换错误", "把阶段性线索误读为固定人格"],
        "out_of_domain": ["临床诊断", "人格定性", "自动治疗建议", "真实结果验证前的效果宣称"],
        "admission_criteria": ["工件哈希通过", "量尺和版本匹配", "固定案例通过", "T30人工方法/授权门禁通过"],
        "disable_criteria": ["工件哈希失败", "量尺错配", "严重文案回归", "越权/泄漏/不良事件"],
        "current_status": "engineering_validated_formal_admission_pending",
    } for item_id, path, description in definitions]


def build_asset_cards() -> dict:
    cards = _normalized_dataset_cards() + _rule_cards() + _model_cards()
    return {
        "schema_version": "safehome.operations-asset-cards.v1",
        "version": VERSION,
        "status": "engineering_cards_complete_human_admission_pending",
        "cards": cards,
        "production_admission_approved": False,
        "boundary_notice": "卡片记录工程证据、偏差和停用条件，不证明现实有效性，也不用于个体诊断。",
    }


def build_knowledge_index() -> dict:
    manifest = json.loads((CONTENT / "content_governance_manifest.json").read_text(encoding="utf-8"))
    entries = []
    for item in manifest.get("sources", []):
        path = CONTENT / str(item.get("filename") or "")
        if not path.is_file():
            continue
        entries.append({
            "source_file": item["filename"],
            "source_version": item.get("source_version"),
            "source_sha256": _file_hash(path),
            "content_types": item.get("content_types", []),
            "governance_status": item.get("governance_status"),
            "runtime_admission": "requires_t27_published_version_and_active_release",
            "raw_participant_text_included": False,
        })
    payload = {
        "schema_version": "safehome.operations-knowledge-index.v1",
        "version": VERSION,
        "entries": sorted(entries, key=lambda item: item["source_file"]),
        "draft_or_internal_notes_indexed": False,
        "participant_text_indexed": False,
        "production_release_approved": False,
    }
    payload["index_hash"] = _hash(payload)
    return payload


def build_release_manifest() -> dict:
    artifacts = []
    for artifact_type, relative in ARTIFACTS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        artifacts.append({"artifact_type": artifact_type, "path": relative.replace("\\", "/"), "sha256": _file_hash(path), "size_bytes": artifact_size_bytes(path)})
    payload = {
        "schema_version": "safehome.operations-release-manifest.v1",
        "version": VERSION,
        "artifacts": artifacts,
        "fixed_replay_suites": [
            {"path": "content/synthetic_content_replay_cases.json", "contains_real_data": False},
            {"path": "content/ai_qa_synthetic_safety_suite.json", "contains_real_data": False},
        ],
        "revision_policy": "never_edit_verified_package_create_new_version",
        "atomic_runtime_switch": True,
        "production_release_approved": False,
    }
    payload["manifest_hash"] = _hash(payload)
    return payload


def _render(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def generate() -> dict[Path, str]:
    registry = build_capability_registry()
    cards = build_asset_cards()
    base = {REGISTRY_PATH: _render(registry), CARDS_PATH: _render(cards)}
    for path, body in base.items():
        path.write_text(body, encoding="utf-8", newline="\n")
    knowledge = build_knowledge_index()
    base[KNOWLEDGE_PATH] = _render(knowledge)
    KNOWLEDGE_PATH.write_text(base[KNOWLEDGE_PATH], encoding="utf-8", newline="\n")
    base[MANIFEST_PATH] = _render(build_release_manifest())
    MANIFEST_PATH.write_text(base[MANIFEST_PATH], encoding="utf-8", newline="\n")
    return base


def check() -> int:
    expected_registry = _render(build_capability_registry())
    expected_cards = _render(build_asset_cards())
    expected_knowledge = _render(build_knowledge_index())
    expected = {REGISTRY_PATH: expected_registry, CARDS_PATH: expected_cards, KNOWLEDGE_PATH: expected_knowledge}
    for path, body in expected.items():
        if not path.exists() or path.read_text(encoding="utf-8") != body:
            print(f"stale: {path.relative_to(ROOT)}")
            return 1
    expected_manifest = _render(build_release_manifest())
    if not MANIFEST_PATH.exists() or MANIFEST_PATH.read_text(encoding="utf-8") != expected_manifest:
        print(f"stale: {MANIFEST_PATH.relative_to(ROOT)}")
        return 1
    print("Task 34 operations registry check passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    files = generate()
    print(json.dumps({"generated": [str(path.relative_to(ROOT)) for path in files]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
