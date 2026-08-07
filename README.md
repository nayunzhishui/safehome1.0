# 安心陪伴 / SafeHome / ReadFeedback

更新时间：2026-08-07

SafeHome 是一个面向家长与学生的**非诊断心理支持与研究协作系统**。项目以情绪调节、支持性反馈、行为练习和人工支持为主线，同时包含受控心理测评、研究工作流、画像分析、隐私/安全治理和仅限合成数据的 AI 研究沙盒。

## 当前事实入口

新会话、Codex 或 Claude 开始工作前优先读取：

1. `PROJECT_STATUS.md` — 当前项目与发布状态
2. `ARCHITECTURE.md` — 当前架构、身份、安全和数据边界
3. `docs/00_当前事实基准/项目进度统一口径.md` — 历史任务与事实基准
4. `docs/03_技术真相/当前项目代码总体解释与功能衔接说明.md` — 代码与功能解释

历史任务文档用于追溯，不应覆盖当前源码事实。

## 产品边界

SafeHome 可以做：

- 情绪/互动事件记录；
- 规则式、支持性、非评判反馈；
- 情绪调节与亲子沟通练习；
- 周期性回顾与人工支持；
- 受控心理测评与非诊断结果解释；
- 研究者工作流、去标识分析和受控导出；
- 安全信号保守分流与人工复核。

SafeHome 不应被解释为：

- 心理或精神疾病诊断系统；
- 自杀/自伤概率预测器；
- 自动危机处置系统；
- 固定人格分类系统；
- 自由聊天式心理治疗 AI；
- 可以替代专业人员和现实紧急支持的系统。

## 核心支持闭环

```text
记录 → 识别 → 支持性反馈 → 练习 → 追踪 → 人工支持
```

研究与治理能力围绕该主线服务，不应反向挤占参与者端核心任务。

## 技术架构

```text
apps/miniprogram  微信小程序参与者端
apps/web          Web 研究/管理后台
backend           Flask API + domain services
content           版本化心理内容/策略/治理注册表
shared            共享 API 常量与类型
analysis          离线研究与画像分析
scripts           构建、审计、验收工具
```

架构风格：模块化单体。详见 `ARCHITECTURE.md`。

## 身份与安全

- 正式身份：Bearer token / CloudBase / 正式后台账号。
- `X-Admin-Token`：仅 development/testing 兼容，production 停用。
- 风险复核审计 actor 必须来自认证身份。
- student 普通心理数据处理需要先完成年龄段确认；未满14岁还需要有效监护人绑定、监护人同意和学生本人 assent。
- 风险规则只做人工安全分流，不构成临床风险分层。

## AI

AI QA 仍是**内部合成研究沙盒**：

- participant entry = off；
- real participant data = forbidden；
- 每个会话和每条消息必须明确 synthetic；
- 输入去标识；
- 只读受控检索；
- 无跨会话记忆；
- 无写工具；
- provider/use case 由服务端冻结。

## 验证

基础全量检查由：

```text
.github/workflows/check.yml
```

执行。

2026-08-07 定向加固额外检查：

```text
.github/workflows/targeted-hardening.yml
```

覆盖：风险/审计身份、未成年人保护、AI 沙盒、运行时架构、SQLite/MySQL 关系完整性、Web 分域边界、Web build/typecheck 与 WCAG 2.2 Playwright 基线。

常用本地命令：

```powershell
python backend\scripts\validate_content.py
python -m pytest backend\tests -q
python backend\scripts\audit_runtime_architecture.py
python backend\scripts\audit_referential_integrity.py
node scripts\audit_web_domain_boundaries.mjs
cd apps\web
npm run typecheck
npm run build
npm run test:e2e
```

## 发布说明

“源码完成”“自动测试通过”“engineering complete”均不等于正式上线批准。正式试点/上线仍需要真实 CloudBase/MySQL、微信开发者工具/真机、心理学人工审核、伦理/隐私/安全审核与负责人批准等独立证据。

当前定向修复分支不得自动合并，必须先由本地 Codex 查看完整 diff 和测试结果，再由负责人决定是否进入 `main`。
