# 开始前了解页 ImageGen 审查

- 采用图：`assets/imagegen-selected-v1.png`
- 采用：单一选择任务、开放工作纸、明确退出选项、克制进度和底部双操作。
- 采用：第一项选中时只用浅绿底、绿边和圆形标记，不使用插画或安全图标。

## 进入 Figma 前校正

- ImageGen 展示的是 `continue` 已选状态；Figma 还要补未选择、`not_now` 已选、Loading、Offline、Error、Saving、SafetyPaused 与 LongContent。
- 进度值、标题、说明、选项和按钮全部读取现有组件属性，代码不硬编码到页面。
- 底部操作继续使用共享组件现有 `handleBack`、`handleContinue` 和 disabled/loading 逻辑。
- 共享组件还要兼容后续 text、feedback、summary 和 action 模式；本页不为 choice 创建只能使用一次的公共组件。

结论：通过，进入 Figma 组件化复现。
