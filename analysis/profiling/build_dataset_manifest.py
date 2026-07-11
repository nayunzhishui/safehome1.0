"""Build a privacy-minimized manifest for repository profile models."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "outputs" / "profile_dataset_manifest.json"


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contains_row_level_points(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"training_points", "row_points", "participant_rows", "raw_rows"} and item:
                return True
            if _contains_row_level_points(item):
                return True
    elif isinstance(value, list):
        return any(_contains_row_level_points(item) for item in value)
    return False


def _source_summary(path: Path) -> str:
    if path.parent.name == "readfeedback":
        return "学生画像聚合训练数据"
    if path.name.startswith("task12_"):
        return "任务十二关系量表清洗数据"
    return "既往研究聚合数据"


def _source_evidence_hash(payload: dict) -> str:
    evidence = {
        "source_dataset": payload.get("source_dataset"),
        "research_dir": payload.get("research_dir"),
        "source_file": payload.get("source_file"),
        "training_source_hashes": payload.get("training_source_hashes"),
        "worksheet_id": payload.get("worksheet_id"),
        "scale_id": payload.get("scale_id"),
    }
    return _canonical_hash(evidence)


def _model_item(path: Path, payload: dict) -> dict:
    stored_artifact_hash = str(payload.get("artifact_hash") or "").strip()
    model_id = "student_profile_model" if path.parent.name == "readfeedback" else path.stem
    features = payload.get("features") if isinstance(payload.get("features"), list) else []
    clusters = payload.get("clusters") if isinstance(payload.get("clusters"), list) else []
    n_features = payload.get("n_features") or len(features) or payload.get("n_columns")
    return {
        "model_id": model_id,
        "model_type": payload.get("selected_method") or payload.get("model_type") or "kmeans",
        "admission_status": payload.get("admission_status") or "legacy_review_required",
        "interpretation_approval_status": payload.get("interpretation_approval_status") or "manual_review_required",
        "sample_count": payload.get("n_cases") or payload.get("sample_size") or payload.get("n_samples"),
        "feature_count": n_features,
        "cluster_count": payload.get("chosen_k") or len(clusters),
        "source_summary": _source_summary(path),
        "source_hash": _source_evidence_hash(payload),
        "artifact_hash": stored_artifact_hash or _canonical_hash(payload),
        "artifact_hash_kind": "governance" if stored_artifact_hash else "repository_file_derived",
        "contains_row_level_points": _contains_row_level_points(payload),
        "model_created_at": payload.get("created_at"),
        "human_validation_status": payload.get("production_approval_status")
        or payload.get("cross_validation_status")
        or "manual_review_required",
    }


def model_paths(root: Path = ROOT) -> list[Path]:
    paths = sorted((root / "content" / "profiles").glob("*.json"))
    student_model = root / "content" / "readfeedback" / "student_profile_model.json"
    if student_model.exists():
        paths.append(student_model)
    return paths


def build_manifest(root: Path = ROOT) -> dict:
    items = []
    for path in model_paths(root):
        payload = json.loads(path.read_text(encoding="utf-8"))
        items.append(_model_item(path, payload))
    created_values = sorted(str(item["model_created_at"]) for item in items if item.get("model_created_at"))
    return {
        "schema_version": "2026.07-profile-dataset-manifest-v1",
        "generated_at": created_values[-1] if created_values else "repository_snapshot",
        "model_count": len(items),
        "privacy": {
            "row_level_data_included": False,
            "absolute_paths_included": False,
            "stable_participant_identifiers_included": False,
            "source_names_replaced_by_aggregate_summary": True,
        },
        "models": sorted(items, key=lambda item: item["model_id"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成不含逐行数据和绝对路径的画像数据来源清单")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    manifest = build_manifest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"profile dataset manifest: {manifest['model_count']} models -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
