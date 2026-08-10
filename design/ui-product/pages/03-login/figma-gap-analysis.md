# 登录页 Figma Phase 0 差距分析

记录时间：2026-08-10 16:29（Asia/Shanghai）

## P0.a 代码真值

- 默认态包含微信一键登录、手机号快捷登录、账号密码登录与注册入口。
- 首次强制改密态包含临时密码、新密码、确认密码和唯一提交动作。
- 必须保留能力不可用、加载、错误、长文案和强制改密状态。
- 不新增忘记密码、验证码、游客登录、自动注册或新的认证接口。

## P0.b Figma 现状

- 已有 3 个变量集合、41 个变量、7 个文字样式和 2 个阴影样式，可直接复用。
- 已有 `Button` 组件集，包含 Brand、Primary、Secondary、Text 与 Loading/Disabled 等状态。
- `03 Screens` 已有首页与情绪记录页状态，没有登录页。
- 本地组件库没有输入字段组件。

## P0.c 远程组件检索

- 当前文件未订阅远程库。
- 已在可用的 Simple Design System 中检索输入/密码字段，未返回可复用资产。
- Material 3 的视觉、token 和组件 API 与本项目“温润编辑感”不一致，不导入。

## P0.d v1 范围锁定

- 复用现有 variables、text styles 与 `Button`。
- 新建本地 `AuthField` 组件集，覆盖 Default、Focused、Filled、Error、Disabled。
- 新建登录页 Default、Loading、Unavailable、Error、LongContent、MustChangePassword 六种状态。
- 不创建插画、隐私承诺卡、忘记密码入口或代码中不存在的交互。

## P0.e 代码到 Figma 冲突处理

- ImageGen v2 的开放式编辑布局保留；真实快捷登录与账号密码路径必须完整落入 Figma。
- ImageGen 不足以表达全部状态，Figma 增补的状态只来自现有代码分支，不构成功能扩展。
- Figma 使用已批准的 Noto Sans SC；小程序代码继续保留系统中文字体栈，最终真机批次核对换行。

## P0.f 结论

差距只有一个可复用输入字段组件和六张登录状态页。现有 token 与按钮足够，不新增全局 token，不引入远程库。
