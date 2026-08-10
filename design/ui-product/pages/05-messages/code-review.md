# 消息页前端实现与 Loop/Harness 审核

结论：`local_complete_device_deferred`
路由：`pages/messages/index`
Figma：`90:1034` 及同族七态

## 修改范围

- `apps/miniprogram/pages/messages/index.wxml`
- `apps/miniprogram/pages/messages/index.wxss`
- `apps/miniprogram/pages/messages/index.json`
- `index.js` 未修改；后端、API、数据库、content、shared 未修改。

## 功能保护

- `onShow → loadMessages → GET /api/messages?page=1&page_size=50` 未变。
- `openMessage` 的消息 ID 和详情跳转未变；详情读取的自动已读语义未动。
- 未读、已读、撤回、研究者来源、创建时间和交付版本仍使用真实返回字段。
- 登录失效、普通重试、诊断复制和 Toast 行为未变。
- 未新增搜索、筛选、分页、全部已读、删除、回复、聊天或未读统计。
- WXML 将 Loading、Error、List、Empty 重组为同一连续条件链，避免加载时旧列表/空态同时渲染；只修正显示互斥，不改变 JS 判断。

## ImageGen / Figma / 代码映射

| 设计要点 | Figma | 小程序实现 |
|---|---|---|
| 开放式标题 | 28/36，24px 左右边距 | 56/72rpx，48rpx 左右边距 |
| 连续列表 | 16px 圆角、1px 边界、无阴影 | 32rpx 圆角、1rpx 边界、无阴影 |
| 消息行 | 20px 内边距、分隔线 | 40rpx 内边距、1rpx 分隔线 |
| 未读 | 4×64px 短线 + 粗标题 + 文字状态 | 8×128rpx 短线 + 700 字重 + “未读” |
| 已撤回 | Subtle 背景、Muted 文字 | `--safe-bg-soft` 与 `--safe-muted` |
| 边界说明 | 无卡片、左侧短线 | 本页原生结构，移除通用卡片容器 |
| 错误诊断 | Error state + Diagnostic | 复用 `page-state`，保留复制按钮 |

## Loop 1：视觉一致性

- ImageGen v2、Figma 默认态和 WXML/WXSS 的模块顺序、状态语言、间距、字级、颜色和圆角逐项对应。
- Figma 七态截图已保存；微信开发者工具 Preview 编译成功，包体 1,487,732 bytes。
- 本轮未采集模拟器/真机页面截图；按冻结规则只登记为本地代码映射通过，Loop 5 统一后置。

## Loop 2：UI 细节

- 正文 28rpx；辅助信息、状态和诊断文字均不低于 24rpx。
- 整行点击区域远大于 88rpx；诊断复制按钮最小 88rpx。
- 正常态只有一个列表强容器；没有英雄卡、嵌套卡片、阴影、渐变或装饰图标。
- 340px 以下元信息改为纵向排列，避免时间、版本与状态横向挤压。

## Loop 3：UX

- 首次进入可立即识别唯一任务“查看消息”；整行点击进入详情。
- 未读、已读和撤回均有文字提示，状态不只依赖颜色。
- 登录失效进入登录页并保留 redirect；网络/服务错误提供重新加载和诊断复制。
- 空状态不增加当前不存在的行动；底部持续说明不是紧急帮助渠道。

## Loop 4：状态

- Figma：Default、Loading、Empty、Error、LoginRequired、LongContent、NetworkFailure 全部覆盖。
- Disabled/Selected 不适用于只读列表，未伪造。
- LongContent 使用自然高度和 `overflow-wrap`；小屏元信息可换列。

## Accessibility

- 页面主区域和每条消息都有可理解的 aria-label；错误/加载继续由 `page-state` 的 `role=status`、`aria-live=polite` 宣读。
- 未读同时使用短线、字重和文字；错误同时使用标题、说明和恢复动作。
- 已知 token 对比度、触控、焦点、溢出和 reduced motion 自动项通过。
- 200% 字体、读屏顺序、Android/iOS 真实触控与动态内容宣读仍需最终真机人工验证，不能据静态检查宣称 WCAG 完全通过。

## Harness

- 视觉：Figma 390×844 七态、Noto Sans SC、0 个未绑定实色；代码尺寸逐项映射。
- 组件：Figma 新增合法 `MessageRow` 三态；代码继续复用真实循环和 `page-state`，未新增组件文件或样式分叉。
- UX：唯一主任务、状态恢复、非颜色线索、触控和边界文案通过。
- 工程：资产审计、53 页前端审计、T23 375/430/768/1440 × 100%/200%、真值与工程 Harness、微信 Preview、`git diff --check` 通过。
- T33 仅保留项目既有 `miniprogram_page_inventory_drift`；不是消息页新增问题。
- T23 首次因未解析到 Playwright 中断，改用 Codex 自带 `NODE_PATH` 重跑后通过；未安装依赖。

## 待最终批次

- Android/iOS、系统大字体、读屏、弱网与真实消息数据滚动。
- 全部页面本地完成后合并当时 main，再全量回归并启动 Loop 5。

