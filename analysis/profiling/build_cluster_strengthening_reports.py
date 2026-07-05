"""Build required clustering strengthening audit reports.

The script reads existing aggregate profile models and derived anonymous
feature matrices. It does not read raw SAV files, rerun the official model
artifacts, or rewrite product model JSON files.
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OTHER_ROOT = Path(r"D:\codex\workspace\safehome1.0其他内容")
DESIGN_DIR = OTHER_ROOT / "画像系统设计_Claude_20260628"
PRODUCT_PROFILE_DIR = PROJECT_ROOT / "content" / "profiles"
PRODUCT_MATRIX_DIR = DESIGN_DIR / "03_画像模型派生文件_20260629" / "特征矩阵"
SUPPLEMENT_ROOT = DESIGN_DIR / "04_未映射问卷补充聚类_20260629"
SUPPLEMENT_MODEL_DIR = SUPPLEMENT_ROOT / "模型JSON"
OFFLINE_AUDIT_ROOT = DESIGN_DIR / "05_画像模型离线审核产物_20260629"

RANDOM_SEED = 42
BOOTSTRAP_RUNS = 30


@dataclass
class ModelBundle:
    model_type: str
    source_json: Path
    model: dict
    matrix_path: Path
    audit_dir: Path | None


def safe_text(value) -> str:
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def safe_slug(value: str, max_length: int = 90) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", str(value)).strip("_")
    return (slug[:max_length] or "model").strip("_")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def feature_ids(model: dict) -> list[str]:
    return [str(item.get("feature_id")) for item in model.get("features", []) if item.get("feature_id")]


def cluster_counts_match(matrix: pd.DataFrame, model: dict) -> bool:
    if "cluster_id" not in matrix.columns:
        return False
    expected = {int(item.get("cluster_id")): int(item.get("n")) for item in model.get("clusters", [])}
    actual = {int(key): int(value) for key, value in matrix["cluster_id"].value_counts().to_dict().items()}
    return expected == actual


def center_diff(matrix: pd.DataFrame, model: dict, columns: list[str]) -> float:
    means = {item.get("feature_id"): item.get("mean") for item in model.get("features", [])}
    stds = {item.get("feature_id"): item.get("std") for item in model.get("features", [])}
    total = 0.0
    count = 0
    for cluster in model.get("clusters", []):
        cluster_id = cluster.get("cluster_id")
        rows = matrix[matrix["cluster_id"] == cluster_id]
        center = cluster.get("center_z") or {}
        if rows.empty:
            continue
        for column in columns:
            mean = means.get(column)
            std = stds.get(column) or 1
            if mean is None or column not in center:
                continue
            observed = (pd.to_numeric(rows[column], errors="coerce").mean() - float(mean)) / float(std)
            if not math.isfinite(observed):
                continue
            total += abs(observed - float(center[column]))
            count += 1
    return total / count if count else float("inf")


def find_product_matrix(model: dict) -> Path:
    ids = set(feature_ids(model))
    candidates: list[tuple[float, Path]] = []
    for path in sorted(PRODUCT_MATRIX_DIR.glob("*.csv")):
        try:
            matrix = read_csv(path)
        except Exception:
            continue
        if len(matrix) != int(model.get("n_cases", -1)):
            continue
        if not ids.issubset(set(matrix.columns)):
            continue
        if not cluster_counts_match(matrix, model):
            continue
        candidates.append((center_diff(matrix, model, list(ids)), path))
    if not candidates:
        raise FileNotFoundError(f"未找到匹配特征矩阵：{model.get('model_id')}")
    return sorted(candidates, key=lambda item: item[0])[0][1]


def audit_dir_lookup() -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    if not OFFLINE_AUDIT_ROOT.exists():
        return lookup
    for source_path in OFFLINE_AUDIT_ROOT.rglob("来源模型.json"):
        try:
            model = read_json(source_path)
        except Exception:
            continue
        model_id = model.get("model_id") or model.get("group_id")
        if model_id:
            lookup[str(model_id)] = source_path.parent
    return lookup


def load_bundles() -> list[ModelBundle]:
    audit_lookup = audit_dir_lookup()
    bundles: list[ModelBundle] = []
    for path in sorted(PRODUCT_PROFILE_DIR.glob("*.json")):
        model = read_json(path)
        if model.get("schema_version") != "2026.06-profile-model-v1":
            continue
        matrix_path = find_product_matrix(model)
        model_id = str(model.get("model_id") or model.get("group_id"))
        bundles.append(ModelBundle("产品候选模型", path, model, matrix_path, audit_lookup.get(model_id)))

    for path in sorted(SUPPLEMENT_MODEL_DIR.glob("*.json")):
        model = read_json(path)
        if model.get("schema_version") != "2026.06-unmapped-supplementary-profile-v1":
            continue
        matrix_path = SUPPLEMENT_ROOT / model.get("matrix_file", "")
        model_id = str(model.get("model_id") or model.get("group_id"))
        bundles.append(ModelBundle("补充聚类模型", path, model, matrix_path, audit_lookup.get(model_id)))
    return bundles


def z_matrix(matrix: pd.DataFrame, model: dict, columns: list[str]) -> pd.DataFrame:
    feature_meta = {item["feature_id"]: item for item in model.get("features", []) if item.get("feature_id")}
    z = pd.DataFrame(index=matrix.index)
    for column in columns:
        meta = feature_meta.get(column, {})
        mean = float(meta.get("mean") or matrix[column].mean())
        std = float(meta.get("std") or matrix[column].std(ddof=0) or 1)
        if std == 0:
            std = 1.0
        z[column] = (pd.to_numeric(matrix[column], errors="coerce") - mean) / std
    return z.fillna(0.0)


def cluster_counts(labels: np.ndarray) -> tuple[str, int, float]:
    values = pd.Series(labels).value_counts().sort_index()
    counts = [int(item) for item in values.tolist()]
    min_count = min(counts) if counts else 0
    min_pct = min_count / len(labels) if len(labels) else 0.0
    return "/".join(str(item) for item in counts), min_count, min_pct


def quality_risk(row: dict) -> str:
    risks: list[str] = []
    if row["样本量"] < 120:
        risks.append("样本量偏小")
    if row["特征数"] < 3:
        risks.append("特征数偏少")
    if row["最小簇占比"] < 0.10:
        risks.append("最小簇占比低")
    if row["silhouette"] != "" and row["silhouette"] < 0.15:
        risks.append("簇分离度弱")
    if row["Davies_Bouldin"] != "" and row["Davies_Bouldin"] > 2.5:
        risks.append("簇内外分离弱")
    if row["PCA前两维解释率"] != "" and row["PCA前两维解释率"] < 0.25:
        risks.append("PCA二维解释率低")
    return "；".join(risks) if risks else "暂未发现硬性质量风险"


def simple_kmeans(values: np.ndarray, k: int, seed: int, max_iter: int = 100) -> np.ndarray:
    """Small deterministic KMeans used only for stability audit.

    This avoids sklearn KMeans on Windows environments where threadpool
    discovery can fail. Official product model JSON files are not rewritten.
    """

    rng = np.random.default_rng(seed)
    values = np.asarray(values, dtype=float)
    n_rows = values.shape[0]
    if n_rows < k:
        raise ValueError("n_rows must be >= k")
    initial = rng.choice(n_rows, size=k, replace=False)
    centers = values[initial].copy()
    labels = np.zeros(n_rows, dtype=int)
    for _ in range(max_iter):
        distances = ((values[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        new_labels = distances.argmin(axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for cluster_id in range(k):
            mask = labels == cluster_id
            if mask.any():
                centers[cluster_id] = values[mask].mean(axis=0)
            else:
                farthest = distances.min(axis=1).argmax()
                centers[cluster_id] = values[farthest]
    return labels


def compute_quality(bundle: ModelBundle) -> tuple[dict, pd.DataFrame, np.ndarray, list[str]]:
    model = bundle.model
    matrix = read_csv(bundle.matrix_path)
    columns = [column for column in feature_ids(model) if column in matrix.columns]
    labels = pd.to_numeric(matrix["cluster_id"], errors="coerce").fillna(-1).astype(int).to_numpy()
    z = z_matrix(matrix, model, columns)

    silhouette = ""
    dbi = ""
    if len(set(labels)) > 1 and len(columns) >= 2:
        silhouette = round(float(silhouette_score(z, labels)), 4)
        dbi = round(float(davies_bouldin_score(z, labels)), 4)

    counts_text, min_count, min_pct = cluster_counts(labels)
    explained = model.get("pca", {}).get("explained_ratio") or []
    pca_two = round(float(sum(explained[:2])), 4) if explained else ""
    preprocessing = model.get("preprocessing") or {}
    row = {
        "模型ID": model.get("model_id") or model.get("group_id"),
        "模型名称": model.get("standard_scale_name") or model.get("display_name") or model.get("model_key"),
        "模型类型": bundle.model_type,
        "来源数据": model.get("source_dataset"),
        "样本量": int(model.get("n_cases") or len(matrix)),
        "缺失处理后样本量": int(preprocessing.get("retained_rows") or model.get("n_cases") or len(matrix)),
        "特征数": int(model.get("n_features") or len(columns)),
        "k": int(model.get("chosen_k") or len(set(labels))),
        "每簇样本量": counts_text,
        "最小簇样本量": min_count,
        "最小簇占比": round(min_pct, 4),
        "silhouette": silhouette,
        "Davies_Bouldin": dbi,
        "PCA前两维解释率": pca_two,
        "质量风险": "",
    }
    row["质量风险"] = quality_risk(row)
    return row, z, labels, columns


def compute_stability(bundle: ModelBundle, z: pd.DataFrame, labels: np.ndarray, quality: dict) -> dict:
    chosen_k = int(bundle.model.get("chosen_k") or quality["k"])
    rng = np.random.default_rng(RANDOM_SEED)
    if len(z) <= chosen_k or chosen_k < 2:
        return {
            "模型ID": quality["模型ID"],
            "模型名称": quality["模型名称"],
            "固定种子复现ARI": "",
            "bootstrap次数": 0,
            "bootstrap平均ARI": "",
            "bootstrap最低ARI": "",
            "簇数量稳定次数": 0,
            "最小簇反复过小次数": 0,
            "稳定性结论": "暂不使用",
            "稳定性说明": "样本量或簇数不足，无法稳定检验",
        }

    full_labels = simple_kmeans(z.to_numpy(), chosen_k, RANDOM_SEED)
    fixed_ari = round(float(adjusted_rand_score(labels, full_labels)), 4)

    aris: list[float] = []
    stable_k_count = 0
    small_cluster_count = 0
    small_threshold = max(8, int(len(z) * 0.04))
    values = z.to_numpy()
    for run in range(BOOTSTRAP_RUNS):
        sampled = rng.integers(0, len(values), size=len(values))
        sample_values = values[sampled]
        sample_reference = labels[sampled]
        sample_labels = simple_kmeans(sample_values, chosen_k, RANDOM_SEED + run + 1)
        aris.append(float(adjusted_rand_score(sample_reference, sample_labels)))
        counts = np.bincount(sample_labels, minlength=chosen_k)
        if len([item for item in counts if item > 0]) == chosen_k:
            stable_k_count += 1
        if int(counts.min()) < small_threshold:
            small_cluster_count += 1

    mean_ari = round(float(np.mean(aris)), 4)
    min_ari = round(float(np.min(aris)), 4)
    if mean_ari >= 0.60 and small_cluster_count <= 6 and fixed_ari >= 0.80:
        conclusion = "稳定性基本通过"
    elif mean_ari >= 0.40:
        conclusion = "仅内部审核"
    else:
        conclusion = "稳定性不足"
    return {
        "模型ID": quality["模型ID"],
        "模型名称": quality["模型名称"],
        "固定种子复现ARI": fixed_ari,
        "bootstrap次数": BOOTSTRAP_RUNS,
        "bootstrap平均ARI": mean_ari,
        "bootstrap最低ARI": min_ari,
        "簇数量稳定次数": stable_k_count,
        "最小簇反复过小次数": small_cluster_count,
        "稳定性结论": conclusion,
        "稳定性说明": f"30次重抽样平均ARI={mean_ari}，固定种子复现ARI={fixed_ari}",
    }


def admission(quality: dict, stability: dict, bundle: ModelBundle) -> tuple[str, str]:
    if bundle.model_type != "产品候选模型":
        return "仅内部审核", "补充聚类模型默认不开放；需人工确认题项来源后再议。"
    risks = quality["质量风险"]
    if "样本量偏小" in risks or "最小簇占比低" in risks:
        return "暂不使用", risks
    if stability["稳定性结论"] == "稳定性基本通过":
        return "可试点接入", "质量和稳定性达到最低试点要求，仍需人工复核画像解释。"
    if stability["稳定性结论"] == "仅内部审核":
        return "仅内部审核", "稳定性一般，暂不建议展示给用户。"
    return "暂不使用", "稳定性不足，暂不进入用户端。"


def project_flags(model: dict) -> tuple[str, str]:
    blob = " ".join(
        safe_text(value)
        for value in [model.get("standard_scale_name"), model.get("display_name"), model.get("scale_id"), model.get("worksheet_id")]
    ).lower()
    project_a_keys = ["scs", "self_compassion", "情绪", "反思", "rsca", "resilience", "regulatory", "调节"]
    project_b_keys = ["hplp", "健康", "睡眠", "学业", "buoyancy"]
    return (
        "是" if any(key in blob for key in project_a_keys) else "否",
        "是" if any(key in blob for key in project_b_keys) else "否",
    )


def write_outputs(bundles: list[ModelBundle]) -> None:
    quality_rows: list[dict] = []
    stability_rows: list[dict] = []
    index_rows: list[dict] = []
    admission_rows: list[dict] = []
    training_rows: list[dict] = []

    for bundle in bundles:
        quality, z, labels, _columns = compute_quality(bundle)
        stability = compute_stability(bundle, z, labels, quality)
        admit_status, admit_reason = admission(quality, stability, bundle)
        model = bundle.model
        has_visuals = bool(
            bundle.audit_dir
            and (bundle.audit_dir / "问卷聚类分布_PCA.png").exists()
            and (bundle.audit_dir / "各聚类画像热图_原始特征.png").exists()
        )
        quality_rows.append(quality)
        stability_rows.append(stability)
        index_rows.append(
            {
                "模型名称": quality["模型名称"],
                "来源数据": quality["来源数据"],
                "样本量": quality["样本量"],
                "特征数": quality["特征数"],
                "k": quality["k"],
                "是否产品候选": "是" if bundle.model_type == "产品候选模型" else "否",
                "是否已有可视化": "是" if has_visuals else "否",
                "是否可接入小程序": "是" if admit_status == "可试点接入" else "否",
                "当前风险说明": admit_reason if admit_status != "可试点接入" else quality["质量风险"],
                "模型ID": quality["模型ID"],
                "模型文件": str(bundle.source_json),
                "特征矩阵": str(bundle.matrix_path),
                "审核产物目录": str(bundle.audit_dir or ""),
            }
        )
        admission_rows.append(
            {
                "模型名称": quality["模型名称"],
                "模型类型": bundle.model_type,
                "来源数据": quality["来源数据"],
                "准入结论": admit_status,
                "准入理由": admit_reason,
                "质量风险": quality["质量风险"],
                "稳定性结论": stability["稳定性结论"],
                "模型ID": quality["模型ID"],
            }
        )
        if admit_status == "可试点接入":
            project_a, project_b = project_flags(model)
            for cluster in model.get("clusters", []):
                card_ids = cluster.get("recommended_card_ids") or []
                training_rows.append(
                    {
                        "模型名称": quality["模型名称"],
                        "模型ID": quality["模型ID"],
                        "画像ID": cluster.get("profile_id") or cluster.get("cluster_id"),
                        "画像名称": cluster.get("display_name") or cluster.get("profile_name"),
                        "推荐训练卡ID": "；".join(str(item) for item in card_ids),
                        "推荐理由": cluster.get("card_reason") or "根据该画像相对偏低或需支持的题项线索生成，需人工审核。",
                        "适用于情绪调节与不确定性项目": project_a,
                        "适用于学业压力与睡眠健康项目": project_b,
                    }
                )

    DESIGN_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(index_rows).to_csv(DESIGN_DIR / "06A_聚类文件索引与状态表.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(quality_rows).to_csv(DESIGN_DIR / "06B_模型质量审计报告.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(stability_rows).to_csv(DESIGN_DIR / "06C_模型稳定性检验报告.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(training_rows).to_csv(DESIGN_DIR / "06E_画像_训练中心最小映射表.csv", index=False, encoding="utf-8-sig")

    lines = [
        "# 聚类补强模型准入清单",
        "",
        "生成日期：2026-06-30",
        "",
        "本清单只用于小程序试点前审核。聚类画像只表示与既往样本的相对接近程度，不构成诊断、筛查、治疗建议或人格标签。",
        "",
        "## 准入规则",
        "",
        "- 产品候选模型：质量指标和 30 次重抽样稳定性基本通过后，列为 `可试点接入`。",
        "- 补充聚类模型：默认 `仅内部审核`，除非后续人工确认题项来源、计分方向和产品映射。",
        "- 样本量偏小、最小簇占比过低或稳定性不足的模型列为 `暂不使用`。",
        "",
        "## 模型结论",
        "",
        "| 模型 | 类型 | n | k | 准入结论 | 理由 |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    quality_by_id = {row["模型ID"]: row for row in quality_rows}
    for row in admission_rows:
        q = quality_by_id[row["模型ID"]]
        lines.append(
            f"| {row['模型名称']} | {row['模型类型']} | {q['样本量']} | {q['k']} | {row['准入结论']} | {row['准入理由']} |"
        )
    lines.extend(
        [
            "",
            "## 用户端保护",
            "",
            "- 答题不足不输出画像。",
            "- 低置信度不强行解释。",
            "- 离聚类中心过远不强行解释。",
            "- 结果页只能使用“当前更接近”，不能使用“你就是某类型”。",
            "- 所有解释必须保留非诊断边界。",
            "",
            "配套文件：",
            "",
            "- `06A_聚类文件索引与状态表.csv`",
            "- `06B_模型质量审计报告.csv`",
            "- `06C_模型稳定性检验报告.csv`",
            "- `06E_画像_训练中心最小映射表.csv`",
        ]
    )
    (DESIGN_DIR / "06D_模型准入清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    bundles = load_bundles()
    write_outputs(bundles)
    print(json.dumps({"models": len(bundles), "output_dir": str(DESIGN_DIR)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
