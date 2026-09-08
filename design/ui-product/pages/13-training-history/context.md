# 训练记录页设计上下文

## UIproduct2 冻结（2026-09-08）

训练记录：总次数独立状态行，条目采用开放纵向列表；反思原文为阅读区，再次练习为次行动，分页和失败恢复不变。

采用清朗青瓷；30rpx正文、26rpx元数据、44rpx标题、96rpx主触控。先Figma后前端，不新增业务功能，不以颜色暗示疗效，最终全页检查与用户验收待完成。


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
