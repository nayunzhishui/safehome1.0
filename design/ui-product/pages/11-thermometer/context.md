# 情绪温度计页设计上下文

版本：2026-08-11 冻结版

## Goal

让家长在低认知带宽下快速记录“此刻强度”，并在需要时补充观察、查看当天变化。

## 核心任务与层级

1. 调整 1–10 强度并记录一次。
2. 可选填写愉悦度、身体唤起、可控感、情绪名称和一句备注。
3. 保存后读取真实回执；查看今日曲线、选中点和当天记录。

## 硬约束

- 保留 `onThermometerTap`、`onThermometerMove`、加减按钮、三个 slider、两个输入事件、保存、回执关闭、训练卡跳转、刷新、曲线点选和重试事件。
- 保留现有 API client 调用、登录门禁、数组字段、回执字段、曲线 canvas 和边界说明。
- 不修改 JS、API、后端、数据库、认证、图表工具或核心业务语义。
- 不把“情绪温度计”改名为“情绪天气”；不增加诊断、筛查、自动解释、风险分数或虚假建议。
- 可见文字不小于 24rpx，正文优先 28rpx；触控目标不小于 88rpx。

## 状态矩阵

- Default、Loading、Saving、Empty、Receipt、SelectedPoint、ReadError/SaveError、LongContent/SmallScreen、LoginRequired。
- Disabled 只对应真实 `saving`；不伪造 Selected、Completed 或训练进度。

## Frozen direction

采用方案 A“安静的纵向温度计”：真实温度计为唯一视觉主角，三个补充维度降为次级观察区；今日曲线和记录使用连续阅读结构，状态反馈优先于装饰。
