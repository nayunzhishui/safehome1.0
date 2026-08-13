# 紧急安全指引页 Figma 审核

日期：`2026-08-11`

结论：`pass`

## 复现范围

- `Screen/EmergencyGuide/Default`：`162:1343`，390 × 844，真实滚动内容 + 固定安全行动区。
- `Screen/EmergencyGuide/LongContentSmallScreen`：`162:1346`，320 × 1460，验证窄屏换行和完整内容。
- `SafetyActionRow`：`157:78`，包含 `Priority` 与 `Grounding` 两个变体，开放 `Number`、`Body` 属性。
- 主行动复用现有 `Button / Brand / Default`；次行动复用 `Button / Outline / Default`。

## 审查修正

1. 将接地法变体默认值从错误的 `01` 修正为 `5`。
2. 将现实资源主按钮从橙色 `Primary` 改为冻结要求的森林绿 `Brand`。
3. 将 `SafetyActionRow` 正文改为横向填充、纵向随文字增高，消除 320px 小屏截断。
4. 将小屏能力边界分隔线从 342px 修正为容器宽度 272px。

## Harness

- 字体：仅 `Noto Sans SC Regular / Medium`。
- 颜色：屏幕子树中未发现未绑定的 SOLID 色值。
- 组件：22 个实例；行动行与按钮均复用组件，无页面级复制样式。
- 可读性：正文 14px/22px；说明 12px/18px；按钮高度 44px。
- 状态：仅 Default 与真实 LongContent/SmallScreen；未伪造加载、错误或网络状态。
- 视觉：两张最终截图无文字截断、越界、重叠或残留 placeholder。

## 实现基准

已从 `162:1343` 获取 `get_design_context`。小程序实现必须转换为 WXML/WXSS，并复用项目现有 token；不得引入 React、Tailwind、图片或新增业务能力。
