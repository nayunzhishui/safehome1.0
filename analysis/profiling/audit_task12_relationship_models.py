"""Aggregate-only audit for the three Task 12 relationship profile models.

The audit never emits participant rows. It checks psychometric summaries,
bootstrap stability, GMM posterior clarity and the agreement between the fitted
GMM assignment and the current online nearest-centre approximation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import sklearn
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NPZ = PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "private" / "item_matrices.npz"
DEFAULT_MODEL_DIR = PROJECT_ROOT / "content" / "profiles"
DEFAULT_VALIDATION = PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "dimension_validation_summary.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "model_audit_summary.json"
RANDOM_SEED = 20260710

MODEL_KEYS = {
    "regulatory_focus": "regulatory_focus_relationship_18",
    "micro_ysq": "micro_ysq_relationship_18",
    "relationship": "relationship_initiation_intention_action",
}
RELIABILITY_GROUPS = {
    "regulatory_focus": {
        "PROM": ["Q3", "Q5", "Q6", "Q8", "Q12", "Q14", "Q16", "Q17", "Q18"],
        "PREV": ["Q1", "Q2", "Q4", "Q7", "Q9", "Q10", "Q11", "Q13", "Q15"],
    },
    "micro_ysq": {"EMS18": [f"YSQ{index}" for index in range(1, 19)]},
    "relationship": {
        "SN": [f"SN{index}" for index in range(1, 5)],
        "PBC6": [f"PBC{index}" for index in range(1, 7)],
        "BI": [f"BI{index}" for index in range(1, 7)],
        "RAP": [f"RAP{index}" for index in range(1, 6)],
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _alpha(matrix: np.ndarray) -> float | None:
    if matrix.ndim != 2 or matrix.shape[1] < 2:
        return None
    total_variance = matrix.sum(axis=1).var(ddof=1)
    if total_variance <= 0:
        return None
    item_variance = matrix.var(axis=0, ddof=1).sum()
    count = matrix.shape[1]
    return round(float(count / (count - 1) * (1 - item_variance / total_variance)), 3)


def _load_models(model_dir: Path) -> dict[str, dict]:
    models = {}
    for path in model_dir.glob("task12_*_profile_model.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        models[str(payload["scale_id"])] = {**payload, "_path": path}
    return models


def _bootstrap_stability(
    matrix: np.ndarray,
    baseline_labels: np.ndarray,
    k: int,
    iterations: int,
    rng: np.random.Generator,
) -> list[float]:
    scores = []
    for iteration in range(iterations):
        sample = rng.integers(0, len(matrix), len(matrix))
        scaler = StandardScaler().fit(matrix[sample])
        sampled = scaler.transform(matrix[sample])
        full = scaler.transform(matrix)
        candidate = GaussianMixture(
            n_components=k,
            covariance_type="diag",
            n_init=3,
            max_iter=500,
            random_state=1000 + iteration,
        ).fit(sampled)
        scores.append(float(adjusted_rand_score(baseline_labels, candidate.predict(full))))
    return scores


def audit_models(
    npz_path: Path = DEFAULT_NPZ,
    model_dir: Path = DEFAULT_MODEL_DIR,
    validation_path: Path = DEFAULT_VALIDATION,
    bootstrap_iterations: int = 50,
) -> dict:
    matrices = np.load(npz_path)
    models = _load_models(model_dir)
    rng = np.random.default_rng(RANDOM_SEED)
    audits = []

    for key, scale_id in MODEL_KEYS.items():
        matrix = np.asarray(matrices[key], dtype=float)
        columns = [str(value) for value in matrices[f"{key}_columns"]]
        column_index = {column: index for index, column in enumerate(columns)}
        model = models[scale_id]
        chosen_k = int(model["chosen_k"])
        scaler = StandardScaler().fit(matrix)
        standardized = scaler.transform(matrix)
        fitted = GaussianMixture(
            n_components=chosen_k,
            covariance_type="diag",
            n_init=5,
            max_iter=500,
            random_state=RANDOM_SEED,
        ).fit(standardized)
        gmm_labels = fitted.predict(standardized)
        posterior = fitted.predict_proba(standardized).max(axis=1)
        euclidean_labels = np.argmin(
            ((standardized[:, None, :] - fitted.means_[None, :, :]) ** 2).sum(axis=2),
            axis=1,
        )
        bootstrap_scores = _bootstrap_stability(
            matrix,
            gmm_labels,
            chosen_k,
            bootstrap_iterations,
            rng,
        )
        reliability = {}
        for name, group_columns in RELIABILITY_GROUPS[key].items():
            indices = [column_index[column] for column in group_columns]
            reliability[name] = _alpha(matrix[:, indices])
        selected_metrics = next(
            (
                row
                for row in model.get("model_selection", [])
                if row.get("method") == model.get("selected_method") and int(row.get("k")) == chosen_k
            ),
            {},
        )
        names = [str(cluster.get("profile_name") or "") for cluster in model.get("clusters", [])]
        audits.append(
            {
                "scale_id": scale_id,
                "n_cases": int(matrix.shape[0]),
                "n_features": int(matrix.shape[1]),
                "selected_method": model.get("selected_method"),
                "chosen_k": chosen_k,
                "selected_metrics": selected_metrics,
                "pca_explained_ratio_sum": round(float(sum(model.get("pca", {}).get("explained_ratio", []))), 3),
                "reliability_alpha": reliability,
                "mean_max_posterior": round(float(posterior.mean()), 3),
                "posterior_below_0_60_ratio": round(float((posterior < 0.60).mean()), 3),
                "posterior_below_0_80_ratio": round(float((posterior < 0.80).mean()), 3),
                "online_euclidean_vs_gmm_agreement": round(float((euclidean_labels == gmm_labels).mean()), 3),
                "bootstrap_ari": {
                    "iterations": bootstrap_iterations,
                    "median": round(float(np.median(bootstrap_scores)), 3),
                    "p10": round(float(np.quantile(bootstrap_scores, 0.10)), 3),
                    "minimum": round(float(np.min(bootstrap_scores)), 3),
                },
                "duplicate_profile_names": sorted({name for name in names if names.count(name) > 1}),
                "mean_item_floor_ratio": round(
                    float(np.mean([(matrix[:, index] == matrix[:, index].min()).mean() for index in range(matrix.shape[1])])),
                    3,
                ),
                "mean_item_ceiling_ratio": round(
                    float(np.mean([(matrix[:, index] == matrix[:, index].max()).mean() for index in range(matrix.shape[1])])),
                    3,
                ),
                "model_artifact_sha256": _sha256(model["_path"]),
            }
        )

    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    return {
        "schema_version": "task12-relationship-model-audit-v1",
        "raw_text_included": False,
        "participant_rows_included": False,
        "audit_scope": "aggregate_only_exploratory_review",
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "random_seed": RANDOM_SEED,
        "input_hashes": {
            "item_matrices_npz": _sha256(npz_path),
            "dimension_validation_summary": _sha256(validation_path),
        },
        "source_conflicts": validation.get("source_conflicts", []),
        "models": audits,
        "interpretation_notes": [
            "bootstrap_ari重抽训练样本并在完整样本上预测，衡量的是样本扰动稳定性；与仅改变初始化种子的ARI不同。",
            "online_euclidean_vs_gmm_agreement低于1表示当前线上最近中心规则与离线GMM分类并不完全一致。",
            "所有结果仅用于模型审查，不构成个体诊断、人格分类或效果结论。",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--npz", type=Path, default=DEFAULT_NPZ)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bootstrap-iterations", type=int, default=50)
    args = parser.parse_args()
    result = audit_models(
        args.npz,
        args.model_dir,
        args.validation,
        bootstrap_iterations=max(10, args.bootstrap_iterations),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "model_count": len(result["models"]), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
