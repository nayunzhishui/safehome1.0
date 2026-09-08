# 提交前摘要页冻结版

本轮实现：Figma `505:467`，前端已显式接入UIproduct2；状态为 `implemented_pending_final_check`。定向原生编译与事件合同已验证，复杂状态与真机未验收。


## UIproduct2 分步冻结（2026-09-08）

复用当前CONFIG的标题、说明、提示、选项及下一步标签；清朗青瓷、正文30rpx、状态26rpx、触控96rpx。进度对应真实8步骤，不当作健康分。恢复原有description正文（此前已传入但未渲染），放在题干之前而非标题小字。页面逐一Figma后显式ui2启用，公共组件默认保持旧视觉。

保留全部事件、输入上限、登录、草稿、离线、过期/撤回、共享、反馈仅sent可见、行动自愿确认和版本校验，不改共享流程JS或API。选择不自动预选；“不像”继续显示原因输入；摘要保留两种来源；行动表单保持目的、日期、提醒、停止条件与未完成记录。复杂状态统一待最终设备验收。

## 历史冻结


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
