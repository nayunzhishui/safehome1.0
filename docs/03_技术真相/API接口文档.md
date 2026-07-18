# API 接口文档

最后更新时间：2026-07-02

本文档记录 `safehome1.0 / 安心陪伴 / ReadFeedback` MVP 1.0 当前已经实现的 Flask + SQLite 后端 API。本文档以当前后端真实行为为准，用于小程序端与网页端并行联调。

进度口径：真实可调用接口以前文已实现章节为准；第 10 节”0版网页评估画像整合”已有基础画像、风险检查、模型信息、画像历史、人工复核、周报画像趋势、`type=profile` 脱敏导出、`type=records` 统一研究导出和高风险导出二次确认。当前总进度见 `docs/00_当前事实基准/项目进度统一口径.md`。

阅读方式：先看”通用约定”和对应接口章节；若与历史日志冲突，以本文开头进度口径和 `docs/00_当前事实基准/项目进度统一口径.md` 为准。

## 地址说明

本项目有两套访问地址，请根据当前场景选择：

| 场景 | 后端 API 地址 | 前端 Web 地址 |
|------|--------------|-------------|
| **本地开发** | `http://127.0.0.1:5050` | `http://127.0.0.1:5173` |
| **云端验收** | CloudBase 云托管域名（如 `https://flask-gh3l-xxx.sh.run.tcloudbase.com`） | 同上本地 Vite dev server（API 转发到云端） |

**本地开发**：后端运行在 `5050` 端口（可通过 `PORT` 环境变量修改），前端 Vite dev server 运行在 `5173`，默认请求本地后端。

**云端验收**：在 `apps/web/.env.local` 中设置 `VITE_SAFEHOME_API_BASE_URL=<云端API地址>`，本地 `5173` 页面会把 API 请求转发到云端。此时 `/readyz` 或 `/healthz/deep` 必须显示 `database.provider=mysql`，且 Web 后台使用云端 `ADMIN_EXPORT_TOKEN`。

注意：历史文档中部分示例仍写 `5000` 端口，实际本地后端默认端口为 `5050`（`app.py` 中 `PORT` 环境变量默认值）。

## 通用约定

- 后端地址：本地开发默认 `http://127.0.0.1:5050`
- API 基础路径：`/api`
- 请求格式：`application/json`
- JSON 响应格式：统一包裹在 `ok` 和 `data` 中。
- CSV 导出接口返回 `text/csv; charset=utf-8`。
- 时间字段：后端当前使用 ISO 8601 字符串。
- CORS 来源白名单由 `ALLOWED_ORIGINS` 环境变量配置；开发默认允许 `http://127.0.0.1:5173` 和 `http://localhost:5173`。
- 当前没有完整登录鉴权；开发环境未传 `user_id` 时，写入和查询接口可使用默认测试用户 `demo-parent`。
- 当 `APP_ENV=production` 时，目标、情绪记录、反馈、画像、打卡、督导、测评结果等写入接口必须传匿名 `user_id`，例如 `parent_xxx`、`student_xxx`、`tester_xxx`，否则返回 `validation_error`。
- 当 `APP_ENV=production` 时，目标、情绪记录、打卡、周报和测评结果等用户查询接口也必须传匿名 `user_id`，否则返回 `validation_error`。
- 后台敏感接口必须带 `X-Admin-Token`：`/api/admin/export`、`/api/risk-review`、`/api/profile-results` 列表、`/api/profile-results/<id>/reviews`、`/api/profile-results/<id>/review`、`/api/content-review/update`。
- 当前不接入复杂 AI 调用，即时反馈由 `content/feedback_rules.json` 规则匹配生成。

通用成功响应：

```json
{
  "ok": true,
  "data": {}
}
```

通用错误响应：

```json
{
  "ok": false,
  "error": {
    "code": "missing_fields",
    "message": "缺少必填字段：scene"
  }
}
```

补充约定（2026-07-09）：鉴权辅助层会按状态码返回稳定错误码：`400 -> validation_error`、`401 -> unauthorized`、`403 -> forbidden`。参数缺失或后台查询缺少必要 `user_id` 时，不应返回 `unauthorized`，避免前端误提示登录过期。

## 0. 健康检查

### `GET /healthz`

用途：确认后端是否启动。该接口只返回轻量状态，不检查数据库。

响应示例：

```json
{
  "ok": true,
  "service": "safehome-backend",
  "env": "development",
  "version": "safehome-2026-06-04"
}
```

### `GET /healthz/deep`

用途：云托管和部署诊断。该接口只做只读检查，不返回 token、用户数据或自由文本。

检查项：

- 数据库是否可连接；
- 核心表是否存在；
- content 必需文件是否存在；
- `training_cards` 是否与 `content/training_cards.json` 同步；
- `assessment_worksheets` 是否与 `content/assessment_worksheets.json` 同步。

### `GET /readyz`

用途：部署 readiness 检查。该接口和 `/healthz/deep` 使用同一组只读检查，但当数据库或 content 不可用时返回 `503`，便于云托管、负载均衡或部署脚本判断服务是否真正可接流量。

响应外形与 `/healthz/deep` 一致：

```json
{
  "ok": true,
  "service": "safehome-backend",
  "env": "development",
  "version": "safehome-2026-06-04",
  "database": {},
  "content": {}
}
```

全局未处理异常会返回稳定 JSON，不向用户暴露堆栈或内部错误：

```json
{
  "ok": false,
  "error": {
    "code": "internal_error",
    "message": "服务暂时没有响应，请稍后再试。"
  }
}
```

## 0T8. 任务八新增接口

### `POST /api/emotion-thermometer`

用途：保存一次当天情绪温度计记录，用于自我观察和日曲线展示，不构成诊断或筛查。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 生产必填 | 匿名用户 ID，开发环境可缺省为 `demo-parent` |
| `intensity_level` | integer | 是 | 1-10 的情绪强度 |
| `valence_level` | integer | 否 | 1-10 的愉悦度/不愉悦度观察，只作自我观察 |
| `arousal_level` | integer | 否 | 1-10 的身体唤起水平观察，只作自我观察 |
| `control_level` | integer | 否 | 1-10 的可控感观察，只作自我观察 |
| `emotion_label` | string | 否 | 40 字内情绪命名，例如“着急”“担心”；不作为诊断标签 |
| `brief_text` | string | 否 | 200 字内简短备注 |
| `created_at` | string | 否 | ISO 时间；缺省为后端当前时间 |

### `GET /api/emotion-thermometer/day?user_id=&date=YYYY-MM-DD`

用途：返回某用户某一天的温度计记录、`min/max/avg/count` 汇总、`valence_avg/arousal_avg/control_avg` 轻量维度均值和边界说明。日期过滤使用 `substr(created_at, 1, 10)=date`，不依赖数据库当前日期函数。

### `GET /api/progress-summary?range=7d`

用途：首页“最近记录”下方的阶段性反馈。汇总近期情绪记录、测评记录、情绪温度计和训练打卡，只输出支持性过程反馈，不输出诊断、筛查或人格判断。生产环境需要 Bearer token；开发环境可回退到匿名 `user_id`。

响应重点字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `stability_status` | string | `insufficient/fluctuating/converging/stable/low_confidence` |
| `summary_text` | string | 支持性阶段总结 |
| `diaries` | object | 近期情绪记录数量、高频场景和高频情绪 |
| `assessments` | object | 近期测评次数、最近测评名称和画像结果 |
| `thermometer` | object | 温度计次数、平均强度和趋势提示 |
| `checkins` | object | 训练打卡次数、最近训练卡 |
| `next_suggestions` | array | 下一步建议 |
| `boundary_notice` | string | 非诊断边界说明 |

### `GET /api/training-plan?user_id=`

用途：根据最近测评结果、测评训练规则和画像簇推荐卡，生成最小个性化训练计划。没有测评记录时只返回“先完成一次测一测”的下一步提示。

生产环境训练卡和课程均执行服务端治理门禁：普通用户只读取 `pilot_approved/production_approved/enabled/trial_enabled` 且启用的内容；研究者、督导或管理员可携带身份并传 `include_unapproved=true` 只读预览。训练推荐同样经过训练卡治理过滤，不能靠测评映射绕过卡片审核状态。

### `GET /api/programs`

用途：返回满足治理状态的项目测试练习包摘要。内容来自 `content/programs.json`。生产环境普通用户只看到 `pilot_approved`；没有批准项目时 `items=[]`，并通过 `availability.approved_count/pending_review_count/status/message` 说明真实状态。研究者、督导或管理员可携带身份令牌并传 `include_drafts=true` 受控预览草案；预览不改变治理状态，也不能绕过提交门禁。每项同时返回 `measurement_plan.status`、测量时间点中文标签和是否仍需人工审核；列表不暴露 worksheet 内部 ID。

### `GET /api/programs/<id>`

用途：返回单个项目测试练习包详情，包括 sessions、书写提示、反思问题、非诊断边界和结构化 `measurement_plan`。生产环境草案详情仅允许研究者、督导或管理员携带身份并传 `include_drafts=true` 预览。测量计划包含前测/后测 worksheet 引用、时间点、主要观察维度和人工审核项；`draft_requires_research_review` 不代表方案已批准。小程序端书写草稿只本地缓存，不上传后端。

### 共享错误码

任务八已在 `shared/constants/api.ts` 增加 `API_ERROR_CODES`，当前覆盖 `unauthorized`、`forbidden`、`not_found`、`missing_user_id`、`invalid_date`、`invalid_intensity_level`、`brief_text_too_long`、`review_required`、`content_validation_failed`。任务九补充 `/readyz` 端点和全局 `internal_error` 稳定错误外形。

## 0A. 用户同意记录

### `POST /api/consent`

用途：记录用户使用说明、隐私说明、非诊断边界说明、匿名研究授权等同意状态。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 匿名用户 ID；开发环境缺省为 `demo-parent`，生产环境必填 |
| `consent_type` | string | 是 | `user_agreement`、`privacy_policy`、`non_diagnostic_notice`、`research_authorization`、`contact_permission` |
| `consent_version` | string | 否 | 同意文本版本，缺省为 `2026.06-consent-v1` |
| `agreed` | boolean | 是 | 是否同意；`research_authorization` 允许为 `false` |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 同意记录 ID |
| `user_id` | string | 匿名用户 ID |
| `consent_type` | string | 同意类型 |
| `consent_version` | string | 同意文本版本 |
| `agreed` | integer | 1 表示同意，0 表示不同意或撤回 |
| `agreed_at` | string | 记录该选择的时间 |
| `revoked_at` | string/null | 不同意或撤回时的时间 |
| `created_at` | string | 创建时间 |

### `GET /api/consent?user_id=xxx`

用途：查看某个匿名用户的同意记录。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 同意记录列表 |
| `count` | integer | 记录数 |

边界：

- 不采集真实姓名、手机号、身份证号等强身份信息。
- 匿名研究授权不与基础使用强绑定。
- 当前只是同意记录，不是完整登录或权限系统。

## 0B. 风险人工复核记录

### `GET /api/risk-review`

用途：查看 high/medium 风险初筛后进入人工关注的复核队列。

请求头：必须带 `X-Admin-Token`。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 否 | 可筛选 `pending`、`reviewed`、`follow_up_needed`、`transferred`、`closed` |
| `limit` | number | 否 | 默认 50 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 风险复核记录列表 |
| `count` | integer | 记录数 |

### `POST /api/risk-review/<id>/review`

用途：保存风险复核处理状态和人工备注。

请求头：必须带 `X-Admin-Token`。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `reviewer_id` | string | 否 | 复核人匿名 ID，默认 `web-admin` |
| `review_status` | string | 否 | `pending`、`reviewed`、`follow_up_needed`、`transferred`、`closed`，默认 `reviewed` |
| `review_note` | string | 否 | 后台人工备注，不应保存完整高风险原文 |
| `action_taken` | string | 否 | 已采取的最小处置动作 |
| `closed_reason` | string | 否 | 关闭或暂不继续处理的原因 |

边界：

- `POST /api/feedback/generate`、`POST /api/profile`、画像 followup、沙盘反思、督导请求和家长测评开放文本命中 medium/high 风险时会自动创建 `pending` 复核记录。
- 复核更新会写入 `audit_logs.action=review_risk`。
- 该接口只做人工关注流转，不承诺实时危机干预。
- `matched_categories_json` 仅保存命中的风险类别和关键词摘要，不保存完整自由文本原文。

## 1. 目标设定

### `POST /api/goals`

用途：创建家长 7 天小目标。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 测试用户或家长弱身份 ID，缺省为 `demo-parent` |
| `nickname` | string | 否 | 昵称或测试编号 |
| `scene` | string | 是 | 高频亲子冲突场景 |
| `smart_goal` | string | 是 | 7 天 SMART 小目标 |
| `motivation` | string | 否 | 改变动机 |
| `start_date` | string | 否 | 目标开始日期 |
| `status` | string | 否 | 默认 `active` |

响应：`data` 中返回完整目标记录。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 目标 ID |
| `user_id` | string | 用户 ID |
| `scene` | string | 高频亲子冲突场景 |
| `smart_goal` | string | 7 天 SMART 小目标 |
| `motivation` | string/null | 改变动机 |
| `start_date` | string/null | 开始日期 |
| `status` | string | `active`、`done`、`paused` |
| `created_at` | string | 创建时间 |
| `updated_at` | string | 更新时间 |

### `GET /api/goals`

用途：查询目标记录。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `status` | string | 否 | 按状态筛选 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 目标记录列表 |

## 2. 情绪事件记录

### `POST /api/diaries`

用途：提交一次亲子互动或情绪事件记录。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `nickname` | string | 否 | 昵称或测试编号 |
| `goal_id` | string | 否 | 关联目标 ID |
| `event_time` | string | 否 | 事件发生时间 |
| `scene` | string | 是 | 冲突或互动场景 |
| `event_description` | string | 是 | 具体事件 |
| `parent_emotion` | string | 是 | 家长主要情绪 |
| `parent_emotion_intensity` | integer | 否 | 家长情绪强度，1-10；缺省为 5 |
| `child_emotion` | string | 否 | 孩子主要情绪 |
| `child_emotion_intensity` | integer | 否 | 孩子情绪强度，1-10 |
| `automatic_thought` | string | 否 | 家长自动想法 |
| `body_sensation` | string | 否 | 身体感觉 |
| `behavior` | string | 否 | 当时行为或回应 |
| `raw_text` | string | 否 | 原始记录文本 |

响应：`data` 中返回完整情绪事件记录。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 情绪事件记录 ID |
| `user_id` | string | 用户 ID |
| `goal_id` | string/null | 关联目标 ID |
| `event_time` | string/null | 事件发生时间 |
| `scene` | string | 场景 |
| `event_description` | string | 事件描述 |
| `parent_emotion` | string | 家长主要情绪 |
| `parent_emotion_intensity` | integer | 家长情绪强度 |
| `child_emotion` | string/null | 孩子主要情绪 |
| `child_emotion_intensity` | integer/null | 孩子情绪强度 |
| `automatic_thought` | string/null | 自动想法 |
| `body_sensation` | string/null | 身体感觉 |
| `behavior` | string/null | 行为或回应 |
| `raw_text` | string/null | 原始记录 |
| `created_at` | string | 创建时间 |
| `updated_at` | string | 更新时间 |

### `GET /api/diaries`

用途：查询情绪事件记录。小程序端可查询本人记录，网页端可用于后台列表。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `page` | integer | 否 | 页码，从 1 开始，默认 1 |
| `page_size` | integer | 否 | 每页条数，默认 50，最大 100 |
| `limit` | integer | 否 | 兼容旧客户端；未传 `page_size` 时作为每页条数 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 情绪事件记录列表 |

当前版本没有返回 `total`，也没有实现 `offset` 分页。

## 3. 即时反馈

### `POST /api/feedback/generate`

用途：基于已保存记录或临时文本生成非诊断、支持性、非评判反馈。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `diary_id` | string | 否 | 已保存情绪事件记录 ID |
| `event_description` | string | 否 | 事件描述，未保存时可直接传入 |
| `automatic_thought` | string | 否 | 自动想法 |
| `behavior` | string | 否 | 当时行为 |
| `free_text` | string | 否 | 补充自由文本，用于风险预检 |
| `raw_text` | string | 否 | 原始记录文本 |

说明：

- 如果传入 `diary_id`，后端会优先读取数据库中的该条情绪事件记录。
- 如果 `diary_id` 不存在，会返回 `not_found`。
- 如果没有匹配任何规则，会返回一条通用支持性反馈。
- 生成普通反馈前会先检查 `event_description`、`automatic_thought`、`behavior`、`free_text`、`raw_text` 中的风险关键词。
- 如果命中 high 风险，后端不会生成普通互动反馈，也不会推荐普通训练卡；`recommended_card_ids=[]`，`supportive_feedback` 使用风险安全提示，`alternative_response` 使用边界说明。
- 如果未命中 high 风险，后端会根据 `content/diary_training_map.json` 匹配情绪日记到训练卡的今日建议；该建议只用于当日轻量练习，不生成长期 3 天计划。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 反馈 ID |
| `diary_id` | string/null | 关联情绪事件记录 ID |
| `tags` | array | 识别标签 |
| `labels` | array | 标签中文名 |
| `trigger_summary` | string | 触发点摘要 |
| `pattern_summary` | string | 互动模式解释 |
| `supportive_feedback` | string | 支持性反馈 |
| `alternative_response` | string | 替代回应建议 |
| `recommended_card_ids` | array | 推荐训练卡 ID |
| `training_recommendation_rules` | array | 命中的情绪日记训练推荐规则，最多返回 2 条；每条规则最多包含 3 张训练卡、推荐理由、今日建议和边界说明 |
| `risk_level` | string | `low`、`medium`、`high` |
| `risk` | object | 风险预检结果，包含 `allow_auto_feedback`、`allow_recommended_training_cards`、`matched_categories`、`safe_response`、`boundary_notice` |

## 4. 训练卡

### `GET /api/cards`

用途：获取当前启用的全部训练卡。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 训练卡列表 |

训练卡字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 训练卡 ID |
| `type` | string | 训练卡类型 |
| `title` | string | 标题 |
| `purpose` | string | 使用目的 |
| `tags` | array | 适用标签 |
| `steps` | array | 练习步骤 |
| `example` | string | 示例话术 |
| `duration_minutes` | integer | 建议练习时长 |
| `enabled` | boolean | 是否启用 |

### `GET /api/cards/recommend`

用途：根据标签推荐训练卡。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `tags` | string | 否 | 逗号分隔标签，例如 `judgmental_language,repeated_urging` |
| `limit` | integer | 否 | 推荐数量，默认 3 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 推荐训练卡列表 |
| `matched_tags` | array | 本次用于匹配的标签 |

## 5. 练习打卡

## 5A. 测一测量表与工作表

### `GET /api/assessments`

用途：返回小程序“测一测”中的当前可用支持性测评列表。2026-06-30 起，接口优先从数据库 `assessment_worksheets` 读取；数据库未初始化或未同步时回退 `content/assessment_worksheets.json`。旧版自建 UP 工作表和附录示例仍下线，不回流到用户端。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `category` | string | 否 | 按分类筛选，例如 `量表类` |
| `audience_class` | string | 否 | 按对象筛选：`student`、`parent`、`adult` 等 |
| `reflex_node` | string | 否 | 按情绪反射弧或主题节点筛选 |
| `enabled` | string | 否 | `true` 只返回已开放项，`false` 只返回未开放项 |
| `q`/`query` | string | 否 | 按 ID、标题、分类和搜索关键词模糊检索 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `version` | string | 内容库版本 |
| `boundary_notice` | string | 统一边界提示 |
| `items` | array | 测一测条目列表 |
| `groups` | array | 按 `audience_class` 和 `reflex_node` 聚合的计数树 |

条目字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 工作表 ID |
| `source_file` | string | 来源 PDF 文件名 |
| `source_title` | string | 原工作表标题 |
| `display_title` | string | 小程序展示标题 |
| `category` | string | 分类 |
| `audience` | string | 目标对象 |
| `audience_class` | string | 前端筛选大类 |
| `reflex_node` | string | 情绪反射弧或主题节点 |
| `search_keywords` | array | 搜索关键词 |
| `sensitive_category` | string | 敏感语义类别；`none` 表示普通 |
| `pages` | integer | PDF 页数 |
| `instructions` | string | 填写说明 |
| `source_type` | string | 内容来源类型 |
| `review_status` | string | 审核状态 |
| `enabled_for_user` | boolean | 是否允许用户端进入填写 |
| `review_note` | string | 审核说明或暂不开放原因 |
| `boundary_notice` | string | 条目边界提示 |
| `result_disclaimer` | string | 结果页免责声明 |
| `profile_model_id` | string/null | 可选，默认使用该工作表下样本量最大的画像模型 |
| `question_count` | integer | 当前电子化填写项数量 |
| `is_reference` | boolean | 是否为附录示例参考 |

### `GET /api/assessments/<worksheet_id>`

用途：返回单个当前测评详情。已下线的旧版自建工作表 ID 会返回 `404 not_found`，不会继续提供详情或填写入口。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 工作表 ID |
| `source_file` | string | 来源 PDF 文件名 |
| `source_title` | string | 原工作表标题 |
| `display_title` | string | 小程序展示标题 |
| `category` | string | 分类 |
| `audience_class` | string | 前端筛选大类 |
| `reflex_node` | string | 情绪反射弧或主题节点 |
| `sensitive_category` | string | 敏感语义类别 |
| `pages` | integer | PDF 页数 |
| `instructions` | string | 原文或补录说明 |
| `sections` | array | 原工作表分区 |
| `questions` | array | 电子化填写项 |
| `scoring` | string | 计分说明 |
| `recommended_card_ids` | array | 建议关联训练卡 |
| `source_type` | string | 内容来源类型 |
| `review_status` | string | 审核状态 |
| `enabled_for_user` | boolean | 是否允许用户端进入填写 |
| `review_note` | string | 审核说明或暂不开放原因 |
| `boundary_notice` | string | 统一边界提示 |
| `result_disclaimer` | string | 结果页免责声明 |
| `profile_model_id` | string/null | 可选画像模型 ID |
| `training_recommendation_rules` | array | 与该测评匹配的训练推荐规则草稿，来源于 `content/assessment_training_map.json`，用于结果页展示推荐理由、今日建议和长期方向 |

### `POST /api/assessment-results`

用途：保存用户一次测一测填写结果。

说明：如果对应测评不存在或已下线，接口返回 `not_found`，不保存结果。如果对应测评仍存在但 `enabled_for_user=false`，接口返回 `assessment_not_enabled`，不保存结果。服务端以 worksheet 为唯一题目和计分真相：拒绝未知题号、重复题号、非法选项和缺少必答题，不使用客户端提交的 `score` 参与计分。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `nickname` | string | 否 | 昵称或测试编号 |
| `worksheet_id` | string | 是 | 工作表 ID |
| `answers` | array | 是 | 用户答案 |
| `result_summary` | string | 否 | 自定义结果摘要 |

`answers` 项字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `question_id` | string | 题目或填写项 ID |
| `prompt` | string | 可省略；保存时以 worksheet 中的题目原文为准 |
| `value` | string | 用户填写内容 |
| `score` | number | 兼容旧客户端，可省略；服务端忽略该值并按 worksheet 选项重新计分 |

答案校验失败时返回 `400`，主要错误码：

| 错误码 | 含义 |
|---|---|
| `invalid_answers` | `answers` 不是数组 |
| `invalid_answer` | 某项回答不是对象 |
| `unknown_question_id` | `question_id` 不属于当前 worksheet |
| `duplicate_question_id` | 同一题号重复提交 |
| `invalid_option_value` | `value` 不属于题目选项 |
| `missing_required_answers` | 缺少 worksheet 标记的必答题 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 结果 ID |
| `user_id` | string | 用户 ID |
| `worksheet_id` | string | 工作表 ID |
| `worksheet_title` | string | 工作表标题 |
| `category` | string | 分类 |
| `answers_json` | string | 答案 JSON |
| `scores_json` | string | 分数 JSON |
| `total_score` | integer/null | 数值题合计；记录型工作表为空 |
| `scores` | object | 本次计算出的总分、维度分、风险摘要等结构化分数 |
| `result_summary` | string | 支持性结果摘要 |
| `created_at` | string | 创建时间 |
| `recommended_card_ids` | array | 建议关联训练卡 |
| `risk` | object/null | 自由文本风险检查结果；高风险时不推荐普通训练卡 |
| `boundary_notice` | string | 量表边界提示 |
| `result_disclaimer` | string | 结果免责声明 |
| `profile_model_id` | string/null | 本次结果缓存的画像模型 ID |
| `profile_cluster_id` | string/null | 本次结果缓存的最接近画像簇 ID |
| `profile_pc1` | number/null | 本次结果在画像模型 PCA 二维图上的横坐标 |
| `profile_pc2` | number/null | 本次结果在画像模型 PCA 二维图上的纵坐标 |
| `profile_confidence` | number/null | 本次画像落点置信度 |

### `GET /api/assessment-results`

用途：查询测一测历史结果。接口只返回当前内容库仍保留的测评 ID 对应结果；旧版自建 UP 工作表或附录示例的历史残留记录不会返回给用户端。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `page` | integer | 否 | 页码，从 1 开始，默认 1 |
| `page_size` | integer | 否 | 每页条数，默认 50，最大 100 |
| `limit` | integer | 否 | 兼容旧客户端；未传 `page_size` 时作为每页条数 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 测一测结果列表 |
| `page` | integer | 当前页码 |
| `page_size` | integer | 当前每页条数 |
| `total` | integer | 当前用户符合条件的历史记录总数 |
| `has_more` | boolean | 是否还有下一页 |

### `GET /api/assessment-results/<result_id>/profile-position`

用途：根据一条已保存的测一测结果，实时计算其在既往调研数据聚类画像中的相对位置。该接口不落表，不返回逐行既往样本，只返回聚合模型、聚类中心和用户坐标。无对应画像模型时返回 `available=false`，不影响普通测评结果页。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为匿名用户 ID |
| `model_id` | string | 否 | 指定画像模型；不传时使用 worksheet 指向模型或同 worksheet 下样本量最大的模型 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `available` | boolean | 是否有可用画像位置 |
| `reason` | string | `available=false` 时的原因 |
| `model_id` | string | 使用的聚合画像模型 ID |
| `standard_scale_name` | string | 标准量表名 |
| `scale_id` | string | 量表 ID |
| `worksheet_id` | string | 工作表 ID |
| `research_dir` | string | 既往调研研究组目录 |
| `source_dataset` | string | 来源数据文件相对路径 |
| `n_cases` | integer | 模型样本量 |
| `n_features` | integer | 模型题项数 |
| `chosen_k` | integer | 聚类数量 |
| `position` | object | 用户 PCA 坐标、簇位置、后验概率、归一化熵、马氏距离和解释状态 |
| `clusters` | array | 聚类中心、人数、占比和支持性解释 |
| `feature_summary` | object | 本次题项覆盖情况 |
| `feature_profile` | array | 本次题项相对 z 分数，用于结果页雷达图 |
| `raw_scores` | object | 本次题项有效分，不含原始逐行研究数据 |
| `z_scores` | object | 本次题项标准分 |
| `explanation` | string | 支持性位置解释 |
| `boundary_notice` | string | 非诊断、非筛查边界 |

模型治理补充（2026-07-11）：

- 运行时只自动加载 `admission_status=pilot_approved/production_approved` 且 `artifact_hash` 校验通过的模型；`internal_only`、缺少准入字段或 hash 不一致的模型不参与自动匹配。
- 任务十二对角协方差 GMM 使用模型内 `mixture_weights`、`center_z` 和 `diag_covariances` 计算 posterior responsibility；`position.posterior`、`normalized_entropy`、`mahalanobis_distance` 和 `assignment_version` 可供研究端审计。
- `interpretation_status` 为 `low_confidence`、`outlier` 或 `pending_approval` 时，`profile_name`、训练问题和项目任务不返回普通自动解释。
- `confidence` 暂保留为兼容字段；前端应展示“匹配清晰度”低/中/较高，不得表述为模型准确率。

### `POST /api/checkins`

用途：提交训练卡练习打卡。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `nickname` | string | 否 | 昵称或测试编号 |
| `card_id` | string | 是 | 训练卡 ID |
| `diary_id` | string | 否 | 关联情绪记录 |
| `completed` | boolean | 否 | 是否完成，缺省为 `true` |
| `emotion_before` | integer | 否 | 练习前情绪强度，1-10 |
| `emotion_after` | integer | 否 | 练习后情绪强度，1-10 |
| `reflection` | string | 否 | 简短复盘 |

响应：`data` 中返回完整打卡记录。当前数据库中 `completed` 返回 `1` 或 `0`。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 打卡 ID |
| `user_id` | string | 用户 ID |
| `card_id` | string | 训练卡 ID |
| `diary_id` | string/null | 关联记录 ID |
| `completed` | integer | 1 表示完成，0 表示未完成 |
| `emotion_before` | integer/null | 练习前情绪强度 |
| `emotion_after` | integer/null | 练习后情绪强度 |
| `reflection` | string/null | 简短复盘 |
| `created_at` | string | 创建时间 |

### `GET /api/checkins`

用途：查询练习打卡记录。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `completed` | boolean | 否 | 仅返回已完成或未完成记录；不传则返回全部 |
| `page` | integer | 否 | 页码，从 1 开始，默认 1 |
| `page_size` | integer | 否 | 每页条数，默认 50，最大 100 |
| `limit` | integer | 否 | 兼容旧客户端；未传 `page_size` 时作为每页条数 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 打卡记录列表 |
| `page` | integer | 当前页码 |
| `page_size` | integer | 当前每页条数 |
| `total` | integer | 当前用户符合筛选条件的记录总数 |
| `has_more` | boolean | 是否还有下一页 |

列表项在原始打卡字段外增加 `card_title`、`card_duration_minutes` 和 `card_safety_level`，用于历史页稳定展示；未知或已移除训练卡仍保留原 `card_id`。

## 6. 周度报告

### `GET /api/weekly-report`

用途：根据本周情绪事件、反馈标签、练习打卡和学生画像复测生成周度报告。当前实现会在每次请求时生成一条 `weekly_reports` 数据库记录。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `week_start` | string | 否 | 周开始日期，例如 `2026-05-18`；不传则使用当前周一 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 周报 ID |
| `user_id` | string | 用户 ID |
| `week_start` | string | 周开始日期 |
| `week_end` | string | 周结束日期 |
| `frequent_scenes` | array | 高频场景，形如 `[["作业拖延", 2]]` |
| `frequent_emotions` | array | 高频情绪，形如 `[["着急", 2]]` |
| `common_patterns` | array | 常见标签，形如 `[["judgmental_language", 1]]` |
| `completed_cards` | array | 已完成训练卡 ID |
| `assessment_trend.assessment_count` | number | 本周普通测评提交次数 |
| `assessment_trend.worksheet_names` | array | 本周测评名称频次 |
| `assessment_trend.dimension_names` | array | 本周测评维度频次 |
| `thermometer_trend.record_count` | number | 本周情绪温度计记录次数 |
| `thermometer_trend.avg_intensity` | number | 本周平均情绪强度 |
| `thermometer_trend.min_intensity` | number | 本周最低情绪强度 |
| `thermometer_trend.max_intensity` | number | 本周最高情绪强度 |
| `thermometer_trend.trend_text` | string | 支持性趋势说明，不做诊断判断 |
| `profile_trend.profile_count` | number | 本周画像记录数 |
| `profile_trend.latest_round` | number | 本周最高画像轮次 |
| `profile_trend.profile_names` | array | 本周画像名称频次 |
| `profile_trend.requires_review_count` | number | 本周需复核画像数 |
| `profile_trend.high_risk_count` | number | 本周高风险画像数 |
| `next_week_suggestion` | string | 下周建议 |

## 7. 人工督导反馈

### `POST /api/supervision`

用途：提交典型记录给人工督导。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `nickname` | string | 否 | 昵称或测试编号 |
| `diary_id` | string | 否 | 关联记录 |
| `message` | string | 是 | 想请督导看的内容 |
| `contact` | string | 否 | 联系方式，第一版可选 |
| `risk_hint` | string | 否 | 用户自述风险提示 |
| `risk_level` | string | 否 | 默认 `low` |

响应：`data` 中返回完整督导请求记录。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 督导请求 ID |
| `user_id` | string | 用户 ID |
| `diary_id` | string/null | 关联记录 |
| `message` | string | 用户提交内容 |
| `contact` | string/null | 联系方式 |
| `risk_hint` | string/null | 风险提示 |
| `risk_level` | string | 风险等级 |
| `status` | string | 当前固定为 `pending` |
| `supervisor_reply` | string/null | 人工回复，当前创建时为空 |
| `created_at` | string | 创建时间 |
| `replied_at` | string/null | 回复时间 |

## 8. 后台数据导出

### `POST /api/content-review/update`

用途：本地开发阶段由 admin 受控修改 content JSON 中的审核状态。该接口只用于内容审核后台，不用于用户端，不自动发布、不上传体验版、不提交审核。

请求头：

| Header | 必填 | 说明 |
|---|---|---|
| `X-Admin-Token` | 是 | 后台令牌。未提供或错误时返回 `401 unauthorized` |

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `content_type` | string | 是 | 支持 `scale`、`training_card`、`feedback_rule`、`student_profile_rule`、`assessment_training_rule`、`diary_training_rule` |
| `item_id` | string | 是 | 内容项 ID |
| `review_status` | string | 否 | 允许值：`draft`、`pending_review`、`reviewed`、`trial_enabled`、`enabled`、`disabled`、`metadata_only`、`pilot_ready` |
| `enabled_for_user` | boolean | 否 | 仅允许写入 `false` 或保持不变；如传 `true`，接口返回 `409 manual_confirmation_required`，不写入文件 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `content_type` | string | 内容类型 |
| `item_id` | string | 内容项 ID |
| `review_status` | string | 更新后的审核状态 |
| `enabled_for_user` | boolean/null | 更新后的开放状态；没有开放字段的规则可能为空 |
| `filename` | string | 被更新的 content JSON 文件 |

边界：

- 该接口必须带 `X-Admin-Token`；
- `enabled_for_user=true` 或任何真实开放状态必须单独人工确认，本接口当前会阻断；
- 不新增数据库，不替代正式环境的后端接口 + `audit_logs` 方案；
- 正式发布前所有 content JSON 修改仍需人工复核。

### `GET /api/admin/worksheets`

用途：后台读取数据库中的测评量表列表，用于任务四量表入库后的管理和核对。

鉴权：

```text
Authorization: Bearer <admin token>
```

开发阶段兼容旧后台令牌：

```text
X-Admin-Token: safehome-local-admin-token
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `category` | string | 否 | 按分类筛选 |
| `audience_class` | string | 否 | 按对象大类筛选 |
| `review_status` | string | 否 | 按审核状态筛选 |
| `enabled` | string | 否 | `true` 或 `false` |
| `q` | string | 否 | 按 ID、标题、来源和关键词搜索 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 量表列表 |
| `count` | integer | 返回数量 |

### `POST /api/admin/worksheets`

用途：后台新增一条测评量表记录，写入 `assessment_worksheets` 表并记录审计日志。

说明：该接口面向本地和后台管理，不代表自动开放用户端。若要给用户端展示，仍需人工确认 `enabled_for_user`、`review_status`、非诊断边界和题项授权。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | 量表 ID |
| `display_title` | string | 是 | 展示标题 |
| `category` | string | 否 | 分类 |
| `audience_class` | string | 否 | 对象大类 |
| `reflex_node` | string | 否 | 情绪反射弧节点 |
| `questions` | array | 否 | 题项数组，会保存为 JSON |
| `dimensions` | array | 否 | 维度数组，会保存为 JSON |
| `enabled_for_user` | boolean | 否 | 是否允许用户端进入填写 |
| `review_status` | string | 否 | 审核状态，默认 `draft` |

### `PUT /api/admin/worksheets/<worksheet_id>`

用途：后台更新一条测评量表记录，写入 `assessment_worksheets` 表并记录审计日志。

说明：可更新字段与新增接口基本一致。接口不会删除历史测评结果，不会替代人工审核。

### `GET /api/admin/export`

用途：导出后台数据，当前版本返回 CSV 文件流。

请求头：

| 请求头 | 必填 | 说明 |
|---|---|---|
| `X-Admin-Token` | 是 | 后台导出令牌。默认本地开发令牌为 `safehome-local-admin-token`，可通过后端环境变量 `ADMIN_EXPORT_TOKEN` 修改。 |

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | string | 否 | 默认 `diaries`。支持：`goals`、`diaries`、`feedback`、`checkins`、`assessments`、`profile`、`student_profiles`、`records`、`student_followups`、`sandplay`、`parent_assessments`、`raw_wide`、`long`、`codebook`、`reports`、`supervision`、`cards` |
| `user_id` | string | 否 | 除 `cards`、`codebook`、`raw_wide`、`long` 外，可按用户筛选 |
| `module_type` | string | 否 | `type=records` 时可按模块筛选，例如 `student_profile` |
| `confirm_high_risk` | boolean | 否 | 当 `profile`、`student_profiles` 或 `records` 导出含高风险/需复核记录时，必须为 `true` |
| `limit` | number | 否 | 默认 `1000`，最大 `5000`；超过最大值返回 `400 invalid_export_limit` |

响应：

- 成功时返回 `text/csv; charset=utf-8`。
- 响应头包含 `Content-Disposition: attachment; filename=safehome_{type}.csv`。
- 未提供或提供错误 `X-Admin-Token` 时返回 `401 unauthorized`。
- 当前不支持 `type=all`。
- 当前不支持 `format` 参数。
- `type=profile` 会从 `student_profiles` 中导出学生画像摘要，默认使用匿名 ID，不导出真实 `user_id`、自由文本原文和联系方式。
- `type=records` 会从 `records` 导出统一研究摘要，可按 `module_type` 筛选。
- `type=assessments` 只导出当前 `content/assessment_worksheets.json` 中仍保留的测评 ID；旧版自建 UP 工作表和附录示例的历史残留记录不会导出。
- 如果画像或 records 导出包含 `risk_level=high` 或 `requires_review=true`，未带 `confirm_high_risk=true` 会返回 `409 high_risk_export_confirmation_required`。
- 导出审计会记录 `contains_high_risk`、`confirmed_high_risk_export`、`limit`、`row_count_before_limit` 和 `row_count_exported`。
- `type=profile` / `student_profiles` 导出包含 `research_authorization_status` 和 `consent_summary_json`。
- `type=parent_assessments` 导出包含 `research_consent` 和 `research_consent_status`。

本地开发调用示例：

```powershell
Invoke-WebRequest `
  -Uri "http://127.0.0.1:5000/api/admin/export?type=diaries" `
  -Headers @{ "X-Admin-Token" = "safehome-local-admin-token" } `
  -OutFile safehome_diaries.csv
```

## 9. 当前已知接口边界

- 当前没有完整登录认证和角色权限控制。
- 当前后台导出接口已增加 `X-Admin-Token` 令牌校验；开发环境默认令牌为 `safehome-local-admin-token`。
- 当 `APP_ENV=production` 时，后端启动必须显式配置 `ADMIN_EXPORT_TOKEN`，且禁止继续使用默认本地令牌。
- 当前没有分页总数 `total`。
- 当前列表接口只提供简单 `limit`。
- 当前即时反馈由规则匹配生成，不代表诊断、评估或治疗建议。

## 10. 学生画像接口：0版网页评估画像整合

本节根据夏老师“0版网页与安心家整合”资料、8 张思维导图和 GitHub 参考项目整理。当前已实现 `POST /api/profile`、`POST /api/risk/check`、`GET /api/model/info`，用于学生画像规则生成、风险关键词初筛和模型/规则版本说明。

当前目标：

- 将 0版网页沉淀为安心家的“评估画像与反馈引擎”；
- 支持学生画像、置信度、维度解释、推荐任务和人工复核；
- 保持非诊断、非标签化、支持性表达；
- 为研究导出保留模型版本、规则版本和授权字段。

### `POST /api/profile`

用途：根据量表分数和自由文本生成学生支持性画像。该接口不输出临床诊断。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 学生或测试用户弱身份 ID，缺省可沿用测试用户 |
| `assessment_result_id` | string | 否 | 关联已有测一测结果；当前生成后会另存一条画像测评结果 |
| `round` | integer | 否 | 第几轮测评，默认 1 |
| `scores.test_anxiety` | number | 是 | 考试焦虑相关分数 |
| `scores.iu_score` | number | 是 | 不确定性不耐受相关分数 |
| `scores.f_score` / `scores.fear_score` | number | 否 | 情绪调节灵活性或恐惧倾向相关分数 |
| `scores.self_compassion` | number | 是 | 自我同情/自我支持相关分数 |
| `support_resource` | string | 否 | 当前可用支持资源 |
| `free_text` | string | 否 | 学生日记、访谈或补充说明文本，仅作辅助线索和风险初筛 |

请求示例：

```json
{
  "user_id": "demo-student",
  "round": 1,
  "scores": {
    "test_anxiety": 3.8,
    "iu_score": 4.2,
    "f_score": 2.9,
    "self_compassion": 3.1
  },
  "free_text": "最近总担心考不好，爸妈会失望..."
}
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `assessment_result_id` | string | 保存到 `assessment_results` 后生成的记录 ID |
| `student_profile_id` | string | 保存到 `student_profiles` 后生成的画像结果 ID |
| `saved_to_assessment_results` | boolean | 是否已保存到现有测一测结果表 |
| `saved_to_student_profiles` | boolean | 是否已保存到画像专用表 |
| `profile_name` | string | 画像名称，例如 `压力警觉型画像`，前端不使用“人格”字样 |
| `profile_code` | string | 画像编码，例如 `pressure_alert` |
| `confidence` | number | 画像置信度，0-1 |
| `dimensions` | array | 关键维度解释列表 |
| `supportive_explanation` | string | 支持性解释 |
| `strength_note` | string | 优势视角提示 |
| `small_step` | string | 当前最小行动建议 |
| `recommended_card_ids` | array | 推荐训练卡 ID |
| `risk_level` | string | `low`、`medium`、`high` |
| `requires_review` | boolean | 是否需要人工复核 |
| `allow_auto_feedback` | boolean | 是否允许继续生成普通自动反馈 |
| `model_version` | string | 模型或规则版本 |
| `rules_version` | string | 画像反馈规则版本 |
| `boundary_notice` | string | 非诊断边界说明 |
| `created_at` | string | 生成时间 |

响应示例：

```json
{
  "ok": true,
  "data": {
    "assessment_result_id": "assessment_001",
    "student_profile_id": "profile_001",
    "saved_to_assessment_results": true,
    "saved_to_student_profiles": true,
    "profile_name": "压力警觉型画像",
    "profile_code": "pressure_alert",
    "confidence": 0.8,
    "dimensions": [
      {
        "key": "anxiety_sensitivity",
        "label": "压力信号敏感度",
        "level": "high",
        "summary": "你可能更容易提前捕捉到考试、评价或不确定事件带来的压力信号。"
      }
    ],
    "supportive_explanation": "你当前可能更容易捕捉到压力信号，这不代表你有问题。",
    "strength_note": "敏锐可以帮助你提前准备，只是需要配合更温和的自我支持方式。",
    "small_step": "先完成一次 3 分钟情绪命名练习。",
    "recommended_card_ids": ["student_emotion_naming", "cbt_auto_thought_student"],
    "risk_level": "low",
    "requires_review": false,
    "allow_auto_feedback": true,
    "model_version": "profile-rules-v1",
    "rules_version": "2026.06-student-profile-rules-v1",
    "boundary_notice": "本结果不是临床诊断，仅用于自我理解和练习参考。",
    "created_at": "2026-06-01T10:00:00"
  }
}
```

高风险说明：

- 当 `free_text` 命中高风险关键词时，接口返回 `profile_code=requires_review`；
- 此时 `allow_auto_feedback=false`，`recommended_card_ids=[]`；
- 前端应优先显示人工支持和现实求助提示，不进入普通训练推荐页。

### `POST /api/risk/check`

用途：检查文本中是否包含自伤、自杀、暴力、家暴、严重失眠等风险关键词。该接口只做初筛和人工复核分流，不构成危机评估结论。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `text` / `free_text` / `raw_text` | string | 否 | 待检查文本 |
| `source` | string | 否 | 来源模块，默认 `student_profile` |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `source` | string | 来源模块 |
| `risk_level` | string | `low`、`medium`、`high` |
| `matched_categories` | array | 命中的风险类别和关键词 |
| `requires_review` | boolean | 是否需要人工复核 |
| `allow_auto_feedback` | boolean | 是否允许普通自动反馈 |
| `allow_recommended_training_cards` | boolean | 是否允许普通训练卡推荐 |
| `export_raw_text_by_default` | boolean | 导出时是否默认允许原文 |
| `safe_response` | string | 支持性安全提示 |
| `boundary_notice` | string | 风险初筛边界说明 |

响应示例：

```json
{
  "ok": true,
  "data": {
    "source": "student_profile",
    "risk_level": "high",
    "matched_categories": [
      {
        "id": "self_harm",
        "label": "自伤/自杀风险表达",
        "risk_level": "high",
        "matched_keywords": ["不想活"],
        "safe_response": "你现在的安全比继续使用系统更重要。请尽快联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。"
      }
    ],
    "requires_review": true,
    "allow_auto_feedback": false,
    "allow_recommended_training_cards": false,
    "export_raw_text_by_default": false,
    "safe_response": "你现在的安全比继续使用系统更重要。请尽快联系现实中的可信成年人、学校老师、专业机构或当地紧急服务。",
    "boundary_notice": "风险关键词只用于初步提示和人工复核分流，不构成诊断或危机评估结论。"
  }
}
```

### `GET /api/model/info`

用途：返回当前画像模型或规则引擎信息，降低“黑箱感”，方便研究追溯。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_version` | string | 模型版本 |
| `rules_version` | string | 规则版本 |
| `available_profiles` | array | 当前可输出的画像类型 |
| `boundary_notice` | string | 非诊断边界说明 |

响应示例：

```json
{
  "ok": true,
  "data": {
    "model_version": "profile-rules-v1",
    "rules_version": "2026.06-student-profile-rules-v1",
    "available_profiles": [
      {
        "profile_code": "pressure_alert",
        "profile_name": "压力警觉型画像",
        "enabled": true,
        "risk_level": "low"
      }
    ],
    "boundary_notice": "学生画像只用于支持性理解和练习推荐，不构成临床诊断。"
  }
}
```

### `GET /api/profile-results`

用途：查询 `student_profiles` 中的学生画像历史结果，用于复测和轮次追踪。

请求头：后台列表接口必须带 `X-Admin-Token`。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 按用户筛选 |
| `round` | integer | 否 | 按测评轮次筛选 |
| `limit` | integer | 否 | 默认 50 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 学生画像结果列表 |

### `GET /api/profile-results/<profile_id>`

用途：查看单条学生画像结果详情，用于后台画像详情和后续人工复核。

说明：

- 读取详情时会写入 `audit_logs`，记录 `view_profile` 操作；
- 当前不返回自由文本原文；
- `dimensions_json`、`recommended_task_ids_json` 为 JSON 字符串。
- 返回中可包含 `latest_review`，表示最近一次人工复核记录。

### `GET /api/profile-results/<profile_id>/reviews`

用途：查看某条学生画像的人工复核记录列表。

请求头：必须带 `X-Admin-Token`。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 复核记录列表，按创建时间倒序 |

### `POST /api/profile-results/<profile_id>/review`

用途：保存人工复核备注、复核结论和处置状态。该接口不会覆盖学生端画像报告。

请求头：必须带 `X-Admin-Token`。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `reviewer_id` | string | 否 | 复核人标识；如果使用 `X-Admin-Token`，审计中只记 `admin-token` |
| `review_status` | string | 否 | `pending`、`in_progress`、`reviewed`、`escalated`、`closed`，默认 `reviewed` |
| `review_decision` | string | 否 | 复核结论 |
| `note` | string | 否 | 后台人工备注，不自动同步学生端 |
| `action_summary` | string | 否 | 处置摘要 |
| `visible_to_student` | boolean | 否 | 是否可向学生端展示，当前后台默认 `false` |

约束：

- `review_decision`、`note`、`action_summary` 至少填写一项；
- 保存后写入 `profile_reviews`；
- 保存后写入 `audit_logs`，`action=review_profile`；
- 不修改 `student_profiles` 的原始画像结果，不覆盖学生端报告。

学生画像保存时会在 `report.consent_summary` 和 `records.data_json.consent_summary` 中记录最近一次同意状态，但当前试点阶段不强制阻断画像提交。

### ReadFeedback 合并后的画像扩展接口

#### `GET /api/student-assessment`

用途：读取旧 ReadFeedback 学生画像量表题目、开放问题和模型版本。前端 `/student/assessment` 使用该接口渲染题目。

#### `GET /api/profile-results/<profile_id>/visuals`

用途：读取学生画像图表数据。

返回包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| `radar` | array | IU、ERF、自我支持、考试压力四类维度 |
| `pca` | object | 当前学生 PCA 坐标、训练样本点和聚类中心 |
| `trends` | array | 初测和后续追踪状态 |
| `keywords` | array | 自由文本关键词摘要，不等于诊断 |

#### `POST /api/profile-results/<profile_id>/followups`

用途：保存画像后的追踪反馈。

请求字段：`round_no`、`fit`、`task_done`、`state_score`、`text`。

#### `GET /api/profile-results/<profile_id>/followups`

用途：读取画像后的追踪反馈列表。

#### `POST /api/profile-results/<profile_id>/sandplay`

用途：保存学生沙盘式表达场景。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `scene.symbols` | array | 是 | 1-12 个象征物，含 `type`、`x`、`y` |
| `reflection_text` | string | 否 | 学生表达文本 |
| `task_title` | string | 否 | 当前沙盘任务标题 |

#### `GET /api/profile-results/<profile_id>/sandplay`

用途：读取某个学生画像下的沙盘表达记录。

### 家长双量表接口

#### `GET /api/parent-assessment`

用途：读取家长双量表、补充问题和非诊断边界说明。前端 `/assessment` 使用该接口渲染题目。

#### `POST /api/parent-assessments`

用途：提交家长双量表并生成支持性反馈报告。

请求字段：`answers`、`question_answers`、`participant_code`、`research_consent`、`started_at`、`completed_at`。

#### `GET /api/parent-assessments/<submission_id>`

用途：读取家长测评报告，前端 `/assessment/report/:id` 使用。

#### `POST /api/parent-assessments/<submission_id>/actions`

用途：保存家长查看报告后的行动反馈。

请求字段：`action_key`。

### 后台导出扩展

`GET /api/admin/export` 当前已支持：

| 参数 | 类型 | 说明 |
|---|---|---|
| `type=profile` | string | 导出学生画像结果摘要 |
| `type=student_profiles` | string | 导出 KMeans/PCA 学生画像摘要 |
| `type=student_followups` | string | 导出学生画像追踪反馈 |
| `type=sandplay` | string | 导出沙盘表达摘要 |
| `type=parent_assessments` | string | 导出家长双量表报告摘要 |
| `type=raw_wide` | string | 导出家长双量表原始宽表 |
| `type=long` | string | 导出家长双量表长表 |
| `type=codebook` | string | 导出学生画像量表和家长双量表 codebook |

后续建议继续支持：

| 参数 | 类型 | 说明 |
|---|---|---|
| `deidentify=true` | boolean | 默认脱敏导出 |
| `format=csv/json` | string | 第一版可只做 CSV，JSON 后置 |

导出边界：

- 默认使用匿名 ID；
- 默认不导出联系方式、自由文本原文和高风险文本原文；
- 未授权或 `export_allowed=false` 的记录不得导出；
- 当前后台导出会写入 `audit_logs`，记录导出类型、筛选用户和导出行数；
- 后续应继续补充导出数据字典和人工复核处置日志。

## 2026-07-01：任务六/任务七新增接口

### `GET /api/auth/capabilities`

用途：登录页在发起授权前读取账号密码、微信一键登录和手机号快捷登录的当前可用状态。接口只返回 `available` 和脱敏 `mode`，不返回 AppID、Secret、openid、手机号、令牌或其他身份值。

返回字段：

| 字段 | 说明 |
|---|---|
| `account_password.available` | 账号密码登录是否可用，当前固定为 `true` |
| `wechat_login.available/mode` | 当前 callContainer 请求是否带可信 CloudBase 身份，或是否配置标准 `jscode2session` |
| `phone_login.available/mode` | 容器微信令牌文件或标准微信 access token 配置是否可用 |
| `privacy_notice` | 能力探测的隐私边界 |

该接口用于区分“按钮代码故障”和“CloudBase 外部能力未配置”。即使快捷登录不可用，账号密码登录也必须继续可用。

### `POST /api/auth/wechat-login`

用途：微信小程序登录或绑定用户。仅当云托管部署显式设置 `TRUST_CLOUDBASE_IDENTITY_HEADERS=1` 时，后端读取 `wx.cloud.callContainer` 注入的 `X-WX-OPENID` 和固定值 `X-WX-SOURCE=wx-cloudbase`；默认关闭该信任路径，防止普通公网请求伪造身份头。非云托管环境使用 `code + WECHAT_APPID/WECHAT_SECRET` 调用 `jscode2session`。开发环境在两者都不可用时保留稳定兜底 openid。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `code` | string | 条件必填 | 微信登录 code；云托管可信身份头存在时可省略 |
| `nickname` / `nickName` | string | 否 | 昵称 |
| `avatar_url` / `avatarUrl` | string | 否 | 头像地址 |
| `anonymous_id` | string | 否 | 旧匿名 ID，用于平滑迁移 |

返回：`token`、`user`、`dev_fallback`、`identity_source`。`identity_source` 可为 `cloudbase_header`、`jscode2session` 或 `development_fallback`。

生产边界：接口不会把 `WECHAT_APPID`、`WECHAT_SECRET` 或微信服务端原始错误暴露给用户；停用账号不能通过微信重新登录。

### `POST /api/auth/admin-create-account`

用途：由持有 `X-Admin-Token` 的负责人创建研究者、督导或管理员等后台角色账号。任务十八后可传 `rotate_existing=true` 幂等轮换同名账号的密码和角色；未显式传该字段时，同名账号仍返回 `409 username_exists`。

生产研究者用户名固定为 `safehome_researcher_01`。一次性密码由 `backend/scripts/bootstrap_researcher.py prepare` 生成到 `.codex_tmp`，再由 `apply` 子命令调用本接口；密码不得写入 Git、API 文档或普通运行日志。

### `GET /api/profile/stats`

用途：小程序“我的”页和首页读取轻量统计。

查询字段：`user_id`。

返回包含：连续天数、本周记录数、本周日记数、本周训练数、本周测评数、已完成测评数、未完成测评数、未读消息数和边界说明。

### `GET /api/messages`

用途：读取用户消息列表。

权限：

- 普通用户必须携带 `Authorization: Bearer <token>`，只能读取自己的消息；
- `admin`、`supervisor` 可按权限带 `user_id` 查询；
- 不再允许只靠 `user_id` 查询参数读取消息。

查询字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `user_id` | string | 用户 ID |
| `status` | string | 可选 `unread` 或 `read` |
| `message_type` | string | 可选，按消息类型筛选 |
| `page` | number | 页码，从 1 开始 |
| `page_size` | number | 每页数量，1 至 100；`limit` 继续作为兼容别名 |

返回：`items`、`count`、`total`、`page`、`page_size`、`has_more`、`unread_count`。

消息对象只返回参与者展示所需字段：`id`、`user_id`、`message_type`、`title`、`body`、`source_type`、`source_id`、`sender_role`、`status`、`is_unread`、`created_at`、`read_at`。内部 `sender_id` 与 `idempotency_key` 不返回给消息列表或详情接口。

### `POST /api/messages`

用途：研究者、督导或管理员向关系探索试点参与者发送站内消息。收件人由 `enrollment_id` 对应的报名记录确定，客户端不能直接指定任意 `user_id`。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `enrollment_id` | string | 是 | 关系试点报名 ID |
| `title` | string | 是 | 1 至 60 个字符 |
| `body` | string | 是 | 1 至 2000 个字符 |
| `message_type` | string | 否 | `researcher_message` 或 `relationship_stage_feedback`，默认前者 |
| `idempotency_key` | string | 否 | 防止重复发送；也可使用 `Idempotency-Key` 请求头 |

约束：发送前执行文本风险预检；研究者消息命中高风险表述时返回 `409 message_requires_supervisor_review`。仅 `status=enrolled` 的报名记录可接收消息；研究者第一次写操作会认领未分配报名，之后其他研究者返回 `403 researcher_assignment_conflict`，督导和管理员不受该分配限制。同一发送者重复使用幂等键时，请求内容必须完全一致，否则返回 `409 idempotency_conflict`。成功写入 `messages` 后，参与者通过 `GET /api/messages` 读取。

### `GET /api/messages/<message_id>`

用途：读取消息详情，并把未读消息标记为已读。

查询字段：`user_id`。

权限：同 `GET /api/messages`。

### `POST /api/messages/<message_id>/read`

用途：显式标记消息已读。

请求字段：`user_id`。

权限：同 `GET /api/messages`。

### `POST /api/messages/read-all`

用途：将当前登录用户的全部未读消息标记为已读。普通用户只能更新自己的消息；管理员或督导可按权限传 `user_id`。

返回：`updated_count`、`status=read`。

### `POST /api/supervision/<request_id>/reply`

用途：后台督导或管理员给人工督导请求补充回复。保存后会向用户写入一条 `supervision_feedback` 消息。

权限：后台 `admin` 或 `supervisor`。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `supervisor_reply` / `reply` | string | 是 | 补充反馈 |

边界：该回复用于补充理解和练习建议，不替代紧急危机处理。

### `GET /api/admin/worksheets`

用途：后台读取数据库中的小程序测评题库入口。该接口读取 `assessment_worksheets`，不是只读量表目录。

权限：后台 `admin`。

### `POST /api/admin/worksheets`

用途：后台新增测评题库入口。

权限：后台 `admin`。

必要字段：`id`。建议同时填写 `display_title`、`category`、`review_status`、`boundary_notice`、`result_disclaimer`、`profile_model_id`。

约束：该接口不能直接设置 `enabled_for_user=true`。新增入口默认隐藏，开放必须走内容审核流程。

### `PUT /api/admin/worksheets/<worksheet_id>`

用途：后台更新测评题库入口，可更新用户端开放状态和 `profile_model_id` 绑定。

权限：后台 `admin`。

约束：该接口不能把 `enabled_for_user` 改为 `true`。如需开放用户端入口，应完成人工题项、授权、伦理复核后，通过内容审核流程开放。

### `DELETE /api/admin/worksheets/<worksheet_id>`

用途：软隐藏测评题库入口，不删除原内容和历史记录。实现方式为设置 `enabled_for_user=0`、`review_status=disabled`。

权限：后台 `admin`。

### `GET /api/admin/assessment-results`

用途：后台查看测评结果和画像落点回填字段。

权限：后台 `admin` 或 `researcher`。

查询字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `limit` | number | 最大 500 |
| `worksheet_id` | string | 按测评入口筛选 |
| `profile_model_id` | string | 按画像模型筛选 |

返回字段中 `profile_cluster_id` 为整数或 `null`，不要再按字符串处理。

## 2026-07-05：任务十新增/补强接口

### `POST /api/auth/bind-phone`

用途：微信小程序手机号绑定入口。

权限：必须携带 `Authorization: Bearer <token>`，不能匿名绑定。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `code` | string | 是 | 微信 `getPhoneNumber` 返回的手机号授权 code |

实现：使用微信 `getPhoneNumber` 一次性 code 换取已验证手机号；云托管优先读取 `/.tencentcloudbase/wx/cloudbase_access_token`，非云托管环境使用 `WECHAT_APPID/WECHAT_SECRET` 获取普通 access token。数据库只保存基于服务端密钥生成的不可逆 `phone_hash`，不保存完整手机号。

返回：`token`、`user`、`phone_bound=true`、仅本次响应可见的 `phone_masked`。

错误：未开通微信开放接口服务时返回 `wechat_phone_config_missing`；授权 code 失效返回 `wechat_phone_exchange_failed`；手机号已属于其他账号返回 `phone_account_conflict`。

### `POST /api/auth/phone-login`

用途：微信小程序手机号快捷登录。用户通过 `button open-type="getPhoneNumber"` 授权后，前端提交一次性 code；后端换取手机号、计算不可逆摘要、查找或创建家长账号并返回登录 token。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `code` | string | 是 | 微信 `getPhoneNumber` 返回的一次性手机号授权 code |
| `anonymous_id` | string | 否 | 旧匿名 ID，用于平滑迁移 |

账号合并规则：同一次云托管请求携带可信 `X-WX-OPENID` 时，优先把微信身份和手机号摘要绑定到同一账号；若二者已属于不同账号则返回 `409 phone_account_conflict`，不静默合并。

返回：`token`、`user`、`phone_bound=true`、`phone_masked`。完整手机号不会写入响应日志、研究导出或数据库。

### `POST /api/programs/<program_id>/entries`

用途：保存项目测试/课程练习过程记录，例如自我关怀书写、睡眠健康促进练习。

权限：优先从 Bearer token 解析用户；开发环境允许兼容 `user_id` 兜底。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `session_no` | number/string | 是 | 项目 session 序号 |
| `answers` | object | 否 | 页面草稿字段 |
| `reflection` | string | 否 | 练习后反思 |
| `analysis_consent` | boolean | 否 | 是否允许进入后续脱敏聚合分析 |
| `participation_status` | string | 否 | `completed/skipped/paused/withdrawn`，默认 `completed` |
| `recommendation_source` | string | 否 | `program_default/user_choice/researcher_adjusted` |
| `distress_before` | number | 否 | 练习前不适，0至10 |
| `distress_after` | number | 否 | 练习后不适，0至10 |
| `adverse_response` | boolean | 否 | 是否出现明显不适或负面体验 |

服务端校验 session 属于当前方案版本，并对反思文本执行透明风险分流。生产环境只允许 `pilot_approved` 项目提交；开发环境可预览草案。返回 `record`、`protocol_version`、`requires_review`、必要时的 `risk_safe_response` 和 `boundary_notice`。

保存位置：`records`，其中 `module_type=program_entry`，`source_id=<program_id>`；`data_json`绑定当前 `protocol_version`，不随之后内容升级漂移。

`answers.reflection_answers`可保存当前节每个反思问题的独立回答，结构为`[{question, answer}]`；旧版`reflection`摘要继续保留兼容。

### `GET /api/programs/<program_id>/entries`

用途：当前登录参与者回看本人在指定项目中已提交的各节记录。

权限：必须登录；Bearer token 所属用户优先于查询参数，不能读取其他参与者记录。

返回：`items[]`包含节次、逐题答案、反思摘要、练习前后不适、负面体验标记、参与状态和提交时间；不返回其他用户数据。

### `GET /api/training-plan`

任务十补强字段：

| 字段 | 说明 |
|---|---|
| `has_recent_checkin` | 用户近期是否有训练打卡 |
| `last_completed_card_ids` | 近期已完成训练卡 ID |
| `assignment` | 用户当前训练阶段、频率、开始日期、状态和短目标；未设置时为 `null` |
| `assignment.is_due_today` | 按开始日期、频率、状态和最近完成记录计算今天是否到期 |
| `assignment.next_practice_date` | 下一次建议练习日期；暂停/完成时为 `null` |
| `assignment.cadence_label` | 用户可读的节奏名称 |
| `assignment.due_reason` | 今日到期、下次日期、暂停或完成的用户说明 |
| `today_plan_items` | 今天到期时优先展示的最多2组推荐；未到期时为空 |
| `empty_state` | 没有推荐时的用户端空状态 |
| `plan_items[].source_worksheet_id` | 推荐来源测评 ID |
| `plan_items[].source_worksheet_title` | 推荐来源测评名称 |
| `plan_items[].source_dimension` | 推荐来源维度 |
| `plan_items[].source_profile_name` | 推荐来源画像名称 |
| `plan_items[].recommendation_reason` | 推荐理由 |
| `plan_items[].next_step` | 下一步练习建议 |
| `plan_items[].evidence_summary` | 来源证据摘要 |

边界：推荐只表示“更适合先尝试的练习线索”，不表示用户属于某种固定类型。

### `POST /api/training-plan/assignment`

用途：保存当前登录用户自行设置的训练阶段和练习频率。该设置复用 `records`，不代表研究者已确认的正式干预安排。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `phase` | string | 是 | `start`、`practice`、`consolidate` |
| `cadence` | string | 是 | `daily`、`every_other_day`、`three_per_week`、`weekly` |
| `start_date` | string | 是 | `YYYY-MM-DD` |
| `status` | string | 否 | `active`、`paused`、`completed`，默认 `active` |
| `goal_text` | string | 否 | 200 字内阶段目标 |

保存位置：`records.module_type=training_plan_assignment`、`source_id=current`、`export_allowed=0`。同一用户重复保存会更新当前记录；审计日志只记录枚举和是否填写目标，不保存目标原文。

返回会附带`is_due_today`、`next_practice_date`、`cadence_label`和`due_reason`，小程序据此安排今日训练，不只保存静态选项。

### `GET /api/progress-summary`

用途：首页“阶段性反馈”板块读取近期过程摘要。

查询字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `range` | string | `7d`、`14d`、`30d`，默认 `7d` |

返回包含：测评摘要、情绪温度计摘要、训练打卡摘要、情绪记录摘要、阶段状态、下一步建议和非诊断边界。

### `GET /api/profile-trend`

用途：返回阶段性画像/测评趋势的最小摘要。

查询字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `worksheet_id` | string | 可选，按测评筛选 |

返回包含：记录数、最近结果、簇计数、稳定性状态和边界说明。

### `GET /api/training-effectiveness`

用途：返回训练打卡效果的轻量摘要。

查询字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `range` | string | `7d`、`14d`、`30d`，默认 `30d` |

返回包含：`training_effectiveness`、兼容字段 `checkins`、`per_card_effectiveness`、`next_action` 和 `boundary_notice`。

任务十一补充：

- 优先使用 `checkins.before_thermometer_id` 和 `checkins.after_thermometer_id` 关联温度计记录计算练习前后变化；
- 如果没有温度计记录，则兼容使用 `emotion_before` 和 `emotion_after`；
- `per_card_effectiveness` 只表示过程观察摘要，不表示训练疗效承诺。

### `GET /api/courses`

用途：返回小程序课程页可展示的课程列表。

数据来源：`content/courses.json`。

返回包含：

| 字段 | 说明 |
|---|---|
| `items` | 课程摘要列表 |
| `pathways` | UP支持性课程路径、内容缺口和禁止自动释放模块 |
| `boundary_notice` | 非诊断边界说明 |

课程摘要包含 `id`、`title`、`theme`、`scene`、`duration_minutes`、`section_count`、`curriculum_node`、`learning_objectives`、`review_status`、关联训练卡和边界。

### `GET /api/courses/pathways`

用途：返回7节点支持性课程路径。当前“巩固与复发预防”保持内容缺口；暴露、内感性暴露和睡眠限制不得由该路径自动开放。

### `GET /api/courses/<course_id>`

用途：返回单个课程详情，供小程序课程详情页展示。

数据来源：`content/courses.json`。

返回包含：

| 字段 | 说明 |
|---|---|
| `course` | 课程详情 |
| `boundary_notice` | 非诊断边界说明 |

课程详情包含课程摘要字段，以及学习目标、核心概念、误区、正反例、理解检查、引导练习、迁移任务、复盘、巩固和分众文案。当前课程只作为支持性练习材料，不构成诊断、治疗或危机干预。

### `GET /api/courses/<course_id>/progress`

用途：读取当前用户该课程最新进度。无记录时 `progress=null`。

### `GET /api/courses/progress`

用途：读取当前用户每门课程的最新进度；研究者跨用户读取仍受 actor 权限控制。

### `POST /api/courses/<course_id>/progress`

用途：保存课程版本、完成章节、已尝试理解检查、迁移任务状态和关联训练卡。页面浏览不会自动写成完成。

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | `in_progress/completed/skipped` |
| `completed_section_count` | number | 不得超过当前课程章节数 |
| `knowledge_check_completed_ids` | string[] | 必须属于当前课程版本 |
| `transfer_task_status` | string | `not_started/planned/attempted/skipped` |
| `linked_card_id` | string | 可选，必须是课程关联训练卡 |

保存位置：`records.module_type=course_progress`、`source_id=<course_id>`、`export_allowed=0`。完成只表示已学习和尝试，不代表掌握或改善。

### `GET /api/text-analysis/summary`

用途：后台或研究视角读取离线文本分析聚合结果。

权限：需要管理员或研究者权限；当前兼容 `X-Admin-Token`。

数据来源：

```text
outputs/text_analysis/text_analysis_summary.json
outputs/text_analysis/text_features_summary.json
outputs/text_analysis/semantic_network_summary.json
outputs/text_analysis/family_topology_audit_summary.json
```

返回包含：

| 字段 | 说明 |
|---|---|
| `items.features` | 按用户/系统/督导写作者分层的情感计算聚合摘要 |
| `items.semantic_network` | 句子级语义共现网络；不是现实社会关系网络 |
| `items.family_topology` | 已生效且未撤回家庭绑定的聚合拓扑审计 |
| `items.summary` | 三类分析的离线总摘要和 manifest |
| `boundary_notice` | 文本分析边界说明 |

边界：

- 该接口只读取离线聚合输出文件；
- 不直接读取用户原始记录；
- 不返回 `event_description`、`raw_text`、`message`、`reflection` 等原文；
- 文本分析只用于脱敏研究摘要和内容质量观察，不用于诊断、个体画像定性或危机判断。
- 输出同时返回 `quality_status` 和 `privacy_gate_passed`；空数据、数据不足、隐私门禁失败的文件均为 `available=false`。
- 离线脚本使用 SQLite 只读连接，不调用 `init_db()`；默认最小支持度为 5，低频节点、边和小分组不输出。

补充约定（2026-07-09）：离线文本分析脚本读取人工督导回复时使用数据库真实字段 `supervision_requests.supervisor_reply`，只参与脱敏聚合输出，不向接口返回原文。

### `POST /api/checkins`

任务十补充可选字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `helpfulness_rating` | string/number | 用户主观有帮助程度 |
| `skip_reason` | string | 暂停或跳过原因 |
| `source_recommendation_id` | string | 来源推荐 ID |
| `before_thermometer_id` | string | 练习前温度计记录 |
| `after_thermometer_id` | string | 练习后温度计记录 |

边界：这些字段只用于过程复盘和聚合分析，不用于诊断或效果承诺。

## 2026-07-10：任务十二关系探索试点接口

统一前缀：`/api/relationship-pilot`。普通用户必须使用 Bearer 登录令牌且只能访问自己的记录；研究者、督导、管理员可查看授权试点档案。Web 后台兼容 `X-Admin-Token`。研究者查看、确认、发送、备注等操作写入 `audit_logs`。

| 方法与路径 | 权限 | 用途 |
|---|---|---|
| `POST /enrollments` | 学生 | 明确研究授权后，关联最近或指定的三份关系测评结果、维度、雷达和画像 |
| `GET /enrollments` | 登录用户/研究者 | 用户查自己；研究者查授权报名列表 |
| `GET /enrollments/<id>` | 本人/研究者 | 查看报名、报告、项目材料和研究备注；敏感材料访问会审计 |
| `POST /enrollments/<id>/report` | 本人/研究者 | 生成同源关系健康初筛报告；未复核时为 `pending_review` |
| `GET /reports/<id>` | 本人/研究者 | 查看报告；`download=1` 下载脱敏结构化 JSON |
| `POST /reports/<id>/confirm` | 研究者/督导/管理员 | 人工确认报告 |
| `PATCH /reports/<id>` | 研究者/督导/管理员 | 为已确认或已发送报告新增不可变版本，可写入 `personalized_interpretation` 等支持性阶段反馈字段；原报告不覆盖 |
| `POST /reports/<id>/send` | 研究者/督导/管理员 | 发送已确认报告或更新版本；更新版本以 `relationship_stage_feedback` 写入参与者消息列表 |
| `POST /enrollments/<id>/tasks` | 本人 | 保存关系绘画笔画数据或句子补全；需材料授权并执行风险预检 |
| `GET /researcher/dashboard` | 研究者/督导/管理员 | 查看报名、画像、报告、任务数、备注数和复核状态 |
| `POST /enrollments/<id>/notes` | 研究者/督导/管理员 | 新增不覆盖用户原报告的人工备注 |
| `POST /enrollments/<id>/narrative` | 研究者/督导/管理员 | 生成探索手记草稿 |
| `POST /narratives/<id>/confirm` | 研究者/督导/管理员 | 确认后允许用户查看探索手记 |
| `GET /narratives/<id>` | 本人/研究者 | 用户只能查看已确认版本 |
| `POST /enrollments/<id>/longitudinal` | 本人 | 保存每周补充测量或关键事件；开放文本进入风险预检 |
| `GET /growth` | 本人/研究者 | 返回变化曲线、成长时间轴、成长报告和四层阶段性画像 |

三份关系测评 ID：

```text
regulatory_focus_relationship_18
micro_ysq_relationship_18
relationship_initiation_intention_action
```

报告、画像、四层画像和成长报告只作阶段性观察、访谈准备和项目任务选择，不构成诊断、人格标签、关系能力评价或疗效证明。

### 2026-07-10 关系试点接口加固

| 方法与路径 | 权限 | 补充约定 |
|---|---|---|
| `GET /reports/<id>?download=1` | 本人/研究者 | 返回仅含用户可见字段的下载JSON；小程序据同源报告生成长图，不含模型中心、研究备注和内部ID |
| `PUT /reports/<id>/hypotheses/<index>` | 本人 | `response`仅允许`matches`、`does_not_match`、`uncertain`，用于共同核对机制假设 |
| `PATCH /reports/<id>` | 研究者/督导/管理员 | 新增一条白名单用户可见报告版本并提供新`version`，原版本保持不变；研究者高风险文字返回`409 report_requires_supervisor_review` |
| `POST /reports/<id>/send` | 研究者/督导/管理员 | `confirmed`或`updated`可发送；同一版本重复调用返回既有消息，不重复创建 |
| `POST /enrollments/<id>/tasks` | 本人 | 支持`Idempotency-Key`请求头，弱网重试不重复保存 |
| `POST /enrollments/<id>/longitudinal` | 本人 | 支持`Idempotency-Key`请求头，周记录/关键事件重试不重复保存 |
| `POST /api/product-events` | 登录用户 | 只接受枚举事件和枚举元数据，拒绝自由文本、绘画、句子及开放叙事原文 |

产品事件允许：`relationship_entry_clicked`、`relationship_step_completed`、`relationship_report_downloaded`、`relationship_task_save_failed`。报告确认继续复用服务端既有 `relationship_report_confirmed` 审计，不重复采集。元数据仅允许 `action`、`stage`、`status`、`source` 和布尔值 `retryable`，且字符串值必须命中服务端枚举。

登录补充：`POST /api/auth/wechat-login`优先使用CloudBase注入的可信`X-WX-OPENID`/`X-WX-SOURCE`；`POST /api/auth/phone-login`用微信`getPhoneNumber`凭证换取手机号并仅保存HMAC摘要。生产环境需配置CloudBase开放接口 `/wxa/business/getuserphonenumber`，否则手机号快捷登录不会可用。

## 统一请求追踪（2026-07-11）

1. 客户端可发送 8—64 位、仅含字母、数字、点、下划线或短横线的 `X-Request-ID`；非法值由服务端替换。
2. 所有响应返回 `X-Request-ID`。错误响应体同时返回顶层 `request_id`，可用于联调报障。
3. 服务端只记录 request ID、method、path、status 和 duration_ms，不记录 Authorization、请求正文、自由文本或联系方式。
4. `/readyz` 不返回数据库路径、MySQL 主机/库名或内容目录；详细部署信息由受控运维环境维护。

`GET /readyz`现同时返回数据库schema版本、内容版本、任务十二画像模型版本、风险复核积压和不含请求正文的进程内聚合指标。指标仅记录请求总量、错误量及指定操作失败次数。

## 2026-07-17：任务二十研究工作台与通用成长仪表盘

### `GET /api/research/participants`

用途：研究工作台参与者矩阵，支持 `q` 按用户 ID/昵称检索，`limit` 最大 100。

权限：

- `researcher` 只返回 `relationship_pilot_enrollments.assigned_researcher_id` 分配给自己的参与者；
- `supervisor`、`admin` 返回全部有业务记录的参与者；
- Web 后台兼容受控 `X-Admin-Token`；
- 每次查询写入 `audit_logs`，不向参与者端开放。

返回每位参与者的测评、情绪日记、训练打卡、项目练习、关系试点、人工支持和未读消息数量。矩阵不返回开放文本。

### `GET /api/research/participants/<user_id>`

用途：在同一只读档案中查看获授权参与者的测评、情绪日记、训练打卡、项目练习、关系试点报名/任务/报告、人工支持、消息和审计摘要。

边界：

- 单模块最多返回最近 100 条；
- 原始填写只读，研究者反馈与备注另存；
- 敏感详情访问写入 `audit_logs`；
- 内部状态由前端映射为中文，不直接展示数据库枚举。

### `GET /api/growth/overview`

用途：当前登录用户查看跨模块成长仪表盘。

返回：

| 字段 | 说明 |
|---|---|
| `summary` | 观察与练习总数、完成练习数、人工反馈数和下一小步 |
| `thermometer` | 最近 30 次 1—10 分情绪温度，按时间返回 |
| `assessment_groups` | 按 `worksheet_id` 分组的最近测评记录，不混合不同量尺 |
| `timeline` | 最近 50 条日记、训练、测评、项目、本周复盘和人工反馈事件 |
| `boundary_notice` | 非诊断、非疗效证明边界 |

该接口不生成跨量尺总分，也不因单次记录判断改善或恶化。

### `POST /api/feedback/generate` 任务二十补充

- 普通反馈按“确认当下感受—描述可观察线索—给一个可选择的小动作—说明边界”组织；
- `recommended_card_ids` 去重后最多返回 3 张，且只包含已启用、允许共享选择的训练卡；
- `training_recommendation_rules` 最多返回 1 条主规则，该规则内为 1 张主练习和最多 2 张备用练习；
- 高风险仍返回空训练卡和空普通规则，优先进入人工与现实支持路径。

## 2026-07-18：微信订阅练习提醒

### `GET /api/notifications/config`

权限：当前登录参与者本人。返回模板是否可用、订阅模式、真实发送开关和本人的授权状态；不返回 AppSecret、调度令牌、OpenID 或 access token。

### `POST /api/notifications/consent`

权限：当前登录参与者本人。

| 字段 | 类型 | 说明 |
|---|---|---|
| `template_id` | string | 必须与后端当前审核通过的模板 ID 一致 |
| `decision` | string | `accept`、`reject` 或 `ban`，来自 `wx.requestSubscribeMessage` 结果 |

拒绝或禁止授权只更新提醒偏好，不影响练习节奏、训练卡或站内消息。默认 `subscription_mode=once`；成功投递后状态改为 `consumed`，参与者需要再次主动授权。

### `POST /api/notifications/run-due`

权限：`admin`，或请求头提供有效 `X-Scheduler-Token`。请求体 `{ "dry_run": true }` 默认为演练，不调用微信发送接口。

真实发送需同时满足：模板已配置、参与者已授权、用户有微信 OpenID、计划状态为进行中、北京时间已到练习日、`WECHAT_SUBSCRIBE_SEND_ENABLED=1`。投递使用 `training_due:user_id:日期:template_id` 幂等键；成功或发送中的同一投递不重复发送，普通失败最多重试 3 次，微信返回未授权时停止并更新授权状态。

## 2026-07-18：匿名试用记录认领

### `GET /api/auth/data-claim-preview`

权限：已登录的 `parent/student/user` 本人。返回是否存在待认领记录、不可猜测的 `claim_id`、总数和按模块汇总的数量，不返回匿名 ID 或填写原文。研究者、督导和管理员不能使用。

### `POST /api/auth/data-claim`

权限：已登录的 `parent/student/user` 本人。请求体必须为 `{ "claim_id": "...", "confirm": true }`。服务只处理绑定到当前账号的候选；事务成功后更新参与者归属、流水和审计。重复提交返回既有结果，不重复迁移。

登录/注册/微信/手机号登录会把当前设备匿名 ID 登记为候选，但不会自动迁移。没有可认领记录时不创建候选。

## 2026-07-18：研究运营监控

### `GET /api/research/operations`

权限：`researcher/supervisor/admin` 或有效后台令牌。研究者只统计分配给自己的参与者；督导和管理员统计全量。返回提醒授权状态、投递状态、重试/过期数量、失败错误代码聚合、待阶段反馈、待人工支持和待风险复核数量。接口不返回 OpenID、模板密钥、联系方式、失败原文或参与者填写原文，并写入审计日志。

