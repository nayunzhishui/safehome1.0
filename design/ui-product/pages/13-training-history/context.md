# 训练记录页设计上下文

版本：2026-08-11 冻结版

## Goal

让用户清楚看到已经真实完成的练习，并可再次练习或继续分页查看。

## 硬约束

- 保留 `total`、Loading、Error、Empty、List、LoadingMore、LoadMoreError 和 End 状态。
- 保留 `retry`、`copyDiagnostic`、`openCard`、`loadMore`、`goTraining` 事件及 `card_id`。
- 保留 `GET /api/checkins`、登录门禁和诊断信息语义；不修改 JS、API、后端或数据库。
- 不增加连续天数、成就、评分、排名、疗效或完成百分比。
- 正文不小于 28rpx，诊断辅助文字不小于 24rpx，触控不小于 88rpx。

## Frozen direction

方案 A“练习时间记录”：总数作为标题辅助信息，记录使用连续分隔列表；反思原文可读但不夸大；再次练习为每行真实次行动。

