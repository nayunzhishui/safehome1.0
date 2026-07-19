# SafeHome Backend MVP 1.0

这是“安心陪伴 / ReadFeedback”MVP 1.0 的 Flask + SQLite 后端。第一版只使用规则匹配生成即时反馈，不接入复杂 AI 调用。

## 环境准备

```powershell
cd D:\codex\workspace\safehome1.0\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

如果暂时不创建虚拟环境，也可以直接在 `backend` 目录执行：

```powershell
pip install -r requirements.txt
```

## 初始化数据库

启动后端时会自动创建 SQLite 数据库并同步 `content/training_cards.json` 中的训练卡。

如需生成演示数据：

```powershell
python seed_data\seed.py
```

数据库文件默认生成在：

```text
D:\codex\workspace\safehome1.0\backend\safehome.sqlite3
```

## 启动后端

```powershell
python app.py
```

启动后访问：

```text
http://127.0.0.1:5000/healthz
```

应返回：

```json
{"ok": true, "service": "safehome-backend"}
```

## MVP API

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| POST | `/api/goals` | 创建目标 |
| GET | `/api/goals` | 获取目标 |
| POST | `/api/diaries` | 创建情绪事件记录 |
| GET | `/api/diaries` | 获取情绪事件记录 |
| POST | `/api/feedback/generate` | 生成规则反馈 |
| GET | `/api/cards` | 获取训练卡 |
| GET | `/api/cards/recommend` | 推荐训练卡 |
| POST | `/api/checkins` | 创建练习打卡 |
| GET | `/api/checkins` | 获取练习打卡 |
| GET | `/api/weekly-report` | 生成周度报告 |
| POST | `/api/supervision` | 提交人工督导请求 |
| GET | `/api/admin/export` | 导出 CSV |
| GET | `/api/research/operations/queues` | 获取受权限约束的研究运营工作队列 |
| GET | `/api/research/work-items/<id>` | 查看工作项详情与处置轨迹 |
| POST | `/api/research/work-items/<id>/actions` | 执行领取、备注、消息、完成等幂等动作 |
| GET | `/api/research/work-items/metrics` | 获取积压、时效与动作趋势，不评价支持质量 |

## 快速测试

创建一条情绪事件记录：

```powershell
$body = @{
  user_id = "demo-parent"
  scene = "作业拖延"
  event_description = "孩子一直不写作业，我说你怎么又这样。"
  parent_emotion = "着急"
  parent_emotion_intensity = 8
  automatic_thought = "他就是故意拖。"
  behavior = "反复催促。"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:5000/api/diaries `
  -ContentType "application/json" `
  -Body $body
```

直接生成即时反馈：

```powershell
$body = @{
  user_id = "demo-parent"
  event_description = "你怎么又这样，我说多少遍了。"
  automatic_thought = "他就是故意拖。"
  behavior = "反复催促。"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:5000/api/feedback/generate `
  -ContentType "application/json" `
  -Body $body
```

导出情绪事件 CSV：

```powershell
Invoke-WebRequest `
  -Uri "http://127.0.0.1:5000/api/admin/export?type=diaries&user_id=demo-parent" `
  -OutFile ".\diaries.csv"
```

## 说明

- 即时反馈是非诊断、支持性、非评判表达。
- 训练卡来自 `content/training_cards.json`。
- 反馈规则来自 `content/feedback_rules.json`。
- 研究运营接口使用现有角色与对象范围鉴权，并写入审计日志；生产环境写操作默认由 `RESEARCH_OPERATIONS_WRITE_ENABLED=0` 关闭。
- 演示环境可使用测试身份；生产环境禁止缺省 `demo-parent`，正式权限验收不得使用临时展示越权作为证据。
