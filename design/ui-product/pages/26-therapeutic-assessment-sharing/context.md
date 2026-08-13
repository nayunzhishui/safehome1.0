# 资料与共享页需求冻结

- 目标：让用户清楚选择本轮共享范围，并知道可后续修改或撤回。
- 顺序：`05 / 08` → 标题说明 → 共享问题 → 三个选择行 → 动态草稿 → 返回/保存。
- 视觉：方案 A 编辑手帐；不使用锁、盾牌、权限表或协议卡片。
- 复用：ChoiceOption、Button、PageState；不新增组件。
- 状态：Default、QuestionOnly、QuestionAndEvent、PauseSharing、Saving、Offline、VersionConflict/Error、SafetyPaused、LongContent。
- 小字：选项说明承担真实范围差异，属于必要信息；删除重复免责声明和机器字段。
- 禁止修改：选项值、scope 映射、expected version、幂等、API、草稿、校验、路由和业务 JS。
