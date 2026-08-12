# 关系探索试点页代码复现审查

## 改动范围

- `apps/miniprogram/pages/relationship-pilot/index.wxml`
- `apps/miniprogram/pages/relationship-pilot/index.wxss`

未修改 `index.js`、登录校验、角色门槛、报名接口、进度读取、埋点、路由或核心业务语义。

## Loop 1–4

1. 视觉：报名与进度页面改为开放章节；当前行动卡保留聚焦；五阶段路径使用轻量竹节语义。
2. UI：正文与辅助文字提高到 24–28rpx；减少层叠卡片和侧边线；其它入口改为连续分隔行。
3. UX：首屏先解释边界，再展示当前唯一主要动作；报名、测评补充入口和后续阶段不互相争抢注意力。
4. 状态：原 Loading、RoleBlocked、EnrollmentRequired、Submitting、Enrolled、Error 与 LongContent 语义均保留。

## Harness

- 视觉：ImageGen 的竹节方向经功能校正后进入 Figma 与 WXSS，报名态和已报名态保持一致。
- 组件：仅继续复用原 JourneyActionCard；竹节路径不抽象为一次性公共组件。
- UX：所有原事件、dataset、绑定和按钮文案保持，主要触控区不小于 88rpx。
- 工程：`git diff --check`、UI governance、WXSS 通配选择器检查与微信开发者工具 Preview 通过；包体 1,496,466 bytes。

结论：本地通过；真机统一验收延期。
