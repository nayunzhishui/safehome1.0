# API 接口文档

最后更新时间：2026-06-04

本文档记录 `safehome1.0 / 安心陪伴 / ReadFeedback` MVP 1.0 当前已经实现的 Flask + SQLite 后端 API。本文档以当前后端真实行为为准，用于小程序端与网页端并行联调。

进度口径：真实可调用接口以前文已实现章节为准；第 10 节“0版网页评估画像整合”已有基础画像、风险检查、模型信息、画像历史、人工复核、周报画像趋势、`type=profile` 脱敏导出、`type=records` 统一研究导出和高风险导出二次确认。当前总进度见 `docs/项目进度统一口径.md`。

阅读方式：先看“通用约定”和对应接口章节；若与历史日志冲突，以本文开头进度口径和 `docs/项目进度统一口径.md` 为准。

## 通用约定

- 后端地址：本地开发默认 `http://127.0.0.1:5000`
- API 基础路径：`/api`
- 请求格式：`application/json`
- JSON 响应格式：统一包裹在 `ok` 和 `data` 中。
- CSV 导出接口返回 `text/csv; charset=utf-8`。
- 时间字段：后端当前使用 ISO 8601 字符串。
- CORS 来源白名单由 `ALLOWED_ORIGINS` 环境变量配置；开发默认允许 `http://127.0.0.1:5173` 和 `http://localhost:5173`。
- 当前没有完整登录鉴权；开发环境未传 `user_id` 时，写入和查询接口可使用默认测试用户 `demo-parent`。
- 当 `APP_ENV=production` 时，目标、情绪记录、反馈、画像、打卡、督导、测评结果等写入接口必须传匿名 `user_id`，例如 `parent_xxx`、`student_xxx`、`tester_xxx`，否则返回 `validation_error`。
- 当 `APP_ENV=production` 时，目标、情绪记录、打卡、周报和测评结果等用户查询接口也必须传匿名 `user_id`，否则返回 `validation_error`。
- 后台敏感接口必须带 `X-Admin-Token`：`/api/admin/export`、`/api/risk-review`、`/api/profile-results` 列表、`/api/profile-results/<id>/reviews`、`/api/profile-results/<id>/review`。
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
- content 必需文件是否存在。

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
| `limit` | integer | 否 | 默认 50 |

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

用途：返回小程序“测一测”中的量表和工作表列表。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `category` | string | 否 | 按分类筛选，例如 `量表类` |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `version` | string | 内容库版本 |
| `boundary_notice` | string | 统一边界提示 |
| `items` | array | 测一测条目列表 |

条目字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 工作表 ID |
| `source_file` | string | 来源 PDF 文件名 |
| `source_title` | string | 原工作表标题 |
| `display_title` | string | 小程序展示标题 |
| `category` | string | 分类 |
| `pages` | integer | PDF 页数 |
| `instructions` | string | 填写说明 |
| `question_count` | integer | 当前电子化填写项数量 |
| `is_reference` | boolean | 是否为附录示例参考 |

### `GET /api/assessments/<worksheet_id>`

用途：返回单个量表或工作表详情。

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 工作表 ID |
| `source_file` | string | 来源 PDF 文件名 |
| `source_title` | string | 原工作表标题 |
| `display_title` | string | 小程序展示标题 |
| `category` | string | 分类 |
| `pages` | integer | PDF 页数 |
| `instructions` | string | 原文或补录说明 |
| `sections` | array | 原工作表分区 |
| `questions` | array | 电子化填写项 |
| `scoring` | string | 计分说明 |
| `recommended_card_ids` | array | 建议关联训练卡 |
| `boundary_notice` | string | 统一边界提示 |

### `POST /api/assessment-results`

用途：保存用户一次测一测填写结果。

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
| `prompt` | string | 题目或填写项原文/提示 |
| `value` | string | 用户填写内容 |
| `score` | number | 可选分值 |

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
| `result_summary` | string | 支持性结果摘要 |
| `created_at` | string | 创建时间 |
| `recommended_card_ids` | array | 建议关联训练卡 |

### `GET /api/assessment-results`

用途：查询测一测历史结果。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID，缺省为 `demo-parent` |
| `limit` | integer | 否 | 默认 50 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 测一测结果列表 |

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
| `limit` | integer | 否 | 默认 50 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 打卡记录列表 |

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
