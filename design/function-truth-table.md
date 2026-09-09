# 小程序功能真值表

## 本轮未验收增量（用户已要求暂停）

- settings-detail的privacy说明改为读取utils/privacy-policy.json，由content/privacy.md同步；全文包含待负责人填写字段，不能称正式完备。构建脚本已增加正文同步，新增整体编译尚未执行。
- 测评空列表区分无开放内容与搜索无匹配；临时开放通过既有review_note/boundary_notice披露，不改底层审核记录。项目只读预览与原写入权限仍保留。
- 本地标题调整：教育热榜→亲子沟通主题、项目测试→陪伴项目、个性化训练方案→练习建议、人工督导入口→人工支持。profile与supervision相关文案减少未经核实的专业人员承诺。
- 本节仅登记源码改动，不代表Figma、真机、全量UI或生产验收通过。主线恢复前不自动继续设计/测试。

> **UIproduct2 当前入口（2026-09-08）**：以本文件“UIproduct2 当前全页功能真值”及当前源码为准。下方旧手工段落保留作历史；“尚无情绪记录页”、旧活动页和 UIproduct 分支限制不适用于本轮。执行顺序为功能核对 → 需求冻结 → Figma → 前端实现 → 全页统一检查 → 用户最终验收；不使用 ImageGen，不逐页等待用户验收。

更新时间：2026-09-08

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

## 2026-09-08 前五页精修增量真值

- 首页温度计：thermometerRecordReady=false时显示“记录次数待更新”，不把未读取计数展示为已记录0次；接口不变。
- 登录/注册：仅增加原生输入aria-label及placeholder样式；用户名、密码、角色、昵称、首次改密阈值、disabled、回跳不变。
- 首页EntryRow：动作文案纳入可访问名称，摘要仅保留单一箭头并自然换行；点击事件及actionKey不变。
- 支持性问答：question-composer增加默认空的guidance展示属性；未同意/未填写时解释禁用原因，不改变sending/disabled条件、同意版本、输入和submit事件。
- 本节不新增业务能力；上述五页事件行号按精修后WXML更新。

## UIproduct2 当前全页功能真值（2026-09-08）

### 第20–28页复核增量

- 共同理解总览保留两条路径：进入分步流程、直接提交问题；前者为主要导航，后者为次行动。服务级别仍显示，合同加载不等于正式批准，标题改为“协作规则”。`production_release_approved`在本地合同中仍为false；未改变发布状态。
- 分步页新增纯展示属性`ui2`，默认false，各页面在Figma完成后显式传true。`description`早已由CONFIG提供并传入组件，本轮将它呈现在正文区；不增加后端字段或新的同意。
- 八步CONFIG、shared_scope映射、版本、草稿和所有API方法完全未改。新增说明条件仅`ui2 && description`，装饰眉题仅在旧视觉保留；所有业务状态分支与事件不变。
- 总览、流程和输入组件原有事件/数据属性/maxlength/disabled/loading保持。共享三选项不预选；“不像”保留原因输入；只有sent反馈可展示；撤回/过期与安全暂停条件不变。
- 行动页初始canContinue仍由既有代码根据已发送反馈决定；表单输入后由内容与自愿确认判断。未把Figma默认稿伪造为所有空字段一律禁用，也未增加日期选择器或提醒承诺。


### 第17–19页复核增量

- 关系报告：feedbackSavingIndex已在JS中锁住全部假设保存；界面现同步disabled及保存提示，没有新增限制。日期新增generatedAtText纯展示，原report.generated_at保留。feedback-rating使用editorial布尔属性，不存在variant属性。
- 关系任务：画布520rpx和坐标、7个情境、草稿、240/300字限制、至少一个句子或绘画加画外音、同意与风险转人工全部保留。
- 关系成长：四栏、两种提交和报名门槛不变；计数/1–5量尺/维度仍独立，图中文字变大并调整对齐，不改坐标/数值算法。记录栏的底部导航只变为次按钮。
- 以下行号为初次静态取证位置，布局编辑后的事件与参数以当前源码及本增量为准。


依据当前工作区源码、组件递归引用、客户端实现及 API 契约/后端处理函数建立。状态为“静态源码已核对，运行与最终验收待完成”；不是生产可用性证明。未增加业务能力，未运行旧 UIproduct Harness，未计算新哈希。

说明：共享步骤工厂中的方法是条件式能力集合，不表示每个步骤可调用全部方法；必须按 stepId、角色、同意和安全状态设计。动态 action 接口列出后端候选，实际动作仍受页面按钮与处理器约束。静态提取不替代逐页实现前阅读。

### 01 安心陪伴 — `pages/home/index`

**用户任务：** 找到当前最适合继续的一步；保留情绪温度计、测评/日记、最近记录、阶段反馈和消息入口。
- 页面源码：`apps/miniprogram/pages/home/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{unreadMessageCount > 0}}`；`{{homeOverviewError}}`；`{{!latestRecordReady && !latestRecordError}}`；`{{latestRecordError}}`；`{{latestRecord}}`；`{{!progressSummaryReady && !progressSummaryError}}`；`{{progressSummary}}`；`{{progressSummaryError}}`；`{{showDevEntry}}`
- 组件：`page-state`、`journey-action-card`、`status-pill`、`entry-row`、`dual-entry`、`function-entry-card`、`section-heading`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 4 | 打开消息中心{{unreadMessageCount > 0 ? '，有未读消息' : ''}} | `bindtap → openMessages` | {} |
| 14 | 首页摘要暂时不可用 | `bind:action → retryHomeData` | {} |
| 23 | {{todayJourney ? todayJourney.title : '继续今天的一小步'}} | `bind:action → openTodayAction` | {} |
| 23 | {{todayJourney ? todayJourney.title : '继续今天的一小步'}} | `bind:retry → retryTodayJourney` | {} |
| 39 | 情绪温度计 | `bind:action → openThermometer` | {} |
| 40 | dual-entry | `bind:action → openCoreEntry` | {} |
| 43 | 如何开始 | `bind:action → openGettingStarted` | {} |
| 47 | 支持性反馈 | `bind:action → openCoreEntry` | {} |
| 48 | 训练中心 | `bind:action → openCoreEntry` | {} |
| 49 | 人工支持 | `bind:action → openCoreEntry` | {} |
| 59 | 暂时无法读取最近记录 | `bind:action → retryHomeData` | {} |
| 67 | {{latestRecord.time}} · {{latestRecord.trigger}} | `bind:action → openDiaryHistory` | {} |
| 68 | 还没有保存的记录 | `bind:action → startDiary` | {} |
| 78 | {{progressSummary.summaryText}} | `bind:action → openWeeklyReport` | {} |
| 79 | 暂时无法读取阶段性反馈 | `bind:action → retryHomeData` | {} |
| 87 | 记录还不够，继续观察 | `bind:action → openWeeklyReport` | {} |
| 91 | button | `bindtap → openIntegrationTest` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/home/index.js:9` | `trackProductEvent` | POST /api/product-events | backend/routes/product_events.py:63 / product_events.create_product_event / role_scoped |
| `apps/miniprogram/pages/home/index.js:200` | `listDiaries` | GET /api/diaries | backend/routes/diaries.py:148 / diaries.list_diaries / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/home/index.js:202` | `getProfileStats` | GET /api/profile/stats | backend/routes/profile.py:163 / profile.get_profile_stats / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/home/index.js:203` | `getEmotionThermometerDay` | GET /api/emotion-thermometer/day | backend/routes/emotion_thermometer.py:192 / emotion_thermometer.get_emotion_thermometer_day / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/home/index.js:204` | `getProgressSummary` | GET /api/progress-summary | backend/routes/progress_summary.py:18 / progress_summary.get_progress_summary / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/home/index.js:264` | `getTodayJourney` | GET /api/journey/today | backend/routes/journey.py:14 / journey.get_today_journey / role_scoped |

- 下游路由：navigateTo → /pages/goal-setting/index；navigateTo → /pages/diary-form/index；navigateTo → /pages/diary-history/index；navigateTo → /pages/thermometer/index；navigateTo → /pages/weekly-report/index；switchTab → /pages/training/index；navigateTo → /pages/assessment/index；navigateTo → /pages/messages/index；navigateTo → /pages/integration-test/index；navigateTo → /pages/getting-started/index；switchTab → /pages/training/index；navigateTo → /pages/getting-started/index；switchTab → /pages/training/index；navigateTo → /pages/diary-form/index；navigateTo → /pages/supervision/index；navigateTo → /pages/assessment/index；navigateTo → /pages/training-card/index?tags=:dynamic；navigateTo → /pages/hot-topics/index；navigateTo → /pages/hot-topics/index?id=:dynamic
- 本地保存：getStorageSync key
- 组件事件转发：page-state → action；journey-action-card → action/retry；entry-row → action；dual-entry → action；function-entry-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 02 登录 — `pages/login/index`

**用户任务：** 使用真实可用的登录方式进入；能力探测、账号密码兜底、强制改密、取消/失败与回跳完整保留。
- 页面源码：`apps/miniprogram/pages/login/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{mustChangePassword}}`；`{{message}}`；`{{wechatAvailable}}`；`{{phoneAvailable}}`；`{{capabilityMessage}}`；`{{message}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 14 | 临时密码 | `bindinput → onCurrentPasswordInput` | {} |
| 18 | 新密码，至少12位并包含三类字符 | `bindinput → onNewPasswordInput` | {} |
| 22 | 再次输入新密码 | `bindinput → onConfirmPasswordInput` | {} |
| 26 | button | `bindtap → submitPasswordChange` | {} |
| 33 | button | `bindtap → submitWechatLogin` | {} |
| 35 | button | `bindgetphonenumber → handlePhoneLogin` | {} |
| 50 | 用户名 | `bindinput → onUsernameInput` | {} |
| 54 | 密码 | `bindinput → onPasswordInput` | {} |
| 58 | button | `bindtap → submitLogin` | {} |
| 59 | button | `bindtap → goRegister` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/login/index.js:78` | `getAuthCapabilities` | GET /api/auth/capabilities | backend/routes/auth.py:373 / auth.auth_capabilities / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/login/index.js:113` | `login` | POST /api/auth/login | backend/routes/auth.py:455 / auth.login / authenticated_identity_match_before_pending_logout_revoke |
| `apps/miniprogram/pages/login/index.js:168` | `changePassword` | POST /api/auth/change-password | backend/routes/auth.py:925 / auth.change_password / role_scoped |
| `apps/miniprogram/pages/login/index.js:204` | `wechatLogin` | POST /api/auth/wechat-login | backend/routes/auth.py:548 / auth.wechat_login / authenticated_identity_match_before_pending_logout_revoke |
| `apps/miniprogram/pages/login/index.js:250` | `phoneLogin` | POST /api/auth/phone-login | backend/routes/auth.py:627 / auth.phone_login / authenticated_identity_match_before_pending_logout_revoke |

- 下游路由：switchTab → /pages/home/index；redirectTo → /pages/register/index:dynamic
- 本地保存：
- 权限/预览线索：apps/miniprogram/pages/login/index.js:34 `if (!user \|\| user.role !== "student") {`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 03 注册 — `pages/register/index`

**用户任务：** 创建允许公开注册的账号；用户名、密码、角色、昵称、校验和登录回跳不变。
- 页面源码：`apps/miniprogram/pages/register/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{message}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 12 | 用户名 | `bindinput → onUsernameInput` | {} |
| 18 | 密码 | `bindinput → onPasswordInput` | {} |
| 25 | 选择角色，当前为{{roleOptions[roleIndex].label}} | `bindchange → onRoleChange` | {} |
| 41 | 昵称，可选 | `bindinput → onNicknameInput` | {} |
| 45 | button | `bindtap → submitRegister` | {} |
| 46 | button | `bindtap → goLogin` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/register/index.js:68` | `register` | POST /api/auth/register | backend/routes/auth.py:413 / auth.register / not_applicable_or_development_legacy |

- 下游路由：redirectTo → /pages/home/index；navigateTo → /pages/login/index:dynamic
- 本地保存：
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 04 消息 — `pages/messages/index`

**用户任务：** 阅读本人消息列表，辨认未读、已读、撤回与版本，进入详情；不是即时聊天。
- 页面源码：`apps/miniprogram/pages/messages/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{errorDiagnostic}}`；`{{messages.length}}`
- 组件：`page-state`、`bottom-tip-card`、`message-row`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 10 | 消息暂时没有读取成功 | `bind:action → handleStateAction` | {} |
| 13 | 复制本次错误的诊断信息 | `bindtap → copyDiagnostic` | {} |
| 18 | message-row | `bind:open → openMessage` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/messages/index.js:25` | `listMessages` | GET /api/messages | backend/routes/messages.py:48 / messages.list_messages / self_for_participant_active_assignment_for_researcher_supervisor_full_for_admin |

- 下游路由：navigateTo → /pages/message-detail/index?id=:dynamic；reLaunch → /pages/home/index；navigateTo → /pages/login/index?redirect=%2Fpages%2Fmessages%2Findex；navigateTo → /pages/register/index?redirect=%2Fpages%2Fmessages%2Findex
- 本地保存：
- 组件事件转发：page-state → action；message-row → open
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 05 支持性问答 — `pages/support-assistant/index`

**用户任务：** 在真实能力开关与同意条件下输入问题、阅读有来源回答；关闭态和失败保留输入。
- 页面源码：`apps/miniprogram/pages/support-assistant/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{error && !enabled}}`；`{{!enabled}}`；`{{messages.length}}`
- 组件：`page-state`、`boundary-note`、`conversation-entry`、`question-composer`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 16 | 暂时无法打开支持性问答 | `bind:action → loadStatus` | {} |
| 32 | boundary-note | `bind:confirm → enableConsent` | {} |
| 38 | question-composer | `bind:input → onQuestionInput` | {} |
| 38 | question-composer | `bind:submit → sendQuestion` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/support-assistant/index.js:49` | `getAiQaConfig` | GET /api/ai-qa/config | backend/routes/ai_qa.py:108 / ai_qa.ai_qa_config / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/support-assistant/index.js:74` | `createConsent` | POST /api/consent | backend/routes/consent.py:40 / consent.create_consent_record / authenticated_self_only_consent_event_history |
| `apps/miniprogram/pages/support-assistant/index.js:94` | `createAiQaSession` | POST /api/ai-qa/sessions | backend/routes/ai_qa.py:222 / ai_qa.ai_qa_session_create / own_synthetic_research_sessions_only |
| `apps/miniprogram/pages/support-assistant/index.js:111` | `sendAiQaMessage` | POST /api/ai-qa/sessions/<session_id>/messages | backend/routes/ai_qa.py:247 / ai_qa.ai_qa_message_create / own_synthetic_research_sessions_only |

- 下游路由：redirectTo → /pages/login/index?redirect=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/support-assistant/index.js:36 `if (!isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；boundary-note → confirm；question-composer → input/submit
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 06 消息详情 — `pages/message-detail/index`

**用户任务：** 阅读本人消息与来源，按真实条件打开来源或共同核对；撤回内容不得重新显示。
- 页面源码：`apps/miniprogram/pages/message-detail/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{canOpenSource}}`；`{{canEvaluate}}`
- 组件：`page-state`、`feedback-rating`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 3 | page-state | `bindaction → handleStateAction` | {} |
| 16 | button | `bindtap → openSource` | {} |
| 19 | feedback-rating | `bindselect → submitFeedbackEvaluation` | {} |
| 30 | 返回消息列表 | `bindtap → goMessages` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/message-detail/index.js:31` | `getMessage` | GET /api/messages/<message_id> | backend/routes/messages.py:83 / messages.get_message / self_for_participant_active_assignment_for_researcher_supervisor_full_for_admin |
| `apps/miniprogram/pages/message-detail/index.js:76` | `createFeedbackLedgerEntry` | POST /api/feedback-ledger | backend/routes/feedback_ledger.py:24 / feedback_ledger.create_entry / role_scoped |

- 下游路由：navigateTo → /pages/relationship-report/index?id=:dynamic；navigateTo → /pages/relationship-narrative/index?id=:dynamic
- 本地保存：
- 组件事件转发：page-state → action；feedback-rating → select
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 07 紧急安全指引 — `pages/emergency-guide/index`

**用户任务：** 优先找到现实帮助，阅读安全行动；不新增拨号、定位或自动危机处置。
- 页面源码：`apps/miniprogram/pages/emergency-guide/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：
- 组件：`page-state`、`safety-action-row`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 32 | 查看现实支持资源 | `bindtap → openResources` | {} |
| 33 | 回到首页 | `bindtap → goHome` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| — | — | 本地内容/导航/状态 | 不新增后端能力 |

- 下游路由：reLaunch → /pages/home/index；navigateTo → /pages/emergency-resources/index
- 本地保存：
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 08 紧急帮助说明 — `pages/emergency-resources/index`

**用户任务：** 阅读四类现实支持方向并返回安全指引；静态资源不是可直接联系的服务。
- 页面源码：`apps/miniprogram/pages/emergency-resources/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：
- 组件：`page-state`、`resource-channel-row`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 19 | 查看紧急安全指引 | `bindtap → goGuide` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| — | — | 本地内容/导航/状态 | 不新增后端能力 |

- 下游路由：navigateTo → /pages/emergency-guide/index
- 本地保存：
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 09 三步开始 — `pages/getting-started/index`

**用户任务：** 理解记录—反馈—练习的真实三步，进入日记或训练；不虚构学习进度。
- 页面源码：`apps/miniprogram/pages/getting-started/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 70 | 记录一次 | `bindtap → startDiary` | {} |
| 71 | 去训练中心 | `bindtap → openTraining` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| — | — | 本地内容/导航/状态 | 不新增后端能力 |

- 下游路由：navigateTo → /pages/diary-form/index；switchTab → /pages/training/index
- 本地保存：
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 10 情绪温度计 — `pages/thermometer/index`

**用户任务：** 记录强度及可选感受维度；查看真实保存回执、当天曲线、点选与记录，保留拖动和加减。
- 页面源码：`apps/miniprogram/pages/thermometer/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{receipt}}`；`{{receipt.practice_available}}`；`{{loading}}`；`{{summary.count && !loading}}`；`{{selectedPoint}}`；`{{!summary.count && !loading}}`；`{{errorMessage}}`；`{{item.emotion_label}}`
- 组件：`page-state`、`intensity-scale`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 13 | − | `bindchange → onIntensityChange` | {} |
| 17 | 情绪强度减一 | `bindtap → decreaseIntensity` | {} |
| 18 | 情绪强度加一 | `bindtap → increaseIntensity` | {} |
| 30 | 调整愉悦度 | `bindchange → onValenceChange` | {} |
| 30 | 调整愉悦度 | `bindchanging → onValenceChange` | {} |
| 37 | 调整身体唤起 | `bindchange → onArousalChange` | {} |
| 37 | 调整身体唤起 | `bindchanging → onArousalChange` | {} |
| 44 | 调整可控感 | `bindchange → onControlChange` | {} |
| 44 | 调整可控感 | `bindchanging → onControlChange` | {} |
| 48 | / 40 | `bindinput → onEmotionLabelInput` | {} |
| 58 | / 200 | `bindinput → onBriefInput` | {} |
| 69 | button | `bindtap → saveRecord` | {} |
| 77 | 收起记录回执 | `bindtap → dismissReceipt` | {} |
| 81 | 去练一张卡 | `bindtap → openPractice` | {} |
| 90 | 刷新 | `bindtap → loadDay` | {} |
| 93 | 今日情绪强度变化曲线，具体记录见下方列表 | `bindtouchstart → handleCanvasTap` | {} |
| 114 | 重试读取 | `bindtap → loadDay` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/thermometer/index.js:96` | `getEmotionThermometerDay` | GET /api/emotion-thermometer/day | backend/routes/emotion_thermometer.py:192 / emotion_thermometer.get_emotion_thermometer_day / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/thermometer/index.js:123` | `createEmotionThermometer` | POST /api/emotion-thermometer | backend/routes/emotion_thermometer.py:128 / emotion_thermometer.create_emotion_thermometer_record / self_only_or_dedicated_domain_command |

- 下游路由：navigateTo → /pages/training-card/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/thermometer/index.js:36 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；intensity-scale → change
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 11 训练 — `pages/training/index`

**用户任务：** 找到可继续的练习，浏览真实推荐、轻量计划、训练库和条件式试点入口。
- 页面源码：`apps/miniprogram/pages/training/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{latestRecommendation}}`；`{{latestRecommendation.reason}}`；`{{latestRecommendation.reason}}`；`{{latestRecommendation.todaySuggestion}}`；`{{latestRecommendation.todaySuggestion}}`；`{{latestRecommendation.primaryCard}}`；`{{latestRecommendation.primaryCard.purpose}}`；`{{latestRecommendation.primaryCard.recentlyCompleted}}`；`{{latestRecommendation.boundaryNotice}}`；`{{relationshipPilotAvailable}}`；`{{threeDayPlan}}`；`{{lightPlanExpanded}}`；`{{libraryExpanded}}`
- 组件：`page-state`、`section-title`、`training-task-card`、`bottom-tip-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 14 | 个性化方案 | `bindtap → openPersonalizedPlan` | {} |
| 18 | 项目测试 | `bindtap → openProgramList` | {} |
| 47 | 查看练习 | `bindtap → openLatestRecommendation` | {} |
| 54 | 进入关系探索试点 | `bindtap → openRelationshipPilot` | {} |
| 63 | button | `bindtap → toggleLightPlan` | {} |
| 65 | button | `bindtap → openPlanDay` | {"card-id":"{{item.cardId}}"} |
| 102 | button | `bindtap → toggleLibrary` | {} |
| 109 | training-task-card | `bindtapcard → openTrainingCard` | {"id":"{{task.id}}","tags":"{{task.tagsText}}"} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/training/index.js:149` | `getShowcaseAccess` | GET /api/showcase-access | backend/routes/showcase_access.py:13 / showcase_access.get_showcase_access / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/training/index.js:159` | `getTrainingPlan` | GET /api/training-plan | backend/routes/training_plan.py:343 / training_plan.get_training_plan / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/training-card/index?card_ids=:dynamic；navigateTo → /pages/training-card/index?card_ids=:dynamic；navigateTo → /pages/personalized-plan/index；navigateTo → /pages/program-list/index；navigateTo → /pages/relationship-pilot/index；navigateTo → /pages/task-detail/index?id=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync LATEST_TRAINING_RECOMMENDATION_KEY；getStorageSync THREE_DAY_LIGHT_PLAN_KEY；getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/training/index.js:148 `const user = getAuthUser();`；apps/miniprogram/pages/training/index.js:150 `this.setData({ relationshipPilotAvailable: !!showcase.enabled \|\| !!(user && user.role === "student") });`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；section-title → more；training-task-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 12 训练记录 — `pages/training-history/index`

**用户任务：** 回看训练记录、再次练习及加载更多；总数、分页错误与末尾状态不混淆。
- 页面源码：`apps/miniprogram/pages/training-history/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage && !items.length}}`；`{{items.length}}`；`{{item.helpfulnessText}}`；`{{item.reflection}}`；`{{hasMore}}`；`{{errorMessage}}`；`{{errorMessage && errorDiagnostic}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 20 | 重新加载 | `bindtap → retry` | {} |
| 21 | 复制诊断信息 | `bindtap → copyDiagnostic` | {} |
| 34 | 再次练习 | `bindtap → openCard` | {"card-id":"{{item.card_id}}"} |
| 37 | button | `bindtap → loadMore` | {} |
| 40 | 复制诊断信息 | `bindtap → copyDiagnostic` | {} |
| 46 | 去训练中心 | `bindtap → goTraining` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/training-history/index.js:56` | `listCheckins` | GET /api/checkins | backend/routes/checkins.py:160 / checkins.list_checkins / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/training-card/index?card_ids=:dynamic；switchTab → /pages/training/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/training-history/index.js:42 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 13 个性化训练方案 — `pages/personalized-plan/index`

**用户任务：** 设置阶段、频率和日期，查看到期摘要及真实推荐；微信提醒按原授权语义运行。
- 页面源码：`apps/miniprogram/pages/personalized-plan/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{assignment.due_reason}}`；`{{plan && plan.assignment}}`；`{{!notification.available}}`；`{{notification.preference && notification.preference.consent_status === 'accepted'}}`；`{{notification.preference && notification.preference.consent_status === 'consumed'}}`；`{{notification.preference && notification.preference.consent_status === 'banned'}}`；`{{notification.available && (!notification.preference \|\| notification.preference.consent_status !== 'accepted') && notification.preference.consent_status !== 'banned'}}`；`{{notification.available && notification.preference && notification.preference.consent_status === 'banned'}}`；`{{!loading && plan && !plan.has_assessment}}`；`{{item.cluster_name}}`；`{{loading}}`；`{{!loading && errorMessage}}`；`{{!loading && plan && plan.has_assessment && !planItems.length}}`
- 组件：`page-state`、`training-task-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 17 | button | `bindtap → selectAssignmentOption` | {"field":"phase","value":"{{item.value}}"} |
| 29 | button | `bindtap → selectAssignmentOption` | {"field":"cadence","value":"{{item.value}}"} |
| 41 | picker | `bindchange → onStartDateChange` | {} |
| 48 | button | `bindtap → selectAssignmentOption` | {"field":"status","value":"{{item.value}}"} |
| 59 | 保存练习节奏 | `bindinput → onGoalInput` | {} |
| 66 | 保存练习节奏 | `bindtap → saveAssignment` | {} |
| 102 | 开启一次微信提醒 | `bindtap → requestTrainingReminder` | {} |
| 108 | 前往微信设置 | `bindtap → openNotificationSettings` | {} |
| 118 | 去测一测 | `bindtap → openAssessment` | {} |
| 129 | training-task-card | `bindtapcard → openSingleCard` | {} |
| 151 | 重试 | `bindtap → loadPlan` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/personalized-plan/index.js:64` | `getNotificationConfig` | GET /api/notifications/config | backend/routes/notifications.py:26 / notifications.get_notification_config / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/personalized-plan/index.js:77` | `getTrainingPlan` | GET /api/training-plan | backend/routes/training_plan.py:343 / training_plan.get_training_plan / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/personalized-plan/index.js:124` | `saveTrainingPlanAssignment` | POST /api/training-plan/assignment | backend/routes/training_plan.py:486 / training_plan.save_training_plan_assignment / self_only_or_dedicated_domain_command |
| `apps/miniprogram/pages/personalized-plan/index.js:150` | `saveNotificationConsent` | POST /api/notifications/consent | backend/routes/notifications.py:35 / notifications.save_notification_consent / self_only_or_dedicated_domain_command |

- 下游路由：navigateTo → /pages/assessment/index；navigateTo → /pages/training-card/index?card_ids=:dynamic；navigateTo → /pages/training-card/index?card_ids=:dynamic
- 本地保存：
- 组件事件转发：page-state → action；training-task-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 14 项目测试 — `pages/program-list/index`

**用户任务：** 选择可用项目或获准只读预览；待审核不表现为正式开放。
- 页面源码：`apps/miniprogram/pages/program-list/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{previewMode}}`；`{{loading}}`；`{{!loading && errorMessage}}`；`{{!loading && !errorMessage && !programs.length}}`；`{{!loading && !errorMessage && !programs.length && availability && availability.pending_review_count}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 14 | 打开项目：{{item.title}} | `bindtap → openProgram` | {"id":"{{item.id}}","preview":"{{item.preview_only}}"} |
| 35 | <text wx:if="{{!loading && !errorMessage && !pro | `bindaction → loadPrograms` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/program-list/index.js:24` | `listPrograms` | GET /api/programs | backend/routes/programs.py:70 / programs.list_programs / not_applicable_or_development_legacy |

- 下游路由：navigateTo → /pages/program-detail/index?id=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/program-list/index.js:11 `previewMode: false,`；apps/miniprogram/pages/program-list/index.js:22 `const user = getAuthUser();`；apps/miniprogram/pages/program-list/index.js:23 `const previewMode = !!(user && ["researcher", "supervisor", "admin"].includes(user.role));`；apps/miniprogram/pages/program-list/index.js:25 `.listPrograms(previewMode ? { include_drafts: true } : {})`；apps/miniprogram/pages/program-list/index.js:31 `previewMode,`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 15 项目详情 — `pages/program-detail/index`

**用户任务：** 核对项目边界、切换小节、填写与保存草稿、授权后提交并回看；预览只读。
- 页面源码：`apps/miniprogram/pages/program-detail/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{program}}`；`{{previewMode}}`；`{{program.neutral_alternative}}`；`{{program.interpretation_boundary}}`；`{{program.clinical_boundary}}`；`{{program.measurementPlan}}`；`{{selectedSession}}`；`{{selectedSession.writing_prompt}}`；`{{!previewMode}}`；`{{!previewMode}}`；`{{!previewMode}}`；`{{!previewMode}}`；`{{successMessage}}`；`{{errorMessage}}`；`{{!previewMode && submittedEntries.length}}`；`{{loading}}`；`{{errorMessage}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 55 | 第 节 | `bindtap → selectSession` | {"session-no":"{{item.session_no}}"} |
| 82 | 保存本机草稿 | `bindinput → onDraftInput` | {} |
| 83 | 保存本机草稿 | `bindtap → saveDraft` | {} |
| 90 | textarea | `bindinput → onReflectionInput` | {"index":"{{index}}"} |
| 107 | 练习后不适程度： / 10 | `bindchange → onDistressBeforeChange` | {} |
| 109 | 这次练习出现了明显不适或负面体验，需要后续关注。 | `bindchange → onDistressAfterChange` | {} |
| 110 | 这次练习出现了明显不适或负面体验，需要后续关注。 | `bindchange → onAdverseResponseChange` | {} |
| 116 | 允许将本次内容用于脱敏聚合分析，不默认展示原文。 | `bindchange → onAnalysisConsentChange` | {} |
| 124 | 登录后正式提交 | `bindtap → submitEntry` | {} |
| 148 | 重试 | `bindtap → retryLoad` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/program-detail/index.js:69` | `getProgram` | GET /api/programs/<program_id> | backend/routes/programs.py:104 / programs.get_program / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/program-detail/index.js:172` | `listProgramEntries` | GET /api/programs/<program_id>/entries | backend/routes/programs.py:122 / programs.list_program_entries / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/program-detail/index.js:203` | `createProgramEntry` | POST /api/programs/<program_id>/entries | backend/routes/programs.py:159 / programs.create_program_entry / self_only_or_dedicated_domain_command |

- 下游路由：
- 本地保存：getStorageSync draftKey；setStorageSync draftKey；removeStorageSync draftKey
- 权限/预览线索：apps/miniprogram/pages/program-detail/index.js:38 `previewMode: false,`；apps/miniprogram/pages/program-detail/index.js:57 `const previewMode = query.preview === "1";`；apps/miniprogram/pages/program-detail/index.js:59 `this.setData({ programId, previewMode, requestedSessionNo });`；apps/miniprogram/pages/program-detail/index.js:70 `.getProgram(programId, this.data.previewMode ? { include_drafts: true } : {})`；apps/miniprogram/pages/program-detail/index.js:87 `if (!this.data.previewMode) this.loadSubmittedEntries();`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 16 关系探索试点 — `pages/relationship-pilot/index`

**用户任务：** 核对资格与报名同意，沿真实五阶段状态继续；角色与参与者保护保持不变。
- 页面源码：`apps/miniprogram/pages/relationship-pilot/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{roleBlocked}}`；`{{!enrollment}}`；`{{errorMessage}}`
- 组件：`page-state`、`journey-action-card`、`status-pill`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 19 | 我已阅读并同意将本次测评用于关系探索试点的评估与复盘。 | `bindchange → toggleConsent` | {} |
| 22 | 确认报名 | `bindtap → enroll` | {} |
| 23 | 还没测评？先完成关系测一测 | `bindtap → goAssessment` | {} |
| 27 | 关系探索当前步骤 | `bindaction → runPrimaryAction` | {} |
| 56 | button | `bindtap → runSecondaryAction` | {"action":"{{item.key}}"} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/relationship-pilot/index.js:69` | `getShowcaseAccess` | GET /api/showcase-access | backend/routes/showcase_access.py:13 / showcase_access.get_showcase_access / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/relationship-pilot/index.js:81` | `listRelationshipEnrollments` | GET /api/relationship-pilot/enrollments | backend/routes/relationship_pilot_routes.py:80 / relationship_pilot.list_enrollments_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/relationship-pilot/index.js:86` | `getRelationshipGrowth` | GET /api/relationship-pilot/growth | backend/routes/relationship_pilot_routes.py:190 / relationship_pilot.relationship_growth_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/relationship-pilot/index.js:129` | `createRelationshipEnrollment` | POST /api/relationship-pilot/enrollments | backend/routes/relationship_pilot_routes.py:69 / relationship_pilot.create_enrollment_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/relationship-pilot/index.js:149` | `trackProductEvent` | POST /api/product-events | backend/routes/product_events.py:63 / product_events.create_product_event / role_scoped |

- 下游路由：navigateTo → /pages/assessment/index?audience_class=student&query=%E5%85%B3%E7%B3%BB；navigateTo → /pages/relationship-report/index?id=:dynamic；navigateTo → /pages/relationship-task/index?type=relationship_drawing&enrollment_id=:dynamic；navigateTo → /pages/relationship-task/index?type=sentence_completion&enrollment_id=:dynamic；navigateTo → /pages/relationship-growth/index?detail=1&enrollment_id=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/relationship-pilot/index.js:67 `if (!requireLogin({ redirectUrl: "/pages/relationship-pilot/index" })) return;`；apps/miniprogram/pages/relationship-pilot/index.js:68 `const user = getAuthUser();`；apps/miniprogram/pages/relationship-pilot/index.js:70 `if (!showcase.enabled && (!user \|\| !["student", "admin"].includes(user.role))) {`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；journey-action-card → action/retry
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 17 阶段性报告 — `pages/relationship-report/index`

**用户任务：** 阅读已获准报告，核对假设与反馈、查看真实维度及导出；未交付状态不泄漏。
- 页面源码：`apps/miniprogram/pages/relationship-report/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{deliveryPending}}`；`{{attentionNotice}}`；`{{radarRows.length}}`；`{{report.four_layer_profile.tension.clues.length}}`；`{{mechanismCards.length}}`；`{{report.four_layer_profile.dynamic.rounds_count >= 2}}`
- 组件：`page-state`、`relationship-status`、`feedback-rating`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 3 | 正在人工核对 | `bindaction → loadReport` | {} |
| 32 | feedback-rating | `bindselect → submitReportEvaluation` | {} |
| 62 | 符合 | `bindtap → saveHypothesisFeedback` | {"index":"{{item.index}}","response":"matches"} |
| 63 | 不符合 | `bindtap → saveHypothesisFeedback` | {"index":"{{item.index}}","response":"does_not_match"} |
| 64 | 不确定 | `bindtap → saveHypothesisFeedback` | {"index":"{{item.index}}","response":"uncertain"} |
| 99 | 生成脱敏报告长图 | `bindtap → drawLongImage` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/relationship-report/index.js:81` | `getRelationshipReport` | GET /api/relationship-pilot/reports/<report_id> | backend/routes/relationship_pilot_routes.py:104 / relationship_pilot.get_report_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/relationship-report/index.js:127` | `saveRelationshipHypothesisFeedback` | PUT /api/relationship-pilot/reports/<report_id>/hypotheses/<int:hypothesis_index> | backend/routes/relationship_pilot_routes.py:120 / relationship_pilot.save_hypothesis_feedback_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/relationship-report/index.js:145` | `createFeedbackLedgerEntry` | POST /api/feedback-ledger | backend/routes/feedback_ledger.py:24 / feedback_ledger.create_entry / role_scoped |
| `apps/miniprogram/pages/relationship-report/index.js:222` | `trackProductEvent` | POST /api/product-events | backend/routes/product_events.py:63 / product_events.create_product_event / role_scoped |

- 下游路由：
- 本地保存：
- 组件事件转发：page-state → action；feedback-rating → select
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 18 关系探索任务 — `pages/relationship-task/index`

**用户任务：** 完成绘画或句子补全；撤销/重做、跳过、草稿、授权与风险转人工保持原行为。
- 页面源码：`apps/miniprogram/pages/relationship-task/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{draftRestored}}`；`{{isDrawing}}`；`{{item.answered}}`；`{{item.expanded}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 13 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchstart → startStroke` | {} |
| 13 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchmove → moveStroke` | {} |
| 13 | 关系感受绘画画布，可使用下方按钮撤销、重做或清空 | `bindtouchend → endStroke` | {} |
| 15 | 撤销 | `bindtap → undoStroke` | {} |
| 16 | 重做 | `bindtap → redoStroke` | {} |
| 17 | 清空 | `bindtap → clearCanvas` | {} |
| 21 | textarea | `bindinput → onNarrationInput` | {} |
| 28 | button | `bindtap → toggleContext` | {"key":"{{item.key}}"} |
| 34 | textarea | `bindinput → onSentenceInput` | {"key":"{{item.key}}"} |
| 41 | 我同意将这份敏感叙事材料用于本次试点评估与人工复核；默认不导出原文。 | `bindchange → toggleConsent` | {} |
| 45 | 提交这份材料 | `bindtap → saveTask` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/relationship-task/index.js:318` | `createRelationshipTask` | POST /api/relationship-pilot/enrollments/<enrollment_id>/tasks | backend/routes/relationship_pilot_routes.py:156 / relationship_pilot.create_task_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/relationship-task/index.js:328` | `trackProductEvent` | POST /api/product-events | backend/routes/product_events.py:63 / product_events.create_product_event / role_scoped |

- 下游路由：
- 本地保存：getStorageSync this；removeStorageSync this；setStorageSync this
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 19 关系探索成长记录 — `pages/relationship-growth/index`

**用户任务：** 按真实指标和事件复盘；保留四类切换、表单、草稿、时间线与分开量尺。
- 页面源码：`apps/miniprogram/pages/relationship-growth/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{growth}}`；`{{activeSection === 'curve'}}`；`{{curveGroups.length}}`；`{{selectedPoints.length >= 2}}`；`{{selectedPoints.length >= 2}}`；`{{recentTimeline.length}}`；`{{activeSection === 'timeline'}}`；`{{filteredTimeline.length}}`；`{{activeSection === 'feedback'}}`；`{{researcherConfirmations.length}}`；`{{showSelfNarratives}}`；`{{!selfNarratives.length}}`；`{{activeSection === 'records'}}`；`{{!canRecord}}`；`{{canRecord}}`；`{{showWeeklyForm}}`；`{{slowSaving}}`；`{{canRecord}}`；`{{showEventForm}}`；`{{errorMessage}}`
- 组件：`page-state`、`visualization-state`、`timeline-record`、`bamboo-timeline-node`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 25 | 查看{{item.label}} | `bindtap → selectSection` | {"section":"{{item.key}}"} |
| 35 | button | `bindtap → selectCurveGroup` | {"key":"{{item.key}}"} |
| 36 | button | `bindtap → selectMetric` | {"key":"{{item.key}}"} |
| 56 | 查看全部 › | `bindtap → showAllTimeline` | {} |
| 67 | button | `bindtap → selectTimelineFilter` | {"key":"{{item.key}}"} |
| 78 | 用户原话（仅你可见） | `bindtap → toggleSelfNarratives` | {} |
| 86 | 前往关系探索 | `bindtap → goRelationshipPilot` | {} |
| 90 | 本周补充记录 | `bindtap → toggleRecordPanel` | {"panel":"weekly"} |
| 92 | input | `bindinput → onFieldInput` | {"key":"active_social_count"} |
| 93 | input | `bindinput → onFieldInput` | {"key":"authentic_expression_count"} |
| 94 | textarea | `bindinput → onFieldInput` | {"key":"setback_coping"} |
| 95 | slider | `bindchange → onSliderChange` | {"key":"approach_willingness"} |
| 96 | slider | `bindchange → onSliderChange` | {"key":"worry_intensity"} |
| 97 | textarea | `bindinput → onFieldInput` | {"key":"achievement"} |
| 98 | textarea | `bindinput → onFieldInput` | {"key":"setback"} |
| 101 | 保存本周记录 | `bindtap → saveWeekly` | {} |
| 106 | 记录一个关键事件 | `bindtap → toggleRecordPanel` | {"panel":"event"} |
| 108 | textarea | `bindinput → onFieldInput` | {"key":"event_summary"} |
| 110 | 加入时间线 | `bindtap → saveEvent` | {} |
| 116 | 共同理解一次关系体验 | `bindtap → goTherapeuticAssessment` | {} |
| 117 | 记录今天的一小步 | `bindtap → openRecordSection` | {} |
| 118 | 查看阶段性反馈 | `bindtap → showFeedbackSection` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/relationship-growth/index.js:182` | `getRelationshipGrowth` | GET /api/relationship-pilot/growth | backend/routes/relationship_pilot_routes.py:190 / relationship_pilot.relationship_growth_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/relationship-growth/index.js:400` | `createRelationshipLongitudinal` | POST /api/relationship-pilot/enrollments/<enrollment_id>/longitudinal | backend/routes/relationship_pilot_routes.py:173 / relationship_pilot.create_longitudinal_entry_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/therapeutic-assessment/index；redirectTo → /pages/growth-dashboard/index?section=relationship:dynamic；navigateTo → /pages/relationship-pilot/index
- 本地保存：getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 20 共同理解 — `pages/therapeutic-assessment/index`

**用户任务：** 开始或继续获准协作，查看成人范围、责任链与反馈/行动；治理状态不冒充已批准。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{notice}}`；`{{errorMessage}}`；`{{activeCase}}`；`{{activeCase}}`；`{{activeCase}}`；`{{loading}}`；`{{activeCase}}`；`{{activeCase.working_question && activeCase.working_question !== activeCase.assessment_question}}`；`{{activeCase.latestFeedback}}`；`{{evidenceSummary && evidenceSummary.item_count}}`；`{{evidenceItems.length}}`；`{{activeCase && activeCase.latestFeedback}}`；`{{productionContract}}`；`{{adultLaunchScope}}`；`{{activeCase && (!launchScreening \|\| launchScreening.decision === 'screening_required')}}`；`{{launchScreening}}`；`{{childPolicy}}`；`{{multiPartyPolicy}}`；`{{aiAssistPolicy}}`；`{{methodCatalog}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 18 | 继续最近一次协作 | `bindtap → continueParticipantFlow` | {} |
| 19 | 开始一次协作 | `bindtap → startParticipantFlow` | {} |
| 20 | 开始新的议题 | `bindtap → startParticipantFlow` | {} |
| 36 | 查看两个问题候选 | `bindtap → updateQuestionAction` | {"action":"generate_candidates"} |
| 37 | 都不符合 | `bindtap → updateQuestionAction` | {"action":"none_fit"} |
| 63 | 这和我的体验不一致 | `bindtap → disagree` | {} |
| 64 | 暂时停一下 | `bindtap → updateQuestionAction` | {"action":"pause"} |
| 65 | 更正与投诉 | `bindtap → openQualityRecord` | {} |
| 67 | 撤回本次协作 | `bindtap → withdraw` | {} |
| 73 | textarea | `bindinput → onActionInput` | {} |
| 74 | 记录下一小步 | `bindtap → chooseAction` | {} |
| 80 | textarea | `bindinput → onQuestionInput` | {} |
| 82 | 上面的问题 | `bindchange → onScopeChange` | {} |
| 86 | 提交协作问题 | `bindtap → createCase` | {} |
| 108 | 确认符合上述范围 | `bindtap → confirmAdultLaunchScope` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/therapeutic-assessment/index.js:84` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:85` | `getTherapeuticAssessmentServiceLevels` | GET /api/therapeutic-assessment/service-levels | backend/routes/therapeutic_assessment.py:334 / therapeutic_assessment.get_service_levels_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:86` | `getTherapeuticAssessmentProductionContract` | GET /api/therapeutic-assessment/production-contract | backend/routes/therapeutic_assessment.py:340 / therapeutic_assessment.get_production_contract_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:87` | `getTherapeuticAssessmentAdultLaunchScope` | GET /api/therapeutic-assessment/launch-scope | backend/routes/therapeutic_assessment.py:178 / therapeutic_assessment.get_launch_scope_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:88` | `getTherapeuticAssessmentChildPolicy` | GET /api/therapeutic-assessment/child-safeguards | backend/routes/therapeutic_assessment.py:184 / therapeutic_assessment.get_child_safeguards_policy_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:89` | `getTherapeuticAssessmentMultiPartyPolicy` | GET /api/therapeutic-assessment/multi-party-safeguards | backend/routes/therapeutic_assessment.py:190 / therapeutic_assessment.get_multi_party_policy_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:90` | `getTherapeuticAssessmentAiAssistPolicy` | GET /api/therapeutic-assessment/ai-assist | backend/routes/therapeutic_assessment.py:196 / therapeutic_assessment.get_ai_assist_policy_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:91` | `getTherapeuticAssessmentMethodLibrary` | GET /api/therapeutic-assessment/method-library | backend/routes/therapeutic_assessment.py:202 / therapeutic_assessment.get_method_library_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:111` | `listTherapeuticAssessmentEvidence` | GET /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:482 / therapeutic_assessment.get_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:112` | `getTherapeuticAssessmentLaunchScreening` | GET /api/therapeutic-assessment/cases/<case_id>/launch-screenings/latest | backend/routes/therapeutic_assessment.py:328 / therapeutic_assessment.get_latest_launch_screening_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:135` | `submitTherapeuticAssessmentLaunchScreening` | POST /api/therapeutic-assessment/cases/<case_id>/launch-screenings | backend/routes/therapeutic_assessment.py:322 / therapeutic_assessment.post_launch_screening_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:188` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:210` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:230` | `updateTherapeuticAssessmentQuestion` | PATCH /api/therapeutic-assessment/cases/<case_id>/question | backend/routes/therapeutic_assessment.py:470 / therapeutic_assessment.patch_question_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment/index.js:254` | `transitionTherapeuticAssessment` | POST /api/therapeutic-assessment/cases/<case_id>/actions；POST /api/therapeutic-assessment/cases/<case_id>/assign；POST /api/therapeutic-assessment/cases/<case_id>/child-safeguards；POST /api/therapeutic-assessment/cases/<case_id>/data-items；POST /api/therapeutic-assessment/cases/<case_id>/disagree；POST /api/therapeutic-assessment/cases/<case_id>/evidence；POST /api/therapeutic-assessment/cases/<case_id>/feedback-versions；POST /api/therapeutic-assessment/cases/<case_id>/launch-screenings；POST /api/therapeutic-assessment/cases/<case_id>/multi-party-safeguards；POST /api/therapeutic-assessment/cases/<case_id>/quality-incidents；POST /api/therapeutic-assessment/cases/<case_id>/readiness；POST /api/therapeutic-assessment/cases/<case_id>/safety-signals；POST /api/therapeutic-assessment/cases/<case_id>/transitions；POST /api/therapeutic-assessment/cases/<case_id>/withdraw；POST /api/therapeutic-assessment/cases/<case_id>/work-queue | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:680 / therapeutic_assessment.post_assign_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:292 / therapeutic_assessment.post_child_safeguard_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:608 / therapeutic_assessment.post_data_item_route / case_participant_owned_data_item_creation；backend/routes/therapeutic_assessment.py:668 / therapeutic_assessment.post_disagree_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:692 / therapeutic_assessment.post_feedback_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:322 / therapeutic_assessment.post_launch_screening_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:254 / therapeutic_assessment.post_multi_party_safeguard_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:800 / therapeutic_assessment.post_quality_incident_route / participant_owned_or_authorized_case_quality_incident_append_only；backend/routes/therapeutic_assessment.py:686 / therapeutic_assessment.post_readiness_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:650 / therapeutic_assessment.post_safety_signal_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:476 / therapeutic_assessment.post_transition_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:674 / therapeutic_assessment.post_withdraw_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin；backend/routes/therapeutic_assessment.py:368 / therapeutic_assessment.post_work_queue_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：navigateTo → /pages/therapeutic-assessment-boundary/index；navigateTo → /pages/therapeutic-assessment-boundary/index?caseId=:dynamic；navigateTo → /pages/therapeutic-assessment-quality/index:dynamic
- 本地保存：
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 21 开始前了解 — `pages/therapeutic-assessment-boundary/index`

**用户任务：** 自主决定开始或退出；安全暂停、登录与草稿状态来自共享流程。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-boundary/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`boundary`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 22 我的议题 — `pages/therapeutic-assessment-issue/index`

**用户任务：** 写下议题并创建/继续协作；原文、草稿、服务端版本及校验保留。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-issue/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`issue`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 23 最近一次事件 — `pages/therapeutic-assessment-recent-event/index`

**用户任务：** 记录具体事件，保存证据后继续；不自动推断动机或机制。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-recent-event/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`recent_event`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 24 例外与资源 — `pages/therapeutic-assessment-resources/index`

**用户任务：** 记录例外时刻与已有资源；不增加无依据的资源推荐。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-resources/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`resources`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 25 资料与共享 — `pages/therapeutic-assessment-sharing/index`

**用户任务：** 选择真实共享范围；账号关联不意味着自动共享，撤回与最小范围保留。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-sharing/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`sharing`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 26 提交前摘要 — `pages/therapeutic-assessment-summary/index`

**用户任务：** 区分原话和整理版本并核对；不覆盖原话，不将空版本填成假总结。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-summary/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`summary`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 27 反馈核对 — `pages/therapeutic-assessment-feedback-check/index`

**用户任务：** 阅读已发送反馈并表达接近程度；不同意见、补充输入与保存状态保留。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-feedback-check/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`feedback_check`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 28 一个小行动 — `pages/therapeutic-assessment-action-review/index`

**用户任务：** 安排自愿的小行动、目的、日期、提醒、停止与回看；不强迫完成。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-action-review/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 共享流程分支：`action_review`。
- 实际条件：
- 组件：`page-state`、`therapeutic-flow-step`、`therapeutic-choice-option`、`therapeutic-textarea`、`therapeutic-comparison`、`therapeutic-feedback-letter`、`therapeutic-compact-textarea`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 1 | therapeutic-flow-step | `bindvaluechange → onValueChange` | {} |
| 1 | therapeutic-flow-step | `bindoptionchange → onOptionChange` | {} |
| 1 | therapeutic-flow-step | `bindactionchange → onActionChange` | {} |
| 1 | therapeutic-flow-step | `bindcontinue → onContinue` | {} |
| 1 | therapeutic-flow-step | `bindretry → onRetry` | {} |
| 1 | therapeutic-flow-step | `bindback → onBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:185` | `getTherapeuticAssessmentStopRecoveryStatus` | GET /api/therapeutic-assessment/stop-recovery/status | backend/routes/therapeutic_assessment.py:548 / therapeutic_assessment.get_stop_recovery_status_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:200` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:252` | `getTherapeuticAssessmentParticipantDraft` | GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:626 / therapeutic_assessment.get_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:324` | `saveTherapeuticAssessmentParticipantDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id> | backend/routes/therapeutic_assessment.py:632 / therapeutic_assessment.put_participant_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:366` | `createTherapeuticAssessmentCase` | POST /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:452 / therapeutic_assessment.post_case_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:394` | `createTherapeuticAssessmentEvidence` | POST /api/therapeutic-assessment/cases/<case_id>/evidence | backend/routes/therapeutic_assessment.py:488 / therapeutic_assessment.post_evidence_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:419` | `updateTherapeuticAssessmentScope` | PATCH /api/therapeutic-assessment/cases/<case_id>/scope | backend/routes/therapeutic_assessment.py:464 / therapeutic_assessment.patch_scope_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:429` | `respondToTherapeuticAssessmentFeedback` | POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses | backend/routes/therapeutic_assessment.py:710 / therapeutic_assessment.post_feedback_response_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:442` | `createTherapeuticAssessmentAction` | POST /api/therapeutic-assessment/cases/<case_id>/actions | backend/routes/therapeutic_assessment.py:734 / therapeutic_assessment.post_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment-action-followup/index?caseId=:dynamic；redirectTo → /pages/therapeutic-assessment/index；redirectTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:150 `if (!requireLogin({ redirectUrl: route(stepId, caseId), message: "请先登录后再继续本次协作。" })) {`；apps/miniprogram/utils/therapeuticAssessmentParticipantFlow.js:391 `const actor = getAuthUser() \|\| {};`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；therapeutic-flow-step → valuechange/optionchange/actionchange/continue/retry/back；therapeutic-choice-option → change；therapeutic-textarea → input；therapeutic-compact-textarea → input
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 29 行动回看 — `pages/therapeutic-assessment-action-followup/index`

**用户任务：** 回看原行动并记录尝试/停止/放弃等真实状态及新观察；不评分、不奖励。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-action-followup/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{error}}`；`{{action}}`；`{{action.training_card_id}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 8 | page-state | `bindaction → load` | {} |
| 29 | 尝试过 | `bindtap → selectStatus` | {"value":"completed"} |
| 30 | 中途停止 | `bindtap → selectStatus` | {"value":"stopped"} |
| 31 | 决定不做 | `bindtap → selectStatus` | {"value":"declined"} |
| 36 | 新的观察 | `bindtap → selectKind` | {"value":"O"} |
| 37 | 仍待了解 | `bindtap → selectKind` | {"value":"U"} |
| 40 | 行动回看内容 | `bindinput → onNoteInput` | {} |
| 41 | 打开关联训练卡 | `bindtap → openTrainingCard` | {} |
| 42 | 保存这次回看 | `bindtap → submit` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/therapeutic-assessment-action-followup/index.js:40` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment-action-followup/index.js:73` | `updateTherapeuticAssessmentAction` | PATCH /api/therapeutic-assessment/actions/<action_id> | backend/routes/therapeutic_assessment.py:740 / therapeutic_assessment.patch_action_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment-action-followup/index.js:82` | `createTherapeuticAssessmentActionFollowup` | POST /api/therapeutic-assessment/actions/<action_id>/followups | backend/routes/therapeutic_assessment.py:746 / therapeutic_assessment.post_action_followup_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |

- 下游路由：redirectTo → /pages/therapeutic-assessment/index；navigateTo → /pages/training-card/index?id=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/therapeutic-assessment-action-followup/index.js:26 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 30 评估质量与更正 — `pages/therapeutic-assessment-quality/index`

**用户任务：** 参与者提交更正/投诉并查处理；复核角色按权限查看队列和质量处置。
- 页面源码：`apps/miniprogram/pages/therapeutic-assessment-quality/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{!loading && !runtime && !productionGate && !cases.length && !reviews.length && !incidents.length && !errorMessage}}`；`{{runtime}}`；`{{errorMessage}}`；`{{notice}}`；`{{loading}}`；`{{productionGate}}`；`{{!loading && cases.length}}`；`{{isReviewRole && !loading}}`；`{{!reviews.length}}`；`{{selectedReview}}`；`{{selectedReview.status === 'pending'}}`；`{{selectedReview.status === 'in_review'}}`；`{{item.status === 'concern'}}`；`{{isReviewRole && !loading}}`；`{{!incidents.length}}`；`{{selectedIncident}}`；`{{selectedIncident.status === 'reported'}}`；`{{selectedIncident.status === 'independent_review'}}`；`{{selectedIncident.status === 'resolved'}}`；`{{!loading && incidents.length && !isReviewRole}}`；`{{item.resolution_summary}}`；`{{isReviewRole}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 18 | 重新读取 | `bindtap → loadData` | {} |
| 51 | picker | `bindchange → onCaseChange` | {} |
| 56 | picker | `bindchange → onIncidentCategory` | {} |
| 61 | textarea | `bindinput → onFieldInput` | {"key":"incidentDescription"} |
| 65 | textarea | `bindinput → onFieldInput` | {"key":"requestedResolution"} |
| 67 | 提交更正或投诉 | `bindtap → submitIncident` | {} |
| 83 | button | `bindtap → selectReview` | {"id":"{{item.id}}"} |
| 97 | 认领这项复核 | `bindtap → claimReview` | {} |
| 101 | 结论： | `bindchange → onDimensionStatus` | {"index":"{{index}}"} |
| 105 | input | `bindinput → onDimensionInput` | {"index":"{{index}}","key":"note"} |
| 106 | input | `bindinput → onDimensionInput` | {"index":"{{index}}","key":"evidenceRef"} |
| 111 | textarea | `bindinput → onFieldInput` | {"key":"remediationSummary"} |
| 113 | 提交质量结论 | `bindtap → completeReview` | {} |
| 130 | button | `bindtap → selectIncident` | {"id":"{{item.id}}"} |
| 141 | textarea | `bindinput → onFieldInput` | {"key":"impactSummary"} |
| 143 | 保存影响分析 | `bindtap → analyzeIncident` | {} |
| 146 | 处理动作： | `bindchange → onResolutionAction` | {} |
| 151 | textarea | `bindinput → onFieldInput` | {"key":"resolutionSummary"} |
| 153 | 独立结案并通知参与者 | `bindtap → resolveIncident` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:85` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:86` | `listTherapeuticAssessmentQualityIncidents` | GET /api/therapeutic-assessment/quality/incidents | backend/routes/therapeutic_assessment.py:806 / therapeutic_assessment.get_quality_incidents_route / participant_owned_assigned_or_task_authorized_quality_incident_history |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:88` | `listTherapeuticAssessmentQualityReviews` | GET /api/therapeutic-assessment/quality/reviews | backend/routes/therapeutic_assessment.py:782 / therapeutic_assessment.get_quality_reviews_route / task_authorized_case_scoped_quality_review_with_version_and_independence_gates |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:91` | `getTherapeuticAssessmentProductionGate` | GET /api/therapeutic-assessment/production-gate | backend/routes/therapeutic_assessment.py:512 / therapeutic_assessment.get_production_gate_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:171` | `claimTherapeuticAssessmentQualityReview` | POST /api/therapeutic-assessment/quality/reviews/<review_id>/claim | backend/routes/therapeutic_assessment.py:788 / therapeutic_assessment.post_quality_review_claim_route / task_authorized_case_scoped_quality_review_with_version_and_independence_gates |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:232` | `completeTherapeuticAssessmentQualityReview` | POST /api/therapeutic-assessment/quality/reviews/<review_id>/complete | backend/routes/therapeutic_assessment.py:794 / therapeutic_assessment.post_quality_review_complete_route / task_authorized_case_scoped_quality_review_with_version_and_independence_gates |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:266` | `createTherapeuticAssessmentQualityIncident` | POST /api/therapeutic-assessment/cases/<case_id>/quality-incidents | backend/routes/therapeutic_assessment.py:800 / therapeutic_assessment.post_quality_incident_route / participant_owned_or_authorized_case_quality_incident_append_only |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:298` | `analyzeTherapeuticAssessmentQualityIncident` | POST /api/therapeutic-assessment/quality/incidents/<incident_id>/impact-analysis | backend/routes/therapeutic_assessment.py:812 / therapeutic_assessment.post_quality_incident_analysis_route / participant_owned_assigned_or_task_authorized_quality_incident_history |
| `apps/miniprogram/pages/therapeutic-assessment-quality/index.js:330` | `resolveTherapeuticAssessmentQualityIncident` | POST /api/therapeutic-assessment/quality/incidents/<incident_id>/resolve | backend/routes/therapeutic_assessment.py:818 / therapeutic_assessment.post_quality_incident_resolution_route / participant_owned_assigned_or_task_authorized_quality_incident_history |

- 下游路由：navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/therapeutic-assessment-quality/index.js:62 `if (!requireLogin({ redirectUrl: "/pages/therapeutic-assessment-quality/index" })) return;`；apps/miniprogram/pages/therapeutic-assessment-quality/index.js:63 `const user = getAuthUser() \|\| {};`；apps/miniprogram/pages/therapeutic-assessment-quality/index.js:66 `isReviewRole: ["supervisor", "admin"].includes(user.role),`；apps/miniprogram/pages/therapeutic-assessment-quality/index.js:67 `isFormalRole: ["researcher", "supervisor", "admin"].includes(user.role),`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 31 我的成长仪表盘 — `pages/growth-dashboard/index`

**用户任务：** 按真实类别复盘记录与练习、关系等线索；无数据不绘制虚假趋势，不合成总分。
- 页面源码：`apps/miniprogram/pages/growth-dashboard/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{growth}}`；`{{activeSection === 'activity'}}`；`{{thermometer.length}}`；`{{activityTimeline.length}}`；`{{activeSection === 'assessments'}}`；`{{assessmentGroups.length}}`；`{{activeSection === 'relationship'}}`；`{{relationshipTimeline.length}}`；`{{feedbackTimeline.length}}`
- 组件：`page-state`、`status-pill`、`timeline-record`、`bamboo-timeline-node`、`growth-segment`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 9 | 重新读取成长线索 | `bindaction → loadGrowth` | {} |
| 13 | growth-segment | `bindchange → selectSection` | {} |
| 29 | 记录一件小事 | `bindtap → startDiary` | {} |
| 30 | 查看练习 | `bindtap → openTraining` | {} |
| 53 | page-state | `bindaction → startDiary` | {} |
| 69 | page-state | `bindaction → openAssessment` | {} |
| 82 | button | `bindtap → openRelationship` | {} |
| 103 | 打开消息列表 | `bindtap → openMessages` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/growth-dashboard/index.js:64` | `getGrowthOverview` | GET /api/growth/overview | backend/routes/general_growth.py:23 / general_growth.get_growth_overview / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/diary-form/index；switchTab → /pages/training/index；navigateTo → /pages/assessment/index；navigateTo → /pages/relationship-pilot/index；navigateTo → /pages/relationship-growth/index?detail=1&enrollment_id=:dynamic；navigateTo → /pages/messages/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/growth-dashboard/index.js:54 `if (!requireLogin({ redirectUrl: "/pages/growth-dashboard/index" })) return;`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；growth-segment → change
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 32 关系探索手记 — `pages/relationship-narrative/index`

**用户任务：** 阅读已授权手记、问题、材料及人工补充，再进入真实下一任务。
- 页面源码：`apps/miniprogram/pages/relationship-narrative/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{isResearcherView && noteRows.length}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 3 | page-state | `bindaction → retryLoad` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/relationship-narrative/index.js:15` | `getRelationshipNarrative` | GET /api/relationship-pilot/narratives/<narrative_id> | backend/routes/relationship_pilot_routes.py:231 / relationship_pilot.get_narrative_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |

- 下游路由：
- 本地保存：
- 权限/预览线索：apps/miniprogram/pages/relationship-narrative/index.js:20 `isResearcherView: narrative.audience === "researcher",`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 33 研究者移动工作台 — `pages/researcher-dashboard/index`

**用户任务：** 在授权范围内处理队列、查看档案/证据/交付及知识检索、情感影子和网络合成摘要；数据和角色隔离。
- 页面源码：`apps/miniprogram/pages/researcher-dashboard/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{offline}}`；`{{developmentFullAccess}}`；`{{capabilityScope}}`；`{{loading && !operations}}`；`{{errorMessage}}`；`{{partialFailures.length}}`；`{{activeWorkspace === 'pending' && !errorMessage}}`；`{{assessmentQueueRuntime}}`；`{{publicationCandidateSummary}}`；`{{assessmentLifecycleSummary}}`；`{{!pendingVisibleItems.length}}`；`{{pendingHasMore}}`；`{{activeWorkspace === 'participants'}}`；`{{participantError}}`；`{{participantLoading && !participantItems.length}}`；`{{!participantItems.length && !participantError}}`；`{{participantItems.length}}`；`{{participantHasMore}}`；`{{participantDossier}}`；`{{participantModuleLoading}}`；`{{participantModule}}`；`{{!participantModule.items.length}}`；`{{record.exploratoryAnalysis}}`；`{{record.reason}}`；`{{record.availability === 'available'}}`；`{{record.affectSummary}}`；`{{record.affectNextCheck}}`；`{{record.networkSummary}}`；`{{!record.networkRows.length}}`；`{{record.networkNextCheck}}`；`{{participantModule.has_more}}`；`{{activeWorkspace === 'feedback'}}`；`{{activeWorkspace === 'assessment'}}`；`{{assessmentCases.length}}`；`{{assessmentError}}`；`{{assessmentLoading}}`；`{{!assessmentCases.length}}`；`{{assessmentWorkbench}}`；`{{assessmentWorkbench.evidence_summary}}`；`{{!assessmentWorkbench.evidence_items.length}}`；`{{item.source_ref}}`；`{{item.observed_at}}`；`{{item.provider_id}}`；`{{item.context}}`；`{{item.kind === 'H'}}`；`{{activeWorkspace === 'analysis'}}`；`{{analysisCatalog}}`；`{{analysisResilience}}`；`{{affectShadowRuns.length}}`；`{{item.reviewReasonText}}`；`{{affectMonitoring}}`；`{{affectMonitoring}}`；`{{affectReleaseGate}}`；`{{affectReleaseGate}}`；`{{knowledgeInventory}}`；`{{knowledgeError}}`；`{{knowledgeResult}}`；`{{knowledgeResult.retrieval_summary}}`；`{{!knowledgeResult.citations.length}}`；`{{networkPolicy}}`；`{{offlineBenchmarkRuns.length}}`；`{{item.networkDetailText}}`；`{{item.networkNextCheck}}`；`{{analysisLoading}}`；`{{analysisError}}`；`{{!analysisJobs.length}}`；`{{item.qualityText}}`；`{{item.suppressed}}`；`{{activeWorkspace === 'mine'}}`；`{{activeWorkspace === 'pilots'}}`；`{{pilotLoading && !items.length}}`；`{{pilotError}}`；`{{!items.length}}`；`{{selected}}`；`{{selected.latestReport}}`；`{{selected.latestReport.status === 'pending_review' \|\| selected.latestReport.status === 'ready'}}`；`{{selected.latestReport.status === 'confirmed' \|\| selected.latestReport.status === 'updated'}}`；`{{selected.latestReport.status === 'sent'}}`；`{{stageFeedbackDelivery}}`；`{{!stageFeedbackDelivery \|\| stageFeedbackDelivery.status === 'draft' \|\| stageFeedbackDelivery.status === 'previewed'}}`；`{{stageFeedbackDelivery.status === 'previewed'}}`；`{{stageFeedbackDelivery.status === 'confirmed'}}`；`{{stageFeedbackDelivery.status === 'sent'}}`；`{{participantMessageDelivery}}`；`{{!participantMessageDelivery \|\| participantMessageDelivery.status === 'draft' \|\| participantMessageDelivery.status === 'previewed'}}`；`{{participantMessageDelivery.status === 'previewed'}}`；`{{participantMessageDelivery.status === 'confirmed'}}`；`{{participantMessageDelivery.status === 'sent'}}`；`{{item.narration}}`；`{{selected.drawingTask}}`；`{{narrative}}`；`{{narrative.status !== 'confirmed'}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 7 | 刷新当前工作区 | `bindtap → refreshActiveWorkspace` | {} |
| 29 | button | `bindtap → switchWorkspace` | {"id":"{{item.id}}"} |
| 41 | 重新同步 | `bindtap → loadWorkbench` | {} |
| 42 | 复制诊断信息 | `bindtap → copyDiagnostic` | {"scope":"workbench"} |
| 49 | 重试未完成同步 | `bindtap → loadWorkbench` | {} |
| 105 | 刷新待处理列表 | `bindtap → loadWorkbench` | {} |
| 121 | 继续查看 | `bindtap → showMorePending` | {} |
| 133 | 搜索参与者 | `bindinput → onParticipantQueryInput` | {} |
| 142 | 重新加载 | `bindtap → retryParticipants` | {} |
| 143 | 复制诊断信息 | `bindtap → copyDiagnostic` | {"scope":"participants"} |
| 155 | 查看{{item.displayName}}的参与者档案 | `bindtap → selectParticipantDossier` | {"id":"{{item.user_id}}"} |
| 164 | 加载下一页 | `bindtap → loadMoreParticipants` | {} |
| 173 | 关闭参与者档案 | `bindtap → closeParticipantDossier` | {} |
| 176 | button | `bindtap → loadParticipantModule` | {"key":"{{item.key}}"} |
| 208 | 加载下一页 | `bindtap → loadParticipantModule` | {"key":"{{participantModule.module}}","page":"{{participantModule.page + 1}}"} |
| 231 | 进入试点项目 | `bindtap → switchWorkspace` | {"id":"pilots"} |
| 242 | 刷新 | `bindtap → loadAssessmentCases` | {} |
| 246 | button | `bindtap → selectAssessmentCase` | {"id":"{{item.id}}"} |
| 251 | 重新加载 | `bindtap → loadAssessmentCases` | {} |
| 284 | 类型： | `bindchange → onAssessmentFilter` | {"key":"kind"} |
| 287 | 权限： | `bindchange → onAssessmentFilter` | {"key":"visibility"} |
| 317 | textarea | `bindinput → onAssessmentDraftInput` | {"key":"assessmentInternalNotes"} |
| 322 | textarea | `bindinput → onAssessmentDraftInput` | {"key":"assessmentParticipantDraft"} |
| 324 | 保存工作台草稿 | `bindtap → saveAssessmentDraft` | {} |
| 326 | 进入质量抽检与修复 | `bindtap → openAssessmentQuality` | {} |
| 338 | 刷新 | `bindtap → loadAnalysisJobs` | {} |
| 398 | 检索方式： | `bindinput → onKnowledgeQueryInput` | {} |
| 399 | 检索方式： | `bindchange → onKnowledgeMethodChange` | {} |
| 402 | 检索已审核内容 | `bindtap → searchKnowledge` | {} |
| 468 | 重新加载 | `bindtap → loadAnalysisJobs` | {} |
| 499 | 重新同步 | `bindtap → loadWorkbench` | {} |
| 513 | 重新加载 | `bindtap → loadDashboard` | {} |
| 514 | 复制诊断信息 | `bindtap → copyDiagnostic` | {"scope":"pilot"} |
| 524 | · | `bindtap → selectEnrollment` | {"id":"{{item.id}}"} |
| 546 | 查看 | `bindtap → openReport` | {} |
| 547 | 人工确认 | `bindtap → confirmReport` | {} |
| 548 | 发送用户 | `bindtap → sendReport` | {} |
| 551 | 生成报告 | `bindtap → createReport` | {} |
| 559 | textarea | `bindinput → onStageFeedbackInput` | {"key":"observation"} |
| 563 | textarea | `bindinput → onStageFeedbackInput` | {"key":"evidence"} |
| 567 | textarea | `bindinput → onStageFeedbackInput` | {"key":"nextStep"} |
| 571 | textarea | `bindinput → onStageFeedbackInput` | {"key":"openQuestion"} |
| 587 | 生成并核对预览 | `bindtap → previewStageFeedback` | {} |
| 588 | 确认这个版本 | `bindtap → runDeliveryStep` | {"kind":"stage","action":"confirm"} |
| 589 | 发送到参与者消息 | `bindtap → runDeliveryStep` | {"kind":"stage","action":"send"} |
| 596 | input | `bindinput → onMessageTitleInput` | {} |
| 597 | textarea | `bindinput → onMessageBodyInput` | {} |
| 611 | 生成并核对预览 | `bindtap → previewParticipantMessage` | {} |
| 612 | 确认这个版本 | `bindtap → runDeliveryStep` | {"kind":"message","action":"confirm"} |
| 613 | 发送到参与者消息 | `bindtap → runDeliveryStep` | {"kind":"message","action":"send"} |
| 631 | textarea | `bindinput → onNoteInput` | {} |
| 632 | 保存备注 | `bindtap → saveNote` | {} |
| 637 | 生成探索手记草稿 | `bindtap → draftNarrative` | {} |
| 641 | 确认后交付用户 | `bindtap → confirmNarrative` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/researcher-dashboard/index.js:335` | `getShowcaseAccess` | GET /api/showcase-access | backend/routes/showcase_access.py:13 / showcase_access.get_showcase_access / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/researcher-dashboard/index.js:336` | `getResearchCapabilities` | GET /api/research/access/capabilities | backend/routes/research_access.py:39 / research_access.capabilities_route / authenticated_actor_capability_summary |
| `apps/miniprogram/pages/researcher-dashboard/index.js:400` | `listTherapeuticAssessmentCases` | GET /api/therapeutic-assessment/cases | backend/routes/therapeutic_assessment.py:446 / therapeutic_assessment.get_cases_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:419` | `getTherapeuticAssessmentResearcherWorkbench` | GET /api/therapeutic-assessment/cases/<case_id>/researcher-workbench | backend/routes/therapeutic_assessment.py:494 / therapeutic_assessment.get_researcher_workbench_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:430` | `getTherapeuticAssessmentAuthorizationStatus` | GET /api/therapeutic-assessment/competency/effective | backend/routes/therapeutic_assessment.py:770 / therapeutic_assessment.get_competency_effective_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/researcher-dashboard/index.js:499` | `saveTherapeuticAssessmentResearcherDraft` | PUT /api/therapeutic-assessment/cases/<case_id>/researcher-workbench/draft | backend/routes/therapeutic_assessment.py:596 / therapeutic_assessment.put_researcher_workbench_draft_route / participant_owner_or_assigned_researcher_or_claimed_queue_or_supervision_chain_or_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:527` | `getResearchAnalysisJobs` | GET /api/research/analysis/jobs | backend/routes/research_analysis.py:61 / research_analysis.get_jobs / analysis_job_or_artifact_bound_to_authorized_snapshot_or_admin_operation |
| `apps/miniprogram/pages/researcher-dashboard/index.js:528` | `getResearchAnalysisCatalog` | GET /api/research/analysis/catalog | backend/routes/research_analysis.py:146 / research_analysis.get_catalog_route / analysis_job_or_artifact_bound_to_authorized_snapshot_or_admin_operation |
| `apps/miniprogram/pages/researcher-dashboard/index.js:529` | `listOfflineModelVersions` | GET /api/research/benchmarks/model-versions | backend/routes/offline_benchmarks.py:136 / offline_benchmarks.model_versions / internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher |
| `apps/miniprogram/pages/researcher-dashboard/index.js:530` | `listOfflineModelShadowRuns` | GET /api/research/benchmarks/shadow-runs | backend/routes/offline_benchmarks.py:170 / offline_benchmarks.shadow_runs / internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher |
| `apps/miniprogram/pages/researcher-dashboard/index.js:531` | `listOfflineModelReviewQueue` | GET /api/research/benchmarks/shadow-review-queue | backend/routes/offline_benchmarks.py:178 / offline_benchmarks.shadow_review_queue / internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher |
| `apps/miniprogram/pages/researcher-dashboard/index.js:532` | `getOfflineModelMonitoring` | GET /api/research/benchmarks/monitoring | backend/routes/offline_benchmarks.py:186 / offline_benchmarks.monitoring_status / internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher |
| `apps/miniprogram/pages/researcher-dashboard/index.js:533` | `getOfflineModelReleaseGate` | GET /api/research/benchmarks/release-gate | backend/routes/offline_benchmarks.py:218 / offline_benchmarks.release_gate_get / internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher |
| `apps/miniprogram/pages/researcher-dashboard/index.js:534` | `getAiKnowledgeInventory` | GET /api/ai-qa/knowledge | backend/routes/ai_qa.py:126 / ai_qa.ai_qa_knowledge / internal_synthetic_evidence_role_scoped |
| `apps/miniprogram/pages/researcher-dashboard/index.js:535` | `getGroupNetworkAnalysisPolicy` | GET /api/research/benchmarks/network-policy | backend/routes/offline_benchmarks.py:108 / offline_benchmarks.network_policy / internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher |
| `apps/miniprogram/pages/researcher-dashboard/index.js:536` | `listOfflineBenchmarkRuns` | GET /api/research/benchmarks/runs | backend/routes/offline_benchmarks.py:301 / offline_benchmarks.runs / internal_offline_synthetic_or_metadata_only_runs_creator_scoped_for_researcher |
| `apps/miniprogram/pages/researcher-dashboard/index.js:615` | `retrieveAiKnowledge` | GET /api/ai-qa/knowledge/retrieve | backend/routes/ai_qa.py:142 / ai_qa.ai_qa_knowledge_retrieve / internal_synthetic_evidence_role_scoped |
| `apps/miniprogram/pages/researcher-dashboard/index.js:633` | `getResearchOperations` | GET /api/research/operations | backend/routes/research_workspace.py:377 / research_workspace.get_research_operations / active_unexpired_assignment_for_researcher_supervisor_full_for_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:634` | `getResearchQueue` | GET /api/research/queues | backend/routes/research_workspace.py:496 / research_workspace.get_research_queue / active_unexpired_assignment_for_researcher_supervisor_full_for_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:638` | `getTherapeuticAssessmentQueueRuntime` | GET /api/therapeutic-assessment/work-queue/runtime | backend/routes/therapeutic_assessment.py:386 / therapeutic_assessment.get_work_queue_runtime_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/researcher-dashboard/index.js:639` | `listTherapeuticAssessmentDutyShifts` | GET /api/therapeutic-assessment/duty-shifts | backend/routes/therapeutic_assessment.py:398 / therapeutic_assessment.get_duty_shifts_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/researcher-dashboard/index.js:640` | `listPublicationCandidates` | GET /api/therapeutic-assessment/publication-candidates | backend/routes/therapeutic_assessment.py:410 / therapeutic_assessment.get_publication_candidates_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/researcher-dashboard/index.js:641` | `getTherapeuticAssessmentLifecycleMetrics` | GET /api/therapeutic-assessment/lifecycle/metrics | backend/routes/therapeutic_assessment.py:506 / therapeutic_assessment.get_lifecycle_metrics_route / module_resource_role_or_owner_scope_without_therapeutic_case_claim |
| `apps/miniprogram/pages/researcher-dashboard/index.js:715` | `getResearchParticipants` | GET /api/research/participants | backend/routes/research_workspace.py:205 / research_workspace.list_participants / active_unexpired_assignment_for_researcher_supervisor_full_for_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:741` | `getResearchParticipant` | GET /api/research/participants/<user_id> | backend/routes/research_workspace.py:293 / research_workspace.get_participant_dossier / active_unexpired_assignment_for_researcher_supervisor_full_for_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:758` | `getResearchParticipantModule` | GET /api/research/participants/<user_id>/modules/<module_key> | backend/routes/research_workspace.py:319 / research_workspace.get_participant_module / active_unexpired_assignment_for_researcher_supervisor_full_for_admin |
| `apps/miniprogram/pages/researcher-dashboard/index.js:774` | `getRelationshipResearchDashboard` | GET /api/relationship-pilot/researcher/dashboard | backend/routes/relationship_pilot_routes.py:198 / relationship_pilot.researcher_dashboard_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/researcher-dashboard/index.js:819` | `claimResearchEnrollment` | POST /api/research/access/enrollments/<enrollment_id>/claim | backend/routes/research_access.py:82 / research_access.claim_enrollment_route / researcher_explicit_enrollment_claim_without_implicit_write_claim |
| `apps/miniprogram/pages/researcher-dashboard/index.js:832` | `getRelationshipEnrollment` | GET /api/relationship-pilot/enrollments/<enrollment_id> | backend/routes/relationship_pilot_routes.py:88 / relationship_pilot.get_enrollment_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/researcher-dashboard/index.js:911` | `createRelationshipResearchNote` | POST /api/relationship-pilot/enrollments/<enrollment_id>/notes | backend/routes/relationship_pilot_routes.py:206 / relationship_pilot.create_note_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/researcher-dashboard/index.js:919` | `createRelationshipReport` | POST /api/relationship-pilot/enrollments/<enrollment_id>/report | backend/routes/relationship_pilot_routes.py:96 / relationship_pilot.create_report_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/researcher-dashboard/index.js:929` | `confirmRelationshipReport` | POST /api/relationship-pilot/reports/<report_id>/confirm | backend/routes/relationship_pilot_routes.py:132 / relationship_pilot.confirm_report_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/researcher-dashboard/index.js:936` | `sendRelationshipReport` | POST /api/relationship-pilot/reports/<report_id>/send | backend/routes/relationship_pilot_routes.py:148 / relationship_pilot.send_report_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/researcher-dashboard/index.js:963` | `createResearchDelivery` | POST /api/research/deliveries | backend/routes/research_workspace.py:63 / research_workspace.create_research_delivery / relationship_delivery_bound_to_active_unexpired_enrollment_assignment |
| `apps/miniprogram/pages/researcher-dashboard/index.js:970` | `saveResearchDelivery` | PATCH /api/research/deliveries/<workflow_id> | backend/routes/research_workspace.py:87 / research_workspace.update_research_delivery / relationship_delivery_bound_to_active_unexpired_enrollment_assignment |
| `apps/miniprogram/pages/researcher-dashboard/index.js:976` | `runResearchDeliveryAction` | POST /api/research/deliveries/<workflow_id>/confirm；POST /api/research/deliveries/<workflow_id>/preview；POST /api/research/deliveries/<workflow_id>/send；POST /api/research/deliveries/<workflow_id>/withdraw | backend/routes/research_workspace.py:119 / research_workspace.confirm_research_delivery / relationship_delivery_bound_to_active_unexpired_enrollment_assignment；backend/routes/research_workspace.py:114 / research_workspace.preview_research_delivery / relationship_delivery_bound_to_active_unexpired_enrollment_assignment；backend/routes/research_workspace.py:124 / research_workspace.send_research_delivery / relationship_delivery_bound_to_active_unexpired_enrollment_assignment；backend/routes/research_workspace.py:129 / research_workspace.withdraw_research_delivery / relationship_delivery_bound_to_active_unexpired_enrollment_assignment |
| `apps/miniprogram/pages/researcher-dashboard/index.js:1039` | `createRelationshipNarrative` | POST /api/relationship-pilot/enrollments/<enrollment_id>/narrative | backend/routes/relationship_pilot_routes.py:215 / relationship_pilot.create_narrative_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |
| `apps/miniprogram/pages/researcher-dashboard/index.js:1044` | `confirmRelationshipNarrative` | POST /api/relationship-pilot/narratives/<narrative_id>/confirm | backend/routes/relationship_pilot_routes.py:223 / relationship_pilot.confirm_narrative_route / self_or_explicit_active_unexpired_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/therapeutic-assessment-quality/index；navigateTo → /pages/relationship-report/index?id=:dynamic；navigateTo → /pages/relationship-report/index?id=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync this；setStorageSync this；removeStorageSync this；getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/researcher-dashboard/index.js:332 `if (!requireLogin({ redirectUrl: "/pages/researcher-dashboard/index" })) return;`；apps/miniprogram/pages/researcher-dashboard/index.js:333 `const user = getAuthUser();`；apps/miniprogram/pages/researcher-dashboard/index.js:345 `if (!showcase.enabled && (!user \|\| !["researcher", "admin", "supervisor"].includes(user.role))) {`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 34 课程 — `pages/course/index`

**用户任务：** 按主题浏览真实课程与进度，进入课程内容；不是课程商城。
- 页面源码：`apps/miniprogram/pages/course/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{errorMessage}}`；`{{loading}}`；`{{!loading && !errorMessage}}`；`{{boundaryNotice}}`
- 组件：`page-state`、`section-title`、`course-card`、`bottom-tip-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 20 | button | `bindtap → selectCategory` | {"category":"{{item}}"} |
| 36 | 重新加载 | `bindtap → retryLoadCourses` | {} |
| 49 | course-card | `bindtapcard → openCourse` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/course/index.js:37` | `listCourses` | GET /api/courses | backend/routes/courses.py:78 / courses.list_courses / not_applicable_or_development_legacy |

- 下游路由：navigateTo → /pages/course-detail/index?id=:dynamic
- 本地保存：
- 组件事件转发：page-state → action；section-title → more；course-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 35 课程内容 — `pages/course-detail/index`

**用户任务：** 阅读课程章节、误区/示例，进入练习并记录完成；保留现有服务端进度。
- 页面源码：`apps/miniprogram/pages/course-detail/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{course}}`；`{{check.feedback}}`；`{{course.boosterText}}`；`{{course.relationText}}`；`{{progressMessage}}`
- 组件：`page-state`、`section-title`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 8 | 重新加载 | `bindtap → retryLoadCourse` | {} |
| 63 | button | `bindtap → chooseKnowledgeAnswer` | {"check-id":"{{check.id}}","value":"{{option.value}}"} |
| 82 | 去训练页 | `bindtap → goTraining` | {} |
| 90 | 记录课程完成 | `bindtap → markCourseComplete` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/course-detail/index.js:39` | `getCourse` | GET /api/courses/<course_id> | backend/routes/courses.py:218 / courses.get_course / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/course-detail/index.js:77` | `getCourseProgress` | GET /api/courses/<course_id>/progress | backend/routes/courses.py:135 / courses.get_course_progress / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/course-detail/index.js:98` | `saveCourseProgress` | POST /api/courses/<course_id>/progress | backend/routes/courses.py:157 / courses.save_course_progress / self_only_or_dedicated_domain_command |

- 下游路由：switchTab → /pages/training/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/course-detail/index.js:44 `if (isLoggedIn()) this.loadProgress();`；apps/miniprogram/pages/course-detail/index.js:88 `if (!requireLogin({ redirectUrl: `/pages/course-detail/index?id=${encodeURIComponent(this.data.courseId)}`, message: "请先登录后再保存课程进度。" })) return;`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；section-title → more
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 36 我的 — `pages/profile/index`

**用户任务：** 查看账号与连接状态，访问记录、专业支持、安全支持、隐私设置及条件式研究入口。
- 页面源码：`apps/miniprogram/pages/profile/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{user.roleText}}`；`{{loggedIn}}`；`{{identityStatus}}`；`{{identityStatus.identities.wechat.can_unbind}}`；`{{identityStatus.identities.phone.can_unbind}}`；`{{dataClaim}}`
- 组件：`page-state`、`section-title`、`function-entry-card`、`bottom-tip-card`、`alert-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 18 | 退出登录 | `bindtap → doLogout` | {} |
| 21 | 去登录 | `bindtap → goLogin` | {} |
| 22 | 注册账号 | `bindtap → goRegister` | {} |
| 34 | 撤销 | `bindtap → requestIdentityUnbind` | {"identity":"wechat"} |
| 41 | 撤销 | `bindtap → requestIdentityUnbind` | {"identity":"phone"} |
| 56 | 确认合并 | `bindtap → confirmDataClaim` | {} |
| 57 | 暂不处理 | `bindtap → dismissDataClaim` | {} |
| 66 | button | `bindtap → goResearcher` | {} |
| 72 | button | `bindtap → openEntry` | {"group":"recordEntries","index":"{{index}}"} |
| 85 | button | `bindtap → openEntry` | {"group":"supportEntries","index":"{{index}}"} |
| 102 | button | `bindtap → openEntry` | {"group":"safetyEntries","index":"{{index}}"} |
| 115 | button | `bindtap → openEntry` | {"group":"settingsEntries","index":"{{index}}"} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/profile/index.js:147` | `getShowcaseAccess` | GET /api/showcase-access | backend/routes/showcase_access.py:13 / showcase_access.get_showcase_access / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/profile/index.js:148` | `getDataClaimPreview` | GET /api/auth/data-claim-preview | backend/routes/auth.py:1313 / auth.data_claim_preview / role_scoped |
| `apps/miniprogram/pages/profile/index.js:149` | `getIdentityStatus` | GET /api/auth/identity-status | backend/routes/auth.py:1140 / auth.get_identity_status / role_scoped |
| `apps/miniprogram/pages/profile/index.js:150` | `getAiQaConfig` | GET /api/ai-qa/config | backend/routes/ai_qa.py:108 / ai_qa.ai_qa_config / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/profile/index.js:161` | `getProfileStats` | GET /api/profile/stats | backend/routes/profile.py:163 / profile.get_profile_stats / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/profile/index.js:260` | `claimAnonymousData` | POST /api/auth/data-claim | backend/routes/auth.py:1334 / auth.data_claim / role_scoped |
| `apps/miniprogram/pages/profile/index.js:286` | `unbindIdentity` | POST /api/auth/identity-unbind | backend/routes/auth.py:1154 / auth.identity_unbind / role_scoped |
| `apps/miniprogram/pages/profile/index.js:303` | `logout` | POST /api/auth/logout | backend/routes/auth.py:1081 / auth.logout / optional_bearer_revoke_all_account_tokens_idempotent |

- 下游路由：switchTab → /pages/login/index?redirect=%2Fpages%2Fprofile%2Findex；navigateTo → /pages/register/index?redirect=%2Fpages%2Fprofile%2Findex；navigateTo → /pages/researcher-dashboard/index；navigateTo → /pages/login/index?redirect=%2Fpages%2Fresearcher-dashboard%2Findex；redirectTo → /pages/login/index?redirect=%2Fpages%2Fprofile%2Findex；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync safehome_dismissed_data_claim_id；setStorageSync safehome_dismissed_data_claim_id；removeStorageSync safehome_dismissed_data_claim_id；getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/profile/index.js:129 `isResearcher: false,`；apps/miniprogram/pages/profile/index.js:143 `const storedUser = getAuthUser();`；apps/miniprogram/pages/profile/index.js:144 `const loggedIn = isLoggedIn();`；apps/miniprogram/pages/profile/index.js:145 `const canClaim = loggedIn && storedUser && ["parent", "student", "user"].includes(storedUser.role);`；apps/miniprogram/pages/profile/index.js:172 `isResearcher: !!showcase.enabled \|\| !!(storedUser && ["researcher", "admin", "supervisor"].includes(storedUser.role)),`；apps/miniprogram/pages/profile/index.js:211 `if (entry.private && !requireLogin({`；apps/miniprogram/pages/profile/index.js:240 `const storedUser = getAuthUser();`；apps/miniprogram/pages/profile/index.js:241 `if (storedUser && (this.data.showcaseAccess \|\| ["researcher", "admin", "supervisor"].includes(storedUser.role))) {`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`
- 组件事件转发：page-state → action；section-title → more；function-entry-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 37 设置与说明 — `pages/settings-detail/index`

**用户任务：** 阅读对应说明并管理真实保护、隐私或设置；动态类别、操作后果与授权边界完整。
- 页面源码：`apps/miniprogram/pages/settings-detail/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{noticeType === 'protection'}}`；`{{protectionLoading}}`；`{{protectionNeedsLogin}}`；`{{protectionError}}`；`{{protectionRole === 'student' && protectionStatus}}`；`{{protectionStatus.age_verification_required}}`；`{{protectionStatus.status === 'guardian_link_required'}}`；`{{protectionStatus.status === 'guardian_consent_required'}}`；`{{protectionStatus.status === 'child_assent_required'}}`；`{{protectionStatus.status === 'blocked_withdrawn_or_refused'}}`；`{{protectionStatus.status === 'active'}}`；`{{protectionStatus.status === 'age_verified'}}`；`{{protectionRole === 'parent'}}`；`{{generatedBindCode}}`；`{{guardianChildren.length}}`；`{{item.safeguard.age_band === 'under_14'}}`；`{{item.safeguard.age_band === '14_or_over'}}`；`{{item.safeguard.age_band === 'under_14'}}`；`{{item.safeguard.guardian_consent_status !== 'active'}}`；`{{protectionRole && protectionRole !== 'student' && protectionRole !== 'parent'}}`；`{{noticeType === 'privacy'}}`；`{{privacyLoading \|\| privacyError}}`；`{{privacyRequests.length}}`；`{{item.participant_notice}}`；`{{item.execution_proof_hash}}`；`{{item.canCancel}}`；`{{item.canAppeal}}`
- 组件：`page-state`、`section-title`、`bottom-tip-card`、`status-pill`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 26 | page-state | `bindaction → goProtectionLogin` | {} |
| 38 | 重新读取 | `bindtap → loadProtectionStatus` | {} |
| 49 | 我已满14周岁 | `bindtap → chooseAge` | {"age":"14_or_over"} |
| 50 | 我未满14周岁 | `bindtap → chooseAge` | {"age":"under_14"} |
| 55 | 完成家长绑定 | `bindinput → onBindCodeInput` | {} |
| 63 | 完成家长绑定 | `bindtap → submitStudentBinding` | {} |
| 72 | 我愿意继续 | `bindtap → updateChildDecision` | {"assented":"true"} |
| 73 | 我暂时不继续 | `bindtap → updateChildDecision` | {"assented":"false"} |
| 82 | 我想暂停受保护功能 | `bindtap → updateChildDecision` | {"assented":"false"} |
| 93 | 生成10位绑定码 | `bindtap → createGuardianBindCode` | {} |
| 112 | 同意受保护数据处理 | `bindtap → updateGuardianDecision` | {"child":"{{item.student_user_id}}","agreed":"true"} |
| 120 | 撤回监护人同意 | `bindtap → updateGuardianDecision` | {"child":"{{item.student_user_id}}","agreed":"false"} |
| 144 | 删除申请< | `bindaction → handlePrivacyStateAction` | {} |
| 163 | 取消申请 | `bindtap → cancelPrivacyRequest` | {"id":"{{item.id}}"} |
| 170 | 补充说明并重新提交 | `bindtap → appealPrivacyRequest` | {"id":"{{item.id}}"} |
| 187 | button | `bindtap → submitPrivacyDeleteRequest` | {} |
| 193 | 返回 | `bindtap → goBack` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/settings-detail/index.js:343` | `listPrivacyRequests` | GET /api/privacy/requests | backend/routes/privacy.py:86 / privacy.list_privacy_requests / self |
| `apps/miniprogram/pages/settings-detail/index.js:375` | `createPrivacyDeleteRequest` | POST /api/privacy/delete-my-data | backend/routes/privacy.py:71 / privacy.delete_my_data / self |
| `apps/miniprogram/pages/settings-detail/index.js:399` | `cancelPrivacyRequest` | POST /api/privacy/requests/<request_id>/cancel | backend/routes/privacy.py:117 / privacy.cancel_privacy_request / self |
| `apps/miniprogram/pages/settings-detail/index.js:429` | `appealPrivacyRequest` | POST /api/privacy/requests/<request_id>/appeal | backend/routes/privacy.py:100 / privacy.appeal_privacy_request / self |

- 下游路由：navigateTo → /pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprivacy；navigateTo → /pages/login/index?redirect=%2Fpages%2Fsettings-detail%2Findex%3Ftype%3Dprotection；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/settings-detail/index.js:191 `if (!isLoggedIn()) {`；apps/miniprogram/pages/settings-detail/index.js:202 `const user = getAuthUser() \|\| {};`；apps/miniprogram/pages/settings-detail/index.js:206 `if (role === "student") {`；apps/miniprogram/pages/settings-detail/index.js:215 `if (role === "parent") {`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`
- 组件事件转发：page-state → action；section-title → more
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 38 本周小目标 — `pages/goal-setting/index`

**用户任务：** 按原有步骤设置本周小目标，保留选项、输入、草稿与保存校验。
- 页面源码：`apps/miniprogram/pages/goal-setting/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{errorMessage}}`；`{{slowSubmitting}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 13 | button | `bindtap → selectScene` | {"value":"{{item}}"} |
| 23 | input | `bindinput → onTextInput` | {"key":"customScene"} |
| 32 | button | `bindtap → selectOldReaction` | {"value":"{{item}}"} |
| 50 | button | `bindtap → selectNewReaction` | {"value":"{{item}}"} |
| 67 | textarea | `bindinput → onTextInput` | {"key":"smartGoal"} |
| 83 | button | `bindtap → submitGoal` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/goal-setting/index.js:85` | `createGoal` | POST /api/goals | backend/routes/goals.py:20 / goals.create_goal / role_scoped |

- 下游路由：navigateTo → /pages/diary-form/index?goal_id=:dynamic
- 本地保存：getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 39 记录情绪事件 — `pages/diary-form/index`

**用户任务：** 记录具体事件和主要感受；选填信息保持可展开，保留目标关联、草稿和提交后反馈。
- 页面源码：`apps/miniprogram/pages/diary-form/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{goalId}}`；`{{showMoreFields}}`；`{{showMoreFields}}`；`{{errorMessage}}`；`{{slowSubmitting}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 18 | button | `bindtap → selectScene` | {"value":"{{item}}"} |
| 30 | input | `bindinput → onTextInput` | {"key":"customScene"} |
| 34 | textarea | `bindinput → onTextInput` | {"key":"eventDescription"} |
| 53 | button | `bindtap → selectParentEmotion` | {"value":"{{item}}"} |
| 65 | slider | `bindchange → onParentIntensityChange` | {} |
| 72 | button | `bindtap → selectChildEmotion` | {"value":"{{item}}"} |
| 84 | slider | `bindchange → onChildIntensityChange` | {} |
| 89 | button | `bindtap → toggleMoreFields` | {} |
| 101 | textarea | `bindinput → onTextInput` | {"key":"automaticThought"} |
| 111 | textarea | `bindinput → onTextInput` | {"key":"behavior"} |
| 130 | button | `bindtap → selectBodySensation` | {"value":"{{item}}"} |
| 140 | input | `bindinput → onTextInput` | {"key":"bodySensationNote"} |
| 144 | textarea | `bindinput → onTextInput` | {"key":"childReaction"} |
| 154 | textarea | `bindinput → onTextInput` | {"key":"shortTermResult"} |
| 164 | textarea | `bindinput → onTextInput` | {"key":"longTermImpact"} |
| 184 | button | `bindtap → submitDiary` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/diary-form/index.js:133` | `createDiary` | POST /api/diaries | backend/routes/diaries.py:29 / diaries.create_diary / self_only_or_dedicated_domain_command |

- 下游路由：navigateTo → /pages/feedback-result/index?diary_id=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/pages/diary-form/index.js:46 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 40 情绪记录 — `pages/diary-history/index`

**用户任务：** 读取本人最近50条日记并完整阅读时间/场景/描述/感受；可新建和重试，无编辑删除或虚构总数。
- 页面源码：`apps/miniprogram/pages/diary-history/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{records.length}}`
- 组件：`page-state`、`bamboo-timeline-node`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 13 | 重新加载情绪记录 | `bindaction → retry` | {} |
| 50 | 记录一件事 | `bindtap → startDiary` | {} |
| 53 | 新建一条情绪事件记录 | `bindaction → startDiary` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/diary-history/index.js:79` | `listDiaries` | GET /api/diaries | backend/routes/diaries.py:148 / diaries.list_diaries / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/diary-form/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/diary-history/index.js:59 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 41 本次反馈 — `pages/feedback-result/index`

**用户任务：** 理解这次支持性反馈并选择下一练习/共同核对/人工支持；高风险不生成普通建议。
- 页面源码：`apps/miniprogram/pages/feedback-result/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{isHighRisk}}`；`{{canShowTraining}}`；`{{trainingRecommendation}}`；`{{recommendedTrainings.length > 1}}`；`{{trainingIndex > 0 && trainingIndex < 3}}`；`{{trainingRecommendation}}`；`{{!isHighRisk}}`
- 组件：`page-state`、`section-title`、`training-task-card`、`bottom-tip-card`、`feedback-rating`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 10 | 先接住这次感受 | `bindaction → handleFeedbackStateAction` | {} |
| 19 | feedback-rating | `bindselect → submitFeedbackEvaluation` | {} |
| 59 | 查看安全指引 | `bindtap → openEmergencyGuide` | {} |
| 60 | 提交人工关注 | `bindtap → openSupervision` | {} |
| 71 | 开始这个练习 | `bindtap → openTrainingCard` | {} |
| 102 | 提交督导 | `bindtap → openSupervision` | {} |
| 106 | 收藏这次反馈 | `bindtap → saveFeedback` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/feedback-result/index.js:45` | `generateFeedback` | POST /api/feedback/generate | backend/routes/feedback.py:103 / feedback.generate / self_or_research_feedback_write_capability_and_active_assignment |
| `apps/miniprogram/pages/feedback-result/index.js:46` | `listCards` | GET /api/cards | backend/routes/cards.py:13 / cards.get_cards / role_scoped |
| `apps/miniprogram/pages/feedback-result/index.js:209` | `createFeedbackLedgerEntry` | POST /api/feedback-ledger | backend/routes/feedback_ledger.py:24 / feedback_ledger.create_entry / role_scoped |

- 下游路由：navigateTo → /pages/diary-form/index；navigateTo → /pages/training-card/index?tags=:dynamic；navigateTo → /pages/supervision/index?diary_id=:dynamic；navigateTo → /pages/emergency-guide/index
- 本地保存：setStorageSync LATEST_TRAINING_RECOMMENDATION_KEY
- 组件事件转发：page-state → action；section-title → more；training-task-card → tapcard；feedback-rating → select
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 42 家庭关系测一测 — `pages/assessment/index`

**用户任务：** 按实际分类和搜索找到支持性测评；是否开放、研究预览与来源以真实返回为准。
- 页面源码：`apps/miniprogram/pages/assessment/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{searchKeyword}}`；`{{errorMessage}}`；`{{loading}}`；`{{!item.items.length && item.emptyText}}`；`{{recentResults.length}}`；`{{recentLoginTip}}`
- 组件：`page-state`、`section-title`、`assessment-worksheet-card`、`function-entry-card`、`alert-card`、`bottom-tip-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 9 | button | `bindtap → switchAudience` | {"key":"{{item.key}}"} |
| 18 | 清除 | `bindinput → onSearchInput` | {} |
| 19 | 清除 | `bindtap → clearSearch` | {} |
| 26 | 重新加载 | `bindtap → loadAssessments` | {} |
| 39 | assessment-worksheet-card | `bindopen → openAssessmentEntry` | {} |
| 52 | 查看测评记录：{{item.worksheet_title}} | `bindtap → openRecentResult` | {"id":"{{item.id}}","worksheet-id":"{{item.worksheet_id}}"} |
| 77 | 去登录 | `bindtap → goLogin` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/assessment/index.js:46` | `getDebugConfig` | 本地配置只读，无网络请求 | 不展示 Secret 或用户原文 |
| `apps/miniprogram/pages/assessment/index.js:195` | `listAssessments` | GET /api/assessments | backend/routes/assessments.py:216 / assessments.list_assessments / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/assessment/index.js:219` | `listAssessmentResults` | GET /api/assessment-results | backend/routes/assessments.py:327 / assessments.list_assessment_results / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/assessment-detail/index?id=:dynamic；navigateTo → /pages/assessment-result/index?id=:dynamic；navigateTo → /pages/integration-test/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/assessment/index.js:66 `const isStudentProfile = item.id === "student_profile_v1" \|\| item.category === "学生画像";`；apps/miniprogram/pages/assessment/index.js:68 `const audienceClass = item.audience_class \|\| (isStudentProfile ? "student" : "adult");`；apps/miniprogram/pages/assessment/index.js:76 `display_title: isStudentProfile ? item.display_title : cleanDisplayTitle(item.display_title \|\| item.source_title),`；apps/miniprogram/pages/assessment/index.js:78 `is_student_profile: isStudentProfile,`；apps/miniprogram/pages/assessment/index.js:85 `action_text: item.enabled_for_user === false ? "暂不开放" : isStudentProfile ? "开始测一测" : "填写",`；apps/miniprogram/pages/assessment/index.js:211 `if (!isLoggedIn()) {`；apps/miniprogram/pages/assessment/index.js:249 `if (!requireLogin({`；apps/miniprogram/pages/assessment/index.js:278 `requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`
- 组件事件转发：page-state → action；section-title → more；assessment-worksheet-card → open；function-entry-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 43 全部测评记录 — `pages/assessment-history/index`

**用户任务：** 回看已保存测评，保留实际分页、详情和错误恢复。
- 页面源码：`apps/miniprogram/pages/assessment-history/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage && !items.length}}`；`{{items.length}}`；`{{hasMore}}`；`{{errorMessage}}`
- 组件：`page-state`、`assessment-worksheet-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 16 | 重新加载 | `bindtap → retry` | {} |
| 20 | assessment-worksheet-card | `bindopen → openResult` | {} |
| 28 | button | `bindtap → loadMore` | {} |
| 36 | 去测一测 | `bindtap → goAssessment` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/assessment-history/index.js:70` | `listAssessmentResults` | GET /api/assessment-results | backend/routes/assessments.py:327 / assessments.list_assessment_results / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/assessment-result/index?id=:dynamic；navigateTo → /pages/assessment/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/assessment-history/index.js:52 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action；assessment-worksheet-card → open
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 44 填写测评 — `pages/assessment-detail/index`

**用户任务：** 完成真实题目和选项，保留题序、进度、草稿、校验及提交；不改测量含义。
- 页面源码：`apps/miniprogram/pages/assessment-detail/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{worksheet}}`；`{{worksheet.sensitive_category && worksheet.sensitive_category !== 'none'}}`；`{{item.required}}`；`{{item.type === 'scale'}}`；`{{errorMessage}}`；`{{needsLogin}}`；`{{slowSubmitting}}`
- 组件：`page-state`、`section-title`、`alert-card`、`bottom-tip-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 27 | 选择 {{opt.displayLabel}} | `bindtap → selectOption` | {"index":"{{qi}}","value":"{{opt.value}}","score":"{{opt.score}}"} |
| 44 | textarea | `bindinput → onTextInput` | {"index":"{{qi}}"} |
| 57 | 去登录后继续 | `bindtap → goLogin` | {} |
| 63 | button | `bindtap → submitWorksheet` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/assessment-detail/index.js:115` | `getAssessment` | GET /api/assessments/<worksheet_id> | backend/routes/assessments.py:275 / assessments.get_assessment / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/assessment-detail/index.js:231` | `createProfile` | POST /api/profile | backend/routes/profile.py:446 / profile.create_profile / role_scoped |
| `apps/miniprogram/pages/assessment-detail/index.js:232` | `createAssessmentResult` | POST /api/assessment-results | backend/routes/assessments.py:291 / assessments.create_assessment_result / self_only_or_dedicated_domain_command |

- 下游路由：navigateTo → /pages/assessment-result/index?id=:dynamic；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/pages/assessment-detail/index.js:39 `const isStudentProfile = worksheet.id === "student_profile_v1" \|\| worksheet.category === "学生画像";`；apps/miniprogram/pages/assessment-detail/index.js:43 `display_title: isStudentProfile ? worksheet.display_title : cleanDisplayTitle(worksheet.display_title \|\| worksheet.source_title),`；apps/miniprogram/pages/assessment-detail/index.js:44 `displaySourceText: isStudentProfile ? "支持性测评" : isReference ? "示例参考" : "电子版简化记录",`；apps/miniprogram/pages/assessment-detail/index.js:51 `isStudentProfile,`；apps/miniprogram/pages/assessment-detail/index.js:77 `if (!requireLogin({`；apps/miniprogram/pages/assessment-detail/index.js:230 `const result = worksheet.isStudentProfile`；apps/miniprogram/pages/assessment-detail/index.js:237 `const resultId = worksheet.isStudentProfile ? result.assessment_result_id : result.id;`；apps/miniprogram/pages/assessment-detail/index.js:264 `requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`
- 组件事件转发：page-state → action；section-title → more
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 45 测一测结果 — `pages/assessment-result/index`

**用户任务：** 阅读结果、维度、群体参照及本人结构化情绪/共现线索；低样本、风险暂缓、权限和非诊断边界分开。
- 页面源码：`apps/miniprogram/pages/assessment-result/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{result}}`；`{{riskSummary}}`；`{{profilePosition}}`；`{{!profilePosition.canUseInterpretation}}`；`{{profilePosition.nCasesText}}`；`{{profilePosition.featureText}}`；`{{profilePosition.visualizationState !== 'data'}}`；`{{profilePosition.userPoint}}`；`{{profilePosition.clusterPoints.length}}`；`{{profilePosition.radarFeatures.length >= 3}}`；`{{profilePosition.radarFeatures.length >= 3}}`；`{{profilePosition.radarFeatures.length < 3}}`；`{{profilePosition.explanation}}`；`{{profilePosition.strengthNote \|\| profilePosition.smallStep}}`；`{{profilePosition.strengthNote}}`；`{{profilePosition.smallStep}}`；`{{profilePosition.suggestedQuestions.length}}`；`{{profilePosition.projectTasks.length}}`；`{{profileSummary}}`；`{{profileSummary.supportiveExplanation}}`；`{{profileSummary.strengthNote \|\| profileSummary.smallStep}}`；`{{profileSummary.strengthNote}}`；`{{profileSummary.smallStep}}`；`{{!profileSummary && scaleDimensions.length}}`；`{{scaleVisualization.showRadar}}`；`{{item.hasComparableRange}}`；`{{exploratoryAnalysis}}`；`{{!exploratoryAnalysis.available}}`；`{{exploratoryAnalysis.available}}`；`{{exploratoryAnalysis.interactionEdges.length}}`；`{{trainingRecommendation}}`；`{{trainingRecommendation.todaySuggestion}}`；`{{item.purpose}}`；`{{!profileSummary \|\| profileSummary.canOpenRecommendedCards}}`
- 组件：`page-state`、`section-title`、`alert-card`、`bottom-tip-card`、`visualization-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 165 | 查看可练习任务 | `bindtap → openRecommendedCards` | {} |
| 166 | 返回测一测 | `bindtap → backToAssessment` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/assessment-result/index.js:472` | `getAssessmentResult` | GET /api/assessment-results/<result_id> | backend/routes/assessments.py:374 / assessments.get_assessment_result / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/assessment-result/index.js:473` | `getAssessment` | GET /api/assessments/<worksheet_id> | backend/routes/assessments.py:275 / assessments.get_assessment / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/assessment-result/index.js:474` | `listCards` | GET /api/cards | backend/routes/cards.py:13 / cards.get_cards / role_scoped |
| `apps/miniprogram/pages/assessment-result/index.js:475` | `getAssessmentExploratoryAnalysis` | GET /api/assessment-results/<result_id>/exploratory-analysis | backend/routes/assessments.py:434 / assessments.get_assessment_exploratory_analysis / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/assessment-result/index.js:480` | `getAssessmentProfilePosition` | GET /api/assessment-results/<result_id>/profile-position | backend/routes/assessments.py:391 / assessments.get_assessment_profile_position / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：navigateTo → /pages/training-card/index?card_ids=:dynamic；navigateTo → /pages/training-card/index?card_ids=:dynamic；switchTab → /pages/training/index
- 本地保存：setStorageSync LATEST_TRAINING_RECOMMENDATION_KEY；setStorageSync THREE_DAY_LIGHT_PLAN_KEY
- 组件事件转发：page-state → action；section-title → more
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 46 教育热榜 — `pages/hot-topics/index`

**用户任务：** 从本地真实案例阅读拆解并进入对应练习；不包装为实时热榜数据。
- 页面源码：`apps/miniprogram/pages/hot-topics/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：
- 组件：`page-state`、`section-title`、`bottom-tip-card`、`training-task-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 9 | button | `bindtap → selectTag` | {"tag":"{{item}}"} |
| 25 | button | `bindtap → selectTopic` | {"id":"{{item.id}}"} |
| 67 | 查看关联训练卡 | `bindtapcard → openPractice` | {} |
| 76 | 查看关联训练卡 | `bindtap → openPractice` | {} |
| 87 | 回到首页 | `bindtap → goHome` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| — | — | 本地内容/导航/状态 | 不新增后端能力 |

- 下游路由：navigateTo → /pages/training-card/index?tags=:dynamic；switchTab → /pages/home/index
- 本地保存：
- 组件事件转发：page-state → action；section-title → more；training-task-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 47 UP任务卡 — `pages/task-detail/index`

**用户任务：** 阅读当前本地任务步骤与示例、做一次记录并进入打卡；不冒充服务端新增任务。
- 页面源码：`apps/miniprogram/pages/task-detail/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{task}}`
- 组件：`page-state`、`section-title`、`alert-card`、`bottom-tip-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 3 | ‹ | `bindtap → goBack` | {} |
| 48 | 当前情绪强度： / 10 | `bindinput → onReflectionInput` | {} |
| 50 | slider | `bindchange → onEmotionLevelChange` | {} |
| 59 | 完成并打卡 | `bindtap → finishPractice` | {} |
| 61 | 从第一步开始 | `bindtap → startPractice` | {} |
| 62 | 暂存感受 | `bindtap → recordFeeling` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| — | — | 本地内容/导航/状态 | 不新增后端能力 |

- 下游路由：navigateTo → /pages/checkin/index?card_id=:dynamic
- 本地保存：getStorageSync safehome:selectedTrainingCard
- 组件事件转发：page-state → action；section-title → more
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 48 推荐训练卡 — `pages/training-card/index`

**用户任务：** 从真实主推荐和备选中选择练习卡，保留风险阻断与详情/打卡路径。
- 页面源码：`apps/miniprogram/pages/training-card/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{tagsText}}`；`{{item.isPrimary}}`；`{{item.isPrimary}}`；`{{item.isPrimary && expandedCardId === item.id}}`；`{{item.examplePhrase}}`；`{{item.stopText}}`；`{{item.isPrimary}}`；`{{cards.length === 0}}`
- 组件：`page-state`、`feedback-rating`、`training-task-card`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 10 | 这次推荐依据 | `bindaction → retryLoadCards` | {} |
| 33 | button | `bindtap → toggleCardDetails` | {"id":"{{item.id}}"} |
| 47 | button | `bindtap → choosePractice` | {"id":"{{item.id}}","title":"{{item.title}}"} |
| 48 | feedback-rating | `bindselect → submitTrainingFeedback` | {"id":"{{item.id}}"} |
| 59 | page-state | `bindaction → goDiary` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/training-card/index.js:61` | `listCards` | GET /api/cards | backend/routes/cards.py:13 / cards.get_cards / role_scoped |
| `apps/miniprogram/pages/training-card/index.js:61` | `recommendCards` | GET /api/cards/recommend | backend/routes/cards.py:24 / cards.recommend / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/training-card/index.js:153` | `createFeedbackLedgerEntry` | POST /api/feedback-ledger | backend/routes/feedback_ledger.py:24 / feedback_ledger.create_entry / role_scoped |

- 下游路由：navigateTo → /pages/task-detail/index?card_id=:dynamic；navigateTo → /pages/diary-form/index
- 本地保存：setStorageSync safehome:selectedTrainingCard
- 组件事件转发：page-state → action；feedback-rating → select；training-task-card → tapcard
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 49 记录尝试 — `pages/checkin/index`

**用户任务：** 记录一次尝试与感受，保留真实输入、草稿、校验、保存与下一步。
- 页面源码：`apps/miniprogram/pages/checkin/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{successMessage}}`；`{{errorMessage}}`；`{{slowSubmitting}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 20 | slider | `bindchange → onEmotionBeforeChange` | {} |
| 25 | slider | `bindchange → onEmotionAfterChange` | {} |
| 31 | button | `bindtap → chooseHelpfulness` | {"value":"{{item.value}}"} |
| 45 | input | `bindinput → onSkipReasonInput` | {} |
| 53 | textarea | `bindinput → onReflectionInput` | {} |
| 67 | button | `bindtap → submitCheckin` | {} |
| 71 | 回到首页 | `bindtap → goHome` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/checkin/index.js:111` | `createCheckin` | POST /api/checkins | backend/routes/checkins.py:22 / checkins.create_checkin / self_only_or_dedicated_domain_command |

- 下游路由：reLaunch → /pages/home/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync safehome:selectedTrainingCard；getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/pages/checkin/index.js:42 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 50 本周复盘 — `pages/weekly-report/index`

**用户任务：** 回顾本周真实记录与练习线索，区分量尺、次数、来源与下一步，不作成绩排名。
- 页面源码：`apps/miniprogram/pages/weekly-report/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{loading}}`；`{{errorMessage}}`；`{{profileTrendNamesText}}`；`{{report.profile_trend && report.profile_trend.requires_review_count}}`；`{{assessmentNamesText}}`；`{{dimensionGroups.length}}`；`{{recommendedCardsText}}`；`{{frequentScenes.length}}`；`{{frequentEmotions.length}}`；`{{commonPatterns.length}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 16 | 重新加载 | `bindtap → refreshReport` | {} |
| 161 | 刷新复盘 | `bindtap → refreshReport` | {} |
| 162 | 回到首页 | `bindtap → goHome` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/weekly-report/index.js:86` | `getWeeklyReport` | GET /api/weekly-report | backend/routes/reports.py:14 / reports.weekly_report / self_or_active_participant_assignment_or_admin_capability |

- 下游路由：reLaunch → /pages/home/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user
- 权限/预览线索：apps/miniprogram/pages/weekly-report/index.js:72 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 51 人工督导入口 — `pages/supervision/index`

**用户任务：** 提交非实时人工支持请求，可关联本人记录；紧急边界、提交与失败恢复清楚。
- 页面源码：`apps/miniprogram/pages/supervision/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{successMessage}}`；`{{errorMessage}}`；`{{slowSubmitting}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 18 | button | `bindtap → selectSource` | {"type":"{{item.type}}","id":"{{item.id}}"} |
| 37 | textarea | `bindinput → onTextInput` | {"key":"message"} |
| 48 | input | `bindinput → onTextInput` | {"key":"contact"} |
| 59 | textarea | `bindinput → onTextInput` | {"key":"riskHint"} |
| 79 | button | `bindtap → submitSupervision` | {} |
| 83 | 回到首页 | `bindtap → goHome` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/supervision/index.js:59` | `listDiaries` | GET /api/diaries | backend/routes/diaries.py:148 / diaries.list_diaries / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/supervision/index.js:60` | `listAssessmentResults` | GET /api/assessment-results | backend/routes/assessments.py:327 / assessments.list_assessment_results / self_or_active_participant_assignment_or_admin_capability |
| `apps/miniprogram/pages/supervision/index.js:125` | `createSupervision` | POST /api/supervision | backend/routes/supervision.py:97 / supervision.create_supervision_request / self_only_or_dedicated_domain_command |

- 下游路由：reLaunch → /pages/home/index；navigateTo → /pages/login/index:dynamic
- 本地保存：getStorageSync auth_token；getStorageSync auth_user；removeStorageSync auth_token；removeStorageSync auth_user；getStorageSync storageKey；setStorageSync storageKey；removeStorageSync storageKey
- 权限/预览线索：apps/miniprogram/pages/supervision/index.js:27 `if (!requireLogin({`；apps/miniprogram/utils/authGuard.js:5 `function getAuthUser() {`；apps/miniprogram/utils/authGuard.js:9 `function isLoggedIn() {`；apps/miniprogram/utils/authGuard.js:13 `function requireLogin(options = {}) {`；apps/miniprogram/utils/authGuard.js:14 `if (isLoggedIn()) {`；apps/miniprogram/utils/authGuard.js:46 `getAuthUser,`；apps/miniprogram/utils/authGuard.js:47 `isLoggedIn,`；apps/miniprogram/utils/authGuard.js:48 `requireLogin,`
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 52 云托管诊断 — `pages/debug/index`

**用户任务：** 保留开发配置、诊断、请求与原始技术输出，仅开发用途。
- 页面源码：`apps/miniprogram/pages/debug/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{lastError}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 16 | 切换本地 5000 | `bindtap → useLocalBackend` | {} |
| 17 | 切回云托管 | `bindtap → useCloudBackend` | {} |
| 18 | 测试 healthz | `bindtap → testHealthz` | {} |
| 19 | 测试 assessments | `bindtap → testAssessments` | {} |
| 20 | 测试 risk/check | `bindtap → testRiskCheck` | {} |
| 21 | 测试 profile | `bindtap → testProfile` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/debug/index.js:42` | `getDebugConfig` | 本地配置只读，无网络请求 | 不展示 Secret 或用户原文 |
| `apps/miniprogram/pages/debug/index.js:71` | `healthz` | GET /healthz | backend/app.py:416 / healthz / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/debug/index.js:106` | `listAssessments` | GET /api/assessments | backend/routes/assessments.py:216 / assessments.list_assessments / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/debug/index.js:111` | `checkRisk` | POST /api/risk/check | backend/routes/profile.py:506 / profile.check_risk / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/debug/index.js:120` | `createProfile` | POST /api/profile | backend/routes/profile.py:446 / profile.create_profile / role_scoped |

- 下游路由：
- 本地保存：
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

### 53 联调测试 — `pages/integration-test/index`

**用户任务：** 保留健康诊断及记录—反馈—推荐三步联调，不作为正式用户入口。
- 页面源码：`apps/miniprogram/pages/integration-test/index.{js,wxml,wxss,json}`（部分步骤无独立 WXSS，使用共享组件）。
- 实际条件：`{{diary}}`；`{{feedback}}`；`{{cards.length}}`
- 组件：`page-state`

| WXML行 | 元素/上下文 | 事件 → 处理器 | 参数 |
|---:|---|---|---|
| 11 | button | `bindtap → runSmokeTest` | {} |

| 调用来源 | 客户端方法 | 真实接口/本地能力 | 后端证据与访问范围 |
|---|---|---|---|
| `apps/miniprogram/pages/integration-test/index.js:7` | `getDebugConfig` | 本地配置只读，无网络请求 | 不展示 Secret 或用户原文 |
| `apps/miniprogram/pages/integration-test/index.js:33` | `healthz` | GET /healthz | backend/app.py:416 / healthz / not_applicable_or_development_legacy |
| `apps/miniprogram/pages/integration-test/index.js:39` | `createDiary` | POST /api/diaries | backend/routes/diaries.py:29 / diaries.create_diary / self_only_or_dedicated_domain_command |
| `apps/miniprogram/pages/integration-test/index.js:53` | `generateFeedback` | POST /api/feedback/generate | backend/routes/feedback.py:103 / feedback.generate / self_or_research_feedback_write_capability_and_active_assignment |
| `apps/miniprogram/pages/integration-test/index.js:60` | `recommendCards` | GET /api/cards/recommend | backend/routes/cards.py:24 / cards.recommend / not_applicable_or_development_legacy |

- 下游路由：
- 本地保存：
- 组件事件转发：page-state → action
- 实现保护：保留上述事件和参数、接口与字段、真实条件分支、输入校验、角色/同意/风险判断；内容仅作不改变含义的展示调整。

<!-- UI_PRODUCT_AUTO_FACTS:END -->


## 2026-09-08：登录与首次使用增量（独立分支，待合入）

2026-09-09后续补齐（覆盖下方“尚未完成”记录）：goal-setting/checkin/supervision/program-detail/relationship-task五页先读取并保存功能同意，再初始化表单/恢复本地草稿；serviceReady为假时无表单。项目preview=1保持只读且不保存/提交。独立项目/关系草稿按进入账号分键，首页只发现当前账号后缀草稿。说明升级2026.09.09-service-notice-v2，明确本地存储用途；不是研究或材料授权。复用当前service-consent/page-state，未重设计页面视觉；原生编译通过，真机仍待验收。

2026-09-09逻辑修复补充：功能同意在GET consent前重新查询微信隐私状态；拒绝首页基础说明时保留遮罩直至导航离开；账号/手机号登录处理函数拒绝并发重入。共用resilientForm草稿按账号保存且旧控制器拒绝跨账号保存/获取提交ID，旧无归属草稿不自动恢复。项目与关系任务独立草稿及home扫描尚未完成归属修复；不宣称全部草稿或首次本地保存同意覆盖已完成。本轮未改变视觉设计。

本节仅对应codex/cloudrun-login-onboarding，以b531b9d9为UI基线，不覆盖UIproduct2并行页面工作。

| 目标 | 新交互 | 真实调用/状态 | 保护边界 |
|---|---|---|---|
| home | 首次大弹窗；同意后六步箭头引导、上一步/下一步/跳过/重看 | wx.getPrivacySetting、agreePrivacyAuthorization；本机教程状态；查询完成前不加载首页账号数据 | 平台同意、本地阅读状态、研究同意互不替代 |
| login | 已配置可信云身份模式走callContainer直接登录 | GET auth/capabilities；POST auth/wechat-login；标准code路线仍保留 | 不伪造身份头，不开启真实云端信任开关 |
| phone login | 继续使用用户触发的getPhoneNumber code | POST auth/phone-login；后端新增显式OpenAPI路线 | 拒绝、失败不当作登录成功；不保存手机号原文 |
| diary-form / assessment-detail | 展示并保存知情选择后才初始化表单/恢复草稿 | GET/POST consent → 原有数据API | 保存同意失败、拒绝或账号/页面变化时不提交 |
| program-detail | 首次保存草稿/提交前功能确认 | consent → 原有本地草稿/项目API | 不改变项目开放、研究和年龄条件 |
| goals / checkins / thermometer / supervision / relationship enrollment | 原生弹窗明确用途，确认后才执行原API | service_data按purpose分开记录 | 不授予可选研究权限，不替代专门同意链路 |

当前六步引导介绍首页真实入口，不自动跳入并操作实际表单，不创建演示记录。新弹窗采用既有青绿/暖白主题、正文28rpx以上；位置取真实节点边界，缺节点时回退居中说明，不绘制假目标。
