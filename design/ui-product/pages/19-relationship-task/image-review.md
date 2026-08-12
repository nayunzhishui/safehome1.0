# 关系探索任务页 ImageGen 审查

采用稿：`assets/imagegen-variants-v1.png`

结论：`pass_with_figma_corrections`

- 通过：绘画与句子补全两个真实模式分屏；画布优先、连续折叠题、授权/边界/提交收束清晰。
- 删除：工具按钮中的图标；现有前端只有撤销、重做、清空文字，不新增图标资源。
- 纠正：恢复草稿提示只在 `draftRestored` 为真时出现，不能和普通保存状态固定并列。
- 纠正：绘画画布在 Figma 中只用不具象的线条验证笔迹层次，代码仍由真实触摸坐标绘制。
- 纠正：七个句子情境严格使用现有 `CONTEXTS`；默认只展开第一题，已回答题由真实 `answered` 状态标记。
- 保留：字符计数、可跳过、授权原文、非解释边界、单一提交按钮与保存/提交状态。
- 状态必须覆盖 DrawingEmpty、DrawingWithDraft、SentenceDefault、SentenceAnswered、SavingLocal、LocalSaveError、Submitting、ValidationToast、RiskEscalated、LongContent。
