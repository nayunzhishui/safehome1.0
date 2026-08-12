# 关系阶段性报告页设计上下文

版本：2026-08-11 冻结版

## Goal

让参与者先看懂报告处于什么阶段、当前阶段性解释是什么，再按需核对数据与假设；避免把参考位置呈现为诊断、能力排名或固定关系标签。

## 硬约束

- 保留 `getRelationshipReport`、人工核对未发送分支、四步状态轨迹与注意提示。
- 保留 `feedback-rating`、机制假设三选一核对、动态记录、讨论问题、项目任务与脱敏长图导出。
- 保留保存假设反馈、报告评价与导出埋点的全部事件、字段和状态。
- 不修改 JS、API、后端、数据库、报告状态或研究流程语义。
- 不新增关系评分、匹配度、能力等级、人格标签、自动诊断、分享排名或虚构维度。

## Frozen direction

方案 A“研究手记报告”：开放页头与状态轨迹 → 阶段性解释 → 用户核对 → 数据轮廓 → 矛盾与假设 → 连续记录 → 讨论与任务 → 边界和脱敏导出。

## 状态矩阵

- Loading；LoadError；DeliveryPending；Delivered；AttentionNotice；SavingFeedback；Exporting；LongContent。
