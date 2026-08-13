# 例外与资源页 Figma 审查

- Figma 页面：`264:6`
- 默认态：`264:7`
- 草稿恢复态：`264:34`
- 状态板：`264:59`

## 结果

- 保持一个资源回想输入，没有拆成人物/做法/环境卡片，也没有标签、推荐或 AI 解释。
- 只复用 `TherapeuticTextarea` 和现有 Button；动态草稿状态保留，重复固定边界不显示。
- Default、DraftRestored、Saving、Offline、LoadError、SafetyPaused、LongContent 已覆盖。
- 三个根节点只使用 Noto Sans SC Regular/Medium；未绑定填充 0、未绑定描边 0、占位符 0。

结论：Figma 通过，可直接复用共享文本步骤实现。
