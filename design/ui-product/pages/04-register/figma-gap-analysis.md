# 注册页 Figma Gap Analysis

状态：`phase0_passed`
日期：2026-08-10
目标文件：`安心陪伴 UIproduct`

## P0.a 代码真值

- 注册页角色字段使用微信小程序原生 `picker`，默认值为“家长”，只允许“家长 / 学生”。
- 页面没有独立 Select 代码组件；角色选择样式当前由页面 WXML/WXSS 承载。
- 本轮不改变 picker、事件、字段值、校验、API 或跳转。

## P0.b Figma 现状

- 已有 3 个变量集合、41 个变量、7 个文字样式和 2 个阴影样式，可覆盖本页。
- 已有 `AuthField` 五状态和 `Button` 四风格四状态，可直接复用。
- 已有 `__Icon/ChevronRight`，但没有向下选择图标；禁止通过旋转线条或右箭头近似。
- 没有 `SelectField`，普通输入组件无法稳定表达尾部选择提示。

## P0.c 外部库

- 当前文件未订阅外部库。
- 在 Simple Design System 中搜索 `select field dropdown input` 无匹配结果。
- 不引入 Material 或其他外部组件，避免 token、圆角和视觉语言分叉。

## P0.d 冻结范围

- 新增私有原子：`__Icon/ChevronDown`，24 × 24，使用 SVG 路径创建并绑定现有文字次级色。
- 新增组件集：`SelectField`。
- 状态：Default、Focused、Error、Disabled，共 4 个变体。
- 组件属性：Label、Value、Message、Icon；不增加新 token、样式、页面或交互。

## P0.e 映射与冲突处理

| 代码 | Figma | 处理 |
|---|---|---|
| 原生 picker | SelectField 视觉组件 | 仅作为设计表达，代码继续使用原生 picker |
| 默认“家长” | Default/Value=家长 | 保持一致 |
| 选中“学生” | 实例文本覆盖为“学生” | 不新增业务状态 |
| 页面整体错误 | 独立状态消息 | 不把 API 错误伪装为角色字段错误 |
| 无向下图标资产 | 私有 ChevronDown | 仅补足选择 affordance，不进入业务资产 |

## P0.f 结论

- 需要新增 `SelectField`，否则角色字段会与可输入字段混淆。
- 现有 Figma foundations 足够，不修改 token。
- 小程序没有独立 Select 代码组件，暂不建立 Code Connect；后续若抽成公共 WXML 组件再补映射。
- Phase 0 无未决功能冲突，可以进入组件创建。
