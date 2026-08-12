# 三步开始页 Figma 审查

结论：`pass`

文件：`8vocq2yUvjQavYpaxGotPs`

## 产物

- Page：`10 Getting Started`（`187:2`）
- Screen：`Screen/GettingStarted`（`187:3`）
- 通过截图：`assets/figma-default-v2.png`
- 首轮裁切截图保留于：`figma/figma-default-v1.png`

## ImageGen → Figma

- 保留开放式三步骨架、纵向七段观察链、安静边界和上下排列的主次行动。
- 按 390px 宽可滚动画板重建，最终画板为 390×1362px。
- 首轮发现文字层被固定为 20px 高、路径第三项横向裁切；第二轮改为 Hug Content 并压缩路径单元后复查通过。
- 所有中文使用 `Noto Sans SC` Regular/Medium，颜色沿用现有 Figma 变量。

## 功能与适配

- 三步、七段链路、三条理由、三条边界和两个真实行动全部存在。
- 无卡片墙、无重复粗侧线、无伪交互、无进度或结果暗示。
- 路径标签允许两行；正文、链路和边界均无截断、重叠或横向溢出。

## 实现基准

- WXML 采用语义化开放区块和原数组绑定。
- WXSS 映射 24px 页面边距、细分隔线、28rpx 正文和至少 88rpx 触控高度。
- JS、路由、API 和本地状态保持不变。

