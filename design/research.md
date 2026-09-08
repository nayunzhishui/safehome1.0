# 任务20界面与研究工作台模式研究

## Apple与设计师参考：落实到自主设计判断（2026-09-08）

- Apple中国官网：https://www.apple.com.cn/ 。本轮实看官网与产品区截图；借鉴清楚的视觉重点、内容成组、主次动作与宽度秩序，不照搬发布会霓虹图、商业营销语或产品海报式留白。
- Apple HIG：https://developer.apple.com/design/human-interface-guidelines/principles 、https://developer.apple.com/design/human-interface-guidelines/layout 、https://developer.apple.com/design/human-interface-guidelines/typography 。本轮通过官方搜索结果读取层级、和谐、一致性、适应性、用户掌控与字体可读性原则；没有宣称已验证全部网页交互。
- Rauno Freiberg官网及Craft：https://rauno.me/ 、https://rauno.me/craft 。本轮实看官网和作品目录；其作品用于校准细节敏感度，不把作品集瀑布流作为小程序模板。
- 《Invisible Details of Interaction Design》原文：https://rauno.me/craft/interaction-design （2023年7月文章）。已读原文：关注界面对意图的响应、可中断性和空间一致性；在安心陪伴中优先落实到清楚的触控、状态和返回路径，不擅自增加滑动提交或动画。
- 已转化的修正：项目列表使用本地真实草案标题/受众/首节内容；所有草案明确待审核；项目详情校准为研究者只读预览并补第4个真实记录点；修复实际长内容带来的状态换行和标题拥挤。未动项目内容、API、权限或后端。

## 前五页精修的一手依据（2026-09-08）

- W3C WAI《Labeling Controls》：https://www.w3.org/WAI/tutorials/forms/labels/ 。本轮读取原文；采用可访问名称、可见标签、标签与输入保持紧密且明确关系。Web示例不直接等同微信支持情况，真机读屏仍待验收。
- GOV.UK Design System《Text input》：https://design-system.service.gov.uk/components/text-input/ 。本轮读取原文；采用简洁上方标签、提示不能仅依赖placeholder、多行回答使用textarea；注册提示放入对应字段组。
- Nielsen Norman Group《Icon Usability》：https://www.nngroup.com/articles/icon-usability/ 。本轮读取原文；采用图标语义一致、保留可见文字、避免同一图标代表多种功能；修正首页温度计误用。
- NN/g视觉层级文章本轮请求超时，不将其记为已读；本轮层级/留白约束采用项目UI总指导与上述已读取的标签亲疏原则。
- 不复制第三方设计素材或安装新UI库；从项目已有Figma图标、原生控件和组件中完成修正。没有把这些原则宣称为本项目用户实验结果。

## UIproduct2 设计调研（2026-09-08）

### 已核对来源与采用范围

- How We Feel 官方公开网站 https://howwefeel.org/ ：浏览器已查看公开页面及视觉，产品表达为记录情绪、观察模式、学习当下策略。采用任务与记录之间的清楚关系，不照搬黑色营销首页、彩色角色或情绪量尺。
- Daylio 官方公开网站 https://daylio.net/ ：公开流程展示选择感受/活动、回看记录和图表。采用低负担输入与记录回看分工，不照搬 emoji、成就、连续打卡、相关性结论，也不复制其隐私承诺。
- Headspace 官方公开网站 https://www.headspace.com/ ：公开目录区分内容、学习及支持服务。仅作内容导航参考，不把其医疗、教练或 AI 服务宣传移植到安心陪伴。此次未验证登录后产品体验。
- Tencent/tdesign-miniprogram 官方 README https://github.com/Tencent/tdesign-miniprogram ：已读取组件库说明，参考按语义复用与小程序原生组件装配，不安装新依赖或整库替换现有组件。
- Tencent/weui-wxss 官方 README https://github.com/Tencent/weui-wxss ：已读取微信一致的 button/cell/dialog/progress/toast/article 等基础样式体系说明，采用熟悉的控件表达和阅读/列表分工，不复制品牌样式。
- Donice 布局原文 https://www.donice010.com/sys-nd/18905.html ：本轮浏览器返回 ERR_CERT_AUTHORITY_INVALID，未绕过证书、未读取付费课程。仅参考既有 safehome-ui-motion-audit 本地公开资料摘要中的对齐、层级、视觉焦点和反同质化原则，明确不算本轮重新验证的原文。

### 转化为本轮设计决策

- 问题：旧版开放分隔、短竹节和白卡重复使用，部分新业务摘要又增加长页面密度。决策：以七类页面结构分工，而非每页统一套卡片。
- 采用：入口行用于导航，表单面用于输入，章节用于长读，状态带用于反馈，双来源对照用于核对，真实阶段用于流程，紧凑数据行用于研究工作台。
- 不采用：营销 Hero、库存人物、虚构健康分、未实现筛选/分页/分享、治疗承诺、无限装饰动效。
- 新方向：design/context.md 的“清朗青瓷”；它是本项目的设计判断，不宣称由竞品测试证明更优。
- 证据限制：本轮不是用户访谈或转化率实验；没有把竞品宣传和站内评价当作客观疗效/可用性证明。

更新时间：2026-07-17

## 采用的行业模式

1. 参与者矩阵作为研究者主入口：先按参与者ID、状态和待处理事项筛选，再进入单人档案。OpenClinica 将 Participant Matrix 作为监测进度和进入详情的主工作区。
2. 单人档案聚合所有模块：基本信息、事件/表单进度、原始填写、审阅状态和审计记录在同一参与者详情中分区呈现。
3. 参与者提交后立即可审阅，但原始表单以只读方式打开，避免研究者误改参与者填写；研究者补充通过独立反馈、备注或查询记录完成。
4. 角色决定可见范围与操作：列表、查看、审阅、导出和管理动作按角色显示，不能仅靠前端隐藏。
5. 研究操作必须可追溯：查看敏感详情、修改状态、发送反馈和导出均写审计日志。
6. 科研平台常见能力包括项目/批次、重复填写、提醒、数据质量控制、实时进度和导出，但参与者端不应承载研究后台的复杂度。

## 参考产品

- 脑岛：研究项目、问卷/实验、被试招募、追踪研究、项目组和数据质量控制。https://service.naodao.com/
- Credamo见数：问卷、样本、数据与统计分析的一体化研究工作流。https://www.credamo.com/
- OpenClinica：Participant Matrix、Participant Details、只读参与者表单、角色权限和审计日志。https://docs.openclinica.com/
- mindLAMP：研究/数字心理健康平台将 dashboard、server、activities 和分析管线分层。https://github.com/BIDMCDigitalPsychiatry/LAMP-dashboard

## 本项目应采用

- Web研究者端使用“参与者列表 + 单人360档案 + 模块标签 + 待办动作”的信息架构。
- 小程序研究者端保留轻量核对和反馈，不承载大表格与复杂导出。
- 参与者端只显示用户语言：测一测、情绪日记、训练、项目练习、阶段性反馈、人工支持。
- 推荐和节奏使用“今天做什么、为什么推荐、下次什么时候”三层，不展示规则编码。
- 图表只做趋势辅助；样本不足时明确空态，不用空坐标轴制造“已有趋势”的错觉。

## 避免的问题

- 把 `pending_review`、`general_support`、卡片ID和规则键直接显示给参与者。
- 在一个页面同时堆叠过多边界说明、说明卡和重复按钮。
- 研究者直接编辑参与者原始回答。
- 只保存练习频率，却不让频率参与到期计算和推荐排序。
- 用横向超宽流程图表达手机端步骤，造成裁切和认知疲劳。
