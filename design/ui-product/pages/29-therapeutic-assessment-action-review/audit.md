# 一个小行动页审查

## 功能真值

- 路由：`pages/therapeutic-assessment-action-review/index`
- 流程：协作阶段性评估第 8/8 步。
- 唯一任务：在收到已发送反馈后，记录一项自愿、可停止的低压力行动及其回看条件。
- 必填：行动内容 `action_text`、行动目的 `purpose_text`、停止条件 `stop_conditions[0]`、未完成记录方式 `setback_plan`、自愿确认。
- 可选：计划日期 `planned_date`；提醒方式 `reminder_mode` 默认 `none`。
- 固定提交确认：`voluntary_confirmed`、`reversible_confirmed`、`stoppable_confirmed` 均随本人勾选后提交为真。
- 提交：继续复用 `createTherapeuticAssessmentAction`；成功后携带真实 `caseId`、`actionId` 进入行动回看页。
- 保留状态：未收到已发送反馈、读取、离线、草稿恢复、校验错误、保存、版本冲突、安全暂停。

## 业务保护

- 不删除任何必填字段，不把默认停止条件或未完成记录方式变成不可编辑说明。
- 不把完成次数、日期或提醒包装成疗效承诺、任务压力或惩罚。
- 不新增系统推荐行动、AI 代写、自动日期、积分、连续打卡或诊断标签。
- 不修改 participant flow、API、数据库、后端、字段、幂等或路由语义。

## 小字审查

- 保留：可选日期标记、提醒当前值、输入占位、动态保存状态、确认语句和错误恢复信息；均直接影响填写或提交。
- 删除/禁止：行动意义宣传、完成益处、重复非诊断免责声明、机器字段、版本号、装饰性提示。
- 标题中的“完成次数不代表疗效”是本页新增行动行为的必要限制，只出现一次。
