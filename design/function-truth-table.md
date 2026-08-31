# 小程序功能真值表

更新时间：2026-08-30

状态：`mandatory_before_imagegen_figma_and_frontend`

本文件记录每个小程序页面的真实功能，是 UI 审查、ImageGen、Figma 和前端视觉实现的共同输入。前端用于承载现有业务与后端能力，视觉不得新增、替换或曲解功能。

## 使用规则

每个页面严格执行：

1. 读取目标页 WXML、WXSS、JS、JSON；
2. 读取页面使用的组件、上游入口和下游页面；
3. 核对前端 API 封装、共享 endpoint、后端 route/service 和本地存储；
4. 写出“页面元素 → 事件 → 路由/API → 后端或本地能力 → 用户任务”；
5. 标记现有文案、点击结果和后端能力之间的差异；
6. 应用用户已冻结的方案 A 与全局 UI 规则；只有出现重大产品歧义时才暂停确认，否则由当前执行方形成页面冻结版后调用 ImageGen；
7. 网页版 GPT 进入 Figma 前重读本页真值表，并把采用的 ImageGen、Figma node 和 `UIproduct` commit 作为远端证据返回；
8. 修改前端前再次对照当前代码，发现漂移先更新真值表；涉及产品语义变化时再向用户确认；
9. Codex 收到远端链接后按本表审查。结论不是“可行”时，Codex 重新核对或生成 ImageGen、修正 Figma，再修正 `UIproduct` 代码并重跑验证。

如果目标设计需要当前后端不存在的读取接口、字段或状态，应停止该部分，记录能力缺口并等待授权。不得用重新生成数据、静态假数据或相似页面冒充真实功能。

## 页面登记

页面清单以 `apps/miniprogram/app.json` 为准。当前 53 个页面已全部登记；严格一次只核对一个页面。

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

## 2026-08-30 小程序可见硬编码文本全量审查

- 已审查 `app.json` 登记的全部 53 个小程序页面及其直接使用组件；本轮不修改网页端。
- 删除标准：装饰性口号、重复等待语、暴露内部实现的说明、与标题或操作重复的空状态解释，以及删文案后留下的空容器。
- 保留标准：动态状态、可执行动作、操作后果、数据来源、研究权限与隐私阈值、安全提示、非诊断边界和必要输入示例。
- 本轮收敛页面：`home`、`messages`、`support-assistant`、`thermometer`、`training`、`training-history`、`program-list`、`relationship-pilot`、`relationship-growth`、`relationship-narrative`、`therapeutic-assessment-action-followup`、`therapeutic-assessment-quality`、`course`、`profile`、`settings-detail`、`diary-history`、`feedback-result`、`hot-topics`、`task-detail`、`checkin`、`weekly-report`。
- 同步收敛组件：`therapeutic-flow-step` 只删除重复的草稿恢复等待说明，首次进入时的使用边界保持不变。
- 页面事件、路由、API、存储、数据结构及高风险处理均未改变；未命中的页面经逐页判断后保留原文。

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

## 05：支持性问答 `pages/support-assistant/index`

核对来源：

- `apps/miniprogram/pages/support-assistant/index.wxml`
- `apps/miniprogram/pages/support-assistant/index.wxss`
- `apps/miniprogram/pages/support-assistant/index.js`
- `apps/miniprogram/pages/support-assistant/index.json`
- `apps/miniprogram/pages/profile/index.js`
- `apps/miniprogram/utils/authGuard.js`
- `apps/miniprogram/services/api.js`
- `content/ai_participant_use_case_policy.json`（只读）
- `content/ai_qa_governance.json`（只读）
- `backend/routes/ai_qa.py`（只读）
- `backend/services/ai_qa_service.py`（只读）

### 功能映射

| 页面区域 | 当前前端事件 | 数据或目标 | 真实用户任务 | 正式设计约束 |
|---|---|---|---|---|
| 登录门禁 | `onLoad` + `isLoggedIn` | 未登录 `redirectTo /pages/login/index?redirect=...` | 登录后使用个人化受控问答 | 不画游客可直接发送状态，不新增本页登录表单 |
| 能力状态 | `loadStatus` | `GET /api/ai-qa/config`；读取 `participant_enabled` 与参与者边界 | 确认问答当前是否开放 | Loading、读取 Error、Disabled 必须独立；关闭时不得出现输入或发送 |
| 使用边界与同意 | `enableConsent` | `POST /api/consent`；`ai_assistance`、版本 `2026.07-consent-v2`、`agreed=true` | 阅读边界并记录本次同意 | 未同意时同意是唯一主行动；不伪造撤回、拒绝或历史同意读取能力 |
| 问题输入 | `onQuestionInput` | 本地 `question`，最多 1000 字 | 写下一个具体问题或想法 | 保留字数、禁用和原占位语义；不新增语音、图片、推荐问题 |
| 会话创建 | `ensureSession` | `POST /api/ai-qa/sessions`；固定 `participant_support_navigation` | 为本次打开建立受控问答会话 | 不展示跨会话记忆、历史会话或其他用例选择 |
| 发送与回答 | `sendQuestion` | `POST /api/ai-qa/sessions/:sessionId/messages`；读取 `message.content` 与 `citations` | 获得基于已审核内容、非诊断的支持性整理 | 保留不足内容兜底与发送错误；不包装为实时咨询或确定结论 |
| 引用 | 无独立事件 | `answer.citations[].title/version_id` | 了解回答参考了哪些已审核内容 | 只展示真实返回标题，不新增可点击来源或外链 |

### 页面状态真值

- `Loading`：正在读取问答开关。
- `Config Error / Network Failure`：配置读取失败，原动作只允许重新读取。
- `Disabled`：服务当前未开放，只展示现有替代能力说明，无按钮。
- `Consent Pending`：开放但未同意，输入和发送不可用。
- `Ready`：同意完成，可输入；空问题时发送禁用。
- `Sending`：同意、输入和发送均受 `sending` 保护。
- `Conversation`：只展示本次打开后本地追加的用户问题、助手回答和真实引用。
- `Inline Error`：同意或发送失败；保留问题文本，允许按原按钮重试。
- `Long Content`：问题最多 1000 字；回答和引用数量由真实返回决定，自然滚动。

### 禁止的视觉推断

- 不新增实时在线、输入中、已读回执、头像、人工客服、紧急处置或自动诊断含义。
- 不新增历史会话、删除、复制、点赞、重试单条回答、引用跳转或跨会话记忆。
- 不将治理文件的拟议服务名、生产状态或外部模型包装为已批准上线事实。
- 本页只允许修改 UI 前端文件；后端、API、数据库、content、shared、认证和开关均禁止修改。
- `coreEntries`、`hotTopics` 以及若干 handler 当前没有对应 WXML 展示，不能因为 JS 中存在就自动加入首页。
- `journey-action-card` 是真实动态主行动组件，应保留状态和恢复能力；视觉可以重做，语义不能改。

### 已确认产品目标与实施边界

1. 用户已确认保留现有接口。支持性反馈继续采用“先记录事件，再生成对应反馈”的现有链路，不新增读取历史反馈接口，不修改后端。
2. 最近记录应进入真实记录页。当前没有该页面；后续单独设计一个前端记录页并复用 `GET /api/diaries`，不新增后端接口，但必须先完成该页的功能真值表、需求冻结、ImageGen 和 Figma。

首页状态更新为 `visual_concept_ready_with_frontend_dependency`：可以重新生成严格按功能真值表约束的 ImageGen 概念稿；用户确认视觉方案前不进入 Figma、不修改前端。“最近记录”真实跳转的前端页面依赖需在实现前按单页流程补齐。

## 首页依赖：情绪记录 `pages/diary-history/index`（实现前真值）

状态：`requirements_frozen_before_imagegen`。该页面当前尚未加入 `app.json`，必须先完成 ImageGen 与 Figma 审查，再创建前端文件。

核对来源：

- `apps/miniprogram/pages/home/index.js` 与 `index.wxml`；
- `apps/miniprogram/pages/diary-form/index.*`；
- `apps/miniprogram/pages/assessment-history/index.*`；
- `apps/miniprogram/services/api.js` 的 `listDiaries`；
- `backend/routes/diaries.py` 的 `GET /api/diaries`（只读核对）。

| 页面元素 | 事件处理 | 路由/API/状态 | 真实用户任务 | 正式设计约束 |
|---|---|---|---|---|
| 页面进入 | `onLoad`、`onShow` | `requireLogin`；`api.listDiaries({limit: 50})` → `GET /api/diaries` | 登录后读取自己最近保存的情绪记录 | 只显示当前账号数据；未登录沿用认证守卫，不改认证体系 |
| 记录列表 | 无点击事件 | 返回项包含 `event_time`、`created_at`、`scene`、`event_description`、`parent_emotion`、`parent_emotion_intensity` 及可选补充字段 | 回看具体事件、当时感受和强度 | 使用真实字段；按接口返回顺序展示，不宣称按事件时间排序，不伪造分析结论 |
| 当前显示数量 | 无点击事件 | 仅使用本次 `items.length` | 知道当前页面加载了多少条 | 文案使用“当前显示”，不得称为全部记录或总数 |
| 记录一件事 | `startDiary` | `navigateTo('/pages/diary-form/index')` | 新建一条情绪事件记录 | 页面唯一主行动；不在列表页复制表单 |
| 重新加载 | `retry` | 重新调用 `listDiaries({limit: 50})` | 从加载失败或断网中恢复 | 错误必须给出恢复动作，不自动无限重试 |
| 返回 | 微信原生导航 | 返回首页或上游页面 | 继续原路径 | 不增加自定义返回栈或底部 tabBar |

接口边界：

- `GET /api/diaries` 当前只有 `limit` 与精确 `date=YYYY-MM-DD`，没有分页游标、详情、编辑、删除或总数。
- 本页 v1 固定读取最近 50 条；不新增筛选器、分页、“查看全部”、记录详情页、编辑或删除。
- 列表直接显示真实 `scene`、`event_description`、家长主要情绪与强度；可选字段为空时不显示，不用占位内容补齐。
- Default、Loading、Empty、Error、Network Failure、Long Content 必须设计；Selected/Disabled 不适用于只读列表，不伪造交互态。
- 文件分类：未来新增页面 WXML/WXSS/JSON 属 A；页面 JS 与首页跳转属 B，限于读取现有接口与导航；后端、数据库、API、`content`、`shared` 属 C，禁止修改。

## 消息列表 `pages/messages/index`（逐页人工冻结）

状态：`requirements_frozen_before_imagegen`。核对时间：2026-08-10。

核对来源：

- `apps/miniprogram/pages/messages/index.*`；
- `apps/miniprogram/components/page-state/index.*`、`status-pill/index.*`、`bottom-tip-card/index.*`；
- 上游 `pages/home/index`、`pages/growth-dashboard/index`、`pages/profile/index`；
- 下游 `pages/message-detail/index.*`；
- `apps/miniprogram/services/api.js` 的 `listMessages`；
- `backend/routes/messages.py` 与 `backend/services/message_service.py`（只读核对）。

| 页面元素 | 事件处理 | 路由/API/状态 | 真实用户任务 | 正式设计约束 |
|---|---|---|---|---|
| 页面进入/再次显示 | `onShow` → `loadMessages` | `GET /api/messages?page=1&page_size=50`，需要登录 | 读取当前账号最多 50 条消息 | 保留每次显示即刷新；不新增缓存、分页、筛选或排序开关 |
| 消息列表 | `openMessage` | `navigateTo('/pages/message-detail/index?id=:id')` | 打开一条消息查看完整内容；详情读取时自动标记已读 | 整行保持可点击；列表页不伪造聊天、回复、删除或批量已读 |
| 消息正文摘要 | 无独立事件 | `title`、`body`、`created_at`、`sender_role`、`delivery_version` | 快速判断消息内容、来源、时间和版本 | 使用接口原值；不改写为营销摘要，不隐藏版本号 |
| 未读/已读状态 | 无独立事件 | `is_unread` | 区分尚未打开与已查看消息 | 必须同时使用文字和视觉差异，不能只靠颜色；不增加“全部标为已读”按钮 |
| 撤回状态 | 仍可进入详情 | `is_withdrawn` | 知道研究者已撤回此前内容并忽略旧版本 | 列表固定显示撤回说明和“已撤回”；不继续展示已撤回正文，不伪造删除 |
| 加载状态 | 无事件 | `loading` | 等待消息读取 | 使用现有 `page-state`；无装饰性循环动效，reduced motion 保持静态可理解 |
| 空状态 | 无事件 | `messages.length === 0` | 确认当前没有消息 | 只说明后续人工补充会出现；不增加刷新、联系研究者或营销入口 |
| 错误恢复 | `handleStateAction` | 登录失效时进入登录页并保留 redirect；其他错误重新调用列表接口 | 恢复登录或重试网络请求 | 一个明确恢复动作；不得把权限错误伪装为空状态 |
| 诊断信息 | `copyDiagnostic` | 复制 `requestId` 与 `serviceVersion`，Toast 反馈结果 | 在服务异常时提供可交接诊断证据 | 仅错误状态展示；不得暴露 token、用户正文或其他敏感数据 |
| 底部边界说明 | 无事件 | 本地静态文案 | 理解消息不是紧急帮助渠道 | 保留“补充说明和支持提醒，不替代紧急帮助”的边界，不改成实时客服承诺 |

接口与产品边界：

- 本页唯一数据接口为现有 `GET /api/messages`；`unread_count` 已写入页面状态但当前不展示，本轮不新增未读统计标题。
- 当前列表不使用后端已有的 `read-all`、筛选和分页能力；视觉不得新增对应控件。
- 状态矩阵为 Default（含未读、已读、撤回、版本）、Loading、Empty、Error、LoginRequired、NetworkFailure、LongContent。Disabled/Selected 不适用于该只读列表，不伪造。
- 文件分类：目标页 WXML/WXSS 属 A；本页 JS 属 B 但本轮无需修改；组件、后端、数据库、API、`content`、`shared` 均不改。

## 消息详情 `pages/message-detail/index`（逐页人工冻结）

状态：`requirements_frozen_and_locally_implemented`。核对时间：2026-08-10。

核对来源：

- `apps/miniprogram/pages/message-detail/index.*`；
- `apps/miniprogram/components/feedback-rating/index.*`、`page-state/index.*`；
- 上游 `pages/messages/index`；
- 下游 `pages/relationship-report/index`、`pages/relationship-narrative/index`；
- `apps/miniprogram/services/api.js` 的 `getMessage`、`createFeedbackLedgerEntry`；
- `backend/routes/messages.py`、`backend/services/message_service.py`、`backend/routes/feedback_ledger.py`、`backend/services/feedback_ledger_service.py`（只读核对）。

| 页面元素 | 事件处理 | 路由/API/状态 | 真实用户任务 | 正式设计约束 |
|---|---|---|---|---|
| 页面进入 | `onLoad` → `loadMessage` | `GET /api/messages/:message_id`，需要登录；读取未读消息时后端自动标为已读 | 打开当前账号的一条完整消息 | 只显示接口真实字段；不得误写为列表接口，也不额外调用 `POST /read` |
| 消息标题与正文 | 无独立事件 | `message_type`、`title`、`body` | 阅读研究者补充或消息提醒 | 保留原文和换行，不改写为 AI 总结、诊断或行动处方 |
| 来源、时间与版本 | 无独立事件 | `sender_role`、`created_at`、`delivery_version` | 理解消息来源和当前版本 | 仅有 `sender_role` 时显示研究者来源；版本存在才显示，不伪造头像、在线状态或已读回执 |
| 撤回内容 | 无独立事件 | `is_withdrawn` 只替换正文为撤回说明 | 知道此前内容已撤回并忽略旧版本 | 撤回不等于删除；来源按钮和评价仍分别按自身条件判断，不擅自隐藏 |
| 查看关系探索报告 | `openSource` | 仅 `source_type=relationship_screening_report` 且有 `source_id` 时进入 `/pages/relationship-report/index?id=:source_id` | 查看该消息对应的真实关系探索报告 | 不为其他消息画报告入口，不伪造报告摘要 |
| 查看已确认探索手记 | `openSource` | 仅 `source_type=relationship_narrative` 且有 `source_id` 时进入 `/pages/relationship-narrative/index?id=:source_id` | 查看对应的已确认探索手记 | 不新增未确认手记、编辑或分享能力 |
| 反馈核对 | `submitFeedbackEvaluation` | 仅 `researcher_message`、`relationship_stage_feedback`、`supervision_feedback`、`relationship_report` 可评价；`POST /api/feedback-ledger`，`source_type=message` | 选择符合、部分符合、不符合或让我不舒服，以共同修订反馈 | 只保存现有四值；不新增星级、文字评论、点赞或诊断推断 |
| 不舒服反馈 | 同上 | `evaluation=uncomfortable` 后形成 `pending_review` / 人工复核信号 | 表达内容带来的不适并进入人工复核 | 明确“不据此推断风险或诊断”；不能包装为实时危机处置或自动风险识别 |
| 保存中与结果 | `feedbackEvaluationSaving`、`feedbackEvaluation` | 保存时禁用重复提交；成功 Toast 与页内状态可见，失败 Toast 保留 | 知道评价是否正在保存或已记录，并可再次调整 | 不伪造撤销、历史评价读取或离线成功；状态不能只靠颜色 |
| 错误恢复 | `handleStateAction` | 缺少 ID 时返回消息列表；有 ID 的加载错误重新调用详情接口 | 从参数错误、接口错误或弱网中恢复 | MissingId 与 LoadError / NetworkFailure 分开；不将权限或网络错误伪装为空消息 |
| 使用边界 | 无事件 | 本地静态说明 | 理解消息内容不处理紧急安全风险 | 保留现实支持提示；不新增紧急电话或聊天入口 |
| 返回消息列表 | `goMessages` | `wx.navigateBack()` | 返回原消息列表与原导航栈 | 不改成 `switchTab`、`redirectTo` 或新的消息首页 |

页面状态真值：

- Loading、MissingId、LoadError、NetworkFailure、Default、WithSource、Evaluable、Saving、Evaluated、Uncomfortable、Withdrawn、LongContent。
- Withdrawn 只改变正文；WithSource 与 Evaluable 是由独立字段决定的可组合状态。
- Disabled 只出现在反馈保存期间；本页没有 Empty、回复、聊天、删除、转发、收藏、复制、举报或紧急呼叫功能。

接口与工程边界：

- 详情接口的完整真值是 `GET /api/messages/:message_id`；自动证据中的 `/api/messages` 只是静态模板前缀，不能据此改变产品语义。
- 评价接口继续使用现有 `POST /api/feedback-ledger`；本轮不修改后端、数据库、API、shared、content、认证、消息已读逻辑或导航语义。
- 前端实现只调整 WXML/WXSS，并给共用 `feedback-rating` 增加默认关闭的 `editorial` 视觉属性；页面 JS 和业务事件保持原样。

## 紧急安全指引 `pages/emergency-guide/index`（逐页人工冻结）

状态：`requirements_frozen_before_imagegen`。核对时间：2026-08-11。

核对来源：

- `apps/miniprogram/pages/emergency-guide/index.*`；
- `apps/miniprogram/components/section-title/index.*`；
- 上游 `pages/profile/index`、`pages/feedback-result/index`、`pages/emergency-resources/index`；
- 下游 `pages/emergency-resources/index`、`pages/home/index`；
- `apps/miniprogram/app.json`、`app.wxss` 与 `shared/design/experience-tokens.json`；
- 当前页面无 API、后端、数据库、本地存储、登录或权限调用。

| 页面元素 | 事件处理 | 路由/API/状态 | 真实用户任务 | 正式设计约束 |
|---|---|---|---|---|
| 安全情境与标题 | 无事件 | 本地固定文案 | 在出现自伤、自杀、暴力、失控或其他安全风险时，立即知道现实帮助优先 | 信息直接、可扫读；不使用库存人物图、庆祝动效、诊断标签或恐吓式视觉 |
| 现在先做 | 无事件 | `supportSteps` 四项本地数组 | 依次离开危险物品或场景、联系可信赖的人、紧急时联系当地紧急服务或线下机构、涉及孩子时联系监护/学校/当地专业机构 | 四项顺序和原文保持；视觉优先级高于接地法，不新增拨号、定位、报警或自动转介 |
| 5-4-3-2-1 接地法 | 无事件 | `groundingSteps` 五项本地数组 | 在联系现实帮助的同时，用感官与慢呼吸稳定当下 | 明确“不替代专业帮助”；显示顺序应与 5→4→3→2→1 一致，不能继续用 1→5 的视觉编号造成冲突 |
| 重要边界 | 无事件 | 本地固定文案 | 理解小程序不能提供实时危机干预、医疗诊断或法律判断 | 保留完整边界，不包装为已连接专业人员、实时客服或风险评估结果 |
| 查看现实支持资源 | `openResources` | `navigateTo('/pages/emergency-resources/index')` | 查看身边可信赖的人、当地紧急服务、学校/社区和专业机构四类现实资源说明 | 全页唯一实心主行动，应在阅读长内容时持续容易找到；不显示虚构号码或机构 |
| 回到首页 | `goHome` | `reLaunch('/pages/home/index')` | 退出安全指引并回到首页根路由 | 保留 `reLaunch` 语义；降为次行动但保持 88rpx 可点击，不改成返回上一页 |

页面状态真值：

- 页面只由本地静态数组和路由驱动，无 Loading、Empty、Error、NetworkFailure、Disabled、Selected 或数据状态。
- 正式设计覆盖 Default、LongContent / SmallScreen，以及按钮 Pressed 与 ReducedMotion；不得为凑状态伪造加载、联网失败或热线不可用。
- 当前录屏文件在本机原路径已不可用，本页没有新的直接截图证据；按统一规则不阻断本地流程，真机视觉、读屏和大字体统一待全量验收。

冻结方案 A：

- 采用“安全行动清单”而非多层卡片：开放式标题，四项现实行动为主清单，接地法为次级 5→1 感官阶梯，边界使用细线与短段落。
- 使用象牙白、深墨、克制危险色提示和森林绿主行动；无插画、无图标装饰、无循环动效。
- 现实资源按钮固定在可达位置，回到首页为低强调次行动；只改变布局与视觉，不改变文案、数组、事件和路由。
- 目标页 WXML/WXSS/JSON 属 A；页面 JS 属 B 但本轮预计不改；后端、API、数据库、content、shared、认证和无关文件属 C/D，禁止修改。

## 三步开始 `pages/getting-started/index`（逐页代理冻结）

状态：`requirements_frozen_before_imagegen`。核对时间：2026-08-11。

核对来源：

- `apps/miniprogram/pages/getting-started/index.*`；
- 上游 `pages/home/index`；
- 下游 `pages/diary-form/index`、`pages/training/index`；
- `apps/miniprogram/app.json`、`app.wxss` 与 `shared/design/experience-tokens.json`；
- 当前页面无 API、后端、数据库、本地存储、登录或权限调用。

| 页面元素 | 事件处理 | 路由/API/状态 | 真实用户任务 | 正式设计约束 |
|---|---|---|---|---|
| 新手说明与页面标题 | 无事件 | 本地固定文案 | 理解此页用于把一次亲子压力事件拆成可练习的小步骤 | 不包装为课程、测评、诊断或已经完成的进度；首屏直接说明“从一件具体小事开始” |
| 情绪反射弧说明 | 无事件 | 固定正文与 `arcNodes` 七项数组 | 理解诱因、反应、觉察、接纳、转化、应对和结果是一条可观察链路 | 七项及顺序全部保留；只能做解释性图示，不绘制分数、风险等级、结果预测或可点击节点 |
| 为什么记录具体事件 | 无事件 | `eventReasons` 三项数组 | 理解具体记录有助于聚焦本次互动和找到下一小步 | 三条理由保留但并入“写一个片段”的阅读层级，避免独立卡片重复说明 |
| 三步练习 | 无事件 | `exerciseSteps` 三项数组 | 依次写片段、标位置、做动作 | 三步是实际顺序，可使用 01–03 编号；不增加表单、勾选、完成状态、计时或自动推荐 |
| 反馈—记录—训练提示 | 无事件 | WXML 固定说明 | 理解记录、查看反馈线索和训练动作之间的关系 | 可压缩成一行路径说明；不画成可点击进度条或后端已完成状态 |
| 使用边界 | 无事件 | `boundaries` 三项数组 | 理解非诊断、高风险优先现实支持、一次一步 | 三条边界完整保留并集中出现一次；不在各步骤重复，不缩成小于 24rpx |
| 记录一次 | `startDiary` | `navigateTo('/pages/diary-form/index')` | 进入真实情绪事件记录表单 | 全页唯一实心主行动，保持原事件和 `navigateTo` 语义 |
| 去训练中心 | `openTraining` | `switchTab('/pages/training/index')` | 前往真实训练 Tab | 作为次行动，保持 `switchTab` 语义；不伪装为本页直接开始训练 |

页面状态真值：

- 页面仅由静态数组和路由驱动，无 Loading、Empty、Error、NetworkFailure、Disabled、Selected 或远端数据状态。
- 正式设计覆盖 Default、LongContent / SmallScreen、按钮 Pressed 与 ReducedMotion；不得为凑状态伪造联网、保存或完成回执。
- 用户最终视觉和真机验收统一后置；逐页本地阶段由 ImageGen、Figma、开发者工具或代码映射、Loop 1–4 与 Harness 自审。

冻结方案 A：

- 采用“展开的三步练习页”：开放标题、真实 01–03 顺序、七段反射弧为一条可扫读的观察链，不使用卡片墙或粗侧线。
- Step 01 承载三条“为什么具体记录”；Step 02 承载七段观察链；Step 03 指向训练动作。重复的动作提示压缩为一行路径说明。
- 主行动固定为“记录一次”，次行动为“去训练中心”；边界集中一次显示。可见文字不小于 24rpx，正文不小于 28rpx。
- 页面 WXML/WXSS/JSON 属 A；页面 JS、数组、事件和路由属 B 且本轮禁止修改；后端、API、数据库、content、shared 与无关文件属 C/D，禁止修改。

<!-- UI_PRODUCT_AUTO_FACTS:BEGIN -->

## 全页面自动代码证据（UIproduct Harness）

生成时间：`2026-08-12T23:19:06+08:00`
分支：`UIproduct`
页面数：`53`

本节由 `scripts/ui_product_loop.py audit-truth` 从当前代码生成，覆盖 WXML 事件、JS 处理器、API 客户端方法、接口模板、路由、本地存储、页面状态、组件和上下游入口。自动证据是逐页人工冻结的底稿；任何未解析项都会阻断 ImageGen。

### 01：安心陪伴 `pages/home/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`caa26cbb0a24ca28c13df3c723cd9c61eea57b05fc578f466b58d872475b8bce`
- 核对文件：`apps/miniprogram/pages/home/index.wxml`、`apps/miniprogram/pages/home/index.wxss`、`apps/miniprogram/pages/home/index.js`、`apps/miniprogram/pages/home/index.json`
- 上游页面：`pages/login/index`、`pages/register/index`、`pages/messages/index`、`pages/emergency-guide/index`、`pages/hot-topics/index`、`pages/checkin/index`、`pages/weekly-report/index`、`pages/supervision/index`
- 页面组件：`journey-action-card` → `/components/journey-action-card/index`、`entry-row` → `/components/entry-row/index`、`dual-entry` → `/components/dual-entry/index`、`section-heading` → `/components/section-heading/index`
- 主要可见内容：安心陪伴、进入联调测试页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 16 | <journey-action-card class="today-step-en | `bindaction` | `openThermometer` | — |
| 18 | <journey-action-card class="today-step-entry" loading=" " error-message=" " stat | `bindaction` | `openCoreEntry` | — |
| 20 | {{todayJourney ? todayJourney.actionAriaLabel :  | `bindaction` | `openTodayAction` | — |
| 20 | {{todayJourney ? todayJourney.actionAriaLabel :  | `bindretry` | `retryTodayJourney` | — |
| 35 | <entry-row icon="training" title="训练中心" subtitle="查看训练计划与练习" action-ke | `bindaction` | `openGettingStarted` | — |
| 39 | — | `bindaction` | `openCoreEntry` | — |
| 40 | — | `bindaction` | `openCoreEntry` | — |
| 41 | — | `bindaction` | `openCoreEntry` | — |
| 52 | — | `bindaction` | `retryHomeData` | — |
| 60 | — | `bindaction` | `openDiaryHistory` | — |
| 61 | — | `bindaction` | `startDiary` | — |
| 72 | <entry-row wx:else class="summary-entry" | `bindaction` | `openWeeklyReport` | — |
| 73 | — | `bindaction` | `retryHomeData` | — |
| 81 | — | `bindaction` | `openWeeklyReport` | — |
| 85 | 进入联调测试页 | `bindtap` | `openIntegrationTest` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 9 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 199 | `listDiaries` | `GET` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 200 | `listDiaries` | `GET` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 201 | `getProfileStats` | `GET` | `/api/profile/stats` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 202 | `getEmotionThermometerDay` | `GET` | `/api/emotion-thermometer/day` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 203 | `getProgressSummary` | `GET` | `/api/progress-summary` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 257 | `getTodayJourney` | `GET` | `/api/journey/today` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/goal-setting/index`（js:247）、`navigateTo` → `/pages/diary-form/index`（js:248）、`navigateTo` → `/pages/diary-history/index`（js:249）、`navigateTo` → `/pages/thermometer/index`（js:250）、`navigateTo` → `/pages/weekly-report/index`（js:251）、`switchTab` → `/pages/training/index`（js:320）、`navigateTo` → `/pages/assessment/index`（js:321）、`navigateTo` → `/pages/messages/index`（js:325）、`navigateTo` → `/pages/integration-test/index`（js:326）、`navigateTo` → `/pages/getting-started/index`（js:327）、`switchTab` → `/pages/training/index`（js:332）、`navigateTo` → `/pages/getting-started/index`（js:333）、`switchTab` → `/pages/training/index`（js:339）、`navigateTo` → `/pages/diary-form/index`（js:342）、`navigateTo` → `/pages/supervision/index`（js:345）、`navigateTo` → `/pages/assessment/index`（js:346）、`navigateTo` → `/pages/training-card/index?tags=:dynamic`（js:350）、`navigateTo` → `/pages/hot-topics/index`（js:352）、`navigateTo` → `/pages/hot-topics/index?id=:dynamic`（js:355）
- 本地存储：`getStorageSync` `key`（JS:110）、`getStorageSync` `key`（JS:132）
- WXML 数据绑定：`unreadMessageCount`、`thermometerRecordCount`、`thermometerRecordReady`、`todayJourneyLoading`、`todayJourneyError`、`todayJourney`、`latestRecordError`、`latestRecord`、`progressSummary`、`progressSummaryError`、`showDevEntry`
- 条件状态：`unreadMessageCount`、`latestRecordReady`、`latestRecordError`、`latestRecord`、`progressSummaryReady`、`progressSummary`、`progressSummaryError`、`showDevEntry`
- `setData` 状态：`todayRecordCount`、`todayRecordCountReady`、`thermometerRecordReady`、`unreadMessageCount`、`latestRecordReady`、`latestRecordError`、`progressSummary`、`progressSummaryReady`、`progressSummaryError`、`latestRecord`、`time`、`trigger`、`status`、`thermometerRecordCount`、`todayJourneyLoading`、`todayJourneyError`、`todayJourney`、`primary_action`、`title`、`description`、`button_label`、`url`、`source_type`、`boundary_notice`、`estimated_minutes`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 02：登录 `pages/login/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`c9dc429506e6a81ab190a678de0d7dc7e51a8fd04c3cc2bbf232bdc8fb109986`
- 核对文件：`apps/miniprogram/pages/login/index.wxml`、`apps/miniprogram/pages/login/index.wxss`、`apps/miniprogram/pages/login/index.js`、`apps/miniprogram/pages/login/index.json`
- 上游页面：`pages/home/index`、`pages/register/index`、`pages/messages/index`、`pages/support-assistant/index`、`pages/profile/index`、`pages/settings-detail/index`
- 页面组件：—
- 主要可见内容：登录、首次登录，请先设置新密码、新密码至少 12 位，并包含三类字符。更新后临时密码和旧会话立即失效。、临时密码、新密码、再次输入新密码、更新密码并继续、快捷登录、微信一键登录、微信一键登录（暂不可用）、手机号快捷登录、手机号快捷登录（暂不可用）、手机号仅用于识别你的账号，系统只保存不可逆摘要，不保存完整号码。、或使用账号密码、用户名、密码、注册新账号

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 15 | — | `bindinput` | `onCurrentPasswordInput` | — |
| 19 | — | `bindinput` | `onNewPasswordInput` | — |
| 23 | — | `bindinput` | `onConfirmPasswordInput` | — |
| 27 | 更新密码并继续 | `bindtap` | `submitPasswordChange` | — |
| 34 | 微信一键登录 | `bindtap` | `submitWechatLogin` | — |
| 36 | 手机号快捷登录 | `bindgetphonenumber` | `handlePhoneLogin` | — |
| 51 | — | `bindinput` | `onUsernameInput` | — |
| 55 | — | `bindinput` | `onPasswordInput` | — |
| 59 | 登录 | `bindtap` | `submitLogin` | — |
| 60 | 注册新账号 | `bindtap` | `goRegister` | — |

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
- 本地存储：—
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
- 源码指纹：`49418f81da315cf2d62943624bb657be68b884d752dbd616c3e43f323029a3db`
- 核对文件：`apps/miniprogram/pages/register/index.wxml`、`apps/miniprogram/pages/register/index.wxss`、`apps/miniprogram/pages/register/index.js`、`apps/miniprogram/pages/register/index.json`
- 上游页面：`pages/login/index`、`pages/messages/index`、`pages/profile/index`
- 页面组件：—
- 主要可见内容：创建账号、账号信息、用户名、至少 3 个字符、密码、至少 8 个字符、角色、昵称（可选）、注册、已有账号，去登录

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 13 | 至少 3 个字符 | `bindinput` | `onUsernameInput` | — |
| 19 | 至少 8 个字符 | `bindinput` | `onPasswordInput` | — |
| 25 | 选择角色，当前为{{roleOptions[roleIndex].label}} | `bindchange` | `onRoleChange` | — |
| 41 | — | `bindinput` | `onNicknameInput` | — |
| 45 | 注册 | `bindtap` | `submitRegister` | — |
| 46 | 已有账号，去登录 | `bindtap` | `goLogin` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 68 | `register` | `POST` | `/api/auth/register` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/home/index`（js:13）、`navigateTo` → `/pages/login/index:dynamic`（js:87）
- 本地存储：—
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
- 源码指纹：`94d9c01cb66ea4aaa4db473bc9d0b829971a9ac4350ba8e6b69fd3d7a905abe4`
- 核对文件：`apps/miniprogram/pages/messages/index.wxml`、`apps/miniprogram/pages/messages/index.wxss`、`apps/miniprogram/pages/messages/index.js`、`apps/miniprogram/pages/messages/index.json`、`apps/miniprogram/utils/errorDiagnostics.js`
- 上游页面：`pages/home/index`、`pages/growth-dashboard/index`、`pages/profile/index`
- 页面组件：`page-state` → `/components/page-state/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`message-row` → `/components/message-row/index`
- 主要可见内容：消息、请求编号： · 服务版本：、复制诊断信息

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 10 | {{needsLogin ?  | `bindaction` | `handleStateAction` | — |
| 13 | 复制本次错误的诊断信息 | `bindtap` | `copyDiagnostic` | — |
| 18 | — | `bindopen` | `openMessage` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 25 | `listMessages` | `GET` | `/api/messages` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/ai_qa.py`、`backend/routes/auth_utils.py`、`backend/routes/emotion_thermometer.py`、`backend/routes/general_growth.py`、`backend/routes/messages.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/message-detail/index?id=:dynamic`（js:50）、`reLaunch` → `/pages/home/index`（js:71）、`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fmessages%2Findex`（js:75）、`navigateTo` → `/pages/register/index?redirect=%2Fpages%2Fmessages%2Findex`（js:79）
- 本地存储：—
- WXML 数据绑定：`loading`、`errorMessage`、`needsLogin`、`errorDiagnostic`、`messages`、`item`
- 条件状态：`loading`、`errorMessage`、`errorDiagnostic`、`messages`
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
- 源码指纹：`70d980fa3a1a19779c8846298960a040fe4d855dd5e3c0c6e694be3c8f400cea`
- 核对文件：`apps/miniprogram/pages/support-assistant/index.wxml`、`apps/miniprogram/pages/support-assistant/index.wxss`、`apps/miniprogram/pages/support-assistant/index.js`、`apps/miniprogram/pages/support-assistant/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/profile/index`
- 页面组件：`page-state` → `/components/page-state/index`、`boundary-note` → `/components/boundary-note/index`、`conversation-entry` → `/components/conversation-entry/index`、`question-composer` → `/components/question-composer/index`
- 主要可见内容：当前未开放、你仍可使用情绪记录、训练卡和人工支持。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 18 | 当前未开放 | `bindaction` | `loadStatus` | — |
| 34 | — | `bindconfirm` | `enableConsent` | — |
| 40 | — | `bindinput` | `onQuestionInput` | — |
| 40 | — | `bindsubmit` | `sendQuestion` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 49 | `getAiQaConfig` | `GET` | `/api/ai-qa/config` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |
| 74 | `createConsent` | `POST` | `/api/consent` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |
| 94 | `createAiQaSession` | `POST` | `/api/ai-qa/sessions` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |
| 111 | `sendAiQaMessage` | `POST` | `/api/ai-qa/sessions` | `backend/app.py`、`backend/config.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/wsgi.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/login/index?redirect=:dynamic`（js:38）、`navigateTo` → `/pages/login/index:dynamic`（js:161）
- 本地存储：`getStorageSync` `auth_token`（JS:137）、`getStorageSync` `auth_user`（JS:141）、`removeStorageSync` `auth_token`（JS:167）、`removeStorageSync` `auth_user`（JS:168）
- WXML 数据绑定：`eyebrow`、`title`、`subtitle`、`loading`、`error`、`boundary`、`consented`、`sending`、`messages`、`item`、`question`
- 条件状态：`loading`、`error`、`enabled`、`messages`
- `setData` 状态：`eyebrow`、`title`、`subtitle`、`focus`、`loading`、`error`、`enabled`、`boundary`、`sending`、`consented`、`question`、`sessionId`、`messages`、`role`、`content`、`citations`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 06：消息详情 `pages/message-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`c096b1e8a75e105a31c3204c3b2d726905014377db67b9d0d2cabf460d2809d8`
- 核对文件：`apps/miniprogram/pages/message-detail/index.wxml`、`apps/miniprogram/pages/message-detail/index.wxss`、`apps/miniprogram/pages/message-detail/index.js`、`apps/miniprogram/pages/message-detail/index.json`
- 上游页面：`pages/messages/index`
- 页面组件：`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：使用边界、这里的内容适合补充理解一条记录，不适合处理紧急安全风险。如正在经历自伤、自杀、暴力、失控或其他安全风险，请先找现实支持。、返回消息列表

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 3 | — | `bindaction` | `handleStateAction` | — |
| 16 | — | `bindtap` | `openSource` | — |
| 19 | — | `bindselect` | `submitFeedbackEvaluation` | — |
| 30 | 返回消息列表 | `bindtap` | `goMessages` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 31 | `getMessage` | `GET` | `/api/messages` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/ai_qa.py`、`backend/routes/auth_utils.py`、`backend/routes/emotion_thermometer.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py` |
| 76 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/ai_qa.py`、`backend/routes/auth_utils.py`、`backend/routes/emotion_thermometer.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:62）、`navigateTo` → `/pages/relationship-narrative/index?id=:dynamic`（js:66）
- 本地存储：—
- WXML 数据绑定：`loading`、`errorMessage`、`id`、`message`、`canOpenSource`、`sourceButtonLabel`、`canEvaluate`、`true`、`feedbackEvaluation`、`feedbackEvaluationSaving`
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
- 源码指纹：`7bca534bdedb5a381b92fb5f64693acc8e659d88371fe4a52923791bcfd0dd3a`
- 核对文件：`apps/miniprogram/pages/emergency-guide/index.wxml`、`apps/miniprogram/pages/emergency-guide/index.wxss`、`apps/miniprogram/pages/emergency-guide/index.js`、`apps/miniprogram/pages/emergency-guide/index.json`
- 上游页面：`pages/emergency-resources/index`、`pages/profile/index`、`pages/feedback-result/index`
- 页面组件：`safety-action-row` → `/components/safety-action-row/index`
- 主要可见内容：先找现实帮助、如果你或孩子正在经历自伤、自杀、暴力、失控或其他安全风险，请优先联系身边可信赖的人、当地紧急服务或线下专业机构。、现在先做、只用于稳定当下，不替代专业帮助、5-4-3-2-1 接地法、把注意力拉回此刻、重要边界、本小程序不能提供实时危机干预、医疗诊断或法律判断。遇到紧急安全风险时，请先使用现实资源。、查看现实支持资源、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 32 | 查看现实支持资源 | `bindtap` | `openResources` | — |
| 33 | 回到首页 | `bindtap` | `goHome` | — |

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
- 源码指纹：`550e049641b205b2bd1f98af274d8dd5a85e414baea509a970522aca49e2231d`
- 核对文件：`apps/miniprogram/pages/emergency-resources/index.wxml`、`apps/miniprogram/pages/emergency-resources/index.wxss`、`apps/miniprogram/pages/emergency-resources/index.js`、`apps/miniprogram/pages/emergency-resources/index.json`
- 上游页面：`pages/emergency-guide/index`、`pages/profile/index`
- 页面组件：`resource-channel-row` → `/components/resource-channel-row/index`
- 主要可见内容：先把人连接上、这里不提供热线号码库，也不判断你是否处于危机。紧急时，请优先找能真实到场或及时回应的帮助。、使用边界、本工具不能替代紧急服务、线下专业评估、法律判断或医疗诊断。安全风险出现时，请先停止独自处理。、查看紧急安全指引

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 19 | 查看紧急安全指引 | `bindtap` | `goGuide` | — |

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
- 源码指纹：`51a242b663c9c40481b1d34b54d9021773b64e3f7a5eede9af2d712052c5c617`
- 核对文件：`apps/miniprogram/pages/getting-started/index.wxml`、`apps/miniprogram/pages/getting-started/index.wxss`、`apps/miniprogram/pages/getting-started/index.js`、`apps/miniprogram/pages/getting-started/index.json`
- 上游页面：`pages/home/index`
- 页面组件：—
- 主要可见内容：从一件具体小事开始、写一个片段、标一个位置、做一个动作、把事件放进以下七个位置，梳理发生的全过程：、记录一次 → 查看反馈线索 → 去训练中心练一个小动作、使用边界、记录一次、去训练中心

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 70 | 记录一次 | `bindtap` | `startDiary` | — |
| 71 | 去训练中心 | `bindtap` | `openTraining` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index`（js:39）、`switchTab` → `/pages/training/index`（js:43）
- 本地存储：—
- WXML 数据绑定：`exerciseSteps`、`eventReasons`、`item`、`arcNodes`、`index`、`boundaries`
- 条件状态：—
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
- 源码指纹：`40534a6f5d180f76eb8185c7e55c6e0646f06c5bfc9e53b53d673327742c4098`
- 核对文件：`apps/miniprogram/pages/thermometer/index.wxml`、`apps/miniprogram/pages/thermometer/index.wxss`、`apps/miniprogram/pages/thermometer/index.js`、`apps/miniprogram/pages/thermometer/index.json`、`apps/miniprogram/utils/chart.js`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`
- 页面组件：`intensity-scale` → `/components/intensity-scale/index`
- 主要可见内容：情绪温度计、现在的强度、补充观察（可保持默认）、愉悦度、身体唤起、可控感、记录完成、去练一张卡、今日曲线、共 次，平均、刷新、正在读取今天的记录…、· 强度 / 10、今天还没有记录、先记录一次，再看曲线。、暂时没能完成、重试读取、今天的记录、强度 / 10、· 愉悦 · 唤起 · 可控

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 13 | − | `bindchange` | `onIntensityChange` | — |
| 17 | 情绪强度减一 | `bindtap` | `decreaseIntensity` | — |
| 18 | 情绪强度加一 | `bindtap` | `increaseIntensity` | — |
| 30 | 调整愉悦度 | `bindchange` | `onValenceChange` | — |
| 30 | 调整愉悦度 | `bindchanging` | `onValenceChange` | — |
| 37 | 调整身体唤起 | `bindchange` | `onArousalChange` | — |
| 37 | 调整身体唤起 | `bindchanging` | `onArousalChange` | — |
| 44 | 调整可控感 | `bindchange` | `onControlChange` | — |
| 44 | 调整可控感 | `bindchanging` | `onControlChange` | — |
| 48 | / 40 | `bindinput` | `onEmotionLabelInput` | — |
| 58 | / 200 | `bindinput` | `onBriefInput` | — |
| 69 | — | `bindtap` | `saveRecord` | — |
| 78 | 收起记录回执 | `bindtap` | `dismissReceipt` | — |
| 82 | 去练一张卡 | `bindtap` | `openPractice` | — |
| 91 | 刷新 | `bindtap` | `loadDay` | — |
| 94 | 今日情绪强度变化曲线，具体记录见下方列表 | `bindtouchstart` | `handleCanvasTap` | — |
| 115 | 重试读取 | `bindtap` | `loadDay` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index`（js:152）、`navigateTo` → `/pages/login/index:dynamic`（js:333）
- 本地存储：`getStorageSync` `auth_token`（JS:309）、`getStorageSync` `auth_user`（JS:313）、`removeStorageSync` `auth_token`（JS:339）、`removeStorageSync` `auth_user`（JS:340）
- WXML 数据绑定：`intensityLevel`、`valenceLevel`、`arousalLevel`、`controlLevel`、`emotionLabel`、`briefText`、`saving`、`receipt`、`item`、`loading`、`summary`、`selectedPoint`、`errorMessage`、`records`、`boundaryNotice`
- 条件状态：`receipt`、`loading`、`summary`、`selectedPoint`、`errorMessage`、`item`、`records`
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
- 源码指纹：`4f6724f35476779461a5f870230fa64721fc4d4c63f74ed1f94ae32e3e10c226`
- 核对文件：`apps/miniprogram/pages/training/index.wxml`、`apps/miniprogram/pages/training/index.wxss`、`apps/miniprogram/pages/training/index.js`、`apps/miniprogram/pages/training/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`、`pages/login/index`、`pages/getting-started/index`、`pages/training-history/index`、`pages/growth-dashboard/index`、`pages/course-detail/index`、`pages/assessment-result/index`
- 页面组件：`section-title` → `/components/section-title/index`、`training-task-card` → `/components/training-task-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：训练中心、通用训练、按阶段浏览训练卡、个性化方案、根据测评推荐练习、项目测试、暑期试点练习包、今天可以先练这个方向、推荐理由、今日建议、优先、近期练过，需要巩固时可以再练。、查看练习、项目试点 · 大学生关系探索、从测一测到评估问题与微行动、聚合阶段性画像、初筛报告、关系绘画、句子补全和连续复盘。它不是治疗或诊断服务。、进入关系探索试点、3 天轻量练习、不知道从哪里开始？、先按“觉察—稳定—回应”的顺序选一张；不需要一次完成全部阶段。、情绪觉察、先看见自己、身体调节、让反应慢下来

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 15 | 个性化方案 | `bindtap` | `openPersonalizedPlan` | — |
| 19 | 项目测试 | `bindtap` | `openProgramList` | — |
| 48 | 查看练习 | `bindtap` | `openLatestRecommendation` | — |
| 55 | 进入关系探索试点 | `bindtap` | `openRelationshipPilot` | — |
| 64 | — | `bindtap` | `toggleLightPlan` | — |
| 66 | — | `bindtap` | `openPlanDay` | {'card-id': '{{item.cardId}}'} |
| 104 | — | `bindtap` | `toggleLibrary` | — |
| 111 | — | `bindtapcard` | `openTrainingCard` | {'id': '{{task.id}}', 'tags': '{{task.tagsText}}'} |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 149 | `getShowcaseAccess` | `GET` | `/api/showcase-access` | `backend/app.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/programs.py`、`backend/routes/showcase_access.py`、`backend/routes/training_plan.py`、`backend/scripts/generate_task32_reliability_registry.py`、`backend/scripts/generate_task34_operations_registry.py` |
| 159 | `getTrainingPlan` | `GET` | `/api/training-plan` | `backend/app.py`、`backend/routes/auth_utils.py`、`backend/routes/courses.py`、`backend/routes/programs.py`、`backend/routes/showcase_access.py`、`backend/routes/training_plan.py`、`backend/scripts/generate_task32_reliability_registry.py`、`backend/scripts/generate_task34_operations_registry.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:227）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:242）、`navigateTo` → `/pages/personalized-plan/index`（js:248）、`navigateTo` → `/pages/program-list/index`（js:252）、`navigateTo` → `/pages/relationship-pilot/index`（js:264）、`navigateTo` → `/pages/task-detail/index?id=:dynamic`（js:269）、`navigateTo` → `/pages/login/index:dynamic`（js:300）
- 本地存储：`getStorageSync` `LATEST_TRAINING_RECOMMENDATION_KEY`（JS:185）、`getStorageSync` `THREE_DAY_LIGHT_PLAN_KEY`（JS:203）、`getStorageSync` `auth_token`（JS:276）、`getStorageSync` `auth_user`（JS:280）、`removeStorageSync` `auth_token`（JS:306）、`removeStorageSync` `auth_user`（JS:307）
- WXML 数据绑定：`latestRecommendation`、`relationshipPilotAvailable`、`threeDayPlan`、`lightPlanExpanded`、`item`、`libraryExpanded`、`trainingStages`、`task`
- 条件状态：`latestRecommendation`、`relationshipPilotAvailable`、`threeDayPlan`、`lightPlanExpanded`、`libraryExpanded`
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
- 源码指纹：`39009712682baf57a05fd38352e14fec831d4a8763f035035c8844a51700e3fc`
- 核对文件：`apps/miniprogram/pages/training-history/index.wxml`、`apps/miniprogram/pages/training-history/index.wxss`、`apps/miniprogram/pages/training-history/index.js`、`apps/miniprogram/pages/training-history/index.json`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/errorDiagnostics.js`
- 上游页面：`pages/profile/index`
- 页面组件：—
- 主要可见内容：训练记录、次记录、正在读取训练记录、记录暂时没有加载成功、请求编号： · 服务版本：、重新加载、复制诊断信息、再次练习、已显示全部 次记录、还没有训练记录、去训练中心

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 20 | 重新加载 | `bindtap` | `retry` | — |
| 21 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | — |
| 34 | 再次练习 | `bindtap` | `openCard` | {'card-id': '{{item.card_id}}'} |
| 37 | — | `bindtap` | `loadMore` | — |
| 40 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | — |
| 47 | 去训练中心 | `bindtap` | `goTraining` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 56 | `listCheckins` | `GET` | `/api/checkins` | `backend/app.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/checkins.py`、`backend/routes/general_growth.py`、`backend/routes/profile.py`、`backend/routes/research_workspace.py`、`backend/routes/training_plan.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:99）、`switchTab` → `/pages/training/index`（js:103）、`navigateTo` → `/pages/login/index:dynamic`（js:132）
- 本地存储：`getStorageSync` `auth_token`（JS:108）、`getStorageSync` `auth_user`（JS:112）、`removeStorageSync` `auth_token`（JS:138）、`removeStorageSync` `auth_user`（JS:139）
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
- 源码指纹：`90a0c747eabf95752088ba9bed3211bed8aaa61131c50d976a6089a796def81d`
- 核对文件：`apps/miniprogram/pages/personalized-plan/index.wxml`、`apps/miniprogram/pages/personalized-plan/index.wxss`、`apps/miniprogram/pages/personalized-plan/index.js`、`apps/miniprogram/pages/personalized-plan/index.json`
- 上游页面：`pages/training/index`
- 页面组件：`training-task-card` → `/components/training-task-card/index`
- 主要可见内容：个性化训练方案、安排练习节奏、先选一个当前可承受的频率，之后可以随时调整。、当前阶段、练习频率、开始日期、计划状态、保存练习节奏、提醒、微信练习提醒、只在你主动授权后发送；关闭提醒不影响训练。、暂未开放、管理员完成微信模板审核后，这里可以开启。、已同意本次提醒、到达下一次练习日期后发送；一次性授权使用后需要重新开启。、上次授权已使用、如需下一次提醒，请再次主动开启。、微信设置中已关闭、如需恢复，请前往小程序设置调整订阅消息权限。、需要时再开启、建议在保存好练习节奏后，开启一次微信提醒。、开启一次微信提醒、前往微信设置、去测一测

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 17 | — | `bindtap` | `selectAssignmentOption` | {'field': 'phase', 'value': '{{item.value}}'} |
| 29 | — | `bindtap` | `selectAssignmentOption` | {'field': 'cadence', 'value': '{{item.value}}'} |
| 41 | — | `bindchange` | `onStartDateChange` | — |
| 48 | — | `bindtap` | `selectAssignmentOption` | {'field': 'status', 'value': '{{item.value}}'} |
| 59 | 保存练习节奏 | `bindinput` | `onGoalInput` | — |
| 66 | 保存练习节奏 | `bindtap` | `saveAssignment` | — |
| 102 | 开启一次微信提醒 | `bindtap` | `requestTrainingReminder` | — |
| 108 | 前往微信设置 | `bindtap` | `openNotificationSettings` | — |
| 118 | 去测一测 | `bindtap` | `openAssessment` | — |
| 129 | — | `bindtapcard` | `openSingleCard` | — |
| 151 | 重试 | `bindtap` | `loadPlan` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment/index`（js:176）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:185）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:191）
- 本地存储：—
- WXML 数据绑定：`assignment`、`phaseOptions`、`item`、`cadenceOptions`、`statusOptions`、`savingAssignment`、`plan`、`notification`、`requestingReminder`、`planItems`、`card`、`loading`、`errorMessage`、`boundaryNotice`
- 条件状态：`assignment`、`plan`、`notification`、`loading`、`item`
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
- 源码指纹：`12cd15109f1d92606b23fdfefcd1370c6cce47e21e1e06e610664076ad52ecfb`
- 核对文件：`apps/miniprogram/pages/program-list/index.wxml`、`apps/miniprogram/pages/program-list/index.wxss`、`apps/miniprogram/pages/program-list/index.js`、`apps/miniprogram/pages/program-list/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/training/index`
- 页面组件：—
- 主要可见内容：项目测试、研究者预览、草案仅供审核，不可作为正式项目提交。、小节、受众：、目标构念：、第一节：、已有 个方案完成开发，待研究、心理和伦理审核。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 14 | 打开项目：{{item.title}} | `bindtap` | `openProgram` | {'id': '{{item.id}}', 'preview': '{{item.preview_only}}'} |
| 35 | <text wx:if="{{!loading && !errorMessage && !pro | `bindaction` | `loadPrograms` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| — | 无直接 API 调用 | — | — | 页面由本地状态或路由驱动 |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/program-detail/index?id=:dynamic`（js:50）、`navigateTo` → `/pages/login/index:dynamic`（js:79）
- 本地存储：`getStorageSync` `auth_token`（JS:55）、`getStorageSync` `auth_user`（JS:59）、`removeStorageSync` `auth_token`（JS:85）、`removeStorageSync` `auth_user`（JS:86）
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
- 源码指纹：`33c52e7b39a59708ce6d5817fab3e9a5ff749bd6a2de73d219810e3a47cd10bd`
- 核对文件：`apps/miniprogram/pages/program-detail/index.wxml`、`apps/miniprogram/pages/program-detail/index.wxss`、`apps/miniprogram/pages/program-detail/index.js`、`apps/miniprogram/pages/program-detail/index.json`
- 上游页面：`pages/home/index`、`pages/program-list/index`
- 页面组件：—
- 主要可见内容：· 方案、研究者只读预览：当前草案尚未完成三方审核，填写、保存和提交均已关闭。、参与前先了解、适合参加的基本条件、这些情况先不要继续、可选替代：、项目记录节奏、用于安排开始前、练习中和完成后的阶段记录。、第 节、预计 分钟、练习步骤、书写提示、保存本机草稿、反思问题、完成标准：、停止提示：、练习前不适程度： / 10、练习后不适程度： / 10、这次练习出现了明显不适或负面体验，需要后续关注。、允许将本次内容用于脱敏聚合分析，不默认展示原文。、登录后正式提交、我已提交的项目记录、提交内容会保留在本人记录中，并按授权范围供研究者只读查看。、已提交

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 55 | 第 节 | `bindtap` | `selectSession` | {'session-no': '{{item.session_no}}'} |
| 82 | 保存本机草稿 | `bindinput` | `onDraftInput` | — |
| 83 | 保存本机草稿 | `bindtap` | `saveDraft` | — |
| 90 | — | `bindinput` | `onReflectionInput` | {'index': '{{index}}'} |
| 107 | 练习后不适程度： / 10 | `bindchange` | `onDistressBeforeChange` | — |
| 109 | 这次练习出现了明显不适或负面体验，需要后续关注。 | `bindchange` | `onDistressAfterChange` | — |
| 110 | 这次练习出现了明显不适或负面体验，需要后续关注。 | `bindchange` | `onAdverseResponseChange` | — |
| 116 | 允许将本次内容用于脱敏聚合分析，不默认展示原文。 | `bindchange` | `onAnalysisConsentChange` | — |
| 124 | 登录后正式提交 | `bindtap` | `submitEntry` | — |
| 148 | 重试 | `bindtap` | `retryLoad` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 172 | `listProgramEntries` | `GET` | `/api/programs/:id/entries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/programs.py` |
| 203 | `createProgramEntry` | `POST` | `/api/programs/:id/entries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/programs.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `draftKey`（JS:118）、`setStorageSync` `draftKey`（JS:163）、`removeStorageSync` `draftKey`（JS:219）
- WXML 数据绑定：`program`、`item`、`previewMode`、`sessions`、`selectedSession`、`index`、`draftText`、`reflectionAnswers`、`distressBefore`、`distressAfter`、`adverseResponse`、`analysisConsent`、`successMessage`、`errorMessage`、`submitting`、`submittedEntries`、`loading`
- 条件状态：`program`、`previewMode`、`selectedSession`、`successMessage`、`errorMessage`、`loading`
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
- 源码指纹：`be881c6c8f56f1fe968d17e529d0072b84df77a91983e1c289f12ef8d2127ac5`
- 核对文件：`apps/miniprogram/pages/relationship-pilot/index.wxml`、`apps/miniprogram/pages/relationship-pilot/index.wxss`、`apps/miniprogram/pages/relationship-pilot/index.js`、`apps/miniprogram/pages/relationship-pilot/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/training/index`、`pages/relationship-growth/index`、`pages/growth-dashboard/index`
- 页面组件：`journey-action-card` → `/components/journey-action-card/index`
- 主要可见内容：从起点测评到连续记录，每一步都可以暂停。这里不判断你是否“适合恋爱”，也不替代心理咨询。、正在读取你的探索进度...、当前仅向学生试点账号开放、你仍可使用情绪记录、训练卡和其它支持功能。若需参加关系探索试点，请切换到已授权的学生账号。、第一步 · 起点测评与报名、确认是否进入第二阶段、报名会关联你最近一份关系探索测评的维度、阶段性画像与报告。逐行研究数据不会显示给其他用户。、我已阅读并同意将本次测评用于关系探索试点的评估与复盘。、确认报名、还没测评？先完成关系测一测、五阶段探索路径、其它入口、所有画像和报告都只作阶段性观察，不构成诊断、人格标签、关系能力评价或疗效证明。

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

- 下游路由：`navigateTo` → `/pages/assessment/index?audience_class=student&query=%E5%85%B3%E7%B3%BB`（js:165）、`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:174）、`navigateTo` → `/pages/relationship-task/index?type=relationship_drawing&enrollment_id=:dynamic`（js:178）、`navigateTo` → `/pages/relationship-task/index?type=sentence_completion&enrollment_id=:dynamic`（js:182）、`navigateTo` → `/pages/relationship-growth/index?detail=1&enrollment_id=:dynamic`（js:186）、`navigateTo` → `/pages/login/index:dynamic`（js:217）
- 本地存储：`getStorageSync` `auth_token`（JS:193）、`getStorageSync` `auth_user`（JS:197）、`removeStorageSync` `auth_token`（JS:223）、`removeStorageSync` `auth_user`（JS:224）
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

### 17：阶段性报告 `pages/relationship-report/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`097f76b1908d3bb72fba73d291be817498f5e082d459d1ce68df482ea14b1f77`
- 核对文件：`apps/miniprogram/pages/relationship-report/index.wxml`、`apps/miniprogram/pages/relationship-report/index.wxss`、`apps/miniprogram/pages/relationship-report/index.js`、`apps/miniprogram/pages/relationship-report/index.json`
- 上游页面：`pages/message-detail/index`、`pages/relationship-pilot/index`、`pages/researcher-dashboard/index`
- 页面组件：`relationship-status` → `/components/relationship-status/index`、`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：正在人工核对、研究者完成核对并发送后，你会在消息列表收到提醒。当前不会展示画像、解释或机制假设。、需要多一点人工核对、当前阶段解释、基础画像、本次维度轮廓、条形只表示本次在参考样本中的相对位置，不代表好坏或能力排名。、矛盾画像、两种需要可能同时存在、靠近与行动意愿、同时、保护与现实节奏、机制画像、待核对假设、这些只是讨论线索。请以你的真实经验为准，共同修订比“被系统定义”更重要。、当前选择：、符合、不符合、不确定、动态画像、连续记录、已有 次记录，变化只作为讨论线索。、目前只有一次记录。完成两次以上后，才显示趋势箭头。、讨论线索

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 3 | 正在人工核对 | `bindaction` | `loadReport` | — |
| 32 | — | `bindselect` | `submitReportEvaluation` | — |
| 62 | 符合 | `bindtap` | `saveHypothesisFeedback` | {'index': '{{item.index}}', 'response': 'matches'} |
| 63 | 不符合 | `bindtap` | `saveHypothesisFeedback` | {'index': '{{item.index}}', 'response': 'does_not_match'} |
| 64 | 不确定 | `bindtap` | `saveHypothesisFeedback` | {'index': '{{item.index}}', 'response': 'uncertain'} |
| 99 | 生成脱敏报告长图 | `bindtap` | `drawLongImage` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 81 | `getRelationshipReport` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |
| 127 | `saveRelationshipHypothesisFeedback` | `PUT` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |
| 145 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |
| 222 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/feedback_ledger.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：—
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
- 源码指纹：`82b8c7e4a31c262876b5685089cf2121d1e8e96baa4c1a740c62ee031524449c`
- 核对文件：`apps/miniprogram/pages/relationship-task/index.wxml`、`apps/miniprogram/pages/relationship-task/index.wxss`、`apps/miniprogram/pages/relationship-task/index.js`、`apps/miniprogram/pages/relationship-task/index.json`
- 上游页面：`pages/home/index`、`pages/relationship-pilot/index`
- 页面组件：—
- 主要可见内容：线上探索材料、已恢复上次未提交的本机草稿，你可以接着完成。、画布、可撤销、重做，草稿自动留在本机、撤销、重做、清空、给这幅画写一两句画外音、已填写、如果在“ ”的情境里，会怎样？、本题可以跳过、我同意将这份敏感叙事材料用于本次试点评估与人工复核；默认不导出原文。、材料只作为访谈和共同理解的线索，不自动解释潜意识、人格、依恋类型或病理模式。、提交这份材料

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 13 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchstart` | `startStroke` | — |
| 13 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchmove` | `moveStroke` | — |
| 13 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchend` | `endStroke` | — |
| 15 | 撤销 | `bindtap` | `undoStroke` | — |
| 16 | 重做 | `bindtap` | `redoStroke` | — |
| 17 | 清空 | `bindtap` | `clearCanvas` | — |
| 21 | — | `bindinput` | `onNarrationInput` | — |
| 28 | — | `bindtap` | `toggleContext` | {'key': '{{item.key}}'} |
| 34 | — | `bindinput` | `onSentenceInput` | {'key': '{{item.key}}'} |
| 41 | 我同意将这份敏感叙事材料用于本次试点评估与人工复核；默认不导出原文。 | `bindchange` | `toggleConsent` | — |
| 45 | 提交这份材料 | `bindtap` | `saveTask` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 318 | `createRelationshipTask` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py` |
| 328 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py` |
| 351 | `trackProductEvent` | `POST` | `/api/product-events` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py` |

#### 路由、本地状态与页面状态

- 下游路由：—
- 本地存储：`getStorageSync` `this`（JS:87）、`removeStorageSync` `this`（JS:138）、`setStorageSync` `this`（JS:143）、`removeStorageSync` `this`（JS:334）
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

### 19：关系探索成长记录 `pages/relationship-growth/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`7bf2edf253baa6499f0d0778cd73ac046e891ea2b18a0374805b87d79cf7f733`
- 核对文件：`apps/miniprogram/pages/relationship-growth/index.wxml`、`apps/miniprogram/pages/relationship-growth/index.wxss`、`apps/miniprogram/pages/relationship-growth/index.js`、`apps/miniprogram/pages/relationship-growth/index.json`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/relationship-pilot/index`、`pages/growth-dashboard/index`
- 页面组件：`visualization-state` → `/components/visualization-state/index`、`timeline-record` → `/components/timeline-record/index`
- 主要可见内容：关系探索成长记录、正在读取成长记录...、累计记录、指标组、阶段性反馈、变化曲线、每组数字含义不同，不合并成总分、再记录 次后可查看变化趋势、数据不足、目前有 个记录点；这里不会根据单次记录判断变化。、最近时间线、查看全部 ›、还没有时间线记录，可以先写下今天的一小步。、成长时间线、按记录类型查看，不急于解释趋势、这一类还没有记录。、系统汇总与研究者补充明确分开、研究者补充、暂时还没有研究者阶段性反馈。、系统汇总、下一步建议：、用户原话（仅你可见）、目前没有开放文字记录。、先建立关系探索起点

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 25 | 查看{{item.label}} | `bindtap` | `selectSection` | {'section': '{{item.key}}'} |
| 35 | — | `bindtap` | `selectCurveGroup` | {'key': '{{item.key}}'} |
| 36 | — | `bindtap` | `selectMetric` | {'key': '{{item.key}}'} |
| 57 | 查看全部 › | `bindtap` | `showAllTimeline` | — |
| 68 | — | `bindtap` | `selectTimelineFilter` | {'key': '{{item.key}}'} |
| 79 | 用户原话（仅你可见） | `bindtap` | `toggleSelfNarratives` | — |
| 87 | 前往关系探索 | `bindtap` | `goRelationshipPilot` | — |
| 91 | 本周补充记录 | `bindtap` | `toggleRecordPanel` | {'panel': 'weekly'} |
| 93 | — | `bindinput` | `onFieldInput` | {'key': 'active_social_count'} |
| 94 | — | `bindinput` | `onFieldInput` | {'key': 'authentic_expression_count'} |
| 95 | — | `bindinput` | `onFieldInput` | {'key': 'setback_coping'} |
| 96 | — | `bindchange` | `onSliderChange` | {'key': 'approach_willingness'} |
| 97 | — | `bindchange` | `onSliderChange` | {'key': 'worry_intensity'} |
| 98 | — | `bindinput` | `onFieldInput` | {'key': 'achievement'} |
| 99 | — | `bindinput` | `onFieldInput` | {'key': 'setback'} |
| 102 | 保存本周记录 | `bindtap` | `saveWeekly` | — |
| 107 | 记录一个关键事件 | `bindtap` | `toggleRecordPanel` | {'panel': 'event'} |
| 109 | — | `bindinput` | `onFieldInput` | {'key': 'event_summary'} |
| 111 | 加入时间线 | `bindtap` | `saveEvent` | — |
| 117 | 共同理解一次关系体验 | `bindtap` | `goTherapeuticAssessment` | — |
| 118 | 记录今天的一小步 | `bindtap` | `openRecordSection` | — |
| 119 | 查看阶段性反馈 | `bindtap` | `showFeedbackSection` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 182 | `getRelationshipGrowth` | `GET` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py`、`backend/routes/research_workspace.py` |
| 400 | `createRelationshipLongitudinal` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py`、`backend/routes/research_workspace.py` |
| 445 | `createRelationshipLongitudinal` | `POST` | `/api/relationship-pilot` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/auth_utils.py`、`backend/routes/general_growth.py`、`backend/routes/relationship_pilot.py`、`backend/routes/relationship_pilot_routes.py`、`backend/routes/research_workspace.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/therapeutic-assessment/index`（js:135）、`redirectTo` → `/pages/growth-dashboard/index?section=relationship:dynamic`（js:144）、`navigateTo` → `/pages/relationship-pilot/index`（js:389）
- 本地存储：`getStorageSync` `storageKey`（JS:487）、`setStorageSync` `storageKey`（JS:509）、`removeStorageSync` `storageKey`（JS:539）
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
- 源码指纹：`b280a1555cbf66f0c8b13746dcafee855332a7cacc6f5c7840dba158a3db59d4`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment/index.wxss`、`apps/miniprogram/pages/therapeutic-assessment/index.js`、`apps/miniprogram/pages/therapeutic-assessment/index.json`
- 上游页面：`pages/relationship-growth/index`、`pages/therapeutic-assessment-action-followup/index`
- 页面组件：—
- 主要可见内容：· 可撤回、共同理解一次关系体验、每一步只做一个主要决定；你可以暂停、表达不同意见或撤回。、继续最近一次协作、开始一次协作、开始新的议题、正在读取协作记录…、当前协作、版本、当前改写：、查看两个问题候选、都不符合、经人工复核的反馈、不确定性：、可讨论的下一步：、研究者正在整理可讨论的草稿；未经人工复核的内容不会发送给你。、本次可见线索、下一步核对、尚无可见线索；内部草稿不会提前展示。、这和我的体验不一致、暂时停一下、更正与投诉、撤回本次协作、选择一个愿意尝试的小行动、仅在收到经人工复核的反馈后记录。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 18 | 继续最近一次协作 | `bindtap` | `continueParticipantFlow` | — |
| 19 | 开始一次协作 | `bindtap` | `startParticipantFlow` | — |
| 20 | 开始新的议题 | `bindtap` | `startParticipantFlow` | — |
| 36 | 查看两个问题候选 | `bindtap` | `updateQuestionAction` | {'action': 'generate_candidates'} |
| 37 | 都不符合 | `bindtap` | `updateQuestionAction` | {'action': 'none_fit'} |
| 58 | 这和我的体验不一致 | `bindtap` | `disagree` | — |
| 59 | 暂时停一下 | `bindtap` | `updateQuestionAction` | {'action': 'pause'} |
| 60 | 更正与投诉 | `bindtap` | `openQualityRecord` | — |
| 62 | 撤回本次协作 | `bindtap` | `withdraw` | — |
| 68 | — | `bindinput` | `onActionInput` | — |
| 69 | 记录下一小步 | `bindtap` | `chooseAction` | — |
| 75 | — | `bindinput` | `onQuestionInput` | — |
| 77 | 上面的问题 | `bindchange` | `onScopeChange` | — |
| 81 | 提交协作问题 | `bindtap` | `createCase` | — |
| 103 | 确认符合上述范围 | `bindtap` | `confirmAdultLaunchScope` | — |

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
- 本地存储：—
- WXML 数据绑定：`activeCase`、`notice`、`errorMessage`、`loading`、`item`、`evidenceSummary`、`evidenceItems`、`actionText`、`saving`、`question`、`shareQuestion`、`shareRecentRecord`、`productionContract`、`adultLaunchScope`、`launchScreening`、`childPolicy`、`multiPartyPolicy`、`aiAssistPolicy`、`methodCatalog`
- 条件状态：`notice`、`errorMessage`、`activeCase`、`loading`、`evidenceSummary`、`evidenceItems`、`productionContract`、`adultLaunchScope`、`launchScreening`、`childPolicy`、`multiPartyPolicy`、`aiAssistPolicy`、`methodCatalog`
- `setData` 状态：`loading`、`errorMessage`、`activeCase`、`defaultServiceLevel`、`cases`、`productionContract`、`adultLaunchScope`、`childPolicy`、`multiPartyPolicy`、`aiAssistPolicy`、`methodCatalog`、`evidenceItems`、`evidenceSummary`、`launchScreening`、`saving`、`notice`、`question`、`actionText`、`shareQuestion`、`shareRecentRecord`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 21：开始前了解 `pages/therapeutic-assessment-boundary/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`e88d6414d79dfa197359aaa394d0783e3d9f346a43526808c9a09abc8987a646`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-boundary/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-boundary/index.js`、`apps/miniprogram/pages/therapeutic-assessment-boundary/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`2462091bf8e06e314f86264dc485bb4a0233984cce9b18961df30be7a98896b7`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-issue/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-issue/index.js`、`apps/miniprogram/pages/therapeutic-assessment-issue/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`7281f2c86b4cfea1f842fd53c84483e2dacb91f051d21794b23a12896b977dd2`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-recent-event/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-recent-event/index.js`、`apps/miniprogram/pages/therapeutic-assessment-recent-event/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`2fdcdee2be49d01a57b661783491f570e553d35c4f321ae49a7b97f7f661ba0f`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-resources/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-resources/index.js`、`apps/miniprogram/pages/therapeutic-assessment-resources/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`1c7cfe9436c4ef83e7d67506fa59a45dcf16bada8e3eae959f3e4e8da2109900`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-sharing/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-sharing/index.js`、`apps/miniprogram/pages/therapeutic-assessment-sharing/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`11187dc22ce051ae17215f02acf666a4ecabcefecb01f5bf278af8c941e3e9eb`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-summary/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-summary/index.js`、`apps/miniprogram/pages/therapeutic-assessment-summary/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`7b10c3a64199e6a2382814f386a034b9468468dcb0be373140cec1f22733f59c`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-feedback-check/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-feedback-check/index.js`、`apps/miniprogram/pages/therapeutic-assessment-feedback-check/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`5226c3568ec69afa9a56bf1e1472156d4f9641c8e7efc1783a2b6412b6ba4bf4`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-action-review/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-action-review/index.js`、`apps/miniprogram/pages/therapeutic-assessment-action-review/index.json`、`apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
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

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment-action-followup/index?caseId=:dynamic`（js:380）、`redirectTo` → `/pages/therapeutic-assessment/index`（js:383）、`redirectTo` → `/pages/login/index:dynamic`（js:473）
- 本地存储：`getStorageSync` `auth_token`（JS:482）、`getStorageSync` `auth_user`（JS:486）、`removeStorageSync` `auth_token`（JS:512）、`removeStorageSync` `auth_user`（JS:513）、`getStorageSync` `storageKey`（JS:555）、`setStorageSync` `storageKey`（JS:577）、`removeStorageSync` `storageKey`（JS:607）
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
- 源码指纹：`51429b19e751e3187aeb4efb007334414336dde11756b78f52efefabf5ec420d`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.wxss`、`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.js`、`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：—
- 页面组件：`page-state` → `/components/page-state/index`
- 主要可见内容：一次记录，不是疗效证明、回看这次小行动、原计划、停止条件、这次的状态、尝试过、中途停止、决定不做、把这次内容记成、新的观察、仍待了解、打开关联训练卡、保存这次回看

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 8 | — | `bindaction` | `load` | — |
| 29 | 尝试过 | `bindtap` | `selectStatus` | {'value': 'completed'} |
| 30 | 中途停止 | `bindtap` | `selectStatus` | {'value': 'stopped'} |
| 31 | 决定不做 | `bindtap` | `selectStatus` | {'value': 'declined'} |
| 36 | 新的观察 | `bindtap` | `selectKind` | {'value': 'O'} |
| 37 | 仍待了解 | `bindtap` | `selectKind` | {'value': 'U'} |
| 40 | 行动回看内容 | `bindinput` | `onNoteInput` | — |
| 41 | 打开关联训练卡 | `bindtap` | `openTrainingCard` | — |
| 42 | 保存这次回看 | `bindtap` | `submit` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 40 | `listTherapeuticAssessmentCases` | `GET` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 73 | `updateTherapeuticAssessmentAction` | `PATCH` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |
| 82 | `createTherapeuticAssessmentActionFollowup` | `POST` | `/api/therapeutic-assessment` | `backend/app.py`、`backend/database.py`、`backend/routes/auth_utils.py`、`backend/routes/therapeutic_assessment.py`、`backend/scripts/audit_task36_f16_therapeutic_assessment.py`、`backend/scripts/audit_task36_f17_reliability_security.py`、`backend/scripts/audit_task38_f01_service_levels.py`、`backend/scripts/audit_task38_f06_participant_flow.py` |

#### 路由、本地状态与页面状态

- 下游路由：`redirectTo` → `/pages/therapeutic-assessment/index`（js:94）、`navigateTo` → `/pages/training-card/index?id=:dynamic`（js:104）、`navigateTo` → `/pages/login/index:dynamic`（js:135）
- 本地存储：`getStorageSync` `auth_token`（JS:111）、`getStorageSync` `auth_user`（JS:115）、`removeStorageSync` `auth_token`（JS:141）、`removeStorageSync` `auth_user`（JS:142）
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
- 源码指纹：`18cba53aa9088e73d419d47a5db7dc9a3ac23c3cc2cef60f32e189bc534e5833`
- 核对文件：`apps/miniprogram/pages/therapeutic-assessment-quality/index.wxml`、`apps/miniprogram/pages/therapeutic-assessment-quality/index.wxss`、`apps/miniprogram/pages/therapeutic-assessment-quality/index.js`、`apps/miniprogram/pages/therapeutic-assessment-quality/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/therapeutic-assessment/index`、`pages/researcher-dashboard/index`
- 页面组件：—
- 主要可见内容：质量与更正、当前没有可处理的质量记录、待处理 · 已超时 · 规则、暂时没有处理成功、重新读取、正在读取质量记录、只加载当前账号可查看的对象范围。、生产门禁、更正与投诉、记录哪里不像，或希望如何处理、协作记录、问题类型、具体哪里不像或发生了什么、希望怎样处理、提交更正或投诉、原记录会保留，反馈、异议和处理版本不会被覆盖。、抽检队列、逐项质量复核、项、当前授权范围内没有复核任务、抽检原因： · 截止：、认领这项复核、结论：、修复说明（有修复项时必填）

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 19 | 重新读取 | `bindtap` | `loadData` | — |
| 52 | — | `bindchange` | `onCaseChange` | — |
| 57 | — | `bindchange` | `onIncidentCategory` | — |
| 62 | — | `bindinput` | `onFieldInput` | {'key': 'incidentDescription'} |
| 66 | — | `bindinput` | `onFieldInput` | {'key': 'requestedResolution'} |
| 68 | 提交更正或投诉 | `bindtap` | `submitIncident` | — |
| 84 | — | `bindtap` | `selectReview` | {'id': '{{item.id}}'} |
| 98 | 认领这项复核 | `bindtap` | `claimReview` | — |
| 102 | 结论： | `bindchange` | `onDimensionStatus` | {'index': '{{index}}'} |
| 106 | — | `bindinput` | `onDimensionInput` | {'index': '{{index}}', 'key': 'note'} |
| 107 | — | `bindinput` | `onDimensionInput` | {'index': '{{index}}', 'key': 'evidenceRef'} |
| 112 | — | `bindinput` | `onFieldInput` | {'key': 'remediationSummary'} |
| 114 | 提交质量结论 | `bindtap` | `completeReview` | — |
| 131 | — | `bindtap` | `selectIncident` | {'id': '{{item.id}}'} |
| 142 | — | `bindinput` | `onFieldInput` | {'key': 'impactSummary'} |
| 144 | 保存影响分析 | `bindtap` | `analyzeIncident` | — |
| 147 | 处理动作： | `bindchange` | `onResolutionAction` | — |
| 152 | — | `bindinput` | `onFieldInput` | {'key': 'resolutionSummary'} |
| 154 | 独立结案并通知参与者 | `bindtap` | `resolveIncident` | — |

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

- 下游路由：`navigateTo` → `/pages/login/index:dynamic`（js:374）
- 本地存储：`getStorageSync` `auth_token`（JS:350）、`getStorageSync` `auth_user`（JS:354）、`removeStorageSync` `auth_token`（JS:380）、`removeStorageSync` `auth_user`（JS:381）
- WXML 数据绑定：`runtime`、`errorMessage`、`notice`、`loading`、`productionGate`、`productionGateChecks`、`item`、`cases`、`selectedCaseIndex`、`incidentCategoryOptions`、`incidentCategoryIndex`、`incidentDescription`、`requestedResolution`、`saving`、`isReviewRole`、`reviews`、`selectedReview`、`reviewDimensions`、`statusOptions`、`index`、`remediationSummary`、`incidents`、`selectedIncident`、`impactSummary`、`resolutionActionOptions`、`resolutionActionIndex`、`resolutionSummary`
- 条件状态：`loading`、`runtime`、`errorMessage`、`notice`、`productionGate`、`isReviewRole`、`reviews`、`selectedReview`、`item`、`incidents`、`selectedIncident`
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
- 源码指纹：`b73fbddfc947a334b2028e20adf5c52ba37a10958e22b4720786befe4f284b9b`
- 核对文件：`apps/miniprogram/pages/growth-dashboard/index.wxml`、`apps/miniprogram/pages/growth-dashboard/index.wxss`、`apps/miniprogram/pages/growth-dashboard/index.js`、`apps/miniprogram/pages/growth-dashboard/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/relationship-growth/index`、`pages/profile/index`
- 页面组件：`page-state` → `/components/page-state/index`、`status-pill` → `/components/status-pill/index`、`timeline-record` → `/components/timeline-record/index`、`growth-segment` → `/components/growth-segment/index`
- 主要可见内容：我的成长、四类线索分别查看，不合成总分、现在可以做什么、记录一件小事、查看练习、情绪温度、1—10分，只与同一量尺的记录比较、记录与练习时间线、只呈现做过的事情，不把次数写成改善、支持性测评、每份量表独立成组，不把不同分值放在同一条曲线上、只在同一量尺再次填写后观察变化，不自动解释好坏。、关系探索单独呈现、不与日记次数或测评分值合并、探索任务、连续记录、阶段报告、关系探索时间线、这里只显示任务、连续记录和阶段报告的事实、共同核对、研究者反馈 条、打开消息列表

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | 重新读取成长线索 | `bindaction` | `loadGrowth` | — |
| 13 | — | `bindchange` | `selectSection` | — |
| 29 | 记录一件小事 | `bindtap` | `startDiary` | — |
| 30 | 查看练习 | `bindtap` | `openTraining` | — |
| 53 | — | `bindaction` | `startDiary` | — |
| 69 | — | `bindaction` | `openAssessment` | — |
| 82 | — | `bindtap` | `openRelationship` | — |
| 103 | 打开消息列表 | `bindtap` | `openMessages` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 64 | `getGrowthOverview` | `GET` | `/api/growth/overview` | `backend/app.py`、`backend/routes/feedback.py`、`backend/routes/general_growth.py`、`backend/routes/product_events.py`、`backend/routes/relationship_pilot_routes.py`、`backend/scripts/enrich_task17_programs.py`、`backend/scripts/generate_task33_ux_registry.py`、`backend/scripts/generate_task34_operations_registry.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index`（js:108）、`switchTab` → `/pages/training/index`（js:112）、`navigateTo` → `/pages/assessment/index`（js:116）、`navigateTo` → `/pages/relationship-pilot/index`（js:121）、`navigateTo` → `/pages/relationship-growth/index?detail=1&enrollment_id=:dynamic`（js:124）、`navigateTo` → `/pages/messages/index`（js:130）、`navigateTo` → `/pages/login/index:dynamic`（js:159）
- 本地存储：`getStorageSync` `auth_token`（JS:135）、`getStorageSync` `auth_user`（JS:139）、`removeStorageSync` `auth_token`（JS:165）、`removeStorageSync` `auth_user`（JS:166）
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
- 源码指纹：`ae91d9d58de693bf4daf0bb4e058fb1f25b25b179938e397c835481902bc6421`
- 核对文件：`apps/miniprogram/pages/relationship-narrative/index.wxml`、`apps/miniprogram/pages/relationship-narrative/index.wxss`、`apps/miniprogram/pages/relationship-narrative/index.js`、`apps/miniprogram/pages/relationship-narrative/index.json`
- 上游页面：`pages/message-detail/index`
- 页面组件：—
- 主要可见内容：关系探索手记、起点画像、一起讨论的问题、线上任务材料、研究者备注、下一步项目任务

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
- 本地存储：—
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

#### 2026-08-29 第二阶段人工冻结（情感计算与网络分析）

- 页面目标不变：研究者按授权查看单个参与者档案；新增内容放在既有“参与者”工作区，不另开一套研究后台。
- 唯一新增任务：选择“情绪与互动线索”标签，按需读取 `GET /api/research/participants/:user_id/modules/exploratory_analysis`。
- 可见数据仅包含参与者本人结构化情绪标签、强度、场景及场景—情绪共现；不返回日记原文、他人记录、中心性、关系质量或诊断判断。
- 状态矩阵：`available` 展示情绪分布与共现线索；`insufficient` 展示至少 5 条记录门槛；`withheld` 展示人工支持提示；`ineligible` 展示仅成人第二阶段开放。
- 信息优先级：可用状态/暂缓原因 > 记录数与方法边界 > 情绪条目 > 场景—情绪共现；保持既有档案标签、卡片和边界文案视觉语法。
- 2026-08-29 开放第二阶段研究资料查看：在同一“在线分析”工作区增加已审核知识库只读检索、情感/网络合成基准运行摘要和网络隐私阈值；仅研究者、督导、管理员可见，不开放参与者自由问答、外部模型或真实群体网络数据。
- 在线分析仍按“运行护栏 → 已审核资料 → 模型质量 → 任务明细”四组展示；移除重复的顶部阅读顺序和数字编号，组名直接承担导航。
- 本轮继续收敛可见硬编码文案：页面标题改为“研究者工作台”，删除加载实现、Web 重复说明、并发实现术语和重复权限说明；保留动态状态、恢复动作、隐私阈值与安全边界。
- 成人低风险治疗性评估继续沿用既有单人、非紧急、低风险入口；L1/L2 仅记录范围筛查并进入真人责任链，未成年人和多人入口保持关闭。
- 2026-08-30 四项强化：评估证据显示授权范围内的来源与未知项摘要；知识库区分有效/撤回内容并显示检索覆盖、适用范围和有效期；情感计算显示结构化情绪摘要与影子复核原因；网络分析显示本人共现覆盖和合成群体敏感性范围。
- 网络基准区只列`network`运行，不再混入情感基准；所有新增摘要均为派生只读信息，不新增自由问答、个体中心性、关系质量、诊断或生产发布能力。

- 真值状态：`auto_evidence_complete`
- 源码指纹：`ef8f074e3b5980c5c40e4d19afc150cf5d9f7ce3649dcd1f7d57cfc930ce5414`
- 核对文件：`apps/miniprogram/pages/researcher-dashboard/index.wxml`、`apps/miniprogram/pages/researcher-dashboard/index.wxss`、`apps/miniprogram/pages/researcher-dashboard/index.js`、`apps/miniprogram/pages/researcher-dashboard/index.json`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/errorDiagnostics.js`
- 上游页面：`pages/profile/index`
- 页面组件：—
- 主要可见内容：研究者工作台、最近同步、重新同步、工作区边界、离线与开发模式提示、身份与能力矩阵、加载/错误/局部失败状态、参与者最小摘要与档案标签、评估证据、在线分析四组（运行护栏、已审核资料、模型质量、任务明细）、知识库检索、情感与网络合成基准、隐私阈值、试点项目和人工交付操作。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 7 | 刷新当前工作区 | `bindtap` | `refreshActiveWorkspace` | — |
| 29 | — | `bindtap` | `switchWorkspace` | {'id': '{{item.id}}'} |
| 41 | 重新同步 | `bindtap` | `loadWorkbench` | — |
| 42 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | {'scope': 'workbench'} |
| 49 | 重试未完成同步 | `bindtap` | `loadWorkbench` | — |
| 105 | 刷新待处理列表 | `bindtap` | `loadWorkbench` | — |
| 121 | 继续查看 | `bindtap` | `showMorePending` | — |
| 133 | 搜索参与者 | `bindinput` | `onParticipantQueryInput` | — |
| 142 | 重新加载 | `bindtap` | `retryParticipants` | — |
| 143 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | {'scope': 'participants'} |
| 155 | 查看{{item.displayName}}的参与者档案 | `bindtap` | `selectParticipantDossier` | {'id': '{{item.user_id}}'} |
| 164 | 加载下一页 | `bindtap` | `loadMoreParticipants` | — |
| 173 | 关闭参与者档案 | `bindtap` | `closeParticipantDossier` | — |
| 176 | — | `bindtap` | `loadParticipantModule` | {'key': '{{item.key}}'} |
| 204 | 加载下一页 | `bindtap` | `loadParticipantModule` | {'key': '{{participantModule.module}}', 'page': '{{participantModule.page + 1}}'} |
| 227 | 进入试点项目 | `bindtap` | `switchWorkspace` | {'id': 'pilots'} |
| 238 | 刷新 | `bindtap` | `loadAssessmentCases` | — |
| 242 | — | `bindtap` | `selectAssessmentCase` | {'id': '{{item.id}}'} |
| 247 | 重新加载 | `bindtap` | `loadAssessmentCases` | — |
| 265 | 类型： | `bindchange` | `onAssessmentFilter` | {'key': 'kind'} |
| 268 | 权限： | `bindchange` | `onAssessmentFilter` | {'key': 'visibility'} |
| 298 | — | `bindinput` | `onAssessmentDraftInput` | {'key': 'assessmentInternalNotes'} |
| 303 | — | `bindinput` | `onAssessmentDraftInput` | {'key': 'assessmentParticipantDraft'} |
| 305 | 保存工作台草稿 | `bindtap` | `saveAssessmentDraft` | — |
| 307 | 进入质量抽检与修复 | `bindtap` | `openAssessmentQuality` | — |
| 319 | 刷新 | `bindtap` | `loadAnalysisJobs` | — |
| 376 | 检索输入 | `bindinput` | `onKnowledgeQueryInput` | — |
| 377 | 检索方式 | `bindchange` | `onKnowledgeMethodChange` | — |
| 380 | 检索已审核内容 | `bindtap` | `searchKnowledge` | — |
| 437 | 重新加载 | `bindtap` | `loadAnalysisJobs` | — |
| 468 | 重新同步 | `bindtap` | `loadWorkbench` | — |
| 482 | 重新加载 | `bindtap` | `loadDashboard` | — |
| 483 | 复制诊断信息 | `bindtap` | `copyDiagnostic` | {'scope': 'pilot'} |
| 493 | · | `bindtap` | `selectEnrollment` | {'id': '{{item.id}}'} |
| 515 | 查看 | `bindtap` | `openReport` | — |
| 516 | 人工确认 | `bindtap` | `confirmReport` | — |
| 517 | 发送用户 | `bindtap` | `sendReport` | — |
| 520 | 生成报告 | `bindtap` | `createReport` | — |
| 528 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'observation'} |
| 532 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'evidence'} |
| 536 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'nextStep'} |
| 540 | — | `bindinput` | `onStageFeedbackInput` | {'key': 'openQuestion'} |
| 556 | 生成并核对预览 | `bindtap` | `previewStageFeedback` | — |
| 557 | 确认这个版本 | `bindtap` | `runDeliveryStep` | {'kind': 'stage', 'action': 'confirm'} |
| 558 | 发送到参与者消息 | `bindtap` | `runDeliveryStep` | {'kind': 'stage', 'action': 'send'} |
| 565 | — | `bindinput` | `onMessageTitleInput` | — |
| 566 | — | `bindinput` | `onMessageBodyInput` | — |
| 580 | 生成并核对预览 | `bindtap` | `previewParticipantMessage` | — |
| 581 | 确认这个版本 | `bindtap` | `runDeliveryStep` | {'kind': 'message', 'action': 'confirm'} |
| 582 | 发送到参与者消息 | `bindtap` | `runDeliveryStep` | {'kind': 'message', 'action': 'send'} |
| 600 | — | `bindinput` | `onNoteInput` | — |
| 601 | 保存备注 | `bindtap` | `saveNote` | — |
| 606 | 生成探索手记草稿 | `bindtap` | `draftNarrative` | — |
| 610 | 确认后交付用户 | `bindtap` | `confirmNarrative` | — |

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
| 487 | `getAiKnowledgeInventory` | `GET` | `/api/ai-qa/knowledge` | `backend/app.py`、`backend/routes/ai_qa.py`、`backend/services/ai_qa_retrieval_service.py` |
| 488 | `getGroupNetworkAnalysisPolicy` | `GET` | `/api/research/benchmarks/network-policy` | `backend/app.py`、`backend/routes/offline_benchmarks.py`、`backend/services/group_network_analysis_service.py` |
| 489 | `listOfflineBenchmarkRuns` | `GET` | `/api/research/benchmarks/runs` | `backend/app.py`、`backend/routes/offline_benchmarks.py`、`backend/services/offline_benchmark_service.py` |
| 558 | `retrieveAiKnowledge` | `GET` | `/api/ai-qa/knowledge/retrieve` | `backend/app.py`、`backend/routes/ai_qa.py`、`backend/services/ai_qa_retrieval_service.py` |
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

- 下游路由：`navigateTo` → `/pages/therapeutic-assessment-quality/index`（js:392）、`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:748）、`navigateTo` → `/pages/relationship-report/index?id=:dynamic`（js:752）、`navigateTo` → `/pages/login/index:dynamic`（js:902）
- 本地存储：`getStorageSync` `this`（JS:701）、`setStorageSync` `this`（JS:707）、`removeStorageSync` `this`（JS:710）、`getStorageSync` `auth_token`（JS:878）、`getStorageSync` `auth_user`（JS:882）、`removeStorageSync` `auth_token`（JS:908）、`removeStorageSync` `auth_user`（JS:909）
- WXML 数据绑定：`lastSyncText`、`offline`、`developmentFullAccess`、`capabilityScope`、`workspaces`、`activeWorkspace`、`item`、`loading`、`errorMessage`、`errorDiagnostic`、`partialFailures`、`index`、`assessmentQueueRuntime`、`assessmentDutyShifts`、`publicationCandidateSummary`、`assessmentLifecycleSummary`、`pendingTotal`、`urgentCount`、`operations`、`pendingVisibleItems`、`pendingHasMore`、`participantQuery`、`participantError`、`participantDiagnostic`、`participantLoading`、`participantItems`、`participantHasMore`、`participantDossier`、`participantModule`、`participantModuleLoading`、`record`、`line`、`assessmentCases`、`assessmentCaseId`、`assessmentError`、`assessmentLoading`、`assessmentWorkbench`、`assessmentAuthorization`、`assessmentFilters`、`assessmentInternalNotes`、`assessmentParticipantDraft`、`assessmentSaving`、`analysisCatalog`、`analysisResilience`、`affectModelVersions`、`affectShadowRuns`、`affectShadowReviewCount`、`affectMonitoring`、`affectReleaseGate`、`analysisLoading`、`analysisError`、`analysisJobs`、`pilotLoading`、`pilotError`、`pilotDiagnostic`、`items`、`selected`、`stageFeedbackForm`、`stageFeedbackDelivery`、`sendingFeedback`、`messageTitle`、`messageBody`、`participantMessageDelivery`、`sendingMessage`、`answer`、`note`、`narrative`
- 条件状态：`offline`、`developmentFullAccess`、`capabilityScope`、`loading`、`errorMessage`、`partialFailures`、`activeWorkspace`、`assessmentQueueRuntime`、`publicationCandidateSummary`、`assessmentLifecycleSummary`、`pendingVisibleItems`、`pendingHasMore`、`participantError`、`participantLoading`、`participantItems`、`participantHasMore`、`participantDossier`、`participantModuleLoading`、`participantModule`、`assessmentCases`、`assessmentError`、`assessmentLoading`、`assessmentWorkbench`、`item`、`analysisCatalog`、`analysisResilience`、`affectShadowRuns`、`affectMonitoring`、`affectReleaseGate`、`analysisLoading`、`analysisError`、`analysisJobs`、`pilotLoading`、`pilotError`、`items`、`selected`、`stageFeedbackDelivery`、`participantMessageDelivery`、`narrative`
- `setData` 状态：`developmentFullAccess`、`activeWorkspace`、`capabilityScope`、`workspaces`、`loading`、`errorMessage`、`offline`、`assessmentLoading`、`assessmentError`、`assessmentCases`、`assessmentCaseId`、`assessmentWorkbench`、`case`、`sharedScopeText`、`evidence_items`、`assessmentInternalNotes`、`assessmentParticipantDraft`、`assessmentAuthorization`、`assessmentFilters`、`assessmentSaving`、`analysisLoading`、`analysisError`、`analysisJobs`、`analysisLabel`、`statusLabel`、`createdText`、`qualityText`、`suppressed`、`errorDiagnostic`、`partialFailures`、`pendingItems`、`pendingTotal`、`pendingVisibleItems`、`pendingPage`、`pendingHasMore`、`urgentCount`、`assessmentQueueRuntime`、`assessmentDutyShifts`、`publicationCandidateSummary`、`approved`、`published`、`assessmentLifecycleSummary`、`lastSyncText`、`operations`、`participantQuery`、`participantError`、`participantLoading`、`participantDiagnostic`、`participantItems`、`participantPage`、`participantHasMore`、`participantDossier`、`participantModule`、`participantModuleLoading`、`items`、`pilotLoading`、`pilotError`、`pilotDiagnostic`、`selected`、`narrative`、`note`、`messageTitle`、`messageBody`、`stageFeedbackForm`、`evidence`、`nextStep`、`openQuestion`、`stageFeedbackDelivery`、`participantMessageDelivery`、`icon`、`sendingFeedback`、`sendingMessage`
- 新增只读开放状态：`knowledgeInventory`、`knowledgeDocumentCount`、`knowledgeQuery`、`knowledgeMethod`、`knowledgeMethodText`、`knowledgeResult`、`knowledgeLoading`、`knowledgeError`、`networkPolicy`、`offlineBenchmarkRuns`；检索和刷新失败均保持当前工作台可用。
- 2026-08-30 增量派生状态：`evidence_summary`、`retrieval_summary`、`affectSummary`、`shadowSummaryText`、`reviewReasonText`、`networkSummary`、`networkSummaryText`、`networkDetailText`；只用于简化阅读，不改变写入、复核或发布门禁。
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 34：课程 `pages/course/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`30e4b2d32d20cc7b2f9ceba9fec77d84ebd1e00502f69881c2ce06c248e6faba`
- 核对文件：`apps/miniprogram/pages/course/index.wxml`、`apps/miniprogram/pages/course/index.wxss`、`apps/miniprogram/pages/course/index.js`、`apps/miniprogram/pages/course/index.json`
- 上游页面：`pages/login/index`
- 页面组件：`section-title` → `/components/section-title/index`、`course-card` → `/components/course-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：课程、本周已查看 小节、重新加载、正在读取课程内容...

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 20 | — | `bindtap` | `selectCategory` | {'category': '{{item}}'} |
| 36 | 重新加载 | `bindtap` | `retryLoadCourses` | — |
| 49 | — | `bindtapcard` | `openCourse` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 37 | `listCourses` | `GET` | `/api/courses` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_courses.py`、`backend/scripts/generate_task34_operations_registry.py`、`backend/services/content_governance_service.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/course-detail/index?id=:dynamic`（js:76）
- 本地存储：—
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
- 源码指纹：`2ac3bdf117123cf1156806a4c3d28c78bc324dda79c9fe6d3e8fdedc6ca0d4cb`
- 核对文件：`apps/miniprogram/pages/course-detail/index.wxml`、`apps/miniprogram/pages/course-detail/index.wxss`、`apps/miniprogram/pages/course-detail/index.js`、`apps/miniprogram/pages/course-detail/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/course/index`
- 页面组件：`section-title` → `../../components/section-title/index`
- 主要可见内容：正在读取课程内容...、重新加载、· · 小节、容易误解、可以这样理解、完整示例、常见反例、真实场景迁移、练习后想一想、关联训练卡、去训练页、记录本次学习、完成表示已经阅读并尝试理解检查，不代表掌握程度或心理状态改善。、记录课程完成

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 8 | 重新加载 | `bindtap` | `retryLoadCourse` | — |
| 63 | — | `bindtap` | `chooseKnowledgeAnswer` | {'check-id': '{{check.id}}', 'value': '{{option.value}}'} |
| 82 | 去训练页 | `bindtap` | `goTraining` | — |
| 90 | 记录课程完成 | `bindtap` | `markCourseComplete` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 39 | `getCourse` | `GET` | `/api/courses/:id` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/progress_summary.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_content.py`、`backend/scripts/enrich_task17_courses.py` |
| 77 | `getCourseProgress` | `GET` | `/api/courses/:id/progress` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/progress_summary.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_content.py`、`backend/scripts/enrich_task17_courses.py` |
| 98 | `saveCourseProgress` | `POST` | `/api/courses/:id/progress` | `backend/app.py`、`backend/routes/content_review.py`、`backend/routes/courses.py`、`backend/routes/progress_summary.py`、`backend/routes/showcase_access.py`、`backend/scripts/audit_task17_content.py`、`backend/scripts/enrich_task17_content.py`、`backend/scripts/enrich_task17_courses.py` |

#### 路由、本地状态与页面状态

- 下游路由：`switchTab` → `/pages/training/index`（js:114）、`navigateTo` → `/pages/login/index:dynamic`（js:143）
- 本地存储：`getStorageSync` `auth_token`（JS:119）、`getStorageSync` `auth_user`（JS:123）、`removeStorageSync` `auth_token`（JS:149）、`removeStorageSync` `auth_user`（JS:150）
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
- 源码指纹：`de0a0b5cc029d3dc6549e90f4ef18f0a1a6ea4f01b51f2e24ce84e055c43935b`
- 核对文件：`apps/miniprogram/pages/profile/index.wxml`、`apps/miniprogram/pages/profile/index.wxss`、`apps/miniprogram/pages/profile/index.js`、`apps/miniprogram/pages/profile/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/login/index`
- 页面组件：`section-title` → `/components/section-title/index`、`function-entry-card` → `/components/function-entry-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`alert-card` → `/components/alert-card/index`
- 主要可见内容：我的登录后，你的记录只会用于本工具内的复盘、训练建议和必要的人工补充反馈。、退出登录、去登录、注册账号、登录方式、只显示连接状态，不显示身份值、微信登录、撤销、手机号登录、撤销登录方式会退出所有设备，但不会删除你的记录。、可找回、把本机试用记录放进当前账号、找到 条本机试用记录。确认后，测评、日记和练习记录会归到当前账号；暂不处理也不会删除。、确认合并、暂不处理、如果出现紧急安全风险、请先联系身边可信赖的人、学校老师、当地紧急医疗或心理危机支持。本小程序不能提供实时危机干预。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 18 | 退出登录 | `bindtap` | `doLogout` | — |
| 21 | 去登录 | `bindtap` | `goLogin` | — |
| 22 | 注册账号 | `bindtap` | `goRegister` | — |
| 34 | 撤销 | `bindtap` | `requestIdentityUnbind` | {'identity': 'wechat'} |
| 41 | 撤销 | `bindtap` | `requestIdentityUnbind` | {'identity': 'phone'} |
| 56 | 确认合并 | `bindtap` | `confirmDataClaim` | — |
| 57 | 暂不处理 | `bindtap` | `dismissDataClaim` | — |
| 66 | — | `bindtap` | `goResearcher` | — |
| 72 | — | `bindtap` | `openEntry` | {'group': 'recordEntries', 'index': '{{index}}'} |
| 85 | — | `bindtap` | `openEntry` | {'group': 'supportEntries', 'index': '{{index}}'} |
| 102 | — | `bindtap` | `openEntry` | {'group': 'safetyEntries', 'index': '{{index}}'} |
| 115 | — | `bindtap` | `openEntry` | {'group': 'settingsEntries', 'index': '{{index}}'} |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 147 | `getShowcaseAccess` | `GET` | `/api/showcase-access` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 148 | `getDataClaimPreview` | `GET` | `/api/auth/data-claim-preview` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 149 | `getIdentityStatus` | `GET` | `/api/auth/identity-status` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 150 | `getAiQaConfig` | `GET` | `/api/ai-qa/config` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 161 | `getProfileStats` | `GET` | `/api/profile/stats` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 260 | `claimAnonymousData` | `POST` | `/api/auth/data-claim` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 286 | `unbindIdentity` | `POST` | `/api/auth/identity-unbind` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/assessments.py`、`backend/routes/auth.py` |
| 303 | `logout` | `POST` | `/api/auth/logout` | `backend/routes/auth.py`；先请求服务端撤销账号全部令牌，再清本地。弱网失败时仅保存不含 Token 的 `safehome_pending_logout`，下次同账号登录完成撤销。 |

#### 路由、本地状态与页面状态

- 下游路由：`switchTab` → `/pages/login/index?redirect=%2Fpages%2Fprofile%2Findex`（js:225）、`navigateTo` → `/pages/register/index?redirect=%2Fpages%2Fprofile%2Findex`（js:236）、`navigateTo` → `/pages/researcher-dashboard/index`（js:242）、`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fresearcher-dashboard%2Findex`（js:245）、`redirectTo` → `/pages/login/index?redirect=%2Fpages%2Fprofile%2Findex`（js:290）、`navigateTo` → `/pages/login/index:dynamic`（js:338）
- 本地存储：`getStorageSync` `safehome_dismissed_data_claim_id`（JS:156）、`setStorageSync` `safehome_dismissed_data_claim_id`（JS:250）、`removeStorageSync` `safehome_dismissed_data_claim_id`（JS:261）、`getStorageSync` `auth_token`（JS:314）、`getStorageSync` `auth_user`（JS:318）、`removeStorageSync` `auth_token`（JS:344）、`removeStorageSync` `auth_user`（JS:345）
- WXML 数据绑定：`user`、`loggedIn`、`identityStatus`、`identityBusy`、`logoutBusy`、`dataClaim`、`item`、`claimBusy`、`isResearcher`、`recordEntries`、`index`、`supportEntries`、`safetyEntries`、`settingsEntries`
- 条件状态：`user`、`loggedIn`、`identityStatus`、`dataClaim`
- `setData` 状态：`user`、`loginState`、`streakText`、`growthLevel`、`roleText`、`isResearcher`、`showcaseAccess`、`stats`、`loggedIn`、`dataClaim`、`identityStatus`、`supportEntries`、`nickname`、`claimBusy`、`identityBusy`、`logoutBusy`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 37：设置与说明 `pages/settings-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`8f24c6780057ba5fa91f9072fcad95f36fea4cb865384cb7d85540e20cfa4ffd`
- 核对文件：`apps/miniprogram/pages/settings-detail/index.wxml`、`apps/miniprogram/pages/settings-detail/index.wxss`、`apps/miniprogram/pages/settings-detail/index.js`、`apps/miniprogram/pages/settings-detail/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`、`pages/login/index`、`pages/profile/index`
- 页面组件：`section-title` → `/components/section-title/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`page-state` → `/components/page-state/index`、`status-pill` → `/components/status-pill/index`
- 主要可见内容：重新读取、学生保护状态、请选择符合你的年龄范围。系统不会要求填写出生日期。、我已满14周岁、我未满14周岁、请向家长获取10位绑定码。完成绑定后，仍需家长单独确认是否同意受保护的数据处理。、完成家长绑定、已完成家长账号绑定，正在等待监护人确认。绑定关系本身不等于监护人同意。、监护人已经同意，但你自己仍可以决定是否继续使用测评、研究参与、自由文本和画像等受保护功能。、我愿意继续、我暂时不继续、参与者本人或监护人已经拒绝/撤回，受保护功能已暂停。需要再次继续时，应重新完成相应确认。、未满14周岁保护条件已经满足。监护人和学生本人仍可撤回。、我想暂停受保护功能、年龄范围已确认，本账号不需要未满14周岁的监护人数据处理门禁。、家长绑定与监护人确认、先生成绑定码给学生。学生完成绑定后，如果其年龄为未满14周岁，你可以在下方单独同意或撤回受保护的数据处理。、生成10位绑定码、绑定码：、有效期至：、绑定码只用于建立家庭账号关系，不代表已经同意敏感数据处理。、已绑定学生、关系：、年龄范围：未满14周岁

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 27 | — | `bindaction` | `goProtectionLogin` | — |
| 39 | 重新读取 | `bindtap` | `loadProtectionStatus` | — |
| 50 | 我已满14周岁 | `bindtap` | `chooseAge` | {'age': '14_or_over'} |
| 51 | 我未满14周岁 | `bindtap` | `chooseAge` | {'age': 'under_14'} |
| 56 | 完成家长绑定 | `bindinput` | `onBindCodeInput` | — |
| 64 | 完成家长绑定 | `bindtap` | `submitStudentBinding` | — |
| 73 | 我愿意继续 | `bindtap` | `updateChildDecision` | {'assented': 'true'} |
| 74 | 我暂时不继续 | `bindtap` | `updateChildDecision` | {'assented': 'false'} |
| 83 | 我想暂停受保护功能 | `bindtap` | `updateChildDecision` | {'assented': 'false'} |
| 94 | 生成10位绑定码 | `bindtap` | `createGuardianBindCode` | — |
| 113 | 同意受保护数据处理 | `bindtap` | `updateGuardianDecision` | {'child': '{{item.student_user_id}}', 'agreed': 'true'} |
| 121 | 撤回监护人同意 | `bindtap` | `updateGuardianDecision` | {'child': '{{item.student_user_id}}', 'agreed': 'false'} |
| 145 | 删除申请< | `bindaction` | `handlePrivacyStateAction` | — |
| 164 | 取消申请 | `bindtap` | `cancelPrivacyRequest` | {'id': '{{item.id}}'} |
| 171 | 补充说明并重新提交 | `bindtap` | `appealPrivacyRequest` | {'id': '{{item.id}}'} |
| 188 | — | `bindtap` | `submitPrivacyDeleteRequest` | — |
| 198 | 返回 | `bindtap` | `goBack` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 343 | `listPrivacyRequests` | `GET` | `/api/privacy/requests` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |
| 375 | `createPrivacyDeleteRequest` | `POST` | `/api/privacy/delete-my-data` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |
| 399 | `cancelPrivacyRequest` | `POST` | `/api/privacy/requests` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |
| 429 | `appealPrivacyRequest` | `POST` | `/api/privacy/requests` | `backend/app.py`、`backend/database.py`、`backend/gunicorn.conf.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/consent.py`、`backend/routes/privacy.py`、`backend/routes/profile.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprivacy`（js:443）、`navigateTo` → `/pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprotection`（js:450）、`navigateTo` → `/pages/login/index:dynamic`（js:483）
- 本地存储：`getStorageSync` `auth_token`（JS:459）、`getStorageSync` `auth_user`（JS:463）、`removeStorageSync` `auth_token`（JS:489）、`removeStorageSync` `auth_user`（JS:490）
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
- 源码指纹：`db4ce43b532222801ec2952ef8cba8d5bdbef727a3ded3af6bdb8b922e4cfa48`
- 核对文件：`apps/miniprogram/pages/goal-setting/index.wxml`、`apps/miniprogram/pages/goal-setting/index.wxss`、`apps/miniprogram/pages/goal-setting/index.js`、`apps/miniprogram/pages/goal-setting/index.json`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/home/index`
- 页面组件：—
- 主要可见内容：本周小目标、高频亲子冲突场景、希望减少的旧反应、希望练习的新反应、本周 SMART 小目标、网络响应较慢；草稿仍在本机，请不要重复点击。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 13 | — | `bindtap` | `selectScene` | {'value': '{{item}}'} |
| 23 | — | `bindinput` | `onTextInput` | {'key': 'customScene'} |
| 32 | — | `bindtap` | `selectOldReaction` | {'value': '{{item}}'} |
| 50 | — | `bindtap` | `selectNewReaction` | {'value': '{{item}}'} |
| 67 | — | `bindinput` | `onTextInput` | {'key': 'smartGoal'} |
| 83 | — | `bindtap` | `submitGoal` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 85 | `createGoal` | `POST` | `/api/goals` | `backend/app.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/goals.py`、`backend/scripts/generate_task33_ux_registry.py`、`backend/scripts/generate_task34_operations_registry.py`、`backend/scripts/migrate_task33_ux_governance.py`、`backend/scripts/verify_privacy_restore.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index?goal_id=:dynamic`（js:100）
- 本地存储：`getStorageSync` `storageKey`（JS:137）、`setStorageSync` `storageKey`（JS:159）、`removeStorageSync` `storageKey`（JS:189）
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
- 源码指纹：`3ee59be146b83a6673fc071d83a1607d37f7de86b6346576837fa99f15e46f5f`
- 核对文件：`apps/miniprogram/pages/diary-form/index.wxml`、`apps/miniprogram/pages/diary-form/index.wxss`、`apps/miniprogram/pages/diary-form/index.js`、`apps/miniprogram/pages/diary-form/index.json`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/home/index`、`pages/getting-started/index`、`pages/growth-dashboard/index`、`pages/goal-setting/index`、`pages/diary-history/index`、`pages/feedback-result/index`、`pages/training-card/index`
- 页面组件：—
- 主要可见内容：记录情绪事件、已关联本周小目标、请不要填写姓名、学校、电话等可识别身份的信息。、发生了什么、其他场景、具体经过、我和孩子当时的感受、家长当时的主要情绪、强度 / 10、孩子当时看起来的情绪、想法与做法（可选）、当时心里的第一反应、我当时的做法、身体与后续（可选）、身体感觉、孩子后来的反应、当下结果、我担心的长期影响、网络响应较慢，请保持页面打开；草稿仍在本机，不需要重复填写。、保存后会进入支持性反馈和训练卡推荐。反馈只用于观察和练习，不做诊断。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 18 | — | `bindtap` | `selectScene` | {'value': '{{item}}'} |
| 30 | — | `bindinput` | `onTextInput` | {'key': 'customScene'} |
| 34 | — | `bindinput` | `onTextInput` | {'key': 'eventDescription'} |
| 53 | — | `bindtap` | `selectParentEmotion` | {'value': '{{item}}'} |
| 65 | — | `bindchange` | `onParentIntensityChange` | — |
| 72 | — | `bindtap` | `selectChildEmotion` | {'value': '{{item}}'} |
| 84 | — | `bindchange` | `onChildIntensityChange` | — |
| 89 | — | `bindtap` | `toggleMoreFields` | — |
| 101 | — | `bindinput` | `onTextInput` | {'key': 'automaticThought'} |
| 111 | — | `bindinput` | `onTextInput` | {'key': 'behavior'} |
| 130 | — | `bindtap` | `selectBodySensation` | {'value': '{{item}}'} |
| 140 | — | `bindinput` | `onTextInput` | {'key': 'bodySensationNote'} |
| 144 | — | `bindinput` | `onTextInput` | {'key': 'childReaction'} |
| 154 | — | `bindinput` | `onTextInput` | {'key': 'shortTermResult'} |
| 164 | — | `bindinput` | `onTextInput` | {'key': 'longTermImpact'} |
| 184 | — | `bindtap` | `submitDiary` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 133 | `createDiary` | `POST` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py`、`backend/routes/general_growth.py`、`backend/routes/minor_safeguards.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/feedback-result/index?diary_id=:dynamic`（js:150）、`navigateTo` → `/pages/login/index:dynamic`（js:189）
- 本地存储：`getStorageSync` `auth_token`（JS:165）、`getStorageSync` `auth_user`（JS:169）、`removeStorageSync` `auth_token`（JS:195）、`removeStorageSync` `auth_user`（JS:196）、`getStorageSync` `storageKey`（JS:238）、`setStorageSync` `storageKey`（JS:260）、`removeStorageSync` `storageKey`（JS:290）
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

### 40：情绪记录 `pages/diary-history/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`82a271fecf256d0f2740bca695dd0103399c00cde0b68b674cf0249af478d435`
- 核对文件：`apps/miniprogram/pages/diary-history/index.wxml`、`apps/miniprogram/pages/diary-history/index.wxss`、`apps/miniprogram/pages/diary-history/index.js`、`apps/miniprogram/pages/diary-history/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`
- 页面组件：`bamboo-timeline-node` → `/components/bamboo-timeline-node/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：情绪记录、记录一件事、这里只展示已经保存的记录，用于支持性观察，不替代专业诊断。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 14 | 重新加载情绪记录 | `bindaction` | `retry` | — |
| 51 | 记录一件事 | `bindtap` | `startDiary` | — |
| 54 | 新建一条情绪事件记录 | `bindaction` | `startDiary` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 79 | `listDiaries` | `GET` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py`、`backend/routes/general_growth.py`、`backend/routes/minor_safeguards.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index`（js:103）、`navigateTo` → `/pages/login/index:dynamic`（js:132）
- 本地存储：`getStorageSync` `auth_token`（JS:108）、`getStorageSync` `auth_user`（JS:112）、`removeStorageSync` `auth_token`（JS:138）、`removeStorageSync` `auth_user`（JS:139）
- WXML 数据绑定：`loading`、`errorMessage`、`errorTitle`、`records`、`item`、`mark`
- 条件状态：`loading`、`errorMessage`、`records`
- `setData` 状态：`loading`、`errorMessage`、`errorTitle`、`errorKind`、`records`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 41：本次反馈 `pages/feedback-result/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`d87f410fff679b09341ca1acc4c741ada410ab9cc9835a843379497d5ff76b79`
- 核对文件：`apps/miniprogram/pages/feedback-result/index.wxml`、`apps/miniprogram/pages/feedback-result/index.wxss`、`apps/miniprogram/pages/feedback-result/index.js`、`apps/miniprogram/pages/feedback-result/index.json`
- 上游页面：`pages/diary-form/index`
- 页面组件：`section-title` → `/components/section-title/index`、`training-task-card` → `/components/training-task-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`
- 主要可见内容：本次反馈、先接住这次感受、主要情绪、情绪强度、优先联系现实支持、这里不是实时危机服务，也不替代线下专业支持或当地紧急服务。、查看安全指引、提交人工关注、主练习 ·、推荐理由：、开始这个练习、今天先做、这次记录暂时没有匹配到具体训练卡，可以先暂停几秒，再说出一个最明显的感受。、今日建议只作为支持性练习参考，不构成诊断或治疗方案。、也可以选择、需要多一个人帮你看一看？、如果这类情况反复出现，或你担心自己撑不住，可以提交给人工督导补充反馈。、提交督导、收藏这次反馈、怎样理解这份反馈、它只整理这一次记录中可观察的情绪、互动和练习位置，不代表固定问题，也不构成诊断、评分或治疗建议。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 10 | 先接住这次感受 | `bindaction` | `handleFeedbackStateAction` | — |
| 19 | — | `bindselect` | `submitFeedbackEvaluation` | — |
| 59 | 查看安全指引 | `bindtap` | `openEmergencyGuide` | — |
| 60 | 提交人工关注 | `bindtap` | `openSupervision` | — |
| 71 | 开始这个练习 | `bindtap` | `openTrainingCard` | — |
| 102 | 提交督导 | `bindtap` | `openSupervision` | — |
| 106 | 收藏这次反馈 | `bindtap` | `saveFeedback` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 45 | `generateFeedback` | `POST` | `/api/feedback/generate` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py`、`backend/routes/cards.py` |
| 46 | `listCards` | `GET` | `/api/cards` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py`、`backend/routes/cards.py` |
| 209 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/ai_qa.py`、`backend/routes/auth.py`、`backend/routes/auth_utils.py`、`backend/routes/cards.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/diary-form/index`（js:226）、`navigateTo` → `/pages/training-card/index?tags=:dynamic`（js:249）、`navigateTo` → `/pages/supervision/index?diary_id=:dynamic`（js:255）、`navigateTo` → `/pages/emergency-guide/index`（js:261）
- 本地存储：`setStorageSync` `LATEST_TRAINING_RECOMMENDATION_KEY`（JS:178）
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

### 42：家庭关系测一测 `pages/assessment/index`

#### 2026-08-30 可见硬编码文案收敛

- 错误状态不再向普通用户暴露“联调测试页”，改为调用既有 `loadAssessments` 的“重新加载”；长期保留的联调页面和其他开发入口未删除。
- 搜索空结果保留“换一个分类或关键词再看”的可执行提示，删除重复的无结果复述。
- 删除页面底部与当前“选择测评”任务无直接关系的固定鼓励语；筛选、加载、登录、最近记录和内容边界保持不变。

- 真值状态：`auto_evidence_complete`
- 源码指纹：`ff6ab6dc1fb6cd993e92a5d898ce23c7b4107428699453c6a64bfbd11ca16c26`
- 核对文件：`apps/miniprogram/pages/assessment/index.wxml`、`apps/miniprogram/pages/assessment/index.wxss`、`apps/miniprogram/pages/assessment/index.js`、`apps/miniprogram/pages/assessment/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`、`pages/personalized-plan/index`、`pages/relationship-pilot/index`、`pages/growth-dashboard/index`、`pages/assessment-history/index`
- 页面组件：`section-title` → `/components/section-title/index`、`assessment-worksheet-card` → `/components/assessment-worksheet-card/index`、`function-entry-card` → `/components/function-entry-card/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：支持性测评、受众筛选、搜索量表、清除、重新加载、正在读取测一测内容、分类与测评卡、最近记录、查看、去登录

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | — | `bindtap` | `switchAudience` | {'key': '{{item.key}}'} |
| 18 | 搜索量表、主题或关键词 | `bindinput` | `onSearchInput` | — |
| 19 | 清除 | `bindtap` | `clearSearch` | — |
| 26 | 重新加载 | `bindtap` | `loadAssessments` | — |
| 39 | — | `bindopen` | `openAssessmentEntry` | — |
| 52 | 查看测评记录：{{item.worksheet_title}} | `bindtap` | `openRecentResult` | {'id': '{{item.id}}', 'worksheet-id': '{{item.worksheet_id}}'} |
| 77 | 去登录 | `bindtap` | `goLogin` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 46 | `getDebugConfig` | `GET` | — | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/general_growth.py`、`backend/routes/parent_assessments.py` |
| 195 | `listAssessments` | `GET` | `/api/assessments` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/general_growth.py`、`backend/routes/parent_assessments.py` |
| 219 | `listAssessmentResults` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/general_growth.py`、`backend/routes/parent_assessments.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment-detail/index?id=:dynamic`（js:263）、`navigateTo` → `/pages/assessment-result/index?id=:dynamic`（js:272）、`navigateTo` → `/pages/integration-test/index`（js:285）、`navigateTo` → `/pages/login/index:dynamic`（js:314）
- 本地存储：`getStorageSync` `auth_token`（JS:290）、`getStorageSync` `auth_user`（JS:294）、`removeStorageSync` `auth_token`（JS:320）、`removeStorageSync` `auth_user`（JS:321）
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

### 43：全部测评记录 `pages/assessment-history/index`

#### 2026-08-30 可见硬编码文案收敛

- 加载状态只保留“正在读取测评记录”，删除不会改变等待动作的“请稍等一下”。
- 空状态保留“还没有测评记录”和“去测一测”主行动，删除对保存结果的重复说明。
- 记录卡的日期与维度数只在元信息中展示一次，右侧统一为“查看”；没有维度摘要时只显示日期，不再重复“查看完整结果”。

- 真值状态：`auto_evidence_complete`
- 源码指纹：`f5a1dc83458fe58b59622cf4499cefb968e71de99d208f7ab2aabbb8a2e5cdfd`
- 核对文件：`apps/miniprogram/pages/assessment-history/index.wxml`、`apps/miniprogram/pages/assessment-history/index.wxss`、`apps/miniprogram/pages/assessment-history/index.js`、`apps/miniprogram/pages/assessment-history/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/profile/index`
- 页面组件：`assessment-worksheet-card` → `/components/assessment-worksheet-card/index`
- 主要可见内容：测评记录、共、份记录、正在读取测评记录、记录暂时没有加载成功、重新加载、加载更多、已显示全部、查看、还没有测评记录、去测一测

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 16 | 重新加载 | `bindtap` | `retry` | — |
| 20 | — | `bindopen` | `openResult` | — |
| 28 | 加载更多 | `bindtap` | `loadMore` | — |
| 36 | 去测一测 | `bindtap` | `goAssessment` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 70 | `listAssessmentResults` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/general_growth.py`、`backend/routes/profile.py`、`backend/routes/research_workspace.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment-result/index?id=:dynamic`（js:104）、`navigateTo` → `/pages/assessment/index`（js:110）、`navigateTo` → `/pages/login/index:dynamic`（js:139）
- 本地存储：`getStorageSync` `auth_token`（JS:115）、`getStorageSync` `auth_user`（JS:119）、`removeStorageSync` `auth_token`（JS:145）、`removeStorageSync` `auth_user`（JS:146）
- WXML 数据绑定：`total`、`loading`、`errorMessage`、`items`、`item`、`hasMore`、`loadingMore`
- 条件状态：`loading`、`errorMessage`、`items`、`hasMore`
- `setData` 状态：`loading`、`loadingMore`、`errorMessage`、`items`、`page`、`total`、`hasMore`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 44：填写测评 `pages/assessment-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`0f793afde8c447dd3a67b1cb4408f32869c33f536f204d8f282e6981e5daec56`
- 核对文件：`apps/miniprogram/pages/assessment-detail/index.wxml`、`apps/miniprogram/pages/assessment-detail/index.wxss`、`apps/miniprogram/pages/assessment-detail/index.js`、`apps/miniprogram/pages/assessment-detail/index.json`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/assessment/index`
- 页面组件：`section-title` → `/components/section-title/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：正在读取测一测内容...、注意：本内容含敏感语义，结果只作为自我观察线索，不作为诊断建议。、去登录后继续、网络响应较慢；草稿仍在本机，请不要重复点击。

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 27 | 选择 {{opt.displayLabel}} | `bindtap` | `selectOption` | {'index': '{{qi}}', 'value': '{{opt.value}}', 'score': '{{opt.score}}'} |
| 44 | — | `bindinput` | `onTextInput` | {'index': '{{qi}}'} |
| 57 | 去登录后继续 | `bindtap` | `goLogin` | — |
| 63 | — | `bindtap` | `submitWorksheet` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 115 | `getAssessment` | `GET` | `/api/assessments` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/content_review.py`、`backend/routes/general_growth.py` |
| 231 | `createProfile` | `POST` | `/api/profile` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/content_review.py`、`backend/routes/general_growth.py` |
| 232 | `createAssessmentResult` | `POST` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/content_review.py`、`backend/routes/general_growth.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/assessment-result/index?id=:dynamic`（js:243）、`navigateTo` → `/pages/login/index:dynamic`（js:296）
- 本地存储：`getStorageSync` `auth_token`（JS:272）、`getStorageSync` `auth_user`（JS:276）、`removeStorageSync` `auth_token`（JS:302）、`removeStorageSync` `auth_user`（JS:303）、`getStorageSync` `storageKey`（JS:345）、`setStorageSync` `storageKey`（JS:367）、`removeStorageSync` `storageKey`（JS:397）
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

### 45：测一测结果 `pages/assessment-result/index`

#### 2026-08-29 第二阶段人工冻结（本人结果分析）

- 页面目标不变：受试者理解本次测评及后续支持；新增“近期情绪与互动线索”位于测评解释之后、训练建议之前。
- 数据源：`GET /api/assessment-results/:id/exploratory-analysis`，由登录态和结果归属共同限制，只读取本人最近最多 100 条结构化情绪日记。
- 可见数据不包含日记原文或其他参与者数据；网络部分只展示场景—情绪共现次数，不展示中心性、关系质量、人格标签或诊断判断。
- 状态矩阵：`available` 展示前 8 个情绪条目和支持度至少 2 的共现线索；`insufficient` 提示至少 5 条；`withheld` 转为人工支持提示；`ineligible` 不生成分析。
- 区块不增加操作按钮，不改变原有“查看可练习任务”主行动；使用现有卡片、列表、空状态和设计变量。

- 真值状态：`auto_evidence_complete`
- 源码指纹：`8abf17e926f9b8ddf87c344bf440aa0a7058c194b358c576738e17ece98b0726`
- 核对文件：`apps/miniprogram/pages/assessment-result/index.wxml`、`apps/miniprogram/pages/assessment-result/index.wxss`、`apps/miniprogram/pages/assessment-result/index.js`、`apps/miniprogram/pages/assessment-result/index.json`、`apps/miniprogram/utils/assessment-dimension-visualization.js`
- 上游页面：`pages/assessment/index`、`pages/assessment-history/index`、`pages/assessment-detail/index`
- 页面组件：`section-title` → `/components/section-title/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`visualization-state` → `/components/visualization-state/index`
- 主要可见内容：正在读取结果...、匹配清晰度：、参照、当前位置、优势提示、可以先做、可以带去讨论的问题、后续项目任务线索、分、查看可练习任务、返回测一测

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 137 | 查看可练习任务 | `bindtap` | `openRecommendedCards` | — |
| 138 | 返回测一测 | `bindtap` | `backToAssessment` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 447 | `getAssessmentResult` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |
| 448 | `getAssessment` | `GET` | `/api/assessments` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |
| 449 | `listCards` | `GET` | `/api/cards` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |
| 454 | `getAssessmentProfilePosition` | `GET` | `/api/assessment-results/:id/profile-position` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:699）、`navigateTo` → `/pages/training-card/index?card_ids=:dynamic`（js:705）、`switchTab` → `/pages/training/index`（js:710）
- 本地存储：`setStorageSync` `LATEST_TRAINING_RECOMMENDATION_KEY`（JS:359）、`setStorageSync` `THREE_DAY_LIGHT_PLAN_KEY`（JS:401）
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

### 46：教育热榜 `pages/hot-topics/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`b4e6b6b40f765431ac6f96336176a06688bc57dbb3d90ab6b267f2ddc7173560`
- 核对文件：`apps/miniprogram/pages/hot-topics/index.wxml`、`apps/miniprogram/pages/hot-topics/index.wxss`、`apps/miniprogram/pages/hot-topics/index.js`、`apps/miniprogram/pages/hot-topics/index.json`
- 上游页面：`pages/home/index`
- 页面组件：`section-title` → `/components/section-title/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`、`training-task-card` → `/components/training-task-card/index`
- 主要可见内容：热门主题、问题情境、常见回应、可以换一种说法、查看关联训练卡、这些案例只用于自我观察和陪伴练习，不用于判断孩子、家长或家庭关系。如果出现紧急安全风险，请优先寻求现实支持和专业帮助。、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 9 | — | `bindtap` | `selectTag` | {'tag': '{{item}}'} |
| 25 | — | `bindtap` | `selectTopic` | {'id': '{{item.id}}'} |
| 67 | 查看关联训练卡 | `bindtapcard` | `openPractice` | — |
| 76 | 查看关联训练卡 | `bindtap` | `openPractice` | — |
| 87 | 回到首页 | `bindtap` | `goHome` | — |

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

### 47：UP任务卡 `pages/task-detail/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`91c636cd98fe56641750238d24eadc63444fa309d40965443547f2cbe1f053cc`
- 核对文件：`apps/miniprogram/pages/task-detail/index.wxml`、`apps/miniprogram/pages/task-detail/index.wxss`、`apps/miniprogram/pages/task-detail/index.js`、`apps/miniprogram/pages/task-detail/index.json`
- 上游页面：`pages/training/index`、`pages/training-card/index`
- 页面组件：`section-title` → `/components/section-title/index`、`alert-card` → `/components/alert-card/index`、`bottom-tip-card` → `/components/bottom-tip-card/index`
- 主要可见内容：适用情境、预计用时、今天的小目标、今日感受、当前情绪强度： / 10、完成并打卡、从第一步开始、暂存感受

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 3 | ‹ | `bindtap` | `goBack` | — |
| 53 | 当前情绪强度： / 10 | `bindinput` | `onReflectionInput` | — |
| 55 | — | `bindchange` | `onEmotionLevelChange` | — |
| 64 | 完成并打卡 | `bindtap` | `finishPractice` | — |
| 66 | 从第一步开始 | `bindtap` | `startPractice` | — |
| 67 | 暂存感受 | `bindtap` | `recordFeeling` | — |

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

### 48：推荐训练卡 `pages/training-card/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`c0c9325a0492ce44a9fbbacf8d4ac5a7801c2987d90dd46cbabd165f2019c732`
- 核对文件：`apps/miniprogram/pages/training-card/index.wxml`、`apps/miniprogram/pages/training-card/index.wxss`、`apps/miniprogram/pages/training-card/index.js`、`apps/miniprogram/pages/training-card/index.json`
- 上游页面：`pages/home/index`、`pages/thermometer/index`、`pages/training/index`、`pages/training-history/index`、`pages/personalized-plan/index`、`pages/therapeutic-assessment-action-followup/index`、`pages/feedback-result/index`、`pages/assessment-result/index`、`pages/hot-topics/index`
- 页面组件：`feedback-rating` → `/components/feedback-rating/index`、`page-state` → `/components/page-state/index`、`training-task-card` → `/components/training-task-card/index`
- 主要可见内容：训练卡、这次推荐依据、今天的小目标、适合、节奏、完成、可以这样说、这些情况先停下来

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 10 | 这次推荐依据 | `bindaction` | `retryLoadCards` | — |
| 33 | — | `bindtap` | `toggleCardDetails` | {'id': '{{item.id}}'} |
| 47 | — | `bindtap` | `choosePractice` | {'id': '{{item.id}}', 'title': '{{item.title}}'} |
| 48 | — | `bindselect` | `submitTrainingFeedback` | {'id': '{{item.id}}'} |
| 59 | — | `bindaction` | `goDiary` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 61 | `listCards` | `GET` | `/api/cards` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 61 | `recommendCards` | `GET` | `/api/cards/recommend` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |
| 153 | `createFeedbackLedgerEntry` | `POST` | `/api/feedback-ledger` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/assessments.py`、`backend/routes/cards.py`、`backend/routes/checkins.py`、`backend/routes/content_review.py` |

#### 路由、本地状态与页面状态

- 下游路由：`navigateTo` → `/pages/task-detail/index?card_id=:dynamic`（js:128）、`navigateTo` → `/pages/diary-form/index`（js:143）
- 本地存储：`setStorageSync` `safehome:selectedTrainingCard`（JS:126）
- WXML 数据绑定：`loading`、`errorMessage`、`errorDetail`、`tagsText`、`cards`、`item`、`false`、`expandedCardId`、`feedbackEvaluationSaving`、`true`
- 条件状态：`loading`、`errorMessage`、`tagsText`、`item`、`cards`
- `setData` 状态：`tagsText`、`diaryId`、`tags`、`cardIds`、`loading`、`errorMessage`、`errorDetail`、`practiceMessage`、`cards`、`index`、`expandedCardId`、`feedbackEvaluationSaving`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 49：记录尝试 `pages/checkin/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`86087b92c1805c2486b082d4f60baf4f6ff4f90f26a54cb9200e7bf43f7f2318`
- 核对文件：`apps/miniprogram/pages/checkin/index.wxml`、`apps/miniprogram/pages/checkin/index.wxss`、`apps/miniprogram/pages/checkin/index.js`、`apps/miniprogram/pages/checkin/index.json`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/task-detail/index`
- 页面组件：—
- 主要可见内容：练习打卡、记录这次尝试和练习前后的感受变化即可。、本次练习、练习前情绪强度： / 10、练习后情绪强度： / 10、这次练习对你有帮助吗？、如果暂时不想完成，可以写一个原因（可选）、练习复盘、网络响应较慢；草稿仍在本机，请不要重复点击。、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 21 | — | `bindchange` | `onEmotionBeforeChange` | — |
| 26 | — | `bindchange` | `onEmotionAfterChange` | — |
| 32 | — | `bindtap` | `chooseHelpfulness` | {'value': '{{item.value}}'} |
| 46 | — | `bindinput` | `onSkipReasonInput` | — |
| 55 | — | `bindinput` | `onReflectionInput` | — |
| 69 | — | `bindtap` | `submitCheckin` | — |
| 73 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 111 | `createCheckin` | `POST` | `/api/checkins` | `backend/app.py`、`backend/models.py`、`backend/routes/admin.py`、`backend/routes/checkins.py`、`backend/routes/general_growth.py`、`backend/routes/profile.py`、`backend/routes/research_workspace.py`、`backend/routes/training_plan.py` |

#### 路由、本地状态与页面状态

- 下游路由：`reLaunch` → `/pages/home/index`（js:141）、`navigateTo` → `/pages/login/index:dynamic`（js:170）
- 本地存储：`getStorageSync` `safehome:selectedTrainingCard`（JS:41）、`getStorageSync` `auth_token`（JS:146）、`getStorageSync` `auth_user`（JS:150）、`removeStorageSync` `auth_token`（JS:176）、`removeStorageSync` `auth_user`（JS:177）、`getStorageSync` `storageKey`（JS:219）、`setStorageSync` `storageKey`（JS:241）、`removeStorageSync` `storageKey`（JS:271）
- WXML 数据绑定：`cardTitle`、`emotionBefore`、`emotionAfter`、`helpfulnessOptions`、`helpfulnessRating`、`item`、`skipReason`、`reflectionPrompts`、`reflection`、`successMessage`、`errorMessage`、`draftRestored`、`saveStatus`、`slowSubmitting`、`submitting`、`submitted`
- 条件状态：`successMessage`、`errorMessage`、`slowSubmitting`
- `setData` 状态：`sourceRecommendationId`、`cardId`、`diaryId`、`cardTitle`、`saveStatus`、`emotionBefore`、`successMessage`、`errorMessage`、`submitting`、`slowSubmitting`、`submitted`
- 未解析事件：—
- 未解析 API：—
- 无效目标路由：—

#### 设计与实现边界

- ImageGen、Figma 和代码只能表现上表中已有事件、接口、路由和状态；不能根据标题猜测新功能。
- API 返回内容、权限、风险边界和本地草稿语义保持不变；视觉不替代业务判断。
- 本页进入 ImageGen 前仍需结合真实截图完成页面目标、唯一主任务、信息优先级和状态矩阵的人工冻结。

### 50：本周复盘 `pages/weekly-report/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`307ce430de25acfc3d3e81b73595a991bc2eaf2db5f7a7c27b577a8ae5b89bdb`
- 核对文件：`apps/miniprogram/pages/weekly-report/index.wxml`、`apps/miniprogram/pages/weekly-report/index.wxss`、`apps/miniprogram/pages/weekly-report/index.js`、`apps/miniprogram/pages/weekly-report/index.json`、`apps/miniprogram/utils/authGuard.js`
- 上游页面：`pages/home/index`、`pages/profile/index`
- 页面组件：—
- 主要可见内容：本周复盘、正在整理本周复盘、周报暂时没有加载成功、重新加载、阶段性画像线索、有内容需要人工关注，请优先等待或提交人工支持。、本周小变化、至、类常见场景、类常见情绪、条互动线索、练习尝试、测评记录、温度记录、本周测评记录、只整理你完成过的测评，不做固定判断、本周还没有测评记录。、推荐训练：、情绪温度趋势、训练效用线索、只看练习前后记录，不承诺疗效、本周高频场景

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 17 | 重新加载 | `bindtap` | `refreshReport` | — |
| 164 | 刷新复盘 | `bindtap` | `refreshReport` | — |
| 165 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 86 | `getWeeklyReport` | `GET` | `/api/weekly-report` | `backend/models.py`、`backend/routes/admin.py`、`backend/routes/general_growth.py`、`backend/routes/reports.py`、`backend/scripts/generate_task33_ux_registry.py`、`backend/scripts/verify_privacy_restore.py`、`backend/services/data_claim_service.py`、`backend/services/participant_action_planner.py` |

#### 路由、本地状态与页面状态

- 下游路由：`reLaunch` → `/pages/home/index`（js:142）、`navigateTo` → `/pages/login/index:dynamic`（js:171）
- 本地存储：`getStorageSync` `auth_token`（JS:147）、`getStorageSync` `auth_user`（JS:151）、`removeStorageSync` `auth_token`（JS:177）、`removeStorageSync` `auth_user`（JS:178）
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

### 51：人工督导入口 `pages/supervision/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`72ebdbd5c4380ba601919f70a9ab26baa52d8ce423b22db105e6c9daee769a0a`
- 核对文件：`apps/miniprogram/pages/supervision/index.wxml`、`apps/miniprogram/pages/supervision/index.wxss`、`apps/miniprogram/pages/supervision/index.js`、`apps/miniprogram/pages/supervision/index.json`、`apps/miniprogram/utils/authGuard.js`、`apps/miniprogram/utils/resilientForm.js`
- 上游页面：`pages/home/index`、`pages/profile/index`、`pages/feedback-result/index`
- 页面组件：—
- 主要可见内容：人工支持、先确认边界、人工反馈可能需要等待，适合补充理解一条记录，不适合处理紧急安全风险。、如果你或孩子正在经历自伤、自杀、暴力、失控或其他安全风险，请先联系身边可信赖的人、当地紧急服务或线下专业机构。、选择想请老师一起看的记录、想请老师补充看的内容、可选联系方式、可选风险提示、网络响应较慢；草稿仍在本机，请不要重复点击。、回到首页

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 18 | — | `bindtap` | `selectSource` | {'type': '{{item.type}}', 'id': '{{item.id}}'} |
| 37 | — | `bindinput` | `onTextInput` | {'key': 'message'} |
| 48 | — | `bindinput` | `onTextInput` | {'key': 'contact'} |
| 59 | — | `bindinput` | `onTextInput` | {'key': 'riskHint'} |
| 79 | — | `bindtap` | `submitSupervision` | — |
| 83 | 回到首页 | `bindtap` | `goHome` | — |

#### 接口真值

| JS 行 | API 客户端方法 | HTTP | 接口模板 | 后端只读证据 |
|---:|---|---|---|---|
| 59 | `listDiaries` | `GET` | `/api/diaries` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/auth_utils.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py` |
| 60 | `listAssessmentResults` | `GET` | `/api/assessment-results` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/auth_utils.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py` |
| 125 | `createSupervision` | `POST` | `/api/supervision` | `backend/app.py`、`backend/database.py`、`backend/models.py`、`backend/test_e2e_profile_position.py`、`backend/routes/admin.py`、`backend/routes/auth_utils.py`、`backend/routes/diaries.py`、`backend/routes/feedback.py` |

#### 路由、本地状态与页面状态

- 下游路由：`reLaunch` → `/pages/home/index`（js:157）、`navigateTo` → `/pages/login/index:dynamic`（js:186）
- 本地存储：`getStorageSync` `auth_token`（JS:162）、`getStorageSync` `auth_user`（JS:166）、`removeStorageSync` `auth_token`（JS:192）、`removeStorageSync` `auth_user`（JS:193）、`getStorageSync` `storageKey`（JS:235）、`setStorageSync` `storageKey`（JS:257）、`removeStorageSync` `storageKey`（JS:287）
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

### 52：云托管诊断 `pages/debug/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`f8ef1424ac0ed8153b0092fbbf0965d9db6ea75cf118c4e9b66024838192c022`
- 核对文件：`apps/miniprogram/pages/debug/index.wxml`、`apps/miniprogram/pages/debug/index.wxss`、`apps/miniprogram/pages/debug/index.js`、`apps/miniprogram/pages/debug/index.json`
- 上游页面：—
- 页面组件：—
- 主要可见内容：云托管诊断、当前配置、切换本地 5000、切回云托管、测试 healthz、测试 assessments、测试 risk/check、测试 profile、最近一次错误

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 16 | 切换本地 5000 | `bindtap` | `useLocalBackend` | — |
| 17 | 切回云托管 | `bindtap` | `useCloudBackend` | — |
| 18 | 测试 healthz | `bindtap` | `testHealthz` | — |
| 19 | 测试 assessments | `bindtap` | `testAssessments` | — |
| 20 | 测试 risk/check | `bindtap` | `testRiskCheck` | — |
| 21 | 测试 profile | `bindtap` | `testProfile` | — |

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
- 本地存储：—
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

### 53：联调测试 `pages/integration-test/index`

- 真值状态：`auto_evidence_complete`
- 源码指纹：`014bf7a7e05d76235e6d8c192e252ea09dcc6c4ddaec2557dd87a9a7bd196606`
- 核对文件：`apps/miniprogram/pages/integration-test/index.wxml`、`apps/miniprogram/pages/integration-test/index.wxss`、`apps/miniprogram/pages/integration-test/index.js`、`apps/miniprogram/pages/integration-test/index.json`
- 上游页面：`pages/home/index`、`pages/assessment/index`
- 页面组件：—
- 主要可见内容：最小联调测试、情绪事件记录、即时反馈、标签：、推荐训练卡

#### 交互与用户任务证据

| 行 | 可见名称/上下文 | 事件 | 处理器 | 事件参数 |
|---:|---|---|---|---|
| 11 | — | `bindtap` | `runSmokeTest` | — |

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
- 本地存储：—
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
