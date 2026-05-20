# API 接口文档

本文档记录 `safehome1.0 / 安心陪伴 / ReadFeedback` MVP 1.0 当前已经实现的 Flask + SQLite 后端 API。本文档以当前后端真实行为为准，用于小程序端与网页端并行联调。

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

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | string | 否 | 默认 `diaries`。支持：`goals`、`diaries`、`feedback`、`checkins`、`reports`、`supervision`、`cards` |
| `user_id` | string | 否 | 除 `cards` 外，可按用户筛选 |

响应：

- 成功时返回 `text/csv; charset=utf-8`。
- 响应头包含 `Content-Disposition: attachment; filename=safehome_{type}.csv`。
- 当前不支持 `type=all`。
- 当前不支持 `format` 参数。

## 9. 当前已知接口边界

- 当前没有认证和权限控制。
- 当前没有分页总数 `total`。
- 当前列表接口只提供简单 `limit`。
- 当前即时反馈由规则匹配生成，不代表诊断、评估或治疗建议。
- 当前 CSV 导出没有权限保护，正式试点前必须增加鉴权。
