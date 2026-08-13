# 关系探索成长记录页设计上下文

版本：2026-08-11 冻结版

## Goal

帮助用户按指标与事件回顾阶段变化，并随时补充真实记录；明确不同指标不可合并，趋势不等于疗效或稳定结论。

## 硬约束

- 保留非 `detail=1` 时重定向统一 `growth-dashboard` 的逻辑。
- 保留曲线、时间线、阶段反馈、补充记录四栏与全部筛选、空状态、画布折线和趋势说明。
- 保留研究者补充、系统汇总、用户原话三种来源分离及仅本人可见语义。
- 保留报名门槛、本周表单、关键事件、本机草稿、慢网络提示、幂等提交和两个保存接口。
- 不修改 JS、API、后端、数据库、导航或核心业务语义。
- 不新增总分、疗效百分比、排名、连续打卡奖励、AI 归因、诊断或人格结论。

## Frozen direction

方案 A“成长记录册”：开放页头 → 三项简洁摘要 → 四栏导航 → 当前栏目开放内容 → 单一主要记录动作与辅助入口。

## 状态矩阵

- Redirecting；Loading；LoadError；CurveWithData；CurveInsufficient；TimelineEmpty；FeedbackEmpty；RecordGate；WeeklyExpanded；EventExpanded；DraftRestored；SlowSaving；SavingSuccess；SavingError；LongContent。
