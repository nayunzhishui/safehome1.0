"""Freeze and validate the 108 documents reviewed for SafeHome task 38."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"D:\codex\workspace\the-learn-of-py")
MANUAL_PATH = Path(
    r"D:\桌面\Desktop\治疗性评估全面学习手册_内容优化版3.0_20260726.docx"
)
OUTPUT_PATH = ROOT / "content" / "task38_source_registry.json"
ALLOWED_EXTENSIONS = {".docx", ".md", ".html", ".json"}


class SourceRegistryError(ValueError):
    """Raised when source provenance is missing, duplicated or malformed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_metadata(path: Path, *, index: int, manual: bool) -> dict[str, Any]:
    if manual:
        locator = str(path)
        source_role = "therapeutic_assessment_translation_source"
        evidence_tier = "method_translation_source"
        authority = "source_or_expert_review_required"
        visual_status = "pending_visual_render_after_libreoffice_repair"
    else:
        relative = path.relative_to(SOURCE_ROOT).as_posix()
        locator = f"the-learn-of-py://{relative}"
        archived_or_record = any(
            marker in relative
            for marker in ("/_存档/", "/learning-records/", "/lab/")
        )
        if archived_or_record:
            source_role = "project_learning_record"
            evidence_tier = "project_learning_record"
        else:
            source_role = "engineering_reference"
            evidence_tier = "engineering_reference"
        authority = "engineering_reference_not_clinical_evidence"
        visual_status = (
            "pending_visual_render_after_libreoffice_repair"
            if path.suffix.lower() == ".docx"
            else "text_structure_review_complete"
        )
    return {
        "id": f"T38-SRC-{index:04d}",
        "title": path.stem,
        "source_locator": locator,
        "extension": path.suffix.lower(),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "source_role": source_role,
        "evidence_tier": evidence_tier,
        "product_rule_authority": authority,
        "structured_read_status": "complete_2026_07_27",
        "visual_review_status": visual_status,
        "license_or_use_boundary": "owner_or_expert_review_required_before_redistribution",
        "raw_content_embedded_in_registry": False,
    }


def build_registry() -> dict[str, Any]:
    if not SOURCE_ROOT.is_dir():
        raise SourceRegistryError(f"资料目录不存在：{SOURCE_ROOT}")
    if not MANUAL_PATH.is_file():
        raise SourceRegistryError(f"治疗性评估手册不存在：{MANUAL_PATH}")
    files = sorted(
        (
            path
            for path in SOURCE_ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
        ),
        key=lambda path: path.relative_to(SOURCE_ROOT).as_posix().casefold(),
    )
    if len(files) != 107:
        raise SourceRegistryError(f"the-learn-of-py文档数量应为107，实际为{len(files)}。")
    sources = [
        _source_metadata(path, index=index, manual=False)
        for index, path in enumerate(files, start=1)
    ]
    sources.append(
        _source_metadata(MANUAL_PATH, index=len(sources) + 1, manual=True)
    )
    extension_counts = Counter(source["extension"] for source in sources)
    return {
        "schema": "safehome.task38.source-registry.v1",
        "version": "2026-07-27-f00-v1",
        "generated_on": date.today().isoformat(),
        "status": "structured_read_complete_external_expert_and_visual_gates_pending",
        "source_count": len(sources),
        "extension_counts": dict(sorted(extension_counts.items())),
        "source_roots": [
            {
                "id": "engineering_learning_materials",
                "locator": str(SOURCE_ROOT),
                "expected_files": 107,
            },
            {
                "id": "therapeutic_assessment_manual_v3",
                "locator": str(MANUAL_PATH),
                "expected_files": 1,
            },
        ],
        "rules": {
            "github_or_engineering_material_counts_as_clinical_evidence": False,
            "structured_read_counts_as_visual_review": False,
            "source_registration_counts_as_expert_approval": False,
            "product_rule_requires_source_or_design_inference_label": True,
            "raw_document_content_embedded": False,
        },
        "sources": sources,
    }


def validate_registry(
    payload: dict[str, Any], *, reverify_external: bool
) -> dict[str, Any]:
    if payload.get("schema") != "safehome.task38.source-registry.v1":
        raise SourceRegistryError("来源注册表schema不兼容。")
    sources = payload.get("sources", [])
    if payload.get("source_count") != 108 or len(sources) != 108:
        raise SourceRegistryError("来源注册表必须固定包含108份资料。")
    if payload.get("extension_counts") != {
        ".docx": 77,
        ".html": 4,
        ".json": 2,
        ".md": 25,
    }:
        raise SourceRegistryError("来源扩展名统计不符合审读事实。")
    ids = [source.get("id") for source in sources]
    hashes = [source.get("sha256") for source in sources]
    if len(set(ids)) != 108 or len(set(hashes)) != 108:
        raise SourceRegistryError("来源ID或内容哈希不唯一。")
    for source in sources:
        if len(str(source.get("sha256", ""))) != 64:
            raise SourceRegistryError(f"{source.get('id')}缺少有效SHA-256。")
        if source.get("raw_content_embedded_in_registry") is not False:
            raise SourceRegistryError("来源注册表不得嵌入原始文档正文。")
        if source.get("product_rule_authority") not in {
            "source_or_expert_review_required",
            "engineering_reference_not_clinical_evidence",
        }:
            raise SourceRegistryError("产品规则证据等级不明确。")

    external_reverified = False
    if reverify_external and SOURCE_ROOT.is_dir() and MANUAL_PATH.is_file():
        rebuilt = build_registry()
        expected = {
            source["source_locator"]: source["sha256"] for source in sources
        }
        actual = {
            source["source_locator"]: source["sha256"]
            for source in rebuilt["sources"]
        }
        if expected != actual:
            raise SourceRegistryError("外部资料内容与冻结注册表不一致。")
        external_reverified = True
    return {
        "valid": True,
        "source_count": len(sources),
        "external_files_reverified": external_reverified,
        "raw_content_embedded": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成或验证任务38资料来源注册表")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.write:
            payload = build_registry()
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = validate_registry(payload, reverify_external=True)
            result["path"] = str(OUTPUT_PATH)
        else:
            try:
                payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SourceRegistryError("冻结来源注册表缺失或损坏。") from exc
            result = validate_registry(payload, reverify_external=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except SourceRegistryError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
