# 消息详情页 Figma 视觉审核

结论：`pass`

## 关键节点

- FeedbackRating：`138:69`
- Button Outline：Default `146:69`、Pressed `146:72`、Disabled `146:75`、Loading `146:78`
- Default：`139:1243`
- Loading：`141:1257`
- MissingId：`141:1271`
- LoadError：`141:1285`
- NetworkFailure：`141:1299`
- Saving：`141:1313`
- Evaluated：`141:1327`
- Uncomfortable：`141:1341`
- Withdrawn：`141:1355`
- LongContent：`141:1369`
- 前端实现基准 `get_design_context`：`139:1243`

## ImageGen → Figma

- 保留开放标题、编辑式左线正文、纯绿来源行动、四项共同核对、低强度边界和返回操作。
- 标题从概念稿的夸张比例收敛到 28/36；按钮去除概念稿轻微渐变。
- 长文按真实滚动页面处理，不压缩正文或反馈选项；390 × 844 画板只展示当前视口。

## Harness

- 10 个页面状态均为 390 × 844。
- 相关节点字体仅为 Noto Sans SC Regular / Medium / Bold。
- FeedbackRating、Outline 变体和 10 个页面状态中未发现未绑定变量的实色 Paint。
- 无 placeholder；无回复、聊天、删除、转发、收藏或假紧急入口。
- 唯一自动检查提示是 Loading 组件中空 ActionLabel 的零宽文本；该文本不可见且对应代码“无动作”的真实状态。

## 已修正问题

1. LongContent 初次出现正文与来源按钮重叠：已固定长正文高度并扩大正文容器。
2. Outline 新变体初次未透传 Label / Icon：已在组件源补齐属性引用，页面正确显示“返回消息列表”且无图标。
3. Withdrawn 隐藏来源的错误假设：已按代码真值保留其他独立条件操作。
4. 可读性复核发现评价结果提示为 11px：已将四个 FeedbackRating 结果状态统一修正为 12/18，并同步前端为 24rpx / 1.5 行高。

## 待最终批次

- Android/iOS 真机、读屏、大字体和真实弱网统一延期；当前不登记为已通过。
