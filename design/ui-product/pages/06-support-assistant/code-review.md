# 支持性问答前端实现与 Loop/Harness 审核

结论：`local_complete_device_deferred`

路由：`pages/support-assistant/index`

Figma：Conversation `107:1121` 及同族十态

## 修改范围

- `apps/miniprogram/pages/support-assistant/index.wxml`
- `apps/miniprogram/pages/support-assistant/index.wxss`
- `index.js`、后端、API、数据库、content、shared 均未修改。

## 功能保护

- 未登录仍由原 `isLoggedIn` 守卫跳转登录，并保留返回本页的 redirect。
- `GET /api/ai-qa/config`、`participant_enabled` 和后端返回的 `boundary_notice` 未变。
- Disabled 状态不渲染输入框，不伪造不可用功能。
- 同意仍调用 `POST /api/consent`，固定 `ai_assistance / 2026.07-consent-v2 / agreed=true`；按钮明确显示“AI 辅助处理”。
- 首次发送仍创建 `participant_support_navigation` 会话，随后调用原消息接口；问题上限仍为 1000 字。
- 消息仍只保存在当前页面内存；没有新增历史、跨会话记忆、附件、语音、搜索、实时客服或诊断能力。
- 回答正文和引用标题继续使用真实 `answer.content`、`answer.citations` 字段。
- `page-state` 的 WXML 属性由错误的 `state/actionText` 对齐为组件真实的 `kind/actionLabel`，只修复状态显示与重试按钮，不改变处理器。

## ImageGen / Figma / 代码映射

| 设计要点 | Figma | 小程序 |
|---|---|---|
| 页面边距 | 24px，顶部 40px | 48rpx，顶部 80rpx |
| 开放式页头 | 12/20/14px | 24/40/28rpx |
| 边界便笺 | 12px 圆角、24px 内边距、无阴影 | 24rpx 圆角、48rpx 内边距、无阴影 |
| 同意动作 | 橙色、明确 AI 辅助处理 | `--safe-orange`，沿用 `enableConsent` |
| 问答记录 | 全宽编辑式条目、分隔线、无气泡 | 原循环与字段，移除左右气泡和头像暗示 |
| 引用 | 回答内脚注式标题列表 | 原 `citations` 循环，仅展示真实标题 |
| 输入区 | 112px 文本区、44px 主按钮 | 224rpx 文本区、88rpx 主按钮 |

## Loop 1：视觉一致性

- ImageGen、Figma 与 WXML/WXSS 的页头、边界、问答、引用和输入顺序一致。
- Figma 十态与三组件集使用 Noto Sans SC，0 个未绑定实色；代码映射到既有 `--safe-*` token。
- 微信开发者工具 Preview 编译通过，包体 1,490,034 bytes，无 WXML/WXSS 编译错误。
- 真机截图按总规则统一后置，本轮不登记 Loop 5 通过。

## Loop 2：UI 细节

- 主要正文 28rpx / 44rpx，辅助文字 24rpx / 36rpx；长文本自然换行。
- 同意和发送按钮最小高度 88rpx，唯一强操作随状态禁用或加载。
- 无渐变、装饰性头像、机器人图标、嵌套卡片和多余阴影。
- 长回答和多条引用在 Figma 中修正为内容自适应，不裁切、不与输入区重叠。

## Loop 3：UX

- 首屏先解释能力与边界，再允许同意和输入，信息层级符合真实操作顺序。
- 未开放状态只说明可替代入口，不显示假输入框。
- 同意按钮显式写出 AI 辅助处理；已同意状态同时使用勾选图形和文字，不只依赖颜色。
- 问答采用“你 / 支持性整理”角色文字，不制造真人在线、机器人陪聊或长期记忆期待。
- 错误分别保留配置重读、同意失败和发送失败的原恢复路径。

## Loop 4：状态

- Figma 覆盖 Loading、ConfigError、Disabled、ConsentPending、Ready、Sending、Conversation、InlineError、LongContent、NetworkFailure。
- 代码由现有 `loading / enabled / consented / sending / messages / error / question` 组合产生同等状态，不新增业务字段。
- Conversation 和 LongContent 使用自然页面滚动；其余主要任务均在 390×844 首屏内。

## Accessibility

- 页面、同意按钮、输入框和发送按钮保留明确 aria-label。
- 加载与错误继续复用 `page-state` 的 `role=status`、`aria-live=polite`。
- 动态问答列表使用 `aria-live=polite`；同意完成同时有图形和文字。
- 触控、对比度、换行和 reduced-motion 自动项通过；读屏、大字体与 Android/iOS 仍待统一真机批次。

## Harness

- 视觉：十个 390×844 状态、字体、token、实色、裁切和长内容审查通过。
- 组件：Figma 新增 `BoundaryNote`、`ConversationEntry`、`QuestionComposer`，复用 Button/PageStateInline；代码继续使用原循环与通用 `page-state`。
- UX：能力边界、同意门禁、错误恢复、触控和非颜色状态线索通过。
- 工程：设计 token、53 页 UI governance、非 UI client、T23 375/430/768/1440 × 100%/200%、truth、Preview 与 `git diff --check` 通过；未新增依赖。

## 待最终批次

- Android/iOS、系统大字体、读屏、弱网、键盘顶起、真实引用数量和长会话滚动。
- 全部页面本地完成后统一合并当时 main，再全量回归并进入真机修正。
