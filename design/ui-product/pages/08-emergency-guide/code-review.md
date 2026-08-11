# 紧急安全指引页代码 Loop 与 Harness

日期：`2026-08-11`

结论：`local_pass_device_deferred`

## 实现范围

- 修改 `index.wxml`：开放编辑式结构、01—04 现实行动、真实 5→1 接地顺序、固定安全行动区。
- 修改 `index.wxss`：映射 Figma 的字体、间距、分隔线、森林绿主行动、小屏换行和安全区留白。
- 修改 `index.json`：移除不再使用的 `section-title` 页面依赖。
- 未修改 `index.js`；`supportSteps`、`groundingSteps`、`openResources()`、`goHome()` 及路由语义保持原样。

## Loop 1：视觉一致性

- ImageGen、Figma 与 WXML/WXSS 均采用“安全行动清单”，没有恢复 hero 卡、卡片墙、插画或装饰图标。
- Figma 28/20/14/12px 字阶映射为 56/40/28/24rpx；22px 行高映射为 44rpx。
- 24px 页面横向边距、24px 区块间距、80px 行最小高度和 44px 按钮高度均已映射。
- 主行动使用 `--experience-primary`，危险色仅用于“安全优先”和 112rpx 细线。
- 微信开发者工具 Preview 编译通过，包体 `1,492,220 bytes`，无 WXML/WXSS 编译错误。
- 自动化模拟器截图因开发者工具 9420 WebSocket 拒绝连接而未生成；不把该工具失败冒充页面失败。Figma 最终截图和代码结构/令牌对照已完成，真实设备截图继续按总规则统一后置。

## Loop 2：UI 细节

- 现实行动编号固定为 `01—04`；接地编号由 `{{5 - index}}` 输出 `5—1`。
- 行组件只有底部分隔线，无圆角卡片、阴影和嵌套表面。
- 正文使用 `min-width: 0`、`flex: 1` 与换行策略；Figma 320px 状态已验证长文本不截断。
- 固定行动区预留 `320rpx + safe-area` 内容空间，避免遮挡最后一段。

## Loop 3：UX

- 页面首屏先给出“先找现实帮助”，现实资源按钮始终可达。
- 接地法明确位于现实行动之后，不暗示其可以替代线下帮助。
- 只有一个实心主行动；“回到首页”为轮廓次行动。
- 没有新增热线号码、拨号、定位、报警、聊天、风险评分、诊断或自动转介。

## Loop 4：真实状态

- 已实现并检查 `Default`、`LongContent/SmallScreen`、按钮 `Pressed`、`ReducedMotion`。
- 页面无数据请求，因此没有伪造 Loading、Empty、Error、Disabled、Selected 或 NetworkFailure。
- 真机、大字体、读屏和 Android/iOS 安全区在全部页面本地完成后统一验收。

## Harness

### 视觉 Harness

通过：Figma `162:1343` / `162:1346`、最终截图和代码 token/尺寸映射一致；未新增图像资产。

### 组件 Harness

通过：两组行动复用同一 `.action-row` 结构与样式；按钮复用全局 `safe-primary-button` / `safe-outline-button`；删除未使用页面组件声明。

### UX Harness

通过：主任务、点击区域、层级、可读性、能力边界和安全语言均符合冻结版。

### 工程 Harness

通过：

- 功能真值：53 页、0 未解析、源码漂移已更新。
- design token、53 页 UI governance、非 UI client、T23 视觉矩阵通过。
- `ui_product_loop.py harness`、JSON 解析、JS 语法、`git diff --check` 通过。
- 变更仅在小程序页面、设计记录和三份强制文档范围；无后端、API、数据库、content、shared 或新增依赖变更。

## 已知后置项

- 本页真机截图、系统大字体、读屏、Android/iOS 与安全区人工检查，统一进入最终真机批次。
