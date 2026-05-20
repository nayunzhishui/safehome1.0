# API 接口文档

本文档定义安心陪伴 MVP 1.0 的后端 API 契约。第一版后端建议使用 Flask + SQLite 实现，所有接口统一返回 JSON。

## 通用约定

- 基础路径：`/api`
- 请求格式：`application/json`
- 响应格式：`application/json`
- 时间字段：ISO 8601 字符串，例如 `2026-05-20T14:30:00+08:00`
- 第一版可以使用测试用户 `user_id`，后续再接入登录。

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
    "code": "VALIDATION_ERROR",
    "message": "缺少必填字段"
  }
}
```

## 1. 目标设定

### `POST /api/goals`

用途：提交家长 7 天小目标。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 是 | 测试用户或家长弱身份 ID |
| `scene` | string | 是 | 高频亲子冲突场景 |
| `smart_goal` | string | 是 | 7 天 SMART 小目标 |
| `motivation` | string | 否 | 改变动机 |
| `start_date` | string | 否 | 目标开始日期 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `goal_id` | string | 目标 ID |
| `status` | string | `active` |

## 2. 情绪事件记录

### `POST /api/diaries`

用途：提交一次亲子互动或情绪事件记录。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 是 | 用户 ID |
| `goal_id` | string | 否 | 关联目标 ID |
| `event_time` | string | 否 | 事件发生时间 |
| `scene` | string | 是 | 冲突或互动场景 |
| `event_description` | string | 是 | 具体事件 |
| `parent_emotion` | string | 是 | 家长主要情绪 |
| `parent_emotion_intensity` | integer | 是 | 家长情绪强度，1-10 |
| `child_emotion` | string | 否 | 孩子主要情绪 |
| `child_emotion_intensity` | integer | 否 | 孩子情绪强度，1-10 |
| `automatic_thought` | string | 否 | 家长自动想法 |
| `body_sensation` | string | 否 | 身体感觉 |
| `behavior` | string | 否 | 当时行为或回应 |
| `raw_text` | string | 否 | 原始记录文本 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `diary_id` | string | 情绪事件记录 ID |
| `created_at` | string | 创建时间 |

### `GET /api/diaries`

用途：查询情绪事件记录。网页后台使用。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 否 | 按用户筛选 |
| `limit` | integer | 否 | 默认 50 |
| `offset` | integer | 否 | 默认 0 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 记录列表 |
| `total` | integer | 总数 |

## 3. 即时反馈

### `POST /api/feedback/generate`

用途：基于情绪事件记录生成非诊断反馈。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `diary_id` | string | 否 | 已保存记录 ID |
| `event_description` | string | 否 | 事件描述，未保存时可直接传入 |
| `automatic_thought` | string | 否 | 自动想法 |
| `behavior` | string | 否 | 当时行为 |
| `raw_text` | string | 否 | 原始记录文本 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `feedback_id` | string | 反馈 ID |
| `tags` | array | 识别标签 |
| `trigger_summary` | string | 触发点摘要 |
| `pattern_summary` | string | 互动模式解释 |
| `supportive_feedback` | string | 支持性反馈 |
| `alternative_response` | string | 替代回应建议 |
| `recommended_card_ids` | array | 推荐训练卡 ID |
| `risk_level` | string | `low`、`medium`、`high` |

## 4. 训练卡推荐

### `GET /api/cards/recommend`

用途：根据标签推荐 UP 训练卡。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `tags` | string | 否 | 逗号分隔标签 |
| `user_id` | string | 否 | 用户 ID |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `cards` | array | 训练卡列表 |

## 5. 练习打卡

### `POST /api/checkins`

用途：提交训练卡练习打卡。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 是 | 用户 ID |
| `card_id` | string | 是 | 训练卡 ID |
| `diary_id` | string | 否 | 关联情绪记录 |
| `completed` | boolean | 是 | 是否完成 |
| `emotion_before` | integer | 否 | 练习前情绪强度，1-10 |
| `emotion_after` | integer | 否 | 练习后情绪强度，1-10 |
| `reflection` | string | 否 | 简短复盘 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `checkin_id` | string | 打卡 ID |
| `created_at` | string | 创建时间 |

## 6. 周度报告

### `GET /api/weekly-report`

用途：获取一名用户的周度报告。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 是 | 用户 ID |
| `week_start` | string | 否 | 周开始日期 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `report_id` | string | 周报 ID |
| `frequent_scenes` | array | 高频场景 |
| `frequent_emotions` | array | 高频情绪 |
| `common_patterns` | array | 常见回应方式 |
| `completed_cards` | array | 已完成训练卡 |
| `next_week_suggestion` | string | 下周建议 |

## 7. 人工督导反馈

### `POST /api/supervision`

用途：提交典型记录给人工督导。

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | string | 是 | 用户 ID |
| `diary_id` | string | 否 | 关联记录 |
| `message` | string | 是 | 想请督导看的内容 |
| `contact` | string | 否 | 联系方式，第一版可选 |
| `risk_hint` | string | 否 | 用户自述风险提示 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `request_id` | string | 督导请求 ID |
| `status` | string | `pending` |

## 8. 后台数据导出

### `GET /api/admin/export`

用途：导出后台数据，第一版可导出 CSV。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | string | 否 | `diaries`、`checkins`、`feedback`、`all` |
| `format` | string | 否 | 第一版默认 `csv` |

响应：

- `text/csv` 文件流，或返回导出文件下载地址。
