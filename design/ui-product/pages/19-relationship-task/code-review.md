# 关系探索任务页代码复现审查

## 改动范围

- `apps/miniprogram/pages/relationship-task/index.wxml`
- `apps/miniprogram/pages/relationship-task/index.wxss`

未修改 `index.js`、本机草稿、离开提醒、触摸绘制、折叠题、授权校验、幂等提交、风险转人工、埋点、API、后端或数据库。

## Loop 1–4

1. 视觉：页头改为开放工作纸；画布成为唯一大视觉面；句子情境改为连续题行；授权和提交统一收束。
2. UI：正文与输入提高到 26–28rpx；保存状态、计数与辅助说明提高到 24–25rpx；工具按钮与提交保持足够触控高度。
3. UX：绘画、画外音、句子补全均保留原顺序；草稿恢复只在真实条件出现；可跳题、授权范围和非解释边界清楚。
4. 状态：DrawingEmpty、DrawingWithDraft、SentenceDefault、SentenceAnswered、SavingLocal、LocalSaveError、Submitting、ValidationToast、RiskEscalated、LongContent 均保留。

## Harness

- 视觉：ImageGen 的双模式工作纸经功能校正后完整进入 Figma 和 WXSS。
- 组件：前端继续使用原生 canvas、textarea、button、checkbox；没有为单页画布或题行新增公共组件。
- UX：全部原事件、dataset、字符限制、disabled/loading 与风险提示保持；按钮触控高度不小于 88rpx。
- 工程：`git diff --check`、UI governance、WXSS 通配选择器检查与微信开发者工具 Preview 通过；包体 1,497,926 bytes。

结论：本地通过；真机统一验收延期。
