# 关系探索任务页设计上下文

版本：2026-08-11 冻结版

## Goal

让用户安全、低压力地完成一份愿意表达的材料，并始终知道草稿是否已保存、哪些内容可以跳过以及提交前需要授权什么。

## 硬约束

- 保留绘画与句子补全两种 `taskType`，不合并、不改变判断条件。
- 保留画布绘制、撤销、重做、清空、本机草稿、离开提醒、字符限制、折叠题、可跳过与授权。
- 保留 `createRelationshipTask` 载荷、幂等键、风险转人工关注、成功/失败埋点与返回逻辑。
- 不修改 JS、API、后端、数据库、本机存储或核心任务语义。
- 不新增图像识别、象征解释、潜意识分析、人格/依恋推断、自动评分、作品分享或云端草稿。

## Frozen direction

方案 A“探索工作纸”：开放任务说明与保存状态 → 绘画画布/连续句子题 → 必要输入 → 授权 → 边界 → 单一提交按钮。

## 状态矩阵

- DrawingEmpty；DrawingWithDraft；SentenceDefault；SentenceAnswered；SavingLocal；LocalSaveError；Submitting；ValidationToast；RiskEscalated；LongContent。
