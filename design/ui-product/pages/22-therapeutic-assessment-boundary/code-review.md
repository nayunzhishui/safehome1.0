# 开始前了解页代码复现审查

## 改动范围

- `apps/miniprogram/components/therapeutic-flow-step/index.wxml`
- `apps/miniprogram/components/therapeutic-flow-step/index.wxss`

仅调整共享步骤组件的进度显示与视觉样式；未修改组件 JS、页面 JS、流程 utility、选项值、事件、路由、草稿或 API。共享样式继续兼容 choice、text、feedback、summary、action。

## Loop 1–4

1. 视觉：进度变为轻量细线；内容区取消浮层阴影；两个选择行和主操作成为唯一视觉重点。
2. UI：选项说明为 25rpx，边界说明为 23rpx；不以缩小字号换取密度；组件无额外装饰与重复卡片。
3. UX：继续、暂不开始、返回、保存、重试与离线语义保持原样；选择态清楚但不制造考试感。
4. 状态：Loading、Saving、Offline、Error、安全暂停、撤回、草稿恢复和长内容兼容性均保留。

## Harness

- 视觉：ImageGen、Figma 与 WXSS 使用同一信息顺序和选择行样式。
- 组件：仅复用选择行、现有按钮和状态组件；没有为复用增加额外结构。
- UX：原有五个组件事件和共享流程状态未变。
- 工程：仅 WXML/WXSS 视觉修改，不触碰后端、API、数据库或核心业务语义。

结论：待本地编译与 Harness 完成后通过；真机统一验收延期。
