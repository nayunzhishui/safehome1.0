# 训练页代码 Loop 与 Harness

日期：`2026-08-11`

结论：`local_pass_device_acceptance_deferred`

## 实现

- 仅修改 `index.wxml` 与 `index.wxss`；三个现有组件、全部条件字段、事件、ID/tags、JS、API 和缓存保持。
- 最近推荐移到第一重点区；关系试点、3 天计划、起步路径和训练库改为连续编辑目录。
- 训练库仍由 `section-title`、`training-task-card`、`bottom-tip-card` 复用渲染。

## Loop 1–4

- 视觉：ImageGen、Figma、代码均取消卡片墙、渐变与重复粗侧线，使用开放标题、细分隔线和一个重点推荐区。
- UI：正文不低于 28rpx，短标签不低于 24rpx；主要按钮不低于 88rpx；小屏入口与三步改为单列。
- UX：动态推荐存在时成为第一行动；展开计划和浏览训练保持次级；条件内容不伪装为固定能力。
- 状态：保留试点、推荐、计划、计划展开、训练库展开与登录门禁；未伪造 Loading/Error/完成度。

## Harness

- Figma `192:3` 截图审查通过。
- 微信开发者工具 Preview 编译通过，包体 `1,493,096 bytes`。
- UI governance、`git diff --check` 与 WXSS 通配选择器检查通过。
- 未修改 main、后端、API、数据库、content、shared、认证或核心业务语义。
- 真机统一验收延期到全部页面本地完成之后。
