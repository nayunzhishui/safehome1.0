# 项目详情页设计上下文

版本：2026-08-11 冻结版

## Goal

让参与者先看清项目边界和参加条件，再选择真实小节、完成练习、保存本机草稿或正式提交；研究者能明确识别只读预览。

## 功能真值

- 数据：`program`、`sessions`、`selectedSession`、`measurementPlan`、`submittedEntries`。
- 真实事件：`selectSession`、`onDraftInput`、`onReflectionInput`、`saveDraft`、两个不适 slider、两个 checkbox、`submitEntry`、`retryLoad`。
- 接口：`GET /api/programs/:id/entries`、`POST /api/programs/:id/entries`；项目读取继续复用现有 client。
- 本地语义：草稿按项目和小节保存在本机，正式提交成功后删除对应草稿。

## 硬约束

- 不修改 JS、API、后端、数据库、授权、审核、草稿或提交语义。
- 保留项目协议版本、目标构念、参与/排除条件、安全门槛、替代方案、解释与临床边界。
- 保留测量节奏、真实小节切换、练习步骤、书写/反思、完成标准、停止提示、提交状态和本人历史。
- 研究者预览必须关闭所有填写、保存和提交控件。
- 不增加折叠事件、完成进度、评分、推荐、分享、收藏、课程购买或 AI 自动分析。

## Frozen direction

方案 A“练习协议手帐”：开放项目页头 → 参与前核对 → 阶段记录节奏 → 小节索引 → 当前练习 → 提交核对 → 我的提交记录。正文优先，胶囊只保留真实短状态。

## 状态矩阵

- Default participant；Preview read-only；Loading；Load error；Missing；Submitting；Submit success；Submit error；Long content。
