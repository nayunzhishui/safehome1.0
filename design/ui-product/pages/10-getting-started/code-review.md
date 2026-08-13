# 三步开始页代码 Loop 与 Harness

日期：`2026-08-11`

结论：`local_pass_device_acceptance_deferred`

## 实现范围

- 仅修改 `index.wxml` 与 `index.wxss`。
- 页面从七组卡片重排为 01–03 开放式步骤，记录理由并入第一步，七段链路并入第二步，流程提示并入第三步。
- 按钮复用全局 `safe-primary-button` 与 `safe-outline-button`。
- `index.js`、`index.json`、`startDiary`、`openTraining` 和全部数据数组保持原样。

## Loop 1：视觉一致性

- ImageGen、Figma 与代码均采用“从一件具体小事开始”的展开式三步结构。
- 代码映射 Figma 的松柏绿、细分隔线、开放区块、浅橙边界和上下主次按钮。
- 未恢复卡片墙、粗侧边线、双主按钮或两列链路。

## Loop 2：UI 细节

- 正文为 28–30rpx，路径短标签为 24rpx；没有低于 24rpx 的小字。
- 主次按钮均不低于 88rpx，具有按下反馈。
- 320–360px 小屏通过媒体规则缩小标题与数字列，内容列使用 `minmax(0, 1fr)` 防止溢出。
- WXSS 未使用通配选择器，避免历史真机编译的 `token *` 问题。

## Loop 3：UX

- 首屏明确核心任务，唯一实心主行动是“记录一次”。
- 七段链路按 DOM 自上而下阅读，不表现为可点击或完成状态。
- 三条边界集中显示一次，未拆成多段脚注。

## Loop 4：页面状态

- 本页无接口和异步数据，只存在 Default、LongContent/SmallScreen 与按钮 Pressed。
- 未伪造 Loading、Empty、Error、Disabled、Selected 或 NetworkFailure。
- 真机、大字体和系统安全区统一留待全部页面本地完成后的用户验收。

## Harness

- 视觉：Figma `187:3` 第二轮截图通过。
- 组件：按钮复用全局样式；步骤、理由、链路和边界均由真实数组循环渲染。
- UX：信息层级、单一主行动、触控尺寸和支持性语言通过。
- 工程：53 页功能真值检查与 UI governance 通过；微信开发者工具 Preview 编译通过，包体 `1,494,761 bytes`；`git diff --check` 与 WXSS 通配选择器检查通过。
- 自动化烟测未运行：本机缺少已声明测试工具 `miniprogram-automator`；不新增依赖，Preview 编译已独立通过。
- 未修改后端、API、数据库、content、shared、认证或核心业务语义。

## 当前门禁

- 本地 Loop 1–4 与四类 Harness 通过，可登记 `done` 并进入下一页。
- 用户统一真机验收继续延期到全部页面本地完成之后。
