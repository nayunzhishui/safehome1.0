# 关系探索试点页设计上下文

版本：2026-08-11 冻结版

## Goal

让授权学生清楚知道自己是否能参加、当前只需做哪一步，以及之后有哪些真实入口；未报名用户能理解研究用途后自主选择。

## 硬约束

- 保留 `requireLogin`、`getShowcaseAccess`、学生/管理员角色门禁、`enrollment`、`growth` 和真实五阶段状态。
- 保留 `toggleConsent`、`enroll`、`runPrimaryAction`、`runSecondaryAction` 与所有现有路由、埋点。
- 保留报名关联最近关系探索测评、逐行研究数据不可见、非诊断边界。
- 不修改 JS、API、后端、数据库、角色或报名语义。
- 不增加完成百分比、排行榜、关系能力评分、匹配度、社交分享、聊天或 AI 建议。

## Frozen direction

方案 A“竹节路径手帐”：开放页头 → 当前状态/报名 → 单一当前行动 → 五阶段竹节路径 → 其它入口连续行 → 非诊断边界。

## 状态矩阵

- Loading；RoleBlocked；EnrollmentRequired；Submitting；Enrolled current path；Error；LongContent。
