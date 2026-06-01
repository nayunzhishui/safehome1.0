# MVP 1.0 验收清单

验收日期：2026-05-21

项目路径：`D:\codex\workspace\safehome1.0`

进度说明：MVP 1.0 已按本文完成封版验收。后续新增的 MVP 1.1、0版网页整合、学生画像和上线准备，以 `docs/项目进度统一口径.md` 为准。

本次验收目标：封版前检查当前 MVP 1.0 是否已经具备“可演示、可联调、可继续迭代”的基础状态。本轮只做检查和文档记录，不新增业务功能，不接入 AI，不做登录注册，不做复杂周报。

## 1. 验收结论

当前项目总体状态：**P1、P2 已修复，剩余 P3 为正式试点前低优先级优化项**。

已通过：

- 小程序 MVP 1.0 最小正式流程已建立；
- 小程序仍保留 `pages/integration-test/index` 长期联调测试页；
- 后端 Flask + SQLite 关键 API 可用；
- 规则反馈和训练卡推荐可用；
- content 中训练卡和反馈规则 JSON 格式有效；
- 数据导出接口可用；
- 当前未发现已被 Git 跟踪的 `node_modules`、`dist`、数据库、虚拟环境或 `__pycache__` 文件。

本轮已修复：

- 网页管理后台已能在记录详情中生成并展示该记录对应的即时反馈和训练卡推荐；
- 数据导出接口已增加 `X-Admin-Token` 后台导出令牌校验。

## 2. 小程序核心流程检查

检查结果：**通过**。

已确认 `apps/miniprogram/app.json` 中包含以下正式页面：

```text
pages/home/index
pages/diary-form/index
pages/feedback-result/index
pages/training-card/index
pages/checkin/index
```

当前正式流程：

```text
首页 -> 情绪事件记录页 -> 即时反馈页 -> UP训练卡推荐页 -> 练习打卡页
```

已确认长期联调测试页仍保留：

```text
pages/integration-test/index
```

本次检查命令：

```powershell
Get-Content -Path apps/miniprogram/app.json
Get-ChildItem -Path apps/miniprogram/pages -Recurse -File
```

语法检查：

```powershell
Get-ChildItem -Path apps/miniprogram -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
Get-ChildItem -Path apps/miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -Path $_.FullName | ConvertFrom-Json }
```

结果：

- 小程序 JS 语法检查通过；
- 小程序 JSON 配置检查通过。

## 3. 网页管理后台流程检查

检查结果：**通过**。

当前已通过：

- 网页端可以打开；
- 网页端可以读取最近 50 条情绪事件记录；
- 网页端可以点击记录查看详情；
- 网页端可以在记录详情中生成即时反馈；
- 网页端可以根据反馈标签展示推荐训练卡；
- 网页端提供带令牌校验的情绪记录 CSV 导出入口；
- 原网页端最小联调测试区仍保留。

实现方式：

- 记录详情中点击“生成反馈和推荐”；
- 调用现有 `POST /api/feedback/generate`；
- 展示 `supportive_feedback`、`labels`、`alternative_response`；
- 使用反馈返回的 `tags` 调用 `GET /api/cards/recommend`；
- 展示推荐训练卡标题、说明和替代话术。

相关文件：

```text
apps/web/src/pages/AdminDashboard.tsx
apps/web/src/pages/IntegrationSmokeTest.tsx
apps/web/src/services/safehomeApi.ts
```

## 4. 后端 API 检查

检查结果：**通过**。

本次实际请求过的接口：

```text
GET /healthz
GET /api/diaries?limit=1
POST /api/feedback/generate
GET /api/cards
GET /api/cards/recommend?tags=judgmental_language&limit=2
GET /api/checkins?limit=3
GET /api/weekly-report
GET /api/admin/export?type=diaries
```

检查结果：

- `/healthz` 正常；
- 情绪记录列表可返回数据；
- 即时反馈生成可返回支持性反馈；
- 训练卡列表可返回数据；
- 训练卡推荐可返回数据；
- 练习打卡列表可返回数据；
- 周报接口可返回数据；
- CSV 导出接口可返回 200。
- CSV 导出接口未提供令牌时返回 401。
- CSV 导出接口提供正确 `X-Admin-Token` 时返回 200。

后端 Python 编译检查：

```powershell
python -m compileall backend
```

结果：通过。

## 5. 数据导出检查

检查结果：**通过**。

本次检查了以下导出类型：

```text
goals
diaries
feedback
checkins
reports
supervision
cards
```

加上正确 `X-Admin-Token` 后，全部返回 HTTP 200。

注意：

- 当前导出接口已有后台令牌校验；
- 本地默认令牌是 `safehome-local-admin-token`；
- 正式部署前必须通过环境变量 `ADMIN_EXPORT_TOKEN` 改掉默认令牌；
- 当前仍不是完整登录和角色权限系统。

## 6. content 训练卡和反馈规则检查

检查结果：**通过，存在低优先级文案优化建议**。

本次检查文件：

```text
content/training_cards.json
content/feedback_rules.json
content/consent.md
content/privacy.md
```

JSON 格式检查：

```powershell
Get-Content -Raw content/feedback_rules.json | ConvertFrom-Json
Get-Content -Raw content/training_cards.json | ConvertFrom-Json
```

结果：通过。

当前内容库已包含：

- 训练卡；
- 反馈规则；
- 知情同意文本；
- 隐私文本；
- 非诊断边界说明；
- 高风险人工支持边界说明。

低优先级文案优化建议：

- `content/feedback_rules.json` 和 `content/training_cards.json` 中出现了“故意拖”“就是懒”“必须马上”“没救了”等词。
- 这些词当前主要作为“待识别的高压表达”或“需要被替换的例子”，不是系统对家长或孩子的判断。
- 当前不构成封版阻断，但正式试点前可以把示例改得更温和，例如改成“我脑中出现了一个很重的判断”。

## 7. 非诊断、非标签化、支持性、非评判文案检查

检查结果：**通过，未发现阻断性问题**。

本次搜索关键词：

```text
焦虑症
抑郁症
控制型人格
人格
病态
诊断
标签化
责备
活该
懒
故意
必须
应该
```

未发现以下禁止表达：

- “孩子有焦虑症”；
- “孩子是抑郁”；
- “家长是控制型人格”；
- “家长存在人格问题”；
- “这个家庭属于病态互动”。

需要说明的命中：

1. `content/consent.md`、`content/privacy.md` 中出现“诊断”，用于说明“不构成诊断”，这是正确边界说明。
2. `content/feedback_rules.json`、`content/training_cards.json` 中出现“懒”“故意”“必须”等词，用于识别或替换高压表达，不是系统反馈结论。
3. `apps/web/src/pages/IntegrationSmokeTest.tsx` 中有“他就是故意拖。”，这是联调测试输入中的自动想法示例，不是面向家长的系统反馈。

当前支持性文案边界：通过。

## 8. Git 与运行产物检查

检查结果：**通过，但本地存在被忽略的运行产物**。

已检查是否有运行产物被 Git 跟踪：

```powershell
git ls-files | Select-String -Pattern '(^|/)(node_modules|dist|\.venv|venv|__pycache__)(/|$)|\.(db|sqlite3)$'
```

结果：没有输出，表示未发现这些文件被 Git 跟踪。

当前本地存在但被忽略的运行产物：

```text
apps/miniprogram/project.private.config.json
apps/web/dist/
apps/web/node_modules/
backend/__pycache__/
backend/routes/__pycache__/
backend/safehome.sqlite3
backend/seed_data/__pycache__/
backend/services/__pycache__/
```

这些文件当前显示为 ignored，不应提交。

## 9. 当前已通过项

1. 小程序正式流程页面存在；
2. 小程序长期联调测试页保留；
3. 小程序 JS/JSON 检查通过；
4. 后端健康检查通过；
5. 情绪记录 API 可用；
6. 反馈生成 API 可用；
7. 训练卡列表 API 可用；
8. 训练卡推荐 API 可用；
9. 打卡查询 API 可用；
10. 周报接口可用；
11. CSV 导出接口可用；
12. content JSON 格式有效；
13. 网页端构建通过；
14. 网页端能查看情绪记录列表和详情；
15. 网页端记录详情能展示即时反馈和推荐训练卡；
16. CSV 导出接口已有令牌校验；
17. 未发现被 Git 跟踪的运行产物；
18. 未发现阻断性诊断化、标签化或责备性系统文案。

## 10. 当前待修复项

### P3：正式试点前可温和化部分示例词

当前“故意拖”“就是懒”“必须马上”等词是识别规则或替代表达示例，不是系统结论。

正式试点前可以进一步降低刺激性，但不影响当前 MVP 封版演示。

## 10.1 已修复项

### P1：网页后台补齐反馈结果和训练卡推荐展示

已修复。

当前网页后台记录详情中可以：

- 生成即时反馈；
- 展示识别标签；
- 展示替代回应；
- 展示推荐训练卡标题、说明和替代话术。

### P2：导出接口正式使用前需要权限保护

已做最小修复。

当前 `/api/admin/export` 要求请求头：

```text
X-Admin-Token: safehome-local-admin-token
```

正式部署前应通过环境变量 `ADMIN_EXPORT_TOKEN` 修改默认令牌。

## 11. 优先级排序

1. P3：正式试点前优化少量示例词。
2. 正式部署前：把 `ADMIN_EXPORT_TOKEN` 改成非默认值。
3. 后续增强：如需要真实后台权限，再单独设计登录和角色系统。

## 12. 下一步最小修复任务

建议下一步只做一个低风险优化任务：

```text
正式试点前温和化 content 中少量高压表达示例。
```

边界：

- 不新增 AI；
- 不新增登录；
- 不新增数据库字段；
- 不新增复杂周报；
- 不删除联调测试页；
- 不改变小程序正式流程。

完成后再重新运行：

```powershell
cd D:\codex\workspace\safehome1.0\apps\web
npm run build
```

并手动打开：

```text
http://127.0.0.1:5173
```

确认网页后台仍可以同时看到：

```text
情绪记录 -> 即时反馈 -> 推荐训练卡
```
