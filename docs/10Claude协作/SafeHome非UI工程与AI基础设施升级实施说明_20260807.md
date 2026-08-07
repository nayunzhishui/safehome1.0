# SafeHome 非 UI 工程与 AI 基础设施升级实施说明（2026-08-07）

## 1. 分支与审查边界

- Base：`codex/safehome-security-enhancement-20260807`
- Head：`codex/safehome-engineering-ai-upgrade-20260807`
- Draft PR：#4
- 本轮明确不修改 UI 视觉、布局、信息架构、文案层级或交互流程。
- 本轮只处理工程运行时、数据库、缓存/协调、部署入口、RAG、Agent、AI 配置、React/小程序工程守卫和 CI。
- `main` 未被直接修改，PR 保持 Draft，禁止自动合并。

## 2. 运行时与依赖升级

`backend/requirements.txt` 已升级并锁定：

- Flask 3.1.3
- Werkzeug 3.1.8
- pytest 9.1.1
- Gunicorn 26.0.0
- PyMySQL 1.2.0
- DBUtils 3.1.2
- redis-py 7.4.1
- scikit-learn 1.9.0
- Pydantic 1.10.26
- jsonschema 4.26.0

Pydantic 暂时保留 v1 最新维护线，避免把 v1→v2 数据模型迁移混入本轮基础设施升级。

新增 `backend/gunicorn.conf.py`：

- 默认 `gthread`
- `WEB_CONCURRENCY=2`
- `WEB_THREADS=4`
- timeout / graceful timeout 默认 30 秒
- keepalive 默认 5 秒
- `max_requests=1000 + jitter=100`
- `preload_app=False`，确保每个 Gunicorn worker 拥有独立的 MySQL pool，不跨进程共享 DB 连接。
- Linux 容器存在 `/dev/shm` 时用于 worker tmp dir。

容器启动入口由 `app:app` 调整为 `wsgi:app`，通过 `backend/services/runtime_bootstrap.py` 在 Flask route/service 导入前安装数据库池和 RAG v2 适配。

## 3. MySQL 升级

### 3.1 保持现有数据库抽象

没有引入 SQLAlchemy，也没有重写现有 `database.py` / SQL。原因：当前 SafeHome 已有大量 SQLite/MySQL 双适配与测试，强行 ORM 化会形成与本轮目标无关的大迁移。

### 3.2 进程内连接池

新增 `backend/services/mysql_pool_runtime.py`，基于 DBUtils `PooledDB`。

默认建议值：

```text
MYSQL_POOL_MIN_CACHED=1
MYSQL_POOL_MAX_CACHED=5
MYSQL_POOL_MAX_CONNECTIONS=7
MYSQL_CONNECT_TIMEOUT_SECONDS=5
MYSQL_READ_TIMEOUT_SECONDS=10
MYSQL_WRITE_TIMEOUT_SECONDS=10
```

这些是单 Gunicorn worker 的连接池上限，不是整个服务的总连接数。例如 2 worker × 7 max connections，理论上单实例最多约 14 条应用连接，因此扩容前必须与腾讯 MySQL 最大连接数联动计算。

### 3.3 TLS

支持：

```text
MYSQL_SSL_CA=/mounted/ca.pem
MYSQL_SSL_VERIFY_IDENTITY=1
```

CA 不进入仓库，应由 CloudBase/Secret Store/部署挂载注入。

### 3.4 实际 CI 证明

`SafeHome Engineering Infrastructure` 使用真实 `mysql:8.4` 容器执行：

1. 完整 `init_db()`；
2. DBUtils pool 安装；
3. `SELECT 1`；
4. migration `062`、`063`；
5. Agent/RAG 新表与列检查。

已验证 MySQL 8.4.11 环境下该路径可执行。

## 4. 显式数据库迁移 063

新增：

`2026_08_07_063 / engineering_ai_runtime_foundation`

### 4.1 `ai_knowledge_chunks` 增量字段

```text
embedding_json
embedding_model
embedding_dimensions
embedding_updated_at
retrieval_metadata_json
```

保留原 `vector_json` 作为确定性 fallback，不删除旧字段。

### 4.2 Agent 审计元数据

新增：

```text
agent_runs
agent_tool_calls
```

只保存：

- actor id / role
- objective SHA256
- tool input/output SHA256
- planner / policy version
- tool 名称
- 状态
- 延迟
- error code
- 时间戳

**不保存原始 objective、tool input 或 tool output。**

## 5. Redis 升级

### 5.1 定位

Redis 只作为：

- 短期缓存；
- 分布式限流；
- 幂等/一次性协调基础；
- 后续异步 job 协调候选。

Redis 不是以下内容的 Source of Truth：

- 监护人同意；
- 儿童 assent；
- 风险复核；
- 测评结果；
- 研究授权；
- 隐私请求；
- 审计证据。

上述内容继续以 MySQL 为事实源。

### 5.2 运行时行为

`backend/services/redis_service.py`：

- 未配置 `REDIS_URL` 时 fail-soft；
- Redis 故障不能单独阻塞普通数据库业务；
- JSON cache 默认 TTL 300 秒；
- 登录分布式限流默认 20 次/分钟/IP hash；
- AI QA 默认 60 次/分钟/IP hash；
- IP 不直接进入 key，先进行 SHA256 派生。

### 5.3 实际 CI

使用真实 `redis:7.4-alpine` 容器验证：

- PING；
- 连接可用；
- 固定窗口限流第 1 次允许、第 2 次超过 `limit=1` 后拒绝。

## 6. Nginx / 入口层

新增：

`deploy/nginx/safehome.conf.example`

它是**可选模板，不是当前生产必需依赖**。

当前 CloudBase 已承担 ingress/TLS 时，不建议为了“技术栈完整”再增加 Nginx。

只有自建 VM/Kubernetes、多 upstream、复杂代理控制时再采用模板。

模板包括：

- TLS 1.2/1.3；
- `client_max_body_size 1m`；
- 5 秒 connect、30 秒普通 API read timeout；
- AI QA 45 秒 read timeout；
- `X-Request-ID`；
- 清空客户端提供的 `X-WX-OPENID / UNIONID / FROM-OPENID`，防止公共客户端伪造平台身份头；
- `/healthz` / `/readyz` 单独代理。

## 7. RAG v2

### 7.1 现状修正

原项目已经具备：

- 内容治理；
- 文档/Chunk；
- BM25；
- 96 维确定性 hash vector；
- cosine；
- hybrid；
- 基础 rerank；
- citation；
- retrieval evaluation。

因此本轮不是“从零实现 RAG”，而是升级检索层。

### 7.2 新 pipeline

`backend/services/rag_v2_service.py`：

```text
approved / published / active knowledge only
              ↓
      BM25 top 20
              +
   Vector top 30
              ↓
         RRF(k=60)
              ↓
 deterministic rerank
              ↓
 final top 6
              ↓
 max 1 chunk/document
```

默认参数：

```text
RAG_LEXICAL_TOP_K=20
RAG_VECTOR_TOP_K=30
RAG_FINAL_CONTEXT_K=6
RAG_RRF_K=60
RAG_MAX_CHUNKS_PER_DOCUMENT=1
RAG_CACHE_TTL_SECONDS=300
```

以上是工程初始值，不代表统计最优值，后续必须通过 Recall@K / MRR / nDCG / citation accuracy / groundedness 做网格或贝叶斯调参。

### 7.3 Embedding

默认：

```text
RAG_EMBEDDING_PROVIDER=hash
```

继续使用 96 维确定性向量，因此：

- CI 无网络也可运行；
- 离线 benchmark 可重复；
- 没有外部 API key 时不会失效。

可显式切换：

```text
RAG_EMBEDDING_PROVIDER=openai_compatible
RAG_EMBEDDING_BASE_URL=...
RAG_EMBEDDING_API_KEY=...
RAG_EMBEDDING_MODEL=...
```

外部 embedding 只有在：

- chunk `embedding_model` 与 query model 完全一致；
- dimensions 完全一致；

时才参与 cosine 排序。禁止混用不同 embedding 模型或不同维度。

### 7.4 Embedding rebuild

新增：

`backend/scripts/rebuild_rag_embeddings.py`

只读取已通过 `content_governance`、`published`、`active`、`approved` 的知识 chunk。

不读取 participant diary/message/assessment/research free text。

推荐操作顺序：

```text
1. 先 dry-run
2. 选 100~500 个治理知识 chunk 做小批量 embedding
3. 固定模型版本
4. 跑检索 benchmark
5. 与 hash baseline 比较
6. Recall/groundedness 无明确收益则不切默认 provider
7. 收益稳定后再全量 rebuild
```

## 8. Agent v1

### 8.1 原则

Agent v1 不是心理咨询 Agent，也不是自治临床 Agent。

状态：

```text
internal_synthetic_only
```

只允许：

```text
researcher
supervisor
admin
```

而且每次必须显式：

```text
synthetic_data=true
```

### 8.2 Planner

当前：

```text
deterministic_tool_router
```

不由 LLM 决定权限和工具。

### 8.3 Tool allowlist

仅 3 个：

```text
knowledge.search
runtime.config
schema.migrations
```

全部 read-only。

### 8.4 明确禁止

Agent 无权：

- 诊断；
- 治疗决定；
- 关闭或降级 risk review；
- 修改监护人同意；
- 修改儿童 assent；
- 删除参与者数据；
- 改角色；
- 批准研究导出；
- 自动发布；
- 给参与者自动发消息；
- 执行任意 SQL；
- 执行 Shell；
- 浏览未批准外部网页。

### 8.5 CLI

```bash
python backend/scripts/run_agent.py \
  --synthetic-data \
  --actor-role researcher \
  --objective "查看 MySQL Redis embedding 运行配置"
```

默认 tool budget = 3。

## 9. AI Provider

本轮没有另造 provider framework，因为 SafeHome 现有 `ai_qa_provider.py` 已有：

- fake provider；
- OpenAI-compatible provider；
- provider allowlist；
- HTTPS 校验；
- timeout；
- cancellation；
- response size；
- usage/cost metadata；
- real provider fail-closed。

RAG embedding 与现有 AI QA provider 逻辑保持解耦，防止为了 embedding 直接开启 participant AI。

## 10. React 工程层

本轮不改 React 页面。

新增 CI guard：

- bearer token 必须使用 `sessionStorage`；
- 禁止重新使用 `localStorage.setItem(AUTH_TOKEN_KEY)`；
- 必须保留旧 localStorage token 清理。

长期仍建议将 Web session 转向 HttpOnly/Secure/SameSite cookie，但需要服务端 CSRF/session 设计，应单独 PR 实施。

## 11. 微信小程序工程层

本轮不修改页面 UI。

主 transport：

`apps/miniprogram/services/api.js`

上一安全分支新增的：

`services/minorSafeguardsApi.js`

目前暂保留为受审查的第二个窄 transport，已补齐：

- Bearer；
- X-Request-ID；
- 401 auth 清理；
- 统一 status/statusCode；
- retryable；
- error details；
- local HTTP / CloudBase 双 transport。

CI 只允许：

```text
services/api.js
services/minorSafeguardsApi.js
pages/debug/index.js
```

直接调用 `wx.cloud.callContainer`，任何新第三套 transport 都会阻断 CI。

长期可以在单独重构 PR 中把 minor safeguards 彻底并回 `api.js`，但不建议在本轮重写 1500+ 行核心 transport 文件。

## 12. CI

### 12.1 SafeHome Checks

继续覆盖：

- dependency install；
- `pip check`；
- release artifact hash；
- content validation；
- API contract；
- API boundary；
- API compatibility；
- backend pytest；
- AI quality gate；
- Web typecheck/build；
- miniprogram static/governance tests。

`checkout` 升为 v6，`setup-python` 升为 v7。

### 12.2 Engineering Infrastructure

新增：

- MySQL 8.4 服务容器；
- Redis 7.4 服务容器；
- pool + migration + Redis + RAG smoke；
- Agent/RAG 7 项专项单测；
- non-UI Web/小程序 transport guard。

## 13. 部署前 preflight

新增：

```bash
python backend/scripts/check_engineering_runtime.py
```

只输出脱敏状态：

- env；
- DB provider；
- pool 阈值；
- Redis 是否配置；
- RAG 参数；
- embedding provider/model；
- Agent policy；
- migration manifest；
- AI QA 开关；
- proxy trust。

不会打印：

- MYSQL_PASSWORD；
- REDIS_URL；
- embedding API key；
- provider API key。

## 14. 快速回滚开关

出现运行问题时优先使用开关，而不是立即做 destructive migration：

```text
MYSQL_POOL_ENABLED=0
REDIS_ENABLED=0
RAG_V2_ENABLED=0
RAG_EMBEDDING_PROVIDER=hash
```

必要时 Docker 入口可回退至原 `app:app`。

migration 063 为 additive；除非经过单独审批，不建议直接 DROP embedding columns 或 Agent audit tables。

## 15. 尚未宣称完成的真实环境验收

即使 CI 全绿，以下仍需真实环境验证：

1. 腾讯云真实 MySQL TLS CA；
2. CloudBase 最大实例数 × pool size 的总连接预算；
3. Managed Redis VPC/ACL/TLS；
4. 真实外部 embedding provider 网络/配额/费用；
5. approved corpus embedding benchmark；
6. RAG Recall@5/10、MRR、nDCG、citation accuracy、groundedness；
7. Gunicorn 并发和连接池压测；
8. CloudBase 灰度部署与 `/readyz`；
9. Agent 仍只允许内部合成数据，不进入 participant runtime。

## 16. Codex 审查重点

请 Codex 优先检查：

1. `backend/services/mysql_pool_runtime.py` 是否维持原 database API 语义；
2. `backend/services/rag_v2_service.py` 是否可能混用不同 embedding model/dimension；
3. `agent_runtime_service.py` 是否存在未登记写工具或 raw input 持久化；
4. migration 063 是否在 SQLite/MySQL 均幂等；
5. Redis unavailable 时是否会意外阻断主业务；
6. `TRUST_PROXY_HOPS` 是否保持默认 0；
7. Nginx 模板是否被误认为当前生产必须依赖；
8. 两套 CI 最终是否全绿。
