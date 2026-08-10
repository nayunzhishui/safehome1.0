# 登录页 Figma 视觉与组件审核

审核时间：2026-08-10 17:02（Asia/Shanghai）

## 审核对象

- ImageGen：`assets/imagegen-default-v2.png`
- Figma 文件：`https://www.figma.com/design/8vocq2yUvjQavYpaxGotPs`
- `AuthField`：`58:53`
- 登录状态页：Default `61:803`、Loading `63:823`、Unavailable `64:843`、Error `65:861`、LongContent `66:877`、MustChangePassword `67:893`

## ImageGen → Figma

- 保留开放式编辑布局、左对齐标题、森林绿主行动、细线分隔与橙色隐私提示点。
- 移除整页大卡片、插画、渐变和无功能装饰；未恢复已淘汰的隐私承诺卡。
- ImageGen 的夸张大标题收敛为现有 `Display/Page`，以统一设计系统和真实 390×844 视口；品牌感由留白、标题节奏和单一绿色主行动承担。
- 微信、手机号、账号密码、注册及首次强制改密均与代码真实路径一致。

## 组件审核

- 新增 `AuthField` 组件集，包含 Default、Focused、Filled、Error、Disabled 五个变体。
- 暴露 Label、Content、Message 三个文本属性，并保留 State 变体属性。
- Error 变体使用内容自适应高度，提示文字不再与下一字段重叠。
- 组件内未绑定纯色 paint 数量为 0；颜色、边框和圆角继续复用现有变量。
- 页面按钮全部复用既有 `Button`，未产生第二套按钮样式。

## 状态审核

- 六张状态页均为 390×844。
- 内容底部位置：Default 740、Loading 772、Unavailable 788、Error 772、LongContent 820、MustChangePassword 600，均在视口内。
- Loading 只展示账号密码登录路径加载，其他入口禁用，符合互斥加载逻辑。
- Error 只展示代码已有的整体错误信息，不推断字段级错误。
- Unavailable、LongContent 与 MustChangePassword 使用现有代码文案，没有新增认证能力。

## 结论

Figma 组件、六种页面状态、功能语义和视觉层级审核通过，可作为登录页前端实现基准。真机字体换行与键盘弹起继续按全量后置规则统一验收。
