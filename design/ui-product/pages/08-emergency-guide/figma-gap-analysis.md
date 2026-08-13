# 紧急安全指引页 Figma Gap Analysis

文件：`安心陪伴 UIproduct` / `8vocq2yUvjQavYpaxGotPs`
阶段：P0.a–P0.f 已完成

## 可直接复用

- 既有 Primitive、Semantic、Dimension 三个变量集合；本页不新增 token。
- 既有 `Button` 组件集：主操作复用 Primary，返回首页复用无图标的 Outline/文本化表现。
- 既有 390 × 844 Screens 画板规则、Noto Sans SC 字体体系和 44px 最小触控尺寸。
- 既有语义变量：Canvas、Surface、Primary、Primary text、Secondary text、Border、Danger。

## 代码有、Figma 当前状态账本中缺失

- `SafetyActionRow`：需要同时承载 01–04 两位编号和 5→1 单位编号，支持真实长文本自然换行。
- 紧急安全指引 Default 与 LongContent/SmallScreen 两个页面状态。
- 固定底部行动坞：唯一实心主行动持续可达，同时避免遮挡正文与安全区。
- “重要边界”的低干扰编辑式区块；不使用警告卡片墙。

## 锁定的解决方式

- 新增 `SafetyActionRow` 两类变体：`Kind=Priority`、`Kind=Grounding`，均暴露 `Number` 与 `Body` 文本属性。
- 行组件采用自动布局、底部分隔线、固定编号列和可自适应正文列；不使用独立卡片背景。
- Default 画板宽 390px，高度按真实滚动内容展开；另建 320px 小屏/长内容验证画板。
- 底部行动坞为白色/象牙色表面加上边界线与安全区，不使用玻璃态或渐变。
- Pressed 复用 Button 既有交互状态；ReducedMotion 以规范说明呈现，不伪造独立业务状态。

## 代码与设计冲突及处理

- 当前 WXML 的接地法编号使用 `index + 1`，视觉为 1→5；功能文本和页面标题明确要求 5→1。Figma 按 5→1，后续 WXML 只改显示表达式，不改数组、点击事件或业务语义。
- 当前顶部使用 Hero 卡片，九个步骤均为独立卡片，形成模板化卡片墙；Figma 改为开放编辑式内容与细分隔线。
- 当前主操作位于长页面末尾，紧急情境下发现成本高；Figma 改为固定底部行动坞，但仍调用原有 `openResources`。
- 当前返回首页是等权描边按钮；Figma 降为次级文本操作，但仍调用原有 `goHome`。
- 当前边界文案写“医疗诊断/使用现实资源”，冻结真值采用“临床诊断/立即寻求现实中的专业帮助”；仅做非诊断边界措辞校准，不增加能力。

## 实时复核门禁

2026-08-11 实时复核通过：

- Components 页仍为 `11:3`，Screens 页仍为 `11:4`；本地状态账本有效。
- 3 个变量集合、41 个变量、7 个文字样式、2 个效果样式数量一致。
- `Button 18:59` 可用，当前含 20 个变体。
- Components 与 Screens 均无 `SafetyActionRow` 或紧急安全指引同名节点。
- 文件未订阅外部库。Simple Design System 的 `Text List Item` / `Text Link List Item` 与本项目 token、字体、编号属性和编辑式结构不兼容，不引入。

P0 退出条件已满足，可以创建本地 `SafetyActionRow`。
