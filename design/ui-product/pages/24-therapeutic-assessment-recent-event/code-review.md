# 最近一次事件页代码复现审查

## 改动范围

- `apps/miniprogram/components/therapeutic-flow-step/index.wxml`

共享边界说明改为仅在第 1 步显示；第 3 步继续复用已完成的 Textarea、进度、按钮和状态样式。未修改页面 JS、组件 JS、flow utility、evidence 创建、API、scope、幂等、草稿或路由。

## Loop 1–4

1. 视觉：大书写区是唯一主体，与 ImageGen/Figma 一致。
2. UI：只保留动态草稿小字；删除重复免责声明；无多字段与装饰组件。
3. UX：标题说明已经提供足够写作边界，不再增加示例或解释。
4. 状态：默认、草稿、保存、离线、读取错误、安全暂停和长内容完整。

## Harness

- 组件：只复用已有 Textarea、Button、PageState。
- 业务：参与者观察证据及所有接口、事件、草稿、恢复与路由语义不变。
- 工程：仅共享 WXML 展示条件变化，不触碰后端、数据库、content、shared 或业务 JS。

结论：待 Preview 与全量 Harness 通过后完成；真机统一验收延期。
