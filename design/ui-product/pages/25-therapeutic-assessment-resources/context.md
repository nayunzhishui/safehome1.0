# 例外与资源页需求冻结

- 目标：让用户用自己的话记录曾经有帮助的时刻或资源。
- 顺序：`04 / 08` → 标题说明 → 提示 → 单一大书写区 → 动态草稿 → 返回/保存。
- 视觉：方案 A 编辑手帐，与前两页连续。
- 复用：TherapeuticTextarea、Button、PageState；不新增卡片、标签、资源推荐或装饰。
- 状态：Default、DraftRestored、Saving、Offline、LoadError、SafetyPaused、LongContent。
- 小字：只保留真实动态状态；删除重复免责声明和说明性填充文案。
- 禁止修改：evidence、scope、幂等、接口、草稿、路由与业务 JS。
