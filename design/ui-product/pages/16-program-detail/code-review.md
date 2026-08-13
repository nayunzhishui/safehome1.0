# 项目详情页代码复现审查

## 改动范围

- `apps/miniprogram/pages/program-detail/index.wxml`
- `apps/miniprogram/pages/program-detail/index.wxss`

未修改 `index.js`、接口、审核、权限、本机草稿、提交载荷、历史读取或核心业务语义。

## Loop 1–4

1. 视觉：多层卡片改为开放章节；真实 session 页签成为唯一显著组件；提交区单独聚焦。
2. UI：正文统一至 28rpx 左右；构念/结果改为内联文本；步骤和历史使用连续分隔行；侧线仅保留在研究只读和安全门槛。
3. UX：先协议后小节再提交；研究者只读提示提前，实际控件仍由原 `wx:if="{{!previewMode}}"` 关闭。
4. 状态：原 Loading、Error 重试、Missing、Submitting、Success、Error、LongContent 与本人记录条件均保留。

## Harness

- 视觉：ImageGen 的手帐结构经功能修正后完整进入 Figma 和 WXSS。
- 组件：前端继续使用原生 button、textarea、slider、checkbox；未引入新依赖或重复业务组件。
- UX：所有原事件、dataset、绑定和按钮名称保持；触控目标不小于 88rpx。
- 工程：`git diff --check`、UI governance 与微信开发者工具 Preview 通过；包体 1,496,039 bytes。

结论：本地通过；真机统一验收延期。
