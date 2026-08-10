# 消息页 Figma 视觉审核

结论：`pass_for_frontend_implementation`
文件：<https://www.figma.com/design/8vocq2yUvjQavYpaxGotPs>

## 组件审核

- `MessageRow` 组件集：`88:57`，3 个状态、5 个内容属性。
- 结构均使用 Auto Layout；列表实例可随标题、正文和元信息增高。
- 未读由短线、标题字重和文字状态共同表达；已读降级；撤回使用 Subtle/Muted。
- 组件说明明确禁止回复、删除、筛选和全部已读。
- 自动审计：Noto Sans SC 以外字体 0；未绑定的实色 fill/stroke 0。

## 页面状态

| 状态 | Node ID | 审核结论 |
|---|---|---|
| Default | `90:1034` | 三种消息状态、来源、时间和版本完整 |
| Loading | `90:1077` | 复用真实加载文案，无虚假进度 |
| Empty | `90:1090` | 仅说明后续补充会出现，无多余入口 |
| Error | `90:1103` | 重试和诊断复制均可见 |
| LoginRequired | `90:1119` | 恢复动作改为去登录，保留诊断证据 |
| LongContent | `90:1135` | 长标题与正文自然增高，无固定高度裁切 |
| NetworkFailure | `90:1178` | 明确网络原因、重试与诊断复制 |

七个画板均为 390 × 844；内容高度 364–668px，首屏无越界。

## ImageGen → Figma 对照

- 保留开放式标题、连续列表、分隔线、未读短线和弱边界说明。
- 按冻结规格把 ImageGen 偏大的内容标题校正为 28/36。
- Figma 使用真实组件与 Auto Layout，消除首稿固定高列表的大空白。
- 概念稿中的三条合成消息逐项复现；Figma 另补齐六类非默认状态。
- 允许差异：Figma 使用现有 `PageStateInline` 的错误色与操作结构，以保持全项目状态一致。

## 实现基准

`get_design_context(90:1034)` 已确认：24px 页面边距、32px区块间距、16px 列表圆角、20px 行内边距、16/23 标题、14/22 正文、12/18 元信息和状态。前端应转换为当前小程序的 WXML/WXSS 与 rpx，不引入 React/Tailwind。

