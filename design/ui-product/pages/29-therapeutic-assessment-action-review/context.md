# 一个小行动页冻结版

- 方向：方案 A「编辑手帐」，像一页可修改的行动便笺，不像任务管理器。
- 主层级：08/08 进度 → 标题与可停止边界 → 行动/目的 → 日期/提醒 → 停止与回看 → 自愿确认 → 动态保存 → 返回/记录。
- 布局：按“想做什么—怎样安排—何时停下”三段组织，但不增加卡片套卡片；日期与提醒在宽度允许时并列。
- 视觉签名：三段之间使用短竹节分隔线，表达步骤关系，不使用连续粗侧边条。
- 组件：复用 Button、PageState、`TherapeuticTextarea` 与现有输入/选择视觉；不为每个字段创建新组件。
- 字体：Noto Sans SC；字段标签与输入正文保持可读层级。
- 小字预算：仅可选标记、输入占位、动态保存状态和自愿确认；不出现解释性脚注。
- 禁止：任务积分、完成率、倒计时、AI 推荐、装饰插画、卡片墙、渐变、玻璃拟态和疗效暗示。

## 状态矩阵

- Empty Form / Disabled Continue
- Filled / Confirmed
- Draft Restored
- Validation Error
- Loading / Empty Feedback / Saving / Offline / Version Conflict / Safety Paused
