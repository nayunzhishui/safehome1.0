---
title: 怎样让网页版 GPT 完成 UIproduct 页面并交给 Codex 审查
contentType: How-to
status: canonical
mandatoryRead: true
updated: 2026-08-11
---

# 怎样让网页版 GPT 完成 UIproduct 页面并交给 Codex 审查

本文件定义新的 UI 协作方式。网页版 GPT 先负责 ImageGen、Figma 和 `UIproduct` 分支前端复现；Codex 收到远端链接后独立审查。若结论不是“可行”，Codex 接管该页并按 ImageGen → Figma → 代码的顺序修正，直到重新审查可行。任何一方都不得修改 `main`、后端、数据库、API 或核心业务语义。

## 1. 职责边界

### 网页版 GPT

网页版 GPT 逐页完成以下工作：

1. 从 `UIproduct` 分支读取项目规则、功能真值和目标页代码
2. 冻结页面目标、信息层级、真实状态和禁改项
3. 使用 ImageGen 生成候选图并进行功能审查
4. 在指定 Figma 文件中组件化复现采用稿
5. 对照 Figma 修改微信小程序前端
6. 运行本地 Loop 1–4 与四类 Harness
7. 在 `UIproduct` 分支提交并推送
8. 返回 GitHub、Figma、ImageGen 和验证证据链接

网页版 GPT 不得把概念图当作代码背景图，也不得用静态假数据补足接口不存在的能力。

### Codex

Codex 收到远端链接后执行独立审查：

1. 核对链接、分支、提交和目标页
2. 对照功能真值检查事件、绑定、路由、API 和状态
3. 对照 ImageGen 与 Figma 检查结构、组件和视觉偏差
4. 对照 Figma 与代码检查尺寸、层级、字号、间距和状态
5. 检查后端隔离、改动范围、重复样式和新增依赖
6. 在安全环境运行可用的静态检查、编译或预览命令
7. 给出 `可行`、`需修正` 或 `阻断` 结论

Codex 先审查，不在审查前改写网页版 GPT 的成果。结论为 `需修正` 或 `阻断` 时，本文件视为用户已授权 Codex 在 `UIproduct` 分支完成修复；不需要再次逐项申请。修复仍必须经过功能真值、ImageGen、Figma、代码、Loop 和 Harness，不得只在代码层遮盖设计问题。

### 用户

用户负责：

- 决定采用哪个视觉方向
- 提供网页版 GPT 所需的项目、Figma 和 GitHub 权限
- 将网页版 GPT 返回的远端链接交给 Codex
- 查看 Codex 的审查结论与修复记录
- 在全部页面完成后执行统一视觉、功能和真机验收

## 2. 唯一事实源

网页版 GPT 开始每个页面前必须读取：

- `AGENTS.md`
- `docs/07_UI设计/UI美术与UX改造总指导.md`
- 本文件
- `design/function-truth-table.md` 中目标页章节
- `shared/design/experience-tokens.json`
- `design/ui-product/README.md`
- `design/ui-product/registry.json`
- `design/ui-product/references/current-ui/README.md` 及其中全部截图
- `apps/miniprogram/app.json`
- `apps/miniprogram/app.wxss`
- 目标页 WXML、WXSS、JS、JSON
- 目标页直接使用的组件
- 目标页上游入口与下游页面
- 目标页涉及的 API client、接口文档和后端路由，仅只读核对

优先级固定为：当前用户要求 → `AGENTS.md` 与事实基准 → 功能真值 → UI 总指导 → 页面冻结版 → ImageGen → Figma → 代码。

ImageGen 不能覆盖功能真值。Figma 不能覆盖已确认的代码状态。代码不能为了贴图而改变业务语义。

截图包记录真实设备问题、历史报错和视觉参考。它用于判断密度、可读性和风格，不是页面字段或业务状态的来源。网页版 GPT 必须逐张阅读截图说明，不能只看竹影参考图。

## 3. 产品与伦理基础

安心陪伴帮助家长记录具体事件、理解互动线索、获得支持性反馈并完成可练习的行动。它不承担诊断、治疗、筛查、人格判断或危机处置。

用户可见内容必须：

- 聚焦具体场景、感受、行为和下一步
- 使用“可能”“阶段性观察”“支持性测评”等保守表达
- 把高风险内容引向现实支持、人工督导或专业帮助
- 明确系统不能替代临床诊断、治疗和危机干预

禁止新增诊断标签、健康分、成长分、精确概率、实时客服、自动转介、未实现的数据图表或治疗承诺。

## 4. Design 基础

### 视觉方向

采用方案 A“温润编辑感”：温暖象牙白、森林绿、深墨文字、少量陶土橙、自然留白和清晰中文层级。页面应像经过编辑的人写工具，不像套模板生成的卡片墙。

禁止：

- 大面积渐变、玻璃拟态、发光光斑和粒子
- 通用 AI 家庭照、治愈系拥抱图和医疗化插画
- 每个模块使用相同圆角卡片
- 多个实心主按钮
- 无意义英文、编号、胶囊标签和重复免责声明
- 小字号塞内容

### 核心 token

| 类别 | Token | 值 | 用途 |
|---|---|---:|---|
| Color | Canvas | `#F7F8F5` | 页面背景 |
| Color | Surface | `#FFFFFF` | 必要容器 |
| Color | Ink | `#202622` | 主要文字 |
| Color | Muted | `#68736D` | 次级文字 |
| Color | Primary | `#4F7C6B` | 主行动 |
| Color | Primary Deep | `#2F5B4D` | 强调与按下态 |
| Color | Warning | `#B86A24` | 克制提醒 |
| Color | Danger | `#A5453F` | 风险和错误 |
| Color | Line | `#DFE5DC` | 分隔线与边界 |
| Type | Caption | `24rpx` | 辅助信息下限 |
| Type | Body | `28rpx` | 连续正文基准 |
| Type | Title | `40rpx` | 页面标题参考 |
| Touch | Minimum | `88rpx` | 最小触控目标 |

Token 的机器事实仍以 `shared/design/experience-tokens.json` 为准。单页不得擅自修改全局 token。

### 布局与组件

- 一个页面只突出一个主任务和一个实心主行动
- 每屏最多两个强视觉卡片，禁止卡片套卡片
- 优先用标题、字重、留白、短分隔线和结构化列表建立层级
- 间距优先使用 `8rpx` 倍数：`8 / 16 / 24 / 32 / 48 / 64rpx`
- pill 只用于状态、筛选或真实胶囊控件
- 普通内容优先无阴影；阴影只表达浮层或必要层级
- 重复内容优先组件化，不复制近似 WXSS
- 触控、禁用、按下、加载、错误和长文本状态必须可辨认

### 小字预算

- 可见文字不得小于 `24rpx`
- 正文、错误原因、恢复动作和关键结论不得使用 Caption
- 单个内容区通常只保留一组小字，且不超过两行
- 三行以上辅助信息必须改写为正文、短列表或渐进披露
- 机器字段和 ISO 时间必须在人机界面中转换为可读标签与日期

## 5. 竹影与自然物象组件

自然物象只能作为低对比装饰，不得承担状态或业务含义。允许建立 `BotanicalAccent` 组件集：

- `CornerShadow`：页头角落的低透明竹叶投影
- `LineBranch`：重点卡片内的单线竹枝
- `SectionSprout`：标题或步骤起点的小型竹节或新叶标记

使用规则：

- 默认每屏不超过一个自然物象装饰
- 装饰层不可点击，读屏应忽略
- 不覆盖文字、图标、按钮和安全信息
- 对比度保持低于正文，不制造背景噪声
- 不把整页 ImageGen 纹理作为位图背景
- 小程序优先使用本地 SVG、伪元素或轻量矢量资产
- 低端设备和 reduced motion 状态不需要额外动画
- 竹影可以替代生硬重复的粗侧线，但不能成为每个列表项的统一边框

## 6. 每页执行顺序

网页版 GPT 每次只处理一个页面：

1. 读取代码与功能真值
2. 列出页面功能、事件、数据、路由、状态和禁改项
3. 写现状审查与需求冻结版
4. 生成 ImageGen 候选
5. 淘汰改变功能、增加假数据或降低可读性的候选
6. 在 Figma 复现采用稿，复用 token 和现有组件
7. 完成 ImageGen → Figma 审查
8. 只修改必要的小程序前端文件
9. 完成 Figma → 代码审查
10. 运行 Loop 1–4 与四类 Harness
11. 提交并推送一个可恢复提交
12. 返回远端证据包，等待 Codex 审查
13. Codex 判定不可行时，由 Codex 接管当前页并完成修复闭环

Codex 审查通过前，网页版 GPT 不应把该页登记为最终通过。它可以继续准备下一页的只读审查，但不得混入同一提交。Codex 修复当前页时，网页版 GPT 不得同时修改同一页面或同一 Figma Frame。

## 7. ImageGen 输入模板

把以下模板与目标页功能真值一起交给网页版 GPT：

```text
请为微信小程序“安心陪伴”的 [页面标题] 生成高保真 UI 概念图。

产品边界：家长非评判陪伴训练，不诊断、不治疗、不做人格判断。
唯一主任务：[从功能真值填写]
必须保留：[真实内容、真实状态、真实入口]
禁止新增：[不存在的接口、数据、状态、按钮、图表或结论]

视觉方向：温润编辑感。象牙白背景，深墨文字，森林绿主行动，陶土橙仅少量提醒。减少卡片、胶囊、小字和重复说明。使用中文信息层级、自然留白和克制线描。可按需使用一个低对比竹影或线性竹枝，不遮挡内容。

可读性：正文至少对应 28rpx，辅助信息至少对应 24rpx，一个页面只有一个实心主按钮，触控高度至少对应 88rpx。

输出：390px 宽微信小程序长页面，不显示手机外壳。完整表现 Default 状态；长内容与其他真实状态另行生成。所有文字必须来自功能真值或页面冻结版。
```

## 8. Figma 复现规则

目标文件：`https://www.figma.com/design/8vocq2yUvjQavYpaxGotPs`

网页版 GPT 必须：

- 先读取 `design/ui-product/figma-state.json`
- 使用现有 Variables、Text Styles、Effect Styles 和组件
- 先检查组件缺口，再创建新组件
- 新组件使用 Auto Layout、变量绑定和真实状态变体
- 新页面放在 `03 Screens`，可复用组件放在 `02 Components`
- 使用 Noto Sans SC 作为 Figma 中文字体代理，不改变小程序平台字体栈
- 建立 Default、Long Content 和代码真实存在的状态
- 不创建代码不存在的 Loading、Empty 或 Error 状态
- 保存具体 Frame、Component 和 Variant Node ID
- 截图审查文字截断、越界、重叠、字号和主次行动

Figma 交付必须提供文件链接与目标 Frame 的 node 链接。只给文件首页不算有效证据。

## 9. GitHub 与前端实现规则

仓库：`https://github.com/nayunzhishui/safehome1.0`

分支固定为 `UIproduct`。网页版 GPT 必须确认当前分支后再修改：

```powershell
git branch --show-current
git status --short
```

硬约束：

- 不切换、不修改、不提交 `main`
- 禁止 `reset` 和 `clean`
- 保留已有未提交或远端提交，不覆盖他人改动
- 禁止修改 `backend/`、数据库、API、CloudBase、认证、`content/` 和 `shared/` 业务语义
- 优先只改目标页 WXML、WXSS 和必要前端视觉资产
- JS 只允许为展示做不改变语义的最小调整
- 保留所有事件名、参数、绑定、路由、接口、错误处理、权限和埋点
- 不新增依赖，不提交本地产物、数据库、缓存、构建目录或密钥
- 一页一个提交；提交信息说明页面和 UI 范围

最低验证：

```powershell
python scripts/ui_product_loop.py check-truth
python scripts/ui_product_loop.py harness
python backend/scripts/validate_miniprogram_assets.py
python backend/scripts/audit_miniprogram_frontend.py
python backend/scripts/audit_task33_experience.py
node scripts/audit_task23_visual_system.mjs
git diff --check
```

若环境具备微信开发者工具，还要运行编译或 Preview。无法运行时必须写明，不能把未执行写成通过。

## 10. 远端证据包

网页版 GPT 完成一页后必须返回：

```text
目标页面：pages/example/index
采用的 ImageGen：图片链接或仓库证据路径
Figma Frame：带 node-id 的链接
GitHub 分支：https://github.com/nayunzhishui/safehome1.0/tree/UIproduct
GitHub 提交：精确 commit 链接
修改文件：逐项列出
功能保护：列出保持不变的事件、路由、API 和状态
验证结果：命令、退出码和未执行项
已知差异：ImageGen → Figma → 代码的允许差异
请求 Codex 审查：是
```

不要只返回分支首页。Codex 需要精确 commit 或 Pull Request 链接，才能判断审查范围。

## 11. Codex 审查结论

Codex 使用以下三级结论：

- `可行`：功能真值、Figma、代码和工程范围一致；未发现阻断问题
- `需修正`：方向可用，但存在明确视觉、UX、状态或工程问题；列出文件与修正条件
- `阻断`：改变业务语义、缺少关键证据、修改禁区、无法编译或远端范围不可确认

Codex 审查至少覆盖：

- 功能：事件、绑定、路由、API、权限和状态不丢失
- 视觉：信息层级、字体、间距、颜色、图标、装饰和主次行动
- 认知：无卡片墙、无小字堆积、无机器字段直接暴露
- 组件：无重复组件、无样式分叉、Figma 与代码语义一致
- 工程：没有后端改动、无无关重构、无新增依赖、验证可重复
- 证据：ImageGen、Figma node、commit 和验证输出可追溯

Codex 的远端审查不等于最终真机通过。全部页面完成后仍需统一执行 Android、iOS、大字体、读屏和真实数据验收。

### 11.1 Codex 不可行修复循环

Codex 判定 `需修正` 或 `阻断` 后按以下顺序处理：

1. 锁定网页版 GPT 的 commit、Figma node 和 ImageGen 证据，避免审查范围继续变化
2. 重读目标页代码、功能真值、页面冻结版和 UI 总指导
3. 判断现有 ImageGen 是否仍可作为视觉基准；功能或方向错误时重新生成，局部偏差时保留并写明修正点
4. 先在 Figma 修正组件、布局、文字和真实状态
5. 完成 ImageGen → Figma 复核后再修改前端
6. 只在 `UIproduct` 分支做最小代码修正
7. 重跑 Loop 1–4、四类 Harness 和可用的微信开发者工具编译
8. 创建独立修复提交并推送，返回新的 commit 与 Figma node 链接
9. 对修复结果重新给出三级结论；仍不可行时继续同一循环

若远端成果修改了后端、数据库、API、认证或 `main`，Codex 不沿用该实现。它先隔离违规改动，再从最后一个可信 `UIproduct` 提交恢复设计链路；禁止使用 `reset` 或 `clean` 破坏其他工作。

## 12. 可直接复制给网页版 GPT 的总提示词

```text
你负责 SafeHome“安心陪伴”微信小程序的单页 UI 设计与前端视觉复现。

仓库：https://github.com/nayunzhishui/safehome1.0
工作分支：UIproduct
Figma：https://www.figma.com/design/8vocq2yUvjQavYpaxGotPs

开始前完整阅读：
1. AGENTS.md
2. docs/07_UI设计/UI美术与UX改造总指导.md
3. docs/07_UI设计/网页版GPT_UIproduct执行与Codex审查规则.md
4. design/function-truth-table.md 中目标页章节
5. shared/design/experience-tokens.json
6. design/ui-product/README.md
7. design/ui-product/registry.json
8. design/ui-product/references/current-ui/README.md 及其中全部截图
9. 目标页 WXML、WXSS、JS、JSON、直接组件、上下游页面和 API client

严格一次只处理一个页面。先核对功能真值和代码，再写页面冻结版。随后使用 ImageGen 生成概念图并自审；改变功能、增加假数据、增加不存在状态或使用大量小字的图必须淘汰。采用稿确认后，在现有 Figma 文件中使用 token、组件和真实状态复现，再对照 Figma 修改 UIproduct 分支前端。

视觉采用“温润编辑感”：象牙白、深墨、森林绿、少量陶土橙，减少卡片、胶囊、渐变和重复说明。正文不小于 28rpx，辅助信息不小于 24rpx，触控目标不小于 88rpx，一个页面只突出一个实心主行动。可按需使用一个不可点击、低对比的竹影或线性竹枝组件，但不能遮挡信息或替代状态。

不得修改 main、backend、数据库、API、CloudBase、认证、content 或 shared 业务语义。保留现有事件、绑定、路由、接口、权限、错误处理和状态。禁止 reset/clean，禁止新增无关依赖或批量重构。

完成后运行项目 UI Loop/Harness 和可用的微信开发者工具编译。提交并推送到 UIproduct，一页一个提交。最后返回：目标页、ImageGen 证据、带 node-id 的 Figma 链接、精确 GitHub commit 链接、修改文件、保持不变的功能、验证命令与结果、未执行项和已知差异。不要把未验证项写成通过。
```
