# 情绪记录页 ImageGen 审查

状态：`approved_for_figma`
日期：2026-08-10
图像：`design/ui-product/pages/02-diary-history/assets/imagegen-default-v1.png`

## 通过项

- 页面名称、三条样例记录、时间、场景、事件描述、主要情绪和强度均符合冻结真值。
- 时间脊线表达真实先后关系，没有使用无意义编号；记录项依靠排版、留白和分隔线组织，没有重复圆角卡片。
- 只有“记录一件事”一个主行动；没有筛选、搜索、图表、总数、趋势、详情箭头、编辑或删除。
- 没有人物、家庭照、emoji、医疗图标、诊断或疗效文案。
- 视觉延续首页变量：暖白画布、墨色正文、森林绿主行动、陶土橙强度标记。

## Figma 必须修正或明确的细节

- ImageGen 按视觉示例画出 10 格强度刻线；Figma 和代码必须将已填格数绑定真实 `parent_emotion_intensity`，不能静态复制。
- 主按钮在概念图中有轻微色差，Figma 使用纯色 `Semantic/color/action/primary`，不使用渐变。
- 原生导航栏、微信胶囊和返回键只作为平台环境参考，不创建自定义替代组件。
- Default 以外还需补 Loading、Empty、Error、NetworkFailure、LongContent 五个状态；概念图不代表这些状态已经完成。

## 结论

概念图功能语义和视觉方向通过，可进入同一 Figma 文件组件化复现；不得据此提前修改前端。
