# 项目测试列表页代码复现审查

## 改动范围

- `apps/miniprogram/pages/program-list/index.wxml`
- `apps/miniprogram/pages/program-list/index.wxss`

未修改 `index.js`、API、权限、数据库、后端、审核条件或跳转语义。

## Loop 1–4

1. 视觉一致性：复现 Figma 的开放页头、研究预览边界、连续项目目录、轻量箭头和底部边界说明。
2. UI 细节：正文不小于 28rpx，状态与构念不小于 24rpx；移除卡片墙与构念胶囊；整行点击区大于 88rpx。
3. UX：继续使用真实 `openProgram`、`data-id`、`data-preview`；不增加筛选、报名、收藏、评分或进度。
4. 页面状态：保留 Loading、Error 重试、Empty、`availability.message` 与 `pending_review_count`。

## Harness

- 视觉：ImageGen → Figma → WXML/WXSS 的信息层级一致；无无效筛选栏。
- 组件：继续复用全局 `page-state`，未新增重复业务组件或依赖。
- UX：项目行有按压反馈、可访问名称与明确箭头；研究草案不伪装为正式项目。
- 工程：`git diff --check`、UI governance 与微信开发者工具 Preview 通过；包体 1,495,198 bytes。

结论：本地实现通过，真机验收按统一批次延期。
