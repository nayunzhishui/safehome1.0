# 反馈核对页审查

## 功能真值

- 路由：`pages/therapeutic-assessment-feedback-check/index`
- 流程：协作阶段性评估第 7/8 步。
- 唯一任务：阅读最近一份已发送反馈，选择其与自身体验的接近程度；选择“不像”时补充不一致之处。
- 动态内容：`feedbackTitle`、`feedbackContent`、`feedbackLayerLabel` 来自最近一份 `status === "sent"` 的反馈版本。
- 四个真实选项：`like`、`partly_like`、`not_like`、`need_time`。
- 提交：继续复用 `respondToTherapeuticAssessmentFeedback`，提交 `recognition` 与可选 `disagreement_note`。
- 主操作：`保存我的核对`；次操作：`上一步`。
- 保留状态：无已发送反馈、读取、离线、草稿保存、错误/版本冲突、安全暂停。

## 业务保护

- 不同意或需要时间不得被表现为错误，也不得被视觉弱化。
- 只有选择“不像”时要求填写不一致之处；其他选项不新增输入负担。
- 不展示未发送、未复核草稿，不增加评分、诊断、自动采纳或 AI 解释。
- 不修改 participant flow、API、数据库、后端、字段或路由语义。

## 小字审查

- 保留：四个选项各自的真实后果、动态草稿状态、“不像”输入提示、无反馈/离线/错误恢复信息。
- 删除：反馈卡底部“可讨论、可不同意、可修订”的固定重复说明；页头已完整表达同一操作边界。
- 禁止：模型能力宣传、机器字段、版本号、内部状态、装饰性标签和重复免责声明。
