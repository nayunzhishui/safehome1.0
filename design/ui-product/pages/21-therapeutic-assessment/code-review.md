# 共同理解页代码复现审查

## 改动范围

- `apps/miniprogram/pages/therapeutic-assessment/index.wxml`
- `apps/miniprogram/pages/therapeutic-assessment/index.wxss`

未修改 `index.js`、16 个 API 调用、协作版本、范围确认、共享选择、候选问题、暂停、异议、撤回、更正与投诉、人工反馈、线索、下一小步或幂等提交语义。

## Loop 1–4

1. 视觉：主协作入口、当前协作和问题工作纸前置；治理内容改为连续索引；只使用一个开放转角。
2. UI：正文与输入使用 25–27rpx，辅助文字不小于 24rpx；移除治理卡片墙、重复阴影和机器字段直出。
3. UX：无协作时可开始或直接写问题；有协作时可继续、提交新议题、异议、暂停、撤回或更正；人工反馈后才显示下一小步。
4. 状态：Loading、Notice、Error、NoCase、WaitingHuman、FeedbackReady、Saving、Withdrawn、LongContent 与范围确认均保留。

## Harness

- 视觉：ImageGen 的协作邀请函方向经功能校正后进入 Figma 与 WXSS。
- 组件：继续复用现有按钮；协作摘要、工作纸、政策行保持页面级结构。
- UX：全部原事件、条件、loading/disabled、共享范围和伦理边界保留。
- 工程：`git diff --check`、UI governance、WXSS 通配选择器检查和微信开发者工具 Preview 通过；包体 1,499,842 bytes。

结论：本地通过；真机统一验收延期。
