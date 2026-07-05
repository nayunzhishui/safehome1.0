"""Build aggregate clustering profile models from confirmed scale crosswalks.

Raw research rows are read-only. Row-level derived feature matrices are written
outside the app project under safehome1.0其他内容/画像系统设计_Claude_20260628.
Only aggregate model JSON files are written to content/profiles.
"""

from __future__ import annotations

import argparse
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
DESIGN_DIR = OTHER_ROOT / "画像系统设计_Claude_20260628"
DATA_ROOT = OTHER_ROOT / r"夏老师文件\2026年6月18日发给董俊杰的(1)\既往调研数据"
CROSSWALK_PATH = DESIGN_DIR / "01C_量表题目映射对照表.csv"
DERIVED_DIR = DESIGN_DIR / "03_画像模型派生文件_20260629"
CONTENT_PROFILE_DIR = PROJECT_ROOT / "content" / "profiles"

BOUNDARY_NOTICE = "画像模型只用于群体位置参考和支持性解释，不构成诊断、筛查、治疗建议或人格标签。"


@dataclass(frozen=True)
class ScaleRule:
    scale_id: str
    worksheet_id: str | None
    item_prefix: str | None
    min_value: int | None = None
    max_value: int | None = None
    reverse_items: frozenset[int] = frozenset()


SCALE_RULES: dict[str, ScaleRule] = {
    "父母反思功能问卷（PRFQ）": ScaleRule(
        "parent_reflective_functioning_prfq",
        "parent_reflective_functioning_prfq",
        "PRFQ",
        1,
        7,
        frozenset({11, 18}),
    ),
    "自我关怀量表（SCS）": ScaleRule(
        "self_compassion_scs_cn",
        "self_compassion_scs_cn",
        "SCS",
        1,
        5,
        frozenset({1, 2, 4, 6, 8, 11, 13, 16, 18, 20, 21, 24, 25}),
    ),
    "青少年情绪弹性问卷": ScaleRule("emotional_resilience_11", "emotional_resilience_11", "ERES", 1, 6),
    "简式心理韧性量表（CD-RISC-10）": ScaleRule(
        "cd_risc10_brief_resilience",
        "cd_risc10_brief_resilience",
        "CDRISC",
        0,
        4,
    ),
    "一般调节聚焦问卷": ScaleRule("regulatory_focus_general_18", None, "RFQG", 1, 7),
    "青少年心理韧性量表（RSCA）": ScaleRule(
        "rsca_adolescent_resilience",
        None,
        "RSCA",
        1,
        5,
        frozenset({1, 2, 5, 6, 9, 12, 15, 16, 17, 21, 26, 27}),
    ),
    "健康促进生活方式量表（HPLP）": ScaleRule("hplp_c_health_promoting_lifestyle", None, "HPLP", 1, 4),
    "心理健康自评问卷（GHQ-12）": ScaleRule(
        "ghq12_general_health",
        None,
        "GHQ",
        1,
        4,
        frozenset({1, 3, 4, 7, 8, 12}),
    ),
    "反思功能问卷8题（RFQ-8）": ScaleRule("rfq8_reflective_functioning", None, "RFQ", 1, 7),
}


def safe_slug(value: str, max_length: int = 80) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", value).strip("_")
    return slug[:max_length] or "group"


def model_filename(model_id: str) -> str:
    digest = hashlib.sha1(model_id.encode("utf-8")).hexdigest()[:10]
    return f"{safe_slug(model_id, 128)}__{digest}.json"


def parse_question_no(value) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else None


def worksheet_question_id(rule: ScaleRule, question_no: int | None, variable: str) -> str:
    if rule.item_prefix and question_no is not None:
        return f"{rule.item_prefix}{question_no:02d}"
    return variable


def read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".sav":
        frame, _meta = pyreadstat.read_sav(str(path), apply_value_formats=False)
        return frame
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"unsupported data file: {path}")


def load_crosswalk() -> pd.DataFrame:
    crosswalk = pd.read_csv(CROSSWALK_PATH, encoding="utf-8-sig")
    usable = crosswalk[
        crosswalk["是否可用于画像"].astype(str).str.contains("是", na=False)
        & crosswalk["是否可用于计分"].astype(str).str.contains("是", na=False)
        & crosswalk["匹配置信度"].astype(str).isin(["high", "medium"])
    ].copy()
    usable = usable[usable["标准量表名"].isin(SCALE_RULES)]
    return usable


def apply_reverse(series: pd.Series, rule: ScaleRule, question_no: int | None) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if question_no in rule.reverse_items and rule.min_value is not None and rule.max_value is not None:
        return rule.min_value + rule.max_value - numeric
    return numeric


def build_feature_matrix(data: pd.DataFrame, rows: pd.DataFrame, rule: ScaleRule) -> tuple[pd.DataFrame, list[dict]]:
    features: dict[str, pd.Series] = {}
    feature_meta: list[dict] = []
    for _, row in rows.iterrows():
        variable = str(row["调研数据变量"])
        if variable not in data.columns:
            continue
        question_no = parse_question_no(row.get("测评问卷题号"))
        feature_id = worksheet_question_id(rule, question_no, variable)
        if feature_id in features:
            feature_id = f"{feature_id}_{safe_slug(variable)}"
        values = apply_reverse(data[variable], rule, question_no)
        features[feature_id] = values
        feature_meta.append(
            {
                "feature_id": feature_id,
                "source_variable": variable,
                "question_no": question_no,
                "worksheet_question_id": worksheet_question_id(rule, question_no, variable),
                "label": str(row.get("调研变量标签") or row.get("测评问卷题目") or variable),
                "reverse_scored": question_no in rule.reverse_items,
                "score_min": rule.min_value,
                "score_max": rule.max_value,
            }
        )
    matrix = pd.DataFrame(features)
    return matrix, feature_meta


def clean_matrix(matrix: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    numeric = matrix.apply(pd.to_numeric, errors="coerce")
    initial_rows, initial_cols = numeric.shape
    valid_columns = [column for column in numeric.columns if numeric[column].notna().sum() >= max(20, int(initial_rows * 0.3))]
    numeric = numeric[valid_columns]
    row_missing = numeric.isna().mean(axis=1)
    numeric = numeric[row_missing <= 0.4]
    fill_values = numeric.mean(axis=0)
    numeric = numeric.fillna(fill_values)
    std = numeric.std(axis=0, ddof=0).replace(0, np.nan)
    valid_columns = [column for column in numeric.columns if not np.isnan(std[column])]
    numeric = numeric[valid_columns]
    return numeric, {
        "initial_rows": int(initial_rows),
        "initial_features": int(initial_cols),
        "retained_rows": int(numeric.shape[0]),
        "retained_features": int(numeric.shape[1]),
        "row_missing_threshold": 0.4,
        "column_min_non_missing": max(20, int(initial_rows * 0.3)),
        "imputation": "column_mean_after_row_filter",
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
        model = KMeans(n_clusters=k, n_init=10, max_iter=200, random_state=42)
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
    chosen = best[1] if best else 2
    return chosen, candidates


def pca_projection(z: pd.DataFrame) -> tuple[np.ndarray, dict]:
    if z.shape[1] == 1:
        values = z.iloc[:, 0].to_numpy()
        projected = np.column_stack([values, np.zeros_like(values)])
        return projected, {
            "components": [[1.0], [0.0]],
            "explained_ratio": [1.0, 0.0],
        }
    pca = PCA(n_components=2, random_state=42)
    projected = pca.fit_transform(z)
    return projected, {
        "components": np.round(pca.components_, 6).tolist(),
        "explained_ratio": np.round(pca.explained_variance_ratio_, 6).tolist(),
    }


def feature_label(feature_meta: list[dict], feature_id: str) -> str:
    for item in feature_meta:
        if item["feature_id"] == feature_id:
            label = re.sub(r"^\d+[.、，,]?\s*", "", item["label"])
            return label[:28]
    return feature_id


def cluster_interpretation(center: pd.Series, feature_meta: list[dict]) -> tuple[str, str]:
    high = center.sort_values(ascending=False).head(2)
    low = center.sort_values(ascending=True).head(2)
    high_labels = "、".join(feature_label(feature_meta, key) for key in high.index if high[key] > 0.25)
    low_labels = "、".join(feature_label(feature_meta, key) for key in low.index if low[key] < -0.25)
    if high_labels and low_labels:
        name = f"{high_labels}较高，{low_labels}较低"
    elif high_labels:
        name = f"{high_labels}较高"
    elif low_labels:
        name = f"{low_labels}较低"
    else:
        name = "接近本组平均"
    explanation = f"该画像表示本组样本在这些题项组合上的相对位置：{name}。它只用于群体参照和支持性解释，不代表固定标签。"
    return name, explanation


def build_model(group_key: tuple[str, str, str], rows: pd.DataFrame) -> dict | None:
    scale_name, research_dir, data_file = group_key
    rule = SCALE_RULES[scale_name]
    data_path = DATA_ROOT / data_file
    if not data_path.exists():
        return None
    data = read_dataset(data_path)
    matrix, feature_meta = build_feature_matrix(data, rows, rule)
    matrix, cleaning = clean_matrix(matrix)
    if matrix.shape[0] < 40 or matrix.shape[1] < 2:
        return {
            "skipped": True,
            "reason": "retained rows < 40 or retained features < 2",
            "scale_name": scale_name,
            "research_dir": research_dir,
            "data_file": data_file,
            "cleaning": cleaning,
        }
    z, means, stds = standardize(matrix)
    chosen_k, candidates = choose_k(z)
    kmeans = KMeans(n_clusters=chosen_k, n_init=20, max_iter=300, random_state=42)
    labels = kmeans.fit_predict(z)
    projected, pca_info = pca_projection(z)

    data_slug = safe_slug(data_file, 96)
    matrix_out = DERIVED_DIR / "特征矩阵" / f"{safe_slug(research_dir, 72)}__{data_slug}__{safe_slug(scale_name, 48)}.csv"
    matrix_out.parent.mkdir(parents=True, exist_ok=True)
    derived = matrix.copy()
    derived.insert(0, "anonymous_row_id", [f"row_{index + 1:05d}" for index in range(len(derived))])
    derived["cluster_id"] = labels
    derived["pc1"] = np.round(projected[:, 0], 6)
    derived["pc2"] = np.round(projected[:, 1], 6)
    derived.to_csv(matrix_out, index=False, encoding="utf-8-sig")

    clusters = []
    z_frame = pd.DataFrame(z, columns=z.columns)
    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        center = z_frame.loc[mask].mean(axis=0)
        name, explanation = cluster_interpretation(center, feature_meta)
        clusters.append(
            {
                "cluster_id": int(cluster_id),
                "profile_id": f"profile_{cluster_id}",
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

    group_id = f"{safe_slug(research_dir, 72)}__{data_slug}__{rule.scale_id}"
    return {
        "schema_version": "2026.06-profile-model-v1",
        "model_id": group_id,
        "group_id": group_id,
        "standard_scale_name": scale_name,
        "scale_id": rule.scale_id,
        "worksheet_id": rule.worksheet_id,
        "research_dir": research_dir,
        "source_dataset": data_file,
        "n_cases": int(matrix.shape[0]),
        "n_features": int(matrix.shape[1]),
        "features": [
            {
                **item,
                "mean": means.get(item["feature_id"]),
                "std": stds.get(item["feature_id"]),
            }
            for item in feature_meta
            if item["feature_id"] in matrix.columns
        ],
        "preprocessing": cleaning,
        "model_selection": candidates,
        "chosen_k": chosen_k,
        "pca": pca_info,
        "clusters": clusters,
        "boundary_notice": BOUNDARY_NOTICE,
        "created_at": "2026-06-29",
    }


def write_reports(models: list[dict], skipped: list[dict]) -> None:
    DESIGN_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 分组聚类设计与执行记录",
        "",
        "更新日期：2026-06-29",
        "",
        "聚类单位固定为：研究组 × 同一问卷/同一量表。如果一个数据表包含多个量表，必须先拆分为各量表题项集合，再分别计分和聚类。",
        "",
        "本轮只使用 `01C_量表题目映射对照表.csv` 中一一对应且可用于计分/画像的题项；不做主题相近映射。",
        "",
        "## 已生成模型",
        "",
        "| 模型ID | 标准量表 | 样本量 | 特征数 | k | 画像命名 | 来源数据 |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for model in models:
        naming = " / ".join(c.get("display_name", "") for c in model["clusters"])
        lines.append(
            f"| `{model['model_id']}` | {model['standard_scale_name']} | {model['n_cases']} | {model['n_features']} | {model['chosen_k']} | {naming} | {model['source_dataset']} |"
        )
    lines.extend(["", "## 跳过项", "", "| 标准量表 | 来源数据 | 原因 |", "| --- | --- | --- |"])
    for item in skipped:
        lines.append(f"| {item.get('scale_name')} | {item.get('data_file')} | {item.get('reason')} |")
    lines.append("")
    (DESIGN_DIR / "02_分组聚类设计.md").write_text("\n".join(lines), encoding="utf-8")

    report = [
        "# 画像聚类结果报告",
        "",
        "输出日期：2026-06-29",
        "",
        "本报告只呈现聚合结果，不包含被试逐行原始数据。画像名称和解释均为支持性描述，不构成诊断、筛查或人格标签。",
        "",
        "## 模型概览",
        "",
        f"- 已生成模型：{len(models)} 个",
        f"- 跳过分组：{len(skipped)} 个",
        "- 聚类方法：KMeans，k 在 2-6 中按 silhouette 和最小簇规模选择；二维展示使用 PCA。",
        "",
    ]
    for model in models:
        report.extend(
            [
                f"## {model['standard_scale_name']}｜{model['research_dir']}",
                "",
                f"- 模型ID：`{model['model_id']}`",
                f"- 样本量：{model['n_cases']}；特征数：{model['n_features']}；选择 k={model['chosen_k']}",
                "",
                "| 画像 | n | 占比 | 支持性解释 |",
                "| --- | ---: | ---: | --- |",
            ]
        )
        for cluster in model["clusters"]:
            report.append(
                f"| {cluster['profile_name']} | {cluster['n']} | {cluster['percent']}% | {cluster['supportive_explanation']} |"
            )
        report.append("")
    (OTHER_ROOT / "画像聚类结果报告_20260629.md").write_text("\n".join(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="optional limit for smoke runs")
    args = parser.parse_args()

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    # Preserve manually curated display_names before clearing old files
    existing_display_names: dict[str, dict[int, str]] = {}
    if not args.limit:
        for path in CONTENT_PROFILE_DIR.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if payload.get("schema_version") == "2026.06-profile-model-v1":
                mid = payload.get("model_id") or payload.get("group_id")
                if mid:
                    existing_display_names[mid] = {
                        c["cluster_id"]: c["display_name"]
                        for c in payload.get("clusters", [])
                        if c.get("display_name")
                    }
                path.unlink()
    crosswalk = load_crosswalk()
    groups = list(crosswalk.groupby(["标准量表名", "既往调研目录", "既往调研数据文件"], sort=False))
    if args.limit:
        groups = groups[: args.limit]

    models: list[dict] = []
    skipped: list[dict] = []
    for group_key, rows in groups:
        try:
            model = build_model(group_key, rows)
        except Exception as exc:
            skipped.append({"scale_name": group_key[0], "data_file": group_key[2], "reason": str(exc)})
            continue
        if not model:
            skipped.append({"scale_name": group_key[0], "data_file": group_key[2], "reason": "source file missing"})
        elif model.get("skipped"):
            skipped.append(model)
        else:
            models.append(model)
            # Restore manually curated display_names from previous run
            mid = model["model_id"]
            if mid in existing_display_names:
                for cluster in model["clusters"]:
                    dn = existing_display_names[mid].get(cluster["cluster_id"])
                    if dn:
                        cluster["display_name"] = dn
            out_path = CONTENT_PROFILE_DIR / model_filename(model["model_id"])
            out_path.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "generated_models": len(models),
        "skipped": len(skipped),
        "model_ids": [model["model_id"] for model in models],
    }
    (DERIVED_DIR / "画像模型构建摘要.json").write_text(
        json.dumps({"summary": summary, "skipped": skipped}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_reports(models, skipped)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
