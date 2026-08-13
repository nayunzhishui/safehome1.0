# 注册页 Figma 视觉审查

状态：`passed`
日期：2026-08-10
Figma：`https://www.figma.com/design/8vocq2yUvjQavYpaxGotPs`

## 组件复现

- 新增私有 `__Icon/ChevronDown`（`73:55`），直接由 SVG 路径创建，没有旋转或拼接线段。
- 新增 `SelectField` 组件集（`77:57`）：Default、Focused、Error、Disabled。
- `SelectField` 暴露 Label、Value、Message、Icon 属性，使用现有颜色、间距、圆角与文字样式。
- 结构审计结果：4 个变体、0 个未绑定 SOLID fill/stroke，字体全部为 Noto Sans SC。

## 页面状态

| 状态 | 节点 | 功能边界 |
|---|---|---|
| Default | `80:907` | 家长默认角色，空表单 |
| StudentSelected | `83:929` | 仅把原生 picker 值切为学生 |
| Loading | `83:989` | 显示“正在注册...”，仅提交按钮 loading/disabled |
| ValidationError | `83:1034` | 使用真实用户名长度错误，页面级反馈 |
| ApiError | `83:1081` | 使用后端真实“该用户名已被使用” |
| LongContent | `83:1132` | 长用户名、密码和昵称溢出检查 |

## ImageGen → Figma 对照

- 保留开放式象牙白画布、SafeHome 品牌、创建账号标题和真实角色边界说明。
- 字段顺序严格为用户名、密码、角色、昵称；长度说明持续可见。
- 角色继续是选择字段，不改为角色卡或分步流程。
- 仅一个绿色主行动，登录为文字次行动；无大卡片、渐变、插画或装饰徽章。
- 输入框 326 × 52、按钮 342 × 44、圆角 16、画板 390 × 844 与冻结稿一致。
- 首次截图发现长度说明居中，已修正为字段左对齐后重新截图。

## 截图证据

- `assets/figma-default.png`
- `assets/figma-student.png`
- `assets/figma-loading.png`
- `assets/figma-validation-error.png`
- `assets/figma-api-error.png`
- `assets/figma-long-content.png`

结论：Figma 通过，可作为注册页前端实现基准。
