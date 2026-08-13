# Figma 组件化复现审查（2026-08-12）

## 结论

- 53 个微信小程序页面均已在 `03 Screens` 找到对应真实画框；每个画框至少包含一个组件实例，不再以整页静态截图代替组件化复现。
- `02 Components / 00 Component Library Overview`（节点 `342:77`）已增加 `05 SafeHome Application Components`（节点 `368:57`）。该分区展示 4 个真实实例：`TrainingTaskCard`、`FunctionEntryCard`、`SectionTitle`、`BottomTipCard`。
- 竹子语言继续使用短竹节、竹节节点和阶段分段；未新增贯穿页面的长绿线、竹林插画或虚构成长百分比。

## 本轮修正

- 首页 `30:2`：居中主标题，保留真实功能层级和组件实例。
- 情绪记录 `316:1571`：普通圆点直线替换为 `BambooTimelineNode` 实例。
- 训练 `192:3`、个性化方案 `194:3`：修复组件替换后的遮挡和旧静态层残留。
- 测评历史、训练卡、成长页、质量与更正等代表页面已复核组件实例和竹节位置。
- 注册表中的关系成长、共同理解、质量与更正链接改为实际页面画框节点，不再指向页面容器。

## 小程序映射

- `FunctionEntryCard` → `components/function-entry-card`，首页双入口通过 `dual-entry` 复用。
- `TrainingTaskCard` → `components/training-task-card`，训练、推荐训练卡和个性化方案复用。
- `AssessmentWorksheetCard` → `components/assessment-worksheet-card`，测评目录和测评历史复用。
- `BambooTimelineNode` → `components/bamboo-timeline-node`，情绪记录与成长时间线复用。
- `GrowthSegment` → `components/growth-segment`，成长仪表盘按真实分类切换。
- `SectionTitle`、`BottomTipCard` → 同名小程序组件，用于需要明确分区或底部提示的页面。

## 验收边界

- 本轮完成结构性组件复现与代表页面截图审查，不宣称 53 页全部状态已完成真机像素级验收。
- 用户统一真机验收仍是最终视觉判断；本轮没有修改后端、API、数据库或核心业务语义。
