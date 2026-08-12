# 关系阶段性报告页 ImageGen 审查

采用稿：`assets/imagegen-default-v1.png`

结论：`pass_with_figma_corrections`

- 通过：开放长报告、四步状态、阶段解释优先、反馈核对、相对位置条、矛盾/机制/动态分层与单一导出主按钮。
- 纠正：图中日期、版本、维度值、解释、问题与任务均为示意；Figma 只使用真实字段结构和内容库中的维度标签，不把示意值写入代码。
- 纠正：维度示例使用真实标签，如“主动关系获益信念”“关系行动可控感”“关系行动意愿”“近月关系行动”；不得使用虚构的综合关系评分。
- 纠正：状态步骤不在每一步下附加虚构日期；`generated_at` 只保留为真实报告元信息。
- 纠正：报告标题、画像名、解释、假设、问题与任务均保持动态绑定；Figma 的示例文案只用于验证长文本布局。
- 简化：去掉无功能意义的小图标与三栏密集尾部，把“理解、讨论、任务”改为连续可读章节。
- 状态必须覆盖 Loading、LoadError、DeliveryPending、Delivered、AttentionNotice、SavingFeedback、Exporting、LongContent。
