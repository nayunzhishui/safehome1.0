# 紧急帮助说明页 Figma 审查

结论：`pass`

文件：`8vocq2yUvjQavYpaxGotPs`

## 产物

- `ResourceChannelRow`：`169:75`
- `EmergencyResources/Default`：`170:1387`
- `EmergencyResources/LongContentSmallScreen`：`170:1389`
- 截图：`assets/figma-default.png`
- 截图：`assets/figma-long-content-small-screen.png`

## ImageGen → Figma

- 保留开放标题、连续资源索引、安静能力边界和轮廓辅助按钮。
- 没有复刻概念图过大的标题；采用项目 `Display/Page` 28/36，默认首屏可以看到多个资源方向。
- 根据用户复核，将重复粗竖条替换为 2px 开放 `┌` 形编辑角标；角标只对齐标题，不贯穿正文，降低模板化和流程暗示。
- 所有文字使用 `Noto Sans SC` Regular/Medium；色彩、间距、圆角全部复用本地变量。

## 功能真值

- 四条资源标题、正文和顺序逐字核对通过。
- `ResourceChannelRow` 仅暴露 `Title`、`Body`，没有点击、图标、箭头或交互状态。
- 唯一按钮保持“查看紧急安全指引”，使用本地 `Button / Outline / Default` 且关闭图标。
- 未新增热线、拨号、地图、定位、机构搜索、联系人、聊天、在线状态、复制、外链、风险评分、诊断或自动转介。

## 结构与适配

- Default：390×844，内容宽 342，左右边距 24，内容高度 751，完整落在视口内。
- LongContentSmallScreen：320×897，内容宽 280；第三条长正文自适应为 3 行，组件高度由 91 增至 113，无截断和重叠。
- 轮廓按钮在两种状态均为 44px 高，对应小程序 88rpx 最小触控区。
- 两个状态均无 placeholder、无 raw solid paint、无假 Loading/Empty/Error 状态。

## Harness

- 视觉：层级、留白、标题、角标、分隔线和按钮权重通过。
- 组件：四条资源均为 `ResourceChannelRow` 实例，无重复手绘分叉。
- UX：静态内容不呈现点击暗示；唯一辅助动作清楚。
- 工程映射：设计只要求 WXML/WXSS 变化，JS、数组、事件、路由、API 与后端保持不变。

## 实现基准

`get_design_context` 已从 `170:1387` 获取。前端实现应转换为现有 WXML/WXSS，不引入 React、Tailwind、远程 SVG 或新依赖。
