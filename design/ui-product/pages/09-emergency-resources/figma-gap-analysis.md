# 紧急帮助说明页 Figma Gap Analysis

日期：`2026-08-11`

文件：`8vocq2yUvjQavYpaxGotPs`

## P0.a 代码真值

- 本页只有四条本地静态资源说明与一个 `goGuide` 跳转。
- 需要的视觉构件：开放标题、非交互资源行、能力边界、轮廓按钮。
- 产品字体：小程序系统无衬线；Figma 已冻结使用 `Noto Sans SC` 映射中文排版。
- 页面没有图片、远程图标或需导入的位图资产。

## P0.b Figma 现状

- 已有 Primitive、Semantic、Dimension 三个变量集合，共 41 个变量。
- 已有 7 个文字样式与 2 个阴影样式；本页复用 `Display/Page`、`Title/Item`、`Body/Default`、`Caption/Default`、`Label/Action`。
- 已有 `Button` 组件集；底部操作复用 `Style=Outline, State=Default`（`146:69`）。
- 已有 `SafetyActionRow`，但它承担编号安全步骤语义；本页资源条目不允许编号或流程暗示，因此不能误用。
- `EmergencyGuide/Default` 已验证相同内容宽度 342px、左右边距 24px 和开放式边界表达，可作为相邻页面版式基准。

## P0.c 复用搜索

- 代码库没有与本页所需组件对应的 Code Connect 文件。
- 设计系统搜索 `resource row support channel list item` 无结果。
- `get_libraries` 本轮出现一次连接层传输错误；不影响本地组件、变量和样式读取，也不影响空搜索结论。未据此虚构外部组件。

## P0.d v1 范围

- 新建一个本地非变体组件：`ResourceChannelRow`。
- 暴露两个 TEXT 属性：`Title`、`Body`。
- 新建两个页面状态：`EmergencyResources/Default`、`EmergencyResources/LongContentSmallScreen`。
- 复用本地轮廓按钮，不新增按钮变体、图标或页面状态。

## P0.e 映射与冲突

| 代码/需求 | Figma 映射 | 结论 |
| --- | --- | --- |
| 四条静态资源说明 | `ResourceChannelRow` 四个实例 | 新建，避免假点击 |
| 森林绿静态识别线 | `Semantic/color/action/primary` | 复用 |
| 标题与正文 | 现有文字样式与语义文本色 | 复用 |
| 分隔线 | `Semantic/color/border/default` | 复用 |
| 查看紧急安全指引 | `Button / Outline / Default` | 复用 |
| 资源条目是否复用 SafetyActionRow | 编号/接地步骤语义冲突 | 不复用、不包装 |

没有代码与 Figma token 值冲突；代码功能真值优先，Figma 仅扩展缺失的静态资源行。

## P0.f Gap 结论

- Code 有、Figma 无：`ResourceChannelRow`。
- Figma 有、可直接复用：全部基础 token、文字样式、轮廓按钮、相邻安全页的内容网格。
- Figma 有、但本页禁用：`SafetyActionRow`、卡片类组件、图标组件。
- 无需新增变量、样式、远程资产或依赖；按最小改动进入组件和页面组装。
