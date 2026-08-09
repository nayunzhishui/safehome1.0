# 小程序功能真值表

更新时间：2026-08-10

状态：`mandatory_before_imagegen_figma_and_frontend`

本文件记录每个小程序页面的真实功能，是 UI 审查、ImageGen、Figma 和前端视觉实现的共同输入。前端用于承载现有业务与后端能力，视觉不得新增、替换或曲解功能。

## 使用规则

每个页面严格执行：

1. 读取目标页 WXML、WXSS、JS、JSON；
2. 读取页面使用的组件、上游入口和下游页面；
3. 核对前端 API 封装、共享 endpoint、后端 route/service 和本地存储；
4. 写出“页面元素 → 事件 → 路由/API → 后端或本地能力 → 用户任务”；
5. 标记现有文案、点击结果和后端能力之间的差异；
6. 用户确认功能范围后才能冻结需求和调用 ImageGen；
7. 进入 Figma 前重读本页真值表；
8. 修改前端前再次对照当前代码，发现漂移先更新真值表并重新确认。

如果目标设计需要当前后端不存在的读取接口、字段或状态，应停止该部分，记录能力缺口并等待授权。不得用重新生成数据、静态假数据或相似页面冒充真实功能。

## 页面登记

页面清单以 `apps/miniprogram/app.json` 为准。当前 52 个页面已全部登记；严格一次只核对一个页面。

| 页面路由 | 当前导航标题 | 真值状态 |
|---|---|---|
| `pages/home/index` | 安心陪伴 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/login/index` | 登录 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/register/index` | 注册 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/messages/index` | 消息 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/support-assistant/index` | 支持性问答 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/message-detail/index` | 消息详情 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/emergency-guide/index` | 紧急安全指引 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/emergency-resources/index` | 紧急帮助说明 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/getting-started/index` | 三步开始 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/thermometer/index` | 情绪温度计 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/training/index` | 训练 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/training-history/index` | 训练记录 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/personalized-plan/index` | 个性化训练方案 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/program-list/index` | 项目测试 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/program-detail/index` | 项目详情 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/relationship-pilot/index` | 关系探索试点 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/relationship-report/index` | 关系健康初筛报告 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/relationship-task/index` | 关系探索任务 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/relationship-growth/index` | 关系探索成长仪表盘 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment/index` | 共同理解 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-boundary/index` | 开始前了解 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-issue/index` | 我的议题 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-recent-event/index` | 最近一次事件 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-resources/index` | 例外与资源 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-sharing/index` | 资料与共享 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-summary/index` | 提交前摘要 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-feedback-check/index` | 反馈核对 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-action-review/index` | 一个小行动 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-action-followup/index` | 行动回看 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/therapeutic-assessment-quality/index` | 评估质量与更正 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/growth-dashboard/index` | 我的成长仪表盘 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/relationship-narrative/index` | 关系探索手记 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/researcher-dashboard/index` | 研究者移动工作台 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/course/index` | 课程 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/course-detail/index` | 课程内容 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/profile/index` | 我的 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/settings-detail/index` | 设置与说明 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/goal-setting/index` | 本周小目标 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/diary-form/index` | 记录情绪事件 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/feedback-result/index` | 本次反馈 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/assessment/index` | 家庭关系测一测 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/assessment-history/index` | 全部测评记录 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/assessment-detail/index` | 填写测评 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/assessment-result/index` | 测一测结果 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/hot-topics/index` | 教育热榜 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/task-detail/index` | UP任务卡 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/training-card/index` | 推荐训练卡 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/checkin/index` | 记录尝试 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/weekly-report/index` | 本周复盘 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/supervision/index` | 人工督导入口 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/debug/index` | 云托管诊断 | 自动代码证据已核对；逐页冻结前复核 |
| `pages/integration-test/index` | 联调测试 | 自动代码证据已核对；逐页冻结前复核 |

## 01：首页 `pages/home/index`

核对来源：

- `apps/miniprogram/pages/home/index.wxml`
- `apps/miniprogram/pages/home/index.js`
- `apps/miniprogram/pages/home/index.json`
- `apps/miniprogram/components/journey-action-card/`
- `apps/miniprogram/services/api.js`
- `shared/constants/api.ts`
- `backend/routes/diaries.py`
- `backend/routes/emotion_thermometer.py`
- `backend/routes/feedback.py`
- `backend/routes/journey.py`
- `backend/routes/progress_summary.py`
- `backend/routes/profile.py`
- `backend/services/participant_action_planner.py`

### 功能映射

| 页面区域 | 当前前端事件 | 数据或目标 | 真实用户任务 | 正式设计约束 |
|---|---|---|---|---|
| 顶栏消息 | `openMessages` | 跳转 `pages/messages/index`；未读数来自 `GET /api/profile/stats` 的 `unread_message_count` | 查看研究者消息、反馈或系统消息 | 只表现消息入口与未读状态，不画聊天输入或即时客服能力 |
| 情绪温度计 | `openThermometer` | 跳转 `pages/thermometer/index`；当天摘要来自 `GET /api/emotion-thermometer/day` | 记录和观察情绪强度、效价、唤醒及控制感 | 正式名称使用“情绪温度计”；可显示当天记录次数或真实摘要，不增加天气选择器、天气图标组或气象含义 |
| 测一测 | `openCoreEntry(assessment)` | 跳转 `pages/assessment/index` | 进入支持性测评，了解当前状态 | 只作为入口，不在首页伪造题目、结果或评分 |
| 情绪日记 | `openCoreEntry(diary)` | 跳转 `pages/diary-form/index`；首页同时通过 `GET /api/diaries` 读取当天次数和最近记录 | 记录一次具体情绪事件 | 只作为记录入口；不得改成普通心情随笔或聊天 |
| 今天的一小步 | `openTodayAction`、`retryTodayJourney` | `GET /api/journey/today`，并检查本机关系任务或项目草稿 | 根据未读消息、训练状态、测评、日记、练习节奏、草稿和参与者保护门禁提供一个可继续行动 | 标题、描述、按钮、状态和边界来自真实返回；保留 Loading、Error、Ready、Paused、Completed、Not Due、登录和保护门禁；不得编写固定建议 |
| 如何开始 | `openGettingStarted` | 跳转 `pages/getting-started/index` | 查看“记录—反馈—练习”的三步说明 | 可按用户确认收成单行入口；不能画成已经完成的进度条 |
| 支持性反馈 | `openCoreEntry(feedback)` | 先提示“请先记录一次事件”，再跳转 `pages/diary-form/index`；记录提交后由现有 `POST /api/feedback/generate` 生成反馈 | 先记录一件具体事件，再获得对应的支持性反馈 | 用户已确认保留现有接口和流程。首页入口可保留“支持性反馈”，辅助文案必须明确“记录后获得反馈”；不得暗示可直接读取历史反馈，也不得新增读取接口 |
| 训练中心 | `openCoreEntry(training)` | `switchTab` 到 `pages/training/index` | 查看训练计划、训练卡和练习入口 | 只表现入口，不在首页复制训练列表或打卡功能 |
| 人工支持 | `openCoreEntry(supervision)` | 跳转 `pages/supervision/index`，该页使用 `POST /api/supervision` | 提交非实时人工支持请求 | 必须保留“非实时危机服务”边界；不得画成实时聊天或紧急热线 |
| 最近记录 | `startDiary`、`openWeeklyReport` | 最近记录来自 `GET /api/diaries`；空状态进入日记，有数据时当前进入 `pages/weekly-report/index` | 用户已确认目标为进入真实记录页 | 当前没有情绪记录列表或详情页。后续需新增前端记录页并优先复用 `GET /api/diaries`；页面结构和路由需单独冻结 |
| 阶段性反馈 | `openWeeklyReport` | `GET /api/progress-summary?range=7d`；进入 `pages/weekly-report/index` | 查看近期测评、打卡、温度计、常见场景或情绪、下一步与非诊断边界 | 只渲染后端真实摘要；无数据时明确“还不能归纳”；不得生成成长评价、疗效或人格结论 |
| 开发入口 | `openIntegrationTest` | 仅 `showDevEntry` 为真时进入 `pages/integration-test/index` | 开发联调 | 正式概念图和 Figma 默认不展示，但源码必须保留 |

### 当前代码中的非展示事实

- `todayRecordCount` 已读取但当前 WXML 未展示，设计不得自行增加，除非用户确认。
- `coreEntries`、`hotTopics` 以及若干 handler 当前没有对应 WXML 展示，不能因为 JS 中存在就自动加入首页。
- `journey-action-card` 是真实动态主行动组件，应保留状态和恢复能力；视觉可以重做，语义不能改。

### 已确认产品目标与实施边界

1. 用户已确认保留现有接口。支持性反馈继续采用“先记录事件，再生成对应反馈”的现有链路，不新增读取历史反馈接口，不修改后端。
2. 最近记录应进入真实记录页。当前没有该页面；后续单独设计一个前端记录页并复用 `GET /api/diaries`，不新增后端接口，但必须先完成该页的功能真值表、需求冻结、ImageGen 和 Figma。

首页状态更新为 `visual_concept_ready_with_frontend_dependency`：可以重新生成严格按功能真值表约束的 ImageGen 概念稿；用户确认视觉方案前不进入 Figma、不修改前端。“最近记录”真实跳转的前端页面依赖需在实现前按单页流程补齐。

<!-- UI_PRODUCT_AUTO_FACTS:BEGIN -->

## 全页面自动代码证据（UIproduct Harness）

生成时间：`2026-08-10T01:47:19+08:00`  
分支：`UIproduct`  
页面数：`52`

本节由 `scripts/ui_product_loop.py audit-truth` 从当前代码生成，覆盖 WXML 事件、JS 处理器、API 客户端方法、接口模板、路由、本地存储、页面状态、组件和上下游入口。自动证据是逐页人工冻结的底稿；任何未解析项都会阻断 ImageGen。

### 01：安心陪伴 `pages/home/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`31c104e2e3191c051d38a2f4c1adc3c50615d5e319259a4183ab3af556f3a237`
- 核对文件：`apps/miniprogram/pages/home/index.wxml`、`apps/miniprogram/pages/home/index.wxss`、`apps/miniprogram/pages/home/index.js`、`apps/miniprogram/pages/home/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/login/index`、`pages/register/index`、`pages/messages/index`、`pages/emergency-guide/index`、`pages/hot-topics/index`、`pages/checkin/index`、`pages/weekly-report/index`、`pages/supervision/index`
- 页面组件：`welcome-card` → `/components/welcome-card/index`、`section-title` → `/components/section-title/index`、`function-entry-card` → `/components/function-entry-card/index`、`training-task-card` → `/components/training-task-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`journey-action-card` → `/components/journey-action-card/index`
- 主要可见内容：安心陪伴、选择今天的一小步、情绪天气、今天已记录 次、记录 ›、测一测、了解当前状态、情绪日记、记录一次具体事件、支持性反馈、查看上次记录的互动线索、训练中心、选择今天的小练习、人工支持、提交补充反馈请求，非实时危机服务、还没有记录、可以先写下一件刚发生的小事、去记录 ›、测评记录、练习打卡、情绪温度、常见场景：、常见情绪：、还不能归纳

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 20 | 情绪天气 | `bindtap` | `openThermometer` | — |
| 31 | 测一测 | `bindtap` | `openCoreEntry` | {'key': 'assessment'} |
| 35 | 情绪日记 | `bindtap` | `openCoreEntry` | {'key': 'diary'} |
| 42 | {{todayJourney ? todayJourney.actionAriaLabel :  | `bindaction` | `openTodayAction` | — |
| 42 | {{todayJourney ? todayJourney.actionAriaLabel :  | `bindretry` | `retryTodayJourney` | — |
| 60 | — | `bindmore` | `openGettingStarted` | — |
| 62 | — | `bindtap` | `openStartStep` | {'key': '{{item.key}}'} |
| 80 | 支持性反馈 | `bindtap` | `openCoreEntry` | {'key': 'feedback'} |
| 87 | 训练中心 | `bindtap` | `openCoreEntry` | {'key': 'training'} |
| 94 | 人工支持 | `bindtap` | `openCoreEntry` | {'key': 'supervision'} |
| 106 | — | `bindmore` | `openWeeklyReport` | — |
| 107 | — | `bindtap` | `openWeeklyReport` | — |
| 114 | 还没有记录 | `bindtap` | `startDiary` | — |
| 125 | — | `bindmore` | `openWeeklyReport` | — |
| 160 | 去测一测 | `bindtap` | `openAssessment` | — |
| 161 | 看本周复盘 | `bindtap` | `openWeeklyReport` | — |
| 167 | 进入联调测试页 | `bindtap` | `openIntegrationTest` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 9 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 197 | `listDiaries` | `GET` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 198 | `listDiaries` | `GET` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 199 | `getProfileStats` | `GET` | `/api/profile/stats` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 200 | `getEmotionThermometerDay` | `GET` | `/api/emotion-thermometer/day` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 201 | `getProgressSummary` | `GET` | `/api/progress-summary` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 248 | `getTodayJourney` | `GET` | `/api/journey/today` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/goal-setting/index`（js:240）、`navigateTo` → `/pages/diary-form/index`（js:241）、`navigateTo` → `/pages/thermometer/index`（js:242）、`navigateTo` → `/pages/weekly-report/index`（js:243）、`switchTab` → `/pages/training/index`（js:311）、`navigateTo` → `/pages/assessment/index`（js:312）、`navigateTo` → `/pages/messages/index`（js:316）、`navigateTo` → `/pages/integration-test/index`（js:317）、`navigateTo` → `/pages/getting-started/index`（js:318）、`switchTab` → `/pages/training/index`（js:323）、`navigateTo` → `/pages/getting-started/index`（js:324）、`switchTab` → `/pages/training/index`（js:330）、`navigateTo` → `/pages/diary-form/index`（js:333）、`navigateTo` → `/pages/supervision/index`（js:336）、`navigateTo` → `/pages/assessment/index`（js:337）、`navigateTo` → `/pages/training-card/index?tags=:dynamic`（js:341）、`navigateTo` → `/pages/hot-topics/index`（js:343）、`navigateTo` → `/pages/hot-topics/index?id=:dynamic`（js:346）
- 本地存储：`getStorageSync` `key`（JS:110）、`getStorageSync` `key`（JS:132）、`getStorageSync` `auth_user`（JS:540）、`removeStorageSync` `auth_token`（JS:564）、`removeStorageSync` `auth_user`（JS:565）、`getStorageSync` `auth_token`（JS:587）、`setStorageSync` `auth_token`（JS:807）、`setStorageSync` `auth_user`（JS:808）、`removeStorageSync` `safehome_anonymous_user_id`（JS:809）、`setStorageSync` `auth_token`（JS:855）、`setStorageSync` `auth_user`（JS:856）、`setStorageSync` `auth_token`（JS:871）、`setStorageSync` `auth_user`（JS:872）、`removeStorageSync` `safehome_anonymous_user_id`（JS:873）、`setStorageSync` `auth_token`（JS:888）、`setStorageSync` `auth_user`（JS:889）、`removeStorageSync` `safehome_anonymous_user_id`（JS:890）、`setStorageSync` `auth_token`（JS:913）、`setStorageSync` `auth_user`（JS:914）、`removeStorageSync` `safehome_anonymous_user_id`（JS:915）、`removeStorageSync` `auth_token`（JS:922）、`removeStorageSync` `auth_user`（JS:923）、`getStorageSync` `STORAGE_KEY`（JS:2266）、`setStorageSync` `STORAGE_KEY`（JS:2272）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2308）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2335）
- WXML 数据绑定：`unreadMessageCount`、`thermometerRecordCount`、`thermometerRecordReady`、`todayJourneyLoading`、`todayJourneyError`、`todayJourney`、`startSteps`、`item`、`index`、`latestRecord`、`progressSummary`、`progressSummaryError`、`showDevEntry`
- 条件状态：`unreadMessageCount`、`latestRecord`、`progressSummary`、`showDevEntry`
- `setData` 状态：`todayRecordCount`、`todayRecordCountReady`、`thermometerRecordReady`、`unreadMessageCount`、`progressSummary`、`progressSummaryReady`、`progressSummaryError`、`latestRecord`、`time`、`trigger`、`status`、`thermometerRecordCount`、`todayJourneyLoading`、`todayJourneyError`、`todayJourney`、`primary_action`、`title`、`description`、`button_label`、`url`、`source_type`、`boundary_notice`、`estimated_minutes`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 02：登录 `pages/login/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`f69ab1447365abc7e7186144d6d224332ea8101e6718337e9a5b9c3fb5a8e021`
- 核对文件：`apps/miniprogram/pages/login/index.wxml`、`apps/miniprogram/pages/login/index.wxss`、`apps/miniprogram/pages/login/index.js`、`apps/miniprogram/pages/login/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/services/minorSafeguardsApi.js`
- 上游页面：`pages/home/index`、`pages/register/index`、`pages/messages/index`、`pages/support-assistant/index`、`pages/profile/index`、`pages/settings-detail/index`
- 页面组件：—
- 主要可见内容：登录、登录后可以查看消息、阶段性反馈和个人记录。选择一种方便的方式继续。、首次登录，请先设置新密码、新密码至少 12 位，并包含三类字符。更新后临时密码和旧会话立即失效。、临时密码、新密码、再次输入新密码、更新密码并继续、微信一键登录、微信一键登录（暂不可用）、手机号快捷登录、手机号快捷登录（暂不可用）、手机号仅用于识别你的账号，系统只保存不可逆摘要，不保存完整号码。、或使用账号密码、用户名、密码、注册新账号

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 12 | — | `bindinput` | `onCurrentPasswordInput` | — |
| 16 | — | `bindinput` | `onNewPasswordInput` | — |
| 20 | — | `bindinput` | `onConfirmPasswordInput` | — |
| 23 | 更新密码并继续 | `bindtap` | `submitPasswordChange` | — |
| 28 | 微信一键登录 | `bindtap` | `submitWechatLogin` | — |
| 30 | 手机号快捷登录 | `bindgetphonenumber` | `handlePhoneLogin` | — |
| 39 | — | `bindinput` | `onUsernameInput` | — |
| 43 | — | `bindinput` | `onPasswordInput` | — |
| 47 | 登录 | `bindtap` | `submitLogin` | — |
| 48 | 注册新账号 | `bindtap` | `goRegister` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 78 | `getAuthCapabilities` | `GET` | `/api/auth/capabilities` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 113 | `login` | `POST` | `/api/auth/login` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 168 | `changePassword` | `POST` | `/api/auth/change-password` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 204 | `wechatLogin` | `POST` | `/api/auth/wechat-login` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 250 | `phoneLogin` | `POST` | `/api/auth/phone-login` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |

#### 路由、本地状态与页面状态

- 下游路由：`switchTab` → `/pages/home/index`（js:17）、`redirectTo` → `/pages/register/index:dynamic`（js:41）
- 本地存储：`getStorageSync` `auth_user`（JS:461）、`removeStorageSync` `auth_token`（JS:485）、`removeStorageSync` `auth_user`（JS:486）、`getStorageSync` `auth_token`（JS:508）、`setStorageSync` `auth_token`（JS:728）、`setStorageSync` `auth_user`（JS:729）、`removeStorageSync` `safehome_anonymous_user_id`（JS:730）、`setStorageSync` `auth_token`（JS:776）、`setStorageSync` `auth_user`（JS:777）、`setStorageSync` `auth_token`（JS:792）、`setStorageSync` `auth_user`（JS:793）、`removeStorageSync` `safehome_anonymous_user_id`（JS:794）、`setStorageSync` `auth_token`（JS:809）、`setStorageSync` `auth_user`（JS:810）、`removeStorageSync` `safehome_anonymous_user_id`（JS:811）、`setStorageSync` `auth_token`（JS:834）、`setStorageSync` `auth_user`（JS:835）、`removeStorageSync` `safehome_anonymous_user_id`（JS:836）、`removeStorageSync` `auth_token`（JS:843）、`removeStorageSync` `auth_user`（JS:844）、`getStorageSync` `STORAGE_KEY`（JS:2187）、`setStorageSync` `STORAGE_KEY`（JS:2193）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2229）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2256）、`removeStorageSync` `auth_token`（JS:2300）、`removeStorageSync` `auth_user`（JS:2301）、`getStorageSync` `auth_token`（JS:2306）
- WXML 数据绑定：`mustChangePassword`、`currentPassword`、`newPassword`、`confirmPassword`、`message`、`status`、`loading`、`wechatAvailable`、`wechatLoading`、`phoneAvailable`、`phoneLoading`、`capabilityMessage`、`username`、`password`
- 条件状态：`mustChangePassword`、`message`、`wechatAvailable`、`phoneAvailable`、`capabilityMessage`
- `setData` 状态：`redirectUrl`、`capabilityMessage`、`wechatAvailable`、`phoneAvailable`、`username`、`password`、`status`、`message`、`loading`、`mustChangePassword`、`currentPassword`、`newPassword`、`confirmPassword`、`wechatLoading`、`phoneLoading`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 03：注册 `pages/register/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`f110e6a5c245978ed94480e36c4d07dfdc25134b35f06190b40fff426674eafb`
- 核对文件：`apps/miniprogram/pages/register/index.wxml`、`apps/miniprogram/pages/register/index.wxss`、`apps/miniprogram/pages/register/index.js`、`apps/miniprogram/pages/register/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/login/index`、`pages/messages/index`、`pages/profile/index`
- 页面组件：—
- 主要可见内容：注册、当前开放家长和学生账号。研究者、督导和管理员由项目负责人单独开通。、用户名、密码、角色、昵称（可选）、已有账号，去登录

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | — | `bindinput` | `onUsernameInput` | — |
| 13 | — | `bindinput` | `onPasswordInput` | — |
| 17 | — | `bindchange` | `onRoleChange` | — |
| 23 | — | `bindinput` | `onNicknameInput` | — |
| 27 | 注册 | `bindtap` | `submitRegister` | — |
| 28 | 已有账号，去登录 | `bindtap` | `goLogin` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 68 | `register` | `POST` | `/api/auth/register` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/home/index`（js:13）、`navigateTo` → `/pages/login/index:dynamic`（js:87）
- 本地存储：`getStorageSync` `auth_user`（JS:281）、`removeStorageSync` `auth_token`（JS:305）、`removeStorageSync` `auth_user`（JS:306）、`getStorageSync` `auth_token`（JS:328）、`setStorageSync` `auth_token`（JS:548）、`setStorageSync` `auth_user`（JS:549）、`removeStorageSync` `safehome_anonymous_user_id`（JS:550）、`setStorageSync` `auth_token`（JS:596）、`setStorageSync` `auth_user`（JS:597）、`setStorageSync` `auth_token`（JS:612）、`setStorageSync` `auth_user`（JS:613）、`removeStorageSync` `safehome_anonymous_user_id`（JS:614）、`setStorageSync` `auth_token`（JS:629）、`setStorageSync` `auth_user`（JS:630）、`removeStorageSync` `safehome_anonymous_user_id`（JS:631）、`setStorageSync` `auth_token`（JS:654）、`setStorageSync` `auth_user`（JS:655）、`removeStorageSync` `safehome_anonymous_user_id`（JS:656）、`removeStorageSync` `auth_token`（JS:663）、`removeStorageSync` `auth_user`（JS:664）、`getStorageSync` `STORAGE_KEY`（JS:2007）、`setStorageSync` `STORAGE_KEY`（JS:2013）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2049）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2076）
- WXML 数据绑定：`username`、`password`、`roleOptions`、`roleIndex`、`nickname`、`message`、`status`、`loading`
- 条件状态：`message`
- `setData` 状态：`redirectUrl`、`username`、`password`、`nickname`、`roleIndex`、`status`、`message`、`loading`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 04：消息 `pages/messages/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`6fc75722196fb3858552bb01d0796eebdb019777e70528ca744d32ada4dd9b03`
- 核对文件：`apps/miniprogram/pages/messages/index.wxml`、`apps/miniprogram/pages/messages/index.wxss`、`apps/miniprogram/pages/messages/index.js`、`apps/miniprogram/pages/messages/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/errorDiagnostics.js`
- 上游页面：`pages/home/index`、`pages/growth-dashboard/index`、`pages/profile/index`
- 页面组件：`bottom-tip-card` → `/components/bottom-tip-card/index`、`page-state` → `/components/page-state/index`、`status-pill` → `/components/status-pill/index`
- 主要可见内容：消息提醒、需要你看看、这里主要放人工督导补充反馈和必要提醒，不做营销推送。、请求编号： · 服务版本：、复制诊断信息

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | {{needsLogin ?  | `bindaction` | `handleStateAction` | — |
| 12 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | — |
| 16 | — | `bindtap` | `openMessage` | {'id': '{{item.id}}'} |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 25 | `listMessages` | `GET` | `/api/messages` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/ai_qa.py`、`backend/routes/auth_utils.py`、`backend/routes/emotion_thermometer.py`、`backend/routes/general_growth.py`、`backend/routes/messages.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/message-detail/index?id=:dynamic`（js:50）、`reLaunch` → `/pages/home/index`（js:71）、`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fmessages%2Findex`（js:75）、`navigateTo` → `/pages/register/index?redirect=%2Fpages%2Fmessages%2Findex`（js:79）
- 本地存储：`getStorageSync` `auth_user`（JS:273）、`removeStorageSync` `auth_token`（JS:297）、`removeStorageSync` `auth_user`（JS:298）、`getStorageSync` `auth_token`（JS:320）、`setStorageSync` `auth_token`（JS:540）、`setStorageSync` `auth_user`（JS:541）、`removeStorageSync` `safehome_anonymous_user_id`（JS:542）、`setStorageSync` `auth_token`（JS:588）、`setStorageSync` `auth_user`（JS:589）、`setStorageSync` `auth_token`（JS:604）、`setStorageSync` `auth_user`（JS:605）、`removeStorageSync` `safehome_anonymous_user_id`（JS:606）、`setStorageSync` `auth_token`（JS:621）、`setStorageSync` `auth_user`（JS:622）、`removeStorageSync` `safehome_anonymous_user_id`（JS:623）、`setStorageSync` `auth_token`（JS:646）、`setStorageSync` `auth_user`（JS:647）、`removeStorageSync` `safehome_anonymous_user_id`（JS:648）、`removeStorageSync` `auth_token`（JS:655）、`removeStorageSync` `auth_user`（JS:656）、`getStorageSync` `STORAGE_KEY`（JS:1999）、`setStorageSync` `STORAGE_KEY`（JS:2005）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2041）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2068）
- WXML 数据绑定：`loading`、`errorMessage`、`needsLogin`、`errorDiagnostic`、`messages`、`item`
- 条件状态：`loading`、`errorMessage`、`messages`
- `setData` 状态：`loading`、`errorMessage`、`errorDiagnostic`、`needsLogin`、`messages`、`unreadCount`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 05：支持性问答 `pages/support-assistant/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`9efaca379b2bb0bf355277a5ff6aa2ee1585f38415debc7c14e38ef931dd71f0`
- 核对文件：`apps/miniprogram/pages/support-assistant/index.wxml`、`apps/miniprogram/pages/support-assistant/index.wxss`、`apps/miniprogram/pages/support-assistant/index.js`、`apps/miniprogram/pages/support-assistant/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/profile/index`
- 页面组件：—
- 主要可见内容：支持性问答、把问题缩小到下一步、只检索已审核内容，不评价你、孩子或关系的好坏。、当前未开放、你仍可使用记录、训练卡和人工支持。、使用边界、我已阅读并同意AI辅助处理、已记录本次选择、参考内容、你的问题或想法

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 14 | 当前未开放 | `bindaction` | `loadStatus` | — |
| 32 | 确认已阅读使用边界并同意AI辅助处理 | `bindtap` | `enableConsent` | — |
| 62 | 输入你的问题或想法，最多一千字 | `bindinput` | `onQuestionInput` | — |
| 72 | 整理一个小步骤 | `bindtap` | `sendQuestion` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 32 | `getAiQaConfig` | `GET` | `/api/ai-qa/config` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |
| 51 | `createConsent` | `POST` | `/api/consent` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |
| 71 | `createAiQaSession` | `POST` | `/api/ai-qa/sessions` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |
| 88 | `sendAiQaMessage` | `POST` | `/api/ai-qa/sessions` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/login/index?redirect=%2Fpages%2Fsupport-assistant%2Findex`（js:21）、`navigateTo` → `/pages/login/index:dynamic`（js:2135）
- 本地存储：`getStorageSync` `auth_user`（JS:303）、`removeStorageSync` `auth_token`（JS:327）、`removeStorageSync` `auth_user`（JS:328）、`getStorageSync` `auth_token`（JS:350）、`setStorageSync` `auth_token`（JS:570）、`setStorageSync` `auth_user`（JS:571）、`removeStorageSync` `safehome_anonymous_user_id`（JS:572）、`setStorageSync` `auth_token`（JS:618）、`setStorageSync` `auth_user`（JS:619）、`setStorageSync` `auth_token`（JS:634）、`setStorageSync` `auth_user`（JS:635）、`removeStorageSync` `safehome_anonymous_user_id`（JS:636）、`setStorageSync` `auth_token`（JS:651）、`setStorageSync` `auth_user`（JS:652）、`removeStorageSync` `safehome_anonymous_user_id`（JS:653）、`setStorageSync` `auth_token`（JS:676）、`setStorageSync` `auth_user`（JS:677）、`removeStorageSync` `safehome_anonymous_user_id`（JS:678）、`removeStorageSync` `auth_token`（JS:685）、`removeStorageSync` `auth_user`（JS:686）、`getStorageSync` `STORAGE_KEY`（JS:2029）、`setStorageSync` `STORAGE_KEY`（JS:2035）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2071）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2098）、`getStorageSync` `auth_token`（JS:2111）、`getStorageSync` `auth_user`（JS:2115）、`removeStorageSync` `auth_token`（JS:2141）、`removeStorageSync` `auth_user`（JS:2142）
- WXML 数据绑定：`loading`、`error`、`boundary`、`sending`、`messages`、`item`、`question`
- 条件状态：`loading`、`error`、`enabled`、`consented`、`messages`、`item`
- `setData` 状态：`loading`、`error`、`enabled`、`boundary`、`sending`、`consented`、`question`、`sessionId`、`messages`、`role`、`content`、`citations`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 06：消息详情 `pages/message-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`1e08b0edf4c67164a6e0524c1305a4c16bf48cc4aaa9af4bdb1ac02602d3930f`
- 核对文件：`apps/miniprogram/pages/message-detail/index.wxml`、`apps/miniprogram/pages/message-detail/index.wxss`、`apps/miniprogram/pages/message-detail/index.js`、`apps/miniprogram/pages/message-detail/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/messages/index`
- 页面组件：`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：先确认边界、这里的内容适合补充理解一条记录，不适合处理紧急安全风险。如正在经历自伤、自杀、暴力、失控或其他安全风险，请先找现实支持。、返回消息列表

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 3 | — | `bindaction` | `handleStateAction` | — |
| 11 | — | `bindtap` | `openSource` | — |
| 14 | — | `bindselect` | `submitFeedbackEvaluation` | — |
| 24 | 返回消息列表 | `bindtap` | `goMessages` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 31 | `getMessage` | `GET` | `/api/messages` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/ai_qa.py`、`backend/routes/auth_utils.py`、`backend/routes/emotion_thermometer.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py` |
| 76 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/ai_qa.py`、`backend/routes/auth_utils.py`、`backend/routes/emotion_thermometer.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:62）、`navigateTo` → `/pages/relationship-narrative/index?id=:dynamic`（js:66）
- 本地存储：`getStorageSync` `auth_user`（JS:283）、`removeStorageSync` `auth_token`（JS:307）、`removeStorageSync` `auth_user`（JS:308）、`getStorageSync` `auth_token`（JS:330）、`setStorageSync` `auth_token`（JS:550）、`setStorageSync` `auth_user`（JS:551）、`removeStorageSync` `safehome_anonymous_user_id`（JS:552）、`setStorageSync` `auth_token`（JS:598）、`setStorageSync` `auth_user`（JS:599）、`setStorageSync` `auth_token`（JS:614）、`setStorageSync` `auth_user`（JS:615）、`removeStorageSync` `safehome_anonymous_user_id`（JS:616）、`setStorageSync` `auth_token`（JS:631）、`setStorageSync` `auth_user`（JS:632）、`removeStorageSync` `safehome_anonymous_user_id`（JS:633）、`setStorageSync` `auth_token`（JS:656）、`setStorageSync` `auth_user`（JS:657）、`removeStorageSync` `safehome_anonymous_user_id`（JS:658）、`removeStorageSync` `auth_token`（JS:665）、`removeStorageSync` `auth_user`（JS:666）、`getStorageSync` `STORAGE_KEY`（JS:2009）、`setStorageSync` `STORAGE_KEY`（JS:2015）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2051）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2078）
- WXML 数据绑定：`loading`、`errorMessage`、`id`、`message`、`canOpenSource`、`sourceButtonLabel`、`canEvaluate`、`feedbackEvaluation`、`feedbackEvaluationSaving`
- 条件状态：`loading`、`errorMessage`、`canOpenSource`、`canEvaluate`
- `setData` 状态：`id`、`loading`、`errorMessage`、`canOpenSource`、`sourceButtonLabel`、`canEvaluate`、`message`、`feedbackEvaluationSaving`、`feedbackEvaluation`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 07：紧急安全指引 `pages/emergency-guide/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`8acb438006916021a723c1624769c5fed7e49e2664153045479a4775a72845c8`
- 核对文件：`apps/miniprogram/pages/emergency-guide/index.wxml`、`apps/miniprogram/pages/emergency-guide/index.wxss`、`apps/miniprogram/pages/emergency-guide/index.js`、`apps/miniprogram/pages/emergency-guide/index.json`
- 上游页面：`pages/emergency-resources/index`、`pages/profile/index`、`pages/feedback-result/index`
- 页面组件：`section-title` → `/components/section-title/index`
- 主要可见内容：安全优先、先找现实帮助、如果你或孩子正在经历自伤、自杀、暴力、失控或其他安全风险，请优先联系身边可信赖的人、当地紧急服务或线下专业机构。、重要边界、本小程序不能提供实时危机干预、医疗诊断或法律判断。遇到紧急安全风险时，请先使用现实资源。、查看现实支持资源、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 36 | 查看现实支持资源 | `bindtap` | `openResources` | — |
| 37 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`reLaunch` → `/pages/home/index`（js:19）、`navigateTo` → `/pages/emergency-resources/index`（js:23）
- 本地存储：—
- WXML 数据绑定：`supportSteps`、`index`、`item`、`groundingSteps`
- 条件状态：—
- `setData` 状态：—
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 08：紧急帮助说明 `pages/emergency-resources/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`e34d79312078b5bd7cde47fa9e2d5f2b41e48cc8ae2393d737696d14cb51a2ff`
- 核对文件：`apps/miniprogram/pages/emergency-resources/index.wxml`、`apps/miniprogram/pages/emergency-resources/index.wxss`、`apps/miniprogram/pages/emergency-resources/index.js`、`apps/miniprogram/pages/emergency-resources/index.json`
- 上游页面：`pages/emergency-guide/index`、`pages/profile/index`
- 页面组件：—
- 主要可见内容：现实资源、先把人连接上、这里不提供热线号码库，也不判断你是否处于危机。它只提醒：紧急时优先找能真实到场或及时回应的帮助。、使用边界、本工具不能替代紧急服务、线下专业评估、法律判断或医疗诊断。安全风险出现时，请先停止独自处理。、查看紧急安全指引

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 22 | 查看紧急安全指引 | `bindtap` | `goGuide` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/emergency-guide/index`（js:24）
- 本地存储：—
- WXML 数据绑定：`resources`、`item`
- 条件状态：—
- `setData` 状态：—
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 09：三步开始 `pages/getting-started/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`a4a15b560cceb2e987e07c63579237bb6996850549b2cc91396a0e29c5cb20d8`
- 核对文件：`apps/miniprogram/pages/getting-started/index.wxml`、`apps/miniprogram/pages/getting-started/index.wxss`、`apps/miniprogram/pages/getting-started/index.js`、`apps/miniprogram/pages/getting-started/index.json`
- 上游页面：`pages/home/index`
- 页面组件：—
- 主要可见内容：新手说明、用“三步”完成一次最小陪伴练习、当亲子互动里出现压力时，可以先把它看成一条“情绪反射弧”。这里不是给谁下结论，而是帮助你把反应链条看清楚，再选择一个可练习的小位置。、它是什么、情绪反射弧是一条可观察链路、压力不是只来自事件本身，也会经过想法、身体感觉和行为反应。把这条链路拆开看，才更容易找到下一次能调整的一小步。、为什么先记录具体事件、视觉链路、从触发到回应：把反应链条分步看清、在反馈里找到一个位置、记录一次、去训练中心练一个小动作、使用边界、去训练中心

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 54 | 记录一次 | `bindtap` | `startDiary` | — |
| 55 | 去训练中心 | `bindtap` | `openTraining` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index`（js:39）、`switchTab` → `/pages/training/index`（js:43）
- 本地存储：—
- WXML 数据绑定：`eventReasons`、`index`、`item`、`arcNodes`、`exerciseSteps`、`boundaries`
- 条件状态：`index`
- `setData` 状态：—
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 10：情绪温度计 `pages/thermometer/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`c8cfb693286c77b32f7ae992a3c599bd1881f18fd482233e67e436160ddaded3`
- 核对文件：`apps/miniprogram/pages/thermometer/index.wxml`、`apps/miniprogram/pages/thermometer/index.wxss`、`apps/miniprogram/pages/thermometer/index.js`、`apps/miniprogram/pages/thermometer/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/chart.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`
- 页面组件：—
- 主要可见内容：情绪温度计、今天可以记录多次，只看一天里的小变化。、现在的强度、也可以点按调节、补充观察（可保持默认）、愉悦度、身体唤起、可控感、记录一次、刚刚记录完成、先看见这一次、去练一张卡、今日曲线、共 次，平均、刷新、今天还没有记录。先记录一次，再看曲线。、暂时没能完成、重试读取、今天的记录、· 愉悦 · 唤起 · 可控、记录后会按时间显示在这里。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 19 | 调整情绪强度 | `bindtap` | `onThermometerTap` | — |
| 19 | 调整情绪强度 | `bindtouchmove` | `onThermometerMove` | — |
| 39 | 情绪强度减一 | `bindtap` | `decreaseIntensity` | — |
| 40 | 情绪强度加一 | `bindtap` | `increaseIntensity` | — |
| 49 | 调整愉悦度 | `bindchange` | `onValenceChange` | — |
| 49 | 调整愉悦度 | `bindchanging` | `onValenceChange` | — |
| 54 | 调整身体唤起 | `bindchange` | `onArousalChange` | — |
| 54 | 调整身体唤起 | `bindchanging` | `onArousalChange` | — |
| 59 | 调整可控感 | `bindchange` | `onControlChange` | — |
| 59 | 调整可控感 | `bindchanging` | `onControlChange` | — |
| 61 | — | `bindinput` | `onEmotionLabelInput` | — |
| 69 | 记录一次 | `bindinput` | `onBriefInput` | — |
| 76 | 记录一次 | `bindtap` | `saveRecord` | — |
| 85 | 收起记录回执 | `bindtap` | `dismissReceipt` | — |
| 89 | 去练一张卡 | `bindtap` | `openPractice` | — |
| 102 | 刷新 | `bindtap` | `loadDay` | — |
| 104 | 今日情绪强度变化曲线，具体记录见下方列表 | `bindtouchstart` | `handleCanvasTap` | — |
| 123 | 重试读取 | `bindtap` | `loadDay` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index`（js:171）、`navigateTo` → `/pages/login/index:dynamic`（js:2349）
- 本地存储：`getStorageSync` `auth_user`（JS:465）、`removeStorageSync` `auth_token`（JS:489）、`removeStorageSync` `auth_user`（JS:490）、`getStorageSync` `auth_token`（JS:512）、`setStorageSync` `auth_token`（JS:732）、`setStorageSync` `auth_user`（JS:733）、`removeStorageSync` `safehome_anonymous_user_id`（JS:734）、`setStorageSync` `auth_token`（JS:780）、`setStorageSync` `auth_user`（JS:781）、`setStorageSync` `auth_token`（JS:796）、`setStorageSync` `auth_user`（JS:797）、`removeStorageSync` `safehome_anonymous_user_id`（JS:798）、`setStorageSync` `auth_token`（JS:813）、`setStorageSync` `auth_user`（JS:814）、`removeStorageSync` `safehome_anonymous_user_id`（JS:815）、`setStorageSync` `auth_token`（JS:838）、`setStorageSync` `auth_user`（JS:839）、`removeStorageSync` `safehome_anonymous_user_id`（JS:840）、`removeStorageSync` `auth_token`（JS:847）、`removeStorageSync` `auth_user`（JS:848）、`getStorageSync` `STORAGE_KEY`（JS:2191）、`setStorageSync` `STORAGE_KEY`（JS:2197）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2233）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2260）、`getStorageSync` `auth_token`（JS:2325）、`getStorageSync` `auth_user`（JS:2329）、`removeStorageSync` `auth_token`（JS:2355）、`removeStorageSync` `auth_user`（JS:2356）
- WXML 数据绑定：`intensityLevel`、`intensityPercent`、`valenceLevel`、`arousalLevel`、`controlLevel`、`emotionLabel`、`briefText`、`saving`、`receipt`、`item`、`summary`、`selectedPoint`、`errorMessage`、`records`、`boundaryNotice`
- 条件状态：`receipt`、`selectedPoint`、`summary`、`errorMessage`、`item`、`records`
- `setData` 状态：`intensityLevel`、`intensityPercent`、`valenceLevel`、`arousalLevel`、`controlLevel`、`emotionLabel`、`briefText`、`loading`、`errorMessage`、`records`、`timeLabel`、`saving`、`receipt`、`selectedPoint`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 11：训练 `pages/training/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`42c2af8577666cc5ad432a3ed860678a2eff1110b41674f818e65fc11107f36d`
- 核对文件：`apps/miniprogram/pages/training/index.wxml`、`apps/miniprogram/pages/training/index.wxss`、`apps/miniprogram/pages/training/index.js`、`apps/miniprogram/pages/training/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`、`pages/login/index`、`pages/getting-started/index`、`pages/training-history/index`、`pages/growth-dashboard/index`、`pages/course-detail/index`、`pages/assessment-result/index`
- 页面组件：`section-title` → `/components/section-title/index`、`training-task-card` → `/components/training-task-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：从先稳定自己开始、每天选一个小练习，不需要一次做很多。先让身体慢下来，再进入沟通。、看见情绪、慢下来、再回应、训练入口、通用训练、按阶段浏览训练卡、个性化方案、根据测评推荐练习、项目测试、暑期试点练习包、项目试点 · 大学生关系探索、从测一测到评估问题与微行动、聚合阶段性画像、初筛报告、关系绘画、句子补全和连续复盘。它不是治疗或诊断服务。、进入关系探索试点、今天可以先练这个方向、查看练习、推荐理由、今日建议、优先、近期练过，需要巩固时可以再练。、3 天轻量练习、先

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 21 | 个性化方案 | `bindtap` | `openPersonalizedPlan` | — |
| 25 | 项目测试 | `bindtap` | `openProgramList` | — |
| 36 | 进入关系探索试点 | `bindtap` | `openRelationshipPilot` | — |
| 45 | 查看练习 | `bindtap` | `openLatestRecommendation` | — |
| 70 | — | `bindtap` | `toggleLightPlan` | — |
| 72 | — | `bindtap` | `openPlanDay` | {'card-id': '{{item.cardId}}'} |
| 110 | — | `bindtap` | `toggleLibrary` | — |
| 117 | — | `bindtapcard` | `openTrainingCard` | {'id': '{{task.id}}', 'tags': '{{task.tagsText}}'} |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 149 | `getShowcaseAccess` | `GET` | `/api/showcase-access` | `backend/app.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/programs.py`、`backend/routes/showcase_access.py`、`backend/routes/training_plan.py`、`backend/scripts/generate_task32_reliability_registry.py`、`backend/scripts/generate_task34_operations_registry.py` |
| 159 | `getTrainingPlan` | `GET` | `/api/training-plan` | `backend/app.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/programs.py`、`backend/routes/showcase_access.py`、`backend/routes/training_plan.py`、`backend/scripts/generate_task32_reliability_registry.py`、`backend/scripts/generate_task34_operations_registry.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:227）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:242）、`navigateTo` → `/pages/personalized-plan/index`（js:248）、`navigateTo` → `/pages/program-list/index`（js:252）、`navigateTo` → `/pages/relationship-pilot/index`（js:264）、`navigateTo` → `/pages/task-detail/index?id=:dynamic`（js:269）、`navigateTo` → `/pages/login/index:dynamic`（js:2297）
- 本地存储：`getStorageSync` `LATEST_TRAINING_RECOMMENDATION_KEY`（JS:185）、`getStorageSync` `THREE_DAY_LIGHT_PLAN_KEY`（JS:203）、`getStorageSync` `auth_user`（JS:465）、`removeStorageSync` `auth_token`（JS:489）、`removeStorageSync` `auth_user`（JS:490）、`getStorageSync` `auth_token`（JS:512）、`setStorageSync` `auth_token`（JS:732）、`setStorageSync` `auth_user`（JS:733）、`removeStorageSync` `safehome_anonymous_user_id`（JS:734）、`setStorageSync` `auth_token`（JS:780）、`setStorageSync` `auth_user`（JS:781）、`setStorageSync` `auth_token`（JS:796）、`setStorageSync` `auth_user`（JS:797）、`removeStorageSync` `safehome_anonymous_user_id`（JS:798）、`setStorageSync` `auth_token`（JS:813）、`setStorageSync` `auth_user`（JS:814）、`removeStorageSync` `safehome_anonymous_user_id`（JS:815）、`setStorageSync` `auth_token`（JS:838）、`setStorageSync` `auth_user`（JS:839）、`removeStorageSync` `safehome_anonymous_user_id`（JS:840）、`removeStorageSync` `auth_token`（JS:847）、`removeStorageSync` `auth_user`（JS:848）、`getStorageSync` `STORAGE_KEY`（JS:2191）、`setStorageSync` `STORAGE_KEY`（JS:2197）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2233）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2260）、`getStorageSync` `auth_token`（JS:2273）、`getStorageSync` `auth_user`（JS:2277）、`removeStorageSync` `auth_token`（JS:2303）、`removeStorageSync` `auth_user`（JS:2304）
- WXML 数据绑定：`relationshipPilotAvailable`、`latestRecommendation`、`threeDayPlan`、`lightPlanExpanded`、`item`、`libraryExpanded`、`trainingStages`、`task`
- 条件状态：`relationshipPilotAvailable`、`latestRecommendation`、`threeDayPlan`、`lightPlanExpanded`、`libraryExpanded`
- `setData` 状态：`relationshipPilotAvailable`、`latestRecommendation`、`primaryCard`、`cardIdsText`、`threeDayPlan`、`cardIds`、`cards`、`sourceLabel`、`days`、`lightPlanExpanded`、`libraryExpanded`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 12：训练记录 `pages/training-history/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`d898076f09f5a70dd625ffb0c358797b24d9366b248362beac3a1b43a67a5198`
- 核对文件：`apps/miniprogram/pages/training-history/index.wxml`、`apps/miniprogram/pages/training-history/index.wxss`、`apps/miniprogram/pages/training-history/index.js`、`apps/miniprogram/pages/training-history/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/errorDiagnostics.js`
- 上游页面：`pages/profile/index`
- 页面组件：—
- 主要可见内容：训练记录、看见已经完成的小练习、这里只记录真实打卡。已完成的训练卡不会继续出现在默认推荐中，但你仍可主动再次练习。、次记录、正在读取训练记录、记录暂时没有加载成功、请求编号： · 服务版本：、重新加载、复制诊断信息、再次练习、已显示全部 次记录、还没有训练记录、完成一张训练卡并打卡后，记录会出现在这里。、去训练中心

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 22 | 重新加载 | `bindtap` | `retry` | — |
| 23 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | — |
| 36 | 再次练习 | `bindtap` | `openCard` | {'card-id': '{{item.card_id}}'} |
| 39 | — | `bindtap` | `loadMore` | — |
| 42 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | — |
| 49 | 去训练中心 | `bindtap` | `goTraining` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 56 | `listCheckins` | `GET` | `/api/checkins` | `backend/app.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/checkins.py`、`backend/routes/general_growth.py`、`backend/routes/profile.py`、`backend/routes/research_workspace.py`、`backend/routes/training_plan.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:99）、`switchTab` → `/pages/training/index`（js:103）、`navigateTo` → `/pages/login/index:dynamic`（js:2129）
- 本地存储：`getStorageSync` `auth_user`（JS:297）、`removeStorageSync` `auth_token`（JS:321）、`removeStorageSync` `auth_user`（JS:322）、`getStorageSync` `auth_token`（JS:344）、`setStorageSync` `auth_token`（JS:564）、`setStorageSync` `auth_user`（JS:565）、`removeStorageSync` `safehome_anonymous_user_id`（JS:566）、`setStorageSync` `auth_token`（JS:612）、`setStorageSync` `auth_user`（JS:613）、`setStorageSync` `auth_token`（JS:628）、`setStorageSync` `auth_user`（JS:629）、`removeStorageSync` `safehome_anonymous_user_id`（JS:630）、`setStorageSync` `auth_token`（JS:645）、`setStorageSync` `auth_user`（JS:646）、`removeStorageSync` `safehome_anonymous_user_id`（JS:647）、`setStorageSync` `auth_token`（JS:670）、`setStorageSync` `auth_user`（JS:671）、`removeStorageSync` `safehome_anonymous_user_id`（JS:672）、`removeStorageSync` `auth_token`（JS:679）、`removeStorageSync` `auth_user`（JS:680）、`getStorageSync` `STORAGE_KEY`（JS:2023）、`setStorageSync` `STORAGE_KEY`（JS:2029）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2065）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2092）、`getStorageSync` `auth_token`（JS:2105）、`getStorageSync` `auth_user`（JS:2109）、`removeStorageSync` `auth_token`（JS:2135）、`removeStorageSync` `auth_user`（JS:2136）
- WXML 数据绑定：`total`、`loading`、`errorMessage`、`errorDiagnostic`、`items`、`item`、`hasMore`、`loadingMore`
- 条件状态：`loading`、`errorMessage`、`items`、`item`、`hasMore`
- `setData` 状态：`loading`、`loadingMore`、`errorMessage`、`errorDiagnostic`、`items`、`page`、`total`、`hasMore`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 13：个性化训练方案 `pages/personalized-plan/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`04981fc9b01230edcddcdd7b4795b2b728fe921c6f83608eb83504593f30f16d`
- 核对文件：`apps/miniprogram/pages/personalized-plan/index.wxml`、`apps/miniprogram/pages/personalized-plan/index.wxss`、`apps/miniprogram/pages/personalized-plan/index.js`、`apps/miniprogram/pages/personalized-plan/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/training/index`
- 页面组件：—
- 主要可见内容：个性化训练方案、根据最近测评和阶段性画像，推荐更适合先练的小动作。、安排练习节奏、先选一个当前可承受的频率，之后可以随时调整。、当前阶段、练习频率、开始日期、计划状态、保存练习节奏、提醒、微信练习提醒、只在你主动授权后发送；关闭提醒不影响训练。、暂未开放、管理员完成微信模板审核后，这里可以开启。、已同意本次提醒、到达下一次练习日期后发送；一次性授权使用后需要重新开启。、上次授权已使用、如需下一次提醒，请再次主动开启。、微信设置中已关闭、如需恢复，请前往小程序设置调整订阅消息权限。、需要时再开启、建议在保存好练习节奏后，开启一次微信提醒。、开启一次微信提醒、前往微信设置

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 18 | — | `bindtap` | `selectAssignmentOption` | {'field': 'phase', 'value': '{{item.value}}'} |
| 30 | — | `bindtap` | `selectAssignmentOption` | {'field': 'cadence', 'value': '{{item.value}}'} |
| 42 | — | `bindchange` | `onStartDateChange` | — |
| 49 | — | `bindtap` | `selectAssignmentOption` | {'field': 'status', 'value': '{{item.value}}'} |
| 60 | 保存练习节奏 | `bindinput` | `onGoalInput` | — |
| 67 | 保存练习节奏 | `bindtap` | `saveAssignment` | — |
| 103 | 开启一次微信提醒 | `bindtap` | `requestTrainingReminder` | — |
| 109 | 前往微信设置 | `bindtap` | `openNotificationSettings` | — |
| 119 | 去测一测 | `bindtap` | `openAssessment` | — |
| 130 | — | `bindtap` | `openSingleCard` | {'card-id': '{{card.id}}'} |
| 148 | 重试 | `bindtap` | `loadPlan` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment/index`（js:176）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:185）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:191）
- 本地存储：`getStorageSync` `auth_user`（JS:385）、`removeStorageSync` `auth_token`（JS:409）、`removeStorageSync` `auth_user`（JS:410）、`getStorageSync` `auth_token`（JS:432）、`setStorageSync` `auth_token`（JS:652）、`setStorageSync` `auth_user`（JS:653）、`removeStorageSync` `safehome_anonymous_user_id`（JS:654）、`setStorageSync` `auth_token`（JS:700）、`setStorageSync` `auth_user`（JS:701）、`setStorageSync` `auth_token`（JS:716）、`setStorageSync` `auth_user`（JS:717）、`removeStorageSync` `safehome_anonymous_user_id`（JS:718）、`setStorageSync` `auth_token`（JS:733）、`setStorageSync` `auth_user`（JS:734）、`removeStorageSync` `safehome_anonymous_user_id`（JS:735）、`setStorageSync` `auth_token`（JS:758）、`setStorageSync` `auth_user`（JS:759）、`removeStorageSync` `safehome_anonymous_user_id`（JS:760）、`removeStorageSync` `auth_token`（JS:767）、`removeStorageSync` `auth_user`（JS:768）、`getStorageSync` `STORAGE_KEY`（JS:2111）、`setStorageSync` `STORAGE_KEY`（JS:2117）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2153）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2180）
- WXML 数据绑定：`assignment`、`phaseOptions`、`item`、`cadenceOptions`、`statusOptions`、`savingAssignment`、`plan`、`notification`、`requestingReminder`、`planItems`、`card`、`loading`、`errorMessage`、`boundaryNotice`
- 条件状态：`assignment`、`plan`、`notification`、`loading`、`item`、`card`
- `setData` 状态：`notification`、`preference`、`loading`、`errorMessage`、`planItems`、`sourceLabel`、`cardIdsText`、`plan`、`assignment`、`savingAssignment`、`requestingReminder`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 14：项目测试 `pages/program-list/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`af85f02ae4c74a4ed827cf7be6a9bf2bc436c0a84a762ff2bddb56f7b3d00a29`
- 核对文件：`apps/miniprogram/pages/program-list/index.wxml`、`apps/miniprogram/pages/program-list/index.wxss`、`apps/miniprogram/pages/program-list/index.js`、`apps/miniprogram/pages/program-list/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/training/index`
- 页面组件：—
- 主要可见内容：项目测试、先选一个主题，按小节慢慢练习。、研究者预览：草案仅供审核，不可作为正式项目提交。、小节、第一节：、已有 个方案完成开发，待研究、心理和伦理审核。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | 打开项目：{{item.title}} | `bindtap` | `openProgram` | {'id': '{{item.id}}', 'preview': '{{item.preview_only}}'} |
| 24 | <text wx:if="{{!loading && !errorMessage && !pro | `bindaction` | `loadPrograms` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/program-detail/index?id=:dynamic`（js:50）、`navigateTo` → `/pages/login/index:dynamic`（js:2076）
- 本地存储：`getStorageSync` `auth_user`（JS:244）、`removeStorageSync` `auth_token`（JS:268）、`removeStorageSync` `auth_user`（JS:269）、`getStorageSync` `auth_token`（JS:291）、`setStorageSync` `auth_token`（JS:511）、`setStorageSync` `auth_user`（JS:512）、`removeStorageSync` `safehome_anonymous_user_id`（JS:513）、`setStorageSync` `auth_token`（JS:559）、`setStorageSync` `auth_user`（JS:560）、`setStorageSync` `auth_token`（JS:575）、`setStorageSync` `auth_user`（JS:576）、`removeStorageSync` `safehome_anonymous_user_id`（JS:577）、`setStorageSync` `auth_token`（JS:592）、`setStorageSync` `auth_user`（JS:593）、`removeStorageSync` `safehome_anonymous_user_id`（JS:594）、`setStorageSync` `auth_token`（JS:617）、`setStorageSync` `auth_user`（JS:618）、`removeStorageSync` `safehome_anonymous_user_id`（JS:619）、`removeStorageSync` `auth_token`（JS:626）、`removeStorageSync` `auth_user`（JS:627）、`getStorageSync` `STORAGE_KEY`（JS:1970）、`setStorageSync` `STORAGE_KEY`（JS:1976）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2012）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2039）、`getStorageSync` `auth_token`（JS:2052）、`getStorageSync` `auth_user`（JS:2056）、`removeStorageSync` `auth_token`（JS:2082）、`removeStorageSync` `auth_user`（JS:2083）
- WXML 数据绑定：`previewMode`、`programs`、`item`、`loading`、`errorMessage`、`availability`、`boundaryNotice`
- 条件状态：`previewMode`、`loading`
- `setData` 状态：`loading`、`errorMessage`、`programs`、`availability`、`boundaryNotice`、`previewMode`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 15：项目详情 `pages/program-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`cabb403361d47c3fa0ac5a6d7e08bee3d045d18dcf49c490474c401ba548d4d9`
- 核对文件：`apps/miniprogram/pages/program-detail/index.wxml`、`apps/miniprogram/pages/program-detail/index.wxss`、`apps/miniprogram/pages/program-detail/index.js`、`apps/miniprogram/pages/program-detail/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/home/index`、`pages/program-list/index`
- 页面组件：—
- 主要可见内容：项目测试、· 方案、参与前先了解、适合参加的基本条件、这些情况先不要继续、可选替代：、项目记录节奏、用于安排开始前、练习中和完成后的阶段记录。、第 节、研究者只读预览：当前草案尚未完成三方审核，填写、保存和提交均已关闭。、预计 分钟、练习步骤、书写提示、保存本机草稿、反思问题、完成标准：、停止提示：、练习前不适程度： / 10、练习后不适程度： / 10、这次练习出现了明显不适或负面体验，需要后续关注。、允许将本次内容用于脱敏聚合分析，不默认展示原文。、登录后正式提交、我已提交的项目记录、提交内容会保留在本人记录中，并按授权范围供研究者只读查看。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 47 | 第 节 | `bindtap` | `selectSession` | {'session-no': '{{item.session_no}}'} |
| 75 | 保存本机草稿 | `bindinput` | `onDraftInput` | — |
| 76 | 保存本机草稿 | `bindtap` | `saveDraft` | — |
| 83 | — | `bindinput` | `onReflectionInput` | {'index': '{{index}}'} |
| 100 | 练习后不适程度： / 10 | `bindchange` | `onDistressBeforeChange` | — |
| 102 | 这次练习出现了明显不适或负面体验，需要后续关注。 | `bindchange` | `onDistressAfterChange` | — |
| 103 | 这次练习出现了明显不适或负面体验，需要后续关注。 | `bindchange` | `onAdverseResponseChange` | — |
| 109 | 允许将本次内容用于脱敏聚合分析，不默认展示原文。 | `bindchange` | `onAnalysisConsentChange` | — |
| 117 | 登录后正式提交 | `bindtap` | `submitEntry` | — |
| 141 | 重试 | `bindtap` | `retryLoad` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 172 | `listProgramEntries` | `GET` | `/api/programs/:id/entries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/programs.py` |
| 203 | `createProgramEntry` | `POST` | `/api/programs/:id/entries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/programs.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `draftKey`（JS:118）、`setStorageSync` `draftKey`（JS:163）、`removeStorageSync` `draftKey`（JS:219）、`getStorageSync` `auth_user`（JS:426）、`removeStorageSync` `auth_token`（JS:450）、`removeStorageSync` `auth_user`（JS:451）、`getStorageSync` `auth_token`（JS:473）、`setStorageSync` `auth_token`（JS:693）、`setStorageSync` `auth_user`（JS:694）、`removeStorageSync` `safehome_anonymous_user_id`（JS:695）、`setStorageSync` `auth_token`（JS:741）、`setStorageSync` `auth_user`（JS:742）、`setStorageSync` `auth_token`（JS:757）、`setStorageSync` `auth_user`（JS:758）、`removeStorageSync` `safehome_anonymous_user_id`（JS:759）、`setStorageSync` `auth_token`（JS:774）、`setStorageSync` `auth_user`（JS:775）、`removeStorageSync` `safehome_anonymous_user_id`（JS:776）、`setStorageSync` `auth_token`（JS:799）、`setStorageSync` `auth_user`（JS:800）、`removeStorageSync` `safehome_anonymous_user_id`（JS:801）、`removeStorageSync` `auth_token`（JS:808）、`removeStorageSync` `auth_user`（JS:809）、`getStorageSync` `STORAGE_KEY`（JS:2152）、`setStorageSync` `STORAGE_KEY`（JS:2158）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2194）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2221）
- WXML 数据绑定：`program`、`item`、`sessions`、`selectedSession`、`previewMode`、`index`、`draftText`、`reflectionAnswers`、`distressBefore`、`distressAfter`、`adverseResponse`、`analysisConsent`、`successMessage`、`errorMessage`、`submitting`、`submittedEntries`、`loading`
- 条件状态：`program`、`selectedSession`、`previewMode`、`successMessage`、`errorMessage`、`loading`
- `setData` 状态：`programId`、`previewMode`、`requestedSessionNo`、`loading`、`errorMessage`、`program`、`sessions`、`selectedSession`、`draftText`、`reflectionAnswers`、`successMessage`、`analysisConsent`、`distressBefore`、`distressAfter`、`adverseResponse`、`submittedEntries`、`createdAtText`、`sessionText`、`submitting`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 16：关系探索试点 `pages/relationship-pilot/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`7a7e4a3a6d0539c7411e32b10ff01d7e6baeb0c600fab9f79fd2aa2610a94dc8`
- 核对文件：`apps/miniprogram/pages/relationship-pilot/index.wxml`、`apps/miniprogram/pages/relationship-pilot/index.wxss`、`apps/miniprogram/pages/relationship-pilot/index.js`、`apps/miniprogram/pages/relationship-pilot/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/training/index`、`pages/relationship-growth/index`、`pages/growth-dashboard/index`
- 页面组件：`journey-action-card` → `/components/journey-action-card/index`
- 主要可见内容：项目试点 · 大学生关系探索、一次只走好当前这一步、从起点测评到连续记录，每一步都可以暂停。这里不判断你是否“适合恋爱”，也不替代心理咨询。、正在读取你的探索进度...、当前仅向学生试点账号开放、你仍可使用情绪记录、训练卡和其它支持功能。若需参加关系探索试点，请切换到已授权的学生账号。、第一步 · 起点测评与报名、确认是否进入第二阶段、报名会关联你最近一份关系探索测评的维度、阶段性画像与报告。逐行研究数据不会显示给其他用户。、我已阅读并同意将本次测评用于关系探索试点的评估与复盘。、确认报名、还没测评？先完成关系测一测、五阶段探索路径、其它入口、不必一次完成，可以随时回来。、所有画像和报告都只作阶段性观察，不构成诊断、人格标签、关系能力评价或疗效证明。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 19 | 我已阅读并同意将本次测评用于关系探索试点的评估与复盘。 | `bindchange` | `toggleConsent` | — |
| 22 | 确认报名 | `bindtap` | `enroll` | — |
| 23 | 还没测评？先完成关系测一测 | `bindtap` | `goAssessment` | — |
| 27 | 关系探索当前步骤 | `bindaction` | `runPrimaryAction` | — |
| 57 | — | `bindtap` | `runSecondaryAction` | {'action': '{{item.key}}'} |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 69 | `getShowcaseAccess` | `GET` | `/api/showcase-access` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/programs.py` |
| 81 | `listRelationshipEnrollments` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/programs.py` |
| 86 | `getRelationshipGrowth` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/programs.py` |
| 129 | `createRelationshipEnrollment` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/programs.py` |
| 149 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/programs.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment/index?audience_class=student&query=%E5%85%B3%E7%B3%BB`（js:165）、`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:174）、`navigateTo` → `/pages/relationship-task/index?type=relationship_drawing&enrollment_id=:dynamic`（js:178）、`navigateTo` → `/pages/relationship-task/index?type=sentence_completion&enrollment_id=:dynamic`（js:182）、`navigateTo` → `/pages/relationship-growth/index?detail=1&enrollment_id=:dynamic`（js:186）、`navigateTo` → `/pages/login/index:dynamic`（js:2214）
- 本地存储：`getStorageSync` `auth_user`（JS:382）、`removeStorageSync` `auth_token`（JS:406）、`removeStorageSync` `auth_user`（JS:407）、`getStorageSync` `auth_token`（JS:429）、`setStorageSync` `auth_token`（JS:649）、`setStorageSync` `auth_user`（JS:650）、`removeStorageSync` `safehome_anonymous_user_id`（JS:651）、`setStorageSync` `auth_token`（JS:697）、`setStorageSync` `auth_user`（JS:698）、`setStorageSync` `auth_token`（JS:713）、`setStorageSync` `auth_user`（JS:714）、`removeStorageSync` `safehome_anonymous_user_id`（JS:715）、`setStorageSync` `auth_token`（JS:730）、`setStorageSync` `auth_user`（JS:731）、`removeStorageSync` `safehome_anonymous_user_id`（JS:732）、`setStorageSync` `auth_token`（JS:755）、`setStorageSync` `auth_user`（JS:756）、`removeStorageSync` `safehome_anonymous_user_id`（JS:757）、`removeStorageSync` `auth_token`（JS:764）、`removeStorageSync` `auth_user`（JS:765）、`getStorageSync` `STORAGE_KEY`（JS:2108）、`setStorageSync` `STORAGE_KEY`（JS:2114）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2150）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2177）、`getStorageSync` `auth_token`（JS:2190）、`getStorageSync` `auth_user`（JS:2194）、`removeStorageSync` `auth_token`（JS:2220）、`removeStorageSync` `auth_user`（JS:2221）
- WXML 数据绑定：`loading`、`roleBlocked`、`consent`、`submitting`、`currentStepNumber`、`currentActionState`、`reportStatusText`、`currentStageTitle`、`enrollment`、`primaryLabel`、`journeySteps`、`item`、`secondaryActions`、`errorMessage`
- 条件状态：`loading`、`roleBlocked`、`enrollment`、`errorMessage`
- `setData` 状态：`loading`、`roleBlocked`、`errorMessage`、`journeySteps`、`currentStepNumber`、`currentActionState`、`currentStageTitle`、`primaryAction`、`primaryLabel`、`reportStatusText`、`enrollment`、`secondaryActions`、`consent`、`submitting`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 17：关系健康初筛报告 `pages/relationship-report/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`6af2d45c018233b03b12a5966d5a89a4554d02fe8cee33de9b3e42a652353757`
- 核对文件：`apps/miniprogram/pages/relationship-report/index.wxml`、`apps/miniprogram/pages/relationship-report/index.wxss`、`apps/miniprogram/pages/relationship-report/index.js`、`apps/miniprogram/pages/relationship-report/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/message-detail/index`、`pages/relationship-pilot/index`、`pages/researcher-dashboard/index`
- 页面组件：`relationship-status` → `/components/relationship-status/index`、`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：正在人工核对、研究者完成核对并发送后，你会在消息列表收到提醒。当前不会展示画像、解释或机制假设。、需要多一点人工核对、基础画像、本次维度轮廓、条形只表示本次在参考样本中的相对位置，不代表好坏或能力排名。、矛盾画像、两种需要可能同时存在、靠近与行动意愿、同时、保护与现实节奏、机制画像、待核对假设、这些只是讨论线索。请以你的真实经验为准，共同修订比“被系统定义”更重要。、当前选择：、符合、不符合、不确定、动态画像、连续记录、已有 次记录，变化只作为讨论线索。、目前只有一次记录。完成两次以上后，才显示趋势箭头。、可以带去讨论的问题、建议的项目任务

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 3 | 正在人工核对 | `bindaction` | `loadReport` | — |
| 25 | — | `bindselect` | `submitReportEvaluation` | — |
| 55 | 符合 | `bindtap` | `saveHypothesisFeedback` | {'index': '{{item.index}}', 'response': 'matches'} |
| 56 | 不符合 | `bindtap` | `saveHypothesisFeedback` | {'index': '{{item.index}}', 'response': 'does_not_match'} |
| 57 | 不确定 | `bindtap` | `saveHypothesisFeedback` | {'index': '{{item.index}}', 'response': 'uncertain'} |
| 89 | 生成脱敏报告长图 | `bindtap` | `drawLongImage` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 81 | `getRelationshipReport` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |
| 127 | `saveRelationshipHypothesisFeedback` | `PUT` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |
| 145 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |
| 222 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `auth_user`（JS:428）、`removeStorageSync` `auth_token`（JS:452）、`removeStorageSync` `auth_user`（JS:453）、`getStorageSync` `auth_token`（JS:475）、`setStorageSync` `auth_token`（JS:695）、`setStorageSync` `auth_user`（JS:696）、`removeStorageSync` `safehome_anonymous_user_id`（JS:697）、`setStorageSync` `auth_token`（JS:743）、`setStorageSync` `auth_user`（JS:744）、`setStorageSync` `auth_token`（JS:759）、`setStorageSync` `auth_user`（JS:760）、`removeStorageSync` `safehome_anonymous_user_id`（JS:761）、`setStorageSync` `auth_token`（JS:776）、`setStorageSync` `auth_user`（JS:777）、`removeStorageSync` `safehome_anonymous_user_id`（JS:778）、`setStorageSync` `auth_token`（JS:801）、`setStorageSync` `auth_user`（JS:802）、`removeStorageSync` `safehome_anonymous_user_id`（JS:803）、`removeStorageSync` `auth_token`（JS:810）、`removeStorageSync` `auth_user`（JS:811）、`getStorageSync` `STORAGE_KEY`（JS:2154）、`setStorageSync` `STORAGE_KEY`（JS:2160）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2196）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2223）
- WXML 数据绑定：`loading`、`errorMessage`、`deliveryPending`、`report`、`record`、`statusSteps`、`item`、`attentionNotice`、`reportEvaluation`、`reportEvaluationSaving`、`radarRows`、`mechanismCards`、`isStageFeedback`、`index`、`exporting`、`shareCanvasHeight`
- 条件状态：`loading`、`errorMessage`、`deliveryPending`、`attentionNotice`、`radarRows`、`report`、`mechanismCards`
- `setData` 状态：`id`、`loading`、`errorMessage`、`report`、`deliveryPending`、`statusText`、`statusSteps`、`record`、`isStageFeedback`、`radarRows`、`mechanismCards`、`attentionNotice`、`feedbackSavingIndex`、`reportEvaluationSaving`、`reportEvaluation`、`shareCanvasHeight`、`exporting`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 18：关系探索任务 `pages/relationship-task/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`f23c49dde3d3f73c7c7d52cd1d2b01b1855053c6ed179930bdcf5e5246dd6e88`
- 核对文件：`apps/miniprogram/pages/relationship-task/index.wxml`、`apps/miniprogram/pages/relationship-task/index.wxss`、`apps/miniprogram/pages/relationship-task/index.js`、`apps/miniprogram/pages/relationship-task/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/home/index`、`pages/relationship-pilot/index`
- 页面组件：—
- 主要可见内容：线上探索材料、已恢复上次未提交的本机草稿，你可以接着完成。、画布、可撤销、重做，草稿自动留在本机、撤销、重做、清空、给这幅画写一两句画外音、已填写、如果在“ ”的情境里，会怎样？、本题可以跳过、我同意将这份敏感叙事材料用于本次试点评估与人工复核；默认不导出原文。、材料只作为访谈和共同理解的线索，不自动解释潜意识、人格、依恋类型或病理模式。、提交这份材料

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 12 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchstart` | `startStroke` | — |
| 12 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchmove` | `moveStroke` | — |
| 12 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchend` | `endStroke` | — |
| 14 | 撤销 | `bindtap` | `undoStroke` | — |
| 15 | 重做 | `bindtap` | `redoStroke` | — |
| 16 | 清空 | `bindtap` | `clearCanvas` | — |
| 20 | — | `bindinput` | `onNarrationInput` | — |
| 27 | — | `bindtap` | `toggleContext` | {'key': '{{item.key}}'} |
| 33 | — | `bindinput` | `onSentenceInput` | {'key': '{{item.key}}'} |
| 39 | 我同意将这份敏感叙事材料用于本次试点评估与人工复核；默认不导出原文。 | `bindchange` | `toggleConsent` | — |
| 43 | 提交这份材料 | `bindtap` | `saveTask` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 318 | `createRelationshipTask` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py` |
| 328 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py` |
| 351 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `this`（JS:87）、`removeStorageSync` `this`（JS:138）、`setStorageSync` `this`（JS:143）、`removeStorageSync` `this`（JS:334）、`getStorageSync` `auth_user`（JS:557）、`removeStorageSync` `auth_token`（JS:581）、`removeStorageSync` `auth_user`（JS:582）、`getStorageSync` `auth_token`（JS:604）、`setStorageSync` `auth_token`（JS:824）、`setStorageSync` `auth_user`（JS:825）、`removeStorageSync` `safehome_anonymous_user_id`（JS:826）、`setStorageSync` `auth_token`（JS:872）、`setStorageSync` `auth_user`（JS:873）、`setStorageSync` `auth_token`（JS:888）、`setStorageSync` `auth_user`（JS:889）、`removeStorageSync` `safehome_anonymous_user_id`（JS:890）、`setStorageSync` `auth_token`（JS:905）、`setStorageSync` `auth_user`（JS:906）、`removeStorageSync` `safehome_anonymous_user_id`（JS:907）、`setStorageSync` `auth_token`（JS:930）、`setStorageSync` `auth_user`（JS:931）、`removeStorageSync` `safehome_anonymous_user_id`（JS:932）、`removeStorageSync` `auth_token`（JS:939）、`removeStorageSync` `auth_user`（JS:940）、`getStorageSync` `STORAGE_KEY`（JS:2283）、`setStorageSync` `STORAGE_KEY`（JS:2289）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2325）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2352）
- WXML 数据绑定：`isDrawing`、`saving`、`saveStatus`、`draftRestored`、`narration`、`narrationCount`、`contextItems`、`item`、`consent`
- 条件状态：`draftRestored`、`isDrawing`、`item`
- `setData` 状态：`isDrawing`、`contextItems`、`narration`、`narrationCount`、`consent`、`saveStatus`、`draftRestored`、`hasLocalDraft`、`canUndo`、`canRedo`、`enrollmentId`、`taskType`、`answers`、`saving`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 19：关系探索成长仪表盘 `pages/relationship-growth/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`3977efd960deaa3a2be77a3a407e143f71183d3e3956310a605cf21a97716586`
- 核对文件：`apps/miniprogram/pages/relationship-growth/index.wxml`、`apps/miniprogram/pages/relationship-growth/index.wxss`、`apps/miniprogram/pages/relationship-growth/index.js`、`apps/miniprogram/pages/relationship-growth/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/relationship-pilot/index`、`pages/growth-dashboard/index`
- 页面组件：`visualization-state` → `/components/visualization-state/index`
- 主要可见内容：关系探索成长仪表盘、变化记录，不是疗效证明、把不同类型的变化分开看，保留可回顾的事实与阶段性反馈。、正在读取成长记录...、累计记录、条、可看指标组、组、阶段性反馈、变化曲线、每组数字含义不同，不合并成总分、再记录 次后可查看变化趋势、持续记录，帮助你看见同一指标在不同时间的变化。、数据不足、目前有 个记录点；这里不会根据单次记录判断变化。、最近时间线、先看最近三条，再决定是否展开、查看全部 ›、还没有时间线记录，可以先写下今天的一小步。、成长时间线、按记录类型查看，不急于解释趋势、这一类还没有记录。、系统汇总与研究者补充明确分开、研究者补充

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 33 | 查看{{item.label}} | `bindtap` | `selectSection` | {'section': '{{item.key}}'} |
| 43 | — | `bindtap` | `selectCurveGroup` | {'key': '{{item.key}}'} |
| 44 | — | `bindtap` | `selectMetric` | {'key': '{{item.key}}'} |
| 65 | 查看全部 › | `bindtap` | `showAllTimeline` | — |
| 79 | — | `bindtap` | `selectTimelineFilter` | {'key': '{{item.key}}'} |
| 93 | 用户原话（仅你可见） | `bindtap` | `toggleSelfNarratives` | — |
| 101 | 前往关系探索 | `bindtap` | `goRelationshipPilot` | — |
| 105 | 本周补充记录 | `bindtap` | `toggleRecordPanel` | {'panel': 'weekly'} |
| 107 | — | `bindinput` | `onFieldInput` | {'key': 'active_social_count'} |
| 108 | — | `bindinput` | `onFieldInput` | {'key': 'authentic_expression_count'} |
| 109 | — | `bindinput` | `onFieldInput` | {'key': 'setback_coping'} |
| 110 | — | `bindchange` | `onSliderChange` | {'key': 'approach_willingness'} |
| 111 | — | `bindchange` | `onSliderChange` | {'key': 'worry_intensity'} |
| 112 | — | `bindinput` | `onFieldInput` | {'key': 'achievement'} |
| 113 | — | `bindinput` | `onFieldInput` | {'key': 'setback'} |
| 116 | 保存本周记录 | `bindtap` | `saveWeekly` | — |
| 121 | 记录一个关键事件 | `bindtap` | `toggleRecordPanel` | {'panel': 'event'} |
| 123 | — | `bindinput` | `onFieldInput` | {'key': 'event_summary'} |
| 125 | 加入时间线 | `bindtap` | `saveEvent` | — |
| 131 | 共同理解一次关系体验 | `bindtap` | `goTherapeuticAssessment` | — |
| 132 | 记录今天的一小步 | `bindtap` | `openRecordSection` | — |
| 133 | 查看阶段性反馈 | `bindtap` | `showFeedbackSection` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 182 | `getRelationshipGrowth` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py`、`backend/routes/research_workspace.py` |
| 400 | `createRelationshipLongitudinal` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py`、`backend/routes/research_workspace.py` |
| 445 | `createRelationshipLongitudinal` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py`、`backend/routes/research_workspace.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/therapeutic-assessment/index`（js:135）、`redirectTo` → `/pages/growth-dashboard/index?section=relationship:dynamic`（js:144）、`navigateTo` → `/pages/relationship-pilot/index`（js:389）
- 本地存储：`getStorageSync` `auth_user`（JS:654）、`removeStorageSync` `auth_token`（JS:678）、`removeStorageSync` `auth_user`（JS:679）、`getStorageSync` `auth_token`（JS:701）、`setStorageSync` `auth_token`（JS:921）、`setStorageSync` `auth_user`（JS:922）、`removeStorageSync` `safehome_anonymous_user_id`（JS:923）、`setStorageSync` `auth_token`（JS:969）、`setStorageSync` `auth_user`（JS:970）、`setStorageSync` `auth_token`（JS:985）、`setStorageSync` `auth_user`（JS:986）、`removeStorageSync` `safehome_anonymous_user_id`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1027）、`setStorageSync` `auth_user`（JS:1028）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1029）、`removeStorageSync` `auth_token`（JS:1036）、`removeStorageSync` `auth_user`（JS:1037）、`getStorageSync` `STORAGE_KEY`（JS:2380）、`setStorageSync` `STORAGE_KEY`（JS:2386）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2422）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2449）、`getStorageSync` `storageKey`（JS:2484）、`setStorageSync` `storageKey`（JS:2506）、`removeStorageSync` `storageKey`（JS:2536）
- WXML 数据绑定：`loading`、`growth`、`curveGroups`、`researcherConfirmations`、`false`、`sectionTabs`、`activeSection`、`item`、`selectedGroup`、`selectedMetrics`、`selectedMetric`、`selectedMetricLabel`、`selectedPoints`、`trendText`、`recentTimeline`、`timelineFilters`、`timelineFilter`、`filteredTimeline`、`showSelfNarratives`、`selfNarratives`、`canRecord`、`showWeeklyForm`、`form`、`draftRestored`、`saveStatus`、`slowSaving`、`savingWeekly`、`showEventForm`、`savingEvent`、`errorMessage`
- 条件状态：`loading`、`growth`、`activeSection`、`curveGroups`、`selectedPoints`、`recentTimeline`、`filteredTimeline`、`researcherConfirmations`、`showSelfNarratives`、`selfNarratives`、`canRecord`、`showWeeklyForm`、`slowSaving`、`showEventForm`、`errorMessage`
- `setData` 状态：`enrollmentId`、`loading`、`errorMessage`、`canRecord`、`curves`、`filteredTimeline`、`recentTimeline`、`selfNarratives`、`researcherConfirmations`、`dateText`、`growth`、`curveGroups`、`selectedGroup`、`selectedMetric`、`selectedMetrics`、`selectedPoints`、`trendText`、`selectedMetricLabel`、`activeSection`、`showWeeklyForm`、`showEventForm`、`timelineFilter`、`showSelfNarratives`、`saveStatus`、`savingWeekly`、`slowSaving`、`weeklySubmissionKey`、`savingEvent`、`eventSubmissionKey`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 20：共同理解 `pages/therapeutic-assessment/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`eab4d026a08ba3500f6b7902a21e913e3e41bf38133087da623bf8e1c1877fcd`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment/index.wxss`、`apps/miniprogram/pages/therapeutic-assessment/index.js`、`apps/miniprogram/pages/therapeutic-assessment/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/relationship-growth/index`、`pages/therapeutic-assessment-action-followup/index`
- 页面组件：—
- 主要可见内容：· 可撤回、共同理解一次关系体验、从你真正关心的问题出发，决定愿意共享什么。反馈是可讨论的版本，不是对你或关系的定论。、协作边界已对齐、服务级别、人员胜任力、对象权限和安全状态分别判断；任一项未知都会暂停继续。、当前首发范围、仅面向自愿参加、单人资料、非紧急议题的成年人，提供L1/L2真人支持性协作。、确认符合上述范围、范围记录：、未成年人/亲子子线、当前入口未开放。监护人同意和儿童知情、同意或拒绝会分别记录。、伴侣与多人子线、当前入口未开放。每个人的个别披露默认不会进入共同反馈。、AI只提供可拒绝的整理候选、原话、候选、人工修改入口和“都不符合”会同时保留；AI不能发送反馈或冒充人工复核。、方法内容由独立审核控制、已登记 项；这里只显示适用范围和治理状态，不公开专业模板正文。、八步协作流程、一屏只做一个主要决定，草稿会先保存在本机，登录后可跨设备继续。、继续最近一次协作、开始一次协作、开始新的议题、1. 写下想共同理解的问题、本次愿意共享

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 23 | 确认符合上述范围 | `bindtap` | `confirmAdultLaunchScope` | — |
| 57 | 继续最近一次协作 | `bindtap` | `continueParticipantFlow` | — |
| 58 | 开始一次协作 | `bindtap` | `startParticipantFlow` | — |
| 59 | 开始新的议题 | `bindtap` | `startParticipantFlow` | — |
| 64 | — | `bindinput` | `onQuestionInput` | — |
| 66 | 上面的问题 | `bindchange` | `onScopeChange` | — |
| 70 | 提交协作问题 | `bindtap` | `createCase` | — |
| 83 | 查看两个问题候选 | `bindtap` | `updateQuestionAction` | {'action': 'generate_candidates'} |
| 84 | 都不符合 | `bindtap` | `updateQuestionAction` | {'action': 'none_fit'} |
| 85 | 暂时停一下 | `bindtap` | `updateQuestionAction` | {'action': 'pause'} |
| 103 | 这和我的体验不一致 | `bindtap` | `disagree` | — |
| 104 | 撤回本次协作 | `bindtap` | `withdraw` | — |
| 106 | 查看或提交更正与投诉 | `bindtap` | `openQualityRecord` | — |
| 111 | — | `bindinput` | `onActionInput` | — |
| 112 | 记录下一小步 | `bindtap` | `chooseAction` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 83 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 84 | `getTherapeuticAssessmentServiceLevels` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 85 | `getTherapeuticAssessmentProductionContract` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 86 | `getTherapeuticAssessmentAdultLaunchScope` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 87 | `getTherapeuticAssessmentChildPolicy` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 88 | `getTherapeuticAssessmentMultiPartyPolicy` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 89 | `getTherapeuticAssessmentAiAssistPolicy` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 90 | `getTherapeuticAssessmentMethodLibrary` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 110 | `listTherapeuticAssessmentEvidence` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 111 | `getTherapeuticAssessmentLaunchScreening` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 130 | `submitTherapeuticAssessmentLaunchScreening` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 183 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 205 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 225 | `updateTherapeuticAssessmentQuestion` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 249 | `transitionTherapeuticAssessment` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 268 | `transitionTherapeuticAssessment` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/therapeutic-assessment-boundary/index`（js:58）、`navigateTo` → `/pages/therapeutic-assessment-boundary/index?caseId=:dynamic`（js:67）、`navigateTo` → `/pages/therapeutic-assessment-quality/index:dynamic`（js:74）
- 本地存储：`getStorageSync` `auth_user`（JS:469）、`removeStorageSync` `auth_token`（JS:493）、`removeStorageSync` `auth_user`（JS:494）、`getStorageSync` `auth_token`（JS:516）、`setStorageSync` `auth_token`（JS:736）、`setStorageSync` `auth_user`（JS:737）、`removeStorageSync` `safehome_anonymous_user_id`（JS:738）、`setStorageSync` `auth_token`（JS:784）、`setStorageSync` `auth_user`（JS:785）、`setStorageSync` `auth_token`（JS:800）、`setStorageSync` `auth_user`（JS:801）、`removeStorageSync` `safehome_anonymous_user_id`（JS:802）、`setStorageSync` `auth_token`（JS:817）、`setStorageSync` `auth_user`（JS:818）、`removeStorageSync` `safehome_anonymous_user_id`（JS:819）、`setStorageSync` `auth_token`（JS:842）、`setStorageSync` `auth_user`（JS:843）、`removeStorageSync` `safehome_anonymous_user_id`（JS:844）、`removeStorageSync` `auth_token`（JS:851）、`removeStorageSync` `auth_user`（JS:852）、`getStorageSync` `STORAGE_KEY`（JS:2195）、`setStorageSync` `STORAGE_KEY`（JS:2201）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2237）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2264）
- WXML 数据绑定：`activeCase`、`notice`、`errorMessage`、`productionContract`、`adultLaunchScope`、`saving`、`launchScreening`、`childPolicy`、`multiPartyPolicy`、`aiAssistPolicy`、`methodCatalog`、`question`、`shareQuestion`、`shareRecentRecord`、`loading`、`item`、`evidenceItems`、`actionText`
- 条件状态：`notice`、`errorMessage`、`productionContract`、`adultLaunchScope`、`activeCase`、`launchScreening`、`childPolicy`、`multiPartyPolicy`、`aiAssistPolicy`、`methodCatalog`、`loading`、`evidenceItems`
- `setData` 状态：`loading`、`errorMessage`、`activeCase`、`defaultServiceLevel`、`cases`、`productionContract`、`adultLaunchScope`、`childPolicy`、`multiPartyPolicy`、`aiAssistPolicy`、`methodCatalog`、`evidenceItems`、`launchScreening`、`saving`、`notice`、`question`、`actionText`、`shareQuestion`、`shareRecentRecord`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 21：开始前了解 `pages/therapeutic-assessment-boundary/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`0c3a23929509baa253143004581492e2e350e65f389a743a750143a4465b1cf1`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-boundary/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-boundary/index.js`、`apps/miniprogram/pages/therapeutic-assessment-boundary/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/therapeutic-assessment/index`
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 22：我的议题 `pages/therapeutic-assessment-issue/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`581ca59aef54afe673be6b32cffd9a7ada80fff4e0c0dafb8c9a41fdda875583`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-issue/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-issue/index.js`、`apps/miniprogram/pages/therapeutic-assessment-issue/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：—
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 23：最近一次事件 `pages/therapeutic-assessment-recent-event/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`53de130f7854b178af6647584ea28b059041278298fb37d1042ba00334945b93`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-recent-event/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-recent-event/index.js`、`apps/miniprogram/pages/therapeutic-assessment-recent-event/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：—
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 24：例外与资源 `pages/therapeutic-assessment-resources/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`cd40b49e9421ee92df3a65e454594708de9a06992439dc182688cf9b638cde38`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-resources/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-resources/index.js`、`apps/miniprogram/pages/therapeutic-assessment-resources/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：—
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 25：资料与共享 `pages/therapeutic-assessment-sharing/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`a67ea60cc4af1422fa90d031ea0daa7521cace07d9b08bf04a41b6cc5227d8e8`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-sharing/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-sharing/index.js`、`apps/miniprogram/pages/therapeutic-assessment-sharing/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：—
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 26：提交前摘要 `pages/therapeutic-assessment-summary/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`6edf3c0aac21680174facea3426c92068508355877265176a7f4cb0513bfa856`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-summary/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-summary/index.js`、`apps/miniprogram/pages/therapeutic-assessment-summary/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：—
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 27：反馈核对 `pages/therapeutic-assessment-feedback-check/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`2d0a0a41ef85d211d1552d6453dbd58137558da75e271c8fc257d313c4676971`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-feedback-check/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-feedback-check/index.js`、`apps/miniprogram/pages/therapeutic-assessment-feedback-check/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：—
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 28：一个小行动 `pages/therapeutic-assessment-action-review/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`36adda01f7ad3db58cf98ca20c0d9bd91a9f7adf6f9e02657860682936ca7a6c`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-action-review/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-action-review/index.js`、`apps/miniprogram/pages/therapeutic-assessment-action-review/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：—
- 页面组件：`therapeutic-flow-step` → `/components/therapeutic-flow-step/index`
- 主要可见内容：—

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 1 | — | `bindvaluechange` | `onValueChange` | — |
| 1 | — | `bindoptionchange` | `onOptionChange` | — |
| 1 | — | `bindactionchange` | `onActionChange` | — |
| 1 | — | `bindcontinue` | `onContinue` | — |
| 1 | — | `bindretry` | `onRetry` | — |
| 1 | — | `bindback` | `onBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 188 | `getTherapeuticAssessmentStopRecoveryStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 203 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 255 | `getTherapeuticAssessmentParticipantDraft` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 327 | `saveTherapeuticAssessmentParticipantDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 369 | `createTherapeuticAssessmentCase` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 397 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 409 | `createTherapeuticAssessmentEvidence` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 422 | `updateTherapeuticAssessmentScope` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 432 | `respondToTherapeuticAssessmentFeedback` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 445 | `createTherapeuticAssessmentAction` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `:dynamic`（js:473）、`navigateTo` → `/pages/login/index:dynamic`（js:2503）
- 本地存储：`getStorageSync` `auth_user`（JS:671）、`removeStorageSync` `auth_token`（JS:695）、`removeStorageSync` `auth_user`（JS:696）、`getStorageSync` `auth_token`（JS:718）、`setStorageSync` `auth_token`（JS:938）、`setStorageSync` `auth_user`（JS:939）、`removeStorageSync` `safehome_anonymous_user_id`（JS:940）、`setStorageSync` `auth_token`（JS:986）、`setStorageSync` `auth_user`（JS:987）、`setStorageSync` `auth_token`（JS:1002）、`setStorageSync` `auth_user`（JS:1003）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1004）、`setStorageSync` `auth_token`（JS:1019）、`setStorageSync` `auth_user`（JS:1020）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1021）、`setStorageSync` `auth_token`（JS:1044）、`setStorageSync` `auth_user`（JS:1045）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1046）、`removeStorageSync` `auth_token`（JS:1053）、`removeStorageSync` `auth_user`（JS:1054）、`getStorageSync` `STORAGE_KEY`（JS:2397）、`setStorageSync` `STORAGE_KEY`（JS:2403）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2439）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2466）、`getStorageSync` `auth_token`（JS:2479）、`getStorageSync` `auth_user`（JS:2483）、`removeStorageSync` `auth_token`（JS:2509）、`removeStorageSync` `auth_user`（JS:2510）、`getStorageSync` `storageKey`（JS:2552）、`setStorageSync` `storageKey`（JS:2574）、`removeStorageSync` `storageKey`（JS:2604）
- WXML 数据绑定：`stepNumber`、`stepTotal`、`title`、`description`、`prompt`、`mode`、`value`、`selected`、`options`、`originalText`、`systemText`、`actionPlan`、`nextLabel`、`saveStatus`、`loading`、`saving`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`
- 条件状态：—
- `setData` 状态：`loading`、`caseId`、`saveStatus`、`offline`、`stateKind`、`stateTitle`、`stateDescription`、`canContinue`、`activeCase`、`originalText`、`systemText`、`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel`、`value`、`selected`、`actionPlan`、`remoteVersion`、`saving`、`createdActionId`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 29：行动回看 `pages/therapeutic-assessment-action-followup/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`b87646ac64e9240ebf37c16b3a90d3bc7d83b108a431dd6b31e552803257000f`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.wxss`、`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.js`、`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：—
- 页面组件：`page-state` → `/components/page-state/index`
- 主要可见内容：一次记录，不是疗效证明、回看这次小行动、无论是否做到，都可以记录真实发生的情况。这里不会按完成次数评价你。、我选择的一小步、停止条件、这次的状态、尝试过、中途停止、决定不做、把这次内容记成、新的观察、仍待了解、打开关联训练卡、保存这次回看、完成、停止或不做都可以被如实记录；这些记录只作为后续共同理解的线索。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | 我选择的一小步 | `bindaction` | `load` | — |
| 22 | 尝试过 | `bindtap` | `selectStatus` | {'value': 'completed'} |
| 23 | 中途停止 | `bindtap` | `selectStatus` | {'value': 'stopped'} |
| 24 | 决定不做 | `bindtap` | `selectStatus` | {'value': 'declined'} |
| 29 | 新的观察 | `bindtap` | `selectKind` | {'value': 'O'} |
| 30 | 仍待了解 | `bindtap` | `selectKind` | {'value': 'U'} |
| 33 | 行动回看内容 | `bindinput` | `onNoteInput` | — |
| 34 | 打开关联训练卡 | `bindtap` | `openTrainingCard` | — |
| 35 | 保存这次回看 | `bindtap` | `submit` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 40 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 73 | `updateTherapeuticAssessmentAction` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 82 | `createTherapeuticAssessmentActionFollowup` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment/index`（js:94）、`navigateTo` → `/pages/training-card/index?id=:dynamic`（js:104）、`navigateTo` → `/pages/login/index:dynamic`（js:2132）
- 本地存储：`getStorageSync` `auth_user`（JS:300）、`removeStorageSync` `auth_token`（JS:324）、`removeStorageSync` `auth_user`（JS:325）、`getStorageSync` `auth_token`（JS:347）、`setStorageSync` `auth_token`（JS:567）、`setStorageSync` `auth_user`（JS:568）、`removeStorageSync` `safehome_anonymous_user_id`（JS:569）、`setStorageSync` `auth_token`（JS:615）、`setStorageSync` `auth_user`（JS:616）、`setStorageSync` `auth_token`（JS:631）、`setStorageSync` `auth_user`（JS:632）、`removeStorageSync` `safehome_anonymous_user_id`（JS:633）、`setStorageSync` `auth_token`（JS:648）、`setStorageSync` `auth_user`（JS:649）、`removeStorageSync` `safehome_anonymous_user_id`（JS:650）、`setStorageSync` `auth_token`（JS:673）、`setStorageSync` `auth_user`（JS:674）、`removeStorageSync` `safehome_anonymous_user_id`（JS:675）、`removeStorageSync` `auth_token`（JS:682）、`removeStorageSync` `auth_user`（JS:683）、`getStorageSync` `STORAGE_KEY`（JS:2026）、`setStorageSync` `STORAGE_KEY`（JS:2032）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2068）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2095）、`getStorageSync` `auth_token`（JS:2108）、`getStorageSync` `auth_user`（JS:2112）、`removeStorageSync` `auth_token`（JS:2138）、`removeStorageSync` `auth_user`（JS:2139）
- WXML 数据绑定：`loading`、`error`、`action`、`item`、`status`、`followupKind`、`note`、`saving`
- 条件状态：`loading`、`error`、`action`
- `setData` 状态：`loading`、`caseId`、`actionId`、`error`、`action`、`status`、`followupKind`、`note`、`saving`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 30：评估质量与更正 `pages/therapeutic-assessment-quality/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`89db4df8b0e78c20c0cf5baadead705598e4441d66fbd8465f3bfabd79217be4`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-quality/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-quality/index.wxss`、`apps/miniprogram/pages/therapeutic-assessment-quality/index.js`、`apps/miniprogram/pages/therapeutic-assessment-quality/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/therapeutic-assessment/index`、`pages/researcher-dashboard/index`
- 页面组件：—
- 主要可见内容：治疗性评估 · 质量监督、把不同理解、修复和通知留在同一条记录里、这里只核对问题、依据、授权、语言、参与者识别与行动适配，不生成诊断或疗效结论。、待处理 · 已超时 · 规则、暂时没有处理成功、重新读取、正在读取质量记录、只加载当前账号可查看的对象范围。、生产门禁、更正与投诉、记录哪里不像，或希望如何处理、协作记录：、问题类型：、具体哪里不像或发生了什么、希望怎样处理、提交更正或投诉、提交不会覆盖原记录；原反馈、异议和处理版本都会保留。、抽检队列、逐项质量复核、项、当前授权范围内没有复核任务、抽检原因： · 截止：、认领这项复核、结论：

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 16 | 重新读取 | `bindtap` | `loadData` | — |
| 46 | 协作记录： | `bindchange` | `onCaseChange` | — |
| 49 | 问题类型： | `bindchange` | `onIncidentCategory` | — |
| 54 | — | `bindinput` | `onFieldInput` | {'key': 'incidentDescription'} |
| 58 | — | `bindinput` | `onFieldInput` | {'key': 'requestedResolution'} |
| 60 | 提交更正或投诉 | `bindtap` | `submitIncident` | — |
| 76 | — | `bindtap` | `selectReview` | {'id': '{{item.id}}'} |
| 85 | 认领这项复核 | `bindtap` | `claimReview` | — |
| 89 | 结论： | `bindchange` | `onDimensionStatus` | {'index': '{{index}}'} |
| 93 | — | `bindinput` | `onDimensionInput` | {'index': '{{index}}', 'key': 'note'} |
| 94 | — | `bindinput` | `onDimensionInput` | {'index': '{{index}}', 'key': 'evidenceRef'} |
| 99 | — | `bindinput` | `onFieldInput` | {'key': 'remediationSummary'} |
| 101 | 提交质量结论 | `bindtap` | `completeReview` | — |
| 118 | — | `bindtap` | `selectIncident` | {'id': '{{item.id}}'} |
| 129 | — | `bindinput` | `onFieldInput` | {'key': 'impactSummary'} |
| 131 | 保存影响分析 | `bindtap` | `analyzeIncident` | — |
| 134 | 处理动作： | `bindchange` | `onResolutionAction` | — |
| 139 | — | `bindinput` | `onFieldInput` | {'key': 'resolutionSummary'} |
| 141 | 独立结案并通知参与者 | `bindtap` | `resolveIncident` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 85 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 86 | `listTherapeuticAssessmentQualityIncidents` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 88 | `listTherapeuticAssessmentQualityReviews` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 91 | `getTherapeuticAssessmentProductionGate` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 171 | `claimTherapeuticAssessmentQualityReview` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 232 | `completeTherapeuticAssessmentQualityReview` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 266 | `createTherapeuticAssessmentQualityIncident` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 298 | `analyzeTherapeuticAssessmentQualityIncident` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 330 | `resolveTherapeuticAssessmentQualityIncident` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/login/index:dynamic`（js:2371）
- 本地存储：`getStorageSync` `auth_user`（JS:539）、`removeStorageSync` `auth_token`（JS:563）、`removeStorageSync` `auth_user`（JS:564）、`getStorageSync` `auth_token`（JS:586）、`setStorageSync` `auth_token`（JS:806）、`setStorageSync` `auth_user`（JS:807）、`removeStorageSync` `safehome_anonymous_user_id`（JS:808）、`setStorageSync` `auth_token`（JS:854）、`setStorageSync` `auth_user`（JS:855）、`setStorageSync` `auth_token`（JS:870）、`setStorageSync` `auth_user`（JS:871）、`removeStorageSync` `safehome_anonymous_user_id`（JS:872）、`setStorageSync` `auth_token`（JS:887）、`setStorageSync` `auth_user`（JS:888）、`removeStorageSync` `safehome_anonymous_user_id`（JS:889）、`setStorageSync` `auth_token`（JS:912）、`setStorageSync` `auth_user`（JS:913）、`removeStorageSync` `safehome_anonymous_user_id`（JS:914）、`removeStorageSync` `auth_token`（JS:921）、`removeStorageSync` `auth_user`（JS:922）、`getStorageSync` `STORAGE_KEY`（JS:2265）、`setStorageSync` `STORAGE_KEY`（JS:2271）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2307）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2334）、`getStorageSync` `auth_token`（JS:2347）、`getStorageSync` `auth_user`（JS:2351）、`removeStorageSync` `auth_token`（JS:2377）、`removeStorageSync` `auth_user`（JS:2378）
- WXML 数据绑定：`runtime`、`errorMessage`、`notice`、`loading`、`productionGate`、`productionGateChecks`、`item`、`cases`、`selectedCaseIndex`、`incidentCategoryOptions`、`incidentCategoryIndex`、`incidentDescription`、`requestedResolution`、`saving`、`isReviewRole`、`reviews`、`selectedReview`、`reviewDimensions`、`statusOptions`、`index`、`remediationSummary`、`incidents`、`selectedIncident`、`impactSummary`、`resolutionActionOptions`、`resolutionActionIndex`、`resolutionSummary`
- 条件状态：`runtime`、`errorMessage`、`notice`、`loading`、`productionGate`、`isReviewRole`、`reviews`、`selectedReview`、`item`、`incidents`、`selectedIncident`
- `setData` 状态：`userRole`、`isReviewRole`、`isFormalRole`、`selectedCaseId`、`loading`、`errorMessage`、`runtime`、`productionGate`、`selectedReview`、`selectedIncident`、`cases`、`selectedCaseIndex`、`reviews`、`incidents`、`productionGateChecks`、`reviewDimensions`、`remediationSummary`、`saving`、`notice`、`incidentCategoryIndex`、`incidentDescription`、`requestedResolution`、`impactSummary`、`resolutionSummary`、`resolutionActionIndex`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 31：我的成长仪表盘 `pages/growth-dashboard/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`ac2994e27bbea2f3bb1fe82256ca21fa0d08b30235dfe730a48afdcb3ca5354c`
- 核对文件：`apps/miniprogram/pages/growth-dashboard/index.wxml`、`apps/miniprogram/pages/growth-dashboard/index.wxss`、`apps/miniprogram/pages/growth-dashboard/index.js`、`apps/miniprogram/pages/growth-dashboard/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/relationship-growth/index`、`pages/profile/index`
- 页面组件：`page-state` → `/components/page-state/index`、`status-pill` → `/components/status-pill/index`
- 主要可见内容：四条线索，各自保留含义、我的成长仪表盘、记录与练习、测评、关系探索和研究者反馈分开查看。这里不生成单一成长分数。、现在可以做什么、记录一件小事、查看练习、情绪温度、1—10分，只与同一量尺的记录比较、记录与练习时间线、只呈现做过的事情，不把次数写成改善、支持性测评、每份量表独立成组，不把不同分值放在同一条曲线上、· 记录值、只在同一量尺再次填写后观察变化，不自动解释好坏。、关系探索单独呈现、不与日记次数或测评分值合并、探索任务、连续记录、阶段报告、关系探索时间线、这里只显示任务、连续记录和阶段报告的事实、共同核对、研究者反馈 条、打开消息列表

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | 重新读取成长线索 | `bindaction` | `loadGrowth` | — |
| 13 | 查看{{item.label}}，当前{{item.count}}条线索 | `bindtap` | `selectSection` | {'key': '{{item.key}}'} |
| 32 | 记录一件小事 | `bindtap` | `startDiary` | — |
| 33 | 查看练习 | `bindtap` | `openTraining` | — |
| 59 | — | `bindaction` | `startDiary` | — |
| 75 | — | `bindaction` | `openAssessment` | — |
| 88 | — | `bindtap` | `openRelationship` | — |
| 115 | 打开消息列表 | `bindtap` | `openMessages` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 64 | `getGrowthOverview` | `GET` | `/api/growth/overview` | `backend/app.py`、`backend/routes/feedback.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot_routes.py`、`backend/scripts/enrich_task17_programs.py`、`backend/scripts/generate_task33_ux_registry.py`、`backend/scripts/generate_task34_operations_registry.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index`（js:104）、`switchTab` → `/pages/training/index`（js:108）、`navigateTo` → `/pages/assessment/index`（js:112）、`navigateTo` → `/pages/relationship-pilot/index`（js:117）、`navigateTo` → `/pages/relationship-growth/index?detail=1&enrollment_id=:dynamic`（js:120）、`navigateTo` → `/pages/messages/index`（js:126）、`navigateTo` → `/pages/login/index:dynamic`（js:2152）
- 本地存储：`getStorageSync` `auth_user`（JS:320）、`removeStorageSync` `auth_token`（JS:344）、`removeStorageSync` `auth_user`（JS:345）、`getStorageSync` `auth_token`（JS:367）、`setStorageSync` `auth_token`（JS:587）、`setStorageSync` `auth_user`（JS:588）、`removeStorageSync` `safehome_anonymous_user_id`（JS:589）、`setStorageSync` `auth_token`（JS:635）、`setStorageSync` `auth_user`（JS:636）、`setStorageSync` `auth_token`（JS:651）、`setStorageSync` `auth_user`（JS:652）、`removeStorageSync` `safehome_anonymous_user_id`（JS:653）、`setStorageSync` `auth_token`（JS:668）、`setStorageSync` `auth_user`（JS:669）、`removeStorageSync` `safehome_anonymous_user_id`（JS:670）、`setStorageSync` `auth_token`（JS:693）、`setStorageSync` `auth_user`（JS:694）、`removeStorageSync` `safehome_anonymous_user_id`（JS:695）、`removeStorageSync` `auth_token`（JS:702）、`removeStorageSync` `auth_user`（JS:703）、`getStorageSync` `STORAGE_KEY`（JS:2046）、`setStorageSync` `STORAGE_KEY`（JS:2052）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2088）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2115）、`getStorageSync` `auth_token`（JS:2128）、`getStorageSync` `auth_user`（JS:2132）、`removeStorageSync` `auth_token`（JS:2158）、`removeStorageSync` `auth_user`（JS:2159）
- WXML 数据绑定：`loading`、`errorMessage`、`growth`、`sectionTabs`、`item`、`activeSection`、`thermometer`、`activityTimeline`、`assessmentGroups`、`score`、`relationshipSummary`、`relationshipTimeline`、`feedbackSummary`、`feedbackTimeline`
- 条件状态：`loading`、`errorMessage`、`growth`、`activeSection`、`thermometer`、`activityTimeline`、`assessmentGroups`、`relationshipTimeline`、`feedbackTimeline`
- `setData` 状态：`activeSection`、`requestedEnrollmentId`、`loading`、`errorMessage`、`sectionTabs`、`thermometer`、`dateText`、`width`、`growth`、`active`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 32：关系探索手记 `pages/relationship-narrative/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`c110dfa6f77082d73c1b8bc2f8983eb608dd3320e95a0c0119bb249a7751be35`
- 核对文件：`apps/miniprogram/pages/relationship-narrative/index.wxml`、`apps/miniprogram/pages/relationship-narrative/index.wxss`、`apps/miniprogram/pages/relationship-narrative/index.js`、`apps/miniprogram/pages/relationship-narrative/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/message-detail/index`
- 页面组件：—
- 主要可见内容：我的关系探索手记、起点画像：、一起讨论的问题、线上任务材料、研究者备注、下一步项目任务

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 3 | — | `bindaction` | `retryLoad` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 15 | `getRelationshipNarrative` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py`、`backend/routes/research_workspace.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `auth_user`（JS:223）、`removeStorageSync` `auth_token`（JS:247）、`removeStorageSync` `auth_user`（JS:248）、`getStorageSync` `auth_token`（JS:270）、`setStorageSync` `auth_token`（JS:490）、`setStorageSync` `auth_user`（JS:491）、`removeStorageSync` `safehome_anonymous_user_id`（JS:492）、`setStorageSync` `auth_token`（JS:538）、`setStorageSync` `auth_user`（JS:539）、`setStorageSync` `auth_token`（JS:554）、`setStorageSync` `auth_user`（JS:555）、`removeStorageSync` `safehome_anonymous_user_id`（JS:556）、`setStorageSync` `auth_token`（JS:571）、`setStorageSync` `auth_user`（JS:572）、`removeStorageSync` `safehome_anonymous_user_id`（JS:573）、`setStorageSync` `auth_token`（JS:596）、`setStorageSync` `auth_user`（JS:597）、`removeStorageSync` `safehome_anonymous_user_id`（JS:598）、`removeStorageSync` `auth_token`（JS:605）、`removeStorageSync` `auth_user`（JS:606）、`getStorageSync` `STORAGE_KEY`（JS:1949）、`setStorageSync` `STORAGE_KEY`（JS:1955）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:1991）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2018）
- WXML 数据绑定：`loading`、`errorMessage`、`isConfirmed`、`narrative`、`index`、`item`、`taskRows`、`isResearcherView`、`noteRows`
- 条件状态：`loading`、`errorMessage`、`isResearcherView`
- `setData` 状态：`narrativeId`、`loading`、`errorMessage`、`isConfirmed`、`isResearcherView`、`noteRows`、`taskRows`、`narrative`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 33：研究者移动工作台 `pages/researcher-dashboard/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`d4420b223a6e4e11dbe20d4e9be36c67dd5e251dee5d87f8ad618ace729d6909`
- 核对文件：`apps/miniprogram/pages/researcher-dashboard/index.wxml`、`apps/miniprogram/pages/researcher-dashboard/index.wxss`、`apps/miniprogram/pages/researcher-dashboard/index.js`、`apps/miniprogram/pages/researcher-dashboard/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/errorDiagnostics.js`
- 上游页面：`pages/profile/index`
- 页面组件：—
- 主要可见内容：研究者移动工作台、先处理重要的一小步、移动端用于查看摘要、处理提醒和进入试点；完整研究配置与批量工作仍在 Web 完成。、最近同步、当前离线、已读取内容会保留；联网后下拉刷新或点“重新同步”。、开发全权限模式、普通测试账号临时可读写研究平台，包括权限配置、治疗性评估、AI、情感计算、网络分析、发布与生产门禁。业务状态机和证据约束仍然生效；正式发布前必须关闭此模式。、当前身份： · 能力矩阵、页面导航按能力显示；每次深链访问仍由服务端重新授权并记录审计。、正在同步工作台、只读取必要摘要，不加载参与者长文本。、工作台暂时没有读取成功、请求编号：、重新同步、复制诊断信息、部分摘要暂未同步、其余工作区仍可使用。失败模块：、重试未完成同步、协作式评估人工队列、个可见班次、待处理 · 超时 · 无人值守紧急项、没有匹配对象范围、胜任力、有效期和值守班次的接手人时，任务不会自动降级给普通角色。、服务端统一核对

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 8 | 刷新当前工作区 | `bindtap` | `refreshActiveWorkspace` | — |
| 28 | — | `bindtap` | `switchWorkspace` | {'id': '{{item.id}}'} |
| 41 | 重新同步 | `bindtap` | `loadWorkbench` | — |
| 42 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | {'scope': 'workbench'} |
| 49 | 重试未完成同步 | `bindtap` | `loadWorkbench` | — |
| 106 | 刷新待处理列表 | `bindtap` | `loadWorkbench` | — |
| 122 | 继续查看 | `bindtap` | `showMorePending` | — |
| 134 | 搜索参与者 | `bindinput` | `onParticipantQueryInput` | — |
| 143 | 重新加载 | `bindtap` | `retryParticipants` | — |
| 144 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | {'scope': 'participants'} |
| 156 | 查看{{item.displayName}}的参与者档案 | `bindtap` | `selectParticipantDossier` | {'id': '{{item.user_id}}'} |
| 165 | 加载下一页 | `bindtap` | `loadMoreParticipants` | — |
| 174 | 关闭参与者档案 | `bindtap` | `closeParticipantDossier` | — |
| 177 | — | `bindtap` | `loadParticipantModule` | {'key': '{{item.key}}'} |
| 186 | 加载下一页 | `bindtap` | `loadParticipantModule` | {'key': '{{participantModule.module}}', 'page': '{{participantModule.page + 1}}'} |
| 209 | 进入试点项目 | `bindtap` | `switchWorkspace` | {'id': 'pilots'} |
| 221 | 刷新 | `bindtap` | `loadAssessmentCases` | — |
| 225 | — | `bindtap` | `selectAssessmentCase` | {'id': '{{item.id}}'} |
| 230 | 重新加载 | `bindtap` | `loadAssessmentCases` | — |
| 248 | 类型： | `bindchange` | `onAssessmentFilter` | {'key': 'kind'} |
| 251 | 权限： | `bindchange` | `onAssessmentFilter` | {'key': 'visibility'} |
| 281 | — | `bindinput` | `onAssessmentDraftInput` | {'key': 'assessmentInternalNotes'} |
| 286 | — | `bindinput` | `onAssessmentDraftInput` | {'key': 'assessmentParticipantDraft'} |
| 288 | 保存工作台草稿 | `bindtap` | `saveAssessmentDraft` | — |
| 290 | 进入质量抽检与修复 | `bindtap` | `openAssessmentQuality` | — |
| 302 | 刷新 | `bindtap` | `loadAnalysisJobs` | — |
| 346 | 重新加载 | `bindtap` | `loadAnalysisJobs` | — |
| 376 | 重新同步 | `bindtap` | `loadWorkbench` | — |
| 391 | 重新加载 | `bindtap` | `loadDashboard` | — |
| 392 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | {'scope': 'pilot'} |
| 402 | · | `bindtap` | `selectEnrollment` | {'id': '{{item.id}}'} |
| 424 | 查看 | `bindtap` | `openReport` | — |
| 425 | 人工确认 | `bindtap` | `confirmReport` | — |
| 426 | 发送用户 | `bindtap` | `sendReport` | — |
| 429 | 生成报告 | `bindtap` | `createReport` | — |
| 437 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'observation'} |
| 441 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'evidence'} |
| 445 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'nextStep'} |
| 449 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'openQuestion'} |
| 465 | 生成并核对预览 | `bindtap` | `previewStageFeedback` | — |
| 466 | 确认这个版本 | `bindtap` | `runDeliveryStep` | {'kind': 'stage', 'action': 'confirm'} |
| 467 | 发送到参与者消息 | `bindtap` | `runDeliveryStep` | {'kind': 'stage', 'action': 'send'} |
| 474 | — | `bindinput` | `onMessageTitleInput` | — |
| 475 | — | `bindinput` | `onMessageBodyInput` | — |
| 489 | 生成并核对预览 | `bindtap` | `previewParticipantMessage` | — |
| 490 | 确认这个版本 | `bindtap` | `runDeliveryStep` | {'kind': 'message', 'action': 'confirm'} |
| 491 | 发送到参与者消息 | `bindtap` | `runDeliveryStep` | {'kind': 'message', 'action': 'send'} |
| 509 | — | `bindinput` | `onNoteInput` | — |
| 510 | 保存备注 | `bindtap` | `saveNote` | — |
| 515 | 生成探索手记草稿 | `bindtap` | `draftNarrative` | — |
| 519 | 确认后交付用户 | `bindtap` | `confirmNarrative` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 209 | `getShowcaseAccess` | `GET` | `/api/showcase-access` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 210 | `getResearchCapabilities` | `GET` | `/api/research/access` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 274 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 293 | `getTherapeuticAssessmentResearcherWorkbench` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 304 | `getTherapeuticAssessmentAuthorizationStatus` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 372 | `saveTherapeuticAssessmentResearcherDraft` | `PUT` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 399 | `getResearchAnalysisJobs` | `GET` | `/api/research/analysis` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 400 | `getResearchAnalysisCatalog` | `GET` | `/api/research/analysis` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 401 | `listOfflineModelVersions` | `GET` | `/api/research/benchmarks` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 402 | `listOfflineModelShadowRuns` | `GET` | `/api/research/benchmarks` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 403 | `listOfflineModelReviewQueue` | `GET` | `/api/research/benchmarks` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 404 | `getOfflineModelMonitoring` | `GET` | `/api/research/benchmarks` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 405 | `getOfflineModelReleaseGate` | `GET` | `/api/research/benchmarks` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 460 | `getResearchOperations` | `GET` | `/api/research/operations` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 461 | `getResearchQueue` | `GET` | `/api/research/queues` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 465 | `getTherapeuticAssessmentQueueRuntime` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 466 | `listTherapeuticAssessmentDutyShifts` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 467 | `listPublicationCandidates` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 468 | `getTherapeuticAssessmentLifecycleMetrics` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 542 | `getResearchParticipants` | `GET` | `/api/research/participants` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 568 | `getResearchParticipant` | `GET` | `/api/research/participants` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 585 | `getResearchParticipantModule` | `GET` | `/api/research/participants` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 601 | `getRelationshipResearchDashboard` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 646 | `claimResearchEnrollment` | `POST` | `/api/research/access` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 659 | `getRelationshipEnrollment` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 738 | `createRelationshipResearchNote` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 746 | `createRelationshipReport` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 756 | `confirmRelationshipReport` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 763 | `sendRelationshipReport` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 790 | `createResearchDelivery` | `POST` | `/api/research/deliveries` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 797 | `saveResearchDelivery` | `PATCH` | `/api/research/deliveries` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 803 | `runResearchDeliveryAction` | `POST` | `/api/research/deliveries` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 845 | `runResearchDeliveryAction` | `POST` | `/api/research/deliveries` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 866 | `createRelationshipNarrative` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 871 | `confirmRelationshipNarrative` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/therapeutic-assessment-quality/index`（js:392）、`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:748）、`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:752）、`navigateTo` → `/pages/login/index:dynamic`（js:2899）
- 本地存储：`getStorageSync` `this`（JS:701）、`setStorageSync` `this`（JS:707）、`removeStorageSync` `this`（JS:710）、`getStorageSync` `auth_user`（JS:1067）、`removeStorageSync` `auth_token`（JS:1091）、`removeStorageSync` `auth_user`（JS:1092）、`getStorageSync` `auth_token`（JS:1114）、`setStorageSync` `auth_token`（JS:1334）、`setStorageSync` `auth_user`（JS:1335）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1336）、`setStorageSync` `auth_token`（JS:1382）、`setStorageSync` `auth_user`（JS:1383）、`setStorageSync` `auth_token`（JS:1398）、`setStorageSync` `auth_user`（JS:1399）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1400）、`setStorageSync` `auth_token`（JS:1415）、`setStorageSync` `auth_user`（JS:1416）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1417）、`setStorageSync` `auth_token`（JS:1440）、`setStorageSync` `auth_user`（JS:1441）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1442）、`removeStorageSync` `auth_token`（JS:1449）、`removeStorageSync` `auth_user`（JS:1450）、`getStorageSync` `STORAGE_KEY`（JS:2793）、`setStorageSync` `STORAGE_KEY`（JS:2799）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2835）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2862）、`getStorageSync` `auth_token`（JS:2875）、`getStorageSync` `auth_user`（JS:2879）、`removeStorageSync` `auth_token`（JS:2905）、`removeStorageSync` `auth_user`（JS:2906）
- WXML 数据绑定：`lastSyncText`、`offline`、`developmentFullAccess`、`capabilityScope`、`workspaces`、`activeWorkspace`、`item`、`loading`、`errorMessage`、`errorDiagnostic`、`partialFailures`、`index`、`assessmentQueueRuntime`、`assessmentDutyShifts`、`publicationCandidateSummary`、`assessmentLifecycleSummary`、`pendingTotal`、`urgentCount`、`operations`、`pendingVisibleItems`、`pendingHasMore`、`participantQuery`、`participantError`、`participantDiagnostic`、`participantLoading`、`participantItems`、`participantHasMore`、`participantDossier`、`participantModule`、`participantModuleLoading`、`record`、`line`、`assessmentCases`、`assessmentCaseId`、`assessmentError`、`assessmentLoading`、`assessmentWorkbench`、`assessmentAuthorization`、`assessmentFilters`、`assessmentInternalNotes`、`assessmentParticipantDraft`、`assessmentSaving`、`analysisCatalog`、`analysisResilience`、`affectModelVersions`、`affectShadowRuns`、`affectShadowReviewCount`、`affectMonitoring`、`affectReleaseGate`、`analysisLoading`、`analysisError`、`analysisJobs`、`pilotLoading`、`pilotError`、`pilotDiagnostic`、`items`、`selected`、`stageFeedbackForm`、`stageFeedbackDelivery`、`sendingFeedback`、`messageTitle`、`messageBody`、`participantMessageDelivery`、`sendingMessage`、`answer`、`note`、`narrative`
- 条件状态：`offline`、`developmentFullAccess`、`capabilityScope`、`loading`、`errorMessage`、`partialFailures`、`activeWorkspace`、`assessmentQueueRuntime`、`publicationCandidateSummary`、`assessmentLifecycleSummary`、`pendingVisibleItems`、`pendingHasMore`、`participantError`、`participantLoading`、`participantItems`、`participantHasMore`、`participantDossier`、`participantModuleLoading`、`participantModule`、`assessmentCases`、`assessmentError`、`assessmentLoading`、`assessmentWorkbench`、`item`、`analysisCatalog`、`analysisResilience`、`affectShadowRuns`、`affectMonitoring`、`affectReleaseGate`、`analysisLoading`、`analysisError`、`analysisJobs`、`pilotLoading`、`pilotError`、`items`、`selected`、`stageFeedbackDelivery`、`participantMessageDelivery`、`narrative`
- `setData` 状态：`developmentFullAccess`、`activeWorkspace`、`capabilityScope`、`workspaces`、`loading`、`errorMessage`、`offline`、`assessmentLoading`、`assessmentError`、`assessmentCases`、`assessmentCaseId`、`assessmentWorkbench`、`case`、`sharedScopeText`、`evidence_items`、`assessmentInternalNotes`、`assessmentParticipantDraft`、`assessmentAuthorization`、`assessmentFilters`、`assessmentSaving`、`analysisLoading`、`analysisError`、`analysisJobs`、`analysisLabel`、`statusLabel`、`createdText`、`qualityText`、`suppressed`、`errorDiagnostic`、`partialFailures`、`pendingItems`、`pendingTotal`、`pendingVisibleItems`、`pendingPage`、`pendingHasMore`、`urgentCount`、`assessmentQueueRuntime`、`assessmentDutyShifts`、`publicationCandidateSummary`、`approved`、`published`、`assessmentLifecycleSummary`、`lastSyncText`、`operations`、`participantQuery`、`participantError`、`participantLoading`、`participantDiagnostic`、`participantItems`、`participantPage`、`participantHasMore`、`participantDossier`、`participantModule`、`participantModuleLoading`、`items`、`pilotLoading`、`pilotError`、`pilotDiagnostic`、`selected`、`narrative`、`note`、`messageTitle`、`messageBody`、`stageFeedbackForm`、`evidence`、`nextStep`、`openQuestion`、`stageFeedbackDelivery`、`participantMessageDelivery`、`icon`、`sendingFeedback`、`sendingMessage`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 34：课程 `pages/course/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`509585f2c49e2868d8d90ecf43eb3cdcfa507bb0a428bcc41d4ad2e10b19cd73`
- 核对文件：`apps/miniprogram/pages/course/index.wxml`、`apps/miniprogram/pages/course/index.wxss`、`apps/miniprogram/pages/course/index.js`、`apps/miniprogram/pages/course/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/login/index`
- 页面组件：`section-title` → `/components/section-title/index`、`course-card` → `/components/course-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：练习内容目录、按需要慢慢看、这里整理一些陪伴练习相关内容。可以先选一个主题看一小节，不需要一次学完。、本周已查看 小节、轻量、重新加载、正在读取课程内容...

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 24 | — | `bindtap` | `selectCategory` | {'category': '{{item}}'} |
| 40 | 重新加载 | `bindtap` | `retryLoadCourses` | — |
| 53 | — | `bindtapcard` | `openCourse` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 37 | `listCourses` | `GET` | `/api/courses` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_courses.py`、`backend/scripts/generate_task34_operations_registry.py`、`backend/services/content_governance_service.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/course-detail/index?id=:dynamic`（js:76）
- 本地存储：`getStorageSync` `auth_user`（JS:276）、`removeStorageSync` `auth_token`（JS:300）、`removeStorageSync` `auth_user`（JS:301）、`getStorageSync` `auth_token`（JS:323）、`setStorageSync` `auth_token`（JS:543）、`setStorageSync` `auth_user`（JS:544）、`removeStorageSync` `safehome_anonymous_user_id`（JS:545）、`setStorageSync` `auth_token`（JS:591）、`setStorageSync` `auth_user`（JS:592）、`setStorageSync` `auth_token`（JS:607）、`setStorageSync` `auth_user`（JS:608）、`removeStorageSync` `safehome_anonymous_user_id`（JS:609）、`setStorageSync` `auth_token`（JS:624）、`setStorageSync` `auth_user`（JS:625）、`removeStorageSync` `safehome_anonymous_user_id`（JS:626）、`setStorageSync` `auth_token`（JS:649）、`setStorageSync` `auth_user`（JS:650）、`removeStorageSync` `safehome_anonymous_user_id`（JS:651）、`removeStorageSync` `auth_token`（JS:658）、`removeStorageSync` `auth_user`（JS:659）、`getStorageSync` `STORAGE_KEY`（JS:2002）、`setStorageSync` `STORAGE_KEY`（JS:2008）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2044）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2071）
- WXML 数据绑定：`weeklyProgress`、`false`、`categories`、`activeCategory`、`item`、`errorMessage`、`loading`、`visibleCourses`、`boundaryNotice`
- 条件状态：`errorMessage`、`loading`、`boundaryNotice`
- `setData` 状态：`loading`、`errorMessage`、`categories`、`boundaryNotice`、`courses`、`activeCategory`、`visibleCourses`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 35：课程内容 `pages/course-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`85be52c1df9c96690e6812a507afafe73a75b0ac6266789bb340e7a16b61e330`
- 核对文件：`apps/miniprogram/pages/course-detail/index.wxml`、`apps/miniprogram/pages/course-detail/index.wxss`、`apps/miniprogram/pages/course-detail/index.js`、`apps/miniprogram/pages/course-detail/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/course/index`
- 页面组件：`section-title` → `../../components/section-title/index`
- 主要可见内容：正在读取课程内容...、重新加载、· 小节、容易误解、可以这样理解、完整示例、常见反例、真实场景迁移、练习后想一想、关联训练卡、去训练页、记录本次学习、完成表示已经阅读并尝试理解检查，不代表掌握程度或心理状态改善。、记录课程完成

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 8 | 重新加载 | `bindtap` | `retryLoadCourse` | — |
| 65 | — | `bindtap` | `chooseKnowledgeAnswer` | {'check-id': '{{check.id}}', 'value': '{{option.value}}'} |
| 84 | 去训练页 | `bindtap` | `goTraining` | — |
| 92 | 记录课程完成 | `bindtap` | `markCourseComplete` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 39 | `getCourse` | `GET` | `/api/courses/:id` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/progress_summary.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_content.py`、`backend/scripts/enrich_task17_courses.py` |
| 77 | `getCourseProgress` | `GET` | `/api/courses/:id/progress` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/progress_summary.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_content.py`、`backend/scripts/enrich_task17_courses.py` |
| 98 | `saveCourseProgress` | `POST` | `/api/courses/:id/progress` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/progress_summary.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_content.py`、`backend/scripts/enrich_task17_courses.py` |

#### 路由、本地状态与页面状态

- 下游路由：`switchTab` → `/pages/training/index`（js:114）、`navigateTo` → `/pages/login/index:dynamic`（js:2140）
- 本地存储：`getStorageSync` `auth_user`（JS:308）、`removeStorageSync` `auth_token`（JS:332）、`removeStorageSync` `auth_user`（JS:333）、`getStorageSync` `auth_token`（JS:355）、`setStorageSync` `auth_token`（JS:575）、`setStorageSync` `auth_user`（JS:576）、`removeStorageSync` `safehome_anonymous_user_id`（JS:577）、`setStorageSync` `auth_token`（JS:623）、`setStorageSync` `auth_user`（JS:624）、`setStorageSync` `auth_token`（JS:639）、`setStorageSync` `auth_user`（JS:640）、`removeStorageSync` `safehome_anonymous_user_id`（JS:641）、`setStorageSync` `auth_token`（JS:656）、`setStorageSync` `auth_user`（JS:657）、`removeStorageSync` `safehome_anonymous_user_id`（JS:658）、`setStorageSync` `auth_token`（JS:681）、`setStorageSync` `auth_user`（JS:682）、`removeStorageSync` `safehome_anonymous_user_id`（JS:683）、`removeStorageSync` `auth_token`（JS:690）、`removeStorageSync` `auth_user`（JS:691）、`getStorageSync` `STORAGE_KEY`（JS:2034）、`setStorageSync` `STORAGE_KEY`（JS:2040）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2076）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2103）、`getStorageSync` `auth_token`（JS:2116）、`getStorageSync` `auth_user`（JS:2120）、`removeStorageSync` `auth_token`（JS:2146）、`removeStorageSync` `auth_user`（JS:2147）
- WXML 数据绑定：`loading`、`errorMessage`、`course`、`index`、`item`、`check`、`option`、`progressMessage`、`savingProgress`
- 条件状态：`loading`、`errorMessage`、`course`、`check`、`progressMessage`
- `setData` 状态：`courseId`、`loading`、`errorMessage`、`course`、`progressMessage`、`savingProgress`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 36：我的 `pages/profile/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`4106c5642d0d7969ce6ca06528893b4c930808f66ab5339fc06be5a1148350de`
- 核对文件：`apps/miniprogram/pages/profile/index.wxml`、`apps/miniprogram/pages/profile/index.wxss`、`apps/miniprogram/pages/profile/index.js`、`apps/miniprogram/pages/profile/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/login/index`
- 页面组件：`section-title` → `/components/section-title/index`、`function-entry-card` → `/components/function-entry-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`alert-card` → `/components/alert-card/index`
- 主要可见内容：家、登录后，你的记录只会用于本工具内的复盘、训练建议和必要的人工补充反馈。、退出登录、去登录、注册账号、登录方式、只显示连接状态，不显示身份值、微信登录、撤销、手机号登录、撤销登录方式会退出所有设备，但不会删除你的记录。、可找回、把本机试用记录放进当前账号、找到 条本机试用记录。确认后，测评、日记和练习记录会归到当前账号；暂不处理也不会删除。、确认合并、暂不处理、这里用于查看记录、复盘和支持入口。当前不做诊断，也不替代专业咨询或紧急帮助。、如果出现紧急安全风险、请先联系身边可信赖的人、学校老师、当地紧急医疗或心理危机支持。本小程序不能提供实时危机干预。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 17 | 退出登录 | `bindtap` | `doLogout` | — |
| 20 | 去登录 | `bindtap` | `goLogin` | — |
| 21 | 注册账号 | `bindtap` | `goRegister` | — |
| 33 | 撤销 | `bindtap` | `requestIdentityUnbind` | {'identity': 'wechat'} |
| 40 | 撤销 | `bindtap` | `requestIdentityUnbind` | {'identity': 'phone'} |
| 55 | 确认合并 | `bindtap` | `confirmDataClaim` | — |
| 56 | 暂不处理 | `bindtap` | `dismissDataClaim` | — |
| 69 | — | `bindtap` | `goResearcher` | — |
| 75 | — | `bindtap` | `openEntry` | {'group': 'recordEntries', 'index': '{{index}}'} |
| 88 | — | `bindtap` | `openEntry` | {'group': 'supportEntries', 'index': '{{index}}'} |
| 105 | — | `bindtap` | `openEntry` | {'group': 'safetyEntries', 'index': '{{index}}'} |
| 118 | — | `bindtap` | `openEntry` | {'group': 'settingsEntries', 'index': '{{index}}'} |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 120 | `getShowcaseAccess` | `GET` | `/api/showcase-access` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 121 | `getDataClaimPreview` | `GET` | `/api/auth/data-claim-preview` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 122 | `getIdentityStatus` | `GET` | `/api/auth/identity-status` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 129 | `getProfileStats` | `GET` | `/api/profile/stats` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 226 | `claimAnonymousData` | `POST` | `/api/auth/data-claim` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 252 | `unbindIdentity` | `POST` | `/api/auth/identity-unbind` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |

#### 路由、本地状态与页面状态

- 下游路由：`switchTab` → `/pages/login/index?redirect=%2Fpages%2Fprofile%2Findex`（js:191）、`navigateTo` → `/pages/register/index?redirect=%2Fpages%2Fprofile%2Findex`（js:202）、`navigateTo` → `/pages/researcher-dashboard/index`（js:208）、`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fresearcher-dashboard%2Findex`（js:211）、`redirectTo` → `/pages/login/index?redirect=%2Fpages%2Fprofile%2Findex`（js:256）、`navigateTo` → `/pages/login/index:dynamic`（js:2295）
- 本地存储：`getStorageSync` `safehome_dismissed_data_claim_id`（JS:124）、`setStorageSync` `safehome_dismissed_data_claim_id`（JS:216）、`removeStorageSync` `safehome_dismissed_data_claim_id`（JS:227）、`getStorageSync` `auth_user`（JS:463）、`removeStorageSync` `auth_token`（JS:487）、`removeStorageSync` `auth_user`（JS:488）、`getStorageSync` `auth_token`（JS:510）、`setStorageSync` `auth_token`（JS:730）、`setStorageSync` `auth_user`（JS:731）、`removeStorageSync` `safehome_anonymous_user_id`（JS:732）、`setStorageSync` `auth_token`（JS:778）、`setStorageSync` `auth_user`（JS:779）、`setStorageSync` `auth_token`（JS:794）、`setStorageSync` `auth_user`（JS:795）、`removeStorageSync` `safehome_anonymous_user_id`（JS:796）、`setStorageSync` `auth_token`（JS:811）、`setStorageSync` `auth_user`（JS:812）、`removeStorageSync` `safehome_anonymous_user_id`（JS:813）、`setStorageSync` `auth_token`（JS:836）、`setStorageSync` `auth_user`（JS:837）、`removeStorageSync` `safehome_anonymous_user_id`（JS:838）、`removeStorageSync` `auth_token`（JS:845）、`removeStorageSync` `auth_user`（JS:846）、`getStorageSync` `STORAGE_KEY`（JS:2189）、`setStorageSync` `STORAGE_KEY`（JS:2195）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2231）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2258）、`getStorageSync` `auth_token`（JS:2271）、`getStorageSync` `auth_user`（JS:2275）、`removeStorageSync` `auth_token`（JS:2301）、`removeStorageSync` `auth_user`（JS:2302）
- WXML 数据绑定：`user`、`loggedIn`、`identityStatus`、`identityBusy`、`dataClaim`、`item`、`claimBusy`、`isResearcher`、`recordEntries`、`index`、`supportEntries`、`safetyEntries`、`settingsEntries`
- 条件状态：`user`、`loggedIn`、`identityStatus`、`dataClaim`
- `setData` 状态：`user`、`loginState`、`streakText`、`growthLevel`、`roleText`、`isResearcher`、`showcaseAccess`、`stats`、`loggedIn`、`dataClaim`、`identityStatus`、`nickname`、`claimBusy`、`identityBusy`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 37：设置与说明 `pages/settings-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`0eac4d44b763061649a9ded63a138923043c067722ede09fd683c53eead8c447`
- 核对文件：`apps/miniprogram/pages/settings-detail/index.wxml`、`apps/miniprogram/pages/settings-detail/index.wxss`、`apps/miniprogram/pages/settings-detail/index.js`、`apps/miniprogram/pages/settings-detail/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/services/minorSafeguardsApi.js`
- 上游页面：`pages/home/index`、`pages/login/index`、`pages/profile/index`
- 页面组件：`section-title` → `/components/section-title/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`page-state` → `/components/page-state/index`、`status-pill` → `/components/status-pill/index`
- 主要可见内容：重新读取、学生保护状态、请选择符合你的年龄范围。系统不会要求填写出生日期。、我已满14周岁、我未满14周岁、请向家长获取6位绑定码。完成绑定后，仍需家长单独确认是否同意受保护的数据处理。、完成家长绑定、已完成家长账号绑定，正在等待监护人确认。绑定关系本身不等于监护人同意。、监护人已经同意，但你自己仍可以决定是否继续使用测评、研究参与、自由文本和画像等受保护功能。、我愿意继续、我暂时不继续、参与者本人或监护人已经拒绝/撤回，受保护功能已暂停。需要再次继续时，应重新完成相应确认。、未满14周岁保护条件已经满足。监护人和学生本人仍可撤回。、我想暂停受保护功能、年龄范围已确认，本账号不需要未满14周岁的监护人数据处理门禁。、家长绑定与监护人确认、先生成绑定码给学生。学生完成绑定后，如果其年龄为未满14周岁，你可以在下方单独同意或撤回受保护的数据处理。、生成6位绑定码、绑定码：、有效期至：、绑定码只用于建立家庭账号关系，不代表已经同意敏感数据处理。、已绑定学生、关系：、年龄范围：未满14周岁

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 28 | — | `bindaction` | `goProtectionLogin` | — |
| 40 | 重新读取 | `bindtap` | `loadProtectionStatus` | — |
| 51 | 我已满14周岁 | `bindtap` | `chooseAge` | {'age': '14_or_over'} |
| 52 | 我未满14周岁 | `bindtap` | `chooseAge` | {'age': 'under_14'} |
| 57 | 完成家长绑定 | `bindinput` | `onBindCodeInput` | — |
| 65 | 完成家长绑定 | `bindtap` | `submitStudentBinding` | — |
| 74 | 我愿意继续 | `bindtap` | `updateChildDecision` | {'assented': 'true'} |
| 75 | 我暂时不继续 | `bindtap` | `updateChildDecision` | {'assented': 'false'} |
| 84 | 我想暂停受保护功能 | `bindtap` | `updateChildDecision` | {'assented': 'false'} |
| 95 | 生成6位绑定码 | `bindtap` | `createGuardianBindCode` | — |
| 114 | 同意受保护数据处理 | `bindtap` | `updateGuardianDecision` | {'child': '{{item.student_user_id}}', 'agreed': 'true'} |
| 122 | 撤回监护人同意 | `bindtap` | `updateGuardianDecision` | {'child': '{{item.student_user_id}}', 'agreed': 'false'} |
| 146 | 删除申请< | `bindaction` | `handlePrivacyStateAction` | — |
| 165 | 取消申请 | `bindtap` | `cancelPrivacyRequest` | {'id': '{{item.id}}'} |
| 172 | 补充说明并重新提交 | `bindtap` | `appealPrivacyRequest` | {'id': '{{item.id}}'} |
| 189 | — | `bindtap` | `submitPrivacyDeleteRequest` | — |
| 199 | 返回 | `bindtap` | `goBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 343 | `listPrivacyRequests` | `GET` | `/api/privacy/requests` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |
| 375 | `createPrivacyDeleteRequest` | `POST` | `/api/privacy/delete-my-data` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |
| 399 | `cancelPrivacyRequest` | `POST` | `/api/privacy/requests` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |
| 429 | `appealPrivacyRequest` | `POST` | `/api/privacy/requests` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprivacy`（js:443）、`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprotection`（js:450）、`navigateTo` → `/pages/login/index:dynamic`（js:2480）
- 本地存储：`getStorageSync` `auth_user`（JS:648）、`removeStorageSync` `auth_token`（JS:672）、`removeStorageSync` `auth_user`（JS:673）、`getStorageSync` `auth_token`（JS:695）、`setStorageSync` `auth_token`（JS:915）、`setStorageSync` `auth_user`（JS:916）、`removeStorageSync` `safehome_anonymous_user_id`（JS:917）、`setStorageSync` `auth_token`（JS:963）、`setStorageSync` `auth_user`（JS:964）、`setStorageSync` `auth_token`（JS:979）、`setStorageSync` `auth_user`（JS:980）、`removeStorageSync` `safehome_anonymous_user_id`（JS:981）、`setStorageSync` `auth_token`（JS:996）、`setStorageSync` `auth_user`（JS:997）、`removeStorageSync` `safehome_anonymous_user_id`（JS:998）、`setStorageSync` `auth_token`（JS:1021）、`setStorageSync` `auth_user`（JS:1022）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1023）、`removeStorageSync` `auth_token`（JS:1030）、`removeStorageSync` `auth_user`（JS:1031）、`getStorageSync` `STORAGE_KEY`（JS:2374）、`setStorageSync` `STORAGE_KEY`（JS:2380）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2416）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2443）、`getStorageSync` `auth_token`（JS:2456）、`getStorageSync` `auth_user`（JS:2460）、`removeStorageSync` `auth_token`（JS:2486）、`removeStorageSync` `auth_user`（JS:2487）、`removeStorageSync` `auth_token`（JS:2538）、`removeStorageSync` `auth_user`（JS:2539）、`getStorageSync` `auth_token`（JS:2544）
- WXML 数据绑定：`notice`、`item`、`line`、`noticeType`、`protectionLoading`、`protectionNeedsLogin`、`protectionError`、`protectionRole`、`protectionStatus`、`protectionBusy`、`bindCodeInput`、`generatedBindCode`、`generatedBindExpiresAt`、`guardianChildren`、`privacyLoading`、`privacyRequests`、`privacySubmitting`
- 条件状态：`noticeType`、`protectionLoading`、`protectionNeedsLogin`、`protectionError`、`protectionRole`、`protectionStatus`、`generatedBindCode`、`guardianChildren`、`item`、`privacyLoading`、`privacyRequests`
- `setData` 状态：`notice`、`noticeType`、`protectionLoading`、`protectionNeedsLogin`、`protectionError`、`protectionRole`、`protectionStatus`、`guardianChildren`、`statusLabel`、`protectionBusy`、`bindCodeInput`、`generatedBindCode`、`generatedBindExpiresAt`、`privacyLoading`、`privacyError`、`privacyNeedsLogin`、`privacyRequests`、`privacySubmitting`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 38：本周小目标 `pages/goal-setting/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`bce5fd9948576f33252bf06c6d82a6abb43a5b1a260868790918f045b6e8cbc6`
- 核对文件：`apps/miniprogram/pages/goal-setting/index.wxml`、`apps/miniprogram/pages/goal-setting/index.wxss`、`apps/miniprogram/pages/goal-setting/index.js`、`apps/miniprogram/pages/goal-setting/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/home/index`
- 页面组件：—
- 主要可见内容：MVP 1.1 第一步、设定本周小目标、先选一个最常出现的亲子场景，再写下这周想练习的一个小动作。、高频亲子冲突场景、选择最常出现的一个场景，也可以自己填写。、希望减少的旧反应、这里不是评价对错，只是找到一个可以先少一点的反应。、希望练习的新反应、先选一个很小、能试一次的动作。、本周 SMART 小目标、写成一周内可以观察到的小目标，不需要很完美。、网络响应较慢；草稿仍在本机，请不要重复点击。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 16 | — | `bindtap` | `selectScene` | {'value': '{{item}}'} |
| 26 | — | `bindinput` | `onTextInput` | {'key': 'customScene'} |
| 36 | — | `bindtap` | `selectOldReaction` | {'value': '{{item}}'} |
| 55 | — | `bindtap` | `selectNewReaction` | {'value': '{{item}}'} |
| 73 | — | `bindinput` | `onTextInput` | {'key': 'smartGoal'} |
| 89 | — | `bindtap` | `submitGoal` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 85 | `createGoal` | `POST` | `/api/goals` | `backend/app.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/goals.py`、`backend/scripts/generate_task33_ux_registry.py`、`backend/scripts/generate_task34_operations_registry.py`、`backend/scripts/migrate_task33_ux_governance.py`、`backend/scripts/verify_privacy_restore.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index?goal_id=:dynamic`（js:100）
- 本地存储：`getStorageSync` `auth_user`（JS:304）、`removeStorageSync` `auth_token`（JS:328）、`removeStorageSync` `auth_user`（JS:329）、`getStorageSync` `auth_token`（JS:351）、`setStorageSync` `auth_token`（JS:571）、`setStorageSync` `auth_user`（JS:572）、`removeStorageSync` `safehome_anonymous_user_id`（JS:573）、`setStorageSync` `auth_token`（JS:619）、`setStorageSync` `auth_user`（JS:620）、`setStorageSync` `auth_token`（JS:635）、`setStorageSync` `auth_user`（JS:636）、`removeStorageSync` `safehome_anonymous_user_id`（JS:637）、`setStorageSync` `auth_token`（JS:652）、`setStorageSync` `auth_user`（JS:653）、`removeStorageSync` `safehome_anonymous_user_id`（JS:654）、`setStorageSync` `auth_token`（JS:677）、`setStorageSync` `auth_user`（JS:678）、`removeStorageSync` `safehome_anonymous_user_id`（JS:679）、`removeStorageSync` `auth_token`（JS:686）、`removeStorageSync` `auth_user`（JS:687）、`getStorageSync` `STORAGE_KEY`（JS:2030）、`setStorageSync` `STORAGE_KEY`（JS:2036）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2072）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2099）、`getStorageSync` `storageKey`（JS:2134）、`setStorageSync` `storageKey`（JS:2156）、`removeStorageSync` `storageKey`（JS:2186）
- WXML 数据绑定：`sceneOptions`、`selectedScene`、`item`、`customScene`、`oldReactionOptions`、`oldReaction`、`newReactionOptions`、`newReaction`、`smartGoal`、`errorMessage`、`draftRestored`、`saveStatus`、`slowSubmitting`、`submitting`
- 条件状态：`errorMessage`、`slowSubmitting`
- `setData` 状态：`saveStatus`、`draftRestored`、`selectedScene`、`errorMessage`、`submitting`、`slowSubmitting`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 39：记录情绪事件 `pages/diary-form/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`44c18f96b0789f09c97fe2a144af991ced26ea076caabe5ee222d2d3d8834130`
- 核对文件：`apps/miniprogram/pages/diary-form/index.wxml`、`apps/miniprogram/pages/diary-form/index.wxss`、`apps/miniprogram/pages/diary-form/index.js`、`apps/miniprogram/pages/diary-form/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/home/index`、`pages/getting-started/index`、`pages/growth-dashboard/index`、`pages/goal-setting/index`、`pages/feedback-result/index`、`pages/training-card/index`
- 页面组件：—
- 主要可见内容：记录刚才发生的一小段、先从一个具体片段开始，写清当时发生了什么、有什么感受。、已关联本周小目标、1 分钟写事件、选一个情绪、保存后看反馈、请不要填写姓名、学校、电话等可识别身份的信息。、发生了什么、选一个场景，再写下刚才最清楚的一小段。、其他场景、具体经过、我和孩子当时的感受、只需要按当时看起来最接近的状态选择。、家长当时的主要情绪、强度 / 10、孩子当时看起来的情绪、想法与做法（可选）、如果愿意，可以补充当时脑中闪过的话和能看到的动作。、当时心里的第一反应、我当时的做法、身体与后续（可选）、身体感受、后续结果和担心可以帮助复盘；不填也能提交。、身体感觉、孩子后来的反应

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 25 | — | `bindtap` | `selectScene` | {'value': '{{item}}'} |
| 37 | — | `bindinput` | `onTextInput` | {'key': 'customScene'} |
| 41 | — | `bindinput` | `onTextInput` | {'key': 'eventDescription'} |
| 61 | — | `bindtap` | `selectParentEmotion` | {'value': '{{item}}'} |
| 73 | — | `bindchange` | `onParentIntensityChange` | — |
| 80 | — | `bindtap` | `selectChildEmotion` | {'value': '{{item}}'} |
| 92 | — | `bindchange` | `onChildIntensityChange` | — |
| 97 | — | `bindtap` | `toggleMoreFields` | — |
| 110 | — | `bindinput` | `onTextInput` | {'key': 'automaticThought'} |
| 120 | — | `bindinput` | `onTextInput` | {'key': 'behavior'} |
| 140 | — | `bindtap` | `selectBodySensation` | {'value': '{{item}}'} |
| 150 | — | `bindinput` | `onTextInput` | {'key': 'bodySensationNote'} |
| 154 | — | `bindinput` | `onTextInput` | {'key': 'childReaction'} |
| 164 | — | `bindinput` | `onTextInput` | {'key': 'shortTermResult'} |
| 174 | — | `bindinput` | `onTextInput` | {'key': 'longTermImpact'} |
| 194 | — | `bindtap` | `submitDiary` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 133 | `createDiary` | `POST` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py`、`backend/routes/general_growth.py`、`backend/routes/minor_safeguards.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/feedback-result/index?diary_id=:dynamic`（js:150）、`navigateTo` → `/pages/login/index:dynamic`（js:2186）
- 本地存储：`getStorageSync` `auth_user`（JS:354）、`removeStorageSync` `auth_token`（JS:378）、`removeStorageSync` `auth_user`（JS:379）、`getStorageSync` `auth_token`（JS:401）、`setStorageSync` `auth_token`（JS:621）、`setStorageSync` `auth_user`（JS:622）、`removeStorageSync` `safehome_anonymous_user_id`（JS:623）、`setStorageSync` `auth_token`（JS:669）、`setStorageSync` `auth_user`（JS:670）、`setStorageSync` `auth_token`（JS:685）、`setStorageSync` `auth_user`（JS:686）、`removeStorageSync` `safehome_anonymous_user_id`（JS:687）、`setStorageSync` `auth_token`（JS:702）、`setStorageSync` `auth_user`（JS:703）、`removeStorageSync` `safehome_anonymous_user_id`（JS:704）、`setStorageSync` `auth_token`（JS:727）、`setStorageSync` `auth_user`（JS:728）、`removeStorageSync` `safehome_anonymous_user_id`（JS:729）、`removeStorageSync` `auth_token`（JS:736）、`removeStorageSync` `auth_user`（JS:737）、`getStorageSync` `STORAGE_KEY`（JS:2080）、`setStorageSync` `STORAGE_KEY`（JS:2086）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2122）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2149）、`getStorageSync` `auth_token`（JS:2162）、`getStorageSync` `auth_user`（JS:2166）、`removeStorageSync` `auth_token`（JS:2192）、`removeStorageSync` `auth_user`（JS:2193）、`getStorageSync` `storageKey`（JS:2235）、`setStorageSync` `storageKey`（JS:2257）、`removeStorageSync` `storageKey`（JS:2287）
- WXML 数据绑定：`goalId`、`sceneOptions`、`selectedScene`、`item`、`customScene`、`eventDescription`、`parentEmotionOptions`、`parentEmotion`、`parentEmotionIntensity`、`childEmotionOptions`、`childEmotion`、`childEmotionIntensity`、`showMoreFields`、`automaticThought`、`behavior`、`bodySensationOptions`、`bodySensation`、`bodySensationNote`、`childReaction`、`shortTermResult`、`longTermImpact`、`errorMessage`、`draftRestored`、`saveStatus`、`slowSubmitting`、`submitting`
- 条件状态：`goalId`、`showMoreFields`、`errorMessage`、`slowSubmitting`
- `setData` 状态：`goalId`、`saveStatus`、`draftRestored`、`errorMessage`、`submitting`、`slowSubmitting`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 40：本次反馈 `pages/feedback-result/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`54b80958824749f223f8ed944a00b05717f9b3413dff50d66ec090ba4e190e43`
- 核对文件：`apps/miniprogram/pages/feedback-result/index.wxml`、`apps/miniprogram/pages/feedback-result/index.wxss`、`apps/miniprogram/pages/feedback-result/index.js`、`apps/miniprogram/pages/feedback-result/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/diary-form/index`
- 页面组件：`section-title` → `/components/section-title/index`、`training-task-card` → `/components/training-task-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：先看见发生了什么、以下内容用于自我观察和练习参考，不评价谁对谁错。、支持性总结、一个小练习、必要时找人看、先接住这次感受、主要情绪、情绪强度、优先联系现实支持、这里不是实时危机服务，也不替代线下专业支持或当地紧急服务。、查看安全指引、提交人工关注、主练习 ·、推荐理由：、开始这个练习、今天先做、这次记录暂时没有匹配到具体训练卡，可以先暂停几秒，再说出一个最明显的感受。、今日建议只作为支持性练习参考，不构成诊断或治疗方案。、也可以选择、需要多一个人帮你看一看？、如果这类情况反复出现，或你担心自己撑不住，可以提交给人工督导补充反馈。、提交督导、收藏这次反馈、怎样理解这份反馈

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 16 | 先接住这次感受 | `bindaction` | `handleFeedbackStateAction` | — |
| 25 | — | `bindselect` | `submitFeedbackEvaluation` | — |
| 65 | 查看安全指引 | `bindtap` | `openEmergencyGuide` | — |
| 66 | 提交人工关注 | `bindtap` | `openSupervision` | — |
| 77 | 开始这个练习 | `bindtap` | `openTrainingCard` | — |
| 108 | 提交督导 | `bindtap` | `openSupervision` | — |
| 112 | 收藏这次反馈 | `bindtap` | `saveFeedback` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 45 | `generateFeedback` | `POST` | `/api/feedback/generate` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py`、`backend/routes/cards.py` |
| 46 | `listCards` | `GET` | `/api/cards` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py`、`backend/routes/cards.py` |
| 209 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py`、`backend/routes/cards.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index`（js:226）、`navigateTo` → `/pages/training-card/index?tags=:dynamic`（js:249）、`navigateTo` → `/pages/supervision/index?diary_id=:dynamic`（js:255）、`navigateTo` → `/pages/emergency-guide/index`（js:261）
- 本地存储：`setStorageSync` `LATEST_TRAINING_RECOMMENDATION_KEY`（JS:178）、`getStorageSync` `auth_user`（JS:455）、`removeStorageSync` `auth_token`（JS:479）、`removeStorageSync` `auth_user`（JS:480）、`getStorageSync` `auth_token`（JS:502）、`setStorageSync` `auth_token`（JS:722）、`setStorageSync` `auth_user`（JS:723）、`removeStorageSync` `safehome_anonymous_user_id`（JS:724）、`setStorageSync` `auth_token`（JS:770）、`setStorageSync` `auth_user`（JS:771）、`setStorageSync` `auth_token`（JS:786）、`setStorageSync` `auth_user`（JS:787）、`removeStorageSync` `safehome_anonymous_user_id`（JS:788）、`setStorageSync` `auth_token`（JS:803）、`setStorageSync` `auth_user`（JS:804）、`removeStorageSync` `safehome_anonymous_user_id`（JS:805）、`setStorageSync` `auth_token`（JS:828）、`setStorageSync` `auth_user`（JS:829）、`removeStorageSync` `safehome_anonymous_user_id`（JS:830）、`removeStorageSync` `auth_token`（JS:837）、`removeStorageSync` `auth_user`（JS:838）、`getStorageSync` `STORAGE_KEY`（JS:2181）、`setStorageSync` `STORAGE_KEY`（JS:2187）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2223）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2250）
- WXML 数据绑定：`loading`、`errorMessage`、`missingDiaryId`、`feedback`、`feedbackEvaluation`、`feedbackEvaluationSaving`、`emotionOverview`、`patternCards`、`item`、`isHighRisk`、`riskSupportText`、`canShowTraining`、`trainingRecommendation`、`recommendedTrainings`、`trainingIndex`
- 条件状态：`loading`、`errorMessage`、`isHighRisk`、`canShowTraining`、`trainingRecommendation`、`recommendedTrainings`、`trainingIndex`
- `setData` 状态：`diaryId`、`loading`、`missingDiaryId`、`errorMessage`、`labelsText`、`patternCards`、`emotionOverview`、`nextAction`、`riskSupportText`、`feedback`、`isHighRisk`、`canShowTraining`、`trainingRecommendation`、`recommendedTrainings`、`feedbackEvaluationSaving`、`feedbackEvaluation`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 41：家庭关系测一测 `pages/assessment/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`21f4d347f34e9fc8a9e2dcab77704f47cd30e95d3d9deefcd039c5d587b994bf`
- 核对文件：`apps/miniprogram/pages/assessment/index.wxml`、`apps/miniprogram/pages/assessment/index.wxss`、`apps/miniprogram/pages/assessment/index.js`、`apps/miniprogram/pages/assessment/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`、`pages/personalized-plan/index`、`pages/relationship-pilot/index`、`pages/growth-dashboard/index`、`pages/assessment-history/index`
- 页面组件：`section-title` → `/components/section-title/index`、`function-entry-card` → `/components/function-entry-card/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：支持性测评、按当前情况做一次自我观察。结果只用于理解线索和选择练习，不给人贴标签。、清除、打开联调测试页、正在读取测一测内容...、· 项 · 约 分钟、查看、去登录

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 10 | — | `bindtap` | `switchAudience` | {'key': '{{item.key}}'} |
| 19 | 清除 | `bindinput` | `onSearchInput` | — |
| 20 | 清除 | `bindtap` | `clearSearch` | — |
| 27 | 打开联调测试页 | `bindtap` | `openIntegrationTest` | — |
| 40 | 打开测评：{{worksheet.display_title}} | `bindtap` | `openAssessmentEntry` | {'id': '{{worksheet.id}}', 'enabled': '{{worksheet.is_enabled_for_user}}'} |
| 64 | 查看测评记录：{{item.worksheet_title}} | `bindtap` | `openRecentResult` | {'id': '{{item.id}}', 'worksheet-id': '{{item.worksheet_id}}'} |
| 89 | 去登录 | `bindtap` | `goLogin` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 46 | `getDebugConfig` | `GET` | — | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/general_growth.py`、`backend/routes/parent_assessments.py` |
| 195 | `listAssessments` | `GET` | `/api/assessments` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/general_growth.py`、`backend/routes/parent_assessments.py` |
| 219 | `listAssessmentResults` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/general_growth.py`、`backend/routes/parent_assessments.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment-detail/index?id=:dynamic`（js:262）、`navigateTo` → `/pages/assessment-result/index?id=:dynamic`（js:271）、`navigateTo` → `/pages/integration-test/index`（js:284）、`navigateTo` → `/pages/login/index:dynamic`（js:2310）
- 本地存储：`getStorageSync` `auth_user`（JS:478）、`removeStorageSync` `auth_token`（JS:502）、`removeStorageSync` `auth_user`（JS:503）、`getStorageSync` `auth_token`（JS:525）、`setStorageSync` `auth_token`（JS:745）、`setStorageSync` `auth_user`（JS:746）、`removeStorageSync` `safehome_anonymous_user_id`（JS:747）、`setStorageSync` `auth_token`（JS:793）、`setStorageSync` `auth_user`（JS:794）、`setStorageSync` `auth_token`（JS:809）、`setStorageSync` `auth_user`（JS:810）、`removeStorageSync` `safehome_anonymous_user_id`（JS:811）、`setStorageSync` `auth_token`（JS:826）、`setStorageSync` `auth_user`（JS:827）、`removeStorageSync` `safehome_anonymous_user_id`（JS:828）、`setStorageSync` `auth_token`（JS:851）、`setStorageSync` `auth_user`（JS:852）、`removeStorageSync` `safehome_anonymous_user_id`（JS:853）、`removeStorageSync` `auth_token`（JS:860）、`removeStorageSync` `auth_user`（JS:861）、`getStorageSync` `STORAGE_KEY`（JS:2204）、`setStorageSync` `STORAGE_KEY`（JS:2210）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2246）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2273）、`getStorageSync` `auth_token`（JS:2286）、`getStorageSync` `auth_user`（JS:2290）、`removeStorageSync` `auth_token`（JS:2316）、`removeStorageSync` `auth_user`（JS:2317）
- WXML 数据绑定：`tabs`、`activeAudience`、`item`、`searchKeyword`、`errorMessage`、`loading`、`categories`、`worksheet`、`recentResults`、`recentLoginTip`
- 条件状态：`searchKeyword`、`errorMessage`、`loading`、`item`、`recentResults`、`recentLoginTip`
- `setData` 状态：`activeAudience`、`searchKeyword`、`categories`、`loading`、`errorMessage`、`boundaryNotice`、`allAssessments`、`recentResults`、`recentLoginTip`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 42：全部测评记录 `pages/assessment-history/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`61b3d85dcdb7a63dfc9b1e48a44350e99651633b16403c81411c124abbf065a3`
- 核对文件：`apps/miniprogram/pages/assessment-history/index.wxml`、`apps/miniprogram/pages/assessment-history/index.wxss`、`apps/miniprogram/pages/assessment-history/index.js`、`apps/miniprogram/pages/assessment-history/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/profile/index`
- 页面组件：—
- 主要可见内容：测评记录、回看每一次阶段性观察、这里保留该账号完成过的全部支持性测评。结果用于自我了解，不构成诊断或固定判断。、份已保存记录、正在读取测评记录、请稍等一下。、记录暂时没有加载成功、重新加载、已显示全部 份记录、还没有测评记录、完成一份支持性测评后，记录会保存在这里。、去测一测

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 20 | 重新加载 | `bindtap` | `retry` | — |
| 24 | — | `bindtap` | `openResult` | {'id': '{{item.id}}', 'worksheet-id': '{{item.worksheet_id}}'} |
| 38 | — | `bindtap` | `loadMore` | — |
| 47 | 去测一测 | `bindtap` | `goAssessment` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 55 | `listAssessmentResults` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/general_growth.py`、`backend/routes/profile.py`、`backend/routes/research_workspace.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment-result/index?id=:dynamic`（js:88）、`navigateTo` → `/pages/assessment/index`（js:94）、`navigateTo` → `/pages/login/index:dynamic`（js:2120）
- 本地存储：`getStorageSync` `auth_user`（JS:288）、`removeStorageSync` `auth_token`（JS:312）、`removeStorageSync` `auth_user`（JS:313）、`getStorageSync` `auth_token`（JS:335）、`setStorageSync` `auth_token`（JS:555）、`setStorageSync` `auth_user`（JS:556）、`removeStorageSync` `safehome_anonymous_user_id`（JS:557）、`setStorageSync` `auth_token`（JS:603）、`setStorageSync` `auth_user`（JS:604）、`setStorageSync` `auth_token`（JS:619）、`setStorageSync` `auth_user`（JS:620）、`removeStorageSync` `safehome_anonymous_user_id`（JS:621）、`setStorageSync` `auth_token`（JS:636）、`setStorageSync` `auth_user`（JS:637）、`removeStorageSync` `safehome_anonymous_user_id`（JS:638）、`setStorageSync` `auth_token`（JS:661）、`setStorageSync` `auth_user`（JS:662）、`removeStorageSync` `safehome_anonymous_user_id`（JS:663）、`removeStorageSync` `auth_token`（JS:670）、`removeStorageSync` `auth_user`（JS:671）、`getStorageSync` `STORAGE_KEY`（JS:2014）、`setStorageSync` `STORAGE_KEY`（JS:2020）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2056）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2083）、`getStorageSync` `auth_token`（JS:2096）、`getStorageSync` `auth_user`（JS:2100）、`removeStorageSync` `auth_token`（JS:2126）、`removeStorageSync` `auth_user`（JS:2127）
- WXML 数据绑定：`total`、`loading`、`errorMessage`、`items`、`item`、`index`、`hasMore`、`loadingMore`
- 条件状态：`loading`、`errorMessage`、`items`、`hasMore`
- `setData` 状态：`loading`、`loadingMore`、`errorMessage`、`items`、`page`、`total`、`hasMore`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 43：填写测评 `pages/assessment-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`2736d02f98e759f2b95d80e5d58933ea50bf9103cec1fc52f5675fa565007186`
- 核对文件：`apps/miniprogram/pages/assessment-detail/index.wxml`、`apps/miniprogram/pages/assessment-detail/index.wxss`、`apps/miniprogram/pages/assessment-detail/index.js`、`apps/miniprogram/pages/assessment-detail/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/assessment/index`
- 页面组件：`section-title` → `/components/section-title/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：正在读取测一测内容...、注意：本内容含敏感语义，结果只作为自我观察线索，不作为诊断建议。、去登录后继续、网络响应较慢；草稿仍在本机，请不要重复点击。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 28 | 选择 {{opt.displayLabel}} | `bindtap` | `selectOption` | {'index': '{{qi}}', 'value': '{{opt.value}}', 'score': '{{opt.score}}'} |
| 45 | — | `bindinput` | `onTextInput` | {'index': '{{qi}}'} |
| 58 | 去登录后继续 | `bindtap` | `goLogin` | — |
| 64 | — | `bindtap` | `submitWorksheet` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 115 | `getAssessment` | `GET` | `/api/assessments` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/content_review.py`、`backend/routes/general_growth.py` |
| 231 | `createProfile` | `POST` | `/api/profile` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/content_review.py`、`backend/routes/general_growth.py` |
| 232 | `createAssessmentResult` | `POST` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/content_review.py`、`backend/routes/general_growth.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment-result/index?id=:dynamic`（js:243）、`navigateTo` → `/pages/login/index:dynamic`（js:2293）
- 本地存储：`getStorageSync` `auth_user`（JS:461）、`removeStorageSync` `auth_token`（JS:485）、`removeStorageSync` `auth_user`（JS:486）、`getStorageSync` `auth_token`（JS:508）、`setStorageSync` `auth_token`（JS:728）、`setStorageSync` `auth_user`（JS:729）、`removeStorageSync` `safehome_anonymous_user_id`（JS:730）、`setStorageSync` `auth_token`（JS:776）、`setStorageSync` `auth_user`（JS:777）、`setStorageSync` `auth_token`（JS:792）、`setStorageSync` `auth_user`（JS:793）、`removeStorageSync` `safehome_anonymous_user_id`（JS:794）、`setStorageSync` `auth_token`（JS:809）、`setStorageSync` `auth_user`（JS:810）、`removeStorageSync` `safehome_anonymous_user_id`（JS:811）、`setStorageSync` `auth_token`（JS:834）、`setStorageSync` `auth_user`（JS:835）、`removeStorageSync` `safehome_anonymous_user_id`（JS:836）、`removeStorageSync` `auth_token`（JS:843）、`removeStorageSync` `auth_user`（JS:844）、`getStorageSync` `STORAGE_KEY`（JS:2187）、`setStorageSync` `STORAGE_KEY`（JS:2193）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2229）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2256）、`getStorageSync` `auth_token`（JS:2269）、`getStorageSync` `auth_user`（JS:2273）、`removeStorageSync` `auth_token`（JS:2299）、`removeStorageSync` `auth_user`（JS:2300）、`getStorageSync` `storageKey`（JS:2342）、`setStorageSync` `storageKey`（JS:2364）、`removeStorageSync` `storageKey`（JS:2394）
- WXML 数据绑定：`loading`、`worksheet`、`qi`、`item`、`opt`、`errorMessage`、`needsLogin`、`draftRestored`、`saveStatus`、`slowSubmitting`、`submitting`
- 条件状态：`loading`、`worksheet`、`item`、`errorMessage`、`needsLogin`、`slowSubmitting`
- `setData` 状态：`loading`、`needsLogin`、`worksheetId`、`errorMessage`、`worksheet`、`saveStatus`、`draftRestored`、`submitting`、`slowSubmitting`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 44：测一测结果 `pages/assessment-result/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`e27c0dd8656cfbc493623cbbba92671eb13ef03c0221f91cef1a397dd75d5394`
- 核对文件：`apps/miniprogram/pages/assessment-result/index.wxml`、`apps/miniprogram/pages/assessment-result/index.wxss`、`apps/miniprogram/pages/assessment-result/index.js`、`apps/miniprogram/pages/assessment-result/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/assessment-dimension-visualization.js`
- 上游页面：`pages/assessment/index`、`pages/assessment-history/index`、`pages/assessment-detail/index`
- 页面组件：`section-title` → `/components/section-title/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`visualization-state` → `/components/visualization-state/index`
- 主要可见内容：正在读取结果...、匹配清晰度：、参照、当前位置、优势提示、可以先做、可以带去讨论的问题、后续项目任务线索、分、查看可练习任务、返回测一测

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 138 | 查看可练习任务 | `bindtap` | `openRecommendedCards` | — |
| 139 | 返回测一测 | `bindtap` | `backToAssessment` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 447 | `getAssessmentResult` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |
| 448 | `getAssessment` | `GET` | `/api/assessments` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |
| 449 | `listCards` | `GET` | `/api/cards` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |
| 454 | `getAssessmentProfilePosition` | `GET` | `/api/assessment-results/:id/profile-position` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:699）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:705）、`switchTab` → `/pages/training/index`（js:710）
- 本地存储：`setStorageSync` `LATEST_TRAINING_RECOMMENDATION_KEY`（JS:359）、`setStorageSync` `THREE_DAY_LIGHT_PLAN_KEY`（JS:401）、`getStorageSync` `auth_user`（JS:908）、`removeStorageSync` `auth_token`（JS:932）、`removeStorageSync` `auth_user`（JS:933）、`getStorageSync` `auth_token`（JS:955）、`setStorageSync` `auth_token`（JS:1175）、`setStorageSync` `auth_user`（JS:1176）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1177）、`setStorageSync` `auth_token`（JS:1223）、`setStorageSync` `auth_user`（JS:1224）、`setStorageSync` `auth_token`（JS:1239）、`setStorageSync` `auth_user`（JS:1240）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1241）、`setStorageSync` `auth_token`（JS:1256）、`setStorageSync` `auth_user`（JS:1257）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1258）、`setStorageSync` `auth_token`（JS:1281）、`setStorageSync` `auth_user`（JS:1282）、`removeStorageSync` `safehome_anonymous_user_id`（JS:1283）、`removeStorageSync` `auth_token`（JS:1290）、`removeStorageSync` `auth_user`（JS:1291）、`getStorageSync` `STORAGE_KEY`（JS:2634）、`setStorageSync` `STORAGE_KEY`（JS:2640）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2676）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2703）
- WXML 数据绑定：`loading`、`result`、`riskSummary`、`profilePosition`、`item`、`index`、`profileSummary`、`scaleVisualization`、`trainingRecommendation`、`errorMessage`
- 条件状态：`loading`、`result`、`riskSummary`、`profilePosition`、`profileSummary`、`scaleVisualization`、`item`、`trainingRecommendation`
- `setData` 状态：`resultId`、`worksheetId`、`loading`、`errorMessage`、`totalScoreText`、`recommendedCardsText`、`result`、`worksheet`、`profileSummary`、`scaleDimensions`、`scaleVisualization`、`sourceNotice`、`trainingRecommendation`、`riskSummary`、`profilePosition`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 45：教育热榜 `pages/hot-topics/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`064f3acc65965fcae7e84e21ff8aaaf626cdf6c0025d0657d5477670e1fa3492`
- 核对文件：`apps/miniprogram/pages/hot-topics/index.wxml`、`apps/miniprogram/pages/hot-topics/index.wxss`、`apps/miniprogram/pages/hot-topics/index.js`、`apps/miniprogram/pages/hot-topics/index.json`
- 上游页面：`pages/home/index`
- 页面组件：`section-title` → `/components/section-title/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`training-task-card` → `/components/training-task-card/index`
- 主要可见内容：教育热榜、看看其他家庭如何处理类似问题、这里不是评价谁做得对错，而是把常见亲子互动片段整理成更容易练习的小步骤。、问题情境、常见回应、可以换一种说法、查看关联训练卡、这些案例只用于自我观察和陪伴练习，不用于判断孩子、家长或家庭关系。如果出现紧急安全风险，请优先寻求现实支持和专业帮助。、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 11 | — | `bindtap` | `selectTag` | {'tag': '{{item}}'} |
| 27 | — | `bindtap` | `selectTopic` | {'id': '{{item.id}}'} |
| 71 | 查看关联训练卡 | `bindtapcard` | `openPractice` | — |
| 80 | 查看关联训练卡 | `bindtap` | `openPractice` | — |
| 91 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index?tags=:dynamic`（js:151）、`switchTab` → `/pages/home/index`（js:157）
- 本地存储：—
- WXML 数据绑定：`false`、`tags`、`activeTag`、`item`、`visibleTopics`、`selectedTopic`
- 条件状态：—
- `setData` 状态：`selectedTopic`、`activeTag`、`visibleTopics`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 46：UP任务卡 `pages/task-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`0561119521c7446178a1afd1c79baf8d49214f258962216335566fe0f212cfd0`
- 核对文件：`apps/miniprogram/pages/task-detail/index.wxml`、`apps/miniprogram/pages/task-detail/index.wxss`、`apps/miniprogram/pages/task-detail/index.js`、`apps/miniprogram/pages/task-detail/index.json`
- 上游页面：`pages/training/index`、`pages/training-card/index`
- 页面组件：`section-title` → `/components/section-title/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：训练卡详情、UP 任务卡、适用情境、预计用时、今天的小目标、今天先练这一小步、先按下面 3 个小动作走一遍。做不到完整也没关系，能停一下就算开始了。、今日感受、当前情绪强度： / 10、完成并打卡、从第一步开始、暂存感受

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 3 | ‹ | `bindtap` | `goBack` | — |
| 55 | 当前情绪强度： / 10 | `bindinput` | `onReflectionInput` | — |
| 57 | — | `bindchange` | `onEmotionLevelChange` | — |
| 66 | 完成并打卡 | `bindtap` | `finishPractice` | — |
| 68 | 从第一步开始 | `bindtap` | `startPractice` | — |
| 69 | 暂存感受 | `bindtap` | `recordFeeling` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/checkin/index?card_id=:dynamic`（js:202）
- 本地存储：`getStorageSync` `safehome:selectedTrainingCard`（JS:156）
- WXML 数据绑定：`task`、`index`、`item`、`reflection`、`emotionLevel`
- 条件状态：`task`
- `setData` 状态：`task`、`title`、`diaryId`、`reflection`、`emotionLevel`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 47：推荐训练卡 `pages/training-card/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`1794ca65afaf455646f246c51e080057d524a32b29f5b3c704714325303548a0`
- 核对文件：`apps/miniprogram/pages/training-card/index.wxml`、`apps/miniprogram/pages/training-card/index.wxss`、`apps/miniprogram/pages/training-card/index.js`、`apps/miniprogram/pages/training-card/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/home/index`、`pages/thermometer/index`、`pages/training/index`、`pages/training-history/index`、`pages/personalized-plan/index`、`pages/therapeutic-assessment-action-followup/index`、`pages/feedback-result/index`、`pages/assessment-result/index`、`pages/hot-topics/index`
- 页面组件：`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：今天先练这一小步、每次选一张卡就可以。重点不是做完整，而是多一个能暂停、观察和回应的机会。、张即可、这次推荐依据、先看第一张；不合适时，再从下面两张里换一张。、今天的小目标、适合、节奏、完成、可以这样说、这些情况先停下来

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 15 | 这次推荐依据 | `bindaction` | `retryLoadCards` | — |
| 42 | — | `bindtap` | `toggleCardDetails` | {'id': '{{item.id}}'} |
| 56 | — | `bindtap` | `choosePractice` | {'id': '{{item.id}}', 'title': '{{item.title}}'} |
| 57 | — | `bindselect` | `submitTrainingFeedback` | {'id': '{{item.id}}'} |
| 68 | — | `bindaction` | `goDiary` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 61 | `listCards` | `GET` | `/api/cards` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 61 | `recommendCards` | `GET` | `/api/cards/recommend` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 152 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/task-detail/index?card_id=:dynamic`（js:127）、`navigateTo` → `/pages/diary-form/index`（js:142）
- 本地存储：`setStorageSync` `safehome:selectedTrainingCard`（JS:125）、`getStorageSync` `auth_user`（JS:369）、`removeStorageSync` `auth_token`（JS:393）、`removeStorageSync` `auth_user`（JS:394）、`getStorageSync` `auth_token`（JS:416）、`setStorageSync` `auth_token`（JS:636）、`setStorageSync` `auth_user`（JS:637）、`removeStorageSync` `safehome_anonymous_user_id`（JS:638）、`setStorageSync` `auth_token`（JS:684）、`setStorageSync` `auth_user`（JS:685）、`setStorageSync` `auth_token`（JS:700）、`setStorageSync` `auth_user`（JS:701）、`removeStorageSync` `safehome_anonymous_user_id`（JS:702）、`setStorageSync` `auth_token`（JS:717）、`setStorageSync` `auth_user`（JS:718）、`removeStorageSync` `safehome_anonymous_user_id`（JS:719）、`setStorageSync` `auth_token`（JS:742）、`setStorageSync` `auth_user`（JS:743）、`removeStorageSync` `safehome_anonymous_user_id`（JS:744）、`removeStorageSync` `auth_token`（JS:751）、`removeStorageSync` `auth_user`（JS:752）、`getStorageSync` `STORAGE_KEY`（JS:2095）、`setStorageSync` `STORAGE_KEY`（JS:2101）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2137）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2164）
- WXML 数据绑定：`loading`、`errorMessage`、`errorDetail`、`tagsText`、`cards`、`item`、`expandedCardId`、`feedbackEvaluationSaving`、`true`
- 条件状态：`loading`、`errorMessage`、`tagsText`、`item`、`cards`
- `setData` 状态：`tagsText`、`diaryId`、`tags`、`cardIds`、`loading`、`errorMessage`、`errorDetail`、`practiceMessage`、`cards`、`index`、`expandedCardId`、`feedbackEvaluationSaving`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 48：记录尝试 `pages/checkin/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`a347071a89e245e66ad0c2de1cb5a1fa2844080c760ff4b648dc869be12468e7`
- 核对文件：`apps/miniprogram/pages/checkin/index.wxml`、`apps/miniprogram/pages/checkin/index.wxss`、`apps/miniprogram/pages/checkin/index.js`、`apps/miniprogram/pages/checkin/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/task-detail/index`
- 页面组件：—
- 主要可见内容：第四步、记录一次尝试、练完后简单复盘一下，帮助你观察练习前后的变化。、这是一次轻复盘、只记录你有没有试着练一次，以及练习前后感受有没有一点变化。隔几天再练也可以，不需要评价自己做得好不好。、本次练习、训练卡：、关联记录：、练习前情绪强度： / 10、练习后情绪强度： / 10、这次练习对你有帮助吗？、如果暂时不想完成，可以写一个原因（可选）、练习复盘、可以围绕这三个问题写：、网络响应较慢；草稿仍在本机，请不要重复点击。、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 25 | — | `bindchange` | `onEmotionBeforeChange` | — |
| 30 | — | `bindchange` | `onEmotionAfterChange` | — |
| 36 | — | `bindtap` | `chooseHelpfulness` | {'value': '{{item.value}}'} |
| 50 | — | `bindinput` | `onSkipReasonInput` | — |
| 59 | — | `bindinput` | `onReflectionInput` | — |
| 73 | — | `bindtap` | `submitCheckin` | — |
| 77 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 111 | `createCheckin` | `POST` | `/api/checkins` | `backend/app.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/checkins.py`、`backend/routes/general_growth.py`、`backend/routes/profile.py`、`backend/routes/research_workspace.py`、`backend/routes/training_plan.py` |

#### 路由、本地状态与页面状态

- 下游路由：`reLaunch` → `/pages/home/index`（js:141）、`navigateTo` → `/pages/login/index:dynamic`（js:2167）
- 本地存储：`getStorageSync` `safehome:selectedTrainingCard`（JS:41）、`getStorageSync` `auth_user`（JS:335）、`removeStorageSync` `auth_token`（JS:359）、`removeStorageSync` `auth_user`（JS:360）、`getStorageSync` `auth_token`（JS:382）、`setStorageSync` `auth_token`（JS:602）、`setStorageSync` `auth_user`（JS:603）、`removeStorageSync` `safehome_anonymous_user_id`（JS:604）、`setStorageSync` `auth_token`（JS:650）、`setStorageSync` `auth_user`（JS:651）、`setStorageSync` `auth_token`（JS:666）、`setStorageSync` `auth_user`（JS:667）、`removeStorageSync` `safehome_anonymous_user_id`（JS:668）、`setStorageSync` `auth_token`（JS:683）、`setStorageSync` `auth_user`（JS:684）、`removeStorageSync` `safehome_anonymous_user_id`（JS:685）、`setStorageSync` `auth_token`（JS:708）、`setStorageSync` `auth_user`（JS:709）、`removeStorageSync` `safehome_anonymous_user_id`（JS:710）、`removeStorageSync` `auth_token`（JS:717）、`removeStorageSync` `auth_user`（JS:718）、`getStorageSync` `STORAGE_KEY`（JS:2061）、`setStorageSync` `STORAGE_KEY`（JS:2067）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2103）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2130）、`getStorageSync` `auth_token`（JS:2143）、`getStorageSync` `auth_user`（JS:2147）、`removeStorageSync` `auth_token`（JS:2173）、`removeStorageSync` `auth_user`（JS:2174）、`getStorageSync` `storageKey`（JS:2216）、`setStorageSync` `storageKey`（JS:2238）、`removeStorageSync` `storageKey`（JS:2268）
- WXML 数据绑定：`cardTitle`、`cardId`、`diaryId`、`emotionBefore`、`emotionAfter`、`helpfulnessOptions`、`helpfulnessRating`、`item`、`skipReason`、`reflectionPrompts`、`reflection`、`successMessage`、`errorMessage`、`draftRestored`、`saveStatus`、`slowSubmitting`、`submitting`、`submitted`
- 条件状态：`cardId`、`diaryId`、`successMessage`、`errorMessage`、`slowSubmitting`
- `setData` 状态：`sourceRecommendationId`、`cardId`、`diaryId`、`cardTitle`、`saveStatus`、`emotionBefore`、`successMessage`、`errorMessage`、`submitting`、`slowSubmitting`、`submitted`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 49：本周复盘 `pages/weekly-report/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`c1bd944d2460b79cc7b89308a5712813c453e13c95116c9b1d8c16cf2cf6b950`
- 核对文件：`apps/miniprogram/pages/weekly-report/index.wxml`、`apps/miniprogram/pages/weekly-report/index.wxss`、`apps/miniprogram/pages/weekly-report/index.js`、`apps/miniprogram/pages/weekly-report/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`、`pages/profile/index`
- 页面组件：—
- 主要可见内容：本周复盘、看看这一周的小变化、这不是评分，也不是判断。只是把记录和练习整理出来，帮你找到下周可以继续的一小步。、正在整理本周复盘、请稍等一下。、周报暂时没有加载成功、重新加载、过程复盘说明、周报是过程复盘，不是成绩单。这里不评价家长或孩子，只整理本周记录中的场景、情绪和练习情况。、阶段性画像线索、有内容需要人工关注，请优先等待或提交人工支持。、本周小变化、至、类常见场景、类常见情绪、条互动线索、练习尝试、测评记录、温度记录、本周测评记录、只整理你完成过的测评，不做固定判断、本周还没有测评记录。、推荐训练：、情绪温度趋势

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 19 | 重新加载 | `bindtap` | `refreshReport` | — |
| 171 | 刷新复盘 | `bindtap` | `refreshReport` | — |
| 172 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 86 | `getWeeklyReport` | `GET` | `/api/weekly-report` | `backend/models.py`、`backend/routes/admin.py`、`backend/routes/general_growth.py`、`backend/routes/reports.py`、`backend/scripts/generate_task33_ux_registry.py`、`backend/scripts/verify_privacy_restore.py`、`backend/services/data_claim_service.py`、`backend/services/participant_action_planner.py` |

#### 路由、本地状态与页面状态

- 下游路由：`reLaunch` → `/pages/home/index`（js:142）、`navigateTo` → `/pages/login/index:dynamic`（js:2168）
- 本地存储：`getStorageSync` `auth_user`（JS:336）、`removeStorageSync` `auth_token`（JS:360）、`removeStorageSync` `auth_user`（JS:361）、`getStorageSync` `auth_token`（JS:383）、`setStorageSync` `auth_token`（JS:603）、`setStorageSync` `auth_user`（JS:604）、`removeStorageSync` `safehome_anonymous_user_id`（JS:605）、`setStorageSync` `auth_token`（JS:651）、`setStorageSync` `auth_user`（JS:652）、`setStorageSync` `auth_token`（JS:667）、`setStorageSync` `auth_user`（JS:668）、`removeStorageSync` `safehome_anonymous_user_id`（JS:669）、`setStorageSync` `auth_token`（JS:684）、`setStorageSync` `auth_user`（JS:685）、`removeStorageSync` `safehome_anonymous_user_id`（JS:686）、`setStorageSync` `auth_token`（JS:709）、`setStorageSync` `auth_user`（JS:710）、`removeStorageSync` `safehome_anonymous_user_id`（JS:711）、`removeStorageSync` `auth_token`（JS:718）、`removeStorageSync` `auth_user`（JS:719）、`getStorageSync` `STORAGE_KEY`（JS:2062）、`setStorageSync` `STORAGE_KEY`（JS:2068）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2104）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2131）、`getStorageSync` `auth_token`（JS:2144）、`getStorageSync` `auth_user`（JS:2148）、`removeStorageSync` `auth_token`（JS:2174）、`removeStorageSync` `auth_user`（JS:2175）
- WXML 数据绑定：`loading`、`errorMessage`、`report`、`profileTrendNamesText`、`frequentScenes`、`frequentEmotions`、`commonPatterns`、`completedCardsText`、`assessmentNamesText`、`dimensionGroups`、`group`、`item`、`recommendedCardsText`、`thermometerDetailText`、`trainingEffectivenessText`
- 条件状态：`loading`、`errorMessage`、`profileTrendNamesText`、`report`、`assessmentNamesText`、`dimensionGroups`、`recommendedCardsText`、`frequentScenes`、`frequentEmotions`、`commonPatterns`
- `setData` 状态：`loading`、`errorMessage`、`frequentScenes`、`frequentEmotions`、`commonPatterns`、`completedCardsText`、`profileTrendNamesText`、`assessmentNamesText`、`dimensionGroups`、`recommendedCardsText`、`thermometerDetailText`、`trainingEffectivenessText`、`report`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 50：人工督导入口 `pages/supervision/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`49205bdcb9665fc560ff518b43f164f59b91f79bfa455621c3b3e8c5d8c5ea44`
- 核对文件：`apps/miniprogram/pages/supervision/index.wxml`、`apps/miniprogram/pages/supervision/index.wxss`、`apps/miniprogram/pages/supervision/index.js`、`apps/miniprogram/pages/supervision/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/home/index`、`pages/profile/index`、`pages/feedback-result/index`
- 页面组件：—
- 主要可见内容：人工补充反馈、请老师补充看看、如果这次记录让你有些拿不准，可以提交给老师，补充理解和练习建议。、先确认边界、人工反馈可能需要等待，适合补充理解一条记录，不适合处理紧急安全风险。、如果你或孩子正在经历自伤、自杀、暴力、失控或其他安全风险，请先联系身边可信赖的人、当地紧急服务或线下专业机构。、选择想请老师一起看的记录、可选一条自己的情绪日记或测一测记录；不选择也可以提交。、想请老师补充看的内容、可选联系方式、可选风险提示、网络响应较慢；草稿仍在本机，请不要重复点击。、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 21 | — | `bindtap` | `selectSource` | {'type': '{{item.type}}', 'id': '{{item.id}}'} |
| 40 | — | `bindinput` | `onTextInput` | {'key': 'message'} |
| 51 | — | `bindinput` | `onTextInput` | {'key': 'contact'} |
| 62 | — | `bindinput` | `onTextInput` | {'key': 'riskHint'} |
| 82 | — | `bindtap` | `submitSupervision` | — |
| 86 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 59 | `listDiaries` | `GET` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/auth_utils.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py` |
| 60 | `listAssessmentResults` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/auth_utils.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py` |
| 125 | `createSupervision` | `POST` | `/api/supervision` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/auth_utils.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py` |

#### 路由、本地状态与页面状态

- 下游路由：`reLaunch` → `/pages/home/index`（js:157）、`navigateTo` → `/pages/login/index:dynamic`（js:2183）
- 本地存储：`getStorageSync` `auth_user`（JS:351）、`removeStorageSync` `auth_token`（JS:375）、`removeStorageSync` `auth_user`（JS:376）、`getStorageSync` `auth_token`（JS:398）、`setStorageSync` `auth_token`（JS:618）、`setStorageSync` `auth_user`（JS:619）、`removeStorageSync` `safehome_anonymous_user_id`（JS:620）、`setStorageSync` `auth_token`（JS:666）、`setStorageSync` `auth_user`（JS:667）、`setStorageSync` `auth_token`（JS:682）、`setStorageSync` `auth_user`（JS:683）、`removeStorageSync` `safehome_anonymous_user_id`（JS:684）、`setStorageSync` `auth_token`（JS:699）、`setStorageSync` `auth_user`（JS:700）、`removeStorageSync` `safehome_anonymous_user_id`（JS:701）、`setStorageSync` `auth_token`（JS:724）、`setStorageSync` `auth_user`（JS:725）、`removeStorageSync` `safehome_anonymous_user_id`（JS:726）、`removeStorageSync` `auth_token`（JS:733）、`removeStorageSync` `auth_user`（JS:734）、`getStorageSync` `STORAGE_KEY`（JS:2077）、`setStorageSync` `STORAGE_KEY`（JS:2083）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2119）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2146）、`getStorageSync` `auth_token`（JS:2159）、`getStorageSync` `auth_user`（JS:2163）、`removeStorageSync` `auth_token`（JS:2189）、`removeStorageSync` `auth_user`（JS:2190）、`getStorageSync` `storageKey`（JS:2232）、`setStorageSync` `storageKey`（JS:2254）、`removeStorageSync` `storageKey`（JS:2284）
- WXML 数据绑定：`sourceOptions`、`item`、`message`、`contact`、`riskHint`、`successMessage`、`errorMessage`、`draftRestored`、`saveStatus`、`slowSubmitting`、`submitting`
- 条件状态：`successMessage`、`errorMessage`、`slowSubmitting`
- `setData` 状态：`diaryId`、`saveStatus`、`draftRestored`、`sourceOptions`、`selected`、`loadingSources`、`selectedSource`、`successMessage`、`errorMessage`、`submitting`、`slowSubmitting`、`message`、`contact`、`riskHint`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 51：云托管诊断 `pages/debug/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`97923436330e8915dc200ffb43cd71076254846d53debec19419e7ca6efbcc94`
- 核对文件：`apps/miniprogram/pages/debug/index.wxml`、`apps/miniprogram/pages/debug/index.wxss`、`apps/miniprogram/pages/debug/index.js`、`apps/miniprogram/pages/debug/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：—
- 页面组件：—
- 主要可见内容：云托管诊断、当前配置、切换本地 5000、切回云托管、测试 healthz、测试 assessments、测试 risk/check、测试 profile、最近一次错误

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 17 | 切换本地 5000 | `bindtap` | `useLocalBackend` | — |
| 18 | 切回云托管 | `bindtap` | `useCloudBackend` | — |
| 19 | 测试 healthz | `bindtap` | `testHealthz` | — |
| 20 | 测试 assessments | `bindtap` | `testAssessments` | — |
| 21 | 测试 risk/check | `bindtap` | `testRiskCheck` | — |
| 22 | 测试 profile | `bindtap` | `testProfile` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 38 | `getDebugConfig` | `GET` | — | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 67 | `healthz` | `GET` | `/healthz` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 104 | `listAssessments` | `GET` | `/api/assessments` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 109 | `checkRisk` | `POST` | `/api/risk/check` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 118 | `createProfile` | `POST` | `/api/profile` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `auth_user`（JS:321）、`removeStorageSync` `auth_token`（JS:345）、`removeStorageSync` `auth_user`（JS:346）、`getStorageSync` `auth_token`（JS:368）、`setStorageSync` `auth_token`（JS:588）、`setStorageSync` `auth_user`（JS:589）、`removeStorageSync` `safehome_anonymous_user_id`（JS:590）、`setStorageSync` `auth_token`（JS:636）、`setStorageSync` `auth_user`（JS:637）、`setStorageSync` `auth_token`（JS:652）、`setStorageSync` `auth_user`（JS:653）、`removeStorageSync` `safehome_anonymous_user_id`（JS:654）、`setStorageSync` `auth_token`（JS:669）、`setStorageSync` `auth_user`（JS:670）、`removeStorageSync` `safehome_anonymous_user_id`（JS:671）、`setStorageSync` `auth_token`（JS:694）、`setStorageSync` `auth_user`（JS:695）、`removeStorageSync` `safehome_anonymous_user_id`（JS:696）、`removeStorageSync` `auth_token`（JS:703）、`removeStorageSync` `auth_user`（JS:704）、`getStorageSync` `STORAGE_KEY`（JS:2047）、`setStorageSync` `STORAGE_KEY`（JS:2053）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2089）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2116）
- WXML 数据绑定：`config`、`status`、`resultTitle`、`resultText`、`lastError`
- 条件状态：`lastError`
- `setData` 状态：`config`、`status`、`resultTitle`、`resultText`、`lastError`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 52：联调测试 `pages/integration-test/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`805d2144f9fc0ed2849b3f205c77c31adfce127a4f330c539df2df36609d55b1`
- 核对文件：`apps/miniprogram/pages/integration-test/index.wxml`、`apps/miniprogram/pages/integration-test/index.wxss`、`apps/miniprogram/pages/integration-test/index.js`、`apps/miniprogram/pages/integration-test/index.json`、`apps/miniprogram/services/api.js`、`apps/miniprogram/services/userIdentity.js`、`apps/miniprogram/services/cloudConfig.js`
- 上游页面：`pages/home/index`、`pages/assessment/index`
- 页面组件：—
- 主要可见内容：最小联调测试、只验证三步数据流：创建情绪事件记录、生成即时反馈、获取训练卡推荐。、情绪事件记录、即时反馈、标签：、推荐训练卡

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 13 | — | `bindtap` | `runSmokeTest` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 7 | `getDebugConfig` | `GET` | — | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 33 | `healthz` | `GET` | `/healthz` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 39 | `createDiary` | `POST` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 53 | `generateFeedback` | `POST` | `/api/feedback/generate` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 60 | `recommendCards` | `GET` | `/api/cards/recommend` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |
| 68 | `getDebugConfig` | `GET` | — | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `auth_user`（JS:269）、`removeStorageSync` `auth_token`（JS:293）、`removeStorageSync` `auth_user`（JS:294）、`getStorageSync` `auth_token`（JS:316）、`setStorageSync` `auth_token`（JS:536）、`setStorageSync` `auth_user`（JS:537）、`removeStorageSync` `safehome_anonymous_user_id`（JS:538）、`setStorageSync` `auth_token`（JS:584）、`setStorageSync` `auth_user`（JS:585）、`setStorageSync` `auth_token`（JS:600）、`setStorageSync` `auth_user`（JS:601）、`removeStorageSync` `safehome_anonymous_user_id`（JS:602）、`setStorageSync` `auth_token`（JS:617）、`setStorageSync` `auth_user`（JS:618）、`removeStorageSync` `safehome_anonymous_user_id`（JS:619）、`setStorageSync` `auth_token`（JS:642）、`setStorageSync` `auth_user`（JS:643）、`removeStorageSync` `safehome_anonymous_user_id`（JS:644）、`removeStorageSync` `auth_token`（JS:651）、`removeStorageSync` `auth_user`（JS:652）、`getStorageSync` `STORAGE_KEY`（JS:1995）、`setStorageSync` `STORAGE_KEY`（JS:2001）、`getStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2037）、`setStorageSync` `CLOUD_CONFIG_STORAGE_KEY`（JS:2064）
- WXML 数据绑定：`diagnostics`、`status`、`message`、`diary`、`feedback`、`cards`、`item`
- 条件状态：`diary`、`feedback`、`cards`
- `setData` 状态：`status`、`message`、`diary`、`feedback`、`cards`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

<!-- UI_PRODUCT_AUTO_FACTS:END -->
