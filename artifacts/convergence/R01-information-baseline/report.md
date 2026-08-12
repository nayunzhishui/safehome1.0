# R01 参与者端信息密度基线

生成日期：2026-08-13
基线来源：当前工作树（包含开始任务前已经存在的 8 个未提交文件）
范围：`config/rc0810/miniprogram_page_policy.json` 中 48 个 `participant` 小程序页面

## 1. 结论

本轮只建立基线，没有修改任何参与者 UI、业务功能、入口、API、数据或流程。

静态源码审计的优先级前 10 名如下：

| 排名 | 页面 | 综合分 | 主要原因 |
|---|---|---:|---|
| 1 | `relationship-growth` | 74.7 | 文本、动作与决策分支均高；同页承载曲线、时间线、反馈和记录 |
| 2 | `settings-detail` | 61.4 | 多类设置与较多按钮共用页面；但包含权限冻结内容，本轮不处理 |
| 3 | `therapeutic-assessment` | 55.3 | 协作边界、首发范围、多人/AI说明和八步流程同时存在 |
| 4 | `home` | 47.2 | 17 个静态可操作点，首页多个业务区块竞争注意力 |
| 5 | `growth-dashboard` | 44.5 | 多类成长线索、多个分区和研究术语同时存在 |
| 6 | `relationship-report` | 42.6 | 多层画像、图表、反馈、问题与任务集中展示 |
| 7 | `assessment-result` | 42.0 | 3 个图表、32 个条件分支和专业结果解释集中展示 |
| 8 | `profile` | 38.5 | 入口和动作较多；当前还有用户未提交改动，后续须继续避让 |
| 9 | `feedback-result` | 37.3 | 结果、线索、训练建议与边界说明并列 |
| 10 | `program-detail` | 37.1 | 项目详情、状态和多项操作集中 |

排名只表示后续人工审计优先级，不表示产品质量、心理安全或真实用户认知负荷。静态扫描会把互斥条件分支合并计算，也不会读取 API 运行时文案，因此 R02/R03 必须增加真机或开发者工具截图与交互复核。

## 2. 六维观察

- Text Density：`relationship-growth`、`therapeutic-assessment` 和 `settings-detail` 静态文本最高。
- Action Density：`relationship-growth`、`settings-detail`、`home` 静态动作最多；首页共识别 17 个动作点。
- Visual Density：`weekly-report`、`assessment-result`、`relationship-report` 的卡片/图表/指标结构突出。
- Terminology Burden：结果与关系报告页出现样本、画像、模型或研究语汇；测评结果页还同时呈现 3 个图表。
- Repetition：部分页面重复边界或状态说明；风险/安全文案不能机械压缩，只能在保持即时提示的前提下分层。
- Decision Load：首页同时要求用户在记录、测评、今日行动、训练、反馈和人工支持之间判断；结果页动作少，但解释路径和条件分支多。

## 3. 首页 before 功能基线摘要

完整机器清单：`artifacts/convergence/function-baseline/home.before.json`。

- 功能：消息中心、情绪天气、测一测、情绪日记、今天的一小步、三步开始、支持性反馈、训练中心、人工支持、最近记录、阶段性反馈、开发态联调测试入口。
- 主要入口/导航：消息、情绪天气、测评、日记、服务端或本地草稿返回的今日行动、三步说明、训练、人工支持、周报；开发态另保留联调页。
- API：`listDiaries`、`getProfileStats`、`getEmotionThermometerDay`、`getProgressSummary`、`getTodayJourney`、`trackProductEvent`。
- loading：今日行动卡加载；情绪天气未就绪时显示“联网后更新”。
- error：今日行动可重试；阶段性反馈显示登录/联网失败；首页整体读取异常时保守回退。
- empty：最近记录空态保留“去记录”；阶段性反馈不足时保留“去测一测”和“看本周复盘”。

## 4. 测评结果页 before 功能基线摘要

完整机器清单：`artifacts/convergence/function-baseline/assessment-result.before.json`。

- 功能：结果摘要、风险状态、阶段性画像和匹配清晰度、相对位置图、画像雷达图、解释、优势、小步骤、讨论问题、项目任务线索、维度图与明细、训练卡推荐、训练入口、返回、边界说明。
- 按钮：查看可练习任务；返回测一测。
- API：`getAssessmentResult`、`getAssessment`、`listCards`、`getAssessmentProfilePosition`。
- loading：整页“正在读取结果”。
- error/empty：结果读取失败或未找到；辅助请求失败时降级；维度不足时解释不绘图；没有专属卡片时回退训练中心。
- 安全约束：风险提示、自动推荐阻断、量表含义、画像准入和非诊断边界均不得因分层展示而改变。

## 5. R02 建议修改范围（待下一步执行）

只允许修改：

- `apps/miniprogram/pages/home/index.wxml`
- `apps/miniprogram/pages/home/index.wxss`
- 如确有展示状态需要，最小修改 `apps/miniprogram/pages/home/index.js`
- R02 的 `after` 基线、截图、测试与三份事实记录

建议结构：顶部状态（问候 + 情绪天气）→ 今日行动 → 快捷功能（测一测、情绪日记、三步开始）→ 我的进展（最近记录、阶段性反馈）→ 更多支持（支持性反馈、训练中心、人工支持）。

不允许修改：

- 所有权限冻结文件、权限/登录/Token/CloudBase 行为
- 后端、数据库、API contract、shared 类型、内容计分与风险规则
- 当前已有的 `profile`、`support-assistant` 用户未提交修改
- 首页任何现有功能、按钮行为、主要入口、数据区块、API 或异常状态

R02 通过条件：`home.before.json` 的功能、按钮、目标、API 和状态均包含于 `home.after.json`；专项测试、静态测试、核心导航测试、开发者工具/截图复核和独立审查全部通过。

## 6. 冻结与限制

- `settings-detail` 虽排名第 2，但包含 Consent、参与者保护和隐私请求等冻结区域，本轮不进入实现范围。
- 未找到项目规则提及的《Codex用户研究与美术设计完整指令.md》，因此本轮只能依据已存在的 AGENTS、执行计划和 UI skills 建立基线；进入 R02 前如该文件补充到仓库，应先读取。
- 本轮没有运行需要真实账号、权限或 CloudBase 的页面操作，以免触碰权限冻结。
