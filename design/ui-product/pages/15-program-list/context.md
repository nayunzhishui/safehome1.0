# 项目测试列表页设计上下文

版本：2026-08-11 冻结版

## Goal

让用户选择真实可用或获准预览的项目，同时清楚区分展示开放、已批准试点和待三方审核。

## 硬约束

- 保留 `previewMode`、`programs`、`availability`、`boundaryNotice`、Loading、Error、Empty 和待审核数量。
- 保留项目 ID、preview_only、openProgram 与原跳转；不修改 JS、API、后端、数据库或审核语义。
- 待审核项目不得表现为正式课程；不增加报名、收藏、进度、评分、价格或推荐排序。
- 正文不小于 28rpx，短标签不小于 24rpx，整行触控不小于 88rpx。

## Frozen direction

方案 A“项目审阅目录”：开放页头、醒目但克制的研究者预览边界、连续项目目录行和独立状态区。
