# 第一次真机验收记录（2026-08-12）

证据目录：`D:\codex\workspace\safehome1.0其他内容\文档图片\真机验收第一次`

本轮按截图时间逐张核对。`pass` 表示该截图未发现需要代码修正的问题；`fix_required` 表示已实施修正，仍需新真机截图复测。未出现在本目录中的页面不冒充已完成真机验收。

| 顺序 | 页面 | 截图 | 结论 | 本轮处理 |
|---|---|---|---|---|
| 1 | 首页 | `bd57442772bb9bf8e073cf4ecf05adb.jpg` | fix_required | 精简阶段反馈区重复小字，只保留真实下一步。 |
| 2–3 | 情绪温度计 | `ea9644e099e6198b1344294170b5ec2.jpg`、`3e425ab1fbd4521c0cc29a99045399d.jpg` | fix_required | 将量尺实现为 `intensity-scale`；空状态不绘制空曲线；移除无职责提示。 |
| 4 | 消息 | `155f19f5d7e565fdb28e064a3ba9f8d.jpg` | fix_required | 消息行实现为 `message-row`；简化页头；底部边界改为竹节短标记。 |
| 5 | 支持性测评列表 | `2e0eec25013bde1aa636c47209ec98a.jpg` | pass | 主操作、分组和边界可读。 |
| 6–9 | 测评结果 | `f7c7fee1ef9712feff93b3a17f1c452.jpg`、`1ad288a14858493da7dab84846398fb.jpg`、`581f677bd3a01ba9661c068ab830b69.jpg`、`bd21445b7f7dc83d260dc0cad48ff34.jpg` | fix_required | 移除主标题下重复结果摘要；分值、维度和非诊断边界保留。系统通知遮挡不计为页面问题。 |
| 10 | 情绪事件记录 | `0f6615de4d630a3da8157871daa29f6.jpg` | pass | 填写顺序、可选区和主行动清晰。 |
| 11 | 三步开始 | `6df08ed8767d9d40f01d1c4c39cadd0.jpg` | fix_required | 删除重复眉题，保留三步任务结构。 |
| 12 | 任务详情 | `ade23841c58f1954b5ef995a05dbaf9.jpg` | pass | 步骤、示例与主行动清晰。 |
| 13 | 练习打卡 | `8242bfbd1c8f5fcd76e24b9197ab18b.jpg` | fix_required | 移除没有信息价值的白色标题卡。 |
| 14 | 人工支持 | `7ea6ac80a05a50a354093ca50c444da.jpg` | fix_required | 移除白色标题卡，保留真实风险边界和提交能力。 |
| 15 | 本周复盘 | `f29814b191e29186b5803542bc2dcc2.jpg` | fix_required | 移除白色标题卡，报告内容与数据语义不变。 |
| 16 | 训练首页 | `f46b299aafc2cb78d256bb6c73d7273.jpg` | pass | 当前推荐、试点和全部训练层级可用。 |
| 17 | 训练卡 | `1bd3cca2607b2f168fe43198b5f408a.jpg` | fix_required | 移除白色标题卡。 |
| 18 | 个性化训练方案 | `e2a4a633c599239d0adb83b1ab7fd5d.jpg` | fix_required | 覆盖全局 `page-head` 卡片样式，标题回到页面层级。 |
| 19 | 项目列表 | `baae332a147cf176ff6cc0038613a9c.jpg` | fix_required | 覆盖全局 `page-head` 卡片样式。 |
| 20–21 | 关系测评结果 | `5549feee50722493238c29704338948.jpg`、`6c4e3ab7d886bf2be191b3887940e91.jpg` | fix_required | 与普通测评结果共用标题摘要修正；长内容保持渐进阅读。 |
| 22 | 关系探索成长 | `a4475dffddfeec5bcad01e8d05a2410.jpg` | fix_required | 时间线实现为 `timeline-record`，删除重复眉题。 |
| 23 | 课程 | `cc26c757bc06089f47db1ec0ee35375.jpg` | pass | 内容主题与入口层级清晰。 |
| 24 | 我的 | `60a03cdceb4cf7a0b81230bf26d12d2.jpg` | pass | 分组和跳转语义一致。 |
| 25–27 | 成长仪表盘 | `2f50b8bd734e376051d955466854b62.jpg`、`959a40ed8795c96575ba71b61c28500.jpg`、`d70545679442f664953b0913b7cf9e1.jpg` | fix_required | 不显示原始 `null`；两类时间线共用 `timeline-record`；不改变记录数量。 |
| 28–30、32–33 | 研究者工作台 | `3f9356f6533dacb349518adacd6a4b3.jpg`、`28f54f6159dc2dcae775112b37a0ca4.jpg`、`09a3d2b3f00ebfe8fee522c86cc500e.jpg`、`d245680b87628e2200e736fe32fa7b0.jpg`、`f01a0d048c1ea568518d65c0ceca708.jpg` | fix_required | 删除重复眉题；压缩开发全权限说明；保留真实权限、队列、参与者、分析任务和项目工作能力。 |
| 31 | 质量与更正 | `373e13722ddf4734417b2499cf0226f.jpg` | fix_required | 无数据且无错误时补明确空状态，避免白屏。 |

## Figma 组件到代码映射

本轮新增并已接入真实页面：

- `IntensityScale` → `components/intensity-scale` → 情绪温度计；
- `MessageRow` → `components/message-row` → 消息；
- `TimelineRecord` → `components/timeline-record` → 成长仪表盘、关系探索成长；
- `ConversationEntry` → `components/conversation-entry` → 支持性问答；
- `QuestionComposer` → `components/question-composer` → 支持性问答；
- `BoundaryNote` → `components/boundary-note` → 支持性问答；
- `SafetyActionRow` → `components/safety-action-row` → 紧急安全指引；
- `ResourceChannelRow` → `components/resource-channel-row` → 现实支持资源。

已存在且继续复用：

- `SectionHeading` → `components/section-title`，本轮更新为竹节短标记；
- `PageStateInline` → `components/page-state`；
- `FeedbackRating` → `components/feedback-rating`；
- `JourneyActionCard` → `components/journey-action-card`；
- `TherapeuticComparison`、`TherapeuticFeedbackLetter`、`TherapeuticCompactTextarea` → `components/therapeutic-flow-step` 的模式变体；
- `Button`、`IconButton`、`TabBarItem` 使用全局按钮与导航样式，不额外包装空壳组件；
- `AuthField`、`SelectField` 使用原生 `input`、`picker` 与页面状态类，避免破坏输入事件和表单语义；
- `EntryRow`、`DualEntry` 已由现有功能入口组件与页面组合实现，不重复制造同义组件。

## 待复测

本轮登记 21/53 个路由，其中 6 个截图结论为 `pass`，15 个路由完成代码修正后仍为 `fix_required`。下一批真机截图应优先覆盖上述 15 个路由；其余未提供截图的页面继续补证据，不写为已通过。
