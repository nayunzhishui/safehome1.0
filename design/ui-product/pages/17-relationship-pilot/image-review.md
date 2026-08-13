# 关系探索试点页 ImageGen 审查

采用稿：`assets/imagegen-default-v1.png`

结论：`pass_with_figma_corrections`

- 通过：开放页头、单一主行动、五阶段竹节路径、其它入口连续行和底部边界层级明确。
- 分离：图中把未报名与已报名同时展示；Figma 必须拆为 EnrollmentRequired 与 Enrolled 两个互斥状态。
- 删除：`SafeHome` 品牌头、参与者头像/姓名/生日/专业、参与次数；现有代码没有这些可见字段。
- 删除：项目说明、隐私管理、需要帮助、联系我们；“其它入口”只能来自真实 `secondaryActions`。
- 纠正：报名说明、同意文案、按钮和当前行动全部使用现有 WXML/JS 原文与绑定。
- 纠正：竹节改为前端可稳定实现的细茎 + 五个节点；不使用写实竹子、头像或大量图标。
- 状态必须覆盖 Loading、RoleBlocked、EnrollmentRequired、Submitting、Enrolled、Error、LongContent。
