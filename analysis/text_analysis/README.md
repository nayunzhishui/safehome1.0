# SafeHome 离线分析唯一主路径

本目录只用于离线、只读输入、脱敏聚合分析，不接入普通用户端实时推断。

## 三类分析

1. **情感计算**：按用户、系统、督导/研究者写作者分层，聚合情绪词、效价、唤醒、强度和覆盖率。
2. **语义共现网络**：分析同一字段或句子中的人物、场景、情绪、行为概念及反射弧线索；它不是真实社会关系网络。
3. **家庭关系拓扑审计**：只分析 `family_links` 中 `status=active`（兼容旧快照 `confirmed`）且未撤回的结构关系，只用于绑定覆盖和数据质量审计。

禁止把结果用于诊断、危机预测、人格判断、关系质量打分或自动惩罚。风险识别继续由独立风险规则和人工队列处理。

## 当前脚本

- `analyze_text_sources.py`：唯一文本来源契约、SQLite 只读适配、情绪规则和句子级概念共现。
- `build_text_features.py`：生成来源分层的情感计算摘要。
- `build_social_network.py`：历史文件名保留，实际生成“语义共现网络”。
- `build_family_topology_audit.py`：生成家庭关系拓扑聚合审计。
- `analysis/profiling/affective_computing_prototype.py`、`social_network_prototype.py`：仅保留兼容入口，已取消外部绝对输出路径。

## 文本来源与写作者

| 数据来源 | 写作者 | 情感计算 | 语义网络 |
|---|---|---:|---:|
| `emotion_diaries.event_description` | 用户 | 是 | 是 |
| `emotion_diaries.automatic_thought` | 用户 | 是 | 是 |
| `emotion_diaries.body_sensation` | 用户 | 是 | 是 |
| `emotion_diaries.behavior` | 用户 | 是 | 是 |
| `emotion_diaries.raw_text` | 用户 | 是 | 是 |
| `feedback_results.supportive_feedback` | 系统 | 是，单独分层 | 否 |
| `supervision_requests.message` | 用户 | 是 | 否 |
| `supervision_requests.supervisor_reply` | 督导 | 是，单独分层 | 否 |
| `checkins.reflection` | 用户 | 是 | 否 |
| `emotion_thermometer.brief_text` | 用户 | 是 | 是 |

用户文本、系统文本和督导文本不得合并解释为一个人的总体效价。

## 运行方式

```powershell
python analysis/text_analysis/analyze_text_sources.py --db backend/safehome.sqlite3 --minimum-support 5
python analysis/text_analysis/build_text_features.py --db backend/safehome.sqlite3 --minimum-support 5
python analysis/text_analysis/build_social_network.py --db backend/safehome.sqlite3 --minimum-support 5
$env:SAFEHOME_ANALYSIS_HMAC_KEY = "仅本次运行使用的随机密钥"
python analysis/text_analysis/build_family_topology_audit.py --db backend/safehome.sqlite3 --minimum-group-size 5
Remove-Item Env:SAFEHOME_ANALYSIS_HMAC_KEY
```

脚本使用 SQLite `mode=ro`，不调用 `init_db()`。输出默认位于 `outputs/text_analysis`。

## 质量与隐私门禁

- 空数据为 `quality_status=empty`，不得标记为可用。
- 小于阈值的节点、边和分组被抑制。
- 产物不包含原始文本、真实用户 ID、原始记录 ID或稳定伪名。
- 家庭拓扑使用运行级 HMAC 仅在内存中连图，对外只输出聚合分布。
- 词典仍是项目测试样例；未完成授权词典、人工标注和外部效标验证前，只能内部探索。
