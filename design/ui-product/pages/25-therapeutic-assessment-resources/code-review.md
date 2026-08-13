# 例外与资源页代码复现审查

## 实现范围

本页直接使用已经完成并编译通过的 `therapeutic-flow-step` 文本模式：进度、Textarea、动态草稿、返回、保存和 PageState 均已真实实现，无需增加页面级 WXML/WXSS 或硬编码文案。

未修改页面 JS、组件 JS、flow utility、evidence、API、scope、幂等、草稿或路由。

## Loop 1–4

1. 视觉：ImageGen、Figma 与共享 Textarea 页面一致。
2. UI：仅保留动态草稿小字；无标签、卡片和重复说明。
3. UX：用户只需回想并记录，不被系统推荐干扰。
4. 状态：默认、草稿、保存、离线、读取错误、安全暂停和长内容完整。

## Harness

- 组件：只复用现有 Textarea、Button、PageState，没有为复用增加内容。
- 业务：观察证据、事件、接口、草稿和恢复语义完整。
- 工程：无页面级代码增量，不触碰后端、数据库、content、shared 或业务 JS。

结论：待 Preview 与全量 Harness 通过后完成；真机统一验收延期。
