# 开始前了解页 Figma 审查

## 复现结果

- Figma 文件：`8vocq2yUvjQavYpaxGotPs`
- 页面：`253:6`
- 默认态：`253:7`
- 继续态：`254:66`
- 暂不开始态：`254:93`
- 状态板：`254:125`
- 复用组件：`TherapeuticChoiceOption`，组件集 `252:89`

## 一致性检查

- 延续 ImageGen 的安静协作邀请方向：进度、标题、两个选择、双按钮和边界说明构成唯一阅读路径。
- 默认态与两种选择态共用同一选择行组件，没有新增卡片墙、插画、竹子或装饰图标。
- Loading、Offline、Error、Saving、SafetyPaused、LongContent 已独立呈现，长文本允许自然增高。
- 四个根节点均只使用 Noto Sans SC Regular/Medium；未绑定颜色为 0，未绑定描边为 0，占位文本为 0。
- 小字仅用于进度与边界说明，正文、选项和操作文字保持可读层级。

结论：Figma 通过，可以进入共享组件的前端视觉复现。
