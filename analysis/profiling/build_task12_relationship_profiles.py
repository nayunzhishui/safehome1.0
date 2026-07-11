"""Compare GMM/KMeans and build three aggregate Task 12 relationship profile models."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NPZ = PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "private" / "item_matrices.npz"
DEFAULT_MAPPING = PROJECT_ROOT / "outputs" / "task12_relationship_profiles" / "item_mapping_preview.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "content" / "profiles"
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "02_专项进度与验收" / "任务十二数据1聚类方法选择报告.md"
RANDOM_SEED = 20260710
BOUNDARY = "画像只表示本次题项组合与既往样本聚合中心的相对接近程度，不构成诊断、筛查、人格标签、关系能力评价或疗效证明。"

SPECS = {
    "regulatory_focus": {
        "scale_id": "regulatory_focus_relationship_18",
        "name": "关系情境中的行动关注方式",
        "cards": ["student_emotion_naming", "cbt_auto_thought_student", "self_support_statement"],
        "training_range": [1, 5],
        "worksheet_range": [1, 7],
    },
    "micro_ysq": {
        "scale_id": "micro_ysq_relationship_18",
        "name": "关系中的常见担心与期待",
        "cards": ["self_support_statement", "scs_mindful_moment", "student_two_thoughts"],
        "training_range": [1, 6],
        "worksheet_range": [1, 6],
    },
    "relationship": {
        "scale_id": "relationship_initiation_intention_action",
        "name": "关系主动性：想法、意愿与行动",
        "cards": ["one_open_question", "erq_expression_gentle", "self_support_statement"],
        "training_range": [1, 5],
        "worksheet_range": [1, 5],
    },
}


def _rounded(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def _readability(centers: np.ndarray) -> float:
    if len(centers) < 2:
        return 0.0
    distances = [float(np.linalg.norm(left - right)) for left, right in combinations(centers, 2)]
    return _rounded(sum(distance >= 0.75 for distance in distances) / len(distances))


def _fit_labels(matrix: np.ndarray, method: str, k: int, seed: int):
    if method == "gaussian_mixture":
        model = GaussianMixture(n_components=k, covariance_type="diag", n_init=5, max_iter=500, random_state=seed)
        labels = model.fit_predict(matrix)
    else:
        model = KMeans(n_clusters=k, n_init=20, random_state=seed)
        labels = model.fit_predict(matrix)
    return model, labels


def compare_methods(matrix: np.ndarray, k_values=range(2, 7), stability_seeds=(11, 23, 37, 53, 71)) -> list[dict]:
    standardized = StandardScaler().fit_transform(matrix)
    rows = []
    for method in ("gaussian_mixture", "kmeans"):
        for k in k_values:
            model, labels = _fit_labels(standardized, method, k, RANDOM_SEED)
            counts = np.bincount(labels, minlength=k)
            stability = []
            for seed in stability_seeds:
                _candidate, candidate_labels = _fit_labels(standardized, method, k, seed)
                stability.append(adjusted_rand_score(labels, candidate_labels))
            centers = model.means_ if method == "gaussian_mixture" else model.cluster_centers_
            row = {
                "method": method,
                "k": k,
                "bic": _rounded(model.bic(standardized), 2) if method == "gaussian_mixture" else None,
                "aic": _rounded(model.aic(standardized), 2) if method == "gaussian_mixture" else None,
                "silhouette": _rounded(silhouette_score(standardized, labels)),
                "min_cluster_ratio": _rounded(counts.min() / len(labels)),
                "stability": _rounded(np.mean(stability)),
                "readability": _readability(centers),
            }
            rows.append(row)
    return rows


def _choose_method(rows: list[dict]) -> tuple[str, int, str]:
    gmm = [
        row
        for row in rows
        if row["method"] == "gaussian_mixture"
        and row["min_cluster_ratio"] >= 0.08
        and row["stability"] >= 0.6
        and row["silhouette"] >= 0.08
    ]
    if gmm:
        best = min(gmm, key=lambda row: (row["bic"], -row["silhouette"], row["k"]))
        return "gaussian_mixture", best["k"], "GMM同时满足最小簇比例、稳定性和最低分离度门槛，并在合格候选中BIC最低；保留KMeans作对照。"
    kmeans = [row for row in rows if row["method"] == "kmeans" and row["min_cluster_ratio"] >= 0.08]
    best = max(kmeans, key=lambda row: (row["silhouette"], row["stability"], -row["k"]))
    return "kmeans", best["k"], "GMM未同时达到最小簇比例和稳定性门槛，降级为轮廓系数更优的KMeans。"


def _mapping(mapping_path: Path) -> dict[str, dict]:
    result = {}
    with mapping_path.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            result[f'{row["scale_id"]}:{row["abbreviation"]}'] = row
    return result


def _dimension_values(key: str, matrix: np.ndarray, columns: list[str]) -> tuple[list[str], np.ndarray]:
    index = {name: position for position, name in enumerate(columns)}
    if key == "regulatory_focus":
        promotion = [index[f"Q{i}"] for i in [3, 5, 6, 8, 12, 14, 16, 17, 18]]
        prevention = [index[f"Q{i}"] for i in [1, 2, 4, 7, 9, 10, 11, 13, 15]]
        prom = matrix[:, promotion].mean(axis=1)
        prev = matrix[:, prevention].mean(axis=1)
        return ["PROM", "PREV", "RFD"], np.column_stack([prom, prev, prom - prev])
    if key == "micro_ysq":
        return ["EMS_M"], matrix.mean(axis=1, keepdims=True)
    benefit = np.mean([matrix[:, index[f"a{i}"]] * matrix[:, index[f"b{i}"]] for i in range(1, 4)], axis=0)
    rejection = matrix[:, index["a4"]] * matrix[:, index["b4"]]
    authenticity_threat = matrix[:, index["a5"]] * matrix[:, index["b5"]]
    threat = (rejection + authenticity_threat) / 2
    protect = ((6 - matrix[:, index["a5"]]) + matrix[:, index["b5"]]) / 2
    means = [matrix[:, [index[name] for name in columns if name.startswith(prefix)]].mean(axis=1) for prefix in ["SN", "PBC", "BI", "RAP"]]
    return ["BENEFIT", "REJ_THREAT", "AUTH_THREAT", "THREAT", "AUTH_PROTECT", "SN", "PBC", "BI", "RAP"], np.column_stack([benefit, rejection, authenticity_threat, threat, protect, *means])


def _profile_name(key: str, dimension_names: list[str], values_z: dict[str, float]) -> str:
    if key == "regulatory_focus":
        if values_z["RFD"] >= 0.35:
            return "成长目标较突出、可继续校准安全感的阶段"
        if values_z["RFD"] <= -0.35:
            return "安全顾虑较突出、可尝试小步探索的阶段"
        return "成长与安全关注相对平衡的观察阶段"
    if key == "micro_ysq":
        if values_z["EMS_M"] >= 0.35:
            return "多项关系担心值得温和梳理的阶段"
        if values_z["EMS_M"] <= -0.35:
            return "关系担心线索相对较少的观察阶段"
        return "部分关系担心正在浮现的观察阶段"
    if values_z["BI"] >= 0.25 and values_z["RAP"] <= -0.25:
        return "行动意愿已出现、实际尝试仍在起步的阶段"
    if values_z["THREAT"] >= 0.3 and values_z["RAP"] <= 0:
        return "想靠近、也在保护自己的探索阶段"
    if values_z["PBC"] >= 0.25 and values_z["RAP"] >= 0.25:
        return "关系行动探索相对活跃的阶段"
    return "关系方向与行动节奏仍在观察的阶段"


def _questions(key: str, dimension_z: dict[str, float]) -> list[str]:
    if key == "regulatory_focus":
        if dimension_z.get("RFD", 0) >= 0.35:
            return ["成长目标更突出时，你希望怎样同时照顾安全感？", "哪一个小行动既能靠近目标，也不会让压力一下变大？"]
        if dimension_z.get("RFD", 0) <= -0.35:
            return ["安全顾虑出现时，你最想先保护什么？", "什么支持能让你愿意尝试一个风险较低的小行动？"]
        return ["成长期待和安全顾虑同时出现时，你通常先回应哪一边？", "怎样安排一个兼顾两边的小步骤？"]
    if key == "micro_ysq":
        if dimension_z.get("EMS_M", 0) >= 0.35:
            return ["多项担心同时出现时，哪一项最影响你当下的选择？", "哪一次例外经验让你感到更安全或被理解？"]
        return ["关系担心较少出现时，哪些情境或支持可能在发挥作用？", "你想保留哪一种已经有帮助的应对方式？"]
    if dimension_z.get("BI", 0) >= 0.25 and dimension_z.get("RAP", 0) <= -0.25:
        return ["意愿已经出现时，哪一步最容易卡住？", "把意愿变成一个很小的行动，需要什么支持？"]
    if dimension_z.get("THREAT", 0) >= 0.3:
        return ["想靠近又想保护自己时，怎样的节奏更可承受？", "哪一种边界表达能同时照顾安全和真实？"]
    return ["你现在更想靠近关系，还是先保护自己的节奏？", "下一次愿意尝试的最小行动是什么？"]


def _unique_profile_names(key: str, clusters: list[dict]) -> None:
    if key == "micro_ysq":
        ordered = sorted(clusters, key=lambda item: item["dimension_z"].get("EMS_M", 0))
        level_names = ["较低", "中低", "中高", "较高"] if len(ordered) == 4 else [f"第{index + 1}层" for index in range(len(ordered))]
        for cluster, level in zip(ordered, level_names):
            cluster["profile_name"] = f"关系担心线索{level}的阶段性观察位置"
            cluster["display_name"] = cluster["profile_name"]
            cluster["supportive_explanation"] = f"这一聚合位置表示本组样本的关系担心线索处于{level}位置。它是可变化的连续观察线索，不代表固定类型，也不构成诊断。"
            cluster["product_explanation"] = f"你当前的题项组合更接近“{cluster['profile_name']}”，可结合本人维度和具体情境共同核对。"
        return
    by_name: dict[str, list[dict]] = {}
    for cluster in clusters:
        by_name.setdefault(cluster["profile_name"], []).append(cluster)
    for duplicates in by_name.values():
        if len(duplicates) <= 1:
            continue
        for index, cluster in enumerate(sorted(duplicates, key=lambda item: item["cluster_id"]), 1):
            cluster["profile_name"] = f"{cluster['profile_name']}（位置{index}）"
            cluster["display_name"] = cluster["profile_name"]


def _make_model(key: str, matrix: np.ndarray, columns: list[str], mapping: dict[str, dict], comparisons: list[dict]) -> dict:
    spec = SPECS[key]
    scaler = StandardScaler().fit(matrix)
    z = scaler.transform(matrix)
    method, chosen_k, reason = _choose_method(comparisons)
    fitted, labels = _fit_labels(z, method, chosen_k, RANDOM_SEED)
    pca = PCA(n_components=2, random_state=RANDOM_SEED).fit(z)
    positions = pca.transform(z)
    dimension_names, dimensions = _dimension_values(key, matrix, columns)
    dimension_scaler = StandardScaler().fit(dimensions)
    dimensions_z = dimension_scaler.transform(dimensions)
    centers = fitted.means_ if method == "gaussian_mixture" else fitted.cluster_centers_
    clusters = []
    for cluster_id in range(chosen_k):
        mask = labels == cluster_id
        dimension_mean = dimensions[mask].mean(axis=0)
        dimension_z_mean = dimensions_z[mask].mean(axis=0)
        dimension_z_lookup = {name: _rounded(value) for name, value in zip(dimension_names, dimension_z_mean)}
        profile_name = _profile_name(key, dimension_names, dimension_z_lookup)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "profile_id": f"task12_{key}_{cluster_id}",
                "profile_name": profile_name,
                "display_name": profile_name,
                "n": int(mask.sum()),
                "percent": _rounded(mask.mean() * 100, 1),
                "center_z": {column: _rounded(value) for column, value in zip(columns, centers[cluster_id])},
                "mean_scores": {column: _rounded(value) for column, value in zip(columns, matrix[mask].mean(axis=0))},
                "dimension_means": {name: _rounded(value) for name, value in zip(dimension_names, dimension_mean)},
                "dimension_z": dimension_z_lookup,
                "pca_centroid": {"pc1": _rounded(positions[mask, 0].mean()), "pc2": _rounded(positions[mask, 1].mean())},
                "supportive_explanation": f"这一聚合画像表示本组样本在题项组合上更接近“{profile_name}”。它是可变化的阶段性观察线索，不代表固定标签，也不构成诊断。",
                "product_explanation": f"你当前的题项组合与“{profile_name}”的聚合中心更接近，可把它当作选择下一步练习和访谈问题的线索。",
                "strength_note": "你已经通过具体作答呈现了当下的关注点，这本身就是进一步理解自己的一步。",
                "small_step": "从建议问题中选一个，写下一次不超过十分钟的小观察或小行动。",
                "suggested_assessment_questions": _questions(key, dimension_z_lookup),
                "recommended_card_ids": spec["cards"],
                "recommended_project_tasks": ["完成一个关系情境记录", "选择一个低压力微行动", "一周后复盘体验变化"],
                "card_reason": "围绕本画像呈现的关系关注点，先从觉察、表达和自我支持中选择轻量练习。",
                "human_review_status": "profile_name_and_interpretation_pending_researcher_review",
            }
        )
    _unique_profile_names(key, clusters)
    assignment_thresholds = {}
    mixture_weights = []
    diag_covariances = []
    if method == "gaussian_mixture":
        probabilities = fitted.predict_proba(z)
        max_posterior = probabilities.max(axis=1)
        safe_probabilities = np.clip(probabilities, 1e-12, 1.0)
        entropy = -np.sum(probabilities * np.log(safe_probabilities), axis=1) / np.log(chosen_k)
        assigned = probabilities.argmax(axis=1)
        mahalanobis = np.sqrt(
            np.sum(
                ((z - fitted.means_[assigned]) ** 2) / np.maximum(fitted.covariances_[assigned], 1e-9),
                axis=1,
            )
        )
        mixture_weights = [_rounded(value, 8) for value in fitted.weights_]
        diag_covariances = [
            {column: _rounded(value, 8) for column, value in zip(columns, covariance)}
            for covariance in fitted.covariances_
        ]
        assignment_thresholds = {
            "calibration_source": "training_empirical_exploratory",
            "min_posterior": _rounded(max(0.5, float(np.quantile(max_posterior, 0.10))), 6),
            "max_entropy": _rounded(float(np.quantile(entropy, 0.90)), 6),
            "max_mahalanobis": _rounded(float(np.quantile(mahalanobis, 0.99)), 6),
            "note": "阈值来自训练样本经验分布，只用于受控试点；待留出样本或独立样本后重新冻结。",
        }
    scale_id = spec["scale_id"]
    train_low, train_high = spec["training_range"]
    worksheet_low, worksheet_high = spec["worksheet_range"]
    features = []
    for index, column in enumerate(columns):
        source = mapping.get(f"{scale_id}:{column}", {})
        feature = {
            "feature_id": column,
            "source_variable": source.get("source_column", column),
            "question_no": index + 1,
            "worksheet_question_id": column,
            "label": source.get("original_prompt", column),
            "reverse_scored": False,
            "score_min": train_low,
            "score_max": train_high,
            "mean": _rounded(scaler.mean_[index], 6),
            "std": _rounded(scaler.scale_[index], 6),
        }
        if [train_low, train_high] != [worksheet_low, worksheet_high]:
            feature["input_transform"] = {
                "type": "linear_range",
                "input_min": worksheet_low,
                "input_max": worksheet_high,
                "output_min": train_low,
                "output_max": train_high,
            }
        features.append(feature)
    return {
        "schema_version": "2026.06-profile-model-v1",
        "model_id": f"task12_{scale_id}_profile_v1",
        "group_id": f"task12_data1_{scale_id}",
        "standard_scale_name": spec["name"],
        "scale_id": scale_id,
        "worksheet_id": scale_id,
        "worksheet_link_status": "connected_pilot_review_required",
        "admission_status": "pilot_approved",
        "interpretation_approval_status": "pilot_approved",
        "production_approval_status": "pending_researcher_review",
        "model_governance_version": "profile_model_governance_v1",
        "scoring_version": "worksheet_server_score_v1",
        "assignment_version": "gmm_diag_posterior_v1" if method == "gaussian_mixture" else "euclidean_center_v1",
        "research_dir": "数据1",
        "source_dataset": "数据1/全部数据1.0.xlsx（逐行数据未入仓）",
        "n_cases": int(len(matrix)),
        "n_features": int(len(columns)),
        "features": features,
        "preprocessing": {"retained_rows": int(len(matrix)), "retained_features": len(columns), "imputation": "none_required", "standardization": "z_score_by_training_mean_std", "random_seed": RANDOM_SEED},
        "model_selection": comparisons,
        "selected_method": method,
        "selection_reason": reason,
        "chosen_k": chosen_k,
        "mixture_weights": mixture_weights,
        "diag_covariances": diag_covariances,
        "assignment_thresholds": assignment_thresholds,
        "clusters": clusters,
        "pca": {"components": [[_rounded(value, 6) for value in row] for row in pca.components_], "explained_ratio": [_rounded(value, 6) for value in pca.explained_variance_ratio_]},
        "radar_support": {"dimensions": [{"code": name, "mean": _rounded(mean), "std": _rounded(std)} for name, mean, std in zip(dimension_names, dimension_scaler.mean_, dimension_scaler.scale_)], "value_source": "clusters[].dimension_z"},
        "cross_validation_status": "exploratory_pending_researcher_review",
        "boundary_notice": BOUNDARY,
    }


def _report(models: list[dict]) -> str:
    lines = ["# 任务十二数据1聚类方法选择报告", "", "生成日期：2026-07-10", "", "三份量表分别建模。GaussianMixture（对角协方差）作为 LPA 风格主方法，KMeans 作为兼容性对照，PCA 只用于二维位置展示。画像数量与名称仍需研究者人工复核。", ""]
    for model in models:
        lines.extend([f"## {model['standard_scale_name']}", "", f"- 样本量：{model['n_cases']}；题项数：{model['n_features']}。", f"- 选择：{model['selected_method']}，k={model['chosen_k']}。", f"- 理由：{model['selection_reason']}", "", "| 方法 | k | BIC | AIC | silhouette | 最小簇比例 | 稳定性 ARI | 可读性 |", "|---|---:|---:|---:|---:|---:|---:|---:|"])
        for row in model["model_selection"]:
            lines.append(f"| {row['method']} | {row['k']} | {row['bic'] if row['bic'] is not None else '-'} | {row['aic'] if row['aic'] is not None else '-'} | {row['silhouette']} | {row['min_cluster_ratio']} | {row['stability']} | {row['readability']} |")
        lines.extend(["", "人工验收：确认画像数量、名称、解释及训练建议；算法指标不能替代研究判断。", ""])
    lines.extend(["## 边界", "", BOUNDARY, "逐行训练样本和开放文本未写入模型或报告。", ""])
    return "\n".join(lines)


def build_profiles(npz_path: Path, mapping_path: Path, output_dir: Path, report_path: Path, k_values=range(2, 7), stability_seeds=(11, 23, 37, 53, 71)) -> dict:
    payload = np.load(npz_path)
    mapping = _mapping(mapping_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    models = []
    summary = []
    for key in SPECS:
        matrix = payload[key]
        columns = [str(value) for value in payload[f"{key}_columns"]]
        comparisons = compare_methods(matrix, k_values=k_values, stability_seeds=stability_seeds)
        model = _make_model(key, matrix, columns, mapping, comparisons)
        model["training_source_hashes"] = {
            npz_path.name: hashlib.sha256(npz_path.read_bytes()).hexdigest(),
            mapping_path.name: hashlib.sha256(mapping_path.read_bytes()).hexdigest(),
        }
        hash_material = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        model["artifact_hash"] = hashlib.sha256(hash_material).hexdigest()
        output_path = output_dir / f"task12_{model['scale_id']}_profile_model.json"
        output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        models.append(model)
        summary.append({"scale_id": model["scale_id"], "model_id": model["model_id"], "method": model["selected_method"], "k": model["chosen_k"]})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_report(models), encoding="utf-8")
    return {"model_count": len(models), "models": summary, "report": str(report_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--npz", type=Path, default=DEFAULT_NPZ)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    print(json.dumps(build_profiles(args.npz, args.mapping, args.output_dir, args.report), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
