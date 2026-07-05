# 前端改造任务书 Claude

更新时间：2026-06-30

本文档用于让 Claude Code / Claude 在不了解项目的情况下，先快速建立 `safehome1.0 / 安心陪伴 / ReadFeedback` 前端上下文，再协助 Codex 和用户推进前端改造。

## 1. 任务目标

本轮目标不是立刻改代码，而是让 Claude 先完成项目理解、前端现状筛选和改造任务制定。

Claude 需要帮助完成：

```text
1. 先读取指定文档和代码，理解项目定位、伦理边界、前后端接口和当前前端结构。
2. 判断现有 Web 和小程序页面哪些可以保留、哪些只需局部调整、哪些可以重写。
3. 制定前端改造任务清单，按小步推进，不一次性大改。
4. 如果旧前端页面不符合用户要求，可以在不影响后端功能和数据结构的基础上丢弃旧页面实现，改为重新实现。
```

## 2. Claude 第一批必须读取

Claude 开始前必须先读以下文件，按顺序阅读。

### 2.1 项目事实和边界

```text
AGENTS.md
docs/00_当前事实基准/项目进度统一口径.md
docs/00_当前事实基准/当前进度交接.md
docs/00_当前事实基准/开发说明.md
docs/03_技术真相/当前项目代码总体解释与功能衔接说明.md
docs/03_技术真相/项目架构边界与后续开发规则.md
```

读取目的：

```text
1. 判断当前真实进度，不被历史规划误导。
2. 知道哪些能力已完成，哪些只是规划。
3. 明确不能破坏 MVP 核心闭环。
4. 明确后端、shared、content 和前端之间的边界。
```

### 2.2 前端设计和伦理边界

```text
docs/10Claude协作/前端设计规范_Claude.md
docs/07_UI设计/小程序设计系统.md
docs/07_UI设计/网站端设计与并行开发方案.md
docs/02_专项进度与验收/UI与伦理边界验收清单.md
docs/05_伦理试用/文案低AI味与伦理表达检查.md
docs/05_伦理试用/content伦理边界校验说明.md
```

读取目的：

```text
1. 统一视觉方向：简洁、高效、干净、清爽、专业、温和。
2. 避免营销式插画页、厚重渐变、AI 味说明和诊断化表达。
3. 保持非诊断、非标签化、非评判、支持性的心理学边界。
4. 明确高风险内容只进入人工关注或督导入口，不生成普通自动建议。
```

### 2.3 API、字段和联调方式

```text
docs/03_技术真相/API接口文档.md
docs/03_技术真相/数据库字段说明.md
docs/03_技术真相/数据字典.md
docs/04_部署联调/前端联调说明.md
shared/types/api.ts
shared/constants/api.ts
shared/mock-data/mvp.ts
```

读取目的：

```text
1. 前端改造必须继续复用现有 API。
2. 不为 Web 和小程序各自发明一套字段。
3. 不随意新增、删除或重命名 shared 类型。
4. 修改前端展示时，要知道数据真实来自哪里。
```

## 3. Claude 第一批必须查看的代码

### 3.1 Web 端

```text
apps/web/package.json
apps/web/src/main.tsx
apps/web/src/styles.css
apps/web/src/services/safehomeApi.ts
apps/web/src/services/authState.ts
apps/web/src/services/adminToken.ts
apps/web/src/services/userIdentity.ts
apps/web/src/pages/LandingPage.tsx
apps/web/src/pages/ResearchDashboard.tsx
apps/web/src/pages/AdminDashboard.tsx
apps/web/src/pages/ReadFeedbackIntegrationPages.tsx
apps/web/src/pages/LoginPage.tsx
apps/web/src/pages/RegisterPage.tsx
apps/web/src/pages/ScalesReview.tsx
apps/web/src/pages/ContentReviewOverview.tsx
apps/web/src/pages/CardsManagement.tsx
apps/web/src/pages/RulesManagement.tsx
apps/web/src/pages/ProfilesManagement.tsx
apps/web/src/pages/ReviewManagement.tsx
apps/web/src/pages/IntegrationSmokeTest.tsx
apps/web/src/components/ProfileScatterChart.tsx
apps/web/src/components/ProfileRadarChart.tsx
```

查看重点：

```text
1. main.tsx 当前路由和后台导航。
2. safehomeApi.ts 当前 API 调用边界。
3. styles.css 是否已经形成可复用 token 和页面布局。
4. 各页面是否只是临时堆叠，是否需要保留、重组或重写。
5. ECharts 图表是否能作为研究看板可视化基础保留。
```

### 3.2 小程序端

```text
apps/miniprogram/app.json
apps/miniprogram/app.wxss
apps/miniprogram/services/api.js
apps/miniprogram/services/cloudConfig.js
apps/miniprogram/services/userIdentity.js
apps/miniprogram/pages/home/index.*
apps/miniprogram/pages/assessment/index.*
apps/miniprogram/pages/assessment-detail/index.*
apps/miniprogram/pages/assessment-result/index.*
apps/miniprogram/pages/diary-form/index.*
apps/miniprogram/pages/feedback-result/index.*
apps/miniprogram/pages/training/index.*
apps/miniprogram/pages/training-card/index.*
apps/miniprogram/pages/checkin/index.*
apps/miniprogram/pages/weekly-report/index.*
apps/miniprogram/pages/supervision/index.*
apps/miniprogram/pages/login/index.*
apps/miniprogram/pages/register/index.*
apps/miniprogram/pages/debug/index.*
apps/miniprogram/pages/integration-test/index.*
apps/miniprogram/components/*
```

查看重点：

```text
1. app.json 页面注册和 tabBar 不要轻易破坏。
2. api.js 和 cloudConfig.js 是小程序请求后端的关键层，不能随意丢弃。
3. pages/integration-test/index 是长期保留联调页，不能删除。
4. debug 页用于 CloudBase 和本地 5000 模式排查，建议保留。
5. 页面视觉可以重写，但数据提交、跳转和接口调用要保持可用。
```

### 3.3 内容库

```text
content/training_cards.json
content/feedback_rules.json
content/assessment_worksheets.json
content/student_profile_rules.json
content/risk_keywords.json
content/assessment_training_map.json
content/diary_training_map.json
content/profiles/*.json
```

查看重点：

```text
1. 页面不得硬编码另一套训练卡、反馈规则或画像解释。
2. 前端可以改善展示方式，但内容来源优先复用 content 或 API。
3. 任何诊断、筛查、人格定性或风险处置文案都必须谨慎。
```

## 4. 允许丢弃旧前端页面的规则

如果旧的 Web 或小程序页面不符合用户要求，Claude 可以建议丢弃旧页面实现，但必须遵守以下规则。

### 4.1 可以丢弃或重写的内容

```text
1. 可以重写 apps/web/src/pages 下某个页面的 JSX 结构和样式组织。
2. 可以重写 apps/miniprogram/pages 下某个页面的 WXML/WXSS 视觉结构。
3. 可以重组页面内文案、信息层级、按钮位置和卡片结构。
4. 可以删除页面内硬编码的临时展示数据，改为 API/content/shared 数据。
5. 可以把旧页面当作草稿，只保留有价值的接口调用和业务逻辑。
```

### 4.2 不可以随意丢弃的内容

```text
1. 不删除后端已有 API。
2. 不删除或重命名 shared/types/api.ts 中已被前后端共用的字段。
3. 不删除 apps/miniprogram/pages/integration-test/index。
4. 不删除 apps/miniprogram/pages/debug/index，除非用户明确要求。
5. 不破坏 POST /api/diaries、POST /api/feedback/generate、GET /api/cards/recommend、POST /api/checkins。
6. 不把训练卡、反馈规则、画像解释硬编码成另一套前端数据。
7. 不为了重做页面而改数据库或改后端响应结构。
8. 不引入诊断化、标签化、责备性、危机干预替代性文案。
```

### 4.3 丢弃旧页面前的判断标准

Claude 需要先给每个页面打一个处理建议：

```text
保留：结构和业务都基本可用，只需小修。
局部改造：接口和逻辑可保留，但视觉层级、文案或布局需要重做。
重写：旧页面实现成本高于重建，但路由、API、数据结构继续复用。
隐藏入口：功能暂不适合展示，先从导航或 tab 中隐藏，不删除代码和 API。
暂缓：风险较高，先不动，等用户确认。
```

## 5. 前端改造任务拆分

### T0：只读理解和页面盘点

输出：

```text
1. Web 路由清单。
2. 小程序页面清单。
3. 每个页面的数据来源。
4. 每个页面的处理建议：保留 / 局部改造 / 重写 / 隐藏入口 / 暂缓。
5. 当前最不符合用户要求的 3-5 个前端问题。
```

要求：

```text
本阶段不写代码。
```

### T1：制定最小前端改造路线

输出：

```text
1. 第一轮只改一个清晰范围，例如“小程序核心主流程”或“Web 研究后台壳层”。
2. 明确本轮修改文件。
3. 明确不修改文件。
4. 明确复用哪些 API 和 content。
5. 明确验收方式。
```

要求：

```text
用户确认后再写代码。
```

### T2：小程序核心体验优先

推荐优先顺序：

```text
1. home：首页是否清楚引导核心闭环。
2. assessment / assessment-detail / assessment-result：测一测和画像结果是否清楚、非诊断、可理解。
3. diary-form：记录页是否低压力、可填写。
4. feedback-result：反馈页是否支持性、能连接训练卡。
5. training-card / checkin / weekly-report：训练、打卡、复盘是否形成闭环。
6. login / register / profile：账号相关页面是否只做必要入口，不干扰核心链路。
```

保底要求：

```text
小程序核心链路仍能跑通：记录 -> 反馈 -> 推荐训练卡 -> 打卡。
```

### T3：Web 端后台和研究看板

推荐优先顺序：

```text
1. main.tsx 后台导航和角色可见性。
2. ResearchDashboard 研究看板。
3. ScalesReview / ContentReviewOverview 内容审核。
4. AdminDashboard / diaries 记录查看。
5. ProfilesManagement / ReviewManagement 学生画像和人工复核。
6. ExportManagement 导出与脱敏提示。
7. LandingPage 网站前台。
```

保底要求：

```text
Web 改坏时，不能影响小程序核心链路和后端 API。
```

### T4：视觉系统收敛

需要统一：

```text
1. 主色、背景色、卡片、边框、阴影、按钮。
2. 页面标题、说明文案、标签、风险提示。
3. 空状态、加载状态、错误状态。
4. Web 和小程序的字段命名、文案口径和伦理边界。
```

避免：

```text
1. 大面积渐变。
2. 纯装饰插画。
3. 营销式 hero。
4. AI 味说明。
5. 诊断化或人格定性表达。
```

### T5：验证和交接

每次修改后至少验证：

```text
1. 后端 /healthz 正常。
2. Web：npm run build。
3. 小程序：修改过的 JS 文件通过 node --check。
4. 小程序：修改过的 JSON 文件能被解析。
5. 核心 API 调用层没有被破坏。
6. git status 中没有误提交 node_modules、dist、db、venv、pycache 等运行产物。
```

如果能人工验收，还需要：

```text
1. 浏览器打开 Web 关键页面。
2. 微信开发者工具打开小程序关键页面。
3. 检查页面没有文字重叠、按钮溢出、信息遮挡。
4. 检查非诊断边界文案仍存在。
```

## 6. 给 Claude 的可复制启动指令

```markdown
请协助我和 Codex 修改 safehome1.0 项目前端。项目路径是 D:\codex\workspace\safehome1.0。

你还不了解项目，所以第一步不要写代码。请先阅读 docs/10Claude协作/前端改造任务书_Claude.md 中列出的第一批必读文档和代码，尤其是 AGENTS.md、docs/00_当前事实基准/项目进度统一口径.md、docs/00_当前事实基准/当前进度交接.md、docs/10Claude协作/前端设计规范_Claude.md、apps/web/src/main.tsx、apps/web/src/services/safehomeApi.ts、apps/miniprogram/app.json 和 apps/miniprogram/services/api.js。

你的第一轮输出只做前端现状盘点和改造方案，不直接改代码。请按页面列出：

1. Web 端有哪些页面和路由；
2. 小程序端有哪些页面；
3. 每个页面当前依赖哪些 API、shared 类型或 content 文件；
4. 每个页面建议“保留 / 局部改造 / 重写 / 隐藏入口 / 暂缓”；
5. 第一轮最小改造任务应该从哪里开始；
6. 需要 Codex 执行哪些具体文件修改；
7. 应该如何测试和回滚。

如果旧的前端页面不符合我的要求，你可以建议丢弃旧页面实现并重新实现，但必须满足：

- 不影响后端功能实现；
- 不删除后端已有 API；
- 不改数据库结构；
- 不破坏 shared/types/api.ts 和 shared/constants/api.ts 的既有字段；
- 不删除 pages/integration-test/index；
- 不破坏小程序核心链路：记录 -> 支持性反馈 -> 推荐训练卡 -> 打卡；
- 不把训练卡、反馈规则、画像解释硬编码成另一套前端数据；
- 所有用户可见文案继续保持非诊断、非标签化、非评判、支持性表达。

请先给我方案，等我确认后再进入代码修改。
```

## 7. 给 Codex 的配合要求

Codex 根据 Claude 输出执行前端修改时，应遵守：

```text
1. 每次只做一个小任务。
2. 改动前说明计划。
3. 不回滚用户或 Claude 已经做过的无关改动。
4. 修改后更新开发日志、当前进度交接、开发说明。
5. 如果 Claude 实际参与对话或审查，追加 docs/10Claude协作/Claude使用记录.md。
```

