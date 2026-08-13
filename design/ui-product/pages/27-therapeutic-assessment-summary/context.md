# 提交前摘要页冻结版

- 方向：方案 A「编辑手帐」，安静、克制、非诊断。
- 主层级：06/08 进度 → 标题与原话保护说明 → 两个版本对照 → 动态保存状态 → 返回/继续。
- 布局：移动端默认纵向堆叠两个文本区，避免双栏压缩长中文；较宽屏才允许双栏。
- 视觉签名：一条克制的“对照脊”连接两个版本标签，只编码对照关系，不作为装饰。
- 组件：复用 Button、PageState，并新增可复用 `TherapeuticComparison` 对照组件（原话/整理双版本）。
- 字体：Noto Sans SC；不使用夸张衬线标题。
- 小字：仅保留真实操作边界、动态状态与空值/错误反馈。
- 禁止：评分、推荐、标签、诊断、AI 头像、聊天气泡、玻璃拟态、渐变堆叠、无功能徽章。

## 状态矩阵

- Default
- Long Original
- Long System Version
- Missing Original
- Missing System Version
- Loading
- Saving
- Offline
- Error / Version Conflict
- Safety Paused
