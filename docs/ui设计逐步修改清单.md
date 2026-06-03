# UI 设计逐步修改清单

创建日期：2026-06-02

适用项目：`safehome1.0 / 安心陪伴 / ReadFeedback`

适用范围：小程序端 `apps/miniprogram`

参考文档：

```text
docs/小程序设计系统.md
docs/UI与伦理边界验收清单.md
docs/当前进度交接.md
docs/开发日志.md
docs/开发说明.md
```

本清单用于把小程序 UI 按“美观精致但少 AI 味”的方向一步一步改完。每一步都尽量小，便于零基础负责人照着检查、确认和继续。

## 0. 总规则

每一轮只做一件事：

```text
只改一个页面，或只改一组公共组件。
不要一次性改所有页面。
不要顺手改后端、数据库、API、shared 类型。
不要删除 pages/integration-test/index。
```

每一轮都必须做四件事：

```text
1. 改前看文件。
2. 只改本轮列出的文件。
3. 改后做验证。
4. 更新 docs/开发日志.md、docs/当前进度交接.md、docs/开发说明.md。
```

每一轮都要检查“少 AI 味”：

```text
不堆“温暖、专业、成长、治愈”等空泛词。
不把所有模块都做成渐变卡片。
不铺满叶子、星星、光斑。
不写营销感按钮，例如“立即开启”“一键生成”“马上提升”。
不出现诊断、异常、疾病、治疗、筛查、人格等表达。
```

## 1. 每轮固定操作模板

以后每一轮 UI 修改都按这个模板执行。

### 1.1 改前检查

在 PowerShell 中运行：

```powershell
cd D:\codex\workspace\safehome1.0
git status --short
git diff --name-only
```

目的：

```text
确认当前工作区有哪些已有改动。
不要回退用户已有改动。
不要把无关文件混进本轮。
```

### 1.2 阅读本轮页面

例如本轮改情绪记录页，就先读：

```powershell
Get-Content -Path apps\miniprogram\pages\diary-form\index.wxml
Get-Content -Path apps\miniprogram\pages\diary-form\index.wxss
Get-Content -Path apps\miniprogram\pages\diary-form\index.js
```

读文件时只确认：

```text
页面有哪些模块。
哪些按钮会跳转。
哪些字段会提交给后端。
哪些样式是当前页面独有。
```

### 1.3 修改原则

优先改：

```text
WXML 结构层级
WXSS 样式
页面提示文案
公共组件引用
```

尽量不改：

```text
index.js 中的 API 调用
字段名
页面路径
app.json 页面列表
services/api.js
backend
shared
content
```

### 1.4 改后验证

每轮至少运行：

```powershell
cd D:\codex\workspace\safehome1.0
Get-Content -Raw apps\miniprogram\app.json | ConvertFrom-Json | Out-Null
node --check apps\miniprogram\app.js
node --check apps\miniprogram\services\api.js
git status --short
git diff --name-only
```

如果本轮改了某个页面 JS，也额外运行：

```powershell
node --check apps\miniprogram\pages\页面名\index.js
```

### 1.5 微信开发者工具人工检查

每轮改完后打开：

```text
D:\codex\workspace\safehome1.0\apps\miniprogram
```

检查本轮页面：

```text
页面能不能打开。
主按钮能不能点击。
文字有没有溢出。
输入框是否好点。
底部内容是否被 tabBar 遮挡。
页面是否过度装饰。
有没有诊断化或营销化文案。
```

## 2. 推荐执行顺序总览

按下面顺序做，不要跳着大改：

```text
第 1 步：公共组件细节收口
第 2 步：首页微调
第 3 步：情绪记录页改造
第 4 步：反馈结果页改造
第 5 步：训练页改造
第 6 步：训练卡详情页改造
第 7 步：周报页改造
第 8 步：我的页改造
第 9 步：课程页轻量优化
第 10 步：测评相关页面统一
第 11 步：人工督导页边界优化
第 12 步：全局验收和微调
```

最建议下一轮先做：

```text
第 3 步：情绪记录页改造
```

原因：

```text
它是核心闭环第一步。
最容易影响用户是否愿意继续使用。
可以只改页面样式和文案，不动后端。
```

## 3. 第 1 步：公共组件细节收口

目标：

```text
让公共组件先稳定，后续页面直接复用。
减少每个页面重复写卡片、标题、按钮和提示样式。
```

修改文件：

```text
apps/miniprogram/components/section-title/index.wxml
apps/miniprogram/components/section-title/index.wxss
apps/miniprogram/components/function-entry-card/index.wxml
apps/miniprogram/components/function-entry-card/index.wxss
apps/miniprogram/components/training-task-card/index.wxml
apps/miniprogram/components/training-task-card/index.wxss
apps/miniprogram/components/alert-card/index.wxml
apps/miniprogram/components/alert-card/index.wxss
apps/miniprogram/components/bottom-tip-card/index.wxml
apps/miniprogram/components/bottom-tip-card/index.wxss
```

具体修改：

```text
1. section-title：
   - 标题只保留主标题和可选副标题。
   - “查看更多”文案统一为“查看全部”或“更多”。
   - 不加多余图标装饰。

2. function-entry-card：
   - 图标容器统一大小。
   - 标题不超过 6 个汉字。
   - 副标题不超过 8 个汉字。
   - 不使用 emoji 作为正式图标。

3. training-task-card：
   - 标题突出。
   - 标签最多 1 个。
   - 场景、时长放在次级区域。
   - 不做课程广告感。

4. alert-card：
   - info、success、warning、danger 四类语义清楚。
   - danger 只用于现实安全提醒，不大面积红色。

5. bottom-tip-card：
   - 文案具体，不写空泛鼓励。
   - 装饰植物弱化，不抢内容。
```

验收标准：

```text
公共组件在首页、训练页、课程页中显示不突兀。
没有明显大面积渐变堆叠。
没有文字拥挤。
```

## 4. 第 2 步：首页微调

页面文件：

```text
apps/miniprogram/pages/home/index.wxml
apps/miniprogram/pages/home/index.wxss
```

尽量不改：

```text
apps/miniprogram/pages/home/index.js
```

首页定位：

```text
今日陪伴面板。
不是功能菜单页。
不是营销首页。
```

保留模块：

```text
顶部问候或品牌区
今日状态卡
快速入口
今日推荐训练
最近记录
安心小贴士
弱化的联调测试入口
```

具体修改：

```text
1. 顶部文案：
   当前如果太像模板，改成：
   “今天也辛苦了，先照顾一下自己。”

2. 今日状态卡：
   主标题要回答“今天要做什么”。
   推荐文案：
   “你今天还没有记录情绪”
   “用 1 分钟记录此刻的感受”

3. 快速入口：
   保持 4 个以内：
   - 情绪日记
   - 测一测
   - 目标设定
   - 周报记录

4. 今日推荐训练：
   只推荐 1 个训练。
   按钮用“开始练习”。
   不写“立即提升”“快速改善”。

5. 最近记录：
   使用列表项样式。
   状态文案短，例如“反馈已生成”。

6. 安心小贴士：
   文案具体：
   “允许自己有情绪，先停一下再回应孩子。”
```

不要做：

```text
不新增第五个快捷入口。
不把联调测试入口删掉。
不把所有模块加插画。
不新增后端数据请求。
```

验收标准：

```text
第一屏能看见今日状态和开始记录按钮。
快速入口不拥挤。
底部 tabBar 不遮挡安心小贴士。
页面没有强烈 AI 海报感。
```

## 5. 第 3 步：情绪记录页改造

优先级：最高。

页面文件：

```text
apps/miniprogram/pages/diary-form/index.wxml
apps/miniprogram/pages/diary-form/index.wxss
```

原则上不改：

```text
apps/miniprogram/pages/diary-form/index.js
```

如果必须改 JS，只能做：

```text
补充页面展示用静态文案。
不改字段名。
不改 createDiary / generateFeedback 调用逻辑。
```

页面目标：

```text
降低问卷感。
让家长愿意写。
帮助家长记录具体事件。
继续对齐 POST /api/diaries。
```

推荐结构：

```text
1. 顶部说明卡
   标题：记录刚才发生的一小段
   副标题：不需要写得完整，先把此刻能想到的写下来。

2. 分组一：发生了什么
   - 场景 scene
   - 事件描述 event_description
   - 补充 raw_text

3. 分组二：我和孩子当时的感受
   - 家长情绪 parent_emotion
   - 家长强度 parent_emotion_intensity
   - 孩子情绪 child_emotion
   - 孩子强度 child_emotion_intensity

4. 分组三：我当时的想法和反应
   - 自动想法 automatic_thought
   - 身体感受 body_sensation
   - 行为反应 behavior

5. 底部操作
   主按钮：保存并查看反馈
   辅助提示：以下内容只用于生成支持性反馈，不评价谁对谁错。
```

样式做法：

```text
页面容器使用 safe-page。
每个分组使用 safe-card。
分组标题使用 safe-h3。
说明文字使用 safe-caption。
输入框统一圆角、边线、内边距。
底部按钮使用 safe-primary-button。
```

输入框建议：

```text
textarea 高度不要低于 160rpx。
placeholder 用具体问题引导。
不要要求“完整填写”。
```

推荐 placeholder：

```text
场景：例如 写作业、考试后、睡前、手机使用
事件描述：刚才发生了什么？写一个片段就可以。
自动想法：当时脑子里闪过的一句话是什么？
身体感受：例如 胸口紧、头胀、手心出汗
行为反应：例如 催促、沉默、提高声音、离开现场
raw_text：还有什么想补充的，可以写在这里。
```

禁止文案：

```text
分析你的问题
判断家庭互动模式
完整填写后生成诊断
识别孩子异常
```

验收标准：

```text
页面看起来不像考试问卷。
不用滚动太久才能看到主按钮。
输入框有足够空间。
字段仍能正常提交。
提交后仍能进入反馈页。
```

## 6. 第 4 步：反馈结果页改造

页面文件：

```text
apps/miniprogram/pages/feedback-result/index.wxml
apps/miniprogram/pages/feedback-result/index.wxss
```

尽量不改：

```text
apps/miniprogram/pages/feedback-result/index.js
```

页面目标：

```text
不像诊断报告。
像一次温和复盘。
让家长知道下一步练什么。
```

推荐结构：

```text
1. 顶部边界说明
   “以下内容用于自我观察和练习参考，不评价谁对谁错。”

2. 支持性总结卡
   用一句话承接家长情绪。

3. 本次情绪概览
   展示家长情绪、孩子情绪、强度。

4. 可能触发点
   用“可能”“看起来”表达。

5. 互动模式提示
   不写固定标签。

6. 下一步小练习
   推荐 1 个最小动作。

7. 推荐训练卡
   只展示 1-2 个。

8. 人工督导入口
   文案：需要老师补充看看
```

文案规则：

```text
使用“这次记录里可以看到……”
使用“可能……”
使用“可以先尝试……”
不使用“你就是……”
不使用“孩子存在……”
不使用“家庭属于……”
```

验收标准：

```text
用户第一眼知道这不是诊断。
每张卡只讲一个重点。
推荐训练入口清楚。
高风险提示不被隐藏，也不制造恐慌。
```

## 7. 第 5 步：训练页改造

页面文件：

```text
apps/miniprogram/pages/training/index.wxml
apps/miniprogram/pages/training/index.wxss
```

页面目标：

```text
体现练习路径。
不要只是训练卡堆叠。
让家长知道从哪里开始。
```

推荐结构：

```text
1. 顶部说明
   标题：从先稳定自己开始
   副标题：每天选一个小练习，不需要一次做很多。

2. 新手推荐
   - 情绪觉察
   - 呼吸放松
   - 暂停训练

3. 阶段一：认识和稳定情绪
4. 阶段二：改变想法和行为
5. 阶段三：改善亲子关系
```

样式做法：

```text
阶段标题用 section-title。
训练项用 training-task-card。
每个阶段之间留 40rpx。
不要每张训练卡都加插画。
```

按钮文案：

```text
开始练习
查看练习
继续练习
```

避免：

```text
立即提升
快速改善亲子关系
解锁课程
训练营
```

## 8. 第 6 步：训练卡相关页面改造

页面文件：

```text
apps/miniprogram/pages/training-card/index.wxml
apps/miniprogram/pages/training-card/index.wxss
apps/miniprogram/pages/task-detail/index.wxml
apps/miniprogram/pages/task-detail/index.wxss
```

页面目标：

```text
先区分两个页面的角色。
training-card 是“推荐训练卡列表页”。
task-detail 是“单张训练卡详情页”。
让用户知道这张卡怎么练。
让练习步骤清楚、轻量、可完成。
```

推荐结构：

```text
training-card 推荐列表页：
1. 顶部说明
2. 推荐依据
3. 推荐训练卡
4. 查看练习步骤按钮

task-detail 详情页：
1. 任务概览
   名称、适用情境、预计用时

2. 今天先练这一小步
   一句话目标

3. 三步练习
   第一步：先停一下
   第二步：说出观察到的情绪
   第三步：用一句接纳话回应

4. 示例话术
   2-3 条即可

5. 练习后记录
   今日感受
   完成按钮
```

样式：

```text
推荐列表页不要直接变成详情页。
点击推荐卡后统一进入 task-detail。
步骤用编号列表。
示例话术用浅色卡片。
完成按钮用 safe-primary-button 或 safe-orange-button。
```

## 9. 第 7 步：周报页改造

页面文件：

```text
apps/miniprogram/pages/weekly-report/index.wxml
apps/miniprogram/pages/weekly-report/index.wxss
```

页面目标：

```text
周报是复盘，不是成绩单。
看见小变化，不评价好坏。
```

推荐结构：

```text
1. 本周小变化
2. 本周记录次数
3. 本周练习次数
4. 常见情绪词
5. 可以继续的一小步
```

避免：

```text
评分
排名
等级
优秀/较差
红色警报式视觉
```

## 10. 第 8 步：我的页改造

页面文件：

```text
apps/miniprogram/pages/profile/index.wxml
apps/miniprogram/pages/profile/index.wxss
```

页面目标：

```text
入口清楚。
按功能分组。
少装饰。
```

推荐分组：

```text
我的记录
- 周报
- 历次反馈
- 训练记录
- 测评记录

专业支持
- 人工督导
- 心理咨询说明

安全支持
- 危机支持
- 紧急帮助说明

设置与说明
- 隐私说明
- 知情同意
```

样式：

```text
分组标题用 safe-h3。
入口用 safe-list-item。
危机支持可以用 warning 样式，但不要大红色。
```

## 11. 第 9 步：课程页轻量优化

页面文件：

```text
apps/miniprogram/pages/course/index.wxml
apps/miniprogram/pages/course/index.wxss
```

页面目标：

```text
课程页是内容库，不是营销页。
当前可以保持轻量 mock。
```

修改重点：

```text
课程分类清楚。
课程卡片统一。
按钮写“查看课程”。
不写“立即学习”“限时开启”。
```

## 12. 第 10 步：测评相关页面统一

页面文件：

```text
apps/miniprogram/pages/assessment/index.wxml
apps/miniprogram/pages/assessment/index.wxss
apps/miniprogram/pages/assessment-detail/index.wxml
apps/miniprogram/pages/assessment-detail/index.wxss
apps/miniprogram/pages/assessment-result/index.wxml
apps/miniprogram/pages/assessment-result/index.wxss
```

页面目标：

```text
支持性测评。
不是诊断量表。
不是人格标签。
```

修改重点：

```text
入口说明写清楚“用于自我观察，不是诊断”。
题目区域留白充足。
结果页突出“阶段性画像”。
高风险结果只显示现实支持和人工复核提示。
```

禁止：

```text
人格
病症
筛查
诊断
异常
治疗结论
```

## 13. 第 11 步：人工督导页边界优化

页面文件：

```text
apps/miniprogram/pages/supervision/index.wxml
apps/miniprogram/pages/supervision/index.wxss
```

页面目标：

```text
人工督导是补充反馈入口。
不是实时咨询。
不是危机处理承诺。
```

推荐文案：

```text
你可以把这次记录提交给老师补充看看。
人工反馈可能需要等待，不适合处理紧急安全风险。
如果你或孩子正在经历安全风险，请先联系身边可信赖的人或当地紧急服务。
```

## 14. 第 12 步：全局验收和微调

完成以上页面后，做一次全局验收。

检查页面：

```text
首页
情绪记录页
反馈结果页
训练页
训练卡详情页
周报页
我的页
课程页
测评入口页
测评详情页
测评结果页
人工督导页
联调测试页
```

功能链路：

```text
首页 -> 情绪记录 -> 反馈结果 -> 推荐训练卡 -> 打卡
首页 -> 测一测 -> 测评详情 -> 测评结果 -> 推荐训练卡
我的 -> 周报
我的 -> 人工督导
integration-test -> healthz -> 三步联调
```

统一检查：

```text
颜色是否统一。
卡片圆角是否统一。
按钮是否有主次。
文字是否过浅。
是否存在 AI 模板文案。
是否存在诊断化文案。
tabBar 是否遮挡底部内容。
页面是否过度装饰。
```

## 15. 每轮文档更新模板

每轮结束都在 `docs/开发日志.md` 增加：

```text
## 日期：完成某页面 UI 改造

完成内容：
1. ...
2. ...

修改文件：
```text
列出文件
```

验证结果：
```text
列出命令和结果
```

当前边界：
1. 未改后端/API/数据库/shared。
2. 未删除 integration-test。

下一步建议：
```text
下一轮改哪个页面
```
```

每轮结束都在 `docs/当前进度交接.md` 增加：

```text
## 编号. 日期：某页面 UI 改造完成

已完成：
1. ...

修改文件：
```text
...
```

下一轮建议：
```text
...
```
```

每轮结束都在 `docs/开发说明.md` 增加：

```text
## 日期：某页面 UI 改造说明

1. 本次用到的技术
2. 本次实现了什么
3. 零基础如何理解
4. 下一步怎么继续
```

## 16. 可直接复制给 Codex 的下一轮提示词

如果下一轮要先改情绪记录页，可以复制：

```text
请继续 safehome1.0 项目，项目路径为 D:\codex\workspace\safehome1.0。

请先阅读 docs/小程序设计系统.md 和 docs/ui设计逐步修改清单.md。

本轮只改小程序情绪记录页：
apps/miniprogram/pages/diary-form/index.wxml
apps/miniprogram/pages/diary-form/index.wxss

目标：降低问卷感，让页面更美观精致但少 AI 味。保留现有 JS、API、字段和页面路径，不改后端、数据库、shared、content，不删除 pages/integration-test/index。

页面结构按 docs/ui设计逐步修改清单.md 第 5 节执行：
顶部说明卡 -> 发生了什么 -> 我和孩子当时的感受 -> 我当时的想法和反应 -> 保存并查看反馈。

完成后运行：
Get-Content -Raw apps\miniprogram\app.json | ConvertFrom-Json | Out-Null
node --check apps\miniprogram\app.js
node --check apps\miniprogram\services\api.js
node --check apps\miniprogram\pages\diary-form\index.js
git status --short
git diff --name-only

任务结束后更新 docs/开发日志.md、docs/当前进度交接.md、docs/开发说明.md。
```

## 17. 超保姆执行版：你每次应该怎么操作

这一节给零基础负责人使用。你不需要理解所有代码，按顺序复制、检查、反馈即可。

### 17.1 每轮开始前，你先做什么

每次开新对话，先复制这一段给 Codex：

```text
请继续 safehome1.0 项目，项目路径为 D:\codex\workspace\safehome1.0。

请先阅读：
1. AGENTS.md
2. docs/小程序设计系统.md
3. docs/ui设计逐步修改清单.md
4. docs/当前进度交接.md
5. docs/开发日志.md
6. docs/开发说明.md

本轮只做一个小任务，不要批量改页面。
请先告诉我本轮计划修改哪些文件、每个文件为什么要改、不会改哪些文件。
```

如果你已经决定改哪个页面，再补一句：

```text
本轮只改【页面名称】，不要改其他页面。
```

例如：

```text
本轮只改情绪记录页 apps/miniprogram/pages/diary-form，不要改其他页面。
```

### 17.2 Codex 开始改之前，你要确认什么

Codex 应该先给你一个文件清单。你看到清单后，按下面判断：

```text
如果只包含本轮页面的 wxml/wxss，通常可以继续。
如果包含 index.js，要确认是不是必须改。
如果包含 backend、database、shared、content，通常应该暂停。
如果包含 app.json，要确认是不是要改路由或 tabBar。
如果包含 pages/integration-test，要要求不要删除。
```

你可以回复：

```text
确认，只按这个文件清单修改。不要扩大范围。
```

如果范围太大，回复：

```text
暂停。请缩小范围，本轮只改本页面的 WXML 和 WXSS，不改 JS、后端、数据库、API、shared。
```

### 17.3 Codex 改完后，你看最终回复要包含什么

每轮最终回复至少要有：

```text
1. 修改了哪些文件。
2. 改了什么。
3. 没有改什么。
4. 运行了哪些验证命令。
5. 是否更新了三份文档。
6. 下一步建议。
```

如果没有这些，你可以继续追问：

```text
请补充本轮修改文件、验证结果、未改范围、下一步建议。
```

## 18. 微信开发者工具超详细验收方法

每次改完小程序页面后，都要用微信开发者工具看一遍。

### 18.1 打开项目

操作：

```text
1. 打开微信开发者工具。
2. 选择“导入项目”或打开最近项目。
3. 项目目录选择：
   D:\codex\workspace\safehome1.0\apps\miniprogram
4. 点击“编译”。
```

如果页面没有变化：

```text
1. 点击“编译”旁边的下拉。
2. 选择“普通编译”。
3. 再点一次“编译”。
4. 如果还是没有变化，关闭微信开发者工具再打开。
```

### 18.2 打开指定页面

如果本轮改的是情绪记录页：

```text
1. 在微信开发者工具顶部找“编译模式”。
2. 新增编译模式。
3. 启动页面填写：
   pages/diary-form/index
4. 保存。
5. 选择这个编译模式。
6. 点击编译。
```

其他页面路径：

```text
首页：pages/home/index
情绪记录页：pages/diary-form/index
反馈结果页：pages/feedback-result/index
训练页：pages/training/index
训练卡详情页：pages/training-card/index
周报页：pages/weekly-report/index
我的页：pages/profile/index
课程页：pages/course/index
测评入口页：pages/assessment/index
测评详情页：pages/assessment-detail/index
测评结果页：pages/assessment-result/index
人工督导页：pages/supervision/index
联调测试页：pages/integration-test/index
```

### 18.3 每页都要看的 10 个点

照着看：

```text
1. 页面能打开吗？
2. 第一眼知道这个页面是干什么的吗？
3. 主按钮明显吗？
4. 主按钮是不是只有一个？
5. 文字有没有被截断？
6. 输入框或卡片有没有贴得太近？
7. 页面底部有没有被 tabBar 遮挡？
8. 页面有没有太多渐变、叶子、光斑？
9. 有没有诊断、筛查、异常、治疗这类词？
10. 按钮文案有没有营销感？
```

### 18.4 你可以直接记录验收结果

复制这个模板：

```text
【页面验收结果】

页面：
通过/不通过：

看到的问题：
1.
2.
3.

我觉得最需要修的是：

截图位置：
```

然后把结果发给 Codex。

## 19. 每个页面的“通过/不通过”标准

### 19.1 首页

通过标准：

```text
第一屏能看到“今日状态”。
能看到“开始记录”或类似主操作。
快速入口不超过 4 个。
插画没有压住文字。
底部小贴士不被 tabBar 挡住。
```

不通过情况：

```text
像功能菜单堆叠。
首屏看不到今天应该做什么。
有太多装饰。
按钮太多，不知道点哪个。
```

### 19.2 情绪记录页

通过标准：

```text
页面不像考试问卷。
顶部说明让人放松。
输入框足够大。
分组清楚：发生了什么 / 感受 / 想法和反应。
底部按钮能提交并进入反馈。
```

不通过情况：

```text
字段挤在一起。
提示语像命令。
要求“完整填写”。
看起来像心理诊断量表。
```

### 19.3 反馈结果页

通过标准：

```text
顶部说明“不是诊断”。
先看到支持性总结。
每张卡只讲一个重点。
推荐训练入口清楚。
人工督导入口清楚但不吓人。
```

不通过情况：

```text
像诊断报告。
出现“你是……”“孩子存在……”。
一屏全是长文字。
高风险提示被藏得太深。
```

### 19.4 训练页

通过标准：

```text
能看出练习顺序。
新手知道先从哪里开始。
训练卡标题清楚。
按钮文案是“开始练习/查看练习”。
```

不通过情况：

```text
只是一堆训练卡。
像课程销售页。
出现“立即提升”“快速改善”。
```

### 19.5 训练卡详情页

通过标准：

```text
知道这张卡适合什么情境。
知道预计用时。
知道三步怎么练。
有示例话术。
能完成打卡。
```

不通过情况：

```text
步骤太长。
话术太像说教。
按钮太多。
看不出下一步。
```

### 19.6 周报页

通过标准：

```text
像复盘，不像成绩单。
能看到记录次数、练习次数、小变化。
没有评分、排名、等级。
下一步建议是一小步。
```

不通过情况：

```text
像考试报告。
出现优秀/较差。
红色警报感太强。
```

### 19.7 我的页

通过标准：

```text
入口按分组展示。
我的记录、专业支持、安全支持、设置说明清楚。
危机支持明显但不刺眼。
```

不通过情况：

```text
入口堆成一长串。
危机支持被藏起来。
安全支持看起来像系统能实时处理危机。
```

## 20. 你每轮可以直接复制的页面改造提示词

### 20.1 改情绪记录页

```text
请继续 safehome1.0 项目，路径 D:\codex\workspace\safehome1.0。

请阅读 docs/小程序设计系统.md 和 docs/ui设计逐步修改清单.md。

本轮只改情绪记录页：
apps/miniprogram/pages/diary-form/index.wxml
apps/miniprogram/pages/diary-form/index.wxss

目标：
降低问卷感，让页面更美观精致但少 AI 味。

结构：
顶部说明卡 -> 发生了什么 -> 我和孩子当时的感受 -> 我当时的想法和反应 -> 保存并查看反馈。

限制：
不改 index.js，除非发现不改无法完成且先告诉我原因。
不改后端、数据库、API、shared、content。
不改页面路径。
不删除 pages/integration-test/index。

完成后运行验证命令，并更新 docs/开发日志.md、docs/当前进度交接.md、docs/开发说明.md。
```

### 20.2 改反馈结果页

```text
本轮只改反馈结果页：
apps/miniprogram/pages/feedback-result/index.wxml
apps/miniprogram/pages/feedback-result/index.wxss

目标：
让反馈页不像诊断报告，像一次温和复盘。

结构：
边界说明 -> 支持性总结 -> 情绪概览 -> 可能触发点 -> 互动模式提示 -> 下一步小练习 -> 推荐训练卡 -> 人工督导入口。

限制：
不改 API、不改反馈生成逻辑、不改后端、不改数据库。
所有文案必须非诊断、非标签化、非评判。
```

### 20.3 改训练页

```text
本轮只改训练页：
apps/miniprogram/pages/training/index.wxml
apps/miniprogram/pages/training/index.wxss

目标：
训练页体现路径感，不只是训练卡堆叠。

结构：
顶部说明 -> 新手推荐 -> 阶段一认识和稳定情绪 -> 阶段二改变想法和行为 -> 阶段三改善亲子关系。

限制：
复用 training-task-card。
不写营销感文案。
不改训练卡数据来源。
```

### 20.4 改我的页

```text
本轮只改我的页：
apps/miniprogram/pages/profile/index.wxml
apps/miniprogram/pages/profile/index.wxss

目标：
入口分组清楚，少装饰，安全支持边界清楚。

分组：
我的记录
专业支持
安全支持
设置与说明

限制：
不新增登录注册。
不承诺人工督导是实时咨询。
危机支持只提供现实帮助指引。
```

## 21. 如果你看到问题，怎么让 Codex 修

### 21.1 文字太挤

复制：

```text
这个页面文字太挤。请只调整本页面 WXSS 的间距、行高、卡片内边距，不改 JS、不改 API。
```

### 21.2 页面太 AI 味

复制：

```text
这个页面 AI 味太重。请减少渐变、光斑、叶子和空泛文案。保留一个视觉焦点，普通内容改成白卡、细边线、轻阴影。
```

### 21.3 文案太像诊断

复制：

```text
这页文案有诊断或评判感。请改成“可能”“看起来”“这次记录中可以看到”“可以先尝试”等支持性表达，不要用诊断、异常、人格、疾病、治疗等词。
```

### 21.4 底部被 tabBar 遮挡

复制：

```text
页面底部被 tabBar 遮挡。请只增加页面底部安全留白或使用 safe-page--with-tabbar，不改页面逻辑。
```

### 21.5 按钮太多

复制：

```text
这个页面按钮太多。请保留一个主按钮，把其他操作降级为文字链接或描边按钮。
```

## 22. 最小回滚方法

如果某轮 UI 改坏了，不要乱删文件。

先让 Codex 做：

```text
请检查本轮改动，只针对本轮修改的页面恢复到可运行状态。不要使用 git reset --hard，不要回退用户其他改动。
```

如果只是样式问题：

```text
请只调整本页面 WXSS，保留 WXML 和 JS。
```

如果页面打不开：

```text
请检查本页面 WXML 是否标签未闭合、组件引用是否错误、class 名是否拼错。不要改后端。
```

## 23. 最终完成标准

全部 UI 改完后，至少满足：

```text
1. 首页知道今天该做什么。
2. 情绪记录页愿意填写，不像问卷。
3. 反馈页不像诊断报告。
4. 训练页有路径感。
5. 训练卡详情页知道怎么练。
6. 周报页像复盘，不像成绩单。
7. 我的页入口分组清楚。
8. 测评页明确不是诊断。
9. 人工督导页不承诺实时危机服务。
10. 联调测试页仍然保留。
```
