# 首页 Figma 组件化复现规格

状态：`figma_ready_code_blocked_by_recent_record_dependency`
页面：`pages/home/index`
视觉基准：方案 A“编辑手帐”
功能基准：`design/function-truth-table.md`
ImageGen：`C:/Users/32257/.codex/generated_images/019fe695-ee6b-7143-9310-0612b3afeb40/exec-1185a562-53e9-40b1-b894-c39c414dbadd.png`

本规格已在 Figma 中完成组件化复现与视觉审查；它仍不授权跳过“最近记录”真实页面依赖直接修改首页前端。

Figma 结果：

- 文件：`https://www.figma.com/design/8vocq2yUvjQavYpaxGotPs`
- 首页状态：Default `30:2`、Loading `34:147`、Empty `34:175`、Error `34:203`、LongContent `34:231`、NetworkFailure `34:259`
- QA：`39:2`
- 设计系统：3 个变量集合、41 个变量、7 个文本样式、2 个阴影样式、8 个组件集、37 个变体、10 个私有图标
- 当前门禁：首页代码实现前，先按单页流程完成“最近记录”真实页面；继续复用 `GET /api/diaries`，不改后端。

## P0 Phase 0 Checklist：Discovery

- `P0.a` 已读取首页 WXML、WXSS、JS、JSON、公共 `app.wxss`、`journey-action-card`、`section-title`、体验 token 和功能真值表。
- `P0.b` 已检查新文件：仅有空白 `Page 1`（ID `0:1`），0 个节点、0 个本地变量、0 个样式、0 个组件。
- `P0.c` 已检查：仓库没有 Code Connect 文件，目标文件没有已添加库；可用社区库仅有 Material、Simple Design System 与 Apple 平台库，不符合本项目中文小程序品牌语义，均不采用。
- `P0.d` 首页 v1 范围锁定为本文件列出的变量、组件、状态和单张 390px 设计稿。
- `P0.e` 代码与方案 A 的冲突已记录在“差异处理”。
- `P0.f` 已完成 gap analysis：目标文件无可复用设计系统，首页应按本规格建立本地 Variables、Styles 与 Components；设计系统搜索 `button`、`list`、`background`、`space` 均为空。

Figma 文件：`https://www.figma.com/design/8vocq2yUvjQavYpaxGotPs`（fileKey `8vocq2yUvjQavYpaxGotPs`）。

Phase 0 已退出：用户确认 Figma 使用 `Noto Sans SC`，代码继续保留原字体栈。

## 1. 页面任务与固定模块

唯一主任务：根据真实 `GET /api/journey/today` 结果继续“今天的一小步”。

模块顺序不可变化：

1. 顶栏与消息；
2. 情绪温度计；
3. 测一测、情绪日记；
4. 今天的一小步；
5. 如何开始；
6. 更多：支持性反馈、训练中心、人工支持；
7. 最近记录；
8. 阶段性反馈；
9. 条件式开发入口；
10. 系统 tabBar。

禁止在 Figma 中加入天气选择、历史反馈读取、即时客服、虚构进度、诊断结论或新业务入口。

## 2. Figma 文件结构

文件名：`安心陪伴 UIproduct`

Figma Pages：

1. `00 Cover`
2. `01 Foundations`
3. `02 Components`
4. `03 Screens`
5. `99 QA`

首页顶层 Frame：`Screen/Home/Default`，尺寸 `390 × 844`，纵向滚动内容，裁切关闭；另建立状态 Frame：

- `Screen/Home/Loading`
- `Screen/Home/Empty`
- `Screen/Home/Error`
- `Screen/Home/LongContent`
- `Screen/Home/NetworkFailure`

状态 Frame 只改变真实状态内容，不改变模块顺序。

## 3. Variables 与代码来源

### 3.1 Collection：`Primitive`

| Variable | Value | 来源 |
|---|---:|---|
| `neutral/0` | `#FFFFFF` | `experience-tokens.json` surface |
| `neutral/50` | `#F7F8F5` | canvas |
| `neutral/100` | `#F2F4F0` | `app.wxss --safe-bg-soft` |
| `neutral/300` | `#DFE5DC` | line |
| `neutral/600` | `#68736D` | muted |
| `neutral/900` | `#202622` | ink |
| `green/100` | `#E8F0EA` | `app.wxss --safe-primary-soft` |
| `green/500` | `#4F7C6B` | primary |
| `green/700` | `#2F5B4D` | primary deep |
| `green/800` | `#174B38` | 方案 A 主行动深底，仅 Figma 候选，不回写全局 token |
| `orange/500` | `#D98243` | `app.wxss --safe-orange` |
| `warning/600` | `#B86A24` | warning |
| `danger/600` | `#A5453F` | danger |

`green/800` 是方案 A 为主行动提出的局部候选值。代码实现若需使用，只允许写在首页作用域；不得修改 `shared/design/experience-tokens.json`，直到完成全局影响审查。

### 3.2 Collection：`Semantic`

所有 Semantic 变量必须 alias Primitive，禁止复制色值：

| Variable | Alias | Scope |
|---|---|---|
| `color/bg/canvas` | `neutral/50` | FRAME_FILL |
| `color/bg/surface` | `neutral/0` | FRAME_FILL, SHAPE_FILL |
| `color/bg/subtle` | `neutral/100` | FRAME_FILL, SHAPE_FILL |
| `color/bg/action` | `green/800` | FRAME_FILL, SHAPE_FILL |
| `color/text/primary` | `neutral/900` | TEXT_FILL |
| `color/text/secondary` | `neutral/600` | TEXT_FILL |
| `color/text/inverse` | `neutral/0` | TEXT_FILL |
| `color/text/action` | `green/700` | TEXT_FILL |
| `color/border/default` | `neutral/300` | STROKE_COLOR |
| `color/action/primary` | `green/500` | FRAME_FILL, SHAPE_FILL |
| `color/action/accent` | `orange/500` | FRAME_FILL, SHAPE_FILL |
| `color/status/danger` | `danger/600` | TEXT_FILL, STROKE_COLOR |

### 3.3 Collection：`Dimension`

| Variable | px | Scope |
|---|---:|---|
| `space/2xs` | 4 | GAP |
| `space/xs` | 8 | GAP |
| `space/sm` | 12 | GAP |
| `space/md` | 16 | GAP |
| `space/lg` | 20 | GAP |
| `space/xl` | 24 | GAP |
| `space/2xl` | 32 | GAP |
| `space/3xl` | 40 | GAP |
| `radius/sm` | 8 | CORNER_RADIUS |
| `radius/md` | 16 | CORNER_RADIUS |
| `radius/lg` | 20 | CORNER_RADIUS |
| `radius/full` | 999 | CORNER_RADIUS |
| `size/touch/min` | 44 | WIDTH_HEIGHT |
| `size/icon/sm` | 16 | WIDTH_HEIGHT |
| `size/icon/md` | 20 | WIDTH_HEIGHT |
| `size/icon/lg` | 24 | WIDTH_HEIGHT |

所有变量显式设置 WEB code syntax；颜色使用 `var(--safe-*)`，没有现成 CSS 变量的候选值标记 `figma-only-candidate`，不得伪造代码映射。

## 4. Typography

产品字体：代码侧为 `PingFang SC`，Windows 回退为 `Microsoft YaHei`。Figma 实测两者均不可用；用户已确认 Figma 使用 `Noto Sans SC Regular/Medium/Bold`，代码仍保留原字体栈，不修改全局字体。

| Text Style | Size/Line | Weight | 用途 |
|---|---|---:|---|
| `Display/Page` | 28/36 | 600 | “安心陪伴” |
| `Title/Section` | 20/28 | 600 | 最近记录、阶段性反馈 |
| `Title/Action` | 22/30 | 600 | 今天的一小步标题 |
| `Title/Item` | 16/22 | 600 | 入口标题 |
| `Body/Default` | 14/22 | 400 | 正文 |
| `Caption/Default` | 12/18 | 400 | 辅助信息下限 |
| `Label/Action` | 14/20 | 600 | 按钮与操作文字 |

## 5. 组件范围与变体

组件全部放在 `02 Components`，先建变量和样式，再逐个创建。

### `Button`

- Properties：`Style=Primary|Secondary|Text`、`State=Default|Pressed|Disabled|Loading`、`Label` TEXT、`Icon` BOOLEAN。
- 高度至少 44px；Primary 仅用于当前页唯一主行动。
- 首页主按钮使用 `Style=Primary`，陶土橙底；普通行操作使用 Text。

### `IconButton`

- Properties：`Icon=Bell`、`State=Default|Pressed`、`Badge=On|Off`。
- 44×44px 触控区域，图标 20px；铃铛与红点不依赖 emoji。

### `EntryRow`

- Properties：`Kind=Thermometer|Standard|Summary`、`Title`、`Subtitle`、`Meta`、`Icon`、`ShowDivider`。
- 对应情绪温度计、更多列表、最近记录和阶段反馈摘要。
- 默认开放式排版，分隔线代替卡片阴影。

### `DualEntry`

- Properties：`Title`、`Subtitle`、`Accent=On|Off`。
- 两个实例并排：测一测、情绪日记；容器不使用独立圆角卡片。

### `JourneyActionCard`

- Properties：`State=Ready|Loading|Error|Paused|Completed|NotDue|AuthRequired|ProtectionGate`、`Title`、`Description`、`Meta`、`ButtonLabel`、`Boundary=On|Off`。
- 唯一强视觉容器，背景 `color/bg/action`；Error 和保护门禁不得使用普通成功样式。
- Loading 必须有骨架和读屏状态；Error 必须提供“重新读取”。

### `SectionHeading`

- Properties：`Title`、`ActionLabel`、`ShowAction`。
- 使用文字和细线建立层级，不使用胶囊标签。

### `TabBarItem`

- Properties：`Label`、`State=Default|Selected`、`Icon` INSTANCE_SWAP。
- 4 个实例：首页、训练、课程、我的。

### `PageStateInline`

- Properties：`State=Loading|Empty|Error|NetworkFailure`、`Title`、`Description`、`ActionLabel`。
- 供最近记录和阶段反馈使用；不画空图表。

## 6. `Screen/Home/Default` 节点结构

所有结构使用 Auto Layout；以下数值是方案 A 的 Figma 复现目标：

```text
Screen/Home/Default 390×844, vertical, canvas
├─ Content 390×auto, vertical, padding 24/24/96, gap 0
│  ├─ Header 342×56, horizontal, space-between
│  │  ├─ Brand “安心陪伴”
│  │  └─ IconButton/Badge
│  ├─ Divider, margin-top 16
│  ├─ EntryRow/Thermometer, min-height 56
│  ├─ Divider
│  ├─ DualEntries 342×80, horizontal
│  │  ├─ DualEntry/Accent “测一测”
│  │  └─ DualEntry “情绪日记”
│  ├─ Divider
│  ├─ JourneyActionCard/Ready, margin-top 14, width fill
│  ├─ EntryRow “如何开始 / 记录 · 反馈 · 练习”
│  ├─ Divider
│  ├─ SectionHeading “更多”
│  ├─ EntryRow “支持性反馈 / 记录后获得对应反馈”
│  ├─ EntryRow “训练中心 / 查看训练计划与练习”
│  ├─ EntryRow “人工支持 / 提交非实时支持请求”
│  ├─ SectionHeading “最近记录”
│  ├─ EntryRow/Summary “今天 18:40 · 作业沟通 / 紧张 · 强度 6 / 查看记录”
│  ├─ SectionHeading “阶段性反馈”
│  └─ EntryRow/Summary “记录还不够，继续观察 / 完成更多记录后，这里会呈现阶段摘要 / 查看说明”
└─ TabBar 390×72, bottom fixed + safe area
```

方案 A 中的叶线只用于 `JourneyActionCard` 的低对比装饰层，透明度不超过 28%，不承担信息；页面右上叶影透明度不超过 8%，不得影响文本对比度。

## 7. 差异处理

| 现有代码 | 方案 A / 已确认语义 | Figma 处理 | 代码阶段边界 |
|---|---|---|---|
| “情绪天气”与笑脸 | 情绪温度计 | 使用温度计线性图标与真实次数 | 改文案和图标，不改事件/API |
| 三个“开始步骤”按钮 | 单行“如何开始” | EntryRow | 保留 `openGettingStarted`，不保留伪进度 |
| 支持性反馈写“查看上次记录” | 记录后生成反馈 | 改为“记录后获得对应反馈” | 继续进入日记，不增加 GET |
| 最近记录进入周报 | 进入真实记录页 | Figma 使用“查看记录” | 代码实现前先完成记录页独立流程 |
| 阶段性反馈复杂卡片 | 先结论和下一步 | 有数据与空状态两套 Summary | 只绑定真实后端字段 |
| 多处圆角卡片 | 开放式编辑排版 | 主要使用分隔线 | 不改业务 JS |

## 8. Figma 审查 Harness

完成后必须提供：

1. Figma 文件 URL、fileKey、每个 Page ID；
2. Variables、Styles、Components 和 Screen 节点 ID 状态账本；
3. Foundations 每页截图；
4. 每个首页组件的 metadata 与局部截图；
5. 五张首页状态截图；
6. 字体 family 读取结果；
7. ImageGen 与 Figma 对比：顺序、字号、间距、颜色、图标、文本和状态；
8. 未绑定变量、重复命名、硬编码填色和低于 44px 触控目标检查结果。

出现以下任一情况即 Figma 审查失败：功能模块缺失或增生、天气语义、主行动不唯一、占位文案残留、文本裁切、组件未实例化、变量未绑定、字体不符、状态缺失或截图证据缺失。
