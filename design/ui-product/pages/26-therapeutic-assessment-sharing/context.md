# 资料与共享页需求冻结

本轮实现：Figma `503:450`，前端已显式接入UIproduct2；状态为 `implemented_pending_final_check`。定向原生编译与事件合同已验证，复杂状态与真机未验收。


## UIproduct2 分步冻结（2026-09-08）

复用当前CONFIG的标题、说明、提示、选项及下一步标签；清朗青瓷、正文30rpx、状态26rpx、触控96rpx。进度对应真实8步骤，不当作健康分。恢复原有description正文（此前已传入但未渲染），放在题干之前而非标题小字。页面逐一Figma后显式ui2启用，公共组件默认保持旧视觉。

保留全部事件、输入上限、登录、草稿、离线、过期/撤回、共享、反馈仅sent可见、行动自愿确认和版本校验，不改共享流程JS或API。选择不自动预选；“不像”继续显示原因输入；摘要保留两种来源；行动表单保持目的、日期、提醒、停止条件与未完成记录。复杂状态统一待最终设备验收。

## 历史冻结


- 目标：让用户清楚选择本轮共享范围，并知道可后续修改或撤回。
- 顺序：`05 / 08` → 标题说明 → 共享问题 → 三个选择行 → 动态草稿 → 返回/保存。
- 视觉：方案 A 编辑手帐；不使用锁、盾牌、权限表或协议卡片。
- 复用：ChoiceOption、Button、PageState；不新增组件。
- 状态：Default、QuestionOnly、QuestionAndEvent、PauseSharing、Saving、Offline、VersionConflict/Error、SafetyPaused、LongContent。
- 小字：选项说明承担真实范围差异，属于必要信息；删除重复免责声明和机器字段。
- 禁止修改：选项值、scope 映射、expected version、幂等、API、草稿、校验、路由和业务 JS。
