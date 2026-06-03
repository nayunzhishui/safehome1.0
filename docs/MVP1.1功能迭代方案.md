# MVP 1.1 功能迭代方案

创建日期：2026-05-21

项目：`safehome1.0 / 安心陪伴 / ReadFeedback 家长情绪管理支持系统`

项目路径：`D:\codex\workspace\safehome1.0`

本方案最初用于 MVP 1.1 规划。当前已补充实际完成情况，用于区分“已完成第一版”和“后置能力”。最新统一进度以 `docs/项目进度统一口径.md` 为准。

## 0A. 2026-06-01 统一进度补充

当前 MVP 1.1 家长端主闭环与网站后台第一版已经完成。本文后续章节中涉及“规划、建议、新增”的内容，若与本节冲突，以本节和 `docs/项目进度统一口径.md` 为准。

当前不要误解为已完成的后置能力：

1. 正式登录注册；
2. 正式权限系统；
3. 正式部署；
4. 画像 API 和风险检查 API；
5. 学生画像结果页；
6. 画像导出、`records` 和审计日志；
7. AI 自由问答、机器学习、深度学习、语音、视频、社群能力。

如果继续开发，不建议再从 MVP 1.1 常规页面开始，而应优先根据 `docs/1.2逐步开发任务清单.md` 执行学生画像 P0-4。

## 0. 截至 2026-05-22 已完成情况

当前 MVP 1.1 第一版已经完成小程序端主闭环增强和网站后台主要查看页补齐。

### 0.1 小程序端已完成

已完成第一版：

1. 目标设定入口和目标保存；
2. 情绪记录页字段升级；
3. 反馈页“情绪与互动模式识别卡”；
4. 训练卡详情增强；
5. 轻打卡页关联记录和训练卡；
6. 简版周度复盘页；
7. 人工督导补充入口；
8. `pages/integration-test/index` 保留。

小程序端当前主链路：

```text
首页 -> 目标设定 -> 情绪记录 -> 反馈结果 -> 推荐训练卡 -> 打卡 -> 周报 -> 督导入口
```

当前仍不做：

1. 正式登录注册；
2. 正式部署；
3. AI 自由问答；
4. 机器学习或深度学习；
5. 语音、视频、社群；
6. 复杂课程体系。

### 0.2 网站后台已完成

已完成第一版：

| 页面 | 当前状态 | 主要数据来源 |
|---|---|---|
| `/dashboard` | 已完成 | `GET /api/goals`、`GET /api/diaries`、`GET /api/checkins`、`GET /api/cards` |
| `/goals` | 已完成 | `GET /api/goals` |
| `/diaries` | 已完成 | `GET /api/diaries`、`POST /api/feedback/generate`、`GET /api/cards/recommend` |
| `/feedback` | 已完成 | `GET /api/admin/export?type=feedback` |
| `/checkins` | 已完成 | `GET /api/checkins`、`GET /api/cards` |
| `/reports` | 已完成 | `GET /api/admin/export?type=reports` |
| `/supervision` | 已完成 | `GET /api/admin/export?type=supervision` |
| `/content/cards` | 已完成 | `GET /api/cards` |
| `/content/rules` | 已完成 | `content/feedback_rules.json` |
| `/export` | 已完成 | `GET /api/admin/export` |
| `/integration-test` | 保留 | 现有联调页 |

网站后台当前特点：

1. 以只读查看为主；
2. 优先复用现有 API 和 CSV 导出；
3. 未新增后端列表 API；
4. 未修改数据库；
5. 未新增正式权限系统；
6. 数据导出仍使用 `X-Admin-Token`。

### 0.3 实际实现与原规划的主要差异

原规划中建议后续新增的部分 API，当前第一版没有新增，而是先用现有导出能力完成后台查看。

| 原规划建议 | 当前第一版实际实现 |
|---|---|
| `GET /api/feedback` | 暂不新增，`/feedback` 复用 `GET /api/admin/export?type=feedback` |
| `GET /api/reports` | 暂不新增，`/reports` 复用 `GET /api/admin/export?type=reports` |
| `GET /api/supervision` | 暂不新增，`/supervision` 复用 `GET /api/admin/export?type=supervision` |
| `GET /api/content/rules` | 暂不新增，`/content/rules` 直接只读导入 `content/feedback_rules.json` |
| `GET /api/admin/summary` | 暂不新增，`/dashboard` 复用已有列表接口 |

这样做的原因：

1. 降低本轮改动风险；
2. 不影响小程序核心链路；
3. 不改变现有数据库结构；
4. 先满足试点查看和验收需要；
5. 将正式后台 API 和权限系统后置。

### 0.4 当前后置能力

以下能力仍为后置：

1. 正式登录注册；
2. 正式权限系统；
3. 正式部署；
4. 训练卡在线编辑；
5. 反馈规则在线编辑；
6. 督导回复和状态流转；
7. 导出脱敏参数；
8. 日期范围筛选；
9. 独立 `GET /api/feedback`；
10. 独立 `GET /api/reports`；
11. 独立 `GET /api/supervision`；
12. AI 自由问答、机器学习、深度学习、语音、视频、社群能力。

### 0.5 当前验收和提交文档

当前新增了两份收尾文档：

```text
docs/网站后台最终验收清单.md
docs/提交前检查清单.md
```

建议提交前按这两份文档完成手动验收和分批暂存。

## 1. MVP 1.1 的定位

MVP 1.1 的目标是在不脱离最小产品边界的前提下，把 MVP 1.0 的最小链路：

```text
记录 -> 反馈 -> 训练卡
```

扩展为更完整但仍然轻量的家长训练闭环：

```text
目标 -> 记录 -> 识别 -> 反馈 -> 练习 -> 追踪 -> 支持
```

对应产品核心闭环：

```text
目标设定 -> 情绪事件记录 -> 情绪与互动模式识别 -> 非诊断反馈 -> UP训练卡推送 -> 练习打卡 -> 周度报告 -> 人工督导补充
```

MVP 1.1 仍然不是正式治疗产品，不做临床诊断，不做复杂 AI，不做登录注册，不做正式部署。

## 2. 为什么这些功能仍属于最小产品

这些功能属于 MVP 范围，因为它们不是横向扩展，而是补齐原闭环中已经定义但尚未充分呈现的关键步骤。

保留在 MVP 1.1 的原因：

1. 目标设定：让家长知道本周想练什么，避免只是零散记录。
2. 情绪事件记录升级：提高记录质量，但仍保持低负担。
3. 模式识别卡：把规则反馈结果变得更可理解。
4. UP训练卡详情与轻打卡：把“推荐”推进到“练习”。
5. 简版周度报告：让家长看到一周内的重复模式和小变化。
6. 人工督导补充入口：为不确定或高风险内容提供人工支持边界。

不纳入本轮的原因：

- AI 自由问答、机器学习、深度学习：会放大伦理、稳定性和成本风险。
- 语音/视频上传、社群、积分勋章：与当前主闭环无关，增加复杂度。
- 正式登录注册、正式部署：属于产品化和安全阶段，不是本轮功能验证重点。
- 复杂课程体系：会把 MVP 变成课程产品，偏离记录与练习闭环。

## 3. 功能优先级

| 优先级 | 功能 | 目标 | 说明 |
|---|---|---|---|
| P0 | 目标设定页 | 补齐闭环起点 | 复用已有 `goals` API，先做 7 天小目标 |
| P0 | 情绪事件记录升级 | 提高记录质量 | 优化表单结构，尽量不改数据库 |
| P0 | 模式识别卡 | 让反馈更可理解 | 复用 `feedback_rules.json` 与 `feedback` API |
| P0 | UP训练卡详情与轻打卡 | 推动练习行为 | 复用 `cards` 与 `checkins` API |
| P1 | 简版周度报告 | 形成追踪闭环 | 复用 `weekly-report` API，先做只读报告 |
| P1 | 人工督导补充入口 | 提供边界内支持 | 复用 `supervision` API，强调非实时和非危机服务 |
| P2 | 网页后台目标/督导扩展 | 支持内部查看 | 只做查看，不做复杂权限 |
| P3 | 内容温和化 | 降低刺激性 | 优化规则和训练卡示例词 |

推荐开发顺序：

```text
目标设定页 -> 记录页字段升级 -> 反馈页模式识别卡 -> 训练卡详情与轻打卡 -> 简版周报 -> 督导入口 -> 网页后台补齐查看
```

## 4. 功能一：目标设定页

### 4.1 小程序页面

新增：

```text
apps/miniprogram/pages/goal-setting/index
```

字段：

- 高频亲子冲突场景；
- 希望减少的旧反应；
- 希望练习的新反应；
- 本周 SMART 小目标。

建议交互：

- 场景使用标签选择加“其他”输入；
- 旧反应和新反应用短文本；
- SMART 小目标用示例提示，不做复杂校验；
- 保存成功后跳转首页或记录页。

### 4.2 后端 API

优先复用：

```text
POST /api/goals
GET /api/goals
```

现有 `goals` 表字段：

- `scene`
- `smart_goal`
- `motivation`
- `start_date`
- `status`

最小映射方案：

| 前端字段 | 当前后端字段 | 说明 |
|---|---|---|
| 高频亲子冲突场景 | `scene` | 直接映射 |
| 本周 SMART 小目标 | `smart_goal` | 直接映射 |
| 希望减少的旧反应 | `motivation` | 第一版可合并写入 |
| 希望练习的新反应 | `motivation` | 第一版可合并写入 |

是否需要改数据库：第一版不需要。后续若要结构化保存旧反应和新反应，再评估新增字段。

### 4.3 content 影响

不必须修改 content。

可选新增：

- 目标设定示例文案；
- SMART 小目标说明文案。

优先放在文档或小程序页面常量中，暂不新增复杂内容库。

### 4.4 网页后台

规划新增目标查看区：

- 查看目标列表；
- 查看目标状态；
- 查看目标关联的情绪记录数量。

第一版只查看，不编辑。

## 5. 功能二：情绪事件记录升级

### 5.1 小程序页面

修改现有：

```text
apps/miniprogram/pages/diary-form/index
```

建议结构：

1. 事件：发生了什么；
2. 情绪：家长情绪、孩子情绪；
3. 强度：家长 0-10、孩子 0-10；
4. 想法：我当时脑中出现了什么念头；
5. 身体感觉：胸口紧、心跳快、头胀等标签；
6. 行为：我说了什么/做了什么；
7. 孩子反应：孩子后来有什么反应；
8. 短期结果：当下有没有暂时停下来；
9. 长期影响：如果常常这样，可能会带来什么影响。

低负担原则：

- 必填字段保留最少：事件、家长情绪、家长强度；
- 能用标签选择的尽量用标签；
- “身体感觉”“短期结果”“长期影响”第一版可作为可选；
- 页面不做长篇解释。

### 5.2 后端 API

优先复用：

```text
POST /api/diaries
GET /api/diaries
```

当前可直接映射字段：

| MVP 1.1 字段 | 当前字段 | 说明 |
|---|---|---|
| 事件 | `event_description` | 直接映射 |
| 情绪 | `parent_emotion`、`child_emotion` | 直接映射 |
| 强度 | `parent_emotion_intensity`、`child_emotion_intensity` | 直接映射 |
| 想法 | `automatic_thought` | 直接映射 |
| 身体感觉 | `body_sensation` | 直接映射 |
| 行为 | `behavior` | 直接映射 |
| 孩子反应 | `raw_text` | 第一版可合并保存 |
| 短期结果 | `raw_text` | 第一版可合并保存 |
| 长期影响 | `raw_text` | 第一版可合并保存 |

是否需要改数据库：第一版不需要。若后续需要单独统计孩子反应、短期结果、长期影响，再新增字段。

### 5.3 content 影响

可复用：

- `content/feedback_rules.json` 用于识别自动想法、评判性语言、情绪性行为；
- `shared/constants/api.ts` 中的常见场景和常见情绪。

可选新增：

- 身体感觉标签；
- 常见回应方式标签；
- 短期结果标签。

优先放 `shared/constants`，不要先改数据库。

### 5.4 网页后台

网页后台记录详情需要跟随展示：

- 事件；
- 情绪强度；
- 自动想法；
- 身体感觉；
- 行为；
- 孩子反应/短期结果/长期影响的合并文本。

## 6. 功能三：情绪与互动模式识别卡

### 6.1 小程序页面

修改现有：

```text
apps/miniprogram/pages/feedback-result/index
```

新增“这次记录中可以看到的模式”卡片。

标签类型：

- 触发点；
- 自动想法；
- 评判性语言；
- 情绪性行为。

推荐文案方式：

- “这次记录中可以看到……”
- “看起来当时可能有一个自动想法……”
- “这里可能出现了比较急的回应方式……”
- “这不是评价谁对谁错，而是帮助我们找到可练习的位置。”

禁止表达：

- “你是控制型家长”；
- “孩子有问题”；
- “这是焦虑症/抑郁症”；
- “你错误地认为……”；
- “你应该纠正认知……”。

### 6.2 后端 API

复用：

```text
POST /api/feedback/generate
```

现有响应字段可用：

- `tags`
- `labels`
- `trigger_summary`
- `pattern_summary`
- `supportive_feedback`
- `alternative_response`
- `recommended_card_ids`
- `risk_level`

是否需要改 API：第一版不需要。

### 6.3 数据库

复用：

```text
feedback_results
```

是否需要改字段：第一版不需要。

### 6.4 content 影响

重点使用：

```text
content/feedback_rules.json
```

规划优化：

- 增加标签说明字段或在前端做标签解释映射；
- 把高压示例词再温和化；
- 明确规则输出必须使用保守措辞。

## 7. 功能四：UP训练卡详情与轻打卡

### 7.1 小程序页面

修改现有：

```text
apps/miniprogram/pages/training-card/index
apps/miniprogram/pages/checkin/index
```

训练卡详情结构：

- 适用场景；
- 训练目标；
- 操作步骤；
- 可复制话术；
- 记录问题。

按钮：

- “我想练习这张卡”；
- “完成一次练习”。

轻打卡字段：

- 是否练习；
- 练习前情绪强度；
- 练习后情绪强度；
- 一句话复盘。

### 7.2 后端 API

复用：

```text
GET /api/cards
GET /api/cards/recommend
POST /api/checkins
GET /api/checkins
```

是否需要改 API：第一版不需要。

### 7.3 数据库

复用：

- `training_cards`
- `checkins`

当前 `checkins` 已支持：

- `card_id`
- `diary_id`
- `completed`
- `emotion_before`
- `emotion_after`
- `reflection`

是否需要改字段：第一版不需要。

### 7.4 content 影响

重点使用：

```text
content/training_cards.json
```

规划优化：

- 每张卡补齐适用场景；
- 每张卡补齐训练目标；
- 每张卡补齐记录问题；
- 可复制话术必须非评判、支持性。

如果现有 JSON 字段不足，优先在前端用现有 `purpose`、`steps`、`example` 组合展示，不先改结构。

## 8. 功能五：简版周度报告

### 8.1 小程序页面

规划新增：

```text
apps/miniprogram/pages/weekly-report/index
```

展示内容：

- 本周高频场景；
- 本周高频情绪；
- 常见回应方式；
- 积极变化；
- 下周练习建议。

文案边界：

- 不做诊断评分；
- 不做复杂心理解释；
- 不写“问题家庭”“控制型家长”等标签；
- 只做复盘、鼓励和下一步建议。

### 8.2 后端 API

复用：

```text
GET /api/weekly-report
```

是否需要改 API：第一版不需要。

### 8.3 数据库

复用：

```text
weekly_reports
```

字段已支持：

- 高频场景；
- 高频情绪；
- 常见模式；
- 已完成训练卡；
- 下周建议。

是否需要改字段：第一版不需要。

### 8.4 网页后台

规划增加：

- 用户周报查看；
- 周报 CSV 导出可继续复用 `type=reports`。

第一版只查看，不编辑。

## 9. 功能六：人工督导补充入口

### 9.1 小程序页面

建议入口放在：

```text
apps/miniprogram/pages/feedback-result/index
apps/miniprogram/pages/weekly-report/index
```

按钮文案：

```text
我想让老师进一步看看这条记录
```

提交字段：

- 关联记录 ID；
- 想请老师看的内容；
- 可选联系方式；
- 风险提示自述。

边界说明必须展示：

```text
人工反馈仅用于补充理解和练习建议，不替代心理咨询、医学诊断或危机干预。如出现自伤、自杀、暴力或其他紧急安全风险，请优先联系线下专业人员或紧急支持。
```

### 9.2 后端 API

复用：

```text
POST /api/supervision
```

当前缺口：

- API 文档中只有创建接口；
- 网页后台若要列表和详情，需要规划 `GET /api/supervision`，或通过 CSV 导出临时查看。

建议 MVP 1.1 最小新增：

```text
GET /api/supervision
```

用于网页后台查看督导请求列表。

### 9.3 数据库

复用：

```text
supervision_requests
```

是否需要改字段：第一版不需要。

### 9.4 网页后台

规划新增：

- 督导请求列表；
- 督导请求详情；
- 状态显示：`pending`、`replied`、`closed`。

第一版不做复杂回复流，不做实时服务承诺。

## 10. 网页后台规划

MVP 1.1 网页后台优先做查看，不做复杂管理。

功能顺序：

1. 目标列表和详情；
2. 情绪记录详情继续保留反馈和训练卡推荐；
3. 练习打卡列表；
4. 周报查看；
5. 督导请求列表和详情；
6. CSV 导出继续保留令牌保护。

不做：

- 登录注册；
- 复杂权限；
- 批量编辑；
- 内容管理后台；
- 训练卡在线编辑；
- 反馈规则在线编辑。

## 11. 心理学与伦理边界

MVP 1.1 参考 UP 框架，但必须转化为家长可理解语言。

允许使用：

- 情绪三成分模型：想法、身体感觉、行为；
- 情绪反射弧：触发事件、反应、短期结果、长期影响；
- 非评判觉察；
- 认知灵活化；
- 情绪性行为与替代行为；
- 练习和复盘。

禁止或暂缓：

- 诊断家长、孩子或家庭关系；
- 写“孩子有焦虑症”“家长是控制型人格”等表达；
- 写“纠正错误认知”；
- 责备家长或孩子；
- 内感性暴露正式训练；
- 情绪暴露正式训练；
- 危机干预自动化；
- AI 自由问答。

所有反馈必须使用保守措辞：

- “可能”；
- “看起来”；
- “这次记录中可以看到”；
- “这不是评价谁对谁错”；
- “可以先尝试一个更小的替代动作”。

## 12. 用户研究验证指标

MVP 1.1 不追求复杂增长指标，重点验证闭环是否可用。

建议观察指标：

1. 目标设定完成率；
2. 每位家长一周记录次数；
3. 记录页平均填写耗时；
4. 反馈页阅读完成率；
5. 训练卡点击率；
6. 练习打卡完成率；
7. 练习前后情绪强度变化；
8. 周报打开率；
9. 督导入口点击率；
10. 家长是否能用自己的话复述“我下次可以练什么”。

伦理与体验指标：

- 家长是否觉得被评价；
- 家长是否觉得文案太临床；
- 家长是否觉得表单太长；
- 家长是否清楚这不是诊断；
- 家长是否知道高风险时应寻求线下支持。

## 13. UI/视觉风格要求

整体风格：

- 温和；
- 绿色；
- 低压力；
- 可信；
- 专业但不临床化。

页面结构：

- 卡片式结构；
- 分步骤呈现；
- 避免长表单；
- 重要信息放在顶部；
- 次要解释可折叠或放在轻提示中。

颜色：

- 主色保持绿色；
- 辅色使用浅绿、灰绿、白色；
- 避免大面积红色；
- 高风险提示可以使用柔和橙色，不使用刺眼警报风。

图标建议使用线性图标：

| 步骤 | 图标含义 |
|---|---|
| 目标设定 | 靶心 |
| 事件记录 | 剪贴板 |
| 模式识别 | 放大镜 |
| 反馈 | 对话气泡 |
| 训练卡 | 卡片 |
| 打卡 | 日历勾选 |
| 周报 | 柱状图 |
| 督导 | 人物盾牌 |

按钮文案：

- 使用“开始记录”“看看反馈”“试试这张练习卡”“完成一次练习”等温和表达；
- 避免“立即纠正”“必须完成”“马上改变”等命令式文案。

## 14. 验收标准

### 14.1 功能验收

MVP 1.1 通过标准：

1. 小程序能完成目标设定；
2. 小程序能完成升级后的情绪事件记录；
3. 反馈页能展示模式识别卡；
4. 训练卡页能展示结构化详情；
5. 打卡页能保存轻打卡；
6. 周报页能展示简版周报；
7. 督导入口能提交请求；
8. 网页后台能查看目标、记录、打卡、周报、督导请求；
9. integration-test 页面仍保留；
10. 原 MVP 1.0 核心链路仍能跑通。

### 14.2 技术验收

每轮实现后至少验证：

```powershell
python -m compileall backend
cd D:\codex\workspace\safehome1.0\apps\web
npm run build
```

小程序验证：

- 微信开发者工具重新编译；
- 首页进入目标设定；
- 完成记录、反馈、训练卡、打卡、周报、督导入口的最小流程；
- Console 无阻断性红色错误。

接口验证：

- `/healthz` 正常；
- goals、diaries、feedback、cards、checkins、weekly-report、supervision 关键接口正常；
- CSV 导出仍需要 `X-Admin-Token`。

### 14.3 文案验收

不得出现：

- “孩子有焦虑症”；
- “孩子是抑郁”；
- “家长是控制型人格”；
- “病态家庭”；
- “纠正错误认知”；
- “你必须马上改变”。

必须体现：

- 非诊断；
- 非标签化；
- 支持性；
- 非评判；
- 练习导向；
- 高风险边界。

## 15. 回滚方案

通用回滚原则：

- 优先隐藏入口，不删除接口、数据表或内容库；
- 保留 `pages/integration-test/index`；
- 保留现有 MVP 1.0 核心链路；
- 保留数据库字段；
- 文档标记为“暂缓”，不要直接删除规划。

功能级回滚：

| 功能 | 回滚方式 |
|---|---|
| 目标设定页 | 从首页隐藏入口，保留 `goals` API |
| 记录页升级 | 恢复旧字段展示，保留已保存数据 |
| 模式识别卡 | 隐藏模式识别卡，保留基础反馈 |
| 训练卡详情 | 回退为标题、说明、话术三段展示 |
| 轻打卡 | 隐藏打卡入口，保留 `checkins` API |
| 周报页 | 隐藏周报入口，保留 `weekly-report` API |
| 督导入口 | 隐藏提交入口，保留 `supervision_requests` 表 |
| 网页后台扩展 | 隐藏相关后台区块，保留导出能力 |

## 16. 需要新增/修改的文件清单

规划新增：

```text
apps/miniprogram/pages/goal-setting/index.js
apps/miniprogram/pages/goal-setting/index.json
apps/miniprogram/pages/goal-setting/index.wxml
apps/miniprogram/pages/goal-setting/index.wxss
apps/miniprogram/pages/weekly-report/index.js
apps/miniprogram/pages/weekly-report/index.json
apps/miniprogram/pages/weekly-report/index.wxml
apps/miniprogram/pages/weekly-report/index.wxss
```

可能新增：

```text
backend/routes/supervision.py 增加 GET /api/supervision
apps/web/src/pages 或 AdminDashboard 中增加目标、打卡、周报、督导查看区
```

规划修改：

```text
apps/miniprogram/app.json
apps/miniprogram/pages/home/index.*
apps/miniprogram/pages/diary-form/index.*
apps/miniprogram/pages/feedback-result/index.*
apps/miniprogram/pages/training-card/index.*
apps/miniprogram/pages/checkin/index.*
apps/miniprogram/services/api.js
apps/web/src/services/safehomeApi.ts
shared/types/api.ts
shared/constants/api.ts
docs/API接口文档.md
docs/数据库字段说明.md
docs/当前进度交接.md
docs/开发日志.md
docs/开发说明.md
AGENTS.md
```

content 可选修改：

```text
content/training_cards.json
content/feedback_rules.json
content/consent.md
content/privacy.md
```

## 17. 是否需要改数据库

MVP 1.1 第一阶段尽量不改数据库。

可复用现有表：

- `goals`
- `emotion_diaries`
- `feedback_results`
- `training_cards`
- `checkins`
- `weekly_reports`
- `supervision_requests`

可能后续需要新增字段，但不作为第一阶段必需：

- `goals.old_reaction`
- `goals.new_reaction`
- `emotion_diaries.child_reaction`
- `emotion_diaries.short_term_result`
- `emotion_diaries.long_term_impact`

建议先通过现有 `motivation`、`raw_text`、前端展示结构完成最小闭环，再根据真实使用反馈决定是否改表。

## 18. 是否需要改 API

大多数功能可复用现有 API。

需要规划的最小 API 增强：

```text
GET /api/supervision
```

用于网页后台查看督导请求列表。

可选增强：

- `GET /api/feedback?diary_id=...`：查看已生成反馈，避免重复生成；
- `GET /api/goals?status=active` 已支持；
- `GET /api/checkins` 已支持；
- `GET /api/weekly-report` 已支持。

第一阶段优先不新增复杂 API。

## 19. 风险点

1. 表单变长导致家长放弃填写；
2. 模式识别文案让家长觉得被评价；
3. 目标设定过于复杂，像课程作业；
4. 周报被误解为心理评估报告；
5. 督导入口被误解为实时咨询或危机支持；
6. 导出数据包含敏感文本，正式部署前权限不足；
7. 训练卡文案若过于技术化，会降低使用意愿；
8. 若过早改数据库，可能影响小程序端和网页端一致性。

## 20. 每一步如何测试

| 步骤 | 测试方式 |
|---|---|
| 目标设定页 | 小程序保存目标，网页后台能看到目标 |
| 记录页升级 | 提交记录后反馈页能读取 diary id |
| 模式识别卡 | 反馈页展示标签、解释、支持性反馈，无诊断表达 |
| 训练卡详情 | 推荐卡能显示步骤和话术 |
| 轻打卡 | 完成打卡后 `GET /api/checkins` 能看到记录 |
| 周报页 | `GET /api/weekly-report` 返回高频场景和下周建议 |
| 督导入口 | 提交后 `supervision_requests` 有记录 |
| 网页后台 | 能查看目标、记录、打卡、周报、督导 |
| 数据导出 | 无令牌 401，有令牌 200 |
| 文案边界 | 搜索禁止词，人工检查反馈文案 |

## 21. 下一轮最小开发任务

如果下一轮开始写代码，建议先做：

```text
新增小程序 pages/goal-setting/index，并复用现有 POST /api/goals 保存目标。
```

原因：

- 它是 MVP 1.1 闭环起点；
- 后端已有 `goals` API；
- 数据库已有 `goals` 表；
- 风险低；
- 可以独立测试；
- 不影响现有记录、反馈、训练卡流程。

最小完成标准：

1. 首页增加“设定本周小目标”入口；
2. 新增目标设定页；
3. 能填写高频场景、旧反应、新反应、SMART 目标；
4. 点击保存后调用 `POST /api/goals`；
5. 保存成功后返回首页或进入记录页；
6. 文档同步更新；
7. 不删除 integration-test 页面。

## 22. 后续规划：0版网页评估画像整合（MVP 1.2 候选）

本节根据夏老师“0版网页与安心家整合”资料、PDF/PNG 思维导图和 GitHub 参考项目整理。它属于 MVP 1.1 后的规划，不改变当前 MVP 1.1 已确定的最小任务顺序。

### 22.1 产品定位

后续不建议把“0版网页”作为一个独立页面直接塞进安心家，而应将其沉淀为安心家的“评估画像与反馈引擎”：

```text
安心家 = 主平台和长期陪伴闭环
0版网页 = 学生画像、解释反馈、任务推荐、研究导出能力
```

对用户展示时统一称为安心家内的“支持性测评”或“学生画像”，不展示“0版网页”这个内部名称。

### 22.2 候选闭环

建议 MVP 1.2 候选链路：

```text
测一测 -> 学生支持性画像 -> 置信度与维度解释 -> 推荐一个训练/沙盘任务 -> 打卡或复测 -> 后台导出
```

它必须接入安心家已有的训练卡和周报体系，避免变成“一次测评即结束”。

### 22.3 最小技术范围

| 优先级 | 内容 | 说明 |
|---|---|---|
| P0 | 非诊断表达、风险关键词、画像命名规范 | 先锁定边界，不直接写代码 |
| P1 | `POST /api/profile`、`student_profile_rules.json`、画像结果页 | 打通最小画像闭环 |
| P2 | `type=profile` 导出、画像后台列表、数据字典 | 支持研究查看和导出 |
| P3 | 雷达图、轮次趋势、PCA 图 | 增强可解释性和复测追踪 |
| P4 | 沙盘表达任务、records 表、审计日志 | 进入研究型平台化阶段 |

### 22.4 参考项目借鉴

- FreeCBT：借鉴 CBT 思维记录和非诊断表达，反馈聚焦“想法和模式”，不评价人格；
- Tempo：借鉴日记、情绪标签和本地隐私感，用于记录和周报；
- Nomie：借鉴“文本即数据”和统一 log 思路，用于后续 `records` 表；
- Loop Habit Tracker：借鉴无惩罚打卡和趋势反馈；
- if-me.org：借鉴可信支持者和人工支持网络，用于督导入口；
- Journal Tree：借鉴日记洞察和免责声明，但不在 MVP 1.2 做自由 AI 咨询；
- WeUI Miniprogram：借鉴小程序原生组件体验；
- mindLAMP：借鉴研究型测评、活动配置和数据门户。

### 22.5 明确不纳入 MVP 1.2 的内容

暂缓：

1. AI 自由心理咨询；
2. 语音、视频、人脸数据采集；
3. 正式危机干预系统；
4. 自动潜意识解释；
5. 复杂权限系统；
6. 云数据库迁移；
7. 社群、排名、积分机制。

### 22.6 后续实现前必须同步的文档

一旦开始实现学生画像模块，必须同步更新：

- `docs/API接口文档.md`
- `docs/数据库字段说明.md`
- `docs/量表与工作表接入方案.md`
- `docs/UI与伦理边界验收清单.md`
- `shared/types/api.ts`
- `content/consent.md`
- `content/privacy.md`
- `docs/当前进度交接.md`
- `docs/开发日志.md`
- `docs/开发说明.md`
