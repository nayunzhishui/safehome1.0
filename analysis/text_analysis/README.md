# SafeHome 文本分析离线脚本

本目录只用于离线、脱敏、聚合分析，不接入用户端实时解释。

## 脚本

- `analyze_text_sources.py`：汇总文本来源，输出情绪关键词和共现网络。
- `build_text_features.py`：只输出文本特征摘要，默认写入 `outputs/text_analysis/text_features_summary.json`。
- `build_social_network.py`：只输出社会网络聚合摘要，默认写入 `outputs/text_analysis/social_network_summary.json`。

## 文本来源

来源包括：

- `emotion_diaries.event_description`
- `emotion_diaries.automatic_thought`
- `emotion_diaries.behavior`
- `emotion_diaries.raw_text`
- `feedback_results.supportive_feedback`
- `supervision_requests.message`
- `supervision_requests.reply`
- `checkins.reflection`
- `emotion_thermometer.brief_text`

## 脱敏规则

- 输出文件不写入原始自由文本。
- 只输出计数、关键词类别、文本长度、节点和边。
- 默认不面向普通用户展示复杂网络图。
- 任何研究导出必须继续走后台授权和脱敏流程。

## 边界

文本分析只用于研究和阶段性反馈参考，不构成诊断、筛查、治疗建议、风险预测或人格判断。
