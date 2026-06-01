# API 接口文档

本文档记录 `safehome1.0 / 安心陪伴 / ReadFeedback` MVP 1.0 当前已经实现的 Flask + SQLite 后端 API。本文档以当前后端真实行为为准，用于小程序端与网页端并行联调。

进度口径：真实可调用接口以前文已实现章节为准；第 10 节“0版网页评估画像整合”仍为后续规划。当前总进度见 `docs/项目进度统一口径.md`。

## 通用约定

- 后端地址：本地开发默认 `http://127.0.0.1:5000`
- API 基础路径：`/api`
- 请求格式：`application/json`
- JSON 响应格式：统一包裹在 `ok` 和 `data` 中。
- CSV 导出接口返回 `text/csv; charset=utf-8`。
- 时间字段：后端当前使用 ISO 8601 字符串。
- 当前没有登录鉴权，未传 `user_id` 时，多数接口会使用默认测试用户 `demo-parent`。
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

用途：确认后端是否启动。

响应示例：

```json
{
  "ok": true,
  "service": "safehome-backend"
}
```

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
| `raw_text` | string | 否 | 原始记录文本 |

说明：

- 如果传入 `diary_id`，后端会优先读取数据库中的该条情绪事件记录。
- 如果 `diary_id` 不存在，会返回 `not_found`。
- 如果没有匹配任何规则，会返回一条通用支持性反馈。

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

用途：根据本周情绪事件、反馈标签和练习打卡生成周度报告。当前实现会在每次请求时生成一条 `weekly_reports` 数据库记录。

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
| `type` | string | 否 | 默认 `diaries`。支持：`goals`、`diaries`、`feedback`、`checkins`、`assessments`、`reports`、`supervision`、`cards` |
| `user_id` | string | 否 | 除 `cards` 外，可按用户筛选 |

响应：

- 成功时返回 `text/csv; charset=utf-8`。
- 响应头包含 `Content-Disposition: attachment; filename=safehome_{type}.csv`。
- 未提供或提供错误 `X-Admin-Token` 时返回 `401 unauthorized`。
- 当前不支持 `type=all`。
- 当前不支持 `format` 参数。

本地开发调用示例：

```powershell
Invoke-WebRequest `
  -Uri "http://127.0.0.1:5000/api/admin/export?type=diaries" `
  -Headers @{ "X-Admin-Token" = "safehome-local-admin-token" } `
  -OutFile safehome_diaries.csv
```

## 9. 当前已知接口边界

- 当前没有完整登录认证和角色权限控制。
- 当前后台导出接口已增加 `X-Admin-Token` 令牌校验；正式部署前必须通过 `ADMIN_EXPORT_TOKEN` 环境变量改掉默认本地令牌。
- 当前没有分页总数 `total`。
- 当前列表接口只提供简单 `limit`。
- 当前即时反馈由规则匹配生成，不代表诊断、评估或治疗建议。

## 10. 后续规划接口：0版网页评估画像整合（未实现）

本节根据夏老师“0版网页与安心家整合”资料、8 张思维导图和 GitHub 参考项目整理，仅作为后续开发规划。当前后端尚未实现以下接口，联调时不要按已上线接口调用。

规划目标：

- 将 0版网页沉淀为安心家的“评估画像与反馈引擎”；
- 支持学生画像、置信度、维度解释、推荐任务和人工复核；
- 保持非诊断、非标签化、支持性表达；
- 为研究导出保留模型版本、规则版本和授权字段。

### `POST /api/profile`（规划）

用途：根据量表分数和自由文本生成学生支持性画像。该接口不输出临床诊断。

请求字段建议：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 学生或测试用户弱身份 ID，缺省可沿用测试用户 |
| `assessment_result_id` | string | 否 | 关联已有测一测结果 |
| `round` | integer | 否 | 第几轮测评，默认 1 |
| `scores.test_anxiety` | number | 是 | 考试焦虑相关分数 |
| `scores.iu_score` | number | 是 | 不确定性不耐受相关分数 |
| `scores.f_score` | number | 否 | 情绪调节灵活性或恐惧倾向相关分数 |
| `scores.self_compassion` | number | 是 | 自我同情/自我支持相关分数 |
| `free_text` | string | 否 | 学生日记、访谈或补充说明文本，仅作辅助线索 |

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

响应字段建议：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 画像结果 ID |
| `profile_name` | string | 画像名称，例如 `压力警觉型画像`，前端不使用“人格”字样 |
| `profile_code` | string | 画像编码，例如 `pressure_alert` |
| `confidence` | number | 画像置信度，0-1 |
| `dimensions` | object | 关键维度结果 |
| `keywords` | array | 从自由文本中提取的辅助关键词 |
| `supportive_explanation` | string | 支持性解释 |
| `suggested_task` | string | 推荐任务 ID，例如沙盘表达或情绪命名任务 |
| `recommended_card_ids` | array | 推荐训练卡 ID |
| `risk_level` | string | `low`、`medium`、`high` |
| `requires_review` | boolean | 是否需要人工复核 |
| `model_version` | string | 模型或规则版本 |
| `rules_version` | string | 画像反馈规则版本 |
| `boundary_notice` | string | 非诊断边界说明 |

响应示例：

```json
{
  "ok": true,
  "data": {
    "id": "profile_001",
    "profile_name": "压力警觉型画像",
    "profile_code": "pressure_alert",
    "confidence": 0.76,
    "dimensions": {
      "anxiety_sensitivity": "high",
      "emotion_regulation": "medium_low",
      "self_support": "developing"
    },
    "keywords": ["担心", "考不好", "失望"],
    "supportive_explanation": "你当前可能更容易捕捉到压力信号，这不代表你有问题。",
    "suggested_task": "sandplay_pressure_awareness",
    "recommended_card_ids": ["emotion_naming", "three_second_pause"],
    "risk_level": "low",
    "requires_review": false,
    "model_version": "profile-rules-v1",
    "rules_version": "2026.06-student-profile-rules-v1",
    "boundary_notice": "本结果不是临床诊断，仅用于自我理解和练习参考。"
  }
}
```

### `GET /api/profile-results`（规划）

用途：查询用户的学生画像历史结果，用于复测和轮次追踪。

查询参数建议：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 用户 ID |
| `limit` | integer | 否 | 默认 50 |

### `GET /api/profile-results/<profile_id>`（规划）

用途：查看单条画像结果详情，用于小程序结果页和网页后台详情页。

### `GET /api/model/info`（规划）

用途：返回当前画像模型或规则引擎信息，降低“黑箱感”，方便研究追溯。

响应字段建议：

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_version` | string | 模型版本 |
| `rules_version` | string | 规则版本 |
| `available_profiles` | array | 当前可输出的画像类型 |
| `last_updated` | string | 更新时间 |
| `boundary_notice` | string | 非诊断边界说明 |

### `POST /api/risk/check`（规划）

用途：检查文本中是否包含自伤、自杀、暴力、家暴、严重失眠等高风险线索。命中高风险时，不应继续生成普通自动反馈。

### 后台导出扩展（规划）

`GET /api/admin/export` 后续建议支持：

| 参数 | 类型 | 说明 |
|---|---|---|
| `type=profile` | string | 导出学生画像结果 |
| `deidentify=true` | boolean | 默认脱敏导出 |
| `format=csv/json` | string | 第一版可只做 CSV，JSON 后置 |

导出边界：

- 默认使用匿名 ID；
- 默认不导出联系方式、自由文本原文和高风险文本原文；
- 未授权或 `export_allowed=false` 的记录不得导出；
- 后续应增加导出数据字典和审计日志。
