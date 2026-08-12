# 情绪温度计页 Figma Gap Analysis

## ImageGen 偏差修正

- 字数上限从概念图的 20/30 纠正为代码真实 40/200。
- 移除概念图记录行的箭头；真实记录行没有点击事件。
- 回执改为真实消息容器，不固定展示虚构结果。
- 三个 slider 只显示现有维度名和数值，不新增端点字段。

## 组件映射

- 温度计：原生 slider 语义容器 + 点按/拖动区域。
- 加减、保存、刷新、关闭、重试、训练卡：保持各自真实事件和触控目标。
- 曲线：保留 canvas；Figma 折线只作布局基准。
- 记录：复用同一记录行结构，不添加可点击外观。

## 状态

- Default、Loading、Empty、Error、Saving、Receipt、SelectedPoint 均有真实代码字段。
- LoginRequired 继续由 `requireLogin` 处理，不在页面伪造登录卡。

