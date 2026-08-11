# 紧急帮助说明页代码 Loop 与 Harness

日期：`2026-08-11`

结论：`awaiting_user_manual_screenshot_review`

## 实现范围

- 修改 `index.wxml`：移除 hero 卡、资源卡片墙和警示卡，改为开放标题、连续资源行、安静边界说明和单一轮廓行动。
- 修改 `index.wxss`：映射 Figma 的字号、行高、间距、颜色、分隔线、按钮尺寸和小屏规则。
- 用户指出的重复粗侧线已替换为 `4rpx` 开放式 `┌` 转角标记；标记只对齐标题，不贯穿正文。
- 未修改 `index.js`、`index.json`；四项资源数据、唯一点击事件和安全指引路由保持原样。

## Loop 1：视觉一致性

- ImageGen、Figma 与 WXML/WXSS 均采用“现实支持索引”，没有恢复卡片墙、阴影、插画或装饰图标。
- Figma 28/16/14/12px 字阶映射为 56/32/28/24rpx；36/22/18px 行高映射为 72/44/36rpx。
- 24px 页面横向边距、24px 区块间距、16px 行内间距和 44px 按钮高度均已映射。
- 主色、正文、分隔线和危险边界均复用 `--experience-*` token，无新增颜色硬编码。
- 微信开发者工具 Preview 编译通过，包体 `1,493,991 bytes`，无 WXML/WXSS 编译错误。
- 用户提供的局部真实页面截图覆盖标题、四项资源与“使用边界”开头；可见区域与 Figma 的层级、角标、换行和间距一致。最终完整页面与真机验收统一后置。

## Loop 2：UI 细节

- 四项资源使用同一行结构；开放转角为 `24rpx × 48rpx`，笔画 `4rpx`，避免原粗竖条的栅栏感。
- 普通内容只使用留白与底部分隔线，无圆角卡片、阴影和嵌套表面。
- 正文使用 `min-width: 0`、`flex: 1` 和强制换行保护；320px Figma 状态已验证长文本不截断。
- 轮廓按钮最小高度 `88rpx`，页面左右边距在窄屏下降为 `40rpx`。
- 小字预算通过：页面无小于 `24rpx` 的文字；`24rpx` 仅用于短标题标记，资源说明和使用边界均为 `28rpx` 正文；无连续三行小字、重复免责声明、机器字段或原始 ISO 时间。

## Loop 3：UX

- 首屏明确说明本页只提供现实支持方向，不提供热线库，也不判断危机。
- 四项资源保持静态说明，不展示箭头、点击态或虚假在线状态。
- 唯一行动仍是“查看紧急安全指引”，保持辅助权重，不与当前内容抢层级。
- 未新增热线、拨号、地图、定位、搜索、联系人、聊天、复制、外链、风险评分、诊断或自动转介。

## Loop 4：真实状态

- 已实现并检查 `Default`、`LongContent/SmallScreen`、按钮 `Pressed`、`ReducedMotion`。
- 页面无数据请求，因此没有伪造 Loading、Empty、Error、Disabled、Selected 或 NetworkFailure。
- 用户局部截图可见区域通过；完整页面、Android/iOS、大字体、读屏与真机安全区仍按总规则统一后置。

## Harness

### 视觉 Harness

本地证据通过：Figma `170:1387` / `170:1389`、设计截图、代码 token/尺寸映射及用户局部截图可见区域一致。

### 组件 Harness

通过：四项资源复用同一 `.resource-row` 结构；按钮复用全局 `safe-outline-button`；未新增重复组件或依赖。

### UX Harness

通过：功能边界、单一行动、触控尺寸、层级、支持性语言和小字预算均符合冻结版。

### 工程 Harness

通过：

- 微信开发者工具 Preview、53 页功能真值、design token、UI governance、non-UI client 与 T23 视觉矩阵通过。
- 页面 JSON、JS、注册表 JSON、Python 脚本语法和 `git diff --check` 通过。
- 页面改动仅涉及 WXML/WXSS；未改后端、API、数据库、content、shared、业务 JS 或新增依赖。

## 当前门禁

- 状态：本地 Loop 1–4 与四类 Harness 已通过，可登记 `done` 并连续进入下一页。
- 完整页面、底部按钮、安全区与 Android/iOS 真机表现纳入全部页面完成后的统一用户验收。
