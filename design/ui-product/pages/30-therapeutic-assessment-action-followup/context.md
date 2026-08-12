# 行动回看页冻结版

- 方向：方案 A「编辑手帐」，像一次诚实回看，不像完成汇报。
- 主层级：标题与非评价说明 → 原行动/目的/停止条件 → 行动状态 → 内容类型 → 回看输入 → 可选训练卡 → 保存。
- 布局：原行动使用开放式行动摘录；状态选择与随访类型各为一组等权按钮；回看输入为主体。
- 视觉签名：行动摘录使用短竹节时间标记，表达“原计划—本次回看”的关联，不使用粗侧边条。
- 组件：复用 Button、PageState、`TherapeuticTextarea` 与等权选择视觉；不新增多余组件。
- 字体：Noto Sans SC；停止条件用正文层级，不缩为脚注。
- 小字预算：只保留输入占位与错误状态；删除页尾重复说明。
- 禁止：成功勋章、奖励绿、完成率、诊断、AI 总结、卡片墙、渐变与玻璃拟态。

## 状态矩阵

- Default / 尝试过 + 新的观察
- Stopped + 仍待了解
- Declined
- Long Action / Multiple Stop Conditions
- Loading / Missing Action / Save Error / Saving
