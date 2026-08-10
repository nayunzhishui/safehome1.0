# 支持性问答页 Figma Phase 0 缺口分析

状态：`complete`
日期：2026-08-10
路由：`pages/support-assistant/index`

## Phase 0 Checklist

| 任务 | 状态 | 证据与结论 |
|---|---|---|
| P0.a 代码与视觉真值 | 完成 | 已核对 WXML、WXSS、JS、全局 tokens、功能真值、冻结稿和 ImageGen；页面无图片、头像或图标资产依赖 |
| P0.b Figma 当前文件盘点 | 完成 | 连接恢复后实读确认 5 个页面、3 个变量集、41 个变量、7 个文本样式、2 个效果样式，均与状态账本一致 |
| P0.c Code Connect 与库搜索 | 完成 | 小程序目录无相关映射；文件未订阅外部库；`Boundary Note`、`Conversation Entry`、`Textarea` 搜索均无兼容组件 |
| P0.d v1 范围锁定 | 完成 | 复用 Button、PageStateInline 与现有 token；只新增 BoundaryNote、ConversationEntry；页面工作区保持本页组合，不新增业务组件 |
| P0.e 代码到 Figma 映射 | 完成 | 所有状态、动作和动态字段均已映射；不改变 API、JS、同意版本、会话或引用语义 |
| P0.f 缺口结论 | 完成 | 没有产品决策分叉；复用本地 Button/PageStateInline，只新增 BoundaryNote 与 ConversationEntry |

## 来源真值

- 产品字体：小程序使用 `-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif`；本 Figma 文件既有约定为 `Noto Sans SC`，仅作为可编辑中文设计字体，不修改代码字体栈。
- 页面尺寸：390 × 844；内容左右边距 24px；内容自然纵向滚动。
- 颜色、间距、圆角必须复用现有 Primitive、Semantic、Dimension 变量；禁止新建平行 token。
- 页面不含图片。ImageGen 只作为构图与层级参考，不作为整图铺底。

## 组件映射

| 页面元素 | Figma 处理 | 原因 |
|---|---|---|
| 主行动、禁用与发送中按钮 | 复用 `Button` | 已有组件能覆盖唯一主行动，不产生按钮分叉 |
| Loading、配置错误、关闭态、网络失败 | 复用 `PageStateInline` | 延续现有页面状态语义与组件体系 |
| 使用边界与同意结果 | 新建 `BoundaryNote` | 这是跨敏感功能可复用的“边界 + 状态/行动”模式，现有卡片组件不承载同意语义 |
| 用户问题、助手回答与引用 | 新建 `ConversationEntry` | 需要编辑式全宽阅读结构，不能复用聊天气泡或消息列表组件 |
| 问题输入工作区 | 页面级 Auto Layout 组合 | 当前只出现一次；由标签、计数、textarea 外观、内联错误和 Button 组成，暂不制造单页专用组件 |
| 引用列表 | `ConversationEntry` 的文本属性与显示开关 | 真实代码支持任意条目；Figma 用多行文本表达典型长内容，不伪造固定数据模型 |

## 新组件 v1 范围

### BoundaryNote

- 变体：`State=ConsentPending`、`State=Consented`。
- 文本属性：`Title`、`Body`、`Status`。
- Pending 内部复用 Button；Consented 使用勾选状态与“已记录本次选择”，颜色外同时提供文字与图形。
- 使用 1px 绿色灰边、16px 圆角、无阴影。

### ConversationEntry

- 变体：`Role=User`、`Role=Assistant`。
- 属性：`RoleLabel`、`Body`、`ShowSources`、`Sources`。
- 全宽纵向结构；不使用头像、左右气泡、渐变或投影。
- Assistant 可显示“参考内容”及多行来源；User 默认隐藏来源。

## 页面状态范围

1. Loading
2. ConfigError
3. Disabled
4. ConsentPending
5. Ready
6. Sending
7. Conversation
8. InlineError
9. LongContent
10. NetworkFailure

每个状态必须严格对应现有 JS 条件；Disabled 不出现输入能力，ConsentPending 不出现可发送主行动，Sending 使用禁用态且不增加打字动画。

## 代码与 Figma 冲突处置

- 旧代码将标题、边界、每条消息和输入区都做成带阴影卡片；冻结方案和 ImageGen 改为开放式标题、两处必要容器及编辑式记录。视觉以冻结方案为准，事件和数据以代码为准。
- ImageGen 展示两条示例引用；代码必须继续渲染真实 `citations` 数组，不写死示例标题。
- ImageGen 展示已同意会话态；Figma 仍必须补齐未同意、关闭、错误和长内容等真实状态。
- 当前代码每次进入页面都重新显示同意步骤；本轮保留，不在 Figma 中暗示跨会话记忆或持久同意恢复。

## 连接恢复结论

Figma `whoami` 已恢复，随后通过文件清单、变量/样式盘点、Components 页元数据、库清单与设计系统搜索完成 P0.b/P0.c。期间一次 `use_figma` 只读调用出现 transport error，调用原子失败且无画布写入；替代只读元数据证据已补齐，现可进入组件创建。
