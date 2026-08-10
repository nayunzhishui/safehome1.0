# 消息页 Figma 组件差距分析

文件：`安心陪伴 UIproduct`
File key：`8vocq2yUvjQavYpaxGotPs`
目标页：`03 Screens`

## 已复用

- 现有 Semantic/Dimension Variables：Canvas、Surface、Subtle、Ink、Muted、Action、Line、Spacing、Radius。
- `PageStateInline`：覆盖 Loading、Empty、Error、NetworkFailure。
- 现有 Noto Sans SC 字体约定与 390 × 844 小程序画板。

## 本页合法新增

新增 `MessageRow` 组件集 `88:57`，原因是消息列表行同时具有稳定字段结构和三种真实状态，现有 `EntryRow`、`TimelineRecord` 都不能表达撤回、版本与已读语义。

组件轴：

- `State=Unread`：`87:61`
- `State=Read`：`87:72`
- `State=Withdrawn`：`87:83`

组件属性：

- Title `Title#88:0`
- Body `Body#88:4`
- Meta `Meta#88:8`
- Status `Status#88:12`
- Show Divider `Show Divider#88:16`

没有把头像、图标、来源类型或消息类别做成新轴；代码没有这些交互或视觉语义。

## 不新增

- 不创建筛选器、Tab、搜索、分页、全部已读、聊天气泡或回复组件。
- 不为底部边界说明创建新组件；它是本页低频静态结构。
- 不创建新的全局变量、文字样式或阴影。

## 代码映射

- Figma `MessageRow` 对应当前 `button.message-row` 结构；代码继续使用真实 WXML 循环和 `status-pill`，不新增抽象组件文件。
- Figma `PageStateInline` 对应已有 `/components/page-state/index`。
- Figma 诊断块对应现有 `.diagnostic-card` 与 `copyDiagnostic`，只调整视觉。

