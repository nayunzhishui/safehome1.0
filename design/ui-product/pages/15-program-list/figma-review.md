# 项目测试列表页 Figma 审查

- Figma 文件：`8vocq2yUvjQavYpaxGotPs`
- 页面：`15 Program List`（`196:2`）
- 默认态：`ProgramList/Default`（`196:3`）
- 状态矩阵：`ProgramList/States`（`196:4`）
- 默认态截图：`assets/figma-default-v1.png`
- 状态截图：`assets/figma-states-v2.png`

## 审查结论

- 保留真实的研究者预览边界、三种项目状态、项目字段、Loading、Error、Empty 与待审核数量。
- 删除 ImageGen 中没有真实事件支持的筛选栏；项目行整行进入 `openProgram`。
- 目录行采用开放式连续排版，构念不再堆叠为胶囊，箭头复用 `__Icon/ChevronRight`。
- Loading 与 Empty 不显示操作占位；Error 唯一操作为“重新读取”。
- 默认态与状态矩阵仅使用 `Noto Sans SC Regular/Medium`；36 个文本节点无字体漂移。
- 0 个未绑定的实色填充；复用 3 个箭头实例和 3 个 `PageStateInline` 状态实例。

结论：通过，可作为前端实现基准。
