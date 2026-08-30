"""Build supplementary clustering models for previously unmapped questionnaires.

This script is intentionally separate from build_profile_models.py. The models
here are exploratory/supporting outputs for historical SAV files marked with
``（聚类用）`` and must not be treated as product-ready questionnaire mappings.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd
import pyreadstat
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OTHER_ROOT = Path(r"D:\codex\workspace\safehome1.0其他内容")
DATA_ROOT = OTHER_ROOT / r"夏老师文件\2026年6月18日发给董俊杰的(1)\既往调研数据"
DESIGN_DIR = OTHER_ROOT / "画像系统设计_Claude_20260628"
OUTPUT_DIR = DESIGN_DIR / "04_未映射问卷补充聚类_20260629"
MATRIX_DIR = OUTPUT_DIR / "特征矩阵"
MODEL_DIR = OUTPUT_DIR / "模型JSON"

BOUNDARY_NOTICE = (
    "本补充聚类只用于既往调研数据探索和人工审核，不代表测评问卷-量表目录中已有同一问卷，"
    "也不构成诊断、筛查、治疗建议、人格标签或用户端开放结论。"
)


@dataclass(frozen=True)
class SupplementaryScaleConfig:
    model_key: str
    display_name: str
    source_file_contains: str
    variable_names: tuple[str, ...]
    construct_note: str
    reverse_items: frozenset[str] = frozenset()
    min_value: float | None = None
    max_value: float | None = None


CONFIGS: tuple[SupplementaryScaleConfig, ...] = (
    SupplementaryScaleConfig(
        model_key="parent_child_communication_father_f",
        display_name="亲子沟通父亲版 F 系列",
        source_file_contains=r"1 王季璇 数据及数据分析结果【亲子沟通 学业浮力 情绪弹性】\总数据（聚类用）.sav",
        variable_names=tuple(f"F{i}" for i in range(1, 38)),
        construct_note="既往数据中 F1-F37 为父亲沟通题项；测评问卷-量表目录未找到同一问卷题项原文，本模型仅作补充聚类。",
    ),
    SupplementaryScaleConfig(
        model_key="parent_child_communication_mother_m",
        display_name="亲子沟通母亲版 M 系列",
        source_file_contains=r"1 王季璇 数据及数据分析结果【亲子沟通 学业浮力 情绪弹性】\总数据（聚类用）.sav",
        variable_names=tuple(f"M{i}" for i in range(1, 38)),
        construct_note="既往数据中 M1-M37 为母亲沟通题项；测评问卷-量表目录未找到同一问卷题项原文，本模型仅作补充聚类。",
    ),
    SupplementaryScaleConfig(
        model_key="academic_buoyancy_s",
        display_name="学业浮力 S 系列",
        source_file_contains=r"1 王季璇 数据及数据分析结果【亲子沟通 学业浮力 情绪弹性】\总数据（聚类用）.sav",
        variable_names=tuple(f"S{i}" for i in range(1, 5)),
        construct_note="既往数据中 S1-S4 为学业浮力相关题项；此前未与测评问卷-量表形成同题映射，本模型仅作补充聚类。",
    ),
    SupplementaryScaleConfig(
        model_key="parent_support_autonomy_candidate",
        display_name="父母支持/自主相关候选变量",
        source_file_contains=r"3 夏媛媛 2024年9月初测【初中生自我关怀】\高一数据10.14（聚类用）.sav",
        variable_names=("Q47", "Q54", "Q55", "Q56", "Q58", "Q61"),
        construct_note="这些题项涉及父母尊重意见、干涉想法、倾听、支持、苛责和鼓励；不是已确认的 Z1-Z12 父母自主支持量表。",
    ),
    SupplementaryScaleConfig(
        model_key="social_support_seeking_candidate",
        display_name="社会支持/倾诉资源相关候选变量",
        source_file_contains=r"3 夏媛媛 2024年9月初测【初中生自我关怀】\高一数据10.14（聚类用）.sav",
        variable_names=("Q30", "Q34", "Q36", "Q39", "Q46", "Q48", "Q51", "Q57", "Q65"),
        construct_note="这些题项涉及被关心、亲近关系、同伴倾诉、求助困难和主动倾诉；不是已确认的领悟社会支持量表。",
    ),
    SupplementaryScaleConfig(
        model_key="psychological_flexibility_lixinsan",
        display_name="心理灵活性相关维度（李欣珊）",
        source_file_contains=r"8 李欣珊的论文数据\有效数据（聚类用）.sav",
        variable_names=("开放", "觉察", "行动"),
        construct_note="该文件提供心理灵活性及开放、觉察、行动维度。此处按已有维度分做聚类，不等同于测评量表中的认知灵活性问卷。",
    ),
)

EXPECTED_BUT_NOT_FOUND = (
    {
        "display_name": "父母自主支持 Z1-Z12",
        "reason": "7 个文件名含（聚类用）的 SAV 中未发现 Z1-Z12 变量组；仅发现若干父母支持/自主相关候选题项，已另做候选聚类。",
    },
    {
        "display_name": "领悟社会支持标准量表",
        "reason": "7 个文件名含（聚类用）的 SAV 中未发现可确认的领悟社会支持标准题项组；仅发现社会支持/倾诉资源相关候选题项，已另做候选聚类。",
    },
    {
        "display_name": "认知灵活性标准问卷",
        "reason": "7 个文件名含（聚类用）的 SAV 中未发现可确认的认知灵活性标准题项组；李欣珊文件为心理灵活性维度，已单独标注为相关维度而非同一问卷。",
    },
)


def safe_slug(value: str, max_length: int = 90) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", value).strip("_")
    return slug[:max_length] or "group"


def find_source_file(config: SupplementaryScaleConfig) -> Path | None:
    marked_files = list(DATA_ROOT.rglob("*聚类用*.sav"))
    normalized_target = config.source_file_contains.replace("/", "\\")
    for path in marked_files:
        rel = str(path.relative_to(DATA_ROOT)).replace("/", "\\")
        if rel == normalized_target or normalized_target in rel:
            return path
    return None


def read_sav(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    frame, meta = pyreadstat.read_sav(str(path), apply_value_formats=False)
    labels = {
        str(name): str(label or "")
        for name, label in zip(meta.column_names, meta.column_labels)
    }
    return frame, labels


def apply_reverse(values: pd.Series, variable_name: str, config: SupplementaryScaleConfig) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if variable_name in config.reverse_items and config.min_value is not None and config.max_value is not None:
        return config.min_value + config.max_value - numeric
    return numeric


def clean_matrix(matrix: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    numeric = matrix.apply(pd.to_numeric, errors="coerce")
    initial_rows, initial_features = numeric.shape
    min_non_missing = max(20, int(initial_rows * 0.3))
    valid_columns = [column for column in numeric.columns if numeric[column].notna().sum() >= min_non_missing]
    numeric = numeric[valid_columns]
    if numeric.empty:
        return numeric, {
            "initial_rows": int(initial_rows),
            "initial_features": int(initial_features),
            "retained_rows": 0,
            "retained_features": 0,
            "row_missing_threshold": 0.4,
            "column_min_non_missing": min_non_missing,
            "imputation": "not_applied_no_valid_columns",
        }
    row_missing = numeric.isna().mean(axis=1)
    numeric = numeric[row_missing <= 0.4]
    numeric = numeric.fillna(numeric.mean(axis=0))
    std = numeric.std(axis=0, ddof=0)
    valid_columns = [column for column in numeric.columns if std[column] > 0]
    numeric = numeric[valid_columns]
    return numeric, {
        "initial_rows": int(initial_rows),
        "initial_features": int(initial_features),
        "retained_rows": int(numeric.shape[0]),
        "retained_features": int(numeric.shape[1]),
        "row_missing_threshold": 0.4,
        "column_min_non_missing": min_non_missing,
        "imputation": "column_mean_after_row_filter",
        "standardization": "z_score_before_clustering",
    }


def standardize(matrix: pd.DataFrame) -> tuple[pd.DataFrame, dict, dict]:
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0, ddof=0).replace(0, 1)
    z = (matrix - means) / stds
    return z, means.round(6).to_dict(), stds.round(6).to_dict()


def choose_k(z: pd.DataFrame) -> tuple[int, list[dict]]:
    n_rows = z.shape[0]
    max_k = min(6, max(2, n_rows // 20))
    candidates: list[dict] = []
    best: tuple[float, int] | None = None
    for k in range(2, max_k + 1):
        model = KMeans(n_clusters=k, n_init=20, max_iter=300, random_state=42)
        labels = model.fit_predict(z)
        counts = np.bincount(labels)
        min_cluster_size = int(counts.min())
        if min_cluster_size < max(8, int(n_rows * 0.04)):
            silhouette = -1.0
        else:
            silhouette = float(silhouette_score(z, labels))
        item = {
            "k": k,
            "inertia": round(float(model.inertia_), 3),
            "silhouette": round(float(silhouette), 4),
            "min_cluster_size": min_cluster_size,
        }
        candidates.append(item)
        score = (silhouette, -k)
        if best is None or score > best:
            best = (silhouette, k)
    return best[1] if best else 2, candidates


def project_pca(z: pd.DataFrame) -> tuple[np.ndarray, dict]:
    if z.shape[1] == 1:
        values = z.iloc[:, 0].to_numpy()
        return np.column_stack([values, np.zeros_like(values)]), {
            "components": [[1.0], [0.0]],
            "explained_ratio": [1.0, 0.0],
        }
    pca = PCA(n_components=2, random_state=42)
    projected = pca.fit_transform(z)
    return projected, {
        "components": np.round(pca.components_, 6).tolist(),
        "explained_ratio": np.round(pca.explained_variance_ratio_, 6).tolist(),
    }


def short_label(labels: dict[str, str], variable_name: str) -> str:
    label = labels.get(variable_name) or variable_name
    label = re.sub(r"^\d+[.、，,]?\s*", "", label)
    return label[:32]


def cluster_name(center: pd.Series, labels: dict[str, str]) -> tuple[str, str]:
    high = center.sort_values(ascending=False).head(2)
    low = center.sort_values(ascending=True).head(2)
    high_labels = "、".join(short_label(labels, key) for key in high.index if high[key] > 0.25)
    low_labels = "、".join(short_label(labels, key) for key in low.index if low[key] < -0.25)
    if high_labels and low_labels:
        name = f"{high_labels}较高，{low_labels}较低"
    elif high_labels:
        name = f"{high_labels}较高"
    elif low_labels:
        name = f"{low_labels}较低"
    else:
        name = "接近本组平均"
    explanation = f"该画像表示本组样本在该变量组上的相对位置：{name}。此解释只用于人工审核和群体参照。"
    return name, explanation


def build_model(config: SupplementaryScaleConfig) -> tuple[dict | None, dict | None]:
    source_path = find_source_file(config)
    if source_path is None:
        return None, {"display_name": config.display_name, "reason": "未找到标注为（聚类用）的源 SAV 文件"}
    frame, labels = read_sav(source_path)
    missing = [name for name in config.variable_names if name not in frame.columns]
    if missing:
        return None, {
            "display_name": config.display_name,
            "source_dataset": str(source_path.relative_to(DATA_ROOT)),
            "reason": f"缺少变量：{', '.join(missing)}",
        }
    matrix = pd.DataFrame({
        name: apply_reverse(frame[name], name, config)
        for name in config.variable_names
    })
    matrix, preprocessing = clean_matrix(matrix)
    if matrix.shape[0] < 40 or matrix.shape[1] < 2:
        return None, {
            "display_name": config.display_name,
            "source_dataset": str(source_path.relative_to(DATA_ROOT)),
            "reason": "清理后样本量 < 40 或特征数 < 2",
            "preprocessing": preprocessing,
        }

    z, means, stds = standardize(matrix)
    chosen_k, candidates = choose_k(z)
    kmeans = KMeans(n_clusters=chosen_k, n_init=30, max_iter=300, random_state=42)
    cluster_labels = kmeans.fit_predict(z)
    projected, pca_info = project_pca(z)

    model_id = f"unmapped__{safe_slug(config.display_name)}__{safe_slug(str(source_path.relative_to(DATA_ROOT)), 80)}"
    digest = hashlib.sha1(model_id.encode("utf-8"), usedforsecurity=False).hexdigest()[:10]
    model_id = f"{model_id}__{digest}"

    MATRIX_DIR.mkdir(parents=True, exist_ok=True)
    matrix_out = MATRIX_DIR / f"特征矩阵_{safe_slug(config.display_name)}__{digest}.csv"
    derived = matrix.copy()
    derived.insert(0, "anonymous_row_id", [f"row_{idx + 1:05d}" for idx in range(len(derived))])
    derived["cluster_id"] = cluster_labels
    derived["pc1"] = np.round(projected[:, 0], 6)
    derived["pc2"] = np.round(projected[:, 1], 6)
    derived.to_csv(matrix_out, index=False, encoding="utf-8-sig")

    z_frame = pd.DataFrame(z, columns=z.columns)
    clusters = []
    for cluster_id in sorted(set(cluster_labels)):
        mask = cluster_labels == cluster_id
        center = z_frame.loc[mask].mean(axis=0)
        name, explanation = cluster_name(center, labels)
        clusters.append(
            {
                "cluster_id": int(cluster_id),
                "profile_name": f"画像{cluster_id + 1}：{name}",
                "n": int(mask.sum()),
                "percent": round(float(mask.mean() * 100), 1),
                "center_z": {key: round(float(value), 4) for key, value in center.items()},
                "mean_scores": {key: round(float(value), 4) for key, value in matrix.loc[mask].mean(axis=0).items()},
                "pca_centroid": {
                    "pc1": round(float(projected[mask, 0].mean()), 4),
                    "pc2": round(float(projected[mask, 1].mean()), 4),
                },
                "supportive_explanation": explanation,
            }
        )

    feature_meta = [
        {
            "feature_id": name,
            "source_variable": name,
            "label": labels.get(name, ""),
            "reverse_scored": name in config.reverse_items,
            "mean": means.get(name),
            "std": stds.get(name),
        }
        for name in matrix.columns
    ]
    model = {
        "schema_version": "2026.06-unmapped-supplementary-profile-v1",
        "model_id": model_id,
        "display_name": config.display_name,
        "model_key": config.model_key,
        "source_dataset": str(source_path.relative_to(DATA_ROOT)),
        "n_cases": int(matrix.shape[0]),
        "n_features": int(matrix.shape[1]),
        "chosen_k": int(chosen_k),
        "features": feature_meta,
        "preprocessing": preprocessing,
        "model_selection": candidates,
        "pca": pca_info,
        "clusters": clusters,
        "construct_note": config.construct_note,
        "boundary_notice": BOUNDARY_NOTICE,
        "matrix_file": str(matrix_out.relative_to(OUTPUT_DIR)),
        "created_at": "2026-06-29",
    }
    return model, None


def write_reports(models: list[dict], skipped: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for model in models:
        out_path = MODEL_DIR / f"{safe_slug(model['display_name'])}__{hashlib.sha1(model['model_id'].encode('utf-8'), usedforsecurity=False).hexdigest()[:10]}.json"
        out_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    variable_rows = []
    for model in models:
        for feature in model["features"]:
            variable_rows.append(
                {
                    "模型名称": model["display_name"],
                    "来源数据": model["source_dataset"],
                    "变量名": feature["source_variable"],
                    "变量标签": feature["label"],
                    "是否反向处理": "是" if feature["reverse_scored"] else "否",
                    "均值": feature["mean"],
                    "标准差": feature["std"],
                    "说明": model["construct_note"],
                }
            )
    pd.DataFrame(variable_rows).to_csv(OUTPUT_DIR / "补充聚类变量使用清单.csv", index=False, encoding="utf-8-sig")

    summary = {
        "generated_models": len(models),
        "skipped": len(skipped),
        "source_rule": "only SAV files whose filename contains （聚类用）",
        "models": [
            {
                "display_name": model["display_name"],
                "source_dataset": model["source_dataset"],
                "n_cases": model["n_cases"],
                "n_features": model["n_features"],
                "chosen_k": model["chosen_k"],
            }
            for model in models
        ],
        "skipped_items": skipped,
        "boundary_notice": BOUNDARY_NOTICE,
    }
    (OUTPUT_DIR / "补充聚类模型构建摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# 未映射问卷补充聚类说明",
        "",
        "更新日期：2026-06-29",
        "",
        "本轮根据用户要求，对此前未写入 01C 的既往调研问卷/变量组做补充聚类。数据来源仅限文件名包含 `（聚类用）` 的 `.sav` 文件。",
        "",
        "重要边界：这些模型不是已确认的产品量表映射，不自动进入小程序用户端，也不代表同名测评量表已完成题项验收。",
        "",
        "## 聚类规则",
        "",
        "- 聚类单位：研究组 × 同一问卷/同一变量组。",
        "- 不合并不同问卷或不同研究组的数据。",
        "- 缺失处理：删除缺失率超过 40% 的行；列非缺失量低于 max(20, 30%) 的变量剔除；剩余缺失用列均值填补。",
        "- 标准化：每个变量做 z 标准化后进入 KMeans。",
        "- k 选择：在 2-6 中按 silhouette 和最小簇规模选择。",
        "- 二维展示坐标：PCA 前两主成分。",
        "- 不输出被试原始身份信息，只输出匿名行号和派生特征矩阵。",
        "",
        "## 已生成模型",
        "",
        "| 模型 | 来源数据 | n | 特征数 | k | 说明 |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for model in models:
        lines.append(
            f"| {model['display_name']} | {model['source_dataset']} | {model['n_cases']} | {model['n_features']} | {model['chosen_k']} | {model['construct_note']} |"
        )
    lines.extend(["", "## 跳过或未确认项目", "", "| 项目 | 原因 |", "| --- | --- |"])
    for item in skipped:
        lines.append(f"| {item.get('display_name')} | {item.get('reason')} |")
    lines.extend(["", "## 输出文件", "", "- `补充聚类模型构建摘要.json`", "- `补充聚类变量使用清单.csv`", "- `模型JSON/`", "- `特征矩阵/`", ""])
    (OUTPUT_DIR / "04_未映射问卷补充聚类说明.md").write_text("\n".join(lines), encoding="utf-8")

    report_path = OTHER_ROOT / "画像聚类结果报告_20260629.md"
    report_append = [
        "",
        "## 未映射问卷补充聚类（2026-06-29）",
        "",
        "本节为补充聚类，不属于已确认产品量表映射模型。仅使用文件名含 `（聚类用）` 的 SAV 文件。",
        "",
        "| 模型 | n | 特征数 | k | 输出位置 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for model in models:
        report_append.append(
            f"| {model['display_name']} | {model['n_cases']} | {model['n_features']} | {model['chosen_k']} | `画像系统设计_Claude_20260628/04_未映射问卷补充聚类_20260629` |"
        )
    report_append.extend(["", "未确认项目见 `04_未映射问卷补充聚类说明.md`。", ""])
    if report_path.exists():
        text = report_path.read_text(encoding="utf-8")
        marker = "## 未映射问卷补充聚类（2026-06-29）"
        if marker in text:
            text = text.split(marker)[0].rstrip() + "\n"
        report_path.write_text(text.rstrip() + "\n" + "\n".join(report_append), encoding="utf-8")

    design_path = DESIGN_DIR / "02_分组聚类设计.md"
    design_append = [
        "",
        "## 未映射问卷补充聚类（2026-06-29）",
        "",
        "按用户要求，对此前未进入 01C 的问卷/变量组进行补充聚类。该部分只使用 `（聚类用）.sav` 文件，不作为产品量表一一映射结论。",
        "",
        f"- 输出目录：`{OUTPUT_DIR.name}`",
        f"- 已生成模型：{len(models)} 个",
        f"- 跳过/未确认：{len(skipped)} 个",
        "",
    ]
    if design_path.exists():
        text = design_path.read_text(encoding="utf-8")
        marker = "## 未映射问卷补充聚类（2026-06-29）"
        if marker in text:
            text = text.split(marker)[0].rstrip() + "\n"
        design_path.write_text(text.rstrip() + "\n" + "\n".join(design_append), encoding="utf-8")


def main() -> int:
    models: list[dict] = []
    skipped: list[dict] = list(EXPECTED_BUT_NOT_FOUND)
    for config in CONFIGS:
        model, skip = build_model(config)
        if model is not None:
            models.append(model)
        if skip is not None:
            skipped.append(skip)
    write_reports(models, skipped)
    print(json.dumps({"generated_models": len(models), "skipped": len(skipped)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
