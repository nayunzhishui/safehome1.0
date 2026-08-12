# R00/R01 Scope Freeze

## 目标

- 记录当前 Git 和用户未提交修改。
- 建立首页、测评结果页功能 before 基线。
- 建立全部参与者页面静态信息密度基线和问题排名。
- 明确 R02 最小修改范围。

## 允许修改

- `scripts/audit_participant_information_density.py`
- `backend/tests/test_participant_information_density_audit.py`
- `artifacts/convergence/` 与 `artifacts/information-density/` 本任务证据
- `docs/01_当前执行入口/0813非权限项产品信息密度与工程收敛执行计划.md`
- 三份强制事实文档和 `Claude计划模式.md` 的增量记录

## 禁止修改

- 全部参与者 UI 源文件
- 登录、认证、RBAC、对象权限、Showcase、Consent、actor/subject、Token、CloudBase 权限
- 后端业务、数据库、API contract、shared 类型
- 量表、计分、阈值、风险、危机响应、人工支持触发和 AI 安全规则
- 任务开始前已有的 8 个未提交文件

## 预计修改量

- 1 个只读审计脚本
- 1 个专项测试文件
- 4 类证据目录
- 1 个仓库内执行计划副本
- 4 份增量状态记录

## 失败后的不同动作

- 若审计写入产品源文件：停止并判定 FAIL。
- 若 before 清单缺少用户明确保护的首页功能：补齐清单和测试后重跑。
- 若触碰权限冻结文件或覆盖既有 dirty 文件：停止，不提交，报告 blocker。
- 若专项测试、JSON 解析、静态检查失败：仅修复本轮脚本/证据，重新生成并复验。
