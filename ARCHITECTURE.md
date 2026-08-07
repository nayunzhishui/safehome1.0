# SafeHome 架构边界

更新时间：2026-08-07

## 1. 架构风格

当前采用 **模块化单体（modular monolith）**，不在本阶段拆微服务。

```text
Web / 微信小程序
        ↓
shared API contract / client
        ↓
Flask routes
        ↓
domain services
        ↓
SQLite（开发/测试） / MySQL（目标部署）
        ↓
content / audit / research artifacts
```

## 2. 四个运行时领域

### participant
家长/学生直接使用：身份、同意、家庭绑定、记录、反馈、测评、训练、打卡、周报、人工支持。

### research
研究者工作流、关系试点、研究分析、画像、计算契约和受控数据使用。

### safety-governance
安全分流、风险复核、隐私、内容治理、可靠性、运营治理和治疗性评估治理。

### internal-rd
AI 合成沙盒、离线 benchmark、集成验证等内部研发能力。不得自动成为参与者能力。

机器可读规则：`config/runtime_architecture.json`。

## 3. 依赖方向

- route 负责 HTTP、认证和输入边界，不承载核心业务决策。
- service 负责领域逻辑，不依赖 test / migration script。
- content 是版本化策略/内容来源，不替代认证和数据库约束。
- Web 新代码优先从 `apps/web/src/services/domainApi.ts` 使用分域 API；旧 `safehomeApi.ts` 仅作为兼容 facade，禁止继续无限增长。
- Task 编号只应存在于测试、脚本、历史文档、迁移元数据和兼容 shim；新的运行时领域代码使用业务名称。

## 4. 身份与权限

正式生产身份以 Bearer/CloudBase/正式后台账号为主。

- `X-Admin-Token`：仅保留 development/testing 兼容；production 拒绝。
- `actor_id`：审计身份必须来源于认证上下文，不能由请求 body 指定。
- Showcase：本轮按负责人决定不修改，仍视为独立既有开发旁路，不作为正式 RBAC 设计的一部分。

## 5. 未成年人参与者边界

student 普通心理数据链路先经过年龄确认：

```text
student 登录
  ↓
年龄段未确认 → 阻断普通心理数据处理
  ↓
≥14岁 → 普通流程
  ↓
<14岁 → active family link
          + guardian consent
          + child assent
          ↓
        普通流程
```

安全求助、风险分流、年龄/同意和家庭绑定路径不被该门禁阻断。

为减少敏感信息，本轮不存储完整出生日期，只保存年龄段确认及同意审计。

## 6. 风险与危机安全边界

规则引擎只做 **safety routing**：

- `standard`
- `human_support_review`
- `human_review`
- `urgent_human_review`

旧 `risk_level` 为兼容字段，不得对外解释为临床风险分层、未来自杀概率或治疗/处置依据。

否定、历史经历和保护因素只记录为上下文信号，不由简单规则自动降级；最终由真人结合上下文复核。

## 7. 数据完整性

历史 schema 大量使用应用层 `*_id` 关系。本轮先通过 `referential_integrity_service.py` 对高价值关系持续审计，再根据本地/生产数据清洁度逐步决定是否增加物理 FK；禁止未经数据审计直接做大规模表重建。

## 8. AI 边界

AI QA 是 `internal-rd`：

- 参与者入口关闭；
- 每个 session 和每条 message 都必须为 synthetic；
- 真实参与者数据不允许；
- 输入去标识；
- 服务端冻结 use case/provider；
- 只读 retrieval allowlist；
- 无跨会话记忆；
- 无写工具；
- 有 kill switch 和独立 release gate。

## 9. 自动架构守卫

- `python backend/scripts/audit_runtime_architecture.py`
- `python backend/scripts/audit_referential_integrity.py`
- `node scripts/audit_web_domain_boundaries.mjs`

这些检查用于防止新增架构债，不代表真实环境、伦理、法律、无障碍或人工心理学审核已经完成。
