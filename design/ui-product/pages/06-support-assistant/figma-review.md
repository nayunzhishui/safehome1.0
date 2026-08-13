# 支持性问答 Figma 视觉审核

审核时间：2026-08-10

## 结论

通过。ImageGen 的“编辑式支持便笺”方向已组件化复现；页面功能仍以现有登录门禁、能力开关、同意、当前会话、1000 字输入、回答与引用为准。

## 组件

- `BoundaryNote`：`99:61`，ConsentPending / Consented 两态。
- `ConversationEntry`：`105:61`，User / Assistant 两态，支持真实引用显隐与引用文本覆盖。
- `QuestionComposer`：`120:69`，Disabled / Ready / Sending / Error 四态。
- 复用既有 `Button` 与 `PageStateInline`，没有复制同类组件。

## 页面状态

- Loading `107:1109`
- ConfigError `107:1111`
- Disabled `107:1113`
- ConsentPending `107:1115`
- Ready `107:1117`
- Sending `107:1119`
- Conversation `107:1121`
- InlineError `107:1123`
- LongContent `107:1125`
- NetworkFailure `107:1127`

## Harness

- 10 个根画板均为 390×844，均开启裁切。
- 字体审计：0 个非 Noto Sans SC 文本。
- 页面实色审计：0 个未绑定 SOLID paint。
- 三个新增组件集实色审计：0 个未绑定 SOLID paint。
- Conversation 与 LongContent 的内容高度分别为 885 和 1057，仅作为页面纵向滚动证据；其他八态均在首屏内完成主要任务。
- 修正了 `ConversationEntry` 与引用组的固定高度，长回答和多条引用不再裁切或与输入区重叠。
- 已对 Conversation `107:1121` 获取 `get_design_context`，作为小程序实现基准。

## 功能边界

- 没有新增聊天历史、跨会话记忆、附件、语音、联网搜索、实时客服、诊断或危机处置控件。
- Disabled 状态不显示假输入框。
- ConsentPending 状态只有真实同意动作，按钮明确写出“AI 辅助处理”，输入与提交保持禁用。
- 引用仅展示后端返回的标题，不伪造链接或跳转。
- 真机、Android/iOS、大字体和读屏继续按总计划统一后置。
