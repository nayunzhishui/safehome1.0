# 项目详情页 Figma 审查

- 页面：`16 Program Detail`（`201:75`）
- 参与者默认态：`201:76`，截图 `assets/figma-default-v2.png`
- 研究者只读态：`205:1527`，截图 `assets/figma-preview-v1.png`
- 状态矩阵：`201:78`，截图 `assets/figma-states-v1.png`

## 审查结论

- `measurementPlan` 与 `sessions` 已分开；小节页签只映射真实 `sessions`。
- 默认态完整覆盖协议、条件、安全门槛、记录节奏、小节、步骤、书写、反思、完成/停止提示、评分、授权、提交与本人历史。
- 研究者态已移除输入框、草稿保存、反思输入、评分、授权、提交和本人历史，符合真实只读逻辑。
- 状态覆盖 Loading、LoadError、Missing、Submitting、SubmitSuccess、SubmitError、LongContent。
- 仅复用语义一致的 Button 与 PageStateInline；其余为简洁页面级开放结构。
- 145 个文本节点仅使用 Noto Sans SC Regular/Medium；0 个未绑定实色填充。

结论：通过，可进入前端复现。
