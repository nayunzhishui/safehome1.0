# 注册页实现与 Design QA

状态：`local_ready_device_deferred`
日期：2026-08-10

## 实现范围

- 修改：`apps/miniprogram/pages/register/index.wxml`
- 修改：`apps/miniprogram/pages/register/index.wxss`
- 新增：`apps/miniprogram/assets/icons/chevron-down.svg`（Figma 原始导出）
- 未修改：注册页 JS、API client、后端、数据库、shared、认证与跳转逻辑。

## 功能保护

- 保留用户名、密码、角色、昵称四个字段及原绑定事件。
- 保留 `parent/student`、默认家长、原生 picker、校验阈值、整体 message、loading、Toast、会话写入和 redirect/home 跳转。
- 主按钮仍只有 `loading` 时 disabled；没有擅自禁用输入或角色 picker。
- 成功仍为“已注册”Toast 后跳转，没有新增静态成功页。

## Design QA

### Visual

- PASS：开放式画布、标题层级、326px 字段、52px 控件、44px 按钮、16px 圆角与 Figma 对齐。
- PASS：长度要求从 placeholder 移到持久辅助文字；角色选择有清晰尾部箭头。
- PASS：错误消息左对齐且使用文字说明，不只依赖红色。
- PASS：没有外层大卡片、胶囊按钮、渐变、插画或新增业务说明。

### Behavior

- PASS：字段、picker、提交、登录跳转的绑定名称与 JS 完全一致。
- PASS：Loading、ValidationError、ApiError 的表达与现有数据状态一致。
- PASS：长内容 Figma 状态未发生横向溢出。

### Accessibility

- PASS：四字段均有持久可见标签；用户名和密码有格式说明。
- PASS：picker 增加包含当前值的可访问名称；动态 message 保留 `aria-live=polite`。
- PASS：按钮与输入控件不小于 44px；焦点边框可见。
- MANUAL：200% 大字体、读屏宣读、Android/iOS 原生 picker 与键盘顶起，按总规则留到全部页面完成后的统一真机批次。

## 验证

- 小程序 JS/JSON、资产校验、53 页前端审计通过。
- T23 在 375、430、768、1440 和 100%/200% 组合通过。
- T33 触控、对比度、焦点、表单关联和溢出通过；仅保留项目既有 `miniprogram_page_inventory_drift`。
- 微信开发者工具 `preview` 成功，包体约 1.4 MB，无 WXSS 编译错误。
- `git diff --check` 通过。

## Verdict

本地设计、代码与工程门禁通过。注册页可进入下一页面；真机视觉与辅助技术验收统一后置。
