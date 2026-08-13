# 消息详情页 Figma Gap Analysis

文件：`安心陪伴 UIproduct` / `8vocq2yUvjQavYpaxGotPs`
阶段：P0.a–P0.f 完成

## 可直接复用

- 既有 Primitive、Semantic、Dimension 三个变量集合；不新增 token。
- `Button`、`PageStateInline` 组件集。
- 现有 390 × 844 Screens 画板规则和 Noto Sans SC 字体体系。

## 代码有、Figma 原先缺失

- `feedback-rating` 四项语义选择、保存禁用、已选择说明与“不舒服”人工复核说明。
- `safe-outline-button` 对应的 Outline 按钮视觉状态。
- 消息详情的编辑式正文、撤回正文、条件来源入口和长内容状态。

## 解决方式

- 新增 `FeedbackRating` 六态组件集 `138:69`：Default、Matches、PartlyMatches、DoesNotMatch、Uncomfortable、Saving。
- 在既有 `Button` 组件集补充 Outline 四态：`146:69`、`146:72`、`146:75`、`146:78`；补齐 Label 与 Icon 属性透传。
- Default、Loading、MissingId、LoadError、NetworkFailure、Saving、Evaluated、Uncomfortable、Withdrawn、LongContent 共 10 个画板。

## 冲突与结论

- ImageGen 标题过大：Figma 收敛为 28/36。
- ImageGen 主按钮有轻微明暗变化：Figma 使用纯色 Primary。
- 撤回态最初假设会隐藏来源入口；代码复核确认不会自动隐藏，Figma 与冻结文档已改为服从 `canOpenSource`、`canEvaluate`。
- Loading 的 `PageStateInline` 将空 ActionLabel 保留为不可见零宽文本；它不产生假操作，属于组件当前结构的可接受差异。
