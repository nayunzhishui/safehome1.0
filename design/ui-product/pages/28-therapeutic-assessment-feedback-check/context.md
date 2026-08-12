# 反馈核对页冻结版

- 方向：方案 A「编辑手帐」，安静、克制、允许保留不同意见。
- 主层级：07/08 进度 → 标题与不同意权说明 → 已发送反馈正文 → 接近程度选择 → 条件式补充输入 → 动态保存状态 → 返回/保存。
- 布局：反馈正文采用一张开放式批注纸；四个选择为紧凑、可扫读的单列选项，不堆叠额外卡片。
- 视觉签名：反馈纸左侧使用一条细窄批注脊及一个短竹节，只编码“待核对文本”，不作装饰。
- 组件：复用 Button、PageState、`TherapeuticChoiceOption`、`TherapeuticTextarea`；反馈正文保持共享 flow 内的简单结构，不新增过度组件。
- 字体：Noto Sans SC；正文保持连续阅读字号和行高。
- 小字预算：只保留四条选项后果与动态保存状态；页头边界不在反馈纸底部重复。
- 禁止：正确答案暗示、满意度星级、诊断标签、AI 头像、聊天气泡、装饰徽章、玻璃拟态、渐变和卡片墙。

## 状态矩阵

- Default / 未选择
- Like Selected
- Partly Like Selected
- Not Like Selected + 必填补充
- Need Time Selected
- Empty Feedback
- Loading / Saving / Offline / Error / Safety Paused
