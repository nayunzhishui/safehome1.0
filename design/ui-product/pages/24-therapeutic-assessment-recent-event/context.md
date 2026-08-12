# 最近一次事件页需求冻结

- 页面目标：低压力记录一个真实具体片段，避免过早解释。
- 信息顺序：`03 / 08` → 标题说明 → 记录提示 → 大书写区 → 草稿状态 → 返回/保存 → 边界。
- 视觉：方案 A 编辑手帐；保持前两步连续性，输入区仍是唯一主体。
- 复用：TherapeuticTextarea、Button、PageState；不新增卡片、标签、情绪量尺或装饰。
- 状态：Default、DraftRestored、Saving、Offline、LoadError、SafetyPaused、LongContent。
- 小字：只保留草稿状态和边界说明，不堆叠操作提示。
- 禁止：修改 evidence 语义、scope、幂等、API、草稿、校验、路由或业务 JS。
