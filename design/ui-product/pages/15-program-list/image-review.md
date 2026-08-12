# 项目测试列表页 ImageGen 审查

采用稿：`assets/imagegen-default-v1.png`

结论：`pass_with_figma_corrections`

- 通过：研究者预览边界、连续项目目录、状态信息、Loading/Error/Empty 与底部边界层级清楚。
- 删除：概念图的“展示开放/待三方审核/已批准试点”筛选栏；代码没有筛选事件。
- 纠正：项目名称、受众、目标构念、小节数和第一节全部绑定真实 `programs`，不采用示例内容。
- 纠正：Empty 使用真实 `availability.message` 与 `pending_review_count`；错误继续由 `page-state` 触发 `loadPrograms`。
- 状态文字只能按 `showcase_open`、`preview_only` 的现有条件生成，不新增审核阶段。
- 字体统一为 `Noto Sans SC`，减少图标和重复粗侧线。
