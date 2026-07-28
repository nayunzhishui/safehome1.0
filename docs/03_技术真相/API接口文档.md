# API 接口文档

最后更新时间：2026-07-24

本文档记录 `safehome1.0 / 安心陪伴 / ReadFeedback` MVP 1.0 当前已经实现的 Flask + SQLite 后端 API。本文档以当前后端真实行为为准，用于小程序端与网页端并行联调。

进度口径：真实可调用接口以前文已实现章节为准；第 10 节”0版网页评估画像整合”已有基础画像、风险检查、模型信息、画像历史、人工复核、周报画像趋势、`type=profile` 脱敏导出、`type=records` 统一研究导出和高风险导出二次确认。当前总进度见 `docs/00_当前事实基准/项目进度统一口径.md`。

阅读方式：先看”通用约定”和对应接口章节；公开操作的机器登记见`API机器契约.md`和`shared/contracts/api-contract.json`。若与历史日志冲突，以机器契约、本文开头进度口径和`docs/00_当前事实基准/项目进度统一口径.md`为准。

## 任务二十七：完整内容治理接口

内容治理使用`content_governance_versions/reviews/releases`，运行内容仍由`content`目录提供。草稿不会覆盖运行内容；导入登记固定为`registered`，不会自动批准。研究者、督导和管理员可查看，发布、暂停、退役和恢复仅管理员可执行，并受`CONTENT_GOVERNANCE_PUBLISH_ENABLED`与独立确认保护。

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/content-review/inventory` | 查看运行内容、受控版本及缺失内容源 |
| POST | `/api/content-review/inventory/register` | 仅登记旧内容，绝不自动批准 |
| GET/POST | `/api/content-review/versions` | 查询版本/建立完整元数据草稿 |
| GET | `/api/content-review/versions/<id>` | 查看校验、审核、发布与依赖影响 |
| GET | `/api/content-review/versions/<id>/diff` | 查看相对父版本或运行内容的统一 diff |
| POST | `/api/content-review/versions/<id>/submit` | 校验通过后送审 |
| POST | `/api/content-review/versions/<id>/reviews` | 按研究、心理、伦理、内容责任保存审核证据 |
| POST | `/api/content-review/versions/<id>/publish` | 核对哈希、依赖和人工确认后原子切换 |
| POST | `/api/content-review/releases/<id>/<pause\|retire\|restore>` | 暂停、退役或按不可变包恢复 |
| POST | `/api/content-review/replay` | 批量运行不含真实数据的固定合成案例 |
| GET | `/api/content-review/active/<type>/<item_id>` | 小程序等客户端读取运行内容哈希与治理状态 |

草稿元数据必填：`source`、`source_version`、`copyright_status`、`age_scope`、`audience`、`change_summary`。版权未核验、适龄未核验、诊断化或疗效承诺文案、哈希变化、专业审核或证据路径缺失均阻断发布。错误响应可在`error.details`返回结构化阻断证据。

`POST /api/content-review/update`仅保留历史兼容；正式内容治理不得依赖该接口直接修改JSON。生产发布开关默认关闭，测试通过不代表研究、心理、伦理或生产发布批准。

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
- JSON成功响应统一包裹在`ok`、`data`和`request_id`中；错误响应统一为`ok:false/error.code/error.message/request_id`。
- CSV 导出接口返回 `text/csv; charset=utf-8`。
- 时间字段：后端当前使用 ISO 8601 字符串。
- CORS 来源白名单由 `ALLOWED_ORIGINS` 环境变量配置；开发默认允许 `http://127.0.0.1:5173` 和 `http://localhost:5173`。
- 当前已有签名登录、角色权限和对象范围校验；仅部分兼容接口在开发环境允许匿名`user_id`或默认测试用户，生产环境禁止依赖该兼容行为。
- 当 `APP_ENV=production` 时，目标、情绪记录、反馈、画像、打卡、督导、测评结果等写入接口必须传匿名 `user_id`，例如 `parent_xxx`、`student_xxx`、`tester_xxx`，否则返回 `validation_error`。
- 当 `APP_ENV=production` 时，目标、情绪记录、打卡、周报和测评结果等用户查询接口也必须传匿名 `user_id`，否则返回 `validation_error`。
- 后台敏感接口必须带 `X-Admin-Token`：`/api/admin/export`、`/api/risk-review`、`/api/profile-results` 列表、`/api/profile-results/<id>/reviews`、`/api/profile-results/<id>/review`、`/api/content-review/update`。
- 当前不接入复杂 AI 调用，即时反馈由 `content/feedback_rules.json` 规则匹配生成。

通用成功响应：

```json
{
  "ok": true,
  "data": {},
  "request_id": "01H..."
}
```

通用错误响应：

```json
{
  "ok": false,
  "error": {
    "code": "missing_fields",
    "message": "缺少必填字段：scene"
  },
  "request_id": "01H..."
}
```

响应头始终返回`X-Request-ID`。`GET /api/assessment-results`、`GET /api/checkins`和`GET /api/messages`暂时兼容旧`limit`参数；使用旧参数时返回`Deprecation:true`和`Sunset: 2026-10-31`，新调用应使用`page/page_size`。契约生成、漂移、兼容快照和API边界扫描已加入CI。

补充约定（2026-07-09）：鉴权辅助层会按状态码返回稳定错误码：`400 -> validation_error`、`401 -> unauthorized`、`403 -> forbidden`。参数缺失或后台查询缺少必要 `user_id` 时，不应返回 `unauthorized`，避免前端误提示登录过期。

## 0. 健康检查

### `GET /healthz`

用途：确认后端是否启动。该接口只返回轻量状态和不含路径/密钥的构建身份，不检查数据库。

响应示例：

```json
{
  "ok": true,
  "service": "safehome-backend",
  "env": "development",
  "version": "safehome-2026-06-04",
  "build": {
    "build_id": "10439c1c26c147970a36",
    "commit_sha": "<git-sha>",
    "build_time": "<UTC>",
    "api_contract_hash": "<sha256>",
    "content_manifest_hash": "<sha256>",
    "schema_expected": {"version": "2026_07_22_025"}
  }
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
- 容器API契约、content清单和数据库schema是否与包内构建指纹一致。

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
  "content": {},
  "build": {},
  "deployment": {"ok": true, "diagnosis": "consistent"}
}
```

生产环境缺少有效构建清单，或API契约、content清单、数据库schema任一不匹配时，`/readyz`返回`503`。所有响应同时带`X-SafeHome-Build-ID`和`X-SafeHome-Service-Version`，便于双端错误页关联；不返回本地路径、密钥或请求正文。

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

响应在原记录字段外增加`receipt`：包含当天本地日期、今日第几次、今日/近七天描述性均值、两条以内支持性文字、练习入口可用状态和非诊断边界。它只描述用户自己的记录，不判断变好、变差或疗效。

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

用途：返回某用户某一天的温度计记录、`min/max/avg/count` 汇总、`valence_avg/arousal_avg/control_avg` 轻量维度均值和边界说明。服务端按`Asia/Shanghai`解释带时区的ISO时间，避免UTC跨日把记录放错到前一天或后一天。

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

用途：微信小程序登录或绑定用户。当前生产默认只使用 `code + WECHAT_APPID/WECHAT_SECRET` 调用 `jscode2session`。只有部署显式设置 `TRUST_CLOUDBASE_IDENTITY_HEADERS=1` 时，后端才允许读取 CloudBase 注入的 `X-WX-OPENID`，并同时要求 `X-WX-SOURCE` 为 `wx_devtools`/`wx_client`、OpenID格式合法，以及存在服务端AppID时请求AppID完全匹配。2026-07-22 公网负向探针证明默认公网域名会透传调用者自填的 `X-WX-*` 头，因此只要服务仍开放该公网入口，就必须保持可信头开关为0；AppID匹配不能证明请求来自CloudBase。只有关闭公网入口、改为仅 `callContainer`，或拆分独立的小程序私有服务并重新完成负向验收后，才可考虑开启可信头。开发环境在正式身份路径都不可用时保留稳定兜底 openid。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `code` | string | 条件必填 | 微信登录 code；云托管可信身份头存在时可省略 |
| `nickname` / `nickName` | string | 否 | 昵称 |
| `avatar_url` / `avatarUrl` | string | 否 | 头像地址 |
| `anonymous_id` | string | 否 | 旧匿名 ID，用于平滑迁移 |

返回：`token`、`user`、`dev_fallback`、`identity_source`。`identity_source` 可为 `cloudbase_header`、`jscode2session` 或 `development_fallback`。

生产边界：接口不会把 `WECHAT_APPID`、`WECHAT_SECRET`、登录 code 或微信服务端原始响应暴露给用户或普通日志；传输故障日志只记录操作名、异常类型、上游HTTP状态和底层原因类型。停用账号不能通过微信重新登录。

### `POST /api/auth/admin-create-account`

用途：由持有 `X-Admin-Token` 的负责人创建研究者、督导或管理员等后台角色账号。可传 `rotate_existing=true` 显式轮换同名账号凭据，但轮换不能同时改变角色；未显式传该字段时，同名账号返回 `409 username_exists`。

生产研究者用户名固定为 `safehome_researcher_01`。一次性密码由 `backend/scripts/bootstrap_researcher.py prepare` 生成到 `.codex_tmp`，再由 `apply` 子命令调用本接口；密码不得写入 Git、API 文档或普通运行日志。

一次性凭据还必须传 `temporary_credential=true`、唯一 `credential_receipt_id` 和不超过24小时的 `credential_expires_at`。同一账号重复应用同一receipt为幂等成功；receipt跨账号复用返回`409 credential_receipt_reused`。一次性密码至少12位并包含四类字符中的三类。

### `POST /api/auth/change-password`

用途：登录用户修改当前密码；一次性账号首次登录后只允许访问`/api/auth/me`、本接口和logout，其他接口固定返回`403 password_change_required`。

请求字段：`current_password`、`new_password`。新密码至少12位并包含大小写字母、数字或符号中的三类，且不能与当前密码相同。成功后清除一次性凭据状态、递增`auth_epoch`、撤销旧token并返回新`token`、`user`与`sessions_revoked=true`。

### `GET /api/auth/admin-accounts/<username>`

用途：持有`X-Admin-Token`的负责人核验账号状态。仅返回用户名、角色、状态、最后登录时间、是否已设置密码、是否必须改密、凭据世代、临时凭据过期时间及锁定状态；不返回密码、哈希或receipt ID。

### `POST /api/auth/admin-accounts/<username>/unlock`

用途：解除因连续5次密码失败产生的15分钟临时锁定，并写入审计日志。不存在账号返回404。

### `POST /api/auth/admin-accounts/<username>/revoke`

用途：停用账号、清除一次性凭据状态并递增`auth_epoch`使现有token失效；重复撤销为幂等成功。恢复账号不属于本接口，必须走新的受控批准流程。

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

用途：研究工作台参与者矩阵，支持 `q` 按用户 ID/昵称检索；支持 `page`、`page_size` 分页，`page_size` 最大 100。旧客户端的 `limit` 参数继续作为 `page_size` 兼容输入。

权限：

- `researcher` 只返回 `relationship_pilot_enrollments.assigned_researcher_id` 分配给自己的参与者；
- `supervisor`、`admin` 返回全部有业务记录的参与者；
- Web 后台兼容受控 `X-Admin-Token`；
- 每次查询写入 `audit_logs`，不向参与者端开放。

返回每位参与者的测评、情绪日记、训练打卡、项目练习、关系试点、人工支持和未读消息数量，并返回 `total/page/page_size/has_more`。排序固定为最近活动倒序、用户 ID 升序，保证翻页稳定。矩阵不返回开放文本。

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
| `sections.activity` | 记录数、完成练习数和是否有数据；不包含测评分值 |
| `sections.assessments` | 测评记录数、量表组数和可比较的重复量表组数 |
| `sections.relationship` | 关系探索报名、任务、连续记录和阶段报告数量，以及最近报名ID |
| `sections.researcher_feedback` | 研究者反馈总数、未读数和最近一条最小摘要 |
| `thermometer` | 最近 30 次 1—10 分情绪温度，按时间返回 |
| `assessment_groups` | 按 `worksheet_id` 分组的最近测评记录，不混合不同量尺 |
| `timeline` | 最近 50 条日记、训练、测评、项目、本周复盘、关系探索和人工反馈事件 |
| `boundary_notice` | 非诊断、非疗效证明边界 |

该接口不生成跨量尺总分或单一成长分数，也不因单次记录判断改善或恶化。原`summary/thermometer/assessment_groups/timeline`字段继续兼容；`sections`为T23-04新增的统一成长入口分区事实。

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

真实发送需同时满足：模板已配置、参与者已授权、用户有微信 OpenID、计划状态为进行中、北京时间已到练习日、`WECHAT_SUBSCRIBE_SEND_ENABLED=1`。投递使用 `training_due:user_id:日期:template_id` 幂等键；成功或发送中的同一投递不重复发送。可恢复失败按5、10、20分钟指数退避，达到最大次数进入死信；拒绝授权、模板配置错误和永久失败停止自动重试并进入对应人工状态。

## 2026-07-18：匿名试用记录认领

### `GET /api/auth/data-claim-preview`

权限：已登录的 `parent/student/user` 本人。返回是否存在待认领记录、不可猜测的 `claim_id`、总数和按模块汇总的数量，不返回匿名 ID 或填写原文。研究者、督导和管理员不能使用。

### `POST /api/auth/data-claim`

权限：已登录的 `parent/student/user` 本人。请求体必须为 `{ "claim_id": "...", "confirm": true }`。服务只处理绑定到当前账号的候选；事务成功后更新参与者归属、流水和审计。重复提交返回既有结果，不重复迁移。

登录/注册/微信/手机号登录会把当前设备匿名 ID 登记为候选，但不会自动迁移。没有可认领记录时不创建候选。

## 2026-07-18：研究运营监控

### `GET /api/research/operations`

权限：`researcher/supervisor/admin` 或有效后台令牌。研究者只统计分配给自己的参与者；督导和管理员统计全量。返回提醒授权状态、投递状态、重试/过期数量、失败错误代码聚合、待阶段反馈、待人工支持和待风险复核数量。接口不返回 OpenID、模板密钥、联系方式、失败原文或参与者填写原文，并写入审计日志。

## 2026-07-19：参与者主旅程与协作式反馈

### `GET /api/journey/today`

权限：当前登录参与者本人；管理员、研究者和督导不能代查，查询其他`user_id`返回403。返回唯一`primary_action`及可选`secondary_action`，状态优先级为未读人工反馈、暂停/阶段完成、到期训练、今日完成、首次测评、首次记录、节奏设置和未到期等待。接口不返回消息正文、日记原文、量表答案或推荐权重。

### `POST /api/feedback-ledger`

权限：当前登录参与者本人。请求字段：`source_type`、`source_id`、`content_version`、`evaluation`、可选`reason_code/reason_text`和`idempotency_key`。`evaluation`只允许`matches/partly_matches/does_not_match/uncomfortable`。同一幂等键重复提交返回原记录；同一来源的新版本会把旧有效评价标为`superseded`。选择`uncomfortable`只进入人工复核并停止正向强化，不推断风险或诊断。

### `GET /api/feedback-ledger`

权限：当前登录参与者本人。可按`source_type/source_id`读取本人历史评价，响应以`status=active/superseded`区分当前版本和历史版本；不得跨用户读取。

### `GET /api/feedback-ledger/summary`

权限：`researcher/supervisor/admin`。研究者只看分配给自己的参与者。只返回评价/来源/复核状态的聚合数量，不返回原因文本和参与者原文。

## 2026-07-19：隐私状态与研究处置队列

### `GET /api/privacy/requests`

权限：当前登录参与者本人。分页返回本人的隐私申请ID、类型、状态和时间，不返回申请原因或内部处理备注。状态包含`pending/processing/completed/rejected/cancelled`。重复提交仍在处理中的删除申请时，`POST /api/privacy/delete-my-data`复用现有申请并返回`already_active=true`。

参与者响应可包含固定安全说明`participant_notice`和完成证明`execution_proof_hash`，但不返回`handled_note`。`POST /api/privacy/requests/<id>/cancel`仅允许本人取消`pending`申请；`POST /api/privacy/requests/<id>/appeal`仅允许本人将`rejected`申请补充说明后恢复为`pending`。两者均要求`Idempotency-Key`。

### 隐私申请后台处理与执行

以下接口仅允许`supervisor/admin`；`researcher`无权读取详情、批准或执行。所有查看、迁移、预览、批准、dry-run与正式执行均写入审计。

| 接口 | 用途与关键门禁 |
|---|---|
| `GET /api/privacy/admin/requests` | 分页队列；不返回申请原因和内部备注 |
| `GET /api/privacy/admin/requests/<id>` | 受控详情、处理轨迹、批准和执行摘要 |
| `POST /api/privacy/admin/requests/<id>/transition` | `start_processing/reject/return_to_pending`；不能人工写`completed` |
| `GET /api/privacy/admin/requests/<id>/preview` | 按白名单返回模块/表计数、保存类别、外部数据面和范围哈希 |
| `POST /api/privacy/admin/requests/<id>/approvals` | 绑定策略版本和范围哈希保存批准；同一人员不能充当两名批准人 |
| `POST /api/privacy/admin/requests/<id>/execute` | `dry_run=true`不改业务数据；`false`执行事务化删除/匿名化 |

正式执行默认由`PRIVACY_EXECUTION_ENABLED=0`阻断；数据保存矩阵未确认时由`PRIVACY_RETENTION_POLICY_APPROVED=0`阻断。生产还要求`PRIVACY_PRODUCTION_EXECUTION_ENABLED=1`、两名不同人员批准且至少一名管理员。执行失败整笔回滚；成功写入策略版本、范围哈希、结果计数、证明哈希和恢复墓碑。临时展示越权不参与这些权限判断，也不能作为正式权限验收证据。

撤回`anonymous_research/research_authorization`后，后端立即把可导出衍生记录设为不可导出，并从研究参与者矩阵、研究型队列、管理员导出和离线文本/家庭拓扑输入中排除；人工支持与风险支持数据不因此删除。

### `GET /api/research/queues`

权限：`researcher/supervisor/admin`。参数：`queue`、`page`、`page_size`和可选`status=active/all/具体状态`；队列类型为`notification_failed/stage_feedback/supervision/risk_review/feedback_review/privacy_request`。研究者仅看到已分配参与者，督导和管理员可看全量；隐私申请仅督导/管理员可见。每项返回工作项ID、优先级、状态、负责人、租约、等待/到期时间、版本和必要来源标识。通知失败另返回错误代码分类、重试次数和下次时间；不返回填写原文、消息正文、提供方错误原文或内部复核备注。

## 2026-07-20：研究运营处置工作项

### `GET /api/research/work-items/<id>`

权限与对象范围同研究队列。返回统一工作项、只读来源标识、内部/处理备注和动作轨迹；不复制原始参与者内容。风险复核和隐私申请继续受各自督导/管理员权限约束。

### `POST /api/research/work-items/<id>/actions`

需要`Idempotency-Key`、`action`和`expected_version`。状态动作包括`claim/renew/return/transfer/start_processing/wait/complete/close/reopen`，说明和消息动作为`add_note/send_participant_message`，通知动作为`retry_notification/recover_notification`。领取与更新使用乐观锁；版本过期返回`work_item_conflict`，有效租约被他人占用返回`work_item_claimed`，重复幂等请求不重复写备注或消息。

研究者只能处理获授权且已分配参与者；风险复核、隐私申请、转交、关闭、重新打开和通知恢复需要督导/管理员。参与者消息写入`messages`，内部备注写入`research_work_item_notes`，原始来源表保持只读。高风险消息由普通研究者发送时返回`message_requires_supervisor_review`。

生产环境写操作由`RESEARCH_OPERATIONS_WRITE_ENABLED=0`默认阻断；本地/测试默认开启，也可显式设为0回滚到只读队列。临时展示越权只覆盖既有展示读取，不覆盖本接口写操作，也不能作为权限验收依据。

### `GET /api/research/work-items/metrics`

参数`window_days`为1至90。返回角色范围内各状态数量、超时、租约过期、关闭原因、动作量和每日新增/关闭趋势。接口明确声明这些数据只用于排班和可靠性观察，不用于评价心理支持质量或参与者好坏。

## 2026-07-20：受控AI合成研究沙盒

`GET /api/ai-qa/config`公开返回“参与者未开放”、fake provider、沙盒是否停用和未决治理状态，不返回停用原因、操作者、密钥或内部提示。小程序只接入这一状态接口，没有参与者问答、创建会话或发送消息方法。

| 接口 | 权限与用途 |
|---|---|
| `GET/POST /api/ai-qa/sessions` | researcher/admin只列出或新建自己的明确合成会话 |
| `GET/DELETE /api/ai-qa/sessions/<id>` | 会话本人读取；删除移除消息与评价原文，重复删除幂等 |
| `POST /api/ai-qa/sessions/<id>/messages` | 会话本人提交合成文本；前检、批准内容检索、fake provider、后检和安全降级 |
| `POST /api/ai-qa/messages/<id>/feedback` | 回答所属研究者纠错；不能通过评价取得研究/训练授权 |
| `POST /api/ai-qa/evaluation/run` | researcher/supervisor/admin运行固定合成安全集 |
| `GET /api/ai-qa/review/evidence` | researcher只看自己的证据，supervisor/admin看内部全量；不返回原始提示词 |
| `POST /api/ai-qa/evaluation/<id>/reviews` | supervisor/admin登记内部复核证据，不改变参与者开关 |
| `POST /api/ai-qa/kill-switch` | admin只允许停用；接口拒绝重新开启 |

回答只检索T27中`published`且存在`active`发布包的训练卡、课程、FAQ和边界文本，并携带内容ID、版本ID、发布ID、哈希和治理状态。高风险、诊断/药物/治疗越界、隐私索取、提示注入和写工具请求不调用普通生成；来源不足明确“不知道”。限流、预算、超时、三次失败熔断、HMAC审计和`AI_QA_ENABLED=0`由服务端控制。临时展示越权不改变这些API角色或对象权限，也不能作为正式验收证据。

## 2026-07-20：离线情感与网络算法基准

全部接口位于`/api/research/benchmarks`，仅供内部离线研究。参与者角色无权访问；小程序只读取配置状态，不提供运行、同步、标注或复核方法。所有运行均固定`production_replacement_allowed=false`和`raw_text_included=false`。

| 接口 | 权限与用途 |
|---|---|
| `GET /config` | researcher/supervisor/admin读取运行、外部接入、生产替换和人工标注门禁 |
| `POST /dataset-cards/sync` | admin将本地登记清单同步到数据库；不下载外部数据 |
| `GET /dataset-cards` | researcher/supervisor/admin查看来源、版本、许可、内容权利、敏感性、用途、哈希与删除方式 |
| `GET /cases` | researcher/supervisor/admin分页读取240条合成案例；不返回生成标签 |
| `POST /cases/<id>/annotations` | 保存本人盲标；效价范围-1至1，唤醒范围0至1 |
| `GET /agreement` | supervisor/admin查看双人完整案例数、Cohen kappa和连续值差异；不自动发布人工金标准 |
| `POST /runs/affect` | 运行词典覆盖率、宏F1、混淆矩阵、校准、亚组和失败案例基准 |
| `POST /runs/network` | 运行合成图边权、中心性、社区阈值、扰动稳定性和复杂度检查 |
| `GET /runs` | researcher仅看本人运行；supervisor/admin看全量工程证据 |
| `POST /runs/<id>/reviews` | supervisor/admin登记工程复核决定和证据路径；不构成发布批准 |
| `POST /disable` | admin只允许停用；不存在远程重新开启接口 |

`GoEmotions`、SNAP目录和NetworkX Zachary当前仅登记公开链接与待人工审查状态，本地路径和工件哈希必须为空；未完成许可、平台条款、内容权利和隐私审查前不得下载或训练。生成标签只用于确定性工程回归，不是双人盲标金标准；真实参与者记录如未来进入研究，必须另行取得授权、脱敏、伦理批准并接入可删除数据链路。

## 2026-07-20：研究方法冻结前证据接口

全部接口位于`/api/research/methodology`。它们不查询参与者真实结局表，不存在签字、正式冻结、验证性分析或重新开启端点。

| 接口 | 权限与用途 |
|---|---|
| `GET /public-status` | 公开读取非敏感草案/关闭状态；不返回内部阻断详情或停用原因 |
| `GET /config` | researcher/supervisor/admin读取版本、测量数、未决项数和运行门禁 |
| `GET /registry` | researcher/supervisor/admin读取问题、测量、指标、缺失、纵向、分析与报告规范结构 |
| `GET /versions` | 内部角色读取不可变注册表版本和哈希 |
| `POST /versions/sync` | admin同步当前内容版本；同版本哈希变化返回409，必须新版本 |
| `POST /checks/run` | 内部角色运行33项登记、九点/五点分离、指标和冻结门禁检查 |
| `POST /simulations/run` | 内部角色运行固定种子纯合成可行性/敏感性检查，不报告功效 |
| `GET /evidence` | 内部角色读取最近机器检查、合成仿真和待签字包 |
| `POST /evidence-packages` | supervisor/admin在检查和仿真通过后生成`draft_for_human_signature`包 |
| `POST /disable` | admin只允许停用；不存在API重新开启 |

稳定错误包括`methodology_content_invalid`、`methodology_workbench_disabled/killed`、`methodology_version_missing/immutable`、`methodology_evidence_incomplete/failed`和`disable_reason_invalid`。小程序只调用`public-status`；内部能力只在Web研究后台提供。临时展示越权不改变后端角色矩阵。

## 2026-07-20：安全、隐私与滥用防护接口

机器契约版本为`2026-07-20.3`，当前共186个操作；`content/security_privacy_abuse_registry.json`必须由该契约生成，不允许手工维护第二套权限矩阵。

| 接口 | 权限与用途 |
|---|---|
| `GET /api/security/public-status` | 公开返回工程状态、正式权限是否通过及展示例外是否阻断；不返回资产、威胁、事件或扫描详情 |
| `GET /api/security/workbench` | researcher/supervisor/admin读取脱敏注册表、扫描摘要、安全事件和删除证明 |
| `POST /api/security/scans` | admin运行本地静态脱敏扫描；不返回密钥值，不推断生产批准 |
| `PATCH /api/security/accounts/<user_id>/status` | admin停用/恢复账号；禁止自停用，支持`expected_auth_epoch`并使旧令牌失效 |
| `POST /api/security/events/<event_id>/resolve` | admin处置安全事件；仅保存结构化状态和最小元数据 |
| `GET /api/privacy/admin/requests/<request_id>/verification` | 已有隐私管理角色读取事务删除核验证明；不返回主体HMAC |

所有API响应增加`X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、`Referrer-Policy`和`Permissions-Policy`；`/api/*`增加`Cache-Control: no-store`。CSV字符串若在可选空白后以`= + - @ TAB CR`开头，服务端以前置单引号阻止表格公式执行。临时展示越权不适用于正式权限验收，也不放宽上述写接口。

## 2026-07-21：体验与无障碍治理接口

| 接口 | 权限与用途 |
|---|---|
| `GET /api/ux-governance/public-status` | 公开返回页面覆盖数、自动门禁概况和外部门禁待补状态；不返回页面矩阵或内部证据 |
| `GET /api/ux-governance/registry` | researcher/supervisor/admin读取页面、状态、角色、敏感性和设计模式注册表 |
| `GET /api/ux-governance/workbench` | researcher/supervisor/admin读取最近自动检查和待人工证据包 |
| `POST /api/ux-governance/audits` | admin登记固定八类自动检查；拒绝额外字段和参与者原文 |
| `POST /api/ux-governance/evidence-packages` | supervisor/admin生成`draft_for_human_ux_review`包；不提供签字或批准动作 |

目标、情绪日记、人工支持、练习打卡、普通测评、学生画像和家长测评写入支持`Idempotency-Key`或`client_submission_id`。相同内容重试返回200及原记录，不同内容复用同一标识返回`idempotency_conflict`（409）；首次创建仍返回201。小程序只接入公开体验状态，不暴露内部登记接口。

## 2026-07-21：内容、数据与模型运营治理接口

机器契约版本为`2026-07-21.2`，共222个操作。T34新增17个操作，全部位于`/api/operations-governance`。

| 接口 | 权限与用途 |
|---|---|
| `GET /public-status` | 公开返回最小工程状态与生产未批准状态，不返回能力清单、制品或事件 |
| `GET /registry`、`GET /workbench` | researcher/supervisor/admin读取能力、卡片、发布、监控、事件和门禁摘要 |
| `POST /packages`、`GET /packages/<id>` | 内部角色创建新版本发布包或读取已脱敏详情；API不返回`bundle_b64` |
| `POST /packages/<id>/replay`、`/submit`、`/reviews`、`/approvals` | 运行固定合成回放并执行独立送审、审核和领域批准 |
| `POST /packages/<id>/release`、`/<action>` | admin执行本地合成发布或暂停/恢复/停用/退役；生产开关当前硬阻断 |
| `POST /runtime/rollback` | admin校验旧包哈希后原子恢复旧包和运行指针 |
| `POST /monitoring/snapshots` | 内部角色保存七类聚合指标；拒绝参与者文本，只触发人工复核 |
| `POST /incidents`、`/<id>/postmortem` | 内部角色报告结构化严重事件；supervisor/admin登记复盘，不自动恢复能力 |
| `POST /incidents/<id>/notifications/<notification_id>/<action>` | admin登记通知已投递或失败重试；不自动向外部发送敏感内容 |
| `POST /evidence-packages` | supervisor/admin生成外部门禁草稿；不存在签字、批准或上线动作 |

高风险包要求提出者、独立审核者、研究/心理/安全批准人和发布执行人分离；同一人不得跨领域批准。发布包版本唯一，清单或制品哈希被篡改返回409；高严重度回归阻断送审和发布。生产发布开关当前强制false，临时展示越权不改变这些权限和门禁。

## T36-F13 研究者在线分析任务接口

- `POST /api/research/analysis/snapshots`：按正式对象范围和最新研究授权创建引用型快照；只接受来源类型、ID、版本和SHA256。
- `POST /api/research/analysis/jobs`：必须提供`Idempotency-Key`，只接受快照ID、分析/资源版本和最小聚合参数；拒绝原文、prompt、正文和诊断标签。
- `GET /api/research/analysis/jobs`、`GET /api/research/analysis/jobs/{id}`：研究者/督导/管理员按对象范围读取任务状态、事件和影子结果。
- `POST /api/research/analysis/jobs/{id}/cancel`：创建者或管理员取消等待/失败/运行任务。
- `POST .../{id}/claim|complete|fail|recover|suspend`：admin/受控执行器路径，执行租约、指数退避、死信、人工恢复和模型停用冻结。
- `GET /api/research/analysis/artifacts/{id}`：只返回覆盖率、未知率、样本量、质量状态、聚合结果和非诊断边界。
- `DELETE /api/research/analysis/artifacts/{id}`：admin受控删除派生结果，保留删除原因、时间和审计；不删除来源业务数据。

状态为`queued/running/succeeded/failed/canceled/expired/suspended`。授权撤回或快照过期会同步冻结任务/结果。临时展示越权只允许既有只读展示，不开放创建、执行、恢复或删除权限。

## 2026-07-21 T23完整主旅程补充接口

- `POST /api/feedback-ledger/<entry_id>/actions`：参与者本人撤回或纠错评价；必须提供幂等键，纠错生成新版本，撤回保留历史，跨用户返回403/404边界。
- `POST /api/training-plan/recommendations/replay`：参与者本人按`feedback_adaptive_v2`或`legacy_rule_order_v1`回放自己的测评推荐并生成快照；必须提供测评结果ID和幂等键。
- `GET /api/training-plan/recommendation-snapshots/<snapshot_id>`：参与者本人读取自己的推荐回放；不向其他参与者或研究者暴露。
- `GET /api/journey/today`兼容新增`state_contract`和`controlled_capabilities`，明确加载、失败、弱网恢复及治疗性评估未开放状态。
- `POST /api/product-events`兼容新增今日行动展示/点击/完成/跳过/恢复、不适和人工升级事件；只接收白名单枚举元数据，可使用`client_event_id`防重复，不接收参与者原文。

以上接口不构成诊断、治疗安排或疗效证明；临时展示越权不能替代服务端对象权限验收。
## 2026-07-22：任务36 F03研究权限API

正式权限使用 `content/researcher_capability_registry.json`，前端显示不具有授权效力。新增接口：

- `GET /api/research/access/capabilities`：返回矩阵版本、正式/有效角色、开发例外状态和能力ID；
- `GET /api/research/access/assignments`：admin查看全部，researcher/supervisor仅查看自己的分配；
- `POST /api/research/access/assignments`：admin-only，必须提供`Idempotency-Key`；
- `PATCH /api/research/access/assignments/{id}`：admin-only，使用`expected_version`撤销或转交；必须提供`Idempotency-Key`，相同键和载荷重放第一次结果，不同载荷复用同一键返回409；
- `POST /api/research/access/enrollments/{id}/claim`：researcher领取活动且未分配报名，必须提供`Idempotency-Key`。

正式对象范围为researcher=明确分配、supervisor=监督分配、admin=全部。拒绝包络为`403 forbidden`，`error.details.required_capability`只说明所需能力，不返回敏感对象内容；顶层始终带`request_id`。临时`researcher_platform_full_access`仍只用于既有精确开发路径，不能授权导出、账号、安全或生产操作。

## 2026-07-22：任务36 F04研究者移动工作台契约

小程序研究者移动工作台复用既有接口，不新增移动端专属高权限聚合接口：

- 首页通过`GET /api/research/operations`读取脱敏数量，通过五类`GET /api/research/queues`读取不含原文的优先级摘要；任一队列失败时保留其他结果并显示对应`request_id`。
- “参与者”通过`GET /api/research/participants?q=&page=&page_size=`进行350毫秒防抖搜索和稳定分页；列表只返回昵称/用户ID及模块数量，详情仍需服务端对象范围复核。
- “试点项目”继续使用`/api/relationship-pilot/researcher/dashboard`及单报名详情接口；移动导航可见不等于深链授权成功。
- 加载失败只在界面显示`request_id`；复制诊断可包含客户端、服务和构建版本，但不包含token、请求/响应正文或参与者文本。

数据库不新增表/列，继续复用`research_work_items`、`relationship_pilot_enrollments`、`messages`和`audit_logs`。回滚可恢复原单页WXML/WXSS/JS及旧`limit`调用；新增分页返回字段为兼容性追加，无需回滚数据。临时展示全权限仍显示显著警告且不能作为正式角色验收证据。
## T36-F05 参与者档案按需读取（2026-07-22）

- `GET /api/research/participants`：最小列表，支持`q/page/page_size`，返回匿名ID、活动数量、`total/has_more`，不返回填写原文。
- `GET /api/research/participants/<user_id>`：档案摘要，返回参与者匿名信息、最近报名/分配状态、十个模块目录和数量，不返回各模块长文本。
- `GET /api/research/participants/<user_id>/modules/<module_key>`：单模块分页。`module_key`为`assessments/measurements/diaries/training/stage_reports/relationship_pilot/project_tests/messages/human_support/timeline`；支持`page/page_size/date_from/date_to/type/status/batch`。
- 三个接口都执行角色、研究授权和对象范围校验；敏感模块查看写审计。错误仍使用统一包络和`request_id`。
# T36-F06 研究反馈与消息交付（2026-07-24）

研究者、督导和管理员在正式对象范围内，通过同一组接口完成“草稿 → 预览 → 确认 → 发送”。临时展示全权限不扩大这些写接口的正式权限。

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/research/deliveries?enrollment_id=...` | 按报名读取交付历史，支持分页 |
| `POST` | `/api/research/deliveries` | 创建阶段性反馈或参与者消息草稿 |
| `GET` | `/api/research/deliveries/{id}` | 读取草稿、当前不可变版本、事件和发送回执 |
| `PATCH` | `/api/research/deliveries/{id}` | 保存草稿；必须提交 `expected_version` |
| `POST` | `/api/research/deliveries/{id}/preview` | 生成不可变预览版本并执行风险检查 |
| `POST` | `/api/research/deliveries/{id}/confirm` | 确认当前预览版本 |
| `POST` | `/api/research/deliveries/{id}/send` | 幂等发送消息；阶段性反馈同时生成报告版本 |
| `POST` | `/api/research/deliveries/{id}/withdraw` | 撤回显示状态但保留消息、报告、版本和审计历史 |

所有写请求必须提供 `Idempotency-Key`。状态冲突、重复键冲突和过期版本统一返回 `409`；报名停用或分配被撤销后不可继续交付。参与者消息增加 `delivery_id`、`delivery_version`、`withdrawn_at` 和 `is_withdrawn`。
## 任务36 F14：受控在线情感与网络分析

- `GET /api/research/analysis/catalog`：研究者、督导和管理员读取版本化管线目录。返回资源 SHA256、最小样本、图规模上限、数据模式和外部门禁状态。
- `POST /api/research/analysis/jobs/{job_id}/execute-synthetic`：仅管理员执行项目自有合成基准。任务必须引用 `synthetic_fixture`，版本与资源指纹必须和目录一致。
- `GET /api/research/analysis/jobs`：除任务字段外，成功任务会附带 researcher-only 工件及覆盖率、未知率、样本量和质量状态。
- 当前 `real_participant_processing_enabled=false`、`production_training_enabled=false`；T35 人工门禁未签前，真实参与者来源固定返回 `real_participant_analysis_blocked`。
- 小样本不返回类别分布或图节点/边；家庭拓扑不推断关系质量、潜意识或家庭病理。
### T36-F17 可靠性与安全统一响应补充

- `GET /api/reliability/workbench` 新增 `task36_integration`：只返回六条关键链路的引擎、幂等、并发、重试、死信、恢复、对象范围和删除范围等元数据。
- `GET /api/security/workbench` 同步返回相同的 `task36_integration`，用于核对生产默认关闭、外部门禁和敏感证据禁入规则。
- `GET /api/research/analysis/catalog` 新增 `resilience_summary`：在线分析的幂等、租约并发、失败恢复和派生删除摘要。
- 以上响应不包含参与者原文、手机号、OpenID、token、密码、Cookie、请求/响应正文或内部堆栈；也不代表生产批准。
### T36-F15 AI问答补充

- AI问答会话接口允许 `researcher/supervisor/admin`，但只能访问本人创建的合成会话；参与者仍返回403。
- `GET /api/ai-qa/config` 新增 `provider_policy` 与保留策略：批准供应商仅fake，外部供应商关闭，返回超时、重试、熔断、预算和合成保留天数。
- 成功回答新增 `uncertainty`，引用仍携带内容/发布版本和hash；回答不能写入正式参与者反馈。
- `POST /api/ai-qa/retention/purge` 仅管理员可用；默认dry-run，实际清理必须提交 `dry_run=false` 和 `confirm_synthetic_purge=true`，且只清理过期合成沙盒内容。
## 任务36 F16：治疗性评估协作接口

统一前缀：`/api/therapeutic-assessment`。所有接口需要登录，所有写接口需要`Idempotency-Key`。

- `GET/POST /cases`：按角色对象范围读取或由参与者创建协作问题。
- `GET /cases/<id>`、`PATCH /cases/<id>/scope`：读取详情、按`expected_version`修改共享范围。
- `POST /cases/<id>/disagree|withdraw`：参与者表达不同意见或撤回。
- `POST /cases/<id>/assign|readiness`：督导/管理员分配对象并登记人工资格、督导、伦理证据引用。
- `POST /cases/<id>/feedback-versions`：正式研究角色保存结构化人工或AI草稿。
- `POST /feedback-versions/<id>/review|send`：督导/管理员人工复核和发送；L0/L1、高风险、撤回或复杂范围被服务端阻断。
- `POST /cases/<id>/actions`、`PATCH /actions/<id>`：参与者选择、完成或拒绝下一小步并保存随访。

参与者永远看不到草稿；成长数据不返回疗效分数。临时展示权限不参与这些写操作的正式鉴权。

### T38-F01服务级别补充

- `GET /api/therapeutic-assessment/service-levels`：登录用户读取L0—L3版本化名称、范围、人工/督导要求和当前生产上限。
- `GET /cases`与`GET /cases/{id}`的每条case新增`service_level`，与`readiness_level`一致，包含`display_name`、`formal_ta`和所需证据类型。
- 当前默认及无人工责任链生产上限为L0；返回L1—L3定义不表示相关服务已经批准开放。

## 2026-07-27：T37-P04计算任务Harness

统一前缀：`/api/reliability/computation-harness`。读取指标需要researcher、supervisor或admin；任务写操作和worker心跳仅admin。临时展示越权不扩展这些接口。

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/jobs` | 按能力、来源引用和幂等键创建元数据任务；不接受原文、身份或凭据 |
| `POST` | `/jobs/{id}/cancel` | 取消尚未终结的任务 |
| `POST` | `/jobs/{id}/freeze` | 使用受控原因冻结任务并释放租约 |
| `POST` | `/jobs/{id}/resume` | 使用受控原因恢复冻结任务 |
| `POST` | `/heartbeat` | 记录哈希化worker引用、容量和活动任务数 |
| `GET` | `/metrics` | 返回吞吐、排队时长、失败率、覆盖率、弃答率、成本和人工积压 |
| `GET` | `/error-categories` | 返回用户、数据、模型、供应商和权限五类错误契约 |

情感计算、社会网络分析和参与者AI具有独立默认关闭开关。工程接口完成不表示生产任务执行或真实模型发布已批准。

## 2026-07-27：T38-F02三轨状态转换

- `POST /api/therapeutic-assessment/cases/<case_id>/transitions`
- 请求头必须携带`Idempotency-Key`；请求体仅允许`track`、`target_state`、`expected_version`、`reason_code`。
- `track`为`workflow`、`hypothesis`或`safety`；合法边和原因码以`content/therapeutic_assessment_state_machine.json`为准。
- 接口校验登录、对象范围、角色、当前状态和版本。非法跳转、旧版本或终态写入返回409，权限不足返回403。
- 相同操作者、幂等键、case和转换会返回已完成结果；幂等键被其它操作占用时返回409。

## 2026-07-27：T38-F03证据账本

- `GET/POST /api/therapeutic-assessment/cases/<case_id>/evidence`：按对象范围读取或创建O/P/H/U证据项。
- `POST /api/therapeutic-assessment/evidence/<evidence_id>/review`：仅督导/管理员复核H，要求版本和幂等键。
- 参与者只能写O/U；AI/系统来源不能写H；参与者读取时过滤未人工复核H和未授权可见范围。

## 2026-07-27：T38-F04问题版本

- `PATCH /api/therapeutic-assessment/cases/<case_id>/question`：参与者本人执行生成候选、改写、选择、都不符合、暂停、删除或提交。
- 必须携带`expected_version`和`Idempotency-Key`；原始`assessment_question`不可覆盖。
- 响应返回`working_question`、`question_candidates`、`question_quality`、`best_guess`、状态和版本。

## 2026-07-27：T38-F05动态同意

- `POST /api/therapeutic-assessment/cases/<case_id>/data-items`：创建不含原文的资料控制记录。
- `GET /api/therapeutic-assessment/data-items/<item_id>`：仅控制者、提供者、逐条指定专业人员或全部确认后的共同查看者可读。
- `PATCH /api/therapeutic-assessment/data-items/<item_id>/consent`：主体/涉及者批准、修改或撤回；要求版本和幂等键。
- 过期返回410，撤回返回403；法定保留不恢复查看权。

## 2026-07-27：T38-F06参与者草稿

- `GET /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id>`：参与者读取本人指定步骤的云端草稿；不存在时返回`version=0`。
- `PUT /api/therapeutic-assessment/cases/<case_id>/participant-drafts/<step_id>`：按`expected_version`、`Idempotency-Key`保存或完成草稿。
- step限定为八个流程标识；跨参与者读取返回403，版本冲突返回409，已撤回case禁止继续同步。

## 2026-07-27：T38-F07人工安全责任链

- `GET /api/therapeutic-assessment/safety/status`：返回普通流程是否可用及当前用户对象范围内的“需要真人了解”数量；参与者不返回内部暂停原因。
- `PUT /api/therapeutic-assessment/cases/<case_id>/responsibility-chain`：仅督导/管理员按版本配置责任人、督导、支持通道、证据和队列时限。
- `POST /api/therapeutic-assessment/cases/<case_id>/safety-signals`：参与者本人或对象范围内专业人员记录安全信号；只形成真人了解队列，不向参与者输出风险等级。
- `POST /api/therapeutic-assessment/safety-events/<event_id>/resolve`：仅督导/管理员提交人工处置证据后解除单个事件。
- `POST /api/therapeutic-assessment/safety/runtime/restore`：全部开放事件已解除后，由督导/管理员提交恢复证据恢复普通流程。
- 安全事件、责任链中断或队列超时会在服务端阻断普通反馈、发送和训练行动；临时展示越权不能解除安全门。

## 2026-07-27：T38-F08研究者证据工作台

- `GET /api/therapeutic-assessment/cases/<case_id>/researcher-workbench`：仅对象范围内研究者、督导或管理员读取；支持`kind`、`review_status`、`visibility`、`page`和`page_size`。
- `PUT /api/therapeutic-assessment/cases/<case_id>/researcher-workbench/draft`：保存内部记录、参与者可见草稿和筛选状态；必须携带`expected_version`和`Idempotency-Key`。
- 工作台读取会写敏感访问审计；草稿保存使用case、操作者、版本和幂等键防止重复与覆盖。
- 参与者读取case时不返回内部记录、内部讨论或未发送草稿；正式反馈仍走独立起草与复核接口。
## 2026-07-27 T38-F09反馈生命周期API

- `POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/responses`：参与者提交“像/部分像/不像/需要想想”。
- `POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/revise`：研究者基于核对意见创建新版本，不覆盖原版本。
- `POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/withdraw`：有权限人员撤回反馈并保留历史。
- `POST /api/therapeutic-assessment/feedback-versions/<feedback_id>/resend`：督导或管理员新增一次发送记录。
- 新增接口均要求登录；写操作要求`Idempotency-Key`。对象范围、人工复核、授权资料和生命周期状态由服务端校验。

## 2026-07-28：T38-F10行动与T38-F11任务授权API

- `POST /api/therapeutic-assessment/cases/<case_id>/actions`、`PATCH /actions/<action_id>`与`POST /actions/<action_id>/followups`：参与者本人创建、更新和回看自选小行动，随访只形成O/U线索。
- `GET /api/therapeutic-assessment/competency/authorizations`：本人查看自己的任务授权；督导/管理员可按`user_id`查看。
- `POST /api/therapeutic-assessment/competency/authorizations`：督导/管理员按级别、任务、范围、督导证据和有效期授予任务权限。
- `PATCH /api/therapeutic-assessment/competency/authorizations/<authorization_id>/revoke`：按版本和原因撤销授权。
- `GET /api/therapeutic-assessment/competency/effective?case_id=...&task_code=...`：按当前账号、case、任务、T级别、范围和有效期返回是否可写。
- 工作台草稿、O/P/H证据、反馈起草、复核、发送、修订、撤回和重发均在服务端重新校验任务授权；普通账号的临时展示越权不会改变正式写权限。

## 2026-07-28：T37-B04反馈生命周期API

- `GET /api/therapeutic-assessment/cases/<case_id>/lifecycle`：参与者本人或对象范围内正式研究角色读取一个case的状态、反馈版本、交付回执、核对、小行动、事件、恢复状态及三类质量指标。
- `GET /api/therapeutic-assessment/lifecycle/metrics`：正式研究角色读取对象范围内汇总；普通参与者返回403，researcher只统计分配给自己的case。
- `THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED=0`时case接口返回关闭状态和核心链路清单；不会关闭目标、日记、训练卡、打卡、周报或消息接口。
- 指标明确分为`process_quality`、`implementation_quality`和`harm_incidents`，不返回疗效、诊断、关系质量或个体风险分数。

## 2026-07-28：T37-B05协作式评估生产门禁API

- `GET /api/therapeutic-assessment/production-gate`：正式研究角色读取五类门禁、缺失项和最近运行；普通参与者返回403。
- `POST /api/therapeutic-assessment/production-gate/evaluate`：督导或管理员按当前注册表和正式证据生成门禁运行快照，需要`Idempotency-Key`。
- `GET/POST /api/therapeutic-assessment/production-gate/evidence`：正式研究角色读取或登记证据；登记后状态始终为`pending`，客户端不能自报通过。
- `POST /api/therapeutic-assessment/production-gate/evidence/<evidence_id>/verify`：督导或管理员按版本核验或拒绝证据；记录人不能核验自己的材料。
- 只有`production`环境、64位SHA-256且记录人与核验人不同的`verified`材料才可计入正式门禁。接口始终返回`production_release_approved=false`，不执行发布。
## 2026-07-28：T37-C01 AI用例冻结

- `GET /api/ai-qa/use-cases`：公开返回版本、当前阶段、5个允许用例、7类禁止用例、参与者入口阶段和边界说明；不返回内部提示模板、密钥或供应商配置。
- `GET /api/ai-qa/config`：新增`use_case_policy`，与用例目录使用同一版本。
- `POST /api/ai-qa/sessions`：除合成标记外必须提交允许的`use_case_id`；参与者角色仍返回403。
- `POST /api/ai-qa/sessions/<id>/messages`：若提交的`use_case_id`与会话不同则返回`ai_qa_use_case_mismatch`；旧无范围会话不能继续执行。

### T37-C02 AI供应商遴选和合同证据

- `GET /api/ai-qa/providers`：`researcher/supervisor/admin`查看DeepSeek、OpenAI公开材料比较、待补证据、出网状态和故障/涨价/停服/迁移预案。公开材料不计作合同批准，接口不返回密钥值。
- `GET /api/ai-qa/providers/evidence`：正式研究角色只读取证据元数据、哈希与复核状态，不返回合同正文。
- `POST /api/ai-qa/providers/evidence`：仅`supervisor/admin`登记脱敏证据引用和SHA-256；要求`Idempotency-Key`，新证据固定为`pending`。
- `POST /api/ai-qa/providers/evidence/<id>/verify`：仅`supervisor/admin`独立复核，登记人与复核人必须不同，并使用`expected_version`防止并发覆盖。
- `GET /api/ai-qa/config`仅增加候选ID和门禁摘要；`selected_provider=null`、`external_provider_enabled=false`。真实适配器、出网白名单和密钥管理属于T37-C03，当前未开启。
- 当前只开放研究者、督导和管理员的合成沙盒。参与者自由问答、自动训练卡处方、自动发布和写工具仍关闭。

### T37-C03 真实Provider适配器与密钥管理

- DeepSeek与OpenAI均通过服务端OpenAI兼容适配器接入；供应商只能由`AI_QA_PROVIDER`选择，消息接口提交`provider`会返回`ai_qa_provider_override_forbidden`。
- 真实调用同时要求`AI_QA_REAL_PROVIDER_ENABLED=1`、C02供应商已选中、12类证据齐全且独立复核、外部供应商与出网白名单已开启。任一条件不满足时失败关闭。
- 密钥只从CloudBase Secret或服务端环境变量`DEEPSEEK_API_KEY`、`OPENAI_API_KEY`读取；模型分别由`DEEPSEEK_MODEL`、`OPENAI_MODEL`指定。接口、前端、数据库和日志均不返回密钥值。
- 传输层只允许固定HTTPS主机，分别执行`AI_QA_CONNECT_TIMEOUT_MS`、`AI_QA_READ_TIMEOUT_MS`和`AI_QA_TIMEOUT_MS`；超时或取消会关闭当前连接，内部不启动后台供应商线程。
- 供应商事件只记录request id、模型版本、输入/输出token、总token、估算成本、币种、时延、状态和错误代码，不记录请求或回答原文。
- `GET /api/ai-qa/config`只返回适配器候选、门禁状态、三类超时和密钥来源类型；`secret_values_exposed=false`。

### T37-C04 批准知识库与RAG

- `GET /api/ai-qa/knowledge`：研究者、督导和管理员读取已索引文档、切片数量及网页隔离候选的元数据；不返回候选网页正文。
- `POST /api/ai-qa/knowledge/rebuild`：仅督导和管理员可从内容治理库重建索引。只有权利状态为`owned/licensed/public_domain/permission_recorded`、四类审核均通过、发布版本和发布记录均有效且未过期的内容可进入索引。
- `GET /api/ai-qa/knowledge/retrieve`：内部角色使用`query`、`method=bm25|vector|hybrid`和`audience`比较检索。每条引用返回文档版本、发布版本、切片ID、字段位置、来源、权利、审核、有效期和分项分数。
- `POST /api/ai-qa/knowledge/candidates`：仅督导和管理员登记HTTPS网页的标题、URL和SHA-256元数据；必须提供`Idempotency-Key`。接口拒绝正文、HTML和原始文本字段，候选固定进入`quarantined`且`indexed=false`。
- `POST /api/ai-qa/knowledge/evaluation/run`：内部角色运行固定合成检索案例，记录召回率、引用正确率、无证据正确率和案例通过率；工程阈值通过不等于发布批准。
- 任何检索都会先同步发布状态；材料暂停、撤回、替换或过期后立即不再返回。无足够证据时`citations=[]`且`evidence_status=insufficient`。
