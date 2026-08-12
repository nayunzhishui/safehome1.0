# 共同理解页 Figma 构建清单

## 画板

1. Ready：无当前协作，主行动“开始一次协作”，保留问题与共享范围表单。
2. Waiting：有当前协作、待人工复核，保留继续、新议题、线索、异议、暂停、撤回和更正入口。
3. Feedback：有经人工复核反馈，额外出现“记录下一小步”。
4. States：Loading、Notice、Error、NoCase、WaitingHuman、Saving、Withdrawn、LongContent。

## 复用与页面级元素

- 复用：Primary Button、Outline Button、语义颜色与文字样式。
- 页面级：协作摘要、问题工作纸、共享范围、政策索引、反馈来源与下一小步。
- 不新增政策卡片组件；“开始前了解”只使用一个低对比开放转角，不重复侧边竖线。

## 功能校正

- 提交文案固定为“提交协作问题”，不推断另一方会收到邀请。
- 所有问题、版本、反馈、线索仅为 Figma 构图示例，代码必须继续使用现有绑定。
- 成人范围确认只在 `activeCase && screening_required` 时出现。
- 下一小步只在 `activeCase.latestFeedback` 时出现。
- 资料与共享保持只读边界，不新增图标入口。
