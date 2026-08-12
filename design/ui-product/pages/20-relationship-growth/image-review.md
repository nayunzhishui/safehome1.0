# 关系探索成长记录页 ImageGen 审查

采用稿：`assets/imagegen-curve-v1.png`

结论：`pass_with_figma_corrections`

- 通过：开放页头、数字摘要带、四栏导航、两层真实筛选、单指标曲线、连续时间线和末端三项动作层级清楚。
- 删除：页面内返回箭头与系统导航；小程序导航栏由真实环境提供。
- 纠正：8/3/2、日期、98 题、互动次数、趋势点与说明均为示意；Figma 只用于长内容和图表布局，代码继续绑定真实 `growth` 数据。
- 纠正：筛选分组严格来自 `curveGroups`，指标严格来自 `selectedMetrics`；没有固定三组或固定指标的业务假设。
- 纠正：曲线说明使用现有 `trendText`，不得根据斜率增加“改善”“退步”或疗效结论。
- 补齐：Figma 还需建立 Timeline、Feedback、Records 与状态矩阵，覆盖研究者/系统/本人来源、报名门槛和草稿保存。
- 状态必须覆盖 Redirecting、Loading、LoadError、CurveWithData、CurveInsufficient、TimelineEmpty、FeedbackEmpty、RecordGate、WeeklyExpanded、EventExpanded、DraftRestored、SlowSaving、SavingSuccess、SavingError、LongContent。
