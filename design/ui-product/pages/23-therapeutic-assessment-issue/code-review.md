# 我的议题页代码复现审查

## 改动范围

- `apps/miniprogram/components/therapeutic-flow-step/index.wxss`

共享文本框最小高度从 260rpx 调整为 360rpx，使真实页面与 Figma 的书写工作纸一致；行动表单继续由 `.taf-textarea--compact` 保持紧凑。未修改页面 JS、组件 JS、flow utility、API、校验、草稿、路由或提交语义。

## Loop 1–4

1. 视觉：单一书写区是页面主体，进度、标题、双按钮与边界沿用前一步骨架。
2. UI：正文与输入为可读字号；仅保留真实动态草稿状态；第 2 步不重复硬编码边界；无范例卡和装饰组件。
3. UX：用户只需写一个非空问题；自动草稿、返回和继续路径保持原样。
4. 状态：默认、草稿恢复、保存、离线、空值错误、读取错误、安全暂停与长问题已覆盖。

## Harness

- 视觉：ImageGen、Figma 与 WXSS 的大书写区一致。
- 组件：仅新增一个四状态 Textarea 组件，供真实文本步骤复用；没有为复用增加页面内容。
- UX：五个事件、首次 case 创建、十个接口和错误文案未变。
- 工程：共享 WXSS 单点校准，不触碰后端、API、数据库、content、shared 或业务 JS。

结论：待 Preview 与全量 Harness 通过后完成；真机统一验收延期。
