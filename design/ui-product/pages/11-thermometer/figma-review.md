# 情绪温度计页 Figma 审查

结论：`pass`

文件：`8vocq2yUvjQavYpaxGotPs`

## 产物

- Page：`11 Thermometer`（`190:2`）
- Default：`Thermometer/Default`（`190:3`），390×1525
- State Matrix：`Thermometer/State Matrix`（`191:2`）
- 截图：`assets/figma-default-v1.png`
- 截图：`assets/figma-state-matrix-v1.png`

## ImageGen → Figma

- 保留单色竖向温度计、清晰强度数值、加减控制、次级观察区、保存、回执、曲线、记录和边界。
- 去除彩色渐变、高光球体、天气隐喻和数据仪表盘感。
- 输入上限纠正为 40/200；记录行去除假箭头；回执和曲线标记为真实数据容器。
- 字体为 `Noto Sans SC` Regular/Medium，色彩沿用现有变量。

## 状态审查

- 状态板覆盖 Loading、Empty、Error、Saving、Receipt；Default 内包含 SelectedPoint 示例。
- 不增加假数据进度、诊断、筛查、风险分数或自动解释。
- 各状态均能映射现有 `loading`、`saving`、`receipt`、`selectedPoint`、`errorMessage`、`summary` 与 `records`。

## 实现基准

- 页面采用开放分区与细分隔线，不恢复卡片墙。
- 文字至少 12px 短标签、14px 正文，代码映射为 24rpx 与 28rpx。
- 所有主要触控目标映射为至少 88rpx。
