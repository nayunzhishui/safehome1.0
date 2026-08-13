# 训练页设计上下文

版本：2026-08-11 冻结版

## Goal

让家长快速找到“今天先练什么”，同时仍能进入个性化方案、项目测试、关系试点、3 天计划和完整训练库。

## 信息优先级

1. 页面方向与今天可做的小练习。
2. 最近推荐（存在时）或觉察—稳定—回应起步路径。
3. 3 天轻量计划与条件试点。
4. 全部训练库与阶段训练卡。

## 硬约束

- 保留全部现有条件字段、按钮事件、动态文案、卡片 ID、tags 和路由。
- 保留 `getShowcaseAccess`、`getTrainingPlan`、本地推荐/计划缓存和登录门禁语义。
- 不修改 JS、API、后端、数据库、content、shared、训练卡组件接口或核心业务语义。
- 不新增进度、打卡、课程状态、自动推荐理由、疗效、诊断或风险评分。
- 正文不小于 28rpx；短标签不小于 24rpx；主要触控不小于 88rpx。

## 状态矩阵

- Default、RelationshipPilotAvailable、LatestRecommendation、ThreeDayPlanCollapsed/Expanded、LibraryCollapsed/Expanded、LoginRequired。
- 页面没有独立 Loading/Error WXML，不伪造新状态。

## Frozen direction

采用方案 A“训练编辑目录”：开放页头、轻量入口索引、一个重点推荐区、可展开计划和连续训练目录；以细分隔线与留白替代卡片墙。
