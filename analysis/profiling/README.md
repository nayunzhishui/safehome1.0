# 画像聚类分析

本目录只保存可复现分析脚本。原始 `.sav`、Excel、逐行题项矩阵、参与者标识和自由文本不得进入仓库。

## 聚合来源清单

运行：

```powershell
python analysis/profiling/build_dataset_manifest.py
```

输出：`outputs/profile_dataset_manifest.json`。

该文件只记录模型 ID、样本量、特征数、聚合来源类型、source hash、artifact hash、准入状态和人工验证状态。来源文件名、研究者目录、绝对路径和逐行数据只参与本地 hash 计算，不写入产物。
