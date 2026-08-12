# 我的议题页 Figma 审查

## 复现结果

- Figma 页面：`259:6`
- 默认态：`259:7`
- 草稿恢复态：`259:47`
- 状态板：`259:85`
- 复用组件：`TherapeuticTextarea` 组件集 `258:85`，四状态 `258:77`、`258:79`、`258:81`、`258:83`

## 一致性与修正

- 保留 ImageGen 的单一大书写区，标题已缩回现有 H1，主按钮改用现有纯色 token，进度顺序与第 22 页一致。
- 首轮自审发现 Auto Layout 将文本框压成单行，已在组件源与实例上修正为固定书写高度并重新截图。
- 页面只复用 Textarea 与现有 Button；没有范例、标签、聊天气泡、插画或额外小字。
- Default、DraftRestored、Typing/Saving、Offline、ValidationError、LoadError、SafetyPaused、LongContent 均有证据。
- 三个根节点仅使用 Noto Sans SC Regular/Medium，未绑定填充 0、未绑定描边 0、占位符 0。
- 按新增门禁移除第 2 步重复硬编码边界；只保留真实动态草稿状态。

结论：Figma 通过，可以进入共享组件代码校准。
