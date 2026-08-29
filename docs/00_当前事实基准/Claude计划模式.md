# Claude 计划模式：量表录入 · 聚类画像 · 前端重构

## 2026-08-29：GitHub required CI Fix Loop

- [x] 读取 Actions #582：6 个独立 job 通过，`security-contract`、`backend`、`npm-audit` 失败，`release-gate` 随之失败。
- [x] 修复 CRLF/LF 历史证据绑定、Harness 悬空 Git tree 测试夹具、Asia/Shanghai 日期测试和 Task35 两项非规范化哈希。
- [x] 定向验证：Harness 7 项、其余受影响组合 57 项、训练日期 1 项、Task35 1 项通过；4 个 F22/F25 用例只报告旧证据按设计失效。
- [ ] 提交修复后重建 F22/F25/F26 当前证据，并运行其冻结层验证。
- [ ] 旧波次 C review pass 已因机器合同/源码变化失效；冻结后续用固定 reviewer，禁止补写或伪造 pass。
- [x] `nanoid` 由 3.3.17 最小更新到 3.3.18；npm audit 0 vulnerability，Web typecheck/build 通过。
- [ ] 正式 registry digest/attestation、微信平台/真机、四方 GO、72h 仍阻断 production。

## 2026-08-28：RC0810 本地发布门禁续跑

- [x] 恢复并验证 Docker、MySQL 8.4、Redis 7.4；完成隔离迁移恢复和正式候选镜像 runtime gate。
- [x] 完成 Web、小程序、内容/API、制品、F14 隐私谱系和 F22 完整安全重扫；未操作生产资源。
- [x] 修复证据哈希循环、过期镜像探针和 Harness 偶然脏状态测试；定向 Fix Loop 已通过。
- [x] 后端全量首轮执行：1339 passed、13 个门禁绑定失败；13 个失败均已有对应最小复验通过。
- [ ] npm audit 4 High、F22 open gate 362、镜像 registry digest/attestation、微信平台/真机、四方 GO 和 72h 未关闭，production NO-GO。
- [ ] 完成 F25/F26 当前证据与固定 reviewer 波次 C 复审后推送；官方 GitHub required CI 和全历史只读审查交给网页 GPT。

## 2026-08-27：Docker 恢复与正式镜像

- [x] 恢复 Docker Desktop，确认 Engine 29.6.1 可用；未删除 Docker 管理的 `dockerInference` 套接字或重置数据。
- [x] 修复 production/validation 镜像遗漏数据库 profile 合同的问题，并把该文件纳入 release/security/RC 依赖绑定。
- [x] F03 专项 12 项和静态合同通过；正式镜像成功构建，非 root、固定 production 入口、文件系统干净、无登记 Secret，非法生产能力覆盖以 78 拒绝。
- [ ] required CI 未完成；后端全量在范围切换时中断，网页 typecheck/build 通过，npm audit 有 4 个 High 且当前报告无修复版本。
- [ ] 迁移回滚、安全重扫、真实 MySQL 启动、finding 关闭和 RC 重冻结转交其他 agent；production 继续 NO-GO。

## 2026-08-27：RC0810-F26 与波次 C 工程收口

- [x] 从与 `origin/main` 一致的 `f879440e` 隔离 Git archive 生成源码包、后端源码包、production 小程序 ZIP、SBOM inventory、manifest 和 SHA-256 清单。
- [x] 77 个 PR #8 编号全部进入关闭矩阵；缺少当前证据的项目没有标记 resolved。
- [x] 发布演练包含冻结、灰度、停止阈值、人工确认、72 小时观察、代码/数据库/内容回滚和数据核对；消息、外部 AI、导出与风险任务分别登记副作用 ledger。
- [x] 12 项 F26 专项和 6 项反伪造/漂移自检通过；未运行无关回归，也未执行生产动作。
- [ ] 10 类 required CI、安全重扫、后端镜像、微信平台/真机、四方 GO 和观察期缺失；工程材料完成但 RC 未形成，production NO-GO。
- [x] 固定 reviewer `sartre_replacement` 完成波次 C Fix Loop；最终 `reviewed_head=fa322a71`、`decision=pass`、`findings=[]`，全部审查 finding 已关闭。
- [x] F26 状态已回填为 `complete_no_go`；RC0810 自动工程任务收口，下一入口为真实责任人补齐外部门禁后重新冻结候选。

## 2026-08-26：RC0810-F25-B 微信平台与真机最终材料

- [x] 修复新增情绪记录历史页未进入 production 页面策略/能力映射的漂移，最终 inventory 为 53 页。
- [x] 从 Git 提交 `11eeeb25` 生成确定性 production 小程序候选包，静态旅程通过并剥离 4 个内部/调试页。
- [x] 审核说明、账号规则、功能路径、边界、失败恢复、证据元数据、冻结窗口和 external blocker 已进入 packet。
- [x] 4 项 F25-B 专项和 5 项反伪造/漂移自检通过；未运行无关全量回归。
- [ ] Docker daemon、DevTools、微信后台、真实账号/请求、iOS/Android、人工审核、RACI 与试点证据缺失，均保持 `pending_external`。
- [ ] F25-B 工程材料完成，父任务 `blocked_external`、production NO-GO；下一项 F26，冻结后才续用固定 reviewer。

## 2026-08-26：RC0810-F24 配置、审计与遗留质量

- [x] 关闭 `F23-SCHEMA-01`，四份机器契约登记治疗性评估创建字段和必需幂等头。
- [x] 生成 146 个直接配置读取点 inventory，路由改用 Flask Config，provider/build/CLI 进入明确 profile；未分类为 0。
- [x] 认证、AI、claim 和家庭绑定登记 Redis 不可用策略；生产/已配置的高风险路径失败关闭。
- [x] claim 改为高熵、15 分钟、一次性 bearer token，数据库只存摘要，并增加猜测锁定与重放约束。
- [x] 077/078 两项加法迁移完成；审计记录增加顺序和链式 SHA-256，可检测修改但不宣称绝对不可篡改。
- [x] 首页摘要 5xx 显示错误和重新加载，不再伪装成空数据；遗留 M-08—M-14 均有引用证据和处置结论。
- [x] 21 项专项/直接影响测试、契约/兼容/配置验证、首页脚本语法和 diff check 通过；未跑无关全量回归。
- [ ] F24 工程完成、等待波次 C 集中复审；下一项 F25-B，F26 前不调用 reviewer。

## 2026-08-26：RC0810-F23 Fuzz 与 Mutation

- [x] 从当前 API 契约和固定 seed `81023` 生成 10 个非法字段、缺字段、超长、深嵌套、Unicode 与分页边界样本。
- [x] 真实 API 覆盖角色、Consent 本人决定、主体/记录/任务/消息/导出/source object 替换、风险、治疗性评估与幂等冲突；9 项非 mutation 专项通过。
- [x] 在临时源码副本删除或反转 6 个关键判断，6 个 mutant 均被对应 API 合同杀死；语法/启动错误不计成功。
- [x] 固定 seed、最小复现、源码摘要与重放命令已写入 `rc0810_f23_mutation_report.json`。
- [ ] `F23-SCHEMA-01`：治疗性评估创建接口的运行时 JSON/Idempotency-Key 要求尚未进入 API 契约，转入 F24 关闭并继续阻断 production。
- [ ] F23 工程完成、等待波次 C 集中复审；下一项 F24，F26 前不调用 reviewer。

## 2026-08-26：F22-B 最终安全 Gate

- [x] 固定扫描器版本、Trivy 镜像摘要、严重度/例外/超时/负向夹具合同。
- [x] 重扫当前源码、依赖、隔离构建镜像，生成 CycloneDX SBOM 和许可证报告；旧 F22-A 报告不复用为当前证据。
- [x] 绑定源码树、依赖锁、Actions 文件、镜像 ID 和运行报告哈希；运行证据缺失或篡改失败关闭。
- [x] 修复 legacy checkpoint 对新运行的越界激活；新运行从 F10-A 开始，当前已有 A/B checkpoint 的运行可进入 F22-B。
- [x] 工程 Gate 保持 NO-GO：外部 attestation 待完成，现有 source/container findings 未关闭，自动化不得批准生产。
- [ ] 提交推送后标记 F22-B `review_pending_wave`；下一项 F23，F26 冻结前不调用 reviewer。

## 2026-08-26：波次 C phase-A checkpoint 恢复

- [x] 复现波次 B pass 后 `next` 错回 F00。
- [x] 固定恢复 F22-A/F25-A 的祖先 commit、baseline hash 与历史 decision 摘要，不新增 pass。
- [x] 支持从合法 terminal/review-pass 记录反推已满足依赖；篡改 checkpoint 失败关闭。
- [x] 专项、plan、next 和 diff check 通过；当前入口为 F22-B。

## 2026-08-26：波次 B review pass

- [x] 同一 `sartre_replacement` 完成最终 Fix Loop 复审，结论 `pass`、findings 为空。
- [x] Harness 接受最终 decision；F13—F21 全部 verified，production/external gates 保持 false/pending。
- [x] 纯事实回填后进入波次 C F22-B；F26 冻结前不调用 reviewer。

## 2026-08-26：波次 B replacement evidence Fix Loop

- [x] 登记同一 reviewer 的 high finding：替换证据未在 wave packet 前预绑定。
- [x] 固定替换证据路径，并在 packet/state 冻结路径、哈希、旧/新 reviewer 与上一有效 checkpoint。
- [x] 拒绝 decision 自报替换路径/哈希，以及冻结后新增、改写或重哈希。
- [x] 最小 Harness 专项通过；下一步重建波次 B packet 并续用 `sartre_replacement` 复审。
- [x] 已固定替代 reviewer 后忽略同波次历史替换动作，避免 Fix Loop 误判为二次替换；状态单测通过。

## 2026-08-26：波次 B reviewer 替换审计适配

- [x] 原 reviewer 不可恢复时，要求绑定旧 reviewer、最后有效 checkpoint、恢复失败记录和替代 reviewer。
- [x] 无替换证据或哈希/checkpoint 不匹配继续拒绝；`fixing` 中途不得重置基线。
- [x] 最小 Harness 合同通过；未改变业务、数据库、生产配置或 review 结论。

## 2026-08-26：波次 B Fix Loop（F15/F21 findings）

- [x] 复现 scheduler 连续三次扫描失败进入 dead-letter 后仍放行高风险自动化。
- [x] dead-letter 事务内激活 kill switch，禁用自动反馈、自由文本 AI 和治疗性新受理。
- [x] 保留低风险记录保存；恢复仍必须提供真人证据。
- [x] F15 专项 9 项通过；不新增迁移、接口、页面或生产动作。
- [x] Harness 重新绑定 F15 证据并保持 `review_pending_wave`，等待同一 reviewer 增量复审。
- [x] production deep/ready 强制有效运维令牌；RFC1918/loopback 代理源不再自动获得权限。
- [x] 非 production 仅默认放行 loopback；额外 CIDR 必须显式配置，且始终不信任转发来源头。
- [x] production 启动缺少 `OPERATIONS_HEALTH_TOKEN` 时 fail-closed；未写入任何真实 Secret。
- [x] F21 专项与生产配置定向合同通过，等待同一 reviewer 增量复审。

## 2026-08-26：RC0810-F21 运行健康与事故恢复

- [x] public health 最小化；deep/ready 仅允许内部源或运维令牌，且不信任转发来源头。
- [x] deep/ready 只读检查数据库、Redis、队列、内容、scheduler 和部署一致性，不触发迁移。
- [x] 冻结 9 个 SLI/SLO、8 类告警及代码/数据库/内容三类独立回滚 Runbook。
- [x] 事件记录保存最小时间线、证据、决策和后续行动并拒绝敏感正文；五类 P0 均有停止、通知、修复和核对动作。
- [x] 隔离注入 5xx、DB/Redis 中断、backlog 和内容版本错误，5/5 告警与恢复通过。
- [x] 冻结性能预算、七类成本/配额和双管理员账号恢复路径；真实账号恢复演练仍 `pending_external`。
- [x] F21 专项 12 项、直接影响 9 项、验证器/自检/演练通过；无迁移、无生产动作、未跑无关全量回归。
- [x] Harness 收口后保持 `review_pending_wave`；提交推送即到达 F21 冻结点，再续用 `Sartre` 做波次 B 累计复审。

## 2026-08-25：RC0810-F20 心理内容与版本治理

- [x] 为 worksheet、训练卡、反馈规则和解释文本建立 governed payload/version/SHA-256 描述。
- [x] 标准测评与学生画像保存原题目、量尺、计分/模型解释、边界、版本和完整快照哈希。
- [x] 历史详情验证并重放原 payload；篡改快照不参与重放。
- [x] 建立 35 个量表来源、版权、适用人群、用途、禁止解释和上线状态清单。
- [x] 缺来源、版权、题目/量尺、计分或非诊断边界时禁止进入 production manifest；当前 allowlist 为空。
- [x] 完成前端硬编码双轨及小程序/Web 对外文案扫描，当前两类 finding 均为 0。
- [x] 建立内部、参与者与微信审核术语映射；专业/版权门禁保持 `pending_external` 且禁止自动批准。
- [x] 新增 076 加法迁移；F20 9 项（含历史与幂等快照回放）、既有测评幂等合同 2 项和定向迁移合同 5 项通过，未运行无关全量回归。
- [x] Harness 收口后保持 `review_pending_wave`；本提交推送后进入 F21，冻结前不调用 reviewer。

## 2026-08-25：RC0810-F14-B 隐私血缘重扫

- [x] 从 F14-A checkpoint 重扫 F17—F19 及同期新增数据库表，目录覆盖 180/180。
- [x] 修复同行多列解析，绑定内容制品、研究来源/Manifest 和 AI capability 决策账本访问路径。
- [x] 建立主体权利、删除后表面、隔离恢复和第三方数据流 F14-B 机器证据。
- [x] 隐私导出定位 AI 决策数量；dry-run 不变更，执行后仅去标识 actor 并保留最小审计事实。
- [x] 隐私负责人、地域/跨境、供应商承诺、子处理者和微信声明保持 `pending_external`，自动批准=false。
- [x] 修复 Harness 波次 B checkpoint 常量与 stale 恢复漂移；只恢复未受影响且已有有效 review 的记录，活跃单元无证据时回查上一 checkpoint，伪造合同仍拒绝。
- [x] F14 专项 12 项、自校验和冻结组合通过；未运行无关全量回归。
- [x] Harness 收口后独立提交推送并保持 `review_pending_wave`；下一项 F20，F21 冻结前不调用 reviewer。

## 2026-08-25：RC0810-F19 正式 AI 关闭与治理统一

- [x] 盘点配置、参与者用例、治理/发布策略、双端入口和 DeepSeek/OpenAI 适配器。
- [x] 建立唯一 capability 事实源与 resolver，统一 UI、route、service 和 provider 决定。
- [x] production 固定关闭入口、沙盒和 provider；配置/密钥注入、旧客户端和直连 API 均失败关闭。
- [x] validation 只保留内部合成/授权路径，并绑定预算、限流、超时、熔断、DLP、来源和审计条件。
- [x] 建立未来 production 人工 Gate 模板，当前 `pending_external` 且禁止自动批准。
- [x] 双端 fake/unavailable 文案改为合成模拟或未开放，不冒充真实 AI 回答。
- [x] 新增 075 加法迁移和 capability 决策账本；同步 API、数据库和功能真值。
- [x] F19 专项 9 项、F11 16 项、Web typecheck/build、小程序语法与目标页真值通过。
- [x] Harness 最终收口并独立提交推送，状态保持 `review_pending_wave`；下一项 F14-B，F21 冻结前不调用 reviewer。

## 2026-08-25：RC0810-F18 研究来源与执行 Manifest

- [x] 冻结合成 source object 类型、权限、SHA-256、权利和保留策略；真实参与者与外部来源保持关闭。
- [x] 服务端一次读取并持久化不可变来源字节，来源替换或客户端伪造 hash 失败关闭。
- [x] worker Manifest 记录代码、环境/镜像、依赖、算法/模型/词典/阈值、快照、随机种子、输出与日志。
- [x] 通用 complete 拒绝无内部证明 metrics；一次性 Manifest 与 artifact 同事务绑定并拒绝重放。
- [x] 完成三类聚合输出合同、部分输出阻断、算法失败和派生删除保留。
- [x] 相同执行输入进行精确结果 hash 对比；不同随机种子形成不同可重复性键。
- [x] 新增 073/074 加法迁移、策略、API/数据库/架构/运维文档；production 外部门禁保持 pending。
- [x] F18 专项 9 项及直接影响测试通过；Harness 收口后状态保持 `review_pending_wave`，独立提交推送后进入 F19，F21 前不调用 reviewer。

## 2026-08-25：RC0810-F17 不可变内容发布

- [x] 盘点并移除发布、暂停、退役和恢复对容器文件的写入路径。
- [x] 新增完整文件不可变 artifact、release 绑定和 CAS active pointer。
- [x] 运行读取校验 artifact hash，缓存键绑定 filename/hash；损坏不回退容器。
- [x] 完成结构/ID 校验、失败原子性、旧制品恢复、双连接/重启与并发冲突合同。
- [x] 新增 071/072 加法迁移、策略、技术/运维文档；production 外部门禁保持 pending。
- [x] 主智能体自审补上构造快照与 CAS 指针绑定，避免同文件并发发布丢更新。
- [x] 完成 F17 冻结验证与 Harness checkpoint；独立提交推送后进入 F18，F21 前不调用 reviewer。

## 2026-08-25：RC0810 历史 checkpoint 证据绑定

- [x] 定位 F14-A 原最终独立复审 packet、`pass` decision、nonce、哈希和提交树。
- [x] 波次 B 仅凭原始证据文件哈希、packet/decision 互绑及 `4a17b9fa` 提交树恢复 F14-A 依赖。
- [x] 新增篡改 decision 哈希拒绝测试；历史 decision 到期不等于不可引用其已冻结提交，但 production Gate 继续为 false。
- [x] 本修复不启动 reviewer、不重跑 F14-A、不修改业务或数据库；独立提交推送后继续 F17。

## 2026-08-25：RC0810-F16 MySQL 安全与隔离恢复

- [x] production MySQL CA、主机身份校验和最低 TLSv1.2 fail-closed。
- [x] 冻结关键 owner 关系和孤儿检测 SQL。
- [x] 完成备份清单、隔离目标校验、损坏/中断/重复恢复合同。
- [x] F11 合成夹具备份→恢复→升级→归属核对通过。
- [x] F16 专项 10 项、直接影响 7 项通过；真实 RPO/RTO 保持外部门禁。
- [x] Harness checkpoint 收口后状态保持 `review_pending_wave`；独立提交推送后进入 F17，F21 前不调用 reviewer。

## 2026-08-25：RC0810 Harness 断点恢复热修复

- [x] scoped 注册表变化仅失效对应执行单元及后继。
- [x] 最新已启动但尚无 outcome 的任务优先作为当前活动任务。
- [x] 同波次 `review_pending_wave` checkpoint 可恢复，全局变化仍递归失效。
- [x] 最小 Harness 专项通过；独立提交推送后继续 F16，不调用 reviewer。

## 2026-08-25：RC0810-F15 主动安全时钟

- [x] 盘点风险复核、治疗性队列、安全事件及读取时触发路径。
- [x] 新增独立 UTC scheduler、单次 worker CLI、全局租约和运行/事件账本。
- [x] 完成风险到期升级、治疗性任务交接、安全超时 kill switch 与同事务事件。
- [x] 完成并发互斥、重启重领、幂等、三次失败死信、暂停/真人证据恢复和补扫。
- [x] 保留低风险记录保存；关闭无人值守时的自动反馈、自由文本 AI 和治疗性新受理。
- [x] 新增 069/070 加法迁移、策略、运维/技术文档；production 容量证据保持 pending。
- [x] F15 专项 9 项通过；未重复全量回归。
- [x] Harness verify 与主审 checkpoint 已完成，状态为 `review_pending_wave`；独立提交推送后继续 F16，F21 前不调用 reviewer。

## 2026-08-24：RC0810-F13 家庭绑定安全闭环

- [x] 冻结 `pending/consumed/expired/revoked/locked` 五态并完成 10 位安全随机码、HMAC 摘要和末四位存储。
- [x] 使用 pending、版本、有效期和锁定条件完成原子单次兑换；并发双学生仅一个成功。
- [x] Consent 或监护附加失败时回滚兑换与本次限流账本；无效尝试保留脱敏计数。
- [x] 完成账号、设备、IP、单码四维限流；生产 Redis 未配置/不可用时 fail-closed。
- [x] 完成重新生成撤销旧码、临时锁定恢复、解绑和未成年人独立 Consent 路径。
- [x] 新增 067/068 加法迁移并将 database profile head 同步到 068；未执行真实/生产迁移。
- [x] 双端 10 位输入、API 机器契约、技术文档和设置页功能真值同步。
- [x] Harness F13 专项 14 项及直接受影响测试、API 契约、Web typecheck/build、小程序静态检查通过。
- [ ] 完成主审 checkpoint、独立提交和推送后保持 `review_pending_wave`；F21 冻结前不启动 reviewer，下一项 F15。

## 2026-08-24：RC0810 波次 A Fix Loop

- [x] F12-B 冻结后才首次启动唯一 reviewer；真实结论 `fix_required` 已写入 Harness。
- [x] validation 限定显式隔离 SQLite，F11 改为临时库真迁移并核对 9 类数据不变量。
- [x] bootstrap 增加客户端批准目标与服务端部署身份双重校验。
- [x] CI evidence 增加唯一测试数和依赖版本；波次 packet 增加 `base..head` 累计文件及摘要。
- [x] F10 16 项、F11 16 项、Task36 14 项和 packet 专项 1 项通过。
- [x] 同一 reviewer 确认前 5 项 finding 全部关闭；新增的 production receipt 测试夹具 finding 已改用批准的 `test_cloud`。
- [x] 凭据专项 9 项、F10 16 项、F12 30 项、Harness+F12 44 项及冻结证据校验通过。
- [x] 最终 packet 绑定 `39e76225..acbd1198`；同一 reviewer `Sartre` 返回 `pass`，Harness 波次 A=`review_pass`。
- [ ] 提交推送纯事实回填后进入 F13；到 F21 冻结前不启动新 reviewer。

## 2026-08-24：RC0810-F12-B 外部证据接收

- [x] 复用并冻结 F12-A 的真实 RC 绑定、场景、设备矩阵、状态机、签署和失效传播合同。
- [x] 合成证据不冒充真机/平台证据，自动化不能跨到人工或平台批准。
- [x] 微信平台、iOS/Android 真机和可信身份门禁如实保持 `pending_external`，production Gate=false。
- [ ] 完成 Harness 验证、提交推送和波次 A 唯一 reviewer 审查。

## 2026-08-24：RC0810-F11 正式数据库 profile

- [x] production 仅允许 MySQL，绑定批准摘要、版本和数据水印，启动只读检查且不自动迁移。
- [x] validation SQLite 使用显式隔离路径；新增脱敏指纹、9 类合成夹具和非破坏回滚说明。
- [x] F11 专项 15 项、直接受影响组合 67 项和合成夹具通过；既有回归项继续开放。
- [ ] 主审、提交、推送后保持 `review_pending_wave`，随后进入 F12-B。

## 2026-08-24：RC0810-F10-B CI Gate

- [x] 三个旧失败合同按当前决策同步，公开自注册和 production participant AI 仍关闭。
- [x] API 边界保持 0 blocker；warning 65→64 的语义差异已审计，Task35 原用例通过。
- [x] 九个 required job 独立运行，最终 aggregate Gate 只接受全部 success。
- [x] action 固定 commit，缓存绑定 requirements/lockfile，支持定向失败注入和 job 级来源/制品证据。
- [x] F10 专项 14 项、原红点非 Harness 6 项和完整 Harness 13 项通过；本地结果不冒充远端 GitHub CI。
- [x] 无迁移、业务、CloudBase、Secret 或 production 配置变更。
- [x] 远端首次运行发现并修复小程序独立 job 的 Playwright 依赖遗漏；backend 注入前移，113 个后端失败等真实 Gate finding 保持红灯。
- [ ] 主审 checkpoint 后独立提交并推送，状态保持 `review_pending_wave`；随后进入 F11，不启动 reviewer。

## 2026-08-24：RC0810 9.2 历史 checkpoint 补正

- [x] 复现旧运行态缺少 F07—F09 task record 时 F10-B 无法启动。
- [x] 波次 A 登记 F09 完整 commit，并继承 F10-A、F12-A、F07—F09 的已审查依赖事实。
- [x] 启动时验证 commit 存在且为当前 HEAD 祖先，并从 checkpoint 仓库注册表核对只发生受支持的波次工具升级；错误 commit 或不相容合同失败关闭。
- [x] 波次 packet base 绑定该 commit/tree，不生成新 review pass，不改变 production NO-GO。
- [x] 新增真实旧运行态注册表恢复合同，完整 Harness `13 passed in 442.61s`。
- [ ] 独立提交并推送；随后恢复 F10-B 草稿并正式 start。

## 2026-08-24：RC0810 9.2 Harness 最小适配

- [x] 注册 `review_pending_wave` 与 A/B/C 三个 checkpoint；波次 A 新增范围为 F10-B、F11、F12-B，F07—F09 复用既有有效 review-pass。
- [x] 波次内主审通过可保存 checkpoint、独立提交并继续；pending 不计入独立 review pass 或 production Gate。
- [x] 波次冻结 packet 只接受固定 reviewer 的 `pass/fix_required/blocked_external`；`fix_required` 不批量关闭，`pass` 才关闭 pending。
- [x] 增加状态转换、断点恢复、证据失效、跨波次阻断、固定 reviewer 和伪造单任务 pass 拒绝合同。
- [x] 保持旧单任务审查与恢复语义；未修改 F10、业务、数据库、CloudBase、Secret 或生产配置。
- [x] 文档冻结后完整 Harness `11 passed in 286.10s`，差异检查通过。
- [ ] 独立提交并推送；随后进入 F10-B，状态保持 `review_pending_wave`，到 F12-B 才启动唯一 reviewer。

## 2026-08-24：RC0810-F09 执行结果

- 六类核心写入已从“先查再写”改为数据库唯一 claim：目标、日记、打卡、人工支持、普通测评和家长测评同 key/同 canonical hash 回放首次资源与响应，同 key/异 hash 稳定返回 409。
- 新增三段显式加法迁移：幂等主账本与六表 `request_hash`、历史提交键回填、副作用 ledger。SQLite 和 MySQL 唯一冲突均重读赢家，不把并发冲突暴露为 500。
- 打卡审计、人工支持事件/风险/审计、普通测评风险/画像/推荐、家长测评 Consent/研究摘要/风险均与主记录同事务且登记一次；微信、站内消息、AI Provider 和导出继续复用各自已有的 delivery/message/provider/audit 专用账本，避免重复造账。
- 旧客户端不提供 key 时维持原创建行为；64 KiB canonical body 上限、actor/endpoint/version 绑定、字段排序、时间归一和明确忽略字段已形成共享 helper。
- 独立审查两轮 Fix Loop 关闭了家长测评风险文本/时间、测评 GET 摘要泄露、补偿状态绕过、低风险督导账本、Web 弱网重试时间漂移和督导来源标题六项 finding，最终 `pass`。
- F09 专项 21 项、受影响组合 60 项、Web typecheck 和四份 API 契约检查已通过；内部 `request_hash` 不进入接口响应。本地实现不等于测试云 MySQL、production 迁移或发布批准，F11 仍负责最终数据库 profile 验证。

## 2026-08-24：RC0810-F08 执行结果

- Web 与小程序退出均先调用 `POST /api/auth/logout`，服务端按 `auth_epoch` 撤销账号既有 Token；成功或失败后才清理本地认证状态和敏感页面缓存，明确允许的未提交草稿继续保留。
- 弱网或 5xx 时只保存 `user_id`、可选 `auth_epoch` 和时间戳组成的 pending 标识，不保存 Token；下次同一账号通过账号密码、微信或手机号登录时先完成旧会话撤销，再签发新 Token。账号不匹配时不会撤销其他账号。
- 匿名、过期 Token、重复退出和多设备退出均为幂等；Test1、wyd 场景保持原用户 ID 和历史归属。本任务未新增数据库表或迁移，也未扩大旧客户端权限。
- 独立审查发现并修复“B 正常退出误删 A 的 pending”问题，复审最终 `pass`；F08 专项 7 项、认证受影响组合 43 项、Web typecheck/build、小程序语法和四份 API 机器契约通过。
- 完成交接和独立提交推送后，下一入口为 RC0810-F09 核心写操作原子幂等。

## 2026-08-24：RC0810-F07 执行结果

- 已完成本人限定的 Consent API、不可变同意/撤回事件、来源与 actor/subject 血缘、行政注释隔离、精确用途合同和隐私导出/删除同步。
- 旧记录只标记 `provenance_unknown`；显式迁移支持 plan/apply/verify/rollback，未执行生产迁移，production 继续 NO-GO。
- 独立审查 Fix Loop 已关闭迁移排序、未知来源授权、撤回合同、事务回滚及机器契约 finding，最终 `pass`。
- F07 专项 11 项、受影响组合 31 项、家庭绑定原测试 3 项，以及 Web typecheck、小程序语法、API 契约和差异检查通过。
- F07 独立提交推送后，执行入口切换到 RC0810-F08 安全退出；先冻结真实 logout/token/auth_epoch 合同和历史账号兼容边界。

## 2026-08-23：RC0810-F06 执行结果

- 已完成跨用户对象授权、分配有效期、治疗性评估 case/data-item 范围、存在性隐藏、迁移与 API 契约同步。
- 两轮独立审查发现均已实现修复；第二轮修复后的定向合同 2 项、队列/动态同意 9 项及静态/契约检查通过。
- 负责人明确要求停止最终 17/115 项 Harness 回归并直接结束 F06；该证据缺口已如实保留，未虚构最终独立 `pass`。
- F06 独立提交推送后，执行入口切换到 `docs/01_当前执行入口/0810bug修改计划.md` 的 RC0810-F07。

> 适用仓库：`nayunzhishui/safehome1.0`
> 本文件位置：`docs/00_当前事实基准/Claude计划模式.md`（创建于 2026-06-29，来源：Claude Code 计划模式 · Claude Opus 4.8）
> 双执行体：**Claude Code** 与 **Codex**。颗粒度对齐 `docs/08_已完成整改记录/6.5已完成增强问题逐步开发清单.md`。
> 核心原则：**先判断是否已完成，再决定是否修改；已完成不重复开发，未完成才最小改动；代码优雅、干净、整洁、简洁、高效。codex在任何前端设计方面参考skills库中的设计库，优先调用skills进行前端设计**

---

## 0. Context（为什么做）

SafeHome 已有完整「测一测」引擎（量表 API / 通用计分 / DB / 三页前端 / 风险护栏），但三处价值未释放：①夏老师 168 份量表已完成内容梳理，但 `scales_catalog.json`（13 台账）/`scale_item_drafts.json`（题项草稿）→ 用户端唯一数据源 `assessment_worksheets.json`（仅 3 份）之间**搬运链路断裂**，且用户无法按分类自由选择；②既往 9 组 SPSS 数据**未转化为聚类画像**，用户看不到自己在群体中的位置；③小程序视觉偏「AI 味」，需全站重构。
**预期结果**：用户在小程序按「三大类 + 情绪反射弧节点 + 搜索」自由选量表 → 填写 → 提交后获计分与（有画像的量表）**散点落点 + 雷达 + 客观特征/支持建议** → 全站视觉统一重构。

## 1. 技术栈结论（评估后：不更换）

| 端 | 栈 | 结论 |
|---|---|---|
| 后端 | Flask 2.2 + 手写 SQL（SQLite/MySQL 双后端）+ pytest（115 测试） | 保留 |
| Web | React 19 + TS 5.8 + Vite 7（无 UI 库、手写路由） | 保留（本计划基本不动） |
| 小程序 | 原生 JS + CloudBase `callContainer` | 保留（任务3 在其上重构） |
| 跨端 | `shared/`（`types/api.ts` + `constants/api.ts`）+ `{ok,data}` 协议 | 保留并强制同步 |

唯一新增技术面：任务2 离线聚类依赖（pandas/scikit-learn/pyreadstat），**隔离在 `analysis/profiling/`**，不进后端运行时。

## 2. 全局规则（Claude 与 Codex 共同遵守）

**2.1 执行前必读**：`docs/10Claude协作/{协作交接.md,代码审查.md,Claude使用记录.md}`、`docs/00_当前事实基准/项目进度统一口径.md`、D:\codex\workspace\safehome1.0\docs\00_当前事实基准\项目进度统一口径.md，本文件对应任务章节。
**2.2 Claude/Codex 差异约定**：差异处用「**【Codex 在本处如何操作】**」标注。通用差异：①解析二进制量表（docx/pdf/sav）——Claude 跑一次性 Python（python-docx/pdfplumber/pyreadstat）；Codex 同理，缺库则标 `pending_extraction` 并把待补清单交用户。②figma——Claude 无 figma skill，走「设计规范+手写」；Codex 若接入 figma MCP 可改为拉 token。③装依赖/长任务——Claude 直接在 `analysis/profiling/` 建 venv 跑；Codex 按 `requirements-analysis.txt` 执行。
**2.3 禁止**：`git add .`/`commit`/`push`（除非用户要求）、删业务文件、重构整体架构、改真实 `.env`、提交 DB/backups/node_modules/dist、提交真实 token、**提交既往 .sav 原始/逐行隐私数据**、**擅改量表题项原文与计分规则**（录入=如实搬运）、把草稿标 `fully_approved`、新增 AI 自由咨询/临床诊断/医疗级危机干预。
**2.4 允许修改**：`backend/** content/** docs/** apps/web/** apps/miniprogram/** shared/** backend/tests/** scripts/** analysis/**`；以下仅对应子任务明确要求时改：`backend/models.py backend/database.py apps/web/src/services/safehomeApi.ts apps/miniprogram/services/api.js content/risk_keywords.json content/readfeedback/**`。
**2.5 留痕**：任务2 设计留痕 → `safehome1.0其他内容/画像系统设计_Claude_20260628/`（补 02/03/04）；最终报告 → `safehome1.0其他内容/画像系统聚类结果报告_Claude_<日期>.md`；每子任务完成向 `docs/10Claude协作/Claude使用记录.md` 第 4 节按模板追加一条；重要进度同步 `docs/00_当前事实基准/{开发日志.md,开发说明.md}`。
**2.6 基础检查命令**：
```powershell
cd D:\codex\workspace\safehome1.0; python backend\scripts\validate_content.py
cd D:\codex\workspace\safehome1.0\backend; python -m pytest tests -q
cd D:\codex\workspace\safehome1.0\apps\web; npm run build
cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram -Recurse -Filter *.js  | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
```

---

## 3. 精确事实基准（执行者必读 · 改之前先核对行号是否漂移）

**3.1 数据库**（`backend/models.py` / `backend/database.py`）
- `assessment_results`（models.py:153-164）：`id,user_id,worksheet_id,worksheet_title,category,answers_json,scores_json,total_score,result_summary,created_at`（**无 updated_at**）。学生画像也写此表（worksheet_id=`student_profile_v1`，category=`学生画像`，total_score=None，结构化结果塞 scores_json）。
- `student_profiles`（models.py:167-200）：已含 `cluster_id(INT),pc1(REAL),pc2(REAL),nearest_distance,second_distance,dimensions_json,visuals_json,report_json,profile_code,profile_name,confidence,scores_json,...` —— **任务2 可参考其字段语义**，但该表语义属"学生画像"。
- 加列：`ensure_column(conn, table, column, definition)`（database.py:413）→ 在 `ensure_schema_columns()`（database.py:477）对应表 dict 加一行；`init_db()` 启动幂等执行。`CURRENT_SCHEMA_VERSION="2026_06_04_001"`（database.py:25），改 schema 时**同步升版本**。
- MySQL 适配：加**长文本 TEXT 列不要**进 `MYSQL_VARCHAR_COLUMNS`（database.py:27）；`*_json` 自动 LONGTEXT；仅"要进索引的短列"才登记白名单。
- 工具：`new_id(prefix)`、`now_iso()`、`json_dumps/json_loads`、`load_content_json(filename)`、`row_to_dict/rows_to_dicts`、`ensure_user`、`write_audit_log`。

**3.2 shared 契约**（`shared/types/api.ts` / `shared/constants/api.ts`，小程序 `apps/miniprogram/services/api.js` 有第二份端点表，**两处同步**）
- `AssessmentQuestion`（api.ts:206-212）当前仅 `type:"text"|"scale"`，**无 dimension/reverse_scored**（仅存在于内容 JSON）→ 若前端要用须扩展类型。
- 已有 `ProfileVisuals`（api.ts:350-359）：`{ radar[]; pca:{user,points,clusters}; trends[]; keywords? }` —— **任务2 落点可视化直接复用此契约**。
- 端点：`assessments=/api/assessments`、`assessmentResults=/api/assessment-results`、`profile=/api/profile`、`profileResults=/api/profile-results`、`modelInfo=/api/model/info` 等。

**3.3 量表 API 与计分**（`backend/routes/assessments.py`）
- `GET /api/assessments`（:151，支持 `?category=`）→ `_summarize_worksheet`（:34-50）固定字段。`GET /api/assessments/<id>`（:161，返回整份 worksheet + `training_recommendation_rules`）。`POST /api/assessment-results`（:176-232）。`GET /api/assessment-results`（:235，仅返回当前 worksheet id 内记录）。
- **通用计分引擎**`_score_answers`（:70-121）已支持：`dimension_score_method` 取 `sum`/`mean`；反向 `_effective_score`（:60-67）按 `low+high-score`；`len(dimensions)>1` 才写 `scores.dimensions`。**结论：新量表（含 7 点+反向+多维如 PRFQ）只配 JSON，零计分代码改动。**
- assessments.py **当前未导入** `check_text_risk`/`create_risk_review_record`（任务1 自由文本题需新增导入）。

**3.4 画像引擎**（`backend/services/student_profile_model_service.py` + `backend/routes/profile.py`）
- 匹配算法（service:231-275）：z 标准化 → 到各 `cluster.center`（z 空间）欧氏距离 → 最近簇 → 置信度 `(second-nearest)/(second)` → PCA 2D `pc=Σ z·pca_components`（**无 pca_mean**，隐含以 feature_means 为中心）。
- `content/readfeedback/student_profile_model.json` 结构：`features[],feature_means{},feature_stds{},chosen_k,model_selection[],pca_components[2×N],pca_explained_ratio,clusters[]{cluster_id,profile_id,profile_name,n,percent,mean_scores,z_profile,center[],center_pc[2],first_task},training_points[]{cluster_id,profile_id,pc1,pc2},scoring_notes` → **任务2 每组产出同构模型**。
- `build_student_visuals`（service:349）已生成 radar+pca散点+trends；接口 `GET /api/profile-results/<id>/visuals` 已存在。
- 家长计分 `score_parent_scale_answers`（parent_assessment_service.py:52）**硬编码 1-5 + `6-raw`**，**PRFQ 7点禁用此函数**（PRFQ 走通用 worksheet 引擎，见 3.3）。

**3.5 风险接入**（`backend/services/risk_service.py` / `risk_review_service.py`）
- `check_text_risk(text|list, source)` → `{risk_level,matched_categories,requires_review,allow_auto_feedback,...}`。
- `create_risk_review_record(conn,user_id,source_type,source_id,risk_result)` 仅 medium/high 落库。范式见 `routes/feedback.py:94-136`、`routes/profile.py:277-278`。

**3.6 前端三页与资产**（`apps/miniprogram/`）
- 列表页 `pages/assessment/index.js`：现有前端关键词硬分组 `GROUP_DEFINITIONS`（student/parent/adult），`getGroupKey` 返回 `"pending"` 会**静默丢卡（bug，须修）**；`listAssessments()` 无参；**无 Tab/无搜索**。
- 详情页 `pages/assessment-detail/index.js`：`withAnswerState` 注入答题态；scale→option-row、text→textarea；提交分叉（`isStudentProfile`→`createProfile`，否则 `createAssessmentResult`）；`buildProfilePayload` 按固定 key 取值。
- 结果页 `pages/assessment-result/index.js`：**无任何 canvas/图表**；维度纯文字卡；有训练卡推荐区；画像分支靠 `category==='学生画像'`。
- **全局无 canvas/chart 代码**（任务2 自建）。组件 7 个（alert-card/section-title/welcome-card/course-card/training-task-card/function-entry-card/bottom-tip-card）。
- **design token 已存在**（app.wxss:1-47）：`--safe-primary:#578b5f`、`--safe-bg:#fff8ee`、`--safe-card:#fffdf8`、`--safe-radius-*`、`--safe-shadow-*`、公共类 `.safe-page/.safe-card/.safe-h1...`。tabBar：home/training/course/profile。
- 现有 3 worksheet 真实 id：`student_profile_v1`（特殊，6 题 4scale+2text、无 dimensions、category=学生画像、走 /api/profile，**导入脚本不可破坏**）、`emotion_regulation_erq`（2维 sum 7点）、`parent_reflective_functioning_prfq`（3维 mean 7点 + PRFQ11/18 reverse_scored，**已验证通用引擎计分正确**）。
- Web `apps/web/src/pages/ScalesReview.tsx`：静态 import `scales_catalog.json`，**纯只读、无写、无画像**。

**3.7 validate_content.py 排除逻辑**（要改的点）：`EXCLUDED_SCALE_KEYWORDS`（:28-49）+ `is_excluded_scale`（:330）+ `validate_scales_catalog_exclusions`（:343-364）当前把焦虑/抑郁/睡眠/人格类**硬钉** `enabled=false/excluded_from_user_flow=true`。

---

# 任务一：量表按分类录入并打通全链路

**目标**：量表按「情绪反射弧 / 家长自助 / 学生自助」三大类（情绪反射弧内再按 诱因→反应→觉知→接纳→转化→应对→结果 节点）录入，用户端**分类 + 搜索**自由选填，API/后端/前端/DB 全链路打通。
**用户授权决策（务必如实记录）**：诊断/筛查类量表（GAD-7/PHQ-9/DASS/ISI/PSQI/EPQ/大五等）**全部开放**；突破原「筛查类不开放」红线，由用户明确授权；实现上**强制保留非诊断免责声明**作为最低防护。

### T1-01 内容模型扩展（分类字段 + schema）
**改动**：worksheet 与 catalog scale 统一新增：
```text
audience_class : "emotion_reflex" | "parent_self" | "student_self"
reflex_node    : "trigger|reaction|awareness|acceptance|transformation|coping|outcome" | null
search_keywords: string[]   # 别名/英文缩写(ERQ/PRFQ/SCS)/主题词
sensitive_category : bool    # 诊断/筛查/人格化量表为 true（驱动免责强校验）
result_disclaimer  : string  # 结果页免责（敏感类必填，普通类可继承 boundary_notice）
```
保留旧 `category`（结果页/导出/旧画像分支仍用）；新字段为分类树权威源。节点取值与情绪反射弧框架链条一致。`content/schemas/` 增 `assessment_worksheets.schema.json`（若无）并补字段；`scales_catalog.schema.json` 同步。
**【Codex 在本处如何操作】**：仅改 schema 定义；worksheet 实例字段由 T1-04 脚本回填，不手工逐条编辑。
**允许修改**：`content/schemas/**`、`content/scales_catalog.json`（人工区字段）。**完成标准**：schema 含新字段且 `validate_content.py` 通过。

### T1-02 改 validate_content.py（放开诊断类 + 必备边界）
**改动**：把"硬排除"改为"软标注 + 必备边界"：
- 移除/改造 `validate_scales_catalog_exclusions` 对 `enabled/excluded_from_user_flow/review_status` 的强制；保留 `is_excluded_scale` 仅用于**自动给该量表打 `sensitive_category=true`** 的校验提示（不再拦截开放）。
- 新增：对 `sensitive_category=true` 的量表与 worksheet，强校验 `boundary_notice` 含 `BOUNDARY_TERMS`（不构成诊断/不替代心理咨询/不替代危机干预）之一，且 `result_disclaimer` 非空——缺失则报错。
- 保留 `FORBIDDEN_TERMS` 全局禁用语、worksheet 旧前缀拦截（`worksheet_`/`appendix_b_examples_`）。
**必须更新测试**`backend/tests/test_content_validation.py`：将"诊断量表必须 disabled"用例改为"诊断量表 `enabled=true` 但缺 boundary/disclaimer→报错；补齐→通过"。
**允许修改**：`backend/scripts/validate_content.py`、`backend/tests/test_content_validation.py`、`content/schemas/**`。**完成标准**：诊断类可 `enabled=true` 且校验通过；缺免责则失败。

### T1-03 题项录入
**改动**：按"D:\codex\workspace\safehome1.0其他内容\量表内容报告_20260628.md"优先，把这些量表都录入进去，把可解析题项如实补入 `content/scale_item_drafts.json`（结构同现有 PRFQ draft：`likert[]/dimensions[]{code,label,item_codes,reverse_item_codes}/items[]{item_code,display_order,text,dimension,reverse_scored}`）。
**Claude 做法**：对 docx（python-docx）/pdf（pdfplumber）/xlsx（openpyxl）写一次性解析脚本抽题→逐条人工核对题面与反向题→更新 catalog `item_status/scoring_status`；解析不出的（caj/sav/老 doc）写入 `docs/00_当前事实基准/量表待人工录入清单.md` **交用户录入**。**严禁臆造题项与计分**。
**【Codex 在本处如何操作】**：同写解析脚本；缺库或解析失败则该量表标 `item_status:pending_extraction` 并入待补清单交用户。
**允许修改**：`content/scale_item_drafts.json`、`content/scales_catalog.json`、`docs/00_当前事实基准/量表待人工录入清单.md`。**完成标准**：每个拟 `enabled=true` 量表题项+计分完整且经核对。

### T1-04 导入脚本 build_worksheets.py（drafts+catalog→worksheets，幂等·零回归）
**新增**`backend/scripts/build_worksheets.py`：
```text
输入 scale_item_drafts.json + scales_catalog.json；对每个 enabled 量表生成 worksheet：
  items[]→questions[]（item_code→id, text→prompt, type=scale, dimension, reverse_scored）
  likert[]→每题 options[]（value/label/score）
  dimensions[] 透传；dimension_score_method（PRFQ=mean，单维/未声明=sum）
  audience_class/reflex_node/search_keywords/sensitive_category/result_disclaimer 来自 catalog
  enabled_for_user=scale.enabled；recommended_card_ids 透传；boundary_notice 注入（敏感类必填）
零回归：worksheet.id==scale.id；**手工保留清单**（不被覆盖）：student_profile_v1 整条、
  各 worksheet 的 sections 文案、source_file/source_title、人工润色字段——用 worksheet 上
  `_generated:true` 标记区分"脚本生成区"与"人工区"；脚本只覆盖生成区，人工区做深合并保留。
  student_profile_v1 直接跳过（它由 /api/profile 链路维护，不在 drafts 中）。
幂等：再次运行无意外 diff；打印 新增/更新/跳过/保留 统计。
```
**必须新增测试**`backend/tests/test_build_worksheets.py`：PRFQ 7点+反向→options/method=mean 正确；student_profile_v1 原样保留；二次运行幂等。
**允许修改**：`backend/scripts/build_worksheets.py`、`content/assessment_worksheets.json`、`backend/tests/**`。**完成标准**：脚本产物过 `validate_content.py`，幂等，现有 3 worksheet 零回归。

### T1-05 后端 API（分类/搜索/groups + 自由文本风险接入）
**改动**`backend/routes/assessments.py`：
- `_summarize_worksheet` 增返回 `audience_class/reflex_node/search_keywords/sensitive_category/enabled_for_user`。
- `list_assessments` 支持 query：`audience_class`、`reflex_node`、`q`（模糊匹配 display_title+search_keywords）；响应增 `groups`（按大类/节点聚合计数树，供前端直接渲染）。
- `get_assessment` 透传 `result_disclaimer`。
- **自由文本风险**：`create_assessment_result` 内对 `answers` 中 `type=="text"` 的值 `check_text_risk(text, source="assessment")`；high 时按 feedback 范式不返回普通推荐、置 `risk_level`；`conn.commit()` 前 `create_risk_review_record(conn,user_id,"assessment",result_id,risk_result)`。新增两处 import。
**必须新增测试**`backend/tests/test_assessments_route.py`：按 `audience_class/reflex_node/q` 过滤、`groups` 计数、含敏感词 text 题→生成 risk_review_record。
**允许修改**：`backend/routes/assessments.py`、`backend/tests/test_assessments_route.py`。**完成标准**：分类/搜索/风险接入正确，旧提交/历史接口不回归。

### T1-06 shared 契约同步（防两端漂移）
**改动**：`shared/types/api.ts` 扩展 `AssessmentListItem`/`AssessmentWorksheet`（加 `audience_class/reflex_node/search_keywords/sensitive_category/result_disclaimer`）、`AssessmentQuestion`（加可选 `dimension?/reverse_scored?`）、新增 `AssessmentGroupNode` 类型；`shared/constants/api.ts` 如需新端点则加。`apps/miniprogram/services/api.js` 的 `API_ENDPOINTS` 与 `listAssessments(params)` 同步（透传分类/搜索参数）。
**允许修改**：`shared/**`、`apps/miniprogram/services/api.js`。**完成标准**：Web `npm run build` 通过；小程序 JS 检查通过；两份端点表一致。

### T1-07 小程序列表页（三大类 Tab + 节点分组 + 搜索 + 修 bug）
**改动**`pages/assessment/`：
- `data` 增 `activeClass`（默认 emotion_reflex）、`keyword`、`groupsTree`。
- 改 `loadAssessments` 调 `api.listAssessments({audience_class, q})`，直接用后端 `groups`/`items` 渲染，**弃用前端关键词硬分组**（修 `getGroupKey` 的 "pending" 丢卡 bug：未归类量表归入"其他"可见分组，不静默丢弃）。
- 顶部三大类 Tab（纯 view 实现，无第三方组件）；情绪反射弧大类下渲染 7 节点二级分组；顶部搜索框 `<input bindinput>` 防抖调 `q`。空分组隐藏。
- 卡片展示 `sensitive_category` 提示标签；点击导航沿用现有 `openAssessmentEntry`。
**允许修改**：`pages/assessment/index.{js,wxml,wxss,json}`。**完成标准**：三大类+节点+搜索可用；无量表被静默丢弃；JS/JSON 检查通过。

### T1-08 小程序详情页（通用渲染适配 + 边界）
**改动**`pages/assessment-detail/`：复用现有 scale/text 渲染（已支持任意 likert，含 7 点）；展示 `instructions`、`boundary_notice`；`sensitive_category` 量表在题首显著展示免责。**保留** student_profile_v1 的 `createProfile` 分叉不动。
**允许修改**：`pages/assessment-detail/index.{js,wxml,wxss}`。**完成标准**：任意量表可填可交；JS 检查通过。

### T1-09 小程序结果页（维度展示 + 免责 + 画像入口预留）
**改动**`pages/assessment-result/`：维度沿用现有 `scaleDimensions` 文字卡（"不相加、不比高低"）；底部固定 `result_disclaimer`；**为任务2 预留画像区占位**：worksheet 含 `profile_model_id` 时显示"查看我的画像位置"入口（T2-09 接入）。
**允许修改**：`pages/assessment-result/index.{js,wxml,wxss}`。**完成标准**：维度/免责正确；有画像量表显示入口占位。

### T1-10 数据字典与文档登记
**改动**：`docs/03_技术真相/数据字典.md`（与 `数据库字段说明.md`）登记 worksheet/catalog 新字段；`docs/10Claude协作/Claude使用记录.md` 追加记录。
**允许修改**：`docs/**`。

### T1-11 任务一验收
```text
python backend\scripts\build_worksheets.py（幂等）→ validate_content.py 通过 → backend pytest 通过
→ Web npm run build 通过 → 小程序 JS/JSON 检查通过
→ 人工走查：三大类/节点/搜索选量表 → 填写（含 7 点/反向）→ 结果维度+免责 → 现有 3 量表零回归
```

### 附录A：量表→三大类/节点 归属 + 第一批开放清单
分类总表（32 条目，节选关键，完整随 T1-03 落 `docs/量表分类映射表.md`）：PRFQ→家长自助；父母养育倦怠/家庭亲密度/父母自主支持→家长自助；ERQ→情绪反射弧·转化；正念MAAS/FMI→觉知；AAQ→接纳；CD-RISC/认知灵活性→转化；SCS→接纳/转化；领悟社会支持→结果；学习投入/认知好奇/情绪弹性/情绪智力/回避融合/心理韧性RSCA→学生自助；GAD-7/PHQ-9/DASS/ISI-PSQI/GHQ-12/EPQ/大五→情绪反射弧·反应（敏感类，按授权开放但 `sensitive_category=true`）。
**第一批开放（题项+计分就绪）**：A1 PRFQ（家长自助，18题草稿已就绪）、A2 ERQ（转化，已就绪）、A3 SCS（接纳）、B1 CD-RISC-10（转化）、B2 青少年情绪弹性（学生自助）、B3 学习投入（学生自助）、B4 MAAS（觉知）。

---

# 任务二：既往数据聚类画像 + 可视化落点

**目标**：对既往数据**每组每量表单独聚类**（绝不跨组合并；一表多量表则拆开），产出画像模型与「客观特征+支持建议」解释；用户填完对应量表后看到**散点落点 + 雷达**。落点端到端先打通有产品量表的组（PRFQ 优先）。

### T2-01 独立分析环境
**新增**`analysis/profiling/`：`requirements-analysis.txt`（pandas,scikit-learn,pyreadstat,numpy,scipy,matplotlib）、`config.py`（既往数据根路径=项目外、输出路径、`RANDOM_SEED=42`）、`README.md`（数据不入仓声明）、`.gitignore`（忽略中间数据/venv）。
**【Codex 在本处如何操作】**：如果已有分析功能，不需要额外添加依赖，先看一下本机有没有对应依赖，按 `requirements-analysis.txt` 装依赖；缺 pyreadstat 则改用既往盘点 CSV 中可用数值列并在报告标注"未读原始 .sav"。**约束**：原始 .sav/逐行数据严禁入仓，仅聚合画像模型 JSON 入仓。

### T2-02 数据拆组与计分（依据附录B）
**新增**`analysis/profiling/01_extract_groups.py`：按「研究组×量表」拆分（字段范围见附录B）；每组：选题→反向计分（按各量表点数，如 PRFQ `8-raw`）→维度分/总分→缺失值处理（缺失比阈值剔除/均值填补，记录策略）→z 标准化。输出每组特征矩阵到项目外中间目录（含 features 列名/均值/标准差/样本量）。留痕至 `画像系统设计_Claude_20260628/02_分组聚类设计.md`。
**完成标准**：每组干净特征矩阵+计分口径文档；PRFQ 组与产品 worksheet 口径一致（7点/`8-raw`/维度均值）。

### T2-03 每组聚类+降维（产出模型 JSON）
**新增**`analysis/profiling/02_cluster.py`，对**每组独立**：KMeans k∈[2..6]（`random_state=RANDOM_SEED`），用 silhouette+肘部+最小簇样本量选 k；PCA 前 2 主成分做 2D 投影。产出**对齐 `student_profile_model.json` 的同构模型**（见 3.4），文件含 `source_group`、`clusters[]{cluster_id,size,center[],centroid_2d,mean_scores,dimension_means}`、`pca_components`、`training_points`（脱敏，仅 cluster_id+pc1+pc2，**不含任何可回溯个体的原值**）。
**约束**：每组一个模型文件，绝不混合；样本<~120 的组（附录B 标注）降 k 或仅出描述、标注"样本偏小"。
**完成标准**：每组模型可复算用户落点；PRFQ 组 silhouette/簇规模合理并记录。

### T2-04 画像定义与解释（客观特征 + 支持建议）
**改动**：为每组每簇写解释入模型 JSON `clusters[].profile`：`title`（中性非诊断画像名）、`objective_desc`（基于 center 的各维相对高低，客观）、`support_advice`（成长方向，非治疗承诺）、`disclaimer`（不构成诊断/不替代咨询）。口径=**客观特征+支持建议**。留痕 `03_画像定义与匹配算法.md`。
**完成标准**：每簇四段齐全；过 `FORBIDDEN_TERMS`，无人格/诊断定性。

### T2-05 画像模型落地 content + schema
**改动**：模型 JSON → `content/profiles/<group_id>_profile_model.json`（脱敏聚合，入仓）；worksheet 增 `profile_model_id` 关联（仅有画像的量表，经 T1-04 脚本/人工）；新增 `content/schemas/profile_model.schema.json` 并纳入 `validate_content.py`（校验 features/clusters/pca 完整性 + 解释非空 + 禁用语）。
**允许修改**：`content/profiles/**`、`content/schemas/**`、`content/assessment_worksheets.json`、`backend/scripts/validate_content.py`。

### T2-06 后端匹配服务 + 接口（实时计算，复用可视化契约）
**新增**`backend/services/profile_match_service.py` + 路由 `GET /api/assessment-results/<id>/profile`：
```text
读 assessment_result.scores_json + worksheet.profile_model_id → 载入 content/profiles 模型
→ 按 feature_means/stds z 标准化 → 投影 pca_components 得 point_2d
→ 到各 cluster.center 欧氏距离取最近簇 + 置信度（复用 student_profile_model_service 同款算法，抽公共函数）
→ 返回（复用 ProfileVisuals 契约，api.ts:350-359 结构）:
   { point_2d, nearest_cluster_id, clusters:[{cluster_id,centroid_2d,size,profile}],
     radar:{ axes, user_values, cluster_values }, confidence, disclaimer }
```
**设计选择**：落点**实时计算不落表**（给定分数+模型可复算，保持简洁；scores 已存 assessment_results）。鉴权沿用 `require_admin_or_owner`（owner=匿名 user_id）。**禁用** `score_parent_scale_answers`（3.4）。
**必须新增测试**`backend/tests/test_profile_match_route.py`：已知分数→落点/最近簇稳定；无 profile_model_id 量表→404 友好；非 owner→401。
**允许修改**：新增 service/route、`backend/routes/assessments.py`（或新 blueprint）、`backend/tests/**`。

### T2-07 shared 契约同步
**改动**：`shared/types/api.ts` 新增 `ProfilePosition`（point_2d/nearest_cluster_id/clusters/radar/confidence/disclaimer）；`shared/constants/api.ts` 加端点；`apps/miniprogram/services/api.js` 加 `getAssessmentProfile(resultId)`。
**完成标准**：Web build + 小程序 JS 通过。

### T2-08 小程序 canvas 可视化（从零自建，零图库）
**新增**`apps/miniprogram/utils/chart.js`（纯函数绘制）+ 组件 `components/profile-scatter/` 与 `components/profile-radar/`：
```text
散点：Canvas 2D；坐标变换（数据域→画布，留边距）；绘簇心+簇着色+用户落点高亮"您在这里"+图例；
     自适应 rpx→px（wx.getSystemInfo dpr）；training_points 作浅色底图。
雷达：N 轴（维度）；归一化到统一量纲（按各维 min/max 或 0..max）；绘用户多边形 + 最近簇轮廓对比 + 轴标签。
性能：单次绘制、无动画循环；离屏数据由接口给好，前端不算聚类。
```
**【Codex 在本处如何操作】**：优先调用skills，同用原生 Canvas 2D；若选用 ec-canvas 需先评估包体，默认不引第三方。
**完成标准**：散点/雷达正确渲染；JS/JSON 检查通过。

### T2-09 结果页接入画像区
**改动**`pages/assessment-result/`：worksheet 有 `profile_model_id` 时，调 `getAssessmentProfile(resultId)` → 渲染散点+雷达组件 + `nearest.title/objective_desc/support_advice/disclaimer`。无模型量表不显示该区。
**完成标准**：填完 PRFQ→结果页见散点落点+雷达+解释。

### T2-10 留痕文档与报告
补全 `画像系统设计_Claude_20260628/{02_分组聚类设计.md,03_画像定义与匹配算法.md,04_量表补齐与落地路线.md}`；输出 `safehome1.0其他内容/画像系统聚类结果报告_Claude_<日期>.md`（覆盖组、每组 k/样本/簇画像、端到端落点的组、待补量表的组与原因）。

### T2-11 任务二验收
```text
analysis 脚本可复现（同种子同结果）→ content/profiles/*.json 过 validate_content.py
→ backend pytest（profile_match）通过 → 小程序可视化走查（PRFQ）→ 留痕 02/03/04 + 报告齐全
```

### 附录B：既往数据 9 组 × 量表 拆分清单（聚类拆组依据）
| 组 | 人群 | 主样本量 | 量表单元（字段） | 可独立聚类 | 端到端对接 |
|---|---|---|---|---|---|
| 2 李霞庆 | 初中生+家长 | PRFQ 家长自评 400+（126+336…） | **PRFQ FS1-18(FS11/18反)**、RFQ T1-8、自主支持 Z1-12(青少年报告)、亲子 F/M | ✅ | **✅ PRFQ 唯一闭环** |
| 1 王季璇 | 初中生 | 634 | 亲子沟通 F1-14+M1-14、学业浮力、情绪弹性 | ✅ | ⚠️需产品新建量表 |
| 3a 夏媛媛初测 | 高一 | 652 | SCS（Q10/12/13/16/19/22/23/26/29 反） | ✅ | ⚠️学生引擎不重训→成人参照 |
| 5 牛至旭 | 中年女性 | 209 | SWLS、WHO-5、SCS | ✅ | ⚠️人群异→成人参照 |
| 6 高鸣聪 | 大学生 | 309 | HPLP(27)、目标感、SCS | ✅ | ✗ 成人参照 |
| 3b 夏媛媛暑期 | 混杂 | 100 | SCS | ⚠️偏小+混杂 | ✗ |
| 4 蒋鑫悦 | 大学生 | 159 | 调节聚焦、学业拖延（题面缺失） | ⚠️需先补题 | ✗ |
| 7 孙天娇 | 大学生 | 706 | 不健康体重控制（敏感主题） | ⚠️越边界 | ✗ |
| 8 李欣珊 | 大学生 | 341 | 学业压力/PSQI/心理灵活性（仅汇总分） | ⚠️无逐题 | ✗ |
| 9 疫情 | 混杂 | 数千 | GHQ-12/RISC/疫苗意向…（多主题混） | ⚠️需再拆 | ✗ |
**硬约束**：9 组各自独立聚类、绝不合并；首批画像聚焦组2 PRFQ（端到端）+ 组1/3a/5/6（画像库/常模，落点待产品量表）。

### 附录C：PRFQ 口径 + 桥强弱 + 需人工核对点
PRFQ：18题3维（PM:1/4/7/10/13/16；CM:2/5/8/11反/14/17；IC:3/6/9/12/15/18反），7点，反向 `8-raw`，维度均值；产品侧已配置正确，历史侧家长自评。桥强弱：PRFQ★★★★★（唯一闭环）＞亲子沟通★★★（产品须新建）＞自主支持★★☆（需补题+报告人对齐）＞SCS★★★☆（学生已闭环不重训）；IUS/ERQ/TA 无历史常模。
**执行期需人工核对（不阻塞计划）**：①PRFQ 历史 .sav 实际点数（确认 7 点以对齐 `8-raw`）；②父母自主支持报告人方向（青少年报告 vs 家长自评）二选一；③catalog 13 条 vs 报告 32 条 vs 运行层粒度不一致，录入以"运行层+草稿层"为准。

---

# 任务三：前端全站视觉重构（小程序用户端为主）

**目标**：小程序用户端**全站视觉重构**，风格「简洁高效 / 干净清爽 / 优雅温暖」、去 AI 味、尽量不用插图。在任务一、二之后做。

### T3-01 设计 token 演进 + 设计规范
**改动**：基于现有 `app.wxss:1-47` 的 `--safe-*` 变量**演进**（非从零）：收敛为「柔和中性底 + 单一温暖主色（沿用/微调 `--safe-primary`）+ 克制语义色」；统一字号/行高阶梯、8 倍数间距、圆角、克制阴影；去高饱和渐变/拟物/emoji 堆砌。沉淀 `docs/10Claude协作/前端设计规范_Claude.md`（色值、组件规范、Do/Don't）。
**【Codex 在本处如何操作】**：若接入 figma MCP，从 figma 拉 token 写入变量；否则按本规范实现。

### T3-02 公共样式与组件重构
**改动**：重构 7 个组件（alert-card/section-title/welcome-card/course-card/training-task-card/function-entry-card/bottom-tip-card）统一到 token；抽公共 class 去重；`welcome-card` 的 CSS 插画按"少插图"原则简化。**完成标准**：组件视觉统一、无样式回归。

### T3-03 逐页重构（清单）
按 tabBar 主线 + 任务1/2 新页逐页套 token：`home`、`training`、`course`、`profile(我的)`、`assessment(选择)`、`assessment-detail(填写)`、`assessment-result(结果+画像)`、`diary-form`、`checkin`、`weekly-report`、`goal-setting`、`feedback-result`、`training-card`、`supervision`、`task-detail`。每页：信息层级梳理、留白、去插图、统一卡片/按钮/列表。**约束**：只改样式与呈现，不改业务数据流与接口。
**完成标准**：全站风格一致、功能不回归、JS/JSON 检查通过。

### T3-04 去 AI 味文案
**改动**：扫描 `apps/miniprogram/**/*.{wxml,js}` 文案，按 6.5 P2-02 词表（治愈/重塑/改变人生/专业诊断/人格/异常/立即改善…）替换为具体、克制、支持性表达；合法边界文案（"不构成诊断"）不误改。留痕 `docs/05_伦理试用/文案低AI味与伦理表达检查.md`。

### T3-05 figma / Codex 差异说明
figma 设计稿对接：用户配置 figma MCP 后，Claude/Codex 可拉取设计稿比对实现；未配置则以 T3-01 规范为准。本任务**不阻塞**于 figma。

### T3-06 任务三验收
```text
小程序 JS/JSON 检查通过 → 设计规范文档齐全 → 走查 5 条主路径视觉与文案 →（可选）figma 比对
```

---

## 4. 收尾 · 归档 · 顺序 · 验证

**4.1 归档**：本计划已写入 `docs/00_当前事实基准/Claude计划模式.md`，并同步更新 `docs/00_当前事实基准/项目进度统一口径.md` 第 8 节「文档分类索引」。
**4.2 使用记录**：每子任务完成向 `Claude使用记录.md` 第 4 节按模板追加一条。
**4.3 执行顺序**：任务一（T1-01→11）→ 任务二（T2-01→11，依赖任务一 worksheet/计分口径）→ 任务三（T3-01→06）。任务一/二有交叉：要让亲子沟通/自主支持组端到端，需在任务一录入对应产品量表。
**4.4 端到端验证（总）**：
```text
后端：validate_content.py && (cd backend && pytest tests -q)
Web ：cd apps\web && npm run build
小程序：node --check 全量 *.js + ConvertFrom-Json 全量 *.json
分析：analysis/profiling 可复现，content/profiles/*.json 校验通过
人工：分类选量表→填写(含7点/反向/text风险)→结果维度+免责→(PRFQ)散点+雷达+解释→全站视觉走查
```
**4.5 最终汇报**：按 6.5 清单「最终汇报格式」输出（执行概况/修改文件/各任务状态表/测试结果/安全检查/下一步≤3 条）。
**4.6 Codex 一句话口令**：「请按 `docs/00_当前事实基准/Claude计划模式.md` 执行：任务一→二→三→四；每步先判断状态（已完成不重复开发），未完成才最小改动；每步跑对应测试并向 `docs/10Claude协作/Claude使用记录.md` 追加记录；遇 Claude/Codex 差异处按【Codex 在本处如何操作】执行。」

---

# 任务四：量表入库 · 云托管部署 · Web 可视化 · 认证打通

**目标**：① 量表定义与作答结果全部可见于数据库（DB 为唯一事实源）；② 后端部署至腾讯云云托管 + MySQL；③ Web 管理端增聚类散点/雷达可视化；④ 用户注册/登录认证打通前后端。
**执行时机**：任务一（T1-04 build_worksheets.py）完成后方可执行 T4-01；任务二（T2-06 profile_match_service）完成后方可执行 T4-03；T4-02/T4-04 可与任务一/二并行。

---

### T4-00 切换腾讯云 MySQL（轻量配置，不涉及部署）

**背景**：现在用本地 SQLite，用户希望数据存到腾讯云 MySQL。`config.py` 与 `database.py` 的双后端切换已完整实现（`DB_PROVIDER=mysql`），Dockerfile 也存在，**本步骤只做连接配置和验证，不改代码**。

**改动**：

**1. 复制并填写环境变量** — 以 `.env.example` 为模板，在项目根创建 `.env`（已在 `.gitignore` 中）：
```text
APP_ENV=production
DB_PROVIDER=mysql
MYSQL_HOST=<腾讯云 MySQL 内网/外网地址>
MYSQL_PORT=3306
MYSQL_USER=<用户名>
MYSQL_PASSWORD=<密码>
MYSQL_DATABASE=safehome
SECRET_KEY=<≥32位随机字符串>
ADMIN_EXPORT_TOKEN=<随机令牌>
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
CONTENT_DIR=content
```

**2. 安装 PyMySQL**（仅首次）：
```bash
pip install pymysql cryptography
```
或加入 `backend/requirements.txt`（若未在其中）。

**3. 初始化远程库** — 启动后端，`init_db()` 自动在 MySQL 上建表（幂等）：
```bash
APP_ENV=production DB_PROVIDER=mysql ... python backend/app.py
# 或直接调
python -c "from backend.database import init_db; init_db()"
```

**4. 验证** — 调 `GET /healthz/deep`，返回 `database.ok=true` + `database.provider=mysql` 即通过。

**完成标准**：`healthz/deep` 中 `database.ok=true`，`provider=mysql`；本地 SQLite 降级路径不破坏（`.env` 改回 `DB_PROVIDER=sqlite` 仍可启动）。**严禁**：把真实密码/host 提交到 git。

---

### T4-01 量表定义入库（assessment_worksheets 表 + 迁移 + API 切换）

**背景**：量表定义（worksheet）目前存 `content/assessment_worksheets.json`；作答结果（`assessment_results`）已在 DB。用户需量表定义也可在 DB 查询/管理。

**改动**：

**1. 新增表** — 在 `backend/models.py` `SCHEMA_SQL` 追加：
```sql
CREATE TABLE IF NOT EXISTS assessment_worksheets (
    id TEXT PRIMARY KEY,
    display_title TEXT NOT NULL,
    source_title TEXT,
    source_file TEXT,
    category TEXT,
    audience_class TEXT,
    reflex_node TEXT,
    questions_json TEXT NOT NULL DEFAULT '[]',
    dimensions_json TEXT NOT NULL DEFAULT '[]',
    dimension_score_method TEXT NOT NULL DEFAULT 'sum',
    scoring_notes_json TEXT NOT NULL DEFAULT '{}',
    search_keywords_json TEXT NOT NULL DEFAULT '[]',
    boundary_notice TEXT,
    result_disclaimer TEXT,
    instructions TEXT,
    sensitive_category INTEGER NOT NULL DEFAULT 0,
    profile_model_id TEXT,
    enabled_for_user INTEGER NOT NULL DEFAULT 1,
    review_status TEXT NOT NULL DEFAULT 'approved',
    review_note TEXT,
    source_version TEXT,
    source_type TEXT,
    audience TEXT,
    audience_class_detail TEXT,
    recommended_card_ids_json TEXT NOT NULL DEFAULT '[]',
    _meta_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```
索引：`CREATE INDEX IF NOT EXISTS idx_assessment_worksheets_audience_enabled ON assessment_worksheets(audience_class, enabled_for_user)`。将以上同步写入 `INDEX_SQL`。`MYSQL_VARCHAR_COLUMNS` 增 `audience_class/reflex_node/review_status/profile_model_id/dimension_score_method/source_version/source_type/audience`。

**2. 迁移脚本** — 新增 `backend/scripts/import_worksheets_to_db.py`：
```text
读 content/assessment_worksheets.json → 逐条 UPSERT 到 assessment_worksheets 表
（ON CONFLICT(id) DO UPDATE 覆盖非人工区字段）
student_profile_v1 特殊项不跳过，照常入库（只是标注 category='学生画像'）
幂等：二次运行仅更新 updated_at
打印 新增/跳过/更新 统计
```

**3. 后端 API 切换** — 修改 `backend/routes/assessments.py` 的三个 `_load_payload`/`_worksheets`/`_find_worksheet` 辅助函数：优先从 DB 读（`SELECT * FROM assessment_worksheets WHERE enabled_for_user=1` 或不过滤），JSON 文件降级为 `content/` 初始化时一次性来源（已入库后不再依赖）。具体：
```python
def _worksheets_from_db(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM assessment_worksheets ORDER BY display_title").fetchall()
    return [_db_row_to_worksheet(row) for row in rows]

def _db_row_to_worksheet(row: dict) -> dict:
    # 展开 *_json 字段并还原完整 worksheet 结构
    ...
```
**保留 `load_content_json` 降级路径**（DB 空时从文件读，便于本地冷启动）。

**4. Admin CRUD 接口** — 在 `backend/routes/admin.py` 增：
```text
GET  /api/admin/worksheets          → 全量列表（含 disabled），需 X-Admin-Token
POST /api/admin/worksheets          → 新增，需 X-Admin-Token + require_admin_token
PUT  /api/admin/worksheets/<id>     → 更新，字段白名单保护（禁改 id/created_at）
```

**5. DB health check** — `check_database_health()` 在 `REQUIRED_HEALTH_TABLES` 加 `assessment_worksheets`；`training_cards_sync_ok` 类比增 `worksheets_sync_ok`（DB 条数 ≥ JSON 条数）。

**必须更新/新增测试**：`backend/tests/test_assessments_route.py` 增 DB 路径下分类/搜索/提交计分用例；`backend/tests/test_import_worksheets.py` 验证迁移幂等 + student_profile_v1 完整保留 + PRFQ 题项/计分正确。

**CURRENT_SCHEMA_VERSION** 升版至 `"2026_07_01_001"` 并同步 `CURRENT_SCHEMA_NAME`。

**允许修改**：`backend/models.py`、`backend/database.py`、`backend/routes/assessments.py`、`backend/routes/admin.py`、`backend/scripts/import_worksheets_to_db.py`（新增）、`backend/tests/**`。

**完成标准**：迁移脚本幂等；`GET /api/assessments` 数据与 JSON 文件一致；pytest 通过；`healthz/deep` 中 `worksheets_sync_ok=true`。

---

### T4-03 聚类落点写入 DB + Web 端可视化（ResearchDashboard）

**背景**：`assessment_profile_service.py` 已完整实现落点匹配（z 标准化 → PCA 投影 → 最近簇），API `GET /api/assessment-results/<id>/profile-position` 已存在，`content/profiles/` 已有 PRFQ 等多个模型 JSON。**缺失**：计算结果没有持久化到 DB（`assessment_results` 无 pc1/pc2 字段；无独立落点缓存表）；Web 端无可视化界面。

**改动**：

**1. 落点结果写入 DB** — 用最轻方案：在 `assessment_results` 表加三列（不新建表）：
```sql
-- 在 ensure_schema_columns() 的 assessment_results dict 中追加：
"profile_model_id":   "TEXT"
"profile_cluster_id": "TEXT"
"profile_pc1":        "REAL"
"profile_pc2":        "REAL"
"profile_confidence": "REAL"
```
在 `routes/assessments.py` 的 `create_assessment_result` 末尾，提交 `assessment_results` 后**异步写落点**：
```python
# 若 worksheet 有匹配模型，实时计算落点并回写
try:
    position = build_assessment_profile_position(result_row, worksheet)
    conn.execute(
        """UPDATE assessment_results SET
           profile_model_id=?, profile_cluster_id=?, profile_pc1=?, profile_pc2=?, profile_confidence=?
           WHERE id=?""",
        (position["model_id"], position["position"]["cluster_id"],
         position["position"]["pc1"], position["position"]["pc2"],
         position["position"]["confidence"], result_id)
    )
    conn.commit()
except ProfilePositionUnavailable:
    pass  # 无模型的量表静默跳过，不影响提交
```
`MYSQL_VARCHAR_COLUMNS` 增 `profile_model_id/profile_cluster_id`。

**2. 安装 ECharts** — `apps/web` 内：
```bash
npm install echarts@^5 --save-exact
```

**3. 新增可视化组件** — `apps/web/src/components/ProfileScatterChart.tsx` + `ProfileRadarChart.tsx`：
```tsx
// ProfileScatterChart: 接收 position（含 pc1/pc2）+ clusters（含 pca_centroid），
//   渲染簇着色散点底图 + 用户落点「您在这里」高亮
// ProfileRadarChart: 接收 feature_profile（z_score 归一化）+ clusters 轮廓，
//   渲染双多边形对比（用户 vs 最近簇均值）
```

**4. ResearchDashboard 接入** — `apps/web/src/pages/ResearchDashboard.tsx`：
- 增 assessment_results 列表 → 选一条有 `profile_pc1` 的记录 → 调 `GET /api/assessment-results/<id>/profile-position` → 渲染两个组件。
- 无模型量表显示"暂无画像数据"，不崩溃。

**5. shared 类型同步** — `shared/types/api.ts` 新增 `AssessmentProfilePosition` 类型（`position/{pc1,pc2,cluster_id,profile_name,confidence}/clusters[]/feature_profile[]`，与 `assessment_profile_service` 返回结构对齐）；`shared/constants/api.ts` 加端点 `assessmentProfilePosition`。

**允许修改**：`backend/database.py`（`ensure_schema_columns`）、`backend/routes/assessments.py`、`apps/web/src/components/ProfileScatterChart.tsx`（新增）、`apps/web/src/components/ProfileRadarChart.tsx`（新增）、`apps/web/src/pages/ResearchDashboard.tsx`、`apps/web/package.json`、`shared/types/api.ts`、`shared/constants/api.ts`。

**完成标准**：填完 PRFQ → `assessment_results` 中 `profile_pc1/pc2` 有值；ResearchDashboard 散点+雷达可渲染；`npm run build` 通过。

---

### T4-04 用户认证打通前端（Web + 小程序，匿名数据丢弃）

**背景**：后端 `/api/auth/register` + `/api/auth/login` 已实现（werkzeug hash + JWT），`users` 表有 `username/password_hash/role/status` 字段，`generate_auth_token` 在 `routes/auth_utils.py`。Web 端 `LoginPage.tsx`/`RegisterPage.tsx` 已存在但未接 API；小程序未接。**匿名用户数据不迁移，注册后视为新用户**。

**改动**：

**1. 后端 auth_utils 补全** — 先确认 `routes/auth_utils.py` 中有：
- `generate_auth_token(user: dict) -> str`：生成含 `user_id/role/exp` 的 JWT
- `require_login` 装饰器：解析 `Authorization: Bearer <token>` header，注入 `g.current_user`
若缺 JWT 解码部分则补全；`PyJWT` 若不在 `requirements.txt` 则加入。

**2. safehomeApi 增认证方法** — `apps/web/src/services/safehomeApi.ts` 增：
```typescript
login(creds: {username: string; password: string}): Promise<{token: string; user: UserInfo}>
register(creds: {username: string; password: string; role?: string; nickname?: string}): Promise<{token: string; user: UserInfo}>
```
`requestRaw` 的默认 headers 增：`Authorization: Bearer <token>`（`authState.getToken()` 读；无 token 时不带）。

**3. authState 完善** — `apps/web/src/services/authState.ts` 确认有 `login/logout/getToken/getUser/isLoggedIn`（localStorage 持久化）；不完整则补全。

**4. LoginPage + RegisterPage 接 API** — 表单提交 → 调对应方法 → 成功后 `authState.login(token, user)` → 跳转主页；失败显示后端返回的 `error.message`。**登录成功后丢弃之前的匿名 `user_id`**（`userIdentity.ts` 中 `clearAnonymousUserId()` 若无则新增）。

**5. 小程序认证** — `apps/miniprogram/app.js` 增：
```javascript
// globalData 增 token/user 字段
// login(username, password): callContainer('/api/auth/login') → wx.setStorageSync('auth_token')
// logout(): wx.removeStorageSync('auth_token')
// 启动时 onLaunch 读缓存恢复登录态
```
`apps/miniprogram/services/api.js` 的请求 headers 增 `Authorization: Bearer ${wx.getStorageSync('auth_token') || ''}`。**同样不迁移匿名数据**（旧 `user_id` 直接丢弃）。

**6. 小程序登录/注册页** — 若无则新增 `pages/login/` 与 `pages/register/`（最小实现：用户名+密码表单，调 api.js 对应方法，成功后 navigateBack 或跳首页）。

**必须新增/确认测试**：`backend/tests/test_auth_route.py` 覆盖：注册→登录→token 有效→重复用户名 400→密码错 401→状态非 active → 403。

**允许修改**：`backend/routes/auth_utils.py`、`backend/requirements.txt`、`apps/web/src/services/authState.ts`、`apps/web/src/services/safehomeApi.ts`、`apps/web/src/services/userIdentity.ts`、`apps/web/src/pages/LoginPage.tsx`、`apps/web/src/pages/RegisterPage.tsx`、`apps/miniprogram/app.js`、`apps/miniprogram/services/api.js`、`apps/miniprogram/pages/login/**`（新增）、`apps/miniprogram/pages/register/**`（新增）、`backend/tests/test_auth_route.py`。

**完成标准**：Web 注册/登录/登出正常，token 随请求发送，登录后匿名 id 丢弃；小程序同；pytest 通过；小程序 JS/JSON 检查通过。

---

### T4-05 任务四验收
```text
云 MySQL ：healthz/deep → database.ok=true + provider=mysql；本地 sqlite 降级不破坏
量表入库 ：python backend/scripts/import_worksheets_to_db.py（幂等）→ GET /api/assessments 数据一致
           → healthz/deep: worksheets_sync_ok=true → pytest 通过
落点写 DB ：填完 PRFQ → assessment_results.profile_pc1/pc2 有值 → GET profile-position 返回正确
Web 可视化：npm run build 通过 → ResearchDashboard 散点+雷达可渲染 → 无画像量表不崩溃
认证      ：Web 注册→登录→登出→token 随请求→匿名 id 丢弃；小程序同；pytest 通过；小程序 JS/JSON 检查通过
```

---

# 任务五：训练卡内容升级 + 推荐算法完善

**目标**：① 训练卡内容达到循证心理学实操水准（UP/CBT 框架，家长 10 张 + 学生 10 张，针对量表核心构念）；② 修复量表维度分→卡推荐的断链；③ 画像簇→卡映射；④ 修复前后端代码逻辑缺陷。
**执行时机**：T5-01/T5-05 无前置依赖，可立刻执行；T5-03 依赖 T1-04（量表题项就绪）；T5-04 依赖 T2-x（画像模型就绪）。

---

### T5-01 训练卡内容重写（20 张，UP/CBT 精准版）

**背景**：现有 12 张卡语言偏模板化，目标达到"循证心理干预实操手册"水准——措辞精准、温暖、去 AI 味，聚焦可执行小动作，每张卡对应量表中的一个核心构念。

**内容框架（保持 UP/CBT，不引入新框架）**：

家长 10 张（对应 PRFQ 三维 + ERQ + 亲子沟通）：
| 卡 ID | 对应构念 | 核心技能 |
|---|---|---|
| `prfq_pm_awareness` | PRFQ-PM（前心智化）| 识别自动反应模式，暂停前先觉察 |
| `prfq_cm_tolerance` | PRFQ-CM（确定心理状态）| 容忍不确定：孩子内心状态不总是可读 |
| `prfq_ic_curiosity` | PRFQ-IC（兴趣好奇）| 用好奇替代解释，开放式问话练习 |
| `erq_reappraisal_parent` | ERQ 认知重评 | 对情境换一个解释，找第二种可能 |
| `erq_suppression_release` | ERQ 表达抑制 | 识别压抑信号，低风险表达一个感受 |
| `repair_after_rupture` | 关系修复 | 冲突后重建连接的具体话术步骤 |
| `validation_before_advice` | 非评判回应 | 先确认后建议，不急着解决 |
| `parent_body_grounding` | 身体信号 | 身体感觉作为情绪信号的落地练习 |
| `specific_request_replace_threat` | 行为替代 | 把威胁/催促换成一个5分钟可执行的小请求 |
| `one_open_question` | 亲子沟通 | 一次只问一个开放式问题，不叠问 |

学生 10 张（对应 SCS + ERQ + RSCA + student_profile）：
| 卡 ID | 对应构念 | 核心技能 |
|---|---|---|
| `scs_self_kindness` | SCS 自我善意 | 把自责改为朋友式支持句 |
| `scs_common_humanity` | SCS 共同人性 | 这种困难不只我一个人有 |
| `scs_mindful_moment` | SCS 正念觉察 | 不放大也不压制：观察情绪一分钟 |
| `erq_reappraisal_student` | ERQ 认知重评 | 找压力情境的第二种解读 |
| `erq_expression_gentle` | ERQ 表达抑制 | 写下一个还没说出口的感受 |
| `rsca_emotion_regulation` | RSCA 情绪调节 | 三步稳定情绪：命名-呼吸-小动作 |
| `rsca_positive_cognition` | RSCA 积极认知 | 找一个今天做到了的小事实 |
| `exam_micro_start` | 考试压力 | 把任务拆到"10分钟可开始"的颗粒度 |
| `auto_thought_rewrite` | CBT 自动想法 | 写下→找证据→改写一句更平衡的话 |
| `body_scan_before_study` | 身体意识 | 开始学习前60秒身体扫描落地 |

**每张卡写作标准**（与现有结构字段对齐，提升内容深度）：
- `steps[]`：3-4 步，每步一句短句，行动动词开头，无"尝试""可以"等软化词，具体到"说什么/做什么"
- `example`：1-2 句真实对话/独白，不用引号嵌套引号，不抽象
- `reflection_questions[]`：3 题，锚定当次练习中的具体行为（"我刚才命名的是哪一个词"而非"有什么感受"）
- `suitable_for[]` / `not_suitable_for[]`：实际临床适应症描述，不泛化
- `purpose`：一句话说明练习的**行为机制**，不说效果承诺

**允许修改**：`content/training_cards.json`。**严禁**：修改卡的 id（已被 `assessment_training_map` 和 `diary_training_map` 引用的旧卡 id）；删除现有卡（只能新增或原地升级文字）。

**完成标准**：20 张卡内容通过 `validate_content.py`；FORBIDDEN_TERMS 无命中；每张卡 steps≥3、example 非空、reflection_questions≥2。

---

### T5-02 推荐算法断链修复（维度分评估引擎）

**背景**：`assessment_training_map.json` 规则有 `trigger_condition.dimension` + `trigger_condition.level`（如 PRFQ_IC "needs_support"），但 `_training_rules_for_worksheet()`（assessments.py:146-159）只按 `worksheet_id/scale_id` 过滤，从不评估维度分。用户填完量表后，规则返回给前端但**从不选择卡**。

**改动**：

**1. 阈值评估逻辑** — 新增 `backend/services/training_recommendation_service.py`：
```python
def evaluate_training_rules(worksheet_id: str, scores_json: str) -> list[dict]:
    """
    从 assessment_training_map.json 中选出满足维度条件的规则。
    阈值策略（按优先级）：
    1. 有对应 content/profiles/ 模型 → 用 feature.mean 作基准，z < -0.5 → "needs_support"
    2. 无模型 → 用量表 score_min/score_max 中点，低于中点 → "needs_support"，高于 → "high"
    """
    rules = _load_all_rules()  # 读 assessment_training_map.json
    scores = json_loads(scores_json, {})
    dim_map = {d["key"]: d["score"] for d in scores.get("dimensions", [])}
    model = _find_profile_model(worksheet_id)  # 从 content/profiles/ 找同 worksheet_id 的模型
    result = []
    for rule in rules:
        if not _matches_worksheet(rule, worksheet_id):
            continue
        if _evaluate_condition(rule["trigger_condition"], dim_map, model):
            result.append(rule)
    return result

def _evaluate_condition(condition, dim_map, model) -> bool:
    dimension = condition.get("dimension")
    level = condition.get("level")
    if not dimension:          # 无维度条件 → 直接匹配
        return True
    score = dim_map.get(dimension)
    if score is None:
        return False
    threshold = _get_threshold(dimension, model)  # 返回 {"support_below": x, "high_above": y}
    return _check_level(level, score, threshold)
```

**2. 接入 create_assessment_result** — 在 `routes/assessments.py` 的 `create_assessment_result` 末尾（写 DB 后）：
```python
from services.training_recommendation_service import evaluate_training_rules
training_rules = evaluate_training_rules(worksheet["id"], json_dumps(scores))
result["training_recommendation_rules"] = training_rules
result["recommended_card_ids"] = _flatten_card_ids(training_rules) or result.get("recommended_card_ids", [])
```

**3. 升级 card_service.py `recommend_cards` fallback** — 无 tag 匹配时改为按类型多样化采样（每种 type 取1张）而非顺序前 N：
```python
if not matched:
    types = {}
    for card in cards:
        types.setdefault(card.get("type", ""), []).append(card)
    return [cards[0] for cards in types.values()][:limit]
```

**4. 更新 assessment_training_map.json** — 为 PRFQ 三个维度（PM/CM/IC）、ERQ 两个维度（CR/ES）、RSCA、SCS 各补充规则，覆盖 `needs_support`/`high` 两种触发条件，每条规则 `recommended_card_ids` 指向 T5-01 新卡。

**必须新增测试** `backend/tests/test_training_recommendation.py`：PRFQ 低 IC 分 → 触发 `prfq_ic_curiosity` 等卡；无维度条件规则直接命中；无模型量表用中点阈值；高风险 → 空列表。

**允许修改**：`backend/services/training_recommendation_service.py`（新增）、`backend/routes/assessments.py`、`backend/services/card_service.py`、`content/assessment_training_map.json`、`backend/tests/**`。

**完成标准**：填完 PRFQ 后 API 返回 `recommended_card_ids` 非空且与维度分对应；pytest 通过。

---

### T5-03 日记→训练卡规则补全

**背景**：`diary_training_map.json` 现有 4 条规则（对应 4 个 feedback_rule_id）；`feedback_rules.json` 中可能有更多规则 id 未覆盖；`_match_diary_training_rules()` 硬限 `[:1]`。

**改动**：
- 检查 `content/feedback_rules.json` 所有 rule id，为未覆盖的补充 `diary_training_map.json` 规则（指向 T5-01 新卡）
- 将 `_match_diary_training_rules()` 的 `[:1]` 改为返回最多 2 条（今日练习 + 备用），前端只展示第一条，第二条作为"还可以做"备选
- 规则补全优先：高强度情绪、自责/自我批评、关系冲突三类场景各至少1条新规则

**允许修改**：`content/diary_training_map.json`、`backend/routes/feedback.py`（`[:1]`→`[:2]`）。**完成标准**：`feedback_rules.json` 中每个 rule id 至少有一条对应日记训练规则；validate_content.py 通过。

---

### T5-04 画像簇→训练卡映射建议

**背景**：`content/profiles/*.json` 每个簇有 `objective_desc`/`support_advice`/`dimension_means`，但无 `recommended_card_ids`。算法用 C 方案：基于簇特征自动建议映射，用户审核。

**改动**：

**1. 生成建议** — 新增 `analysis/profiling/suggest_cluster_card_map.py`（离线脚本）：
读每个 profile JSON → 对每个簇：检查 `dimension_means` 中最低的2-3个维度 → 在 `training_cards.json` 中找 `target_skill` 最匹配的卡 → 输出建议映射到 `docs/10Claude协作/画像簇训练卡映射建议.md`（供人工审核）。

**2. 审核后落地** — 人工审核建议映射 → 修改对应 `content/profiles/*.json`，为每个 `clusters[i]` 加：
```json
"recommended_card_ids": ["card_id_1", "card_id_2"],
"card_reason": "PM 维度偏低，优先识别自动反应"
```

**3. 接入落点接口** — `assessment_profile_service.py` 的 `build_assessment_profile_position` 返回值中，在 `clusters[i]` 里透传 `recommended_card_ids`；前端结果页可直接展示"与你最近的群体通常练习的卡"。

**允许修改**：`analysis/profiling/suggest_cluster_card_map.py`（新增）、`content/profiles/**`（人工审核后）、`backend/services/assessment_profile_service.py`。**完成标准**：PRFQ 每个簇有 `recommended_card_ids`；接口返回中含簇推荐卡；建议文档已产出供审核。

---

### T5-05 代码逻辑缺陷修复清单

**已知问题与修复方案**：

| 文件 | 问题 | 修复 |
|---|---|---|
| `task-detail/index.js` | 硬编码 `TASKS` 字典（10个任务）与 API 卡数据完全独立，新增卡永远 fallback 到 `nonjudgmental_company`，**这是最高优先级 bug** | 当前保留不改（T3 视觉重构时彻底重构），**在文件顶部加注释标记 `// TODO T3: REFACTOR - hardcoded, disconnect from API`** |
| `training-card/index.js:36` | `cardIds.length > 0` 时调 `api.listCards()` 拉全量再过滤，浪费 | 改为直接用传入的 cardIds 匹配已获取到的卡列表；或新增 `GET /api/cards/:id` 端点 |
| `training-card/index.js:formatCard` | `todayGoal`/`reflectionPrompt` 是固定字符串，与卡无关 | 改为读卡的 `reflection_questions[0]` 和 `suitable_for[0]`；字段不存在时才用默认值 |
| `feedback-result/index.js:buildEmotionOverview` | 情绪词硬编码（`"着急 / 生气 / 委屈"`），与实际 tag 无关 | 改为用 `feedback.labels` 数组直接组合；无 labels 时显示触发摘要 |
| `card_service.py:recommend_cards` | 无匹配时按顺序返回前N（T5-02 已修） | 见 T5-02 |
| `feedback.py:_match_diary_training_rules` | `[:1]` 限制最多1条规则 | 见 T5-03 |

**允许修改**：`apps/miniprogram/pages/training-card/index.js`、`apps/miniprogram/pages/feedback-result/index.js`、`apps/miniprogram/pages/task-detail/index.js`（只加注释）、`backend/services/card_service.py`。

**完成标准**：小程序 JS/JSON 检查通过；`training-card` 页的 `todayGoal` 随卡变化；`buildEmotionOverview` 不再硬编码情绪词。

---

### T5-06 任务五验收
```text
内容    ：validate_content.py 通过；20 张卡 steps≥3、example 非空；FORBIDDEN_TERMS 无命中
算法    ：填完 PRFQ（IC 维度低分）→ API 返回对应卡 ID → pytest test_training_recommendation 通过
日记链路：日记提交 → feedback-result 显示训练卡推荐 → 最多2条规则可见
画像映射：PRFQ 各簇有 recommended_card_ids；建议文档已产出
代码修复：小程序 JS/JSON 检查通过；todayGoal/emotionOverview 不再使用硬编码字符串
task-detail bug：文件顶部已加 TODO 注释，等待 T3 重构
```

# 任务六：前端改造（小程序端）

> 创建时间：2026-06-30
> 负责人：Claude（方向把握+技术安排）+ Codex（技术实现）
> 改造范围：`apps/miniprogram/pages/*`（暂不动 `apps/web/*`）

---

## ⚠️ 执行前必读 · 全章订正总表（Claude 核实修订 2026-07-01）

> 本任务六初稿大量"原代码"标注了"(推测)"，经逐文件核实，部分行号/字段名/API 名/"已完成代码"与真实代码**不符甚至虚构**。Codex 执行时**以下表与各节内的【Claude订正】块为准**，原文保留仅作对照。**凡与本表冲突，一律以本表为准。**

### A. 全局 API 方法名（最高频错误，按计划调用一律 `TypeError`）

| 计划写的（错） | 真实方法（`apps/miniprogram/services/api.js`） | 返回 |
|---|---|---|
| `api.getAssessments()` | `api.listAssessments(params)`（:360） | `{ worksheets / items }` |
| `api.getDiaries(params)` | `api.listDiaries(params)`（:277） | `{ items: [...] }`（非裸数组） |
| `api.getTrainingCards()` | `api.listCards()`（:347）/ `api.recommendCards(params)`（:351） | `{ cards }` / 推荐卡 |
| `api.getWeeklyReport()` | ✅ 存在（:394），此名正确 | 周报对象 |

### B. 后端约定（T6-01 等）

| 主题 | 计划写的（错） | 真实约定 |
|---|---|---|
| 建表容器 | `SCHEMA` 列表 | **`SCHEMA_SQL`**（`models.py:28`）；索引加 `INDEX_SQL`（:399） |
| 按天统计 SQL | `WHERE DATE(created_at)=DATE('now')` | **禁用**。MySQL 下 `DATE('now')` 解析为 NULL→统计恒为 0。统一用 `substr(created_at,1,10)=?`，日期串在 **Python 端**用 `date.today().isoformat()` 算好再传参（见 `report_service.py:26`） |
| `parse_int` | `parse_int(x, default=20, min_val=1, max_val=100)` | **只有 `default` 参数**，无 min/max → 写了会 `TypeError`。范围校验自己写 `if`（`routes/utils.py:70`） |
| 工具签名 | — | `fail(code, message, status=400)`、`ensure_user(conn, user_id, nickname=None)`、`new_id(prefix)` 必传 prefix；蓝图变量名统一 `bp`，`app.py` 用 `from routes.X import bp as X_bp` |

### C. 周报字段（T6-04/T6-05）

- 周报对象**没有** `diaries_count / emotions_count / checkins_count / profiles_count`（计划所谓"原代码用这些"是**虚构**）。
- 真实字段（`report_service.py:85-101`）：`frequent_scenes`、`frequent_emotions`、`common_patterns` 均为 **`[[名称, 次数], ...]` 元组列表**（不是纯字符串数组）；`completed_cards` 是字符串数组；`profile_trend.profile_count`；`next_week_suggestion`。
- `profile_trend` **不落库**（`weekly_reports` 表无此列），只在 HTTP 响应透出。
- 前端 `weekly-report/index.js` 已有 `formatPairs([[名,次]])→{name,count}`，4 格已正确绑 `frequentScenes.length` 等——**不要按"原代码 diaries_count"去改**。

### D. 训练卡（T6-06）

- 实际 **34 张**（全 enabled）。文档里"20 张/12 张"作废，统一 **34**。
- 字段名：计划的 `theory_background`→真实 **`theory_source`**；`target_competency`→真实 **`target_skill`**；`practice_tips` **不存在**（最近似 `reflection_questions`）。**改文案时复用现有字段名，不要新造同义字段并存。**
- 硬约束（`validate_content.py` + `schemas/training_cards.schema.json`）：`theory_source`/`target_skill`/`reflection_questions`/`not_suitable_for` 为 required，**不可删**；`reflection_questions` ≥2 条；每卡 `not_suitable_for` 必须含"高风险/危机/安全/现实支持"之一。好消息：脚本不拦额外字段，"前额叶/杏仁核/认知加工"等不在禁用词（禁用词仅 8 个）。

### E. 量表 worksheet（T6-02）

- **无任何 demo 量表**（数据全走 `api.listAssessments()`）→ 计划"删除所有 demo 量表"**无对象可删**，该子目标取消。
- 启用数核对无误：**16 个（学生5 / 家长1 / 成人10）**。
- `audience_class` 真实取值 **`student / parent / adult`**（英文）；标题字段是 **`display_title`**（非 `title`）。
- **分组维度（用户决策 2026-07-01）：保留现有"Tab=人群 + section=反射弧节点(`reflex_node`)"双层结构**，**不改为按 audience 分组**（否则与 Tab 重复且丢节点维度）。T6-02 只做：修选项截断 bug + 接真实搜索/分类，不动分组维度。
- 真实函数名：`refreshVisibleAssessments`（非 applyFilters）、`buildAssessmentSections`（非 buildCategorySections）。

### F. 方法名 / 其它（T6-04）

- home 页统计方法是 **`refreshTodayRecordCount`**（非 `loadTodayRecordCount`）。
- `created_at` 是 **UTC**（`now_iso()`）；前端 `new Date(created_at)` 按本地时区解析，"今天/昨天"判断会偏移——T6-04 时间格式化需按 UTC 处理或后端返回本地化字段。
- 字段名 `scene / event_description / parent_emotion` 前后端一致（✅）；`feedback-result` 接收 `diary_id`（✅）。

### G. T6-08 全节为"从零实现"（不是对接已有）

> T6-08 声称"Claude 已提供/已完成"的 **后端 7 项 + 前端 4 页面 + home 消息入口 + profile 改造，经核实全部不存在**（`messages` 表/路由、`/api/auth/wechat-login`、`/api/profile/stats`、`calculate_consecutive_days`、`users.wechat_openid/avatar_url`、supervision 回复建消息、`pages/messages|message-detail|emergency-guide|emergency-resources/`、`loadUnreadCount/openMessages` 均无）。**整节按"从零新建"执行，详见 T6-08 节内【Claude订正】重写规格。**

### 各节状态速览

| 节 | 状态 | 关键动作 |
|---|---|---|
| T6-01 | 方向OK，3处技术坑 | 见节内订正：SCHEMA_SQL / 日期SQL / parse_int |
| T6-02 | 部分订正 | 保留节点分组；删"删demo"；选项截断改 `keep-all`；API/函数名 |
| T6-03 | ✅ 行号精确，可照做 | 无需订正 |
| T6-04 | 部分订正 | `listDiaries` / `refreshTodayRecordCount` / UTC时区 |
| T6-05 | 部分订正 | 删虚构 `diaries_count` 叙述；对齐元组字段 |
| T6-06 | 多处订正 | `theory_source`/`target_skill`；34张；`listCards/recommendCards`；required不可删 |
| T6-07 | 保留GitHub+补防护 | 微信合法域名 + 版权/内容审核/伦理免责 |
| T6-08 | 整节重写 | 从零实现规格 |

---

## T6-01：情绪温度计功能开发（后端+前端）

### 一、任务目标

将首页"情绪天气"功能改造为"情绪温度计"功能，支持用户快速记录即时情绪波动和简短事件。

**核心变更：**
1. 首页卡片文案：`情绪天气` → `情绪温度计`，`今天已记录 X 次` → `即时情绪记录`
2. 新增独立的情绪温度计记录页面（非情绪日记）
3. 新增后端 API 和数据表支持温度计记录

---

### 二、后端代码审核结论

**现有相关代码：**
- `backend/models.py:90-107` - `emotion_diaries` 表（详细日记）
- `backend/routes/diaries.py` - 日记 CRUD 接口
- `backend/database.py:413` - `ensure_column` 动态加列
- `shared/types/api.ts` - 前后端类型定义
- `shared/constants/api.ts:1-41` - API 端点常量

**审核结论：**
- ✅ 数据库设计：新建独立表 `emotion_thermometer`（不与日记混用）
- ✅ API 设计：新建 `/api/emotion-thermometer` 端点
- ✅ 类型定义：需在 `shared/types/api.ts` 新增接口
- ✅ 常量定义：需在 `shared/constants/api.ts` 新增端点
- ✅ 风险等级：仅 low/medium/high 三级（无 critical）

---

### 三、详细实现方案

#### 3.1 后端实现

##### 3.1.1 数据库表设计

**文件：`backend/models.py`**

在 `SCHEMA` 列表末尾（约第 600 行附近）追加：

> **【Claude订正】** 真实变量名是 **`SCHEMA_SQL`**（`backend/models.py:28`，一个 list，元素为 CREATE TABLE 字符串），不是 `SCHEMA`。请追加到 `SCHEMA_SQL`。`init_db()`（`database.py:270`）遍历 `SCHEMA_SQL` 建表，幂等。本表无强索引需求；如需按 `user_id` 查询加速，把 `CREATE INDEX ...` 追加进 `INDEX_SQL`（`models.py:399`）。`emotion_thermometer` 经核实为全新表（content/schema/代码层均无既有定义）。

```python
"""
CREATE TABLE IF NOT EXISTS emotion_thermometer (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    intensity_level INTEGER NOT NULL,
    brief_text TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""",
```

**字段说明：**
- `id`: 主键，格式 `thermo_<uuid>`
- `user_id`: 用户ID
- `intensity_level`: 情绪波动强度，1-10（1-3=低波动，4-7=中等波动，8-10=高波动）
- `brief_text`: 一句话内容（事件+感受+想法）
- `created_at`: 创建时间（ISO 8601格式）

##### 3.1.2 API 路由实现

**新建文件：`backend/routes/emotion_thermometer.py`**

```python
"""Emotion thermometer endpoints."""

from flask import Blueprint, request

from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts
from routes.utils import (
    fail,
    ok,
    parse_int,
    require_fields,
    require_user_id,
)

bp = Blueprint("emotion_thermometer", __name__, url_prefix="/api/emotion-thermometer")


@bp.post("")
def create_thermometer_record():
    """创建情绪温度计记录"""
    payload = request.get_json(silent=True) or {}
    missing = require_fields(payload, ["intensity_level", "brief_text"])
    if missing:
        return fail("missing_fields", f"缺少必填字段：{', '.join(missing)}")

    try:
        user_id = require_user_id(payload)
    except ValueError as exc:
        return fail("validation_error", str(exc), status=400)

    intensity_level = payload.get("intensity_level")
    brief_text = payload.get("brief_text", "").strip()

    # 验证 intensity_level 范围
    if not isinstance(intensity_level, int) or not (1 <= intensity_level <= 10):
        return fail("validation_error", "intensity_level 必须是 1-10 之间的整数")

    # 验证 brief_text 长度
    if not brief_text:
        return fail("validation_error", "brief_text 不能为空")
    if len(brief_text) > 500:
        return fail("validation_error", "brief_text 不能超过 500 字符")

    timestamp = now_iso()
    record_id = new_id("thermo")

    with get_connection() as conn:
        ensure_user(conn, user_id, payload.get("nickname"))
        conn.execute(
            """
            INSERT INTO emotion_thermometer (
                id, user_id, intensity_level, brief_text, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (record_id, user_id, intensity_level, brief_text, timestamp),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM emotion_thermometer WHERE id = ?", (record_id,)
        ).fetchone()

    return ok(row_to_dict(row))


@bp.get("")
def list_thermometer_records():
    """获取情绪温度计记录列表"""
    user_id = request.args.get("user_id", "demo-parent")
    limit = parse_int(request.args.get("limit"), default=20, min_val=1, max_val=100)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM emotion_thermometer
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        # 统计今日记录数
        today_count_row = conn.execute(
            """
            SELECT COUNT(*) as count FROM emotion_thermometer
            WHERE user_id = ? AND DATE(created_at) = DATE('now')
            """,
            (user_id,),
        ).fetchone()

    today_count = today_count_row["count"] if today_count_row else 0

    return ok({"items": rows_to_dicts(rows), "total": len(rows), "today_count": today_count})
```

> **【Claude订正 · 上方 `list_thermometer_records` 有两处会出错，必改】**
>
> **(1) `parse_int` 没有 `min_val`/`max_val` 参数**（`routes/utils.py:70` 只有 `default`）。写 `parse_int(..., min_val=1, max_val=100)` 会 `TypeError`。改为：
> ```python
> limit = parse_int(request.args.get("limit"), default=20)
> limit = max(1, min(limit or 20, 100))  # 范围裁剪手动写
> ```
>
> **(2) 禁用 `DATE(created_at) = DATE('now')`** —— 这是双后端兼容坑：MySQL 把字符串 `'now'` 当日期解析得 `NULL`，`WHERE ... = NULL` 恒为假，`today_count` 在 MySQL 永远是 0（仅 SQLite 正常）；方言层 `_mysqlize_query` 只换占位符/引号，不会翻译该函数。改用项目唯一约定（Python 端算日期串 + `substr`，见 `report_service.py:26`）：
> ```python
> from datetime import date
> today_str = date.today().isoformat()  # 'YYYY-MM-DD'
> today_count_row = conn.execute(
>     "SELECT COUNT(*) AS count FROM emotion_thermometer "
>     "WHERE user_id = ? AND substr(created_at, 1, 10) = ?",
>     (user_id, today_str),
> ).fetchone()
> ```
> 注：`created_at` 由 `now_iso()` 写为 **UTC** ISO，`substr(...,1,10)` 取日期前缀，两后端一致。本期按 UTC 自然日统计；若要严格"用户本地自然日"需另定时区策略（与 T6-04 时间显示同源问题）。
>
> **(3) import 与蓝图写法（3.1.2/3.1.3）经核实正确**：`from database import ensure_user, get_connection, new_id, now_iso, row_to_dict, rows_to_dicts` 与 `from routes.utils import fail, ok, parse_int, require_fields, require_user_id` 均可用；蓝图变量名 `bp`、`app.py` 用 `from routes.emotion_thermometer import bp as emotion_thermometer_bp` + `app.register_blueprint(...)` 均符合现有约定，照做即可。

##### 3.1.3 注册蓝图

**文件：`backend/app.py`**

在文件顶部导入区（约第 18 行附近）添加：

```python
from routes.emotion_thermometer import bp as emotion_thermometer_bp
```

在蓝图注册区（约第 75 行附近）添加：

```python
app.register_blueprint(emotion_thermometer_bp)
```

##### 3.1.4 类型定义（shared）

**文件：`shared/types/api.ts`**

在文件末尾（约第 400 行附近）添加：

```typescript
export interface EmotionThermometerRecord {
  id: ID;
  user_id: ID;
  intensity_level: number; // 1-10
  brief_text: string;
  created_at: ISODateTime;
}

export interface EmotionThermometerInput {
  user_id?: ID;
  nickname?: string;
  intensity_level: number;
  brief_text: string;
}

export interface EmotionThermometerListResponse {
  items: EmotionThermometerRecord[];
  total: number;
  today_count: number;
}
```

##### 3.1.5 API 常量定义

**文件：`shared/constants/api.ts`**

在 `API_ENDPOINTS` 对象中（约第 40 行附近）添加：

```typescript
emotionThermometer: "/api/emotion-thermometer",
```

#### 3.2 前端实现

##### 3.2.1 小程序 API 服务

**文件：`apps/miniprogram/services/api.js`**

在 `API_ENDPOINTS` 对象中（约第 27 行附近）添加：

```javascript
emotionThermometer: "/api/emotion-thermometer",
```

在文件末尾（约第 200 行附近）的 `return` 对象中添加：

```javascript
// 情绪温度计
createThermometerRecord(input) {
  return request("POST", API_ENDPOINTS.emotionThermometer, input);
},
getThermometerRecords(params = {}) {
  return request("GET", API_ENDPOINTS.emotionThermometer + queryString(params));
},
```

##### 3.2.2 首页卡片改造

**文件：`apps/miniprogram/pages/home/index.wxml`**

**修改位置：第 14-22 行**

**原代码：**
```xml
<!-- 情绪天气：紧凑横条 -->
<button class="mood-strip" bindtap="startDiary">
  <view class="mood-strip-left">
    <text class="mood-strip-label">情绪天气</text>
    <text class="mood-strip-sub">今天已记录 {{todayRecordCount}} 次{{todayRecordCountReady ? '' : '，联网后更新'}}</text>
  </view>
  <text class="mood-strip-face">☺</text>
  <text class="mood-strip-action">记录 ›</text>
</button>
```

**修改为：**
```xml
<!-- 情绪温度计：紧凑横条 -->
<button class="mood-strip" bindtap="startThermometer">
  <view class="mood-strip-left">
    <text class="mood-strip-label">情绪温度计</text>
    <text class="mood-strip-sub">即时情绪记录</text>
  </view>
  <text class="mood-strip-face">🌡</text>
  <text class="mood-strip-action">记录 ›</text>
</button>
```

**文件：`apps/miniprogram/pages/home/index.js`**

**修改位置：约第 110 行附近**

**原方法：**
```javascript
startDiary() {
  wx.navigateTo({ url: "/pages/diary-form/index" });
},
```

**修改为：**
```javascript
startThermometer() {
  wx.navigateTo({ url: "/pages/thermometer/index" });
},
```

同时保留原有的 `startDiary` 方法（用于其他入口）。

删除 `todayRecordCount` 和 `todayRecordCountReady` 相关逻辑：
- 删除 `data` 中的这两个字段（第 26-27 行）
- 删除 `onShow` 中的 `loadTodayRecordCount` 调用（第 117 行附近）
- 删除 `loadTodayRecordCount` 方法（第 120-145 行附近）

##### 3.2.3 新建情绪温度计页面

**新建目录：`apps/miniprogram/pages/thermometer/`**

**新建文件：`apps/miniprogram/pages/thermometer/index.wxml`**

```xml
<view class="safe-page thermometer-page">
  
  <!-- 页面标题 -->
  <view class="safe-section">
    <text class="safe-h1">情绪温度计</text>
    <text class="safe-caption">记录此刻的情绪波动</text>
  </view>

  <!-- 温度计标尺 -->
  <view class="safe-section">
    <text class="thermometer-label">当前情绪波动程度</text>
    <view class="thermometer-scale">
      <view class="thermometer-bar">
        <view class="thermometer-fill" style="height: {{intensity * 10}}%;"></view>
      </view>
      <view class="thermometer-marks">
        <text class="thermometer-mark" wx:for="{{[10,9,8,7,6,5,4,3,2,1]}}" wx:key="*this">{{item}}</text>
      </view>
    </view>
    <slider 
      class="thermometer-slider" 
      min="1" 
      max="10" 
      step="1" 
      value="{{intensity}}" 
      bindchange="onIntensityChange" 
      activeColor="var(--safe-primary)"
      backgroundColor="var(--safe-border)"
    />
    <view class="thermometer-level-hint">
      <text class="safe-caption">{{intensityHint}}</text>
    </view>
  </view>

  <!-- 一句话输入 -->
  <view class="safe-section">
    <text class="thermometer-label">刚才发生了什么？</text>
    <textarea 
      class="thermometer-textarea" 
      placeholder="用一句话记录：发生的事件、你的感受和想法"
      maxlength="500"
      value="{{briefText}}"
      bindinput="onBriefTextInput"
      auto-height
    />
    <text class="safe-caption">{{briefText.length}}/500</text>
  </view>

  <!-- 提交按钮 -->
  <view class="safe-section">
    <button 
      class="safe-primary-button" 
      bindtap="submitRecord"
      disabled="{{!canSubmit}}"
    >
      保存记录
    </button>
  </view>

  <!-- 非诊断边界说明 -->
  <view class="safe-section">
    <view class="alert-card alert-card--info">
      <text class="safe-caption">本功能仅用于自我觉察和情绪记录，不构成诊断或评估。</text>
    </view>
  </view>

</view>
```

**新建文件：`apps/miniprogram/pages/thermometer/index.js`**

```javascript
const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

const INTENSITY_HINTS = {
  1: "很平静",
  2: "略有波动",
  3: "轻微波动",
  4: "有些波动",
  5: "中等波动",
  6: "明显波动",
  7: "较强波动",
  8: "强烈波动",
  9: "非常强烈",
  10: "极度波动",
};

Page({
  data: {
    intensity: 5,
    intensityHint: "中等波动",
    briefText: "",
    canSubmit: false,
  },

  onLoad() {
    this.updateIntensityHint();
  },

  onIntensityChange(e) {
    const intensity = parseInt(e.detail.value, 10);
    this.setData({ intensity }, () => {
      this.updateIntensityHint();
      this.checkCanSubmit();
    });
  },

  onBriefTextInput(e) {
    this.setData({ briefText: e.detail.value }, () => {
      this.checkCanSubmit();
    });
  },

  updateIntensityHint() {
    const hint = INTENSITY_HINTS[this.data.intensity] || "中等波动";
    this.setData({ intensityHint: hint });
  },

  checkCanSubmit() {
    const canSubmit = this.data.briefText.trim().length > 0;
    this.setData({ canSubmit });
  },

  async submitRecord() {
    if (!this.data.canSubmit) {
      return;
    }

    wx.showLoading({ title: "保存中..." });

    try {
      const result = await api.createThermometerRecord({
        intensity_level: this.data.intensity,
        brief_text: this.data.briefText.trim(),
      });

      wx.hideLoading();

      if (result.ok) {
        wx.showToast({
          title: "记录成功",
          icon: "success",
          duration: 2000,
        });

        setTimeout(() => {
          wx.navigateBack();
        }, 2000);
      } else {
        wx.showToast({
          title: result.error?.message || "保存失败",
          icon: "none",
          duration: 3000,
        });
      }
    } catch (err) {
      wx.hideLoading();
      wx.showToast({
        title: "网络错误，请重试",
        icon: "none",
        duration: 3000,
      });
      console.error("submitRecord error:", err);
    }
  },
});
```

**新建文件：`apps/miniprogram/pages/thermometer/index.wxss`**

```css
.thermometer-page {
  padding-bottom: 120rpx;
}

.thermometer-label {
  display: block;
  color: var(--safe-title);
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 24rpx;
}

.thermometer-scale {
  display: flex;
  align-items: stretch;
  gap: 24rpx;
  margin-bottom: 32rpx;
}

.thermometer-bar {
  width: 80rpx;
  height: 600rpx;
  background: var(--safe-bg-soft);
  border: 2rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  position: relative;
  overflow: hidden;
}

.thermometer-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, var(--safe-primary), var(--safe-primary-soft));
  transition: height 0.3s ease;
}

.thermometer-marks {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12rpx 0;
}

.thermometer-mark {
  display: block;
  color: var(--safe-muted);
  font-size: 24rpx;
  line-height: 1;
}

.thermometer-slider {
  width: 100%;
  margin-bottom: 16rpx;
}

.thermometer-level-hint {
  text-align: center;
  padding: 16rpx;
  background: var(--safe-primary-pale);
  border-radius: var(--safe-radius-sm);
}

.thermometer-textarea {
  width: 100%;
  min-height: 200rpx;
  padding: 24rpx;
  background: var(--safe-card);
  border: 2rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  font-size: 28rpx;
  line-height: 1.6;
  color: var(--safe-text);
  margin-bottom: 16rpx;
}
```

**新建文件：`apps/miniprogram/pages/thermometer/index.json`**

```json
{
  "navigationBarTitleText": "情绪温度计",
  "usingComponents": {
    "section-title": "/components/section-title/index",
    "alert-card": "/components/alert-card/index"
  }
}
```

##### 3.2.4 注册页面路由

**文件：`apps/miniprogram/app.json`**

在 `pages` 数组中（约第 12 行附近）添加：

```json
"pages/thermometer/index",
```

---

### 四、验收标准

#### 4.1 后端验收

**运行测试：**
```bash
cd D:\codex\workspace\safehome1.0\backend
python -m pytest tests -q
```

**手动测试 API：**

1. **创建记录：**
```bash
curl -X POST http://127.0.0.1:5000/api/emotion-thermometer \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-parent",
    "intensity_level": 7,
    "brief_text": "孩子写作业磨蹭，我有点着急"
  }'
```

预期响应：
```json
{
  "ok": true,
  "data": {
    "id": "thermo_xxx",
    "user_id": "demo-parent",
    "intensity_level": 7,
    "brief_text": "孩子写作业磨蹭，我有点着急",
    "created_at": "2026-06-30T..."
  }
}
```

2. **获取列表：**
```bash
curl http://127.0.0.1:5000/api/emotion-thermometer?user_id=demo-parent
```

预期响应：
```json
{
  "ok": true,
  "data": {
    "items": [...],
    "total": 1,
    "today_count": 1
  }
}
```

#### 4.2 前端验收

**在微信开发者工具中测试：**

1. 启动小程序，进入首页
2. 确认首页卡片显示"情绪温度计"+"即时情绪记录"
3. 点击卡片，跳转到情绪温度计页面
4. 拖动滑块，确认：
   - 温度计填充高度变化
   - 底部提示文案跟随变化（1=很平静，10=极度波动）
5. 输入一句话内容（至少1个字符）
6. 确认"保存记录"按钮可点击
7. 点击提交，确认：
   - 显示"保存中..."加载提示
   - 成功后显示"记录成功"
   - 2秒后自动返回首页
8. 返回首页，再次点击"情绪温度计"，确认能再次记录

#### 4.3 边界验收

**必须符合：**
- ✅ 非诊断文案：页面底部显示"不构成诊断或评估"
- ✅ API 不变：不破坏现有 `/api/diaries` 接口
- ✅ 核心链路：情绪日记功能保持可用
- ✅ 风险等级：无风险判断逻辑（温度计纯记录功能）
- ✅ 代码检查：小程序 JS/JSON 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
```

---

### 五、完成后更新文档

**1. 更新 API 文档：**
文件：`docs/03_技术真相/API接口文档.md`

在"已实现接口"章节末尾添加：

```markdown
### POST /api/emotion-thermometer
创建情绪温度计记录。

Request:
{
  "user_id": "demo-parent",
  "intensity_level": 7,
  "brief_text": "孩子写作业磨蹭，我有点着急"
}

Response:
{
  "ok": true,
  "data": {
    "id": "thermo_xxx",
    "user_id": "demo-parent",
    "intensity_level": 7,
    "brief_text": "...",
    "created_at": "2026-06-30T..."
  }
}

### GET /api/emotion-thermometer
获取情绪温度计记录列表。

Query: ?user_id=demo-parent&limit=20

Response:
{
  "ok": true,
  "data": {
    "items": [...],
    "total": 5,
    "today_count": 2
  }
}
```

**2. 更新数据库文档：**
文件：`docs/03_技术真相/数据库字段说明.md`

在表清单中添加：

```markdown
### emotion_thermometer（情绪温度计记录）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT | 主键，格式 thermo_<uuid> |
| user_id | TEXT | 用户ID |
| intensity_level | INTEGER | 情绪波动强度 1-10 |
| brief_text | TEXT | 一句话内容 |
| created_at | TEXT | 创建时间 ISO 8601 |
```

**3. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 新增情绪温度计功能（T6-01）
  - 后端：新增 `/api/emotion-thermometer` 接口和 `emotion_thermometer` 表
  - 前端：首页"情绪天气"改为"情绪温度计"，新增 `/pages/thermometer` 记录页
  - 设计：1-10 档标尺，一句话快速记录
```

**4. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-01 情绪温度计功能开发
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：情绪温度计后端API + 小程序页面 + 首页入口改造
- 关键决策：独立表设计，1-10档标尺，与情绪日记功能解耦
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的设计图片（如有）
- [ ] 3. 在 `backend/models.py` 添加 `emotion_thermometer` 表定义
- [ ] 4. 创建 `backend/routes/emotion_thermometer.py` 文件
- [ ] 5. 在 `backend/app.py` 注册蓝图
- [ ] 6. 在 `shared/types/api.ts` 添加类型定义
- [ ] 7. 在 `shared/constants/api.ts` 添加端点常量
- [ ] 8. 在 `apps/miniprogram/services/api.js` 添加 API 方法
- [ ] 9. 修改 `apps/miniprogram/pages/home/index.wxml` 卡片文案
- [ ] 10. 修改 `apps/miniprogram/pages/home/index.js` 事件处理
- [ ] 11. 创建 `apps/miniprogram/pages/thermometer/` 目录及 4 个文件
- [ ] 12. 在 `apps/miniprogram/app.json` 注册页面路由
- [ ] 13. 启动后端，测试 API（curl 或 Postman）
- [ ] 14. 在微信开发者工具中测试小程序页面
- [ ] 15. 运行代码检查命令（JS/JSON 语法）
- [ ] 16. 更新 4 个文档（API、数据库、开发日志、Claude记录）
- [ ] 17. 截图验收结果，提交给用户确认

---

### 七、注意事项

1. **不要删除情绪日记功能**：温度计和日记是独立功能，保留所有日记相关代码
2. **参考设计 skills**：Codex 在实现时优先调用 `C:\Users\32257\.codex\skills\frontend-design` 等本地 skills
3. **遵守伦理边界**：页面必须显示"不构成诊断"等非诊断文案
4. **代码风格**：保持与现有代码一致（缩进、命名、注释）
5. **错误处理**：API 调用失败时显示友好提示，不暴露技术细节

---

**任务状态：** 待执行
**预计工时：** 2-3 小时（后端1h + 前端1.5h + 测试0.5h）
**优先级：** P0（首页核心功能改造）

---

## T6-02：测一测页面改造（量表列表+搜索+学生画像详情修复）

### 一、任务目标

改造"测一测"页面，实现：
1. **删除所有 demo 测试量表**，只展示后端已启用的正式量表
2. **修复学生支持性画像测评详情页**选项显示不完整问题
3. **实现搜索功能**：支持标题和关键词搜索
4. **分类展示**：按"学生自助/家长自助/成人自助"正确分类

**核心变更：**
- 前端不再使用硬编码的 demo 量表数据
- 从后端 API `/api/assessments` 动态获取启用量表
- 修复选项按钮样式的文字断行问题
- 实现分类和搜索的正确逻辑

---

### 二、后端代码审核结论

**现有后端代码：**
- `backend/routes/assessments.py` - 量表 API 路由
- `content/assessment_worksheets.json` - 量表数据源（27个量表）
- API `/api/assessments` 返回所有 `enabled_for_user=True` 的量表

**审核结论：**
- ✅ 后端数据完整：27个量表，16个已启用
- ✅ 后端 API 正常：返回正确的量表列表
- ✅ 数据编码正确：UTF-8 格式，中文显示正常
- ✅ 分类字段存在：`audience_class` 字段（student/parent/adult）
- ✅ 搜索字段存在：`search_keywords` 数组字段

**启用量表统计：**
- 学生自助（student）：5个量表
- 家长自助（parent）：1个量表
- 成人自助（adult）：10个量表
- 总计：16个启用量表

> **【Claude订正】** 启用数核对**无误**（27 个 worksheet，启用 16 = 学生5/家长1/成人10）。但 **`content/assessment_worksheets.json` 里没有任何 demo/示例量表**（无"工作表1.1"之类），数据全部经 `api.listAssessments()` 取得——**故本任务"删除所有 demo 测试量表"无对象可删，该子目标取消**，前端也无硬编码量表数组。`audience_class` 真实取值是英文 `student/parent/adult`；标题字段是 `display_title`（不是 `title`，`title` 为空）。

**问题诊断：**
- 前端选项显示问题：`.option-button` 样式中 `word-break: break-all` 导致中文被强制断开
- 示例："1 很少" 被断成 "1 很 少"，导致显示为乱码形式

---

### 三、详细实现方案

#### 3.1 前端修复：学生画像详情页选项显示

**文件：`apps/miniprogram/pages/assessment-detail/index.wxss`**

**修改位置：约第 115-126 行**

**原代码：**
```css
.option-button {
  min-height: var(--safe-touch);
  padding: 0 18rpx;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
  color: var(--safe-text);
  font-size: 25rpx;
  line-height: 1.5;
  transition: all 120ms ease;
  word-break: break-all;
  font-weight: 800;
}
```

**修改为：**
```css
.option-button {
  min-height: var(--safe-touch);
  padding: 0 18rpx;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
  color: var(--safe-text);
  font-size: 25rpx;
  line-height: 1.5;
  transition: all 120ms ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 800;
}
```

**改动说明：**
- 删除 `word-break: break-all;`（导致中文断开）
- 添加 `white-space: nowrap;`（不换行）
- 添加 `overflow: hidden;`（超出隐藏）
- 添加 `text-overflow: ellipsis;`（超长显示省略号）

> **【Claude订正 · 此修复方向会引入新 bug，改用下面的版本】**
> 选项是 **grid 多列窄格**（`assessment-detail/index.wxss` 选项容器 `repeat(auto-fill, minmax(0,1fr))`，按钮 `font-size:20rpx`、可两行），"5 几乎总是"这类 5–6 字标签**靠换行**才能完整显示。改成 `white-space:nowrap; text-overflow:ellipsis` 后，窄格单行放不下会被截成 **"5 几…"**，用户分不清"几乎总是 / 几乎从不"——**直接损坏量表作答语义**。
> 正确做法：把 `break-all` 换成 `keep-all`（中文按词/标点断、不拆字），并**保留可换行**（不要 nowrap/ellipsis）：
> ```css
> .option-button {
>   /* ...其余不变... */
>   word-break: keep-all;   /* 替换 break-all */
>   white-space: normal;    /* 允许换行 */
>   font-weight: 800;
> }
> ```
> （`.option-button` 真实位置 `index.wxss:106-120`，`word-break: break-all` 在 :119，核实无误。选项 label 形如 "5 几乎总是" 由后端 `build_worksheets.py:39` 拼接。）

#### 3.2 前端改造：测一测列表页

**文件：`apps/miniprogram/pages/assessment/index.js`**

> **【Claude订正 · 本节 3.2 整体方向调整，以下为准，原各子节按此取舍】**
> 1. **API 名**：用 `api.listAssessments(params)`（`services/api.js:360`），**不是 `api.getAssessments()`**（不存在，会 `TypeError` 致测一测页白屏）。
> 2. **真实函数名**：筛选用 `refreshVisibleAssessments()`（**非** `applyFilters`）；分组用模块级 `buildAssessmentSections(items, activeAudience, query)`（**非** `buildCategorySections`）。**改这两个真实函数**，不要新建同名函数（否则成孤儿函数、改了不生效）。
> 3. **无 demo 数据**：3.2.2"删除 demo 数据逻辑"无对象，跳过（页面本就无硬编码量表）。
> 4. **分组维度——保留现状（用户决策 2026-07-01）**：当前是「顶部 Tab = 学生/家长/成人（按 `audience_class` 过滤）+ 页内 section 按**反射弧节点 `reflex_node`** 分组（标题取 `NODE_LABELS`）」。**👉 3.2.4『改为按 audience_class 分组』作废**——那会与 Tab 重复、并丢掉反射弧节点维度（量表体系核心分类）。section 继续按 `reflex_node` 分组，**不改**。
> 5. **本节真正要做的只有 3 件**：① 搜索接好（在 `refreshVisibleAssessments` 内按 `display_title` + `search_keywords` 过滤）；② 确认 Tab 用 `audience_class ∈ {student,parent,adult}` 过滤；③ 修详情页选项截断（见 3.1 的【Claude订正】，用 `keep-all` 不用 ellipsis）。其余"删 demo / 换分组维度"描述忽略。

##### 3.2.1 修改分类标签

**修改位置：第 5-10 行**

**原代码：**
```javascript
const AUDIENCE_TABS = [
  { key: "all", label: "全部", description: "查看当前可填写内容" },
  { key: "student", label: "学生自助", description: "学习、压力和支持画像" },
  { key: "parent", label: "家长自助", description: "亲子理解和陪伴练习" },
  { key: "adult", label: "成人自助", description: "情绪、觉察和自我支持" },
];
```

**保持不变**（已经是正确的分类）

##### 3.2.2 删除 demo 数据逻辑

**修改位置：第 161-243 行**

在 `Page({})` 中找到 `onLoad` 方法，删除所有硬编码的 demo 量表数据。

**原代码：**
```javascript
onLoad() {
  this.setData({
    activeAudience: this.getDefaultAudience(),
  });
  this.loadAssessments();
},
```

**保持不变**（逻辑正确）

**但需要检查 `loadAssessments` 方法，确保没有混入 demo 数据。**

**修改位置：约第 176-200 行**

找到 `loadAssessments` 方法，**确认是否有硬编码的 demo 数据混入**。

**期望的正确代码：**
```javascript
async loadAssessments() {
  this.setData({ loading: true, errorMessage: "" });

  try {
    const result = await api.getAssessments();

    if (!result.ok) {
      this.setData({
        loading: false,
        errorMessage: result.error?.message || "读取失败",
      });
      return;
    }

    const worksheets = result.data.worksheets || [];
    
    // 只保留启用的量表
    const enabledWorksheets = worksheets.filter(
      (w) => w.enabled_for_user !== false
    );

    this.setData({
      loading: false,
      allAssessments: enabledWorksheets,
      boundaryNotice: result.data.boundary_notice || "",
    });

    this.applyFilters();
  } catch (err) {
    this.setData({
      loading: false,
      errorMessage: "网络错误，请重试",
    });
    console.error("loadAssessments error:", err);
  }
},
```

**如果发现有硬编码的 demo 数据（如 `const demoWorksheets = [...]`），全部删除。**

##### 3.2.3 修改搜索逻辑

**修改位置：约第 230-250 行**

找到 `applyFilters` 方法，确保搜索逻辑正确匹配**标题和关键词**。

**期望的正确代码：**
```javascript
applyFilters() {
  const { allAssessments, activeAudience, searchKeyword } = this.data;
  const keyword = (searchKeyword || "").trim().toLowerCase();

  // 按分类过滤
  let filtered = allAssessments;
  if (activeAudience !== "all") {
    filtered = filtered.filter(
      (item) => item.audience_class === activeAudience
    );
  }

  // 按搜索关键词过滤（搜索标题 + search_keywords）
  if (keyword) {
    filtered = filtered.filter((item) => {
      const title = (item.display_title || "").toLowerCase();
      const keywords = (item.search_keywords || [])
        .map((k) => String(k).toLowerCase())
        .join(" ");
      return title.includes(keyword) || keywords.includes(keyword);
    });
  }

  const categories = buildCategorySections(filtered);
  this.setData({ categories });
},
```

##### 3.2.4 检查分组逻辑

> **【Claude订正 · 本子节作废】** 分组维度**保留按反射弧节点 `reflex_node` 分组**（用户决策 2026-07-01），**不**改为 `audience_class`。真实分组函数名是 `buildAssessmentSections`（非 `buildCategorySections`）。以下"按 audience_class 分组"的代码**不要执行**。

**修改位置：约第 100-138 行**

找到 `buildCategorySections` 函数，**确认分组逻辑是否正确**。

根据你的要求，分类应该是"学生自助/家长自助/成人自助"，而不是按 `reflex_node` 分组。

**修改后的正确代码：**
```javascript
function buildCategorySections(filtered) {
  if (!filtered.length) {
    return [
      {
        key: "empty",
        title: "没有匹配内容",
        subtitle: "换一个分类或关键词再看",
        emptyText: "当前条件下没有可显示的测评内容。",
        items: [],
      },
    ];
  }

  // 按 audience_class 分组
  const audienceMap = {
    student: {
      key: "student",
      title: "学生自助",
      subtitle: "学习、压力和支持画像",
      items: [],
    },
    parent: {
      key: "parent",
      title: "家长自助",
      subtitle: "亲子理解和陪伴练习",
      items: [],
    },
    adult: {
      key: "adult",
      title: "成人自助",
      subtitle: "情绪、觉察和自我支持",
      items: [],
    },
  };

  filtered.forEach((item) => {
    const audienceClass = item.audience_class || "adult";
    if (audienceMap[audienceClass]) {
      audienceMap[audienceClass].items.push(item);
    }
  });

  // 只返回有内容的分组
  const sections = Object.values(audienceMap).filter(
    (section) => section.items.length > 0
  );

  return sections;
}
```

**改动说明：**
- 删除原有的 `reflex_node` 分组逻辑
- 改为按 `audience_class` 分组
- 分组标签使用固定的"学生自助/家长自助/成人自助"

#### 3.3 前端样式优化

**文件：`apps/miniprogram/pages/assessment/index.wxss`**

**无需修改**，当前样式已适配分类展示。

---

### 四、验收标准

#### 4.1 学生画像详情页验收

**在微信开发者工具中测试：**

1. 进入"测一测"页面
2. 点击"学生支持性画像测评"
3. 确认选项按钮显示正确：
   - ✅ "1 很少" 显示为完整文字，不被断开
   - ✅ "2 偶尔" 显示为完整文字
   - ✅ "3 有时" 显示为完整文字
   - ✅ "4 经常" 显示为完整文字
   - ✅ "5 几乎总是" 显示为完整文字
4. 确认题目和选项布局清晰，无乱码

#### 4.2 测一测列表页验收

**在微信开发者工具中测试：**

1. 进入"测一测"页面
2. 确认默认显示"家长自助"分类
3. 确认页面展示的量表数量：
   - **全部**：约16个量表
   - **学生自助**：约5个量表
   - **家长自助**：约1个量表
   - **成人自助**：约10个量表
4. 确认**没有 demo 测试量表**（如"工作表1.1"等）
5. 确认分组标题正确：
   - 学生自助分组显示"学生自助"标题
   - 家长自助分组显示"家长自助"标题
   - 成人自助分组显示"成人自助"标题

#### 4.3 搜索功能验收

**在微信开发者工具中测试：**

1. 在搜索框输入"情绪"
   - 确认显示所有标题或关键词包含"情绪"的量表
2. 在搜索框输入"学生"
   - 确认显示"学生支持性画像测评"等相关量表
3. 在搜索框输入"压力"
   - 确认显示所有与压力相关的量表
4. 点击"清除"按钮
   - 确认搜索框清空，列表恢复默认显示
5. 搜索"不存在的关键词"
   - 确认显示"没有匹配内容"提示

#### 4.4 边界验收

**必须符合：**
- ✅ 非诊断文案：页面保留"不构成诊断或贴标签"等边界说明
- ✅ API 不变：不破坏后端 `/api/assessments` 接口
- ✅ 数据来源：前端只从后端 API 获取量表，不使用硬编码数据
- ✅ 代码检查：小程序 JS/JSON/WXSS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram\pages\assessment -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram\pages\assessment-detail -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 测一测页面改造（T6-02）
  - 删除所有 demo 测试量表，改为从后端 API 动态获取
  - 修复学生画像测评详情页选项显示问题（word-break 导致断行）
  - 实现搜索功能（标题+关键词）
  - 按"学生自助/家长自助/成人自助"正确分类展示
  - 启用量表：学生5个、家长1个、成人10个，共16个
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"测一测"章节更新：

```markdown
### 测一测页面

**验收结果：**
- ✅ 量表列表从后端动态获取，无硬编码 demo 数据
- ✅ 搜索功能正常（标题+关键词）
- ✅ 分类展示正确（学生/家长/成人自助）
- ✅ 学生画像测评选项显示完整，无断行乱码
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-02 测一测页面改造
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：删除 demo 量表 + 修复学生画像详情页显示 + 搜索功能 + 分类展示
- 关键决策：前端完全依赖后端 API，不使用硬编码数据；修复 word-break 导致的中文断行问题
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的设计图片（两张截图）
- [ ] 3. 修改 `apps/miniprogram/pages/assessment-detail/index.wxss` 第 115-126 行（选项按钮样式）
- [ ] 4. 审查 `apps/miniprogram/pages/assessment/index.js` 的 `loadAssessments` 方法
- [ ] 5. 删除任何硬编码的 demo 量表数据
- [ ] 6. 修改 `buildCategorySections` 函数（改为按 audience_class 分组）
- [ ] 7. 检查 `applyFilters` 方法的搜索逻辑（确保搜索标题+关键词）
- [ ] 8. 在微信开发者工具中测试学生画像详情页（选项显示）
- [ ] 9. 在微信开发者工具中测试量表列表页（分类+数量）
- [ ] 10. 测试搜索功能（输入"情绪""学生""压力"等关键词）
- [ ] 11. 确认无 demo 量表残留
- [ ] 12. 运行代码检查命令（JS 语法）
- [ ] 13. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 14. 截图验收结果（列表页+详情页+搜索结果），提交给用户确认

---

### 七、注意事项

1. **保留学生画像测评**：不要删除 `student_profile_v1`，这是核心功能
2. **删除所有 demo**：检查代码中是否有 `const demoWorksheets = [...]` 等硬编码数据，全部删除
3. **参考设计 skills**：Codex 在实现时优先调用本地 `frontend-design` 等 skills
4. **遵守伦理边界**：页面必须保留"不构成诊断"等非诊断文案
5. **代码风格**：保持与现有代码一致（缩进、命名、注释）
6. **测试完整性**：必须在微信开发者工具中实际测试，不能只改代码不验证

---

**任务状态：** 待执行
**预计工时：** 2-3 小时（前端修复1h + 列表改造1h + 测试验收1h）
**优先级：** P0（核心测评功能改造）

---

## T6-03：三步开始页面优化（文案+视觉）

> **【Claude订正 · 本节可信，按原文执行即可】** 经逐行核实，T6-03 引用的行号/文案/字段**全部精确命中**（intro-text 在 `index.wxml:5`、steps/boundaries 在 `index.js`、按钮在 `index.wxml:24-25`、step 结构 `index.wxml:8-13`、`.step-title` 在 `index.wxss:62-66`）。是任务六里最可靠的一节。唯一提醒：`steps`/`boundaries` 是 `index.js` 里的 data（不在 wxml）。

### 一、任务目标

优化"三步开始"页面，提升新手理解度和视觉吸引力：
1. **优化文案**：去除专业术语，改为生活化表达
2. **添加视觉元素**：步骤卡片增加数字标签，提升层次感
3. **统一按钮文案**：保持温和一致的表达风格

**核心变更：**
- 将"情绪反射弧"等专业术语改为通俗表达
- 简化新手说明文案，降低认知负担
- 为三个步骤卡片添加数字标签（1/2/3）
- 统一按钮文案风格

---

### 二、前端代码审核结论

**现有文件：**
- `apps/miniprogram/pages/getting-started/index.wxml` - 页面结构
- `apps/miniprogram/pages/getting-started/index.js` - 数据和逻辑
- `apps/miniprogram/pages/getting-started/index.wxss` - 样式

**审核结论：**
- ✅ 信息层级清晰：新手说明 → 三步流程 → 使用边界 → 行动按钮
- ✅ 视觉设计符合规范：色彩、圆角、阴影、间距正确
- ✅ 伦理边界明确：底部说明"不下诊断结论"
- ⚠️ 文案过于专业化："情绪反射弧""链路"等术语不够通俗
- ⚠️ 缺少视觉辅助：纯文字卡片略显单调

---

### 三、详细实现方案

#### 3.1 文案优化

**文件：`apps/miniprogram/pages/getting-started/index.js`**

##### 3.1.1 优化新手说明文案

**修改位置：data 对象外（需要新增常量）**

在 `Page({})` 之前添加常量定义：

```javascript
const INTRO_TEXT = "当和孩子出现冲突或情绪时，先记录下来：发生了什么、你有什么感受、你做了什么。记下这些线索，下次就更容易找到可以调整的地方。";
```

**文件：`apps/miniprogram/pages/getting-started/index.wxml`**

**修改位置：第 5 行**

**原代码：**
```xml
<text class="intro-text">当亲子互动里出现压力时，可以先把它当作一次"情绪反射弧"：事件出现后，我们会有情绪、想法、身体反应和行为。把这条链路写下来，才更容易找到下一次可以轻轻调整的位置。</text>
```

**修改为：**
```xml
<text class="intro-text">当和孩子出现冲突或情绪时，先记录下来：发生了什么、你有什么感受、你做了什么。记下这些线索，下次就更容易找到可以调整的地方。</text>
```

##### 3.1.2 优化步骤2文案

**文件：`apps/miniprogram/pages/getting-started/index.js`**

**修改位置：data.steps 数组第2项（第 8-11 行）**

**原代码：**
```javascript
{
  title: "2. 查看支持性反馈",
  text: "系统只做非诊断、非评判的线索提示，帮助你看见情绪、想法、身体反应和行为之间的连接。",
},
```

**修改为：**
```javascript
{
  title: "2. 查看支持性反馈",
  text: "系统会给你一些支持性反馈，帮你理解当时的情绪和反应模式，不做诊断或评判。",
},
```

##### 3.1.3 优化使用边界文案

**文件：`apps/miniprogram/pages/getting-started/index.js`**

**修改位置：data.boundaries 数组第2项（第 19 行）**

**原代码：**
```javascript
"高风险内容需要优先寻求人工支持或专业帮助。",
```

**修改为：**
```javascript
"如遇严重安全问题，请优先寻求专业帮助或人工支持。",
```

##### 3.1.4 优化按钮文案

**文件：`apps/miniprogram/pages/getting-started/index.wxml`**

**修改位置：第 24-25 行**

**原代码：**
```xml
<button class="primary-action" bindtap="startDiary">记录一次</button>
<button class="secondary-action" bindtap="openTraining">去训练中心</button>
```

**修改为：**
```xml
<button class="primary-action" bindtap="startDiary">开始记录</button>
<button class="secondary-action" bindtap="openTraining">看看训练卡</button>
```

#### 3.2 视觉优化：添加步骤数字标签

##### 3.2.1 修改页面结构

**文件：`apps/miniprogram/pages/getting-started/index.wxml`**

**修改位置：第 8-13 行**

**原代码：**
```xml
<view class="step-list">
  <view wx:for="{{steps}}" wx:key="title" class="step-card">
    <text class="step-title">{{item.title}}</text>
    <text class="step-text">{{item.text}}</text>
  </view>
</view>
```

**修改为：**
```xml
<view class="step-list">
  <view wx:for="{{steps}}" wx:key="title" class="step-card">
    <view class="step-header">
      <view class="step-number">{{index + 1}}</view>
      <text class="step-title">{{item.title}}</text>
    </view>
    <text class="step-text">{{item.text}}</text>
  </view>
</view>
```

##### 3.2.2 添加数字标签样式

**文件：`apps/miniprogram/pages/getting-started/index.wxss`**

**修改位置：在 `.step-card` 样式后（约第 60 行附近）添加**

```css
.step-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

.step-number {
  width: 56rpx;
  height: 56rpx;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--safe-primary);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
}

.step-title {
  flex: 1;
  color: var(--safe-title);
  font-size: 29rpx;
  font-weight: 850;
  line-height: 1.35;
}
```

**同时删除原有的独立 `.step-title` 样式（约第 68-72 行）：**

**删除这段：**
```css
.step-title {
  color: var(--safe-title);
  font-size: 29rpx;
  font-weight: 850;
}
```

---

### 四、验收标准

#### 4.1 文案验收

**在微信开发者工具中测试：**

1. 进入"三步开始"页面
2. 确认新手说明文案：
   - ✅ 没有"情绪反射弧"等专业术语
   - ✅ 使用"冲突或情绪""线索"等通俗表达
3. 确认步骤2文案：
   - ✅ "支持性反馈"清晰易懂
   - ✅ 没有"线索提示""连接"等抽象词
4. 确认使用边界文案：
   - ✅ "严重安全问题"比"高风险内容"更温和
5. 确认按钮文案：
   - ✅ "开始记录"+"看看训练卡"长度接近
   - ✅ 风格一致，都是温和表达

#### 4.2 视觉验收

**在微信开发者工具中测试：**

1. 确认步骤卡片结构：
   - ✅ 每个步骤卡片左侧显示圆形数字标签（1/2/3）
   - ✅ 数字标签为绿色底白字
   - ✅ 标题在数字标签右侧，与数字水平对齐
2. 确认布局美观：
   - ✅ 数字标签和标题之间间距适中（16rpx）
   - ✅ 标题和正文之间间距合理（12rpx）
   - ✅ 整体视觉层次清晰

#### 4.3 交互验收

**在微信开发者工具中测试：**

1. 点击"开始记录"按钮
   - ✅ 跳转到情绪日记表单页面
2. 点击"看看训练卡"按钮
   - ✅ 跳转到训练中心页面（tabBar）

#### 4.4 边界验收

**必须符合：**
- ✅ 伦理边界说明保持清晰："不下诊断结论"
- ✅ 文案保持非评判、支持性表达
- ✅ 没有诊断化、标签化表达
- ✅ 代码检查：JS/WXML/WXSS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
node --check apps\miniprogram\pages\getting-started\index.js
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 三步开始页面优化（T6-03）
  - 文案优化：去除"情绪反射弧"等专业术语，改为生活化表达
  - 视觉优化：步骤卡片增加数字标签（1/2/3），提升层次感
  - 按钮文案统一：改为"开始记录"+"看看训练卡"
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"三步开始"章节更新：

```markdown
### 三步开始页面

**验收结果：**
- ✅ 文案通俗易懂，无专业术语
- ✅ 步骤卡片有数字标签，视觉层次清晰
- ✅ 按钮文案温和一致
- ✅ 伦理边界说明清楚
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-03 三步开始页面优化
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：文案优化（去除专业术语）+ 视觉优化（数字标签）
- 关键决策：降低新手理解门槛，提升视觉吸引力
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的截图（三步开始页面）
- [ ] 3. 修改 `apps/miniprogram/pages/getting-started/index.wxml` 第5行（新手说明文案）
- [ ] 4. 修改 `apps/miniprogram/pages/getting-started/index.js` data.steps 第2项（步骤2文案）
- [ ] 5. 修改 `apps/miniprogram/pages/getting-started/index.js` data.boundaries 第2项（边界文案）
- [ ] 6. 修改 `apps/miniprogram/pages/getting-started/index.wxml` 第24-25行（按钮文案）
- [ ] 7. 修改 `apps/miniprogram/pages/getting-started/index.wxml` 第8-13行（添加数字标签结构）
- [ ] 8. 在 `apps/miniprogram/pages/getting-started/index.wxss` 添加数字标签样式
- [ ] 9. 删除 `index.wxss` 中原有的独立 `.step-title` 样式
- [ ] 10. 在微信开发者工具中测试页面显示
- [ ] 11. 确认文案通俗易懂，无专业术语
- [ ] 12. 确认数字标签显示正确（1/2/3圆形绿底白字）
- [ ] 13. 测试按钮跳转（开始记录→日记表单，看看训练卡→训练中心）
- [ ] 14. 运行代码检查命令（JS 语法）
- [ ] 15. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 16. 截图验收结果（优化前后对比），提交给用户确认

---

### 七、注意事项

1. **保持伦理边界**：不删除"使用边界"卡片，只优化表达
2. **保持色彩规范**：数字标签使用 `var(--safe-primary)`，不使用其他颜色
3. **保持简洁风格**：不添加过多装饰，保持克制的设计
4. **参考设计 skills**：Codex 在实现时优先调用本地 `frontend-design` 等 skills
5. **代码风格**：保持与现有代码一致（缩进、命名、注释）
6. **测试完整性**：必须在微信开发者工具中实际测试，不能只改代码不验证

---

### 八、设计参考（视觉效果）

**数字标签预期效果：**

```
┌──────────────────────────────┐
│  ⊙   1. 记录一个具体事件      │
│  1                            │
│                               │
│  先写清楚发生了什么、当时...  │
└──────────────────────────────┘
```

**数字标签样式：**
- 直径：56rpx
- 背景：绿色（`--safe-primary`）
- 文字：白色，28rpx，粗体
- 与标题间距：16rpx

---

**任务状态：** 待执行
**预计工时：** 1-1.5 小时（文案修改0.5h + 视觉优化0.5h + 测试验收0.5h）
**优先级：** P2（体验优化，非核心功能）

---

## T6-04：首页支持性反馈和最近记录改造

> **【Claude订正 · 本节 API名/方法名/时区，以下为准】**
> 1. **`api.getDiaries` 不存在 → 改用 `api.listDiaries(params)`**（`services/api.js:277`，GET `/api/diaries`）。本节 3.1.2 代码块里 `api.getDiaries({limit:1})` 全部改成 `api.listDiaries({limit:1})`；列表取 `result.data.items`（沿用本计划统一的 `{ok,data}` 包装）。
> 2. **`onShow` 的统计方法真名是 `refreshTodayRecordCount`（非 `loadTodayRecordCount`）**——3.1.3"原代码"写错了。只需在 `onShow` 里**新增** `this.loadLatestRecord()`，别去找不存在的 `loadTodayRecordCount`。
> 3. **时区**：`created_at` 是 `now_iso()` 写入的 **UTC** ISO 串。`new Date(created_at)` 在小程序按设备本地时区解析，会让"今天/昨天"判断偏移（跨零点误判）。建议后端补一个本地化展示字段，或前端按 `+08:00` 显式校正；本期至少在验收里注明此偏移已知。
> 4. 字段 `scene/event_description/parent_emotion` 前后端一致（✅）；`latestRecord` 硬编码属实可放心替换；`feedback-result` 收 `diary_id`（✅）。

### 一、任务目标

改造首页的"支持性反馈"入口和"最近记录"模块，实现动态数据展示和正确的跳转逻辑：
1. **删除硬编码数据**：最近记录从后端 API 动态获取
2. **修复跳转逻辑**：点击记录卡片跳转到该次反馈详情，而非本周复盘
3. **优化文案**："查看全部"改为"本周复盘"
4. **优化支持性反馈入口**：根据是否有记录，跳转到最近一次反馈或引导记录

**核心变更：**
- 删除 `latestRecord` 硬编码数据
- 调用 API 获取最近一条情绪日记记录
- 记录卡片点击跳转到对应的反馈详情页
- "查看全部"改为"本周复盘"

---

### 二、前端代码审核结论

**现有代码：**
- `apps/miniprogram/pages/home/index.js` - 首页逻辑
- `apps/miniprogram/pages/home/index.wxml` - 首页结构

**审核结论：**
- ❌ **问题1**：最近记录是硬编码（第 105-110 行）
  ```javascript
  latestRecord: {
    mood: "有点烦",
    time: "昨天 21:30",
    trigger: "孩子写作业磨蹭",
    status: "支持性反馈已完成",
  }
  ```
- ❌ **问题2**：记录卡片点击跳转到 `openWeeklyReport`（本周复盘），应该跳转到反馈详情
- ❌ **问题3**："查看全部"文案不清晰，应改为"本周复盘"
- ❌ **问题4**："支持性反馈"入口当前只是提示记录，未展示上次互动线索

---

### 三、详细实现方案

#### 3.1 删除硬编码数据，改为动态获取

**文件：`apps/miniprogram/pages/home/index.js`**

##### 3.1.1 修改 data 定义

**修改位置：第 105-110 行**

**原代码：**
```javascript
latestRecord: {
  mood: "有点烦",
  time: "昨天 21:30",
  trigger: "孩子写作业磨蹭",
  status: "支持性反馈已完成",
},
```

**修改为：**
```javascript
latestRecord: null,
latestRecordReady: false,
```

##### 3.1.2 添加加载最近记录的方法

**修改位置：在 `onShow()` 方法后添加（约第 120 行附近）**

```javascript
async loadLatestRecord() {
  try {
    const result = await api.getDiaries({ limit: 1 });
    
    if (!result.ok || !result.data.items || result.data.items.length === 0) {
      this.setData({
        latestRecord: null,
        latestRecordReady: true,
      });
      return;
    }

    const diary = result.data.items[0];
    
    // 格式化时间
    const createdAt = new Date(diary.created_at);
    const now = new Date();
    const diffMs = now - createdAt;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    let timeLabel = "";
    if (diffDays === 0) {
      const hours = createdAt.getHours();
      const minutes = createdAt.getMinutes();
      timeLabel = `今天 ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    } else if (diffDays === 1) {
      const hours = createdAt.getHours();
      const minutes = createdAt.getMinutes();
      timeLabel = `昨天 ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    } else if (diffDays < 7) {
      timeLabel = `${diffDays}天前`;
    } else {
      const month = createdAt.getMonth() + 1;
      const day = createdAt.getDate();
      timeLabel = `${month}月${day}日`;
    }

    this.setData({
      latestRecord: {
        id: diary.id,
        mood: diary.parent_emotion || "情绪记录",
        time: timeLabel,
        trigger: diary.scene || diary.event_description?.slice(0, 15) || "具体事件",
        status: "支持性反馈已完成",
      },
      latestRecordReady: true,
    });
  } catch (err) {
    console.error("loadLatestRecord error:", err);
    this.setData({
      latestRecord: null,
      latestRecordReady: true,
    });
  }
},
```

> **【Claude订正】** 上方 `api.getDiaries({ limit: 1 })` → **`api.listDiaries({ limit: 1 })`**；`new Date(diary.created_at)` 的 `created_at` 是 **UTC**（见本节节首订正第 3 点，"今天/昨天"判断需按 UTC 或 `+08:00` 处理，否则跨零点会误判）。

##### 3.1.3 在 onShow 中调用

**修改位置：第 114-118 行**

**原代码：**
```javascript
onShow() {
  this.loadTodayRecordCount();
  this.checkDevEntry();
},
```

**修改为：**
```javascript
onShow() {
  this.loadTodayRecordCount();
  this.loadLatestRecord();
  this.checkDevEntry();
},
```

#### 3.2 修复跳转逻辑

##### 3.2.1 修改记录卡片点击事件

**文件：`apps/miniprogram/pages/home/index.wxml`**

**修改位置：第 78-84 行**

**原代码：**
```xml
<button class="recent-record-card" bindtap="openWeeklyReport">
  <view class="recent-copy">
    <text class="recent-time">{{latestRecord.time}}</text>
    <text class="recent-title">{{latestRecord.mood}}，{{latestRecord.trigger}}</text>
  </view>
  <text class="recent-status">{{latestRecord.status}} ›</text>
</button>
```

**修改为：**
```xml
<button wx:if="{{latestRecord}}" class="recent-record-card" bindtap="openLatestRecordFeedback">
  <view class="recent-copy">
    <text class="recent-time">{{latestRecord.time}}</text>
    <text class="recent-title">{{latestRecord.mood}}，{{latestRecord.trigger}}</text>
  </view>
  <text class="recent-status">{{latestRecord.status}} ›</text>
</button>
<view wx:else class="recent-empty">
  <text class="recent-empty-text">还没有记录，先去记录一次吧</text>
</view>
```

##### 3.2.2 添加跳转方法

**文件：`apps/miniprogram/pages/home/index.js`**

**修改位置：在 `openWeeklyReport()` 方法后添加（约第 167 行附近）**

```javascript
openLatestRecordFeedback() {
  if (!this.data.latestRecord || !this.data.latestRecord.id) {
    wx.showToast({
      title: "没有找到记录",
      icon: "none",
    });
    return;
  }
  
  // 跳转到反馈结果页
  wx.navigateTo({
    url: `/pages/feedback-result/index?diary_id=${encodeURIComponent(this.data.latestRecord.id)}`,
  });
},
```

#### 3.3 优化文案

##### 3.3.1 "查看全部"改为"本周复盘"

**文件：`apps/miniprogram/pages/home/index.wxml`**

**修改位置：第 77 行**

**原代码：**
```xml
<section-title title="最近记录" subtitle="方便继续查看与跟进" more-text="查看全部" bind:more="openWeeklyReport" />
```

**修改为：**
```xml
<section-title title="最近记录" subtitle="方便继续查看与跟进" more-text="本周复盘" bind:more="openWeeklyReport" />
```

#### 3.4 优化支持性反馈入口

##### 3.4.1 修改跳转逻辑

**文件：`apps/miniprogram/pages/home/index.js`**

**修改位置：第 200-207 行**

**原代码：**
```javascript
if (key === "feedback") {
  wx.showToast({
    title: "请先记录一次事件",
    icon: "none",
  });
  wx.navigateTo({ url: "/pages/diary-form/index" });
  return;
}
```

**修改为：**
```javascript
if (key === "feedback") {
  if (this.data.latestRecord && this.data.latestRecord.id) {
    // 有最近记录，跳转到最近一次反馈
    wx.navigateTo({
      url: `/pages/feedback-result/index?diary_id=${encodeURIComponent(this.data.latestRecord.id)}`,
    });
  } else {
    // 没有记录，引导先记录
    wx.showToast({
      title: "请先记录一次事件",
      icon: "none",
    });
    wx.navigateTo({ url: "/pages/diary-form/index" });
  }
  return;
}
```

#### 3.5 添加空状态样式

**文件：`apps/miniprogram/pages/home/index.wxss`**

**在文件末尾添加（约第 200 行附近）：**

```css
.recent-empty {
  padding: 40rpx 24rpx;
  text-align: center;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-bg);
}

.recent-empty-text {
  color: var(--safe-muted);
  font-size: 26rpx;
  line-height: 1.6;
}
```

---

### 四、验收标准

#### 4.1 动态数据验收

**在微信开发者工具中测试：**

1. **首次进入（无记录）：**
   - ✅ "最近记录"显示"还没有记录，先去记录一次吧"
   - ✅ 点击"支持性反馈"提示"请先记录一次事件"，跳转到日记表单

2. **记录一次后：**
   - ✅ 返回首页，"最近记录"显示真实数据（时间+情绪+场景）
   - ✅ 时间格式正确（今天 17:09、昨天 21:30、3天前、6月30日）
   - ✅ 情绪和场景取自真实记录

3. **点击记录卡片：**
   - ✅ 跳转到该次记录的反馈详情页（`/pages/feedback-result/index?diary_id=xxx`）
   - ✅ 显示该次记录对应的反馈和推荐训练卡

4. **点击"本周复盘"：**
   - ✅ 跳转到本周复盘页面（`/pages/weekly-report/index`）

5. **点击"支持性反馈"入口：**
   - ✅ 有记录时跳转到最近一次反馈详情
   - ✅ 无记录时提示先记录

#### 4.2 数据格式验收

**确认以下字段映射正确：**
- `diary.id` → `latestRecord.id` ✅
- `diary.parent_emotion` → `latestRecord.mood` ✅
- `diary.scene` 或 `diary.event_description` → `latestRecord.trigger` ✅
- `diary.created_at` → `latestRecord.time`（格式化后）✅

#### 4.3 边界验收

**必须符合：**
- ✅ 无硬编码数据，所有内容从 API 获取
- ✅ API 调用失败时显示空状态，不影响其他功能
- ✅ 时间格式友好（今天/昨天/X天前/X月X日）
- ✅ 代码检查：JS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
node --check apps\miniprogram\pages\home\index.js
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 首页支持性反馈和最近记录改造（T6-04）
  - 删除硬编码数据，改为从 API 动态获取最近一条记录
  - 修复跳转逻辑：记录卡片跳转到反馈详情，"本周复盘"跳转到周报
  - 优化支持性反馈入口：根据是否有记录智能跳转
  - 添加空状态提示
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"首页"章节更新：

```markdown
### 首页

**验收结果：**
- ✅ 最近记录从 API 动态获取，无硬编码
- ✅ 记录卡片点击跳转到反馈详情
- ✅ "本周复盘"跳转正确
- ✅ 支持性反馈入口智能跳转（有记录→反馈详情，无记录→引导记录）
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-04 首页支持性反馈和最近记录改造
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：删除硬编码 + 动态数据 + 修复跳转逻辑 + 空状态
- 关键决策：记录卡片直接跳转反馈详情，支持性反馈入口智能判断
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的首页截图
- [ ] 3. 修改 `apps/miniprogram/pages/home/index.js` data 定义（删除硬编码）
- [ ] 4. 在 `index.js` 添加 `loadLatestRecord()` 方法
- [ ] 5. 修改 `index.js` 的 `onShow()` 方法（调用 loadLatestRecord）
- [ ] 6. 修改 `apps/miniprogram/pages/home/index.wxml` 记录卡片结构（添加空状态）
- [ ] 7. 在 `index.js` 添加 `openLatestRecordFeedback()` 方法
- [ ] 8. 修改 `index.wxml` 的 "查看全部" 文案为 "本周复盘"
- [ ] 9. 修改 `index.js` 的 `openCoreEntry()` 方法（优化支持性反馈逻辑）
- [ ] 10. 在 `apps/miniprogram/pages/home/index.wxss` 添加空状态样式
- [ ] 11. 在微信开发者工具中测试首次进入（无记录）
- [ ] 12. 记录一次情绪日记，返回首页查看动态数据
- [ ] 13. 点击记录卡片，确认跳转到反馈详情页
- [ ] 14. 点击"本周复盘"，确认跳转到周报页
- [ ] 15. 点击"支持性反馈"，确认智能跳转逻辑
- [ ] 16. 运行代码检查命令（JS 语法）
- [ ] 17. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 18. 截图验收结果（动态数据+跳转逻辑），提交给用户确认

---

### 七、注意事项

1. **时间格式友好**：使用"今天/昨天/X天前/X月X日"，不直接显示 ISO 时间
2. **空状态处理**：无记录时显示友好提示，不显示错误信息
3. **API 失败处理**：调用失败时设置 `latestRecord: null`，不影响其他功能
4. **代码风格**：保持与现有代码一致（缩进、命名、注释）
5. **测试完整性**：必须在微信开发者工具中实际测试完整流程

---

**任务状态：** 待执行
**预计工时：** 2-2.5 小时（删除硬编码1h + 修复逻辑1h + 测试验收0.5h）
**优先级：** P1（核心交互功能，影响用户体验）

---

## T6-05：本周复盘页面改造

> **【Claude订正 · 周报字段真相，以下为准】**
> 1. **API `api.getWeeklyReport()` 名正确**（`services/api.js:394`）。
> 2. **周报对象没有 `diaries_count/emotions_count/checkins_count/profiles_count`** —— 计划多处所谓"原代码用这些"是**虚构**。真实字段（`report_service.py:85-101`）：`frequent_scenes`、`frequent_emotions`、`common_patterns` 都是 **`[[名称,次数], ...]` 元组列表**；`completed_cards` 是字符串数组；`profile_trend.profile_count`；`next_week_suggestion`。
> 3. 前端 `weekly-report/index.js` 已有 `formatPairs([[名,次]]) → {name,count}`，结果存进 data 的 `frequentScenes/frequentEmotions/commonPatterns`。**高频场景显示场景名**直接用 `item.name`（已存在）——可行，照做。
> 4. **4 格数据绑定现状已正确**（已绑 data 的 `frequentScenes.length` 等）——见 3.2.1 订正：**只改样式、不改绑定**。
> 5. `profile_trend` **不落库**（`weekly_reports` 表无此列），仅 HTTP 响应透出；本期不要依赖它已持久化。
> 6. "下周可以继续的一小步"板块**确实存在**（`index.wxml:115-118`），可按计划删除。
> 7. tag 中文映射（3.4）可行，未命中映射表的回退原文不报错——照做。

### 一、任务目标

优化本周复盘页面，提升信息展示和视觉体验：
1. **删除冗长说明文案**：顶部说明过长，删除
2. **优化本周小变化卡片**：4个格子缩小，居中文字
3. **修复高频场景显示**：显示场景名称（不只是次数）
4. **修复互动线索显示**：`general_support` 改为中文"一般支持"
5. **删除"下周可以继续的一小步"板块**

**核心变更：**
- 删除顶部"这不是评分..."长文案
- 本周小变化4格：宽度缩小，内容居中
- 高频场景：显示场景名+次数（如"亲子沟通 3次"）
- 互动线索：tag 中文映射（`general_support` → "一般支持"）
- 删除最后的"下周可以继续的一小步"卡片

---

### 二、前端代码审核结论

**现有代码：**
- `apps/miniprogram/pages/weekly-report/index.wxml` - 页面结构
- `apps/miniprogram/pages/weekly-report/index.js` - 数据逻辑
- `backend/services/report_service.py` - 后端周报生成逻辑

**审核结论：**
- ❌ **问题1**：顶部说明文案过长（第6行）
  ```xml
  <text class="hero-summary">这不是评分，也不是判断。只是把记录和练习整理出来，帮你找到下周可以继续的一小步。</text>
  ```
  
- ❌ **问题2**：本周小变化4格太大，未居中（第44-63行）
  ```xml
  <view class="stat-grid">
    <view class="stat-card">
      <text class="stat-num">{{report.diaries_count || 0}}</text>
      <text class="stat-label">类常见场景</text>
    </view>
    ...
  </view>
  ```

- ❌ **问题3**：高频场景只显示次数，不显示场景名（第83-91行）
  ```xml
  <block wx:for="{{frequentScenes}}" wx:key="name">
    <view class="freq-row">
      <text class="row-num">{{item.count}}</text>
      <!-- 缺少场景名显示 -->
    </view>
  </block>
  ```

- ❌ **问题4**：互动线索显示英文 tag（第98-105行）
  ```xml
  <text class="row-name">{{item.name}}</text>
  <!-- item.name 是 "general_support"，未做中文映射 -->
  ```

- ❌ **问题5**：存在"下周可以继续的一小步"板块（第115-118行）
  ```xml
  <view class="next-step-card">
    <text class="next-title">下周可以继续的一小步</text>
    <text class="next-text">{{report.next_week_suggestion}}</text>
  </view>
  ```

**互动线索来源逻辑（已确认）：**
- 后端：`backend/services/report_service.py` 第64-67行
- 从 `feedback_results.tags_json` 统计最常见的5个 tag
- tag 是英文（如 `general_support`, `high_demand_language`）
- 前端直接显示，未做中文映射

---

### 三、详细实现方案

#### 3.1 删除顶部冗长说明

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第2-8行**

**原代码：**
```xml
<view class="weekly-hero safe-card safe-card--hero">
  <view class="hero-copy">
    <text class="hero-kicker">本周复盘</text>
    <text class="hero-title">看看这一周的小变化</text>
    <text class="hero-summary">这不是评分，也不是判断。只是把记录和练习整理出来，帮你找到下周可以继续的一小步。</text>
  </view>
</view>
```

**修改为：**
```xml
<view class="weekly-hero safe-card safe-card--hero">
  <view class="hero-copy">
    <text class="hero-kicker">本周复盘</text>
    <text class="hero-title">看看这一周的小变化</text>
  </view>
</view>
```

**删除：** `<text class="hero-summary">...</text>`

#### 3.2 优化本周小变化卡片

##### 3.2.1 修改卡片结构和样式

> **【Claude订正 · 只改样式，别改数据绑定】** 4 格现状**已正确**绑定 data 字段（`{{frequentScenes.length}}` / `{{frequentEmotions.length}}` / `{{commonPatterns.length}}` / `{{completedCardsText ? '已记' : '待记'}}`，均经 `formatPairs` 处理）。本子节"原代码 `report.diaries_count`"是虚构、"修改为 `report.frequent_scenes.length`"也不对（应是 data 里的 `frequentScenes`，不是 `report.frequent_scenes`）。**故下面的数据绑定改写不要做**（会把已正确的绑定改坏），只保留 `.stat-card` 缩小居中的**样式**改造。

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第44-63行**

**原代码：**
```xml
<view class="stat-grid">
  <view class="stat-card">
    <text class="stat-num">{{report.diaries_count || 0}}</text>
    <text class="stat-label">类常见场景</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.emotions_count || 0}}</text>
    <text class="stat-label">类常见情绪</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.checkins_count || 0}}</text>
    <text class="stat-label">条互动索引</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.profiles_count || '待记'}}</text>
    <text class="stat-label">{{report.profiles_count ? '次画像' : '续写测试'}}</text>
  </view>
</view>
```

**修改为：**
```xml
<view class="stat-grid">
  <view class="stat-card">
    <text class="stat-num">{{report.frequent_scenes.length || 0}}</text>
    <text class="stat-label">类常见场景</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.frequent_emotions.length || 0}}</text>
    <text class="stat-label">类常见情绪</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.completed_cards.length || 0}}</text>
    <text class="stat-label">条互动索引</text>
  </view>
  <view class="stat-card">
    <text class="stat-num">{{report.profile_trend.profile_count || 0}}</text>
    <text class="stat-label">{{report.profile_trend.profile_count ? '次画像' : '续写测试'}}</text>
  </view>
</view>
```

**文件：`apps/miniprogram/pages/weekly-report/index.wxss`**

**查找 `.stat-card` 样式，修改宽度和对齐**

**原样式（需要查找）：**
```css
.stat-card {
  /* 当前样式 */
}
```

**修改为：**
```css
.stat-card {
  flex: 0 0 calc(50% - 12rpx);
  max-width: 200rpx;
  padding: 24rpx 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
}

.stat-num {
  display: block;
  color: var(--safe-primary);
  font-size: 48rpx;
  font-weight: 900;
  line-height: 1;
  text-align: center;
}

.stat-label {
  display: block;
  margin-top: 12rpx;
  color: var(--safe-text);
  font-size: 24rpx;
  line-height: 1.4;
  text-align: center;
}
```

#### 3.3 修复高频场景显示

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第83-91行**

**原代码：**
```xml
<block wx:for="{{frequentScenes}}" wx:key="name">
  <view class="freq-row">
    <text class="row-num">{{item.count}}</text>
  </view>
</block>
```

**修改为：**
```xml
<block wx:for="{{frequentScenes}}" wx:key="name">
  <view class="freq-row">
    <text class="row-name">{{item.name}}</text>
    <text class="row-count">{{item.count}} 次</text>
  </view>
</block>
```

**改动说明：**
- 添加 `<text class="row-name">{{item.name}}</text>` 显示场景名
- `{{item.count}}` 改为 `{{item.count}} 次`

#### 3.4 修复互动线索中文映射

##### 3.4.1 添加 tag 中文映射

**文件：`apps/miniprogram/pages/weekly-report/index.js`**

**在文件开头添加常量（第3行附近）：**

```javascript
const TAG_LABELS = {
  general_support: "一般支持",
  high_demand_language: "高要求语言",
  emotional_behavior: "情绪与行为",
  cognitive_flexibility: "认知灵活性",
  acceptance_openness: "接纳与开放",
  mindful_awareness: "觉察当下",
  self_compassion: "自我关怀",
  parental_burnout: "家长耗竭",
  parent_child_interaction: "亲子互动",
  academic_pressure: "学业压力",
  emotion_regulation: "情绪调节",
  uncertainty_intolerance: "不确定性不耐受",
  fear_negative_evaluation: "害怕负面评价",
  test_anxiety: "考试焦虑",
};
```

##### 3.4.2 修改数据处理逻辑

**文件：`apps/miniprogram/pages/weekly-report/index.js`**

**修改位置：第5-10行**

**原代码：**
```javascript
function formatPairs(items = []) {
  return items.map((item) => ({
    name: item[0],
    count: item[1],
  }));
}
```

**修改为：**
```javascript
function formatPairs(items = [], useTagLabel = false) {
  return items.map((item) => ({
    name: useTagLabel ? (TAG_LABELS[item[0]] || item[0]) : item[0],
    count: item[1],
  }));
}
```

**修改位置：第36-37行**

**原代码：**
```javascript
commonPatterns: formatPairs(report.common_patterns || []),
```

**修改为：**
```javascript
commonPatterns: formatPairs(report.common_patterns || [], true),
```

#### 3.5 删除"下周可以继续的一小步"板块

**文件：`apps/miniprogram/pages/weekly-report/index.wxml`**

**修改位置：第115-118行**

**删除以下代码：**
```xml
<view class="next-step-card">
  <text class="next-title">下周可以继续的一小步</text>
  <text class="next-text">{{report.next_week_suggestion}}</text>
</view>
```

---

### 四、验收标准

#### 4.1 顶部说明验收

**在微信开发者工具中测试：**
1. 进入本周复盘页面
2. 确认顶部只有：
   - ✅ "本周复盘"（标签）
   - ✅ "看看这一周的小变化"（标题）
   - ❌ 没有长文案说明

#### 4.2 本周小变化卡片验收

**在微信开发者工具中测试：**
1. 确认4个格子：
   - ✅ 宽度缩小（约200rpx）
   - ✅ 数字和文字居中对齐
   - ✅ 布局为 2x2 网格
2. 确认内容正确：
   - ✅ 第1格：X 类常见场景（取自 `frequent_scenes.length`）
   - ✅ 第2格：X 类常见情绪（取自 `frequent_emotions.length`）
   - ✅ 第3格：X 条互动索引（取自 `completed_cards.length`）
   - ✅ 第4格：X 次画像（取自 `profile_trend.profile_count`）

#### 4.3 高频场景验收

**在微信开发者工具中测试：**
1. 确认每行显示：
   - ✅ 场景名称（如"亲子沟通"）
   - ✅ 出现次数（如"3 次"）
2. 确认排序：
   - ✅ 按次数从高到低

#### 4.4 互动线索验收

**在微信开发者工具中测试：**
1. 确认显示中文：
   - ✅ `general_support` 显示为"一般支持"
   - ✅ `high_demand_language` 显示为"高要求语言"
   - ✅ 其他 tag 显示为对应中文
2. 确认未映射的 tag：
   - ✅ 如果 tag 不在映射表，显示原始英文（不报错）

#### 4.5 板块删除验收

**在微信开发者工具中测试：**
1. 确认页面底部：
   - ✅ 没有"下周可以继续的一小步"卡片
   - ✅ 只有"刷新复盘"和"回到首页"按钮

#### 4.6 边界验收

**必须符合：**
- ✅ 无数据时显示友好提示
- ✅ 各板块数据正确对应后端 API 返回值
- ✅ 代码检查：JS/WXML/WXSS 语法通过

**检查命令：**
```powershell
cd D:\codex\workspace\safehome1.0
node --check apps\miniprogram\pages\weekly-report\index.js
```

---

### 五、完成后更新文档

**1. 更新开发日志：**
文件：`docs/00_当前事实基准/开发日志.md`

追加一条：

```markdown
## 2026-06-30
- 本周复盘页面改造（T6-05）
  - 删除顶部冗长说明文案
  - 优化本周小变化4格：缩小宽度，居中文字
  - 修复高频场景显示：显示场景名+次数
  - 修复互动线索显示：tag 中文映射（general_support→一般支持）
  - 删除"下周可以继续的一小步"板块
```

**2. 更新 UI 验收清单：**
文件：`docs/02_专项进度与验收/UI与伦理边界验收清单.md`

在"本周复盘"章节更新：

```markdown
### 本周复盘页面

**验收结果：**
- ✅ 顶部说明简洁，无冗长文案
- ✅ 本周小变化4格缩小居中
- ✅ 高频场景显示场景名+次数
- ✅ 互动线索显示中文
- ✅ 已删除"下周一小步"板块
```

**3. 更新 Claude 使用记录：**
文件：`docs/10Claude协作/Claude使用记录.md`

在第 4 节追加：

```markdown
### T6-05 本周复盘页面改造
- 会话链接：（由用户补充）
- 完成时间：2026-06-30
- 交付内容：删除冗长文案 + 优化卡片 + 修复场景/线索显示 + 删除下周板块
- 关键决策：简化信息密度，提升可读性；tag 中文映射提升理解度
```

---

### 六、Codex 执行检查清单

**Codex 在执行本任务时，请按以下顺序操作：**

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的本周复盘页面截图
- [ ] 3. 修改 `apps/miniprogram/pages/weekly-report/index.wxml` 删除顶部长文案（第6行）
- [ ] 4. 修改 `index.wxml` 本周小变化4格的数据绑定（第44-63行）
- [ ] 5. 修改 `apps/miniprogram/pages/weekly-report/index.wxss` 的 `.stat-card` 样式（缩小居中）
- [ ] 6. 修改 `index.wxml` 高频场景显示逻辑（第83-91行，添加场景名）
- [ ] 7. 在 `apps/miniprogram/pages/weekly-report/index.js` 添加 `TAG_LABELS` 映射表
- [ ] 8. 修改 `index.js` 的 `formatPairs` 函数（添加 tag 映射参数）
- [ ] 9. 修改 `index.js` 的 `commonPatterns` 处理（第37行，传入 true）
- [ ] 10. 删除 `index.wxml` 的"下周一小步"板块（第115-118行）
- [ ] 11. 在微信开发者工具中测试本周复盘页面
- [ ] 12. 确认顶部简洁、4格缩小居中
- [ ] 13. 确认高频场景显示"场景名 X次"
- [ ] 14. 确认互动线索显示中文
- [ ] 15. 确认已删除"下周一小步"
- [ ] 16. 运行代码检查命令（JS 语法）
- [ ] 17. 更新 3 个文档（开发日志、UI验收、Claude记录）
- [ ] 18. 截图验收结果（优化前后对比），提交给用户确认

---

### 七、注意事项

1. **tag 映射表完整性**：确保常见 tag 都有中文映射，未映射的显示原文不报错
2. **4格数据准确性**：使用后端返回的数组长度（`.length`），不使用可能不存在的 `_count` 字段
3. **高频场景格式**：显示为"场景名 X次"，不只显示数字
4. **代码风格**：保持与现有代码一致（缩进、命名、注释）
5. **测试完整性**：必须在微信开发者工具中实际测试，确认数据正确显示

---

**任务状态：** 待执行
**预计工时：** 2-2.5 小时（前端修改1.5h + 样式优化0.5h + 测试验收0.5h）
**优先级：** P1（核心功能页面，影响用户体验）

---

## T6-06：训练页面改造

> **【Claude订正 · 本节初稿多为"(推测)"，以下为准】**
> - **API**：`api.listCards()`（:347）/ `api.recommendCards()`（:351）；**无 `getTrainingCards`**（3.4 的 `loadAllCards` 内改成 `api.listCards()`）。
> - **训练卡共 34 张**（"20/12张"作废）；改文案聚焦核心 5 张即可。
> - **字段名**：`theory_background`→**`theory_source`**、`target_competency`→**`target_skill`**、`practice_tips` 不存在（用 `reflection_questions`）。3.5 的 JSON 示例按此替换；**别新造同义字段**。
> - **硬约束**：`theory_source/target_skill/reflection_questions/not_suitable_for` 为 required 不可删；`reflection_questions`≥2；`not_suitable_for` 须含"高风险/危机/安全/现实支持"之一。("前额叶/杏仁核"等不在禁用词，可用。)
> - **training 页是静态 `trainingStages`，不调 API**；候选卡在 `training-card`（`loadCards`→`listCards/recommendCards`）。`suitable_for[0]` 改多场景 join 可行。新手路径"图标"是文字 `<text class="starter-icon">先</text>`，删它即删该节点。

### 一、任务目标

优化训练页面，提升视觉层次和信息展示：
1. **顶部标题居中**："从先稳定自己开始"居中显示
2. **删除新手推荐路径图标**：左侧小图标去掉
3. **优化新手推荐3个板块**：缩小上下高度，内容居中，保持横向排列
4. **新增"其他训练卡"入口**：在阶段三下方，独立卡片区域，进入后显示所有训练卡列表
5. **优化训练卡详情页内容**：使用更结构化的专业表达
6. **优化"适用情境"展示**：显示多个场景，避免误解为只有一个

**核心变更：**
- 顶部文案居中对齐
- 新手推荐路径简化（去图标，缩小板块）
- 新增"其他训练卡"入口（34张卡片全展示）
- 训练卡详情页文案重构（更结构化）
- 适用情境改为多场景展示

---

### 二、前端代码审核结论

**现有代码：**
- `apps/miniprogram/pages/training/index.wxml` - 训练页面结构
- `apps/miniprogram/pages/training/index.wxss` - 训练页面样式
- `apps/miniprogram/pages/training-card/index.wxml` - 训练卡详情页
- `content/training_cards.json` - 训练卡数据（34张卡片）

**审核结论：**
- ✅ 后端有34张训练卡数据，全部启用
- ❌ 问题1：顶部标题左对齐（第4行）
- ❌ 问题2：新手推荐路径有图标（第52行附近）
- ❌ 问题3：新手推荐3个板块高度较大（需缩小）
- ❌ 问题4：缺少"其他训练卡"入口
- ❌ 问题5：训练卡详情页文案过于口语化
- ❌ 问题6：适用情境只显示一个（`suitable_for` 数组第一项）

---

### 三、详细实现方案

#### 3.1 顶部标题居中

**文件：`apps/miniprogram/pages/training/index.wxss`**

**查找 `.hero-title` 样式，添加居中：**

```css
.hero-title {
  color: var(--safe-title);
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.25;
  text-align: center; /* 新增 */
}
```

同时确认 `.hero-copy` 也居中：

```css
.hero-copy {
  display: flex;
  flex-direction: column;
  align-items: center; /* 新增 */
  text-align: center; /* 新增 */
}
```

#### 3.2 删除新手推荐路径图标

**文件：`apps/miniprogram/pages/training/index.wxml`**

**修改位置：第51-62行（推测）**

**原代码（推测）：**
```xml
<view class="path-card">
  <view class="path-icon">图标</view>
  <text class="path-label">新手推荐路径</text>
  <text class="path-text">如果不知道从哪张卡开始，先按这三个小练习走一遍。</text>
</view>
```

**修改为：**
```xml
<view class="path-card">
  <text class="path-label">新手推荐路径</text>
  <text class="path-text">如果不知道从哪张卡开始，先按这三个小练习走一遍。</text>
</view>
```

**删除图标相关的样式（wxss）**

#### 3.3 优化新手推荐3个板块

**文件：`apps/miniprogram/pages/training/index.wxss`**

**修改板块样式（推测为 `.stage-preview-card` 或类似）：**

```css
.stage-preview-card {
  flex: 1;
  min-width: 180rpx;
  padding: 24rpx 16rpx; /* 原来可能是 32rpx 24rpx，缩小上下 */
  display: flex;
  flex-direction: column;
  align-items: center; /* 居中 */
  justify-content: center;
  text-align: center; /* 文字居中 */
  border: 1rpx solid var(--safe-border);
  border-radius: var(--safe-radius-md);
  background: var(--safe-card);
}

.stage-preview-title {
  display: block;
  color: var(--safe-title);
  font-size: 28rpx;
  font-weight: 800;
  line-height: 1.3;
  text-align: center; /* 居中 */
  margin-bottom: 8rpx;
}

.stage-preview-text {
  display: block;
  color: var(--safe-text);
  font-size: 24rpx;
  line-height: 1.5;
  text-align: center; /* 居中 */
}
```

#### 3.4 新增"其他训练卡"入口

**文件：`apps/miniprogram/pages/training/index.wxml`**

**在阶段三区域后添加（约第120行附近）：**

```xml
<!-- 其他训练卡入口 -->
<view class="safe-section">
  <view class="other-cards-entry" bindtap="openAllCards">
    <view class="entry-copy">
      <text class="entry-title">查看更多训练卡</text>
      <text class="entry-subtitle">浏览全部 34 张训练卡，找到适合你的练习</text>
    </view>
    <text class="entry-arrow">›</text>
  </view>
</view>
```

**文件：`apps/miniprogram/pages/training/index.wxss`**

**添加样式：**

```css
.other-cards-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 24rpx;
  border: 2rpx solid var(--safe-primary);
  border-radius: var(--safe-radius-md);
  background: var(--safe-primary-pale);
}

.entry-copy {
  flex: 1;
}

.entry-title {
  display: block;
  color: var(--safe-primary-deep);
  font-size: 30rpx;
  font-weight: 850;
  line-height: 1.3;
  margin-bottom: 8rpx;
}

.entry-subtitle {
  display: block;
  color: var(--safe-text);
  font-size: 24rpx;
  line-height: 1.5;
}

.entry-arrow {
  flex: 0 0 auto;
  color: var(--safe-primary);
  font-size: 48rpx;
  font-weight: 300;
}
```

**文件：`apps/miniprogram/pages/training/index.js`**

**添加方法（约第200行附近）：**

```javascript
openAllCards() {
  wx.navigateTo({
    url: "/pages/training-card/index?showAll=true",
  });
},
```

**文件：`apps/miniprogram/pages/training-card/index.js`**

**修改 `onLoad` 方法，支持显示全部卡片：**

```javascript
onLoad(options) {
  const showAll = options.showAll === "true";
  if (showAll) {
    this.loadAllCards();
  } else {
    this.loadCards(options);
  }
},

async loadAllCards() {
  this.setData({ loading: true, errorMessage: "" });

  try {
    const result = await api.getTrainingCards();
    
    if (!result.ok) {
      this.setData({
        loading: false,
        errorMessage: "无法加载训练卡列表",
      });
      return;
    }

    const cards = (result.data.cards || []).map((card) => ({
      id: card.id,
      title: card.title,
      purpose: card.purpose,
      duration: card.duration_minutes,
      tagsText: (card.tags || []).join("、"),
      todayGoal: card.purpose, // 使用 purpose 作为目标
      suitableScenarios: (card.suitable_for || []).join("、"), // 多场景
    }));

    this.setData({
      loading: false,
      cards,
    });
  } catch (err) {
    this.setData({
      loading: false,
      errorMessage: "加载失败，请重试",
    });
  }
},
```

#### 3.5 优化训练卡详情页内容（更结构化表达）

**文件：`content/training_cards.json`**

**需要重写部分训练卡的字段，使其更结构化。以下是改写示例：**

**原数据（情绪识别卡）：**
```json
{
  "id": "emotion_naming",
  "title": "情绪识别卡：先命名情绪",
  "purpose": "帮助家长在回应孩子前，先识别自己和孩子的情绪。",
  "steps": [
    "暂停 3 秒，先不急着讲道理。",
    "在心里说出自己的情绪：我现在是着急、失望，还是害怕？",
    "再尝试命名孩子的情绪：孩子可能是委屈、害怕，还是挫败？",
    "用一句非评判的话开头：我看到你现在很难受。"
  ],
  "example": "我看到你这次数学没考好后很沮丧，我也有点着急。我们先把发生了什么说清楚。"
}
```

**改为（更结构化）：**
```json
{
  "id": "emotion_naming",
  "title": "情绪识别卡：先命名情绪",
  "purpose": "通过暂停反应、识别情绪的方式，帮助家长在高情绪强度情境下建立觉察窗口，为后续有效沟通创造条件。",
  "theory_background": "基于情绪调节理论（Emotion Regulation Theory），情绪命名是情绪觉察的第一步，能够激活前额叶皮层对情绪的认知加工，降低杏仁核的自动化反应。",
  "target_competency": "情绪觉察能力（Emotional Awareness）",
  "steps": [
    "【暂停】当注意到情绪激活信号时，暂停 3 秒，不立即做出言语或行为反应。",
    "【自我识别】在内心命名自己的情绪状态：着急、失望、愤怒、担忧或其他。",
    "【他人识别】尝试推测孩子当前的情绪：委屈、害怕、挫败、愤怒或其他。",
    "【非评判开场】用一句描述性、非评判的话开启对话，如'我看到你现在很难受'。"
  ],
  "example": "【情境】孩子数学考试成绩不理想。\n【应用】我看到你这次数学没考好后很沮丧（识别孩子情绪），我也有点着急（识别自己情绪）。我们先把发生了什么说清楚（非评判开场）。",
  "practice_tips": [
    "初次练习时，可以先在纸上写下情绪词，帮助具体化。",
    "情绪词汇表可参考：着急、失望、愤怒、担忧、无力、内疚、害怕等。",
    "如果无法准确命名，可以用'不舒服''有压力'等宽泛词汇替代。"
  ]
}
```

**需要Codex按此模式重写以下核心训练卡：**
1. `emotion_naming` - 情绪识别卡
2. `cognitive_flexibility` - 认知灵活化卡
3. `pause_3_seconds` - 3秒暂停卡
4. `body_awareness` - 身体觉察卡
5. `validation_first` - 先确认卡

**其他训练卡保持原样，优先级低。**

#### 3.6 优化"适用情境"展示（多场景）

**文件：`apps/miniprogram/pages/training-card/index.wxml`**

**修改位置：约第57行**

**原代码（推测）：**
```xml
<view class="scenario-box">
  <text class="scenario-label">适用情境：</text>
  <text class="scenario-text">{{card.suitableScenario}}</text>
</view>
```

**修改为：**
```xml
<view class="scenario-box">
  <text class="scenario-label">适用情境</text>
  <text class="scenario-text">{{card.suitableScenarios}}</text>
</view>
```

**文件：`apps/miniprogram/pages/training-card/index.js`**

**修改数据处理（约第40-50行附近）：**

**原代码（推测）：**
```javascript
suitableScenario: card.suitable_for[0] || "多种情境",
```

**修改为：**
```javascript
suitableScenarios: (card.suitable_for || []).join("、") || "多种亲子互动情境",
```

**样式优化（让多个情境换行显示）：**

```css
.scenario-box {
  padding: 20rpx;
  border-left: 4rpx solid var(--safe-primary);
  border-radius: var(--safe-radius-sm);
  background: var(--safe-primary-pale);
  margin-bottom: 24rpx;
}

.scenario-label {
  display: block;
  color: var(--safe-primary-deep);
  font-size: 24rpx;
  font-weight: 800;
  margin-bottom: 12rpx;
}

.scenario-text {
  display: block;
  color: var(--safe-text);
  font-size: 26rpx;
  line-height: 1.7;
  word-wrap: break-word; /* 支持长文本换行 */
}
```

---

### 四、验收标准

#### 4.1 顶部标题验收
- ✅ "从先稳定自己开始"居中显示

#### 4.2 新手推荐路径验收
- ✅ 左侧图标已删除
- ✅ 3个板块高度缩小（padding 减小）
- ✅ 板块内容（标题+文字）居中对齐

#### 4.3 其他训练卡入口验收
- ✅ 在阶段三下方显示独立卡片区域
- ✅ 显示"查看更多训练卡"+"浏览全部34张训练卡"
- ✅ 点击进入训练卡列表页，显示所有34张卡片

#### 4.4 训练卡详情页验收
- ✅ 核心5张卡片使用结构化表达（purpose/theory_background/target_competency/practice_tips）
- ✅ 文案专业化，使用心理学术语

#### 4.5 适用情境验收
- ✅ 显示多个场景，用"、"分隔
- ✅ 如"家长催促前、亲子冲突后、孩子情绪激动时"

---

### 五、完成后更新文档

**1. 更新开发日志**
**2. 更新 UI 验收清单**
**3. 更新 Claude 使用记录**

---

### 六、Codex 执行检查清单

- [ ] 1. 读取本指令完整内容
- [ ] 2. 读取用户提供的训练页面截图
- [ ] 3. 修改 `.hero-title` 和 `.hero-copy` 样式（居中）
- [ ] 4. 删除新手推荐路径的图标元素
- [ ] 5. 修改新手推荐3个板块样式（缩小padding，居中）
- [ ] 6. 在阶段三后添加"其他训练卡"入口结构
- [ ] 7. 添加"其他训练卡"入口样式
- [ ] 8. 在 `training/index.js` 添加 `openAllCards` 方法
- [ ] 9. 在 `training-card/index.js` 添加 `loadAllCards` 方法
- [ ] 10. 重写 5 张核心训练卡的 JSON 数据（更结构化）
- [ ] 11. 修改适用情境数据处理（显示多场景）
- [ ] 12. 修改适用情境样式（支持换行）
- [ ] 13. 在微信开发者工具中测试训练页面
- [ ] 14. 测试"其他训练卡"入口跳转
- [ ] 15. 测试训练卡详情页新文案
- [ ] 16. 测试适用情境多场景显示
- [ ] 17. 更新 3 个文档
- [ ] 18. 截图验收结果

---

**任务状态：** 待执行
**预计工时：** 3-4 小时（文案重构1.5h + 前端修改1h + 样式优化0.5h + 测试1h）
**优先级：** P1（核心功能页面）

---

## T6-07：课程页面重新设计

> **【Claude订正 · 保留从 GitHub 拉取（用户决策 2026-07-01），但必须补以下防护】**
> - **微信合法域名**：外链封面/视频在真机/体验版需在「微信公众平台→开发管理→服务器域名」配置 `downloadFile` 合法域名，否则图片空白。开发者工具 `urlCheck:false` 能显示是假象、不代表真机可用。**建议把封面下载到本地 `assets/` 或转 Base64**，减少外链依赖。
> - **内容/版权/伦理**（心理健康产品红线）：GitHub 第三方课程须 ① 核对开源协议（标注来源/许可，避开不可商用或强传染协议）；② 人工过内容质量与边界（不得含诊断/治疗承诺，命中禁用词的删改）；③ 每门课加"内容来源 + 非诊断/非治疗"声明。**不可整包导入未审内容**。
> - **现状**：无 `content/courses.json`，`course/index.js` 是硬编码 5 门课、`openCourse` 仅弹 toast。本节实为"新建数据层 + 重写页面"，不是改已有 JSON。

### 一、任务目标

完全重新设计课程页面，打造吸引人的学习体验：
1. **全新视觉设计**：参考优秀的教育类 App 设计
2. **课程内容来源**：从 GitHub 开源社区搜索心理学、家庭教育相关课程数据
3. **支持分类**：按训练卡阶段分类（阶段一/阶段二/阶段三）
4. **支持搜索和筛选**：标题搜索、分类筛选、难度筛选
5. **课程详情页**：完整的课程信息展示
6. **学习进度跟踪**：标记已完成、学习中、未开始
7. **完成标记**：支持打卡完成

**核心变更：**
- 删除现有课程页面代码，完全重写
- 从 GitHub 获取开源课程数据
- 实现完整的课程学习系统

---

### 二、GitHub 课程数据搜索

**Codex 需要执行：**

1. 搜索 GitHub 上的开源课程项目：
   - 关键词：parenting psychology, family education, emotional intelligence, child development
   - 筛选条件：有结构化课程数据（JSON/Markdown）
   - 推荐仓库：psychology-courses, parenting-guides, family-education-resources

2. 提取课程数据结构：
   ```json
   {
     "id": "course_001",
     "title": "情绪管理基础课程",
     "category": "阶段一",
     "description": "帮助家长理解情绪的本质和调节方法",
     "duration": "30分钟",
     "difficulty": "入门",
     "instructor": "李明",
     "cover_image": "https://...",
     "lessons": [
       {
         "id": "lesson_001",
         "title": "什么是情绪",
         "duration": "10分钟",
         "content_type": "video",
         "content_url": "https://..."
       }
     ],
     "tags": ["情绪管理", "基础知识"],
     "status": "not_started"
   }
   ```

3. 整理成 `content/courses.json`

---

### 三、前端设计方案

#### 3.1 课程列表页设计

**参考设计风格：**
- 网易云课堂
- 得到 App
- Coursera

**布局结构：**
```
[搜索框]
[分类标签] 全部 | 阶段一 | 阶段二 | 阶段三
[筛选器] 难度 | 时长 | 讲师

[课程卡片]
- 封面图
- 标题
- 描述
- 时长 | 难度
- 学习进度条
- [开始学习] 按钮
```

**文件：`apps/miniprogram/pages/course/index.wxml`**

```xml
<view class="safe-page course-page">
  
  <!-- 搜索栏 -->
  <view class="search-bar">
    <input class="search-input" placeholder="搜索课程..." bindinput="onSearchInput" />
  </view>

  <!-- 分类标签 -->
  <view class="category-tabs">
    <button 
      wx:for="{{categories}}" 
      wx:key="key"
      class="category-tab {{activeCategory === item.key ? 'active' : ''}}"
      data-key="{{item.key}}"
      bindtap="switchCategory"
    >
      {{item.label}}
    </button>
  </view>

  <!-- 筛选器 -->
  <view class="filter-bar">
    <button class="filter-btn" bindtap="showDifficultyFilter">
      难度 {{difficultyFilter ? ': ' + difficultyFilter : ''}}
    </button>
    <button class="filter-btn" bindtap="showDurationFilter">
      时长 {{durationFilter ? ': ' + durationFilter : ''}}
    </button>
  </view>

  <!-- 课程列表 -->
  <view class="course-list">
    <view wx:for="{{courses}}" wx:key="id" class="course-card" bindtap="openCourse" data-id="{{item.id}}">
      <image class="course-cover" src="{{item.cover_image}}" mode="aspectFill" />
      <view class="course-info">
        <text class="course-title">{{item.title}}</text>
        <text class="course-desc">{{item.description}}</text>
        <view class="course-meta">
          <text class="course-duration">{{item.duration}}</text>
          <text class="course-difficulty">{{item.difficulty}}</text>
        </view>
        <progress class="course-progress" percent="{{item.progress}}" />
        <button class="course-action">
          {{item.status === 'completed' ? '已完成' : item.status === 'learning' ? '继续学习' : '开始学习'}}
        </button>
      </view>
    </view>
  </view>

</view>
```

#### 3.2 课程详情页设计

**文件：`apps/miniprogram/pages/course-detail/index.wxml`**

```xml
<view class="safe-page course-detail-page">
  
  <!-- 课程头部 -->
  <view class="course-header">
    <image class="course-banner" src="{{course.cover_image}}" mode="aspectFill" />
    <view class="course-header-info">
      <text class="course-title-large">{{course.title}}</text>
      <text class="course-instructor">讲师：{{course.instructor}}</text>
      <view class="course-stats">
        <text>{{course.duration}}</text>
        <text>{{course.difficulty}}</text>
        <text>{{course.lessons.length}} 课时</text>
      </view>
    </view>
  </view>

  <!-- 课程描述 -->
  <view class="course-section">
    <text class="section-title">课程介绍</text>
    <text class="course-description">{{course.description}}</text>
  </view>

  <!-- 课程目录 -->
  <view class="course-section">
    <text class="section-title">课程目录</text>
    <view wx:for="{{course.lessons}}" wx:key="id" class="lesson-item" bindtap="openLesson" data-id="{{item.id}}">
      <view class="lesson-number">{{index + 1}}</view>
      <view class="lesson-info">
        <text class="lesson-title">{{item.title}}</text>
        <text class="lesson-duration">{{item.duration}}</text>
      </view>
      <view class="lesson-status">
        {{item.completed ? '✓' : ''}}
      </view>
    </view>
  </view>

  <!-- 开始学习按钮 -->
  <view class="action-bar">
    <button class="primary-button" bindtap="startCourse">开始学习</button>
  </view>

</view>
```

---

### 四、验收标准

#### 4.1 课程数据验收
- ✅ 从 GitHub 获取至少 10 门课程数据
- ✅ 课程数据结构完整（包含所有必需字段）
- ✅ 按阶段一/阶段二/阶段三分类

#### 4.2 课程列表验收
- ✅ 搜索功能正常（标题搜索）
- ✅ 分类筛选正常（全部/阶段一/阶段二/阶段三）
- ✅ 难度筛选正常（入门/进阶/高级）
- ✅ 时长筛选正常（<15分钟/15-30分钟/>30分钟）
- ✅ 课程卡片美观，信息清晰

#### 4.3 课程详情验收
- ✅ 课程信息完整展示
- ✅ 课程目录可点击
- ✅ 支持标记完成

#### 4.4 学习进度验收
- ✅ 学习进度正确记录（本地存储）
- ✅ 进度条正确显示
- ✅ 已完成课程显示✓标记

---

### 五、Codex 执行检查清单

- [ ] 1. 搜索 GitHub 开源课程数据
- [ ] 2. 整理课程数据到 `content/courses.json`
- [ ] 3. 删除现有课程页面代码
- [ ] 4. 创建新的课程列表页（wxml/js/wxss/json）
- [ ] 5. 创建课程详情页（wxml/js/wxss/json）
- [ ] 6. 实现搜索功能
- [ ] 7. 实现分类筛选
- [ ] 8. 实现难度/时长筛选
- [ ] 9. 实现学习进度跟踪（本地存储）
- [ ] 10. 实现完成标记功能
- [ ] 11. 在微信开发者工具中测试
- [ ] 12. 更新文档
- [ ] 13. 截图验收

---

**任务状态：** 待执行
**预计工时：** 6-8 小时（数据搜索2h + 页面开发4h + 功能实现2h）
**优先级：** P2（新功能开发，非核心链路）

---

## T6-08："我的"页面全量改造

### 任务概述

**优先级：** P1  
**预计工时：** 8-10 小时  
**执行方式：** Codex 在 Claude 已提供的代码基础上继续完成

---

### 一、任务目标

全量改造"我的"页面，实现用户信息展示、消息系统、记录统计和安全支持：

1. **样式改造**：参考用户提供的第3张图片的简洁列表布局，保留现有配色
2. **用户信息动态化**：实现微信登录，显示微信头像和昵称
3. **统计数据真实化**：连续打卡天数、本周记录数从后端动态获取
4. **新增消息系统**：首页顶部消息入口 + 消息列表页 + 消息详情页
5. **人工督导反馈**：督导回复推送到消息列表
6. **删除冗余内容**：
   - 去掉绿框内容
   - 删除所有图案标签（"周""反""急""助"等）
   - 去掉"专业资源边界"前端入口
7. **紧急安全指引**：新增危机干预文字指引（200-300字，带步骤编号，包含蝴蝶拍等方法）

---

### 二、Claude 已提供的代码

#### 2.1 后端代码（已完成）

**以下代码 Codex 可以直接使用或参考修改：**

##### 微信登录接口
- 文件：`backend/routes/auth.py`
- 接口：`POST /api/auth/wechat-login`
- 功能：接收微信 code，换取 openid，创建或查询用户

##### 用户统计接口
- 文件：`backend/routes/profile.py`
- 接口：`GET /api/profile/stats`
- 功能：返回连续打卡天数和本周记录数
- 算法：`calculate_consecutive_days()` - 计算连续打卡天数

##### 消息系统接口
- 文件：`backend/routes/messages.py`（新建）
- 接口：
  - `POST /api/messages` - 创建消息
  - `GET /api/messages` - 获取消息列表（含未读数）
  - `GET /api/messages/<id>` - 获取消息详情并标记已读
  - `POST /api/messages/<id>/mark-read` - 标记已读

##### 数据库表
- `messages` 表结构已在 `backend/models.py` 中定义

##### 督导反馈推送
- 修改 `backend/routes/supervision.py`，督导回复时创建消息

#### 2.2 前端代码（已完成）

**以下代码 Codex 可以直接使用或参考修改：**

##### 首页顶部消息入口
- 文件：`apps/miniprogram/pages/home/index.wxml`
- 位置：顶部标题栏右侧
- 显示：🔔图标 + 未读数气泡
- 逻辑：`apps/miniprogram/pages/home/index.js` 中的 `loadUnreadCount()` 和 `openMessages()`

##### 消息列表页
- 目录：`apps/miniprogram/pages/messages/`
- 文件：`index.wxml`, `index.js`, `index.wxss`, `index.json`
- 功能：显示消息列表，未读消息高亮

##### 消息详情页
- 目录：`apps/miniprogram/pages/message-detail/`
- 文件：`index.wxml`, `index.js`, `index.wxss`, `index.json`
- 功能：显示完整消息内容

##### "我的"页面改造
- 文件：`apps/miniprogram/pages/profile/index.wxml`
- 样式：参考用户提供的第3张图片（简洁列表布局）
- 删除：所有图案标签（"周""反""急""助"等）

---

### 三、Codex 需要完成的部分

#### 3.1 紧急安全指引内容（未完成）

**文件：`apps/miniprogram/pages/emergency-guide/index.wxml`（新建）**

**内容要求：**
- 长度：200-300字简短版
- 格式：带步骤编号的指引
- 必须包含：蝴蝶拍技术、5-4-3-2-1接地法、深呼吸练习
- 必须包含：紧急联系方式（120、110、心理援助热线）

**建议内容结构：**

```xml
<view class="safe-page emergency-page">
  
  <view class="emergency-header">
    <text class="emergency-title">紧急安全指引</text>
    <text class="emergency-subtitle">在紧急情况下可以做些什么</text>
  </view>

  <view class="alert-card alert-important">
    <text class="alert-title">⚠️ 重要提醒</text>
    <text class="alert-text">本指引仅作为应急参考，不替代专业危机干预。如遇生命安全紧急情况，请立即拨打120或110。</text>
  </view>

  <view class="guide-section">
    <text class="guide-title">一、即时自我安抚方法</text>
    
    <view class="guide-item">
      <text class="guide-number">1. 蝴蝶拍技术</text>
      <text class="guide-text">双臂交叉放在胸前，左右手轮流轻拍对侧肩膀，每次约10-15下。这个动作可以帮助情绪降温。</text>
    </view>
    
    <view class="guide-item">
      <text class="guide-number">2. 5-4-3-2-1接地法</text>
      <text class="guide-text">说出5样你能看到的东西、4样你能触摸的、3样你能听到的、2样你能闻到的、1样你能尝到的。帮助你回到当下。</text>
    </view>
    
    <view class="guide-item">
      <text class="guide-number">3. 深呼吸练习</text>
      <text class="guide-text">吸气4秒，屏住7秒，呼气8秒。重复3-5次，帮助身体放松。</text>
    </view>
  </view>

  <view class="guide-section">
    <text class="guide-title">二、紧急联系方式</text>
    <view class="contact-list">
      <text class="contact-item">• 急救电话：120</text>
      <text class="contact-item">• 报警电话：110</text>
      <text class="contact-item">• 心理援助热线：400-161-9995（24小时）</text>
      <text class="contact-item">• 希望24热线：400-161-9995</text>
    </view>
  </view>

  <view class="guide-footer">
    <text class="guide-footer-text">如果您或孩子有自杀或自伤想法，请立即联系身边可信赖的人、学校老师或拨打上述热线。</text>
  </view>

</view>
```

**对应的样式和逻辑文件也需要创建。**

#### 3.2 紧急帮助说明页（未完成）

**文件：`apps/miniprogram/pages/emergency-resources/index.wxml`（新建）**

**内容：解释可用的现实资源**

#### 3.3 完善 API 调用

**文件：`apps/miniprogram/services/api.js`**

**需要添加的 API 方法：**

```javascript
// 微信登录
wechatLogin(code, nickname, avatarUrl) {
  return request("POST", API_ENDPOINTS.wechatLogin, {
    code,
    nickname,
    avatar_url: avatarUrl,
  });
},

// 获取用户统计
getUserStats(userId) {
  return request("GET", API_ENDPOINTS.userStats + queryString({ user_id: userId }));
},

// 消息相关
getMessages(params = {}) {
  return request("GET", API_ENDPOINTS.messages + queryString(params));
},

getMessage(messageId) {
  return request("GET", `${API_ENDPOINTS.messages}/${messageId}`);
},

markMessageRead(messageId) {
  return request("POST", `${API_ENDPOINTS.messages}/${messageId}/mark-read`);
},
```

**添加 API 端点常量：**

```javascript
// shared/constants/api.ts
wechatLogin: "/api/auth/wechat-login",
userStats: "/api/profile/stats",
messages: "/api/messages",
```

#### 3.4 "我的"页面逻辑完善

**文件：`apps/miniprogram/pages/profile/index.js`**

**需要实现的方法：**

```javascript
data: {
  userInfo: {},
  userStats: {},
  loading: true,
},

onLoad() {
  this.loadUserInfo();
  this.loadUserStats();
},

async loadUserInfo() {
  // 从本地存储获取用户信息
  // 或调用 API 获取
},

async loadUserStats() {
  try {
    const result = await api.getUserStats();
    if (result.ok) {
      this.setData({
        userStats: {
          check_in_days: result.data.check_in_days,
          weekly_record_count: result.data.weekly_record_count,
        },
      });
    }
  } catch (err) {
    console.error("loadUserStats error:", err);
  }
},

// 各个跳转方法
openWeeklyReport() {
  wx.navigateTo({ url: "/pages/weekly-report/index" });
},

openFeedbackHistory() {
  // 跳转到反馈历史页
},

openTrainingHistory() {
  // 跳转到训练记录页
},

openAssessmentHistory() {
  // 跳转到测评记录页
},

openSupervision() {
  wx.navigateTo({ url: "/pages/supervision/index" });
},

openSupervisionGuide() {
  // 跳转到专业资源说明页
},

openEmergencyGuide() {
  wx.navigateTo({ url: "/pages/emergency-guide/index" });
},

openEmergencyResources() {
  wx.navigateTo({ url: "/pages/emergency-resources/index" });
},

openBoundary() {
  // 跳转到知情与边界页
},

openPrivacy() {
  wx.navigateTo({ url: "/pages/privacy/index" });
},
```

#### 3.5 微信登录流程（前端部分）

**需要在小程序启动时或"我的"页面首次加载时触发：**

```javascript
// app.js 或 profile/index.js
async doWechatLogin() {
  try {
    // 获取微信登录凭证
    const loginRes = await wx.login();
    const code = loginRes.code;
    
    // 获取用户信息（需要用户授权）
    const userInfoRes = await wx.getUserProfile({
      desc: '用于完善用户资料'
    });
    
    const { nickName, avatarUrl } = userInfoRes.userInfo;
    
    // 发送到后端
    const result = await api.wechatLogin(code, nickName, avatarUrl);
    
    if (result.ok) {
      // 保存用户信息到本地
      wx.setStorageSync('user_id', result.data.user_id);
      wx.setStorageSync('user_info', {
        nickname: result.data.nickname,
        avatar_url: result.data.avatar_url,
      });
      
      this.setData({
        userInfo: {
          nickname: result.data.nickname,
          avatar_url: result.data.avatar_url,
        },
      });
    }
  } catch (err) {
    console.error("wechatLogin error:", err);
  }
}
```

#### 3.6 注册新页面路由

**文件：`apps/miniprogram/app.json`**

**在 `pages` 数组中添加：**

```json
"pages/messages/index",
"pages/message-detail/index",
"pages/emergency-guide/index",
"pages/emergency-resources/index"
```

#### 3.7 后端蓝图注册

**文件：`backend/app.py`**

**确保已注册：**

```python
from routes.messages import bp as messages_bp

app.register_blueprint(messages_bp)
```

#### 3.8 数据库表创建

**文件：`backend/models.py`**

**确保已添加 `messages` 表定义到 `SCHEMA` 列表。**

**确保 `users` 表有以下字段：**
- `wechat_openid`
- `avatar_url`

**使用 `ensure_column` 添加：**

```python
# backend/database.py 的 ensure_schema_columns() 中
"users": [
    ("wechat_openid", "TEXT"),
    ("avatar_url", "TEXT"),
],
"messages": [],  # 已在 SCHEMA 中定义完整
```

---

### 四、验收标准

#### 4.1 微信登录验收
- [ ] 用户首次进入可以授权登录
- [ ] 登录后显示微信昵称和头像
- [ ] 用户信息保存到本地存储和后端数据库

#### 4.2 用户统计验收
- [ ] "连续打卡X天"显示正确（情绪日记+训练打卡）
- [ ] "本周有X条记录"显示正确
- [ ] 数据从后端动态获取，非硬编码

#### 4.3 消息系统验收
- [ ] 首页顶部显示消息图标
- [ ] 有未读消息时显示红色数字气泡
- [ ] 点击进入消息列表页
- [ ] 消息列表显示正确，未读消息高亮
- [ ] 点击消息进入详情页
- [ ] 查看消息后自动标记已读

#### 4.4 督导反馈验收
- [ ] 督导回复后，消息推送到用户消息列表
- [ ] 用户收到"老师回复了您的补充内容"通知
- [ ] 点击消息可查看督导回复内容

#### 4.5 "我的"页面样式验收
- [ ] 页面布局参考第3张图片（简洁列表）
- [ ] 删除所有图案标签（"周""反""急""助"等）
- [ ] 删除绿框内容
- [ ] 删除"专业资源边界"入口
- [ ] 所有菜单项文字居中

#### 4.6 紧急安全指引验收
- [ ] 内容长度200-300字
- [ ] 包含蝴蝶拍技术说明
- [ ] 包含5-4-3-2-1接地法
- [ ] 包含深呼吸练习
- [ ] 包含紧急联系方式（120/110/热线）
- [ ] 带步骤编号，结构清晰

---

### 五、Codex 执行检查清单

**Codex 请按以下顺序执行：**

#### 阶段一：后端实现（3-4h）

- [ ] 1. 在 `backend/models.py` 添加 `messages` 表定义
- [ ] 2. 在 `backend/models.py` 确保 `users` 表有 `wechat_openid` 和 `avatar_url` 字段
- [ ] 3. 创建 `backend/routes/messages.py`，实现消息 CRUD 接口
- [ ] 4. 在 `backend/routes/auth.py` 实现微信登录接口
- [ ] 5. 在 `backend/routes/profile.py` 实现用户统计接口
- [ ] 6. 修改 `backend/routes/supervision.py`，督导回复时创建消息
- [ ] 7. 在 `backend/app.py` 注册 messages_bp 蓝图
- [ ] 8. 启动后端，测试 API 接口

#### 阶段二：前端实现（4-5h）

- [ ] 9. 在 `shared/constants/api.ts` 添加新端点常量
- [ ] 10. 在 `apps/miniprogram/services/api.js` 添加 API 方法
- [ ] 11. 修改 `apps/miniprogram/pages/home/index.wxml` 添加消息图标
- [ ] 12. 修改 `apps/miniprogram/pages/home/index.js` 实现 `loadUnreadCount` 和 `openMessages`
- [ ] 13. 创建消息列表页（`pages/messages/`）
- [ ] 14. 创建消息详情页（`pages/message-detail/`）
- [ ] 15. 改造"我的"页面（`pages/profile/`）- 样式参考第3张图
- [ ] 16. 实现"我的"页面逻辑（用户信息+统计数据）
- [ ] 17. 创建紧急安全指引页（`pages/emergency-guide/`）
- [ ] 18. 创建紧急帮助说明页（`pages/emergency-resources/`）
- [ ] 19. 在 `app.json` 注册新页面路由
- [ ] 20. 实现微信登录流程

#### 阶段三：测试验收（1-2h）

- [ ] 21. 测试微信登录（获取头像和昵称）
- [ ] 22. 测试用户统计数据显示
- [ ] 23. 测试消息系统（创建消息→列表显示→查看详情→标记已读）
- [ ] 24. 测试督导反馈推送
- [ ] 25. 测试"我的"页面所有跳转
- [ ] 26. 测试紧急安全指引内容完整性
- [ ] 27. 检查所有图案标签已删除
- [ ] 28. 检查样式符合第3张图布局
- [ ] 29. 运行代码检查（JS/WXML 语法）
- [ ] 30. 截图验收结果

---

### 六、注意事项

#### 6.1 微信登录配置

**需要配置环境变量：**

```bash
# .env 文件
WECHAT_APPID=你的小程序AppID
WECHAT_SECRET=你的小程序Secret
```

#### 6.2 连续打卡天数算法

**逻辑：**
- 从今天开始倒推
- 如果当天有记录（`emotion_diaries` 或 `checkins` 任一），计数+1
- 继续检查前一天
- 直到遇到某天没记录，停止

#### 6.3 本周记录数定义

**本周：** 从本周一到本周日  
**记录数：** `emotion_diaries` 表记录数 + `checkins` 表记录数

#### 6.4 消息类型

**当前只支持：** `supervision_feedback`（督导反馈）  
**未来可扩展：** 系统通知、训练提醒等

#### 6.5 图案标签删除

**需要删除的图案：**
- "周"（周报入口）
- "反"（历次反馈）
- "练"（训练记录）
- "测"（测评记录）
- "督"（人工督导）
- "询"（专业资源说明）
- "急"（紧急安全指引）
- "助"（紧急帮助说明）
- "知"（知情与边界）
- "隐"（隐私说明）

**改为：** 纯文字菜单项，文字居中

---

### 七、完成后更新文档

**1. 更新开发日志**

```markdown
## 2026-06-30
- "我的"页面全量改造（T6-08）
  - 实现微信登录，显示用户头像和昵称
  - 新增消息系统（列表+详情+未读提醒）
  - 用户统计动态化（连续打卡天数+本周记录数）
  - 督导反馈推送到消息列表
  - 样式改造：简洁列表布局，删除图案标签
  - 新增紧急安全指引（含蝴蝶拍等方法）
```

**2. 更新 API 文档**

添加新接口文档：
- `POST /api/auth/wechat-login`
- `GET /api/profile/stats`
- 消息相关接口

**3. 更新数据库文档**

添加 `messages` 表说明

**4. 更新 Claude 使用记录**

```markdown
### T6-08 "我的"页面全量改造
- 会话链接：（补充）
- 完成时间：2026-06-30
- 交付内容：微信登录+消息系统+用户统计+样式改造+安全指引
- 关键决策：Claude 提供代码框架，Codex 完成实现和集成
```

---

### 八、问题与支持

**如果 Codex 遇到以下问题：**

1. **微信登录接口调用失败**：检查 AppID 和 Secret 配置
2. **连续打卡天数计算不准**：检查日期格式和数据库查询逻辑
3. **消息未推送**：检查督导回复接口是否正确调用消息创建
4. **样式不符合第3张图**：参考图片的简洁列表布局，使用纯白背景+灰色分隔线

**可随时向 Claude 反馈问题，Claude 会协助调整。**

---

**任务状态：** 待执行  
**优先级：** P1  
**预计工时：** 8-10 小时

---

**Codex 可以在 Claude 提供的代码基础上开始执行了！** ✅

---

# 任务七：四层一致性审查与修复（API契约 / Flask后端 / React Web / SQLite·MySQL）

> 创建时间：2026-07-01｜来源：Claude 四路并行核实审查（Explore over `d:\codex\workspace\safehome1.0`）
> 基准（最新进度）：**量表录入**——2026-06-29 worksheet 构建/后端 API/shared/小程序链路已落地，已入库 `assessment_worksheets`（27 份，16 启用），后台 admin CRUD 后端已实现；**聚类画像**——2026-06-29~30 已生成 7 个产品候选模型 + 落点接口 `GET /api/assessment-results/<id>/profile-position` + 小程序 Canvas + Web ECharts。
> 性质：**对已实现部分做一致性修复与补齐**，不是从零开发。多条为两路 agent 交叉确认。
> 优先级：**P0**=数据损坏/画像不可用/后台缺功能；**P1**=契约不一致/健壮性；**P2**=清理与统一。

## 优先级总览

| 子任务 | 层 | 核心 | 优先级 |
|---|---|---|---|
| T7-01 | 后端+DB | 画像落点链路打通（cluster0空串 / scale_id兜底 / 回填 / 题号对齐 / 交叉校验） | **P0** |
| T7-02 | 契约+Web | 后台量表管理（admin worksheet CRUD 端点+类型+Web 页面） | **P0** |
| T7-03 | 契约+Web+小程序 | 画像落点字段补齐（strength_note / small_step / display_name） | P1 |
| T7-04 | 后端 | 落点接口健壮性（GET 回填 / 置信度阈值 / model 归属校验 / list 规范化） | P1 |
| T7-05 | DB | 索引 / REAL→DOUBLE / 健康检查 / 白名单 | P1 |
| T7-06 | 后端+小程序 | 遗留统一（学生画像去硬编码 / 端点漂移 / review_status / worksheet 下线） | P2 |
| T7-07 | — | 验收 | — |

---

## T7-01：聚类画像落点链路打通（P0｜后端 + DB）

落点链路 `scores → model → 落点 → 接口` 当前**端到端未真正打通**，7 个产品模型里约 4 个对用户恒不可用，且簇 0 落点静默损坏。

| # | 问题 | 文件:行 | 改法 |
|---|---|---|---|
| 1 | **`cluster_id=0` 写成空串**（簇从 0 编号的 PRFQ/SCS 高频命中；后端+DB 两路确认）。列将统一为 **INTEGER**（见 T7-05#5） | `backend/routes/assessments.py:386` | `cid=(position.get("position") or {}).get("cluster_id"); cluster_val = None if cid is None else int(cid)` —— None 安全、不再 `... or ""` 短路丢 0；存 int |
| 2 | `_choose_model` 自动兜底**只按 `worksheet_id` 匹配**，4/7 模型 `worksheet_id=None` 永远选不中 | `backend/services/assessment_profile_service.py:58-62` | 兜底候选改 `model.get("worksheet_id")==wid or model.get("scale_id")==wid`；hplp 有两个模型共享 scale_id，需指定保留哪个或给不同 worksheet_id |
| 3 | worksheet 普遍缺 `profile_model_id`、模型普遍缺 `worksheet_id`，build 脚本不回填 | `backend/scripts/build_worksheets.py:149` | build 阶段加载 `content/profiles`，按 scale_id/worksheet_id 反查回填 worksheet 的 `profile_model_id`（让链路在静态内容层即连通） |
| 4 | `rsca_adolescent_resilience` 模型 23 题号与 worksheet `questions[].id` **0/23 匹配**，即便选中也必抛"题项不足" | `content/profiles/*rsca*` 的 `features[].worksheet_question_id` vs `content/assessment_worksheets.json` rsca 题号；消费 `assessment_profile_service.py:225-227` | 对齐题号（重建该 worksheet 或修模型）；`regulatory_focus_general_18` 缺 1 题同理补齐 |
| 5 | `validate_content.py` **不校验 worksheet↔model 连通性**，放任 #2/#4 静默通过 | `backend/scripts/validate_content.py:194-196,383-433` | 新增交叉规则：模型声明 worksheet_id/scale_id 时校验对应 worksheet 存在且题号覆盖率 ≥ 运行时门槛（`assessment_profile_service.py:226`）；worksheet 声明 profile_model_id 时校验模型存在 |

**完成标准**：青少年情绪弹性/RFQ-8/RSCA/HPLP/一般调节聚焦/PRFQ/SCS 各自填完→落点接口 `available:true` 且簇 id 正确落库（含簇 0）；`validate_content.py` 能拦断链。

---

## T7-02：后台量表管理（P0｜契约 + Web）

后端 `GET/POST /api/admin/worksheets` + `PUT /api/admin/worksheets/<id>` 已实现（`backend/routes/admin.py:593-655`，鉴权 `require_role("admin", allow_legacy_admin=True)`），但 **shared / web / 小程序三端零声明**，后台无法查看/管理驱动真实测评+画像的 DB 量表（契约+Web 两路确认）。ScalesReview 读的是构建期静态 `scales_catalog.json`，与 `assessment_worksheets` 表不是同一份数据。

1. **shared**：`shared/constants/api.ts` 增 `adminWorksheets: "/api/admin/worksheets"`；`shared/types/api.ts` 定义 `AdminWorksheet`（字段对齐 `admin.py:72-100` 的 `_worksheet_from_row`）与 `AdminWorksheetInput`（对齐 `WORKSHEET_WRITABLE_FIELDS` `admin.py:33-62`）。
2. **web service**：`apps/web/src/services/safehomeApi.ts` 增 `listAdminWorksheets / createAdminWorksheet(input) / updateAdminWorksheet(id, input)`，复用现有 `adminHeaders(adminToken)` 模式。
3. **web 页面**：新增 `WorksheetsManagement.tsx`（挂 `/content/worksheets`，role 限 admin），在 `main.tsx:43-61` 注册路由+导航：列表（含 disabled）、详情（questions/dimensions/scoring_notes）、表单编辑白名单字段、`enabled_for_user` 开关、`profile_model_id` 绑定。ScalesReview 保留为"content 目录只读视图"但页面注明"不等于 DB 量表"。
4. **后端补全**：admin worksheet 缺 **DELETE/下线接口** → 补 `@bp.delete("/worksheets/<id>")`（软删：`enabled_for_user=0`+`review_status=disabled`+写 audit_log）。

**完成标准**：admin 在 Web 可查看/新增/编辑/启用停用 DB 量表，并能绑定 `profile_model_id`；`npm run build` 通过。

---

## T7-03：画像落点字段补齐（P1｜契约 + Web + 小程序已在用）

后端落点返回 `strength_note / small_step / position.display_name / clusters[].display_name / explanation`，**小程序已渲染**，但 **shared 类型缺这些字段 → web TS 取不到 → ResearchDashboard 不展示**（契约+Web 两路确认）。

1. **shared**（`shared/types/api.ts`）：`AssessmentProfilePosition` 顶层补 `strength_note?: string; small_step?: string;`；`.position` 补 `display_name?: string;`；`AssessmentProfileCluster` 补 `display_name?: string;`。
2. **Web 展示**（`apps/web/src/components/ProfileScatterChart.tsx:46`、`pages/ResearchDashboard.tsx:361`）：散点标签与标题优先用 `display_name`（回退 `profile_name`）；落点区块增展示 `explanation / strength_note / small_step / interpretation.message`。
3. 顺带补具名类型 `AssessmentGroupNode/AssessmentGroup`（替换 `AssessmentListResponse.groups` 的匿名内联类型，`api.ts:751-755`）；`AssessmentWorksheet` 补 `dimensions? / dimension_score_method? / scoring_notes?`（后端 `get_assessment` 已下发，内容库 25 份在用）。

**完成标准**：Web 研究看板画像区与小程序展示同源字段；TS 无 `as any`。

---

## T7-04：落点接口健壮性（P1｜后端）

| # | 问题 | 文件:行 | 改法 |
|---|---|---|---|
| 1 | POST 落点写 DB、GET 落点只实时算**不回填**；POST 时模型不可用被静默 pass 后，DB `profile_*` 永远空 | `backend/routes/assessments.py:372-396,441-479` | GET 计算成功后顺带 UPDATE `profile_*` 列（复用修正后的 cluster_id 逻辑） |
| 2 | 低置信度阈值 `0.05` 过低，护栏几乎不触发（与"不贴标签"边界冲突） | `assessment_profile_service.py:13,178-184` | 结合复核校准（如 0.15~0.2），设为可配置 + 补单测 |
| 3 | GET `?model_id=` 命中即用，**不校验该模型属于此 worksheet** | `assessment_profile_service.py:46-50` | 命中后校验 `model.worksheet_id/scale_id == worksheet.id`，不符则忽略或报不可用 |
| 4 | `list_assessment_results` 返回裸行，未解析 `answers_json/scores_json`、带出空串 cluster | `backend/routes/assessments.py:414-438` | 统一解析 JSON + 规范 cluster（修 T7-01#1 后自然一致） |
| 5 | ✅**新增 admin 全量测评结果列表**（研究看板跨用户，用户已确认做） | 新增 `GET /api/admin/assessment-results`（`require_role("admin")`，跨 user，支持 `worksheet_id/profile_model_id` 过滤+分页）+ shared 端点常量 + web `safehomeApi.listAdminAssessmentResults` + `ResearchDashboard` 有后台令牌时改调该接口 | 中 |

---

## T7-05：数据库层（P1｜双后端）

| # | 问题 | 文件:行 | 改法 | 优先 |
|---|---|---|---|---|
| 1 | `ensure_column` 后补的 `REAL` 列在 MySQL 不转 DOUBLE（落点 pc1/pc2/confidence、student_profiles 距离列均后补） | `backend/database.py:236-238` | 在 `mysqlize_column_definition` 对结果同样 `.replace("REAL","DOUBLE")` | 中 |
| 2 | `assessment_results` **无任何索引**，且不在 `REQUIRED_HEALTH_TABLES` | `models.py:399-411`、`database.py:14-25` | 加 `idx_assessment_results_user_created(user_id, created_at)`；把 `assessment_results` 加进必需表；可选加列存在性检查 | 中 |
| 3 | 白名单缺 `sensitive_category/source_file/source_title/display_title` 等短列（MySQL 落 TEXT，无法直接索引/等值） | `database.py:28-119` | 按需加入 `MYSQL_VARCHAR_COLUMNS` | 低中 |
| 4 | `review_status` 缺省 `approved` 与内容侧 `pilot_review_required` 相反（缺省即放行风险） | `models.py:173`、`database.py:775`、`admin.py:129` vs `build_worksheets.py:144` | DB 层缺省与内容侧统一（建议缺省 pilot/未审），并在 validator 校验 worksheet.review_status ∈ 枚举 | 低 |
| 5 | ✅**已定：统一改 INTEGER**（`profile_cluster_id` 对齐 `student_profiles.cluster_id`） | `database.py:533`列定义、`:60`白名单 | ①列定义 TEXT→INTEGER；②从 `MYSQL_VARCHAR_COLUMNS` **移除** `profile_cluster_id`；③写迁移：MySQL `ALTER ... MODIFY`、SQLite 重建/`ensure_column` 不改存量需单独迁移，空串→NULL；④升 `CURRENT_SCHEMA_VERSION`；⑤T7-01#1 写 int | 中（含存量迁移） |

---

## T7-06：遗留统一项（P2｜后端 + 小程序）

1. **学生画像去硬编码**：`student_profile_model_service.py` 是与 `assessment_profile_service` 重复的另一套 z/PCA/距离/置信度，且 `_validate_answers:102-108` 硬编码 `{"1".."5"}`、`score_student_answers:130` 硬编码 `6-raw`。抽公共工具两 service 共用；学生侧 1-5/反向改为从 likert 上下界推导。
2. **小程序端点漂移**：`apps/miniprogram/services/api.js:8-32` 自带一份 `API_ENDPOINTS`，比 shared 缺 ~14 键，`getAssessmentProfilePosition:379` 硬编码路径。最小补齐已用端点 + privacy/family 缺失方法；长期根治=构建期注入 shared 常量。
3. **review_status 枚举**三处取值域统一（见 T7-05#4）。
4. **契约纠偏**：`User` 类型补 `username?/anonymous_id?/status?`、`UserRole` 补 researcher/supervisor；`admin-create-account` 端点可补声明。
5. **401 文案**（`safehomeApi.ts:417-422`）：登录失败别显示"后台令牌无效"，优先用后端 `error.message`，仅 admin-token 接口用云托管提示。

---

## T7-07：任务七验收

```text
后端：validate_content.py（含新交叉校验）通过 → pytest 通过
画像：7 个候选模型各自填完 → profile-position available:true、簇 id 正确落库（含簇0）→ GET 回填 DB
契约：shared 补字段后 Web npm run build 通过；小程序 JS 检查通过；端点三端核对
Web ：/content/worksheets 量表 CRUD 可用；研究看板画像区展示 display_name/strength_note/small_step
DB  ：healthz/deep 含 assessment_results 必需表与 worksheets_sync；MySQL 下落点列为 DOUBLE
```

## 【已确认决策 · 用户 2026-07-01】

1. **研究看板跨用户画像** → ✅ **做**：新增后端 admin 全量测评结果列表端点（见 **T7-04#5**），研究看板改调该接口，看全部参与者落点。
2. **cluster_id 类型** → ✅ **统一改 INTEGER**（对齐 `student_profiles.cluster_id`）：见 **T7-05#5**（含存量迁移 + 升 schema 版本）；**T7-01#1** 落点写库相应存 int。
3. **微信登录** → ✅ **归 T6-08 从零实现**：`/api/auth/wechat-login` 在 T6-08 补齐；任务七不重复，仅做 **T7-06#4** 的 `User` 类型纠偏。

---

## T7-08：任务七补遗（对比 6.30 已交付的训练推荐层后核实，2026-07-01）

> 6.30 已交付训练推荐引擎（T5）与画像簇→训练卡映射，任务七初稿只审了「量表录入 + 聚类画像落点」，**漏审了训练推荐这一层**。已直接核实代码，结论与补充如下。

### 核实结论：训练推荐层基本已打通（**不是缺口，勿重复开发**）
- `evaluate_training_rules` 已接入 `create_assessment_result`（`backend/routes/assessments.py:401-406`），填完量表返回 `recommended_card_ids` ✓
- 日记侧 `_match_diary_training_rules` 已从 `[:1]` 改为 `[:2]`（`backend/routes/feedback.py:74`）✓
- 画像簇 `recommended_card_ids`/`card_reason` 已落地 **8 个** `content/profiles/*.json`，且 `build_assessment_profile_position` 已透传（`assessment_profile_service.py:290-291`）✓
- 小程序 `assessment-result`（wxml+js）已读取展示簇推荐卡 ✓

### 补充缺口（任务七需补做）

| # | 问题/缺口 | 文件:行 | 改法 | 优先级 |
|---|---|---|---|---|
| 1 | **Web 研究看板不展示簇推荐卡**（与 T7-03 同源：web 也没展示 display_name/strength_note） | `apps/web/src/pages/ResearchDashboard.tsx`（grep `recommended_card_ids` 0 命中） | 落点区补展示 `clusters[].recommended_card_ids` + `card_reason`（"与你最近群体常练的卡"）；并入 T7-03 一起做 | P1 |
| 2 | **卡 id 悬空引用未校验**：`assessment_training_map.json`/`diary_training_map.json`/`content/profiles/*.json` 的 `recommended_card_ids` 是否都存在于 `training_cards.json`（34 张） | `backend/scripts/validate_content.py` | 加交叉校验（与 T7-01#5 worksheet↔model 同批补） | P1 |
| 3 | `card_service.recommend_cards` 无 tag 命中时的 fallback 是否仍顺序前 N | `backend/services/card_service.py:14-28 之后` | 确认；若是，改按 card `type` 多样化采样（每型取 1） | P2 |
| 4 | **文档同步（任务七收尾必做）**：任务七新增 `GET /api/admin/assessment-results`、`cluster_id` 改 INTEGER、新增列/索引、shared 类型字段 | `docs/03_技术真相/{API接口文档.md, 数据库字段说明.md, 数据字典.md}` | 随代码同步更新（项目统一口径第 7 条强制）；T7-07 验收增一条"文档已同步" | P1 |
| 5 | 认证层：6.30 已接入登录/注册+token，属"需人工验收"项 | — | 任务七仅 T7-06 纠偏 User 类型/401 文案，**无新增代码缺口**（确认不漏审） | — |

### T7-07 验收补充
```text
+ 训练推荐：填完量表→recommended_card_ids 非空；簇推荐卡在小程序与 Web 落点区均可见
+ 卡引用：validate_content 校验 *_training_map/profiles 的 card id 均存在于 training_cards.json
+ 文档：API接口文档.md / 数据库字段说明.md / 数据字典.md 随新端点与 cluster_id 类型变更同步
```

---

# 任务八：温度计全天曲线 · 反射弧三步 · 训练中心分层与项目测试 · 情感计算与SNA雏形 · 跨层审查

> 创建 2026-07-01｜Claude｜接任务七后。来源：用户 4 项新需求 + 一轮跨层审查。
> **决策（用户 2026-07-01）**：训练中心=三块；项目内容=框架+首节完整样例+其余大纲；情感计算/SNA=离线雏形（`analysis/profiling/`，脱敏输出，不进后端运行时）。
> **前置**：T6-01 情绪温度计**尚未由 Codex 实现**（`emotion_thermometer` 表不在 models.py）。T8-01 是对 T6-01 的**增补**——执行时先落 T6-01 基础表/接口，再叠 T8-01。

## T8-01：情绪温度计——每日多次记录 + 全天情绪曲线（增补 T6-01）

**现状**：`emotion_thermometer`（T6-01 计划：id/user_id/intensity_level 1-10/brief_text/created_at）**每条一行、天然支持一天多次记录**，无需改表结构；缺的是"按日拉取 + 曲线展示"。

**后端**
- 新增按日查询 `GET /api/emotion-thermometer/day?user_id=&date=YYYY-MM-DD`（date 缺省=今天）→ 当日记录按 `created_at` 升序 + 汇总 `{min,max,avg,count}`。
- **日期过滤用双后端安全写法** `WHERE user_id=? AND substr(created_at,1,10)=?`，date 串 Python 端算好传参（**禁 `DATE('now')`**，见任务六总表 B）。
- 索引 `emotion_thermometer(user_id, created_at)` 进 INDEX_SQL。

**小程序**
- thermometer 页加"今日曲线"区（或独立 `pages/thermometer-day`）：Canvas 2D 折线图，x=当日时间、y=强度 1–10；每点可点看 `brief_text`+时间；空态"今天还没有记录"。
- 复用纯函数 `utils/chart.js`；rpx→px 适配 dpr；单次绘制无动画循环。
- 入口：记录成功后"查看今天波动"；首页温度计卡副标"今天已记录 N 次"。

**shared**：`EmotionThermometerDayResponse { date; items[]; summary{min,max,avg,count} }`；端点常量 `emotionThermometerDay`。
**验收**：一天多记录→曲线按时间连线正确；跨零点不串天（UTC 归日一致，与 T6-04 时区注意同源）。

## T8-02：三步开始——讲清情绪反射弧 + 记录必要性 + 逻辑链条 + 一次练习（修订 T6-03）

> **覆盖声明**：本项**推翻** T6-03 早前"去除情绪反射弧术语"的【Claude订正】。按用户新要求，getting-started 页**显式讲解**情绪反射弧。以 T8-02 为准。

**页面四段**（`apps/miniprogram/pages/getting-started/`）
1. **什么是情绪反射弧**：一句通俗定义（"一件事发生后，情绪、想法、身体、行为会像反射一样接连出现——看清它，就能找到可调整的点"）。
2. **为什么先记录一次具体事件**：泛泛说情绪难改，落到一件具体的事上才看得见链条、找得到抓手。
3. **逻辑链条可视化**：横向步骤条/箭头链呈现，每节点一句话。**权威链条已核实填死（勿自造、勿改序、勿增减节点）**——来源：情绪反射弧框架 + 前端 `NODE_LABELS` 用词对齐。

   **诱因/应激源 → 反应（想法·身体感觉·行为）→ 觉察 → 接纳 → 转化 → 应对（适应性策略与行为）→ 结果（适应与发展）**

   | 节点 | 用户向一句话 |
   |---|---|
   | 诱因/应激源 | 一件让你有情绪的事发生了 |
   | 反应 | 紧接着冒出的想法、身体感觉和行为 |
   | 觉察 | 先停一下，看见自己正在反应 |
   | 接纳 | 允许这些感受存在，不急着对抗 |
   | 转化 | 换个角度理解，给自己一点余地 |
   | 应对 | 选一个此刻能做的小行动 |
   | 结果 | 回看这次经历，带走一点成长 |

   ⚠️ **用词对齐**：用 **觉察**（非"觉知"，与前端 `NODE_LABELS` 一致）。**必须区分两套概念，勿混用**：① 上面 7 节点是**用户教育用的"概念弧"**（getting-started 展示）；② 测一测里的 `reflex_node`（reaction / reflection / acceptance / awareness / resource / fusion / transformation / behavior / motivation / outcome / integrated_profile…）是**量表分类标签**，粒度更细、用途不同——**不要把 reflex_node 的 10+ 个值当作这条教育弧来渲染**。
4. **一次练习**：引导用户就"最近一件小事"沿链条走一遍（最简：选诱因→写当时反应→做一次"觉知"微练习），或跳记录页带入链条提示。

**边界**：保留"不下诊断结论"；练习是自我觉察、非治疗。
**文件**：getting-started index.{wxml,js,wxss}。**验收**：四段齐全、链条与框架一致、练习可完成。

## T8-03：训练中心分层改造（三块）

**目标结构**（`apps/miniprogram/pages/training/`）
- **第一档·通用**：现有训练卡/`trainingStages` 保留为"通用训练"档。
- **入口二·个性化定制方案（=个性化治疗入口）**：进入后**基于测一测结果**生成定制训练卡方案。复用已有 `evaluate_training_rules`（维度分→卡）+ 画像簇 `recommended_card_ids`（profiles）。
  - 后端新增 `GET /api/training-plan?user_id=`：取该用户最近若干测评结果 → 汇总/去重 recommended_card_ids（按维度/簇归类）→ 返回 `{plan_items[]{source_worksheet, dimension|cluster, card_ids, reason}}`；无测评则引导"先去测一测"。
  - 前端新增 `pages/personalized-plan`：展示"根据你的测评，为你定制"，分组列卡，点击进训练卡页。
- **入口三·项目测试**：列出 3 个循证项目（T8-04），点击进项目详情/分节。
  - 前端新增 `pages/program-list` + `pages/program-detail`（分节 + 书写）。

**shared**：`TrainingPlan`、`Program`/`ProgramSession` 类型；端点 `trainingPlan/programs`。
**文件**：training/index 改为三入口；新增 personalized-plan、program-list、program-detail；app.json 注册；api.js 加方法。
**验收**：三块入口可达；个性化方案随测评变化；无测评优雅引导。

## T8-04：三个循证书写/管理项目（框架 + 首节完整样例 + 其余大纲）

**内容模型**（`content/programs.json` + `content/schemas/programs.schema.json`，纳入 `validate_content.py`）：
```text
program{ id, title, target_constructs[], theory_source, audience,
  sessions[]{ session_no, title, objective, steps[], writing_prompt?, reflection_questions[], duration_minutes, disclaimer },
  boundary_notice, review_status }
```
**伦理**：每项目 `boundary_notice` + 每节 `disclaimer`（非诊断/非治疗承诺）；过 FORBIDDEN_TERMS。**首节给完整可用内容，其余节给大纲，整包标 `review_status:"pilot_draft"` 待专业审核后扩写。**

### 项目 A：自我关怀书写·考试焦虑（提升情绪调节 + 降低不确定性不耐受 IUS）
- 构念：自我关怀(SCS)、情绪调节、不确定性不耐受(IUS)；理论：自我关怀写作 + UP/CBT。
- 6 节大纲：①认识考试焦虑与不确定 ②自我关怀三要素书写 ③把"最坏假设"写成"多种可能" ④对不确定的接纳练习 ⑤考前自我对话脚本 ⑥回顾与迁移。
- **第 1 节完整样例**：目标=看见考试焦虑里"对不确定的不耐受"；步骤（写下最近一次考试焦虑的具体情境／标出最让你不安的"不确定点"／用一句自我关怀的话回应自己）；书写提示（"如果好朋友有同样的担心，你会怎么对他说？把这句话写给自己"）；反思（我最担心的不确定是什么？／这句关怀话让身体有什么变化？）；时长 10–15 分钟；disclaimer（本练习用于自我觉察，不构成诊断或治疗）。

### 项目 B：自我关怀·亲密关系建立中的自我成长
- 构念：自我关怀、关系自我、边界；理论：自我关怀 + 关系成长。
- 6 节大纲：①关系里的自我觉察 ②自我关怀 vs 自我批评 ③需求与边界表达书写 ④冲突后的自我修复 ⑤从依赖到相互支持 ⑥回顾与迁移。
- **第 1 节完整样例**：目标=在关系里先看见自己的感受与需求；步骤（写一段近期关系中的具体互动／标出当时自己的感受与未说出口的需求／用自我关怀的一句话肯定这份需求的合理）；书写提示、反思、时长 10–15 分钟、disclaimer（结构同 A，主题为亲密关系）。

### 项目 C：缓解学业压力·健康促进睡眠管理
- 构念：学业压力、健康促进生活方式(HPLP)、睡眠卫生；理论：压力管理 + 睡眠卫生（**非临床失眠治疗**）。
- 6 节大纲：①学业压力盘点 ②压力-睡眠关系觉察 ③睡眠卫生小步计划 ④睡前放松(呼吸/身体扫描) ⑤白天节律与任务拆解 ⑥回顾与迁移。
- **第 1 节完整样例**：目标=看清压力来源与睡眠现状；步骤（记录一周作息与压力事件／找出 1 个最影响睡眠的因素／定 1 个今晚可做的小改变）；书写提示、反思、时长 10–15 分钟、disclaimer（如长期严重失眠请就医）。

**后端**：`GET /api/programs`、`GET /api/programs/<id>`；书写留存先本地缓存（仿 3 天计划），如需入库另立 `program_entries`(P2)。
**验收**：3 项目过 `validate_content`；首节完整、其余大纲齐、边界文案齐。

## T8-05：情感计算 + 社会网络分析雏形（离线，不进后端运行时）

**约束**：沿 `analysis/profiling/` 聚类同款——离线脚本、脱敏聚合输出、原始/逐行不入仓、不进后端运行时；依赖入 `requirements-analysis.txt`。

- **情感计算雏形** `analysis/profiling/affective_computing_prototype.py`：读 `emotion_diaries` 自由文本（`event_description/automatic_thought/raw_text`）+ 温度计 `brief_text`（离线导出或只读）；做中文情绪/情感倾向分析（**优先轻量词典法，避免重 ML**）；输出**脱敏聚合**（个体情绪走势/效价随时间、群体分布）→ 可视化数据 JSON。**只出"情绪倾向"描述，不产诊断标签**。
- **社会网络分析雏形** `analysis/profiling/social_network_prototype.py`：以 `family_links`（bind_code/relation_label）建家庭关系图；算基础指标（度、连通分量、简单中心性）；输出脱敏图摘要 + 可视化数据。**注明 family_links 多为试点/稀疏，仅雏形**。
- **可视化**：先离线出图/JSON；如上 Web，ResearchDashboard 加两个"雏形"面板读离线产物 JSON（只读、标注雏形、非诊断、researcher/admin 鉴权）。
- 留痕 → `画像系统设计_Claude_20260628/`。**验收**：两脚本可复现、输出脱敏、不改后端运行时依赖。

## T8-06：跨层审查修改意见（service / schema / 契约 / 类型 / 错误码 / 权限脱敏 / 前端服务层）

**✅ 现状良好（已核实）**：MySQL 连接 `charset=utf8mb4` + `DictCursor` + `autocommit=False`（`database.py:150-158`）——中文/emoji 安全、显式事务；**SQL 无注入**（f-string 只拼内部表/列/索引标识符，值一律 `?` 占位；admin 导出 base_sql 内部构造 + `LIMIT ?`）；`{ok,data}`/`{ok,error}` 协议三端一致；导出脱敏 + `require_role` 已在。

**🔧 修改意见**

| # | 主题 | 问题 | 改法 | 优先 |
|---|---|---|---|---|
| 1 | **事务安全** | `autocommit=False` + 单连接复用；请求在 execute 后、commit 前抛异常且无 rollback，下个复用该连接的请求可能续到脏事务 | `get_connection`/`MySQLConnection.__exit__` 异常路径补 `rollback()`（或每请求独立连接/失效重连） | 高 |
| 2 | **连接健壮性** | `pymysql.connect` 无 `connect_timeout/read_timeout`、无池、无重连，长驻易 `MySQL server has gone away` | 加超时 + `ping(reconnect=True)` 或 per-request 连接 | 中 |
| 3 | **标识符插值护栏** | `ensure_column`/索引/导出的 f-string DDL 拼表列名 | 固化"只接内部白名单、绝不接用户输入"（断言+注释），防未来变注入面 | 中 |
| 4 | **错误码体系** | `fail(code,message)` 的 code 是散串（validation_error/missing_fields…），前端易按 message 判分支 | 收敛为集中错误码枚举（shared 常量），前端按 code 判；API 文档补"错误码表" | 中 |
| 5 | **契约/类型单一源** | 小程序端点表仍漂移（T7-06#2 未做） | T8 新类型/端点**先落 shared 再两端用**；顺带把小程序端点表对齐 shared | 中 |
| 6 | **权限脱敏** | T8-05 情感/SNA 产物、T8-04 书写自由文本 | 上 Web 前脱敏聚合 + researcher/admin 鉴权；书写导出走既有白名单、默认不导原文 | 高 |
| 7 | **文档同步** | T8 新增 `emotion_thermometer`(按日索引)、`programs`、可能的 `program_entries`、多个新端点 | 同步 `docs/03_技术真相/{数据库字段说明.md, API接口文档.md, 数据字典.md}` | 中 |

## T8-07：任务八验收
```text
后端：validate_content(含 programs+新schema) 通过；pytest 通过；healthz/deep 绿
温度计：一天多记录→今日曲线正确；按日接口 substr 双后端一致
三步开始：反射弧四段+练习；链条节点与框架一致
训练中心：三块入口可达；个性化方案随测评生成；项目测试可进
项目内容：3 项目首节完整+其余大纲+边界文案；过 FORBIDDEN_TERMS
情感/SNA：analysis 脚本可复现、脱敏、不进后端运行时
审查：事务 rollback + 连接超时/重连已加；错误码表已补；字段/API 文档同步
```

# 任务九：代码审查与修改计划（小程序原生 / 数据库 / Flask / 项目结构 / 日志排错）

> 创建时间：2026-07-02  
> 来源：用户提供的 31 项代码审查事项。  
> 执行原则：任务九先做审查和问题定位，再按风险分批最小修复。每个小任务都要输出：审查范围、发现问题、建议修复、涉及文件、验证命令。涉及代码、文档、配置或内容库改动时，必须同步 `docs/00_当前事实基准/{开发日志.md,当前进度交接.md,开发说明.md}`。涉及 API、字段或数据库时，还必须同步 API 文档、数据库字段说明和 shared 契约。

## T9-01：小程序页面、组件、配置和请求层分工审查

审查微信小程序原生开发中页面、组件、配置文件和请求层之间的职责分工。

重点检查：

```text
1. api 封装是否集中在服务层。
2. 本地后端和云托管后端差异是否通过配置处理。
3. 身份 token 是否由统一请求层注入。
4. api.js 是否承担稳定业务入口，而不是让页面拼接接口。
5. page 层是否只处理 data、路由参数、用户事件和页面状态。
```

交付物：小程序分层审查记录。

## T9-02：小程序失败态、空态和用户可见错误审查

审查小程序页面是否只写成功态，导致接口失败时页面空白，或只 `console.log` 错误不给用户提示。

重点检查：

```text
1. loading、empty、error、success 状态是否完整。
2. 接口失败时是否有用户能看懂的提示。
3. 是否存在只在控制台打印错误、页面无反馈的问题。
4. 是否存在错误后按钮不可恢复、页面无法重试的问题。
```

交付物：页面失败态和空态清单。

## T9-03：小程序 page / component / service 职责边界审查

审查 component 中是否混入请求数据、身份校验和复杂错误处理，确认这些逻辑留在页面或服务层。

重点检查：

```text
1. page 放页面状态、路由参数、调用服务层、用户提示。
2. page 不放重复展示结构。
3. component 放局部 UI、展示逻辑、轻量交互事件。
4. service 放接口地址、请求头、错误转换、云托管分支。
5. 是否有多个页面重复写相同展示结构或请求逻辑。
```

交付物：page/component/service 职责边界表。

## T9-04：小程序服务层和请求封装审查

审查服务层是否统一处理 `baseURL`、云托管调用、token 注入和错误转换。

重点检查：

```text
1. 页面中不得硬编码本地或云托管地址。
2. 是否用配置开关区分 mock、本地后端和云托管后端。
3. 测试环境 token 不得带到生产环境。
4. 请求头、身份信息和环境分支是否集中维护。
5. 失败响应是否统一转换。
```

交付物：请求封装审查清单。

## T9-05：后端错误到小程序页面错误结构转换审查

审查后端错误是否转换成页面能理解的稳定结构，而不是页面直接解析各种 `res.statusCode` 和原始报错。

重点检查：

```text
1. 前端是否拿到 message、code、retryable 等稳定字段。
2. 用户可见错误是否统一。
3. 是否避免暴露数据库连接失败、权限校验细节、堆栈等内部信息。
4. 页面是否按 code 做稳定动作。
```

交付物：API 错误转换表。

## T9-06：小程序上线后普通用户可打开页面联调审查

审查页面在上线后是否能被普通用户打开，并且不会依赖开发者临时状态。

重点检查：

```text
1. 普通用户入口是否可达。
2. 页面是否依赖调试页、测试 token 或开发者缓存。
3. 缺少登录态、缺少数据、接口失败时是否能正常提示。
4. 微信开发者工具和真机环境表现是否一致。
```

交付物：普通用户可打开页面清单。

## T9-07：小程序身份、token、401/403/404/500 处理审查

审查小程序端身份和 token 保存边界，以及各类 HTTP 错误对应动作。

重点检查：

```text
1. 小程序端可以保存登录态或临时 token。
2. 不得把服务端秘钥、数据库密码、管理员 token 放到前端代码或缓存。
3. token 失效时服务层统一处理 401，清理登录态、跳转登录或提示重新授权。
4. 不允许每个页面各写一套 token 失效逻辑。
5. 401、403、404、500 是否对应正确页面动作。
```

交付物：身份和错误状态处理审查表。

## T9-08：小程序用户提示语义审查

审查用户提示是否能区分不同错误类型，并给出合适动作。

重点检查：

```text
1. 可自行处理的问题是否给出补充引导。
2. 需要稍后再试的问题是否提示重试。
3. 参数缺失是否提示用户补充信息。
4. 权限不足是否停止操作。
5. 网络失败是否提示检查网络或重试。
```

交付物：用户提示语义表。

## T9-09：小程序 api.js 业务入口命名与封装审查

审查 `api.js` 是否承担环境选择、路径拼接、身份注入、响应处理和错误转换。

重点检查：

```text
1. api.js 是否暴露稳定业务方法，而不是暴露页面自己拼接的请求。
2. 页面代码是否接近业务语言。
3. 入口函数命名是否稳定。
4. 页面调用的业务方法语义是否稳定。
5. 是否存在多个页面重复拼接同一接口的问题。
```

交付物：api.js 入口函数审查表。

## T9-10：小程序请求分支和环境定位审查

审查请求分支是否能清楚回答当前环境是什么、目标服务在哪、失败时如何定位。

重点检查：

```text
1. 当前运行环境是否可见或可诊断。
2. mock、本地后端、云托管后端分支是否清楚。
3. 失败日志是否能定位目标服务、接口路径和请求方式。
4. 是否有隐藏的默认环境导致联调混乱。
```

交付物：环境分支定位记录。

## T9-11：小程序响应处理统一性审查

审查响应处理是否把后端结构转换成页面可消费的数据。

重点检查：

```text
1. 成功时统一返回 data。
2. 失败时统一抛出 error。
3. 页面是否避免直接处理后端原始外形。
4. 数据缺省值和空数组是否由服务层或页面稳定处理。
```

交付物：响应处理一致性清单。

## T9-12：CloudBase 云托管调用链审查

审查小程序云托管调用链是否和后端接口一致。

重点检查：

```text
1. wx.cloud.init 的环境 ID 是否正确。
2. callContainer 的 path、method、header 是否与后端接口一致。
3. 云托管服务是否有健康检查接口。
4. 健康检查是否返回稳定 JSON。
5. 本地和云端调用差异是否集中配置。
```

交付物：CloudBase 调用链审查表。

## T9-13：数据库持久化边界和数据归属审查

审查需要保留的数据是否进入数据库，字段是否一致并支持查询。

重点检查：

```text
1. 需要长期保留的数据是否写入数据库。
2. 字段是否和 API、shared、文档一致。
3. 查询是否支持业务需要。
4. SQL 是否按路由层、服务层、数据库适配层拆分。
5. SQLite 与 MySQL 边界是否清楚。
```

交付物：数据库持久化边界表。

## T9-14：数据库字段稳定性和字段说明审查

审查数据库字段名是否稳定、含义单一，并在字段说明文档记录。

重点检查：

```text
1. 是否存在重复字段或含义重叠字段。
2. 前端、测试和数据库字段是否一致。
3. 表是否按实体拆分。
4. 每行是否保留主键，方便更新、追踪和关联。
5. 字段名是否可解释。
6. 字段说明文档是否记录含义。
```

交付物：字段检查表。

## T9-15：数据库主键、外键和关联关系审查

审查主键、外键和服务逻辑中的关联关系是否清楚。

重点检查：

```text
1. 每张表是否有稳定主键。
2. 需要关联的表是否有外键或服务层明确约束。
3. 字段命名是否能表达关联关系。
4. 服务逻辑是否避免误把不同用户或不同实体的数据关联在一起。
```

交付物：主外键和关联关系审查表。

## T9-16：数据库事务安全审查

审查事务能否保证一组操作全部成功或全部失败。

重点检查：

```text
1. 一次请求同时写入多张表时是否使用事务。
2. 失败时是否 rollback。
3. 是否存在半完成数据。
4. 测试是否覆盖写入失败场景。
```

交付物：事务安全审查记录。

## T9-17：SQLite 连接生命周期和参数化查询审查

审查 SQLite 是否使用上下文管理器，连接生命周期是否和一次操作绑定。

重点检查：

```text
1. 是否避免多个函数共享同一个全局连接。
2. 是否使用参数化查询。
3. 不得出现 f"select * from feedback where user_id = '{user_id}'" 这类拼接 SQL。
4. SQL 结构和值是否分离。
5. 异常时连接是否正确关闭。
```

交付物：SQLite 连接和 SQL 安全审查表。

## T9-18：schema 初始化脚本幂等性审查

审查 schema 初始化脚本是否可重复运行，并写清楚字段、默认值和必要索引。

重点检查：

```text
1. 初始化脚本是否幂等。
2. 每张表字段是否完整。
3. 默认值是否明确。
4. 必要索引是否存在。
5. 初始化失败时是否有清楚错误日志。
```

交付物：schema 初始化审查记录。

## T9-19：MySQL、编码、健康检查和备份策略审查

审查 MySQL 连接、字符集、云端部署前数据库可用性和备份策略。

重点检查：

```text
1. MySQL 是否能连接成功。
2. 字符集是否使用 utf8mb4。
3. 同时检查数据库字符集、表字符集、连接 charset 和前后端 JSON 编码。
4. 是否存在乱码、插入失败、emoji 报错、排序异常。
5. 云端部署前后端是否能连上数据库。
6. schema 是否已初始化。
7. 健康检查是否能区分服务可用和数据库可用。
8. 是否有备份策略、恢复演练和保存周期。
9. database 是否有连接函数、初始化 schema 函数。
10. 查询函数是否全部使用参数化写法。
11. 是否有统一异常处理和日志。
12. 需要输出索引表，即字段检查表。
```

交付物：MySQL/编码/备份/字段索引综合审查表。

## T9-20：审计日志、迁移留痕和端到端编码验证审查

审查是否有审计日志、迁移留痕，以及中文、英文、数字、标点和 emoji 的端到端编码验证。

重点检查：

```text
1. 是否记录必要摘要。
2. 后续迁移是否能记录变更原因、执行 SQL、影响表、验证方式和回滚策略。
3. 写一条同时包含中文、英文、数字、标点和 emoji 的记录。
4. 从接口写入数据库，再从数据库读回页面。
5. 验证写入、读出、接口返回、页面展示四步。
6. 能否定位编码问题出现在哪一层。
```

交付物：审计日志和端到端编码验证记录。

## T9-21：Flask 路由拆分、响应结构和中文 JSON 审查

审查 Flask 后端是否按业务域拆分路由，并形成稳定请求响应链路。

重点检查：

```text
1. 是否避免一个 app.py 承担所有职责。
2. 请求解析、业务调用、错误响应、跨域联调和测试验证是否稳定。
3. 成功响应、校验失败、权限失败和服务器错误是否有稳定外形。
4. JSON 对中文是否有 provider 控制序列化行为。
5. 接口调试和日志中中文是否可读。
6. 是否仍使用 utf8 和标准 JSON。
```

交付物：Flask 路由和响应结构审查表。

## T9-22：Flask 应用工厂和测试配置审查

审查 Flask 应用是否可配置、可测试、可拆分。

重点检查：

```text
1. 是否有 create_app。
2. 配置是否隔离开发、测试和生产。
3. create_app 是否允许传入 URL 或临时配置。
4. 接口测试是否能使用临时配置。
5. 测试是否避免依赖真实生产配置。
```

交付物：Flask 应用工厂审查记录。

## T9-23：Blueprint、service、database 分层审查

审查 blueprint、route、service、database 是否分别放置对应职责。

重点检查：

```text
1. route 放 URL、method、请求参数和响应结构。
2. service 放业务规则、数据组装和权限判断。
3. database 放连接、SQL、事务、索引相关查询。
4. 开发、测试和生产配置是否隔离。
5. 是否有跨层调用导致测试困难。
```

交付物：后端分层审查表。

## T9-24：CORS、healthz/readyz 和错误码稳定性审查

审查前端是否能调用后端，CORS、健康检查和错误码是否稳定。

重点检查：

```text
1. CORS 是否允许正确来源访问。
2. 是否存在长期允许所有来源加携带凭证的问题。
3. healthz 是否安全、稳定。
4. 是否拆分基础 healthz 和 readyz。
5. 不要把所有检查都堆进一个接口。
6. 错误响应是否使用稳定 code。
```

交付物：CORS 和健康检查审查表。

## T9-25：后端入口装配轻量化审查

审查入口装配分层是否混乱。

重点检查：

```text
1. 入口文件是否保持轻量。
2. 入口是否只负责装配，而不是承载所有业务。
3. 是否同时出现大量 SQL、复杂业务判断和页面文案。
4. 业务逻辑是否已下沉到 service。
5. 数据访问是否已下沉到 database。
```

交付物：后端入口轻量化审查记录。

## T9-26：argparse 脚本 main 函数边界审查

审查命令行脚本是否把 argparse 和业务函数边界分开。

重点检查：

```text
1. main 函数是否只处理命令行边界。
2. 测试是否可以直接测业务函数。
3. 测试是否可以单独测参数解析。
4. 脚本失败时是否返回清楚退出码和错误提示。
```

交付物：脚本 main 函数边界审查表。

## T9-27：项目结构、依赖方向和内容库组织审查

审查当前项目结构是否能减少混乱、降低协作成本，并让测试和部署有稳定入口。

重点检查：

```text
1. 当前分层是否清楚。
2. 入口、路由、服务、模型之间关系是否稳定。
3. 依赖方向是否清楚。
4. 当前脚本命名是否规范。
5. 内容库命名是否清晰、字段稳定、格式可校验。
6. 内容库是否有写死在路由里的问题。
7. 虚拟环境和本地运行产物是否避免进入仓库。
```

交付物：项目结构审查报告。

## T9-28：requirements 和依赖文件审查

审查依赖文件和运行命令是否对应。

重点检查：

```text
1. requirements 是否明确。
2. 后端依赖和分析依赖是否区分。
3. 前端依赖是否和 package 文件对应。
4. 文档中的安装命令是否可执行。
5. 是否有未记录但运行时必需的依赖。
```

交付物：依赖审查清单。

## T9-29：环境变量和敏感配置审查

审查 `.env`、配置文件、前端代码、文档和脚本中是否暴露敏感配置。

重点检查：

```text
1. 数据库密码、云服务秘钥、token、内部管理账号登录信息不得进入前端或仓库。
2. 生产环境不得使用默认 token 或弱 secret。
3. Web、小程序和后端对环境变量的读取路径是否清楚。
4. 示例配置是否脱敏。
5. 日志和错误提示是否避免打印密钥。
```

交付物：敏感配置扫描记录和整改建议。

## T9-30：logging 日志体系审查

审查项目是否有统一、可过滤、可定位的日志体系。

重点检查：

```text
1. 是否使用 logging 模块。
2. 同一条事件是否能输出到控制台、文件或平台日志，并按级别过滤。
3. 后端请求、数据库连接、脚本批处理和容器启动是否可追踪。
4. 日志是否描述事件，而不只是“这里执行了什么”。
5. 是否用 DEBUG、INFO、WARNING、ERROR 表达严重程度。
6. 是否有结构化上下文。
7. logger、level、handler、formatter 是否清楚。
8. 是否有随意创建不同名字 logger 的问题。
9. basicConfig 是否只在程序入口调用一次。
10. handler 输出位置是否清楚。
```

交付物：日志体系审查报告。

## T9-31：异常追踪、错误码和用户可见错误审查

审查异常与追踪信息是否能帮助协作者定位问题，同时避免向用户暴露内部细节。

重点检查：

```text
1. exception 日志是否保留堆栈信息。
2. 协作者是否能先看异常类型，再看项目代码行号，再回到函数输入条件。
3. 错误码是否成为日志、接口响应和测试之间的桥梁。
4. 用户看到提示，前端拿到 code，后端日志记录 code 加上下文。
5. 错误码是否使用稳定的大写枚举。
6. 用户可见错误是否简短可理解，不过度暴露内部细节。
7. 测试是否覆盖关键错误码和错误外形。
```

交付物：错误码和异常追踪审查表。

---

# 任务十：小程序登录闭环、测评体验、训练反馈、阶段性画像与文本分析能力补强（修订版，下一轮执行要求）

适用仓库：

```text
D:\codex\workspace\safehome1.0
```

相关图片位置：

```text
D:\codex\workspace\safehome1.0其他内容\文档图片\改错用图第一
```

请先查看该图片文件夹内所有图片。图片和任务的对应关系需要你根据截图内容自行判断，不要要求我逐张解释。若某张图片无法打开或无法判断，请在报告中单独列出“无法判断的图片”。

---

## 0. Context（为什么做）

SafeHome 当前已经完成了家长端主闭环、小程序测一测、训练卡、情绪温度计、个性化训练方案、项目测试、周报、画像落点和 CloudBase 部署等大量基础功能。但当前小程序仍存在若干体验、内容、登录、记录追踪和后续研究分析方面的问题。

本轮任务是 **任务十**，目标不是重构整个项目，而是在现有 SafeHome 技术架构上补强以下能力：

1. 统一登录入口与登录后使用规则；
2. 优化测一测指导语、结果页、题项选项和上线审核；
3. 补充“我的”页面中的设置、说明、隐私与边界内容；
4. 补充个性化训练方案、项目测试和训练卡文本填写位置；
5. 检查课程界面是否真实接入；
6. 设计微信授权登录和手机号授权登录；在真实配置具备时接入，缺少配置或授权权限时只完成接口骨架、配置检查、文档和前端入口，不伪造授权成功；
7. 让最近记录和本周复盘纳入测一测结果；
8. 优化情绪温度计为轻量多维情绪记录与温度计式交互；
9. 实现阶段性反馈、画像逐步收束、训练卡效用评价和动态训练推荐；
10. 设计情感计算和社会网络分析功能，为后续文本分析做准备。

本轮任务必须遵守 SafeHome 的项目边界：系统是非诊断、非治疗、非危机干预系统。所有结果只用于自我观察、支持性反馈、练习建议、研究分析和人工复核线索，不得写成临床诊断、人格判断或治疗效果。

---

## 0A. 用户确认后的修订口径（优先于下文细则）

1. 本任务十要求下一轮一次性连续执行完 T10-01 至 T10-16，不拆成多轮等待确认；除明确需要用户提供微信配置、人工验收、真机截图或外部平台权限的事项外，执行者需要自动判断、自动修复、自动验证并完整留痕。
2. T10-01 与 T10-02 合并执行：登录页、我的页面、全局登录守卫、登录用户身份绑定和后端私有数据权限视为同一个闭环，不重复开发。后端不得信任前端随意传入的 `user_id` 查询私有数据；用户私有数据应优先从 `Authorization: Bearer token` 解析当前用户，管理员或督导场景必须有独立权限校验。
3. T10-07 微信授权登录和手机号授权登录按“配置具备则接入，配置缺失则完成骨架和文档”的口径执行：不硬编码 AppID/AppSecret，不伪造授权成功，不把账号密码登录删除；账号密码登录作为调试/备用入口保留。
4. T10-13 统一称为“轻量多维情绪结构”：强度是温度计主字段，效价、唤醒度、可控感是补充维度。若正文出现“三维/四维”表述，以本条为准。
5. T10-12 必须把真机截图中出现的量表选项挤压、重叠、截断、不可读问题纳入验收。Likert 题、单选题、长选项题需要分别保证移动端可读、可点、不会把数字和文字压成竖条。
6. T10-16 中 `docs/10Claude协作/Claude使用记录.md` 只在本轮实际使用 Claude 或 Claude Code 时更新；如果只使用 Codex，不更新该文档，并在最终报告中说明原因。
7. 用户明确要求：不要新增云端与本地一致性核对专项，不新增 P0/P1/P2 优先级拆分，不降低 T10-14 和 T10-15 的执行范围。
8. 阶段性反馈必须放在小程序首页“最近记录”下面，作为单独板块展示；页面设计沿用当前小程序方案，不另起一套视觉风格。

## 0B. 代码级执行明细（下一轮优先按此落地）

本节基于当前仓库代码状态补充，目的是让下一轮执行者知道“具体改哪些文件、补哪些字段、加哪些内容”。若本节与后续 T10-01 至 T10-16 的泛化描述冲突，以本节为准。

### T10-01 / T10-02 登录闭环与用户身份规则

当前代码事实：

```text
backend/routes/auth.py 已有 /api/auth/register、/api/auth/login、/api/auth/wechat-login、/api/auth/me。
backend/routes/auth_utils.py 已有 require_login、require_role、get_current_actor。
backend/routes/utils.py 仍有 require_user_id、resolve_user_id_for_query，并会在 development 下回退 demo-parent。
apps/miniprogram/services/api.js 会从 auth_user 取 user_id，但缺少登录时仍会回退 anonymous id。
apps/miniprogram/pages/profile/index.js 目前只显示“试点体验模式/已登录”，还没有完整登录卡、退出入口和登录/注册入口。
```

必须改动：

```text
1. backend/routes/auth_utils.py
   - 新增 resolve_actor_user_id(requested_user_id=None, payload=None, allow_legacy_admin=False, allow_dev_fallback=False)。
   - 非 admin/supervisor/researcher 只能返回 token 中的 actor["id"]。
   - admin/supervisor/researcher 可按权限读取 requested_user_id。
   - 未登录时返回 AuthError，不再静默使用前端 user_id。

2. backend/routes/assessments.py
   - create_assessment_result、list_assessment_results、get_assessment_profile_position 改为使用 token 解析用户。
   - GET /api/assessments 可保持公开读取题库，但提交和结果查询必须登录。

3. backend/routes/messages.py
   - 保留当前按 require_login 查询用户消息的方向。
   - 确认 GET/POST read 不允许普通用户通过 query user_id 读取别人消息。

4. backend/routes/training_plan.py、reports.py、emotion_thermometer.py、programs.py、checkins/diaries/supervision 相关路由
   - 所有保存记录和私有查询统一改为 token 解析 user_id。
   - 仅保留 development/debug 页面必要的临时兼容，并在执行记录中说明。

5. apps/miniprogram/utils/authGuard.js（新增）
   - getAuthUser()
   - getAuthToken()
   - isLoggedIn()
   - requireLogin({ redirectUrl, message })
   - logout()

6. apps/miniprogram/app.js
   - onLaunch 同步 auth_token/auth_user 到 globalData。
   - 暴露 setAuthSession、clearAuthSession。

7. apps/miniprogram/services/api.js
   - 增加 isAuthRequiredEndpoint 或 request options.requiresAuth。
   - 需要保存/查询用户私有数据的接口无 token 时直接抛 auth_required，不再默认 anonymous user_id。
   - 保留 listAssessments、getAssessment、healthz、readyz 等公开读取接口。

8. apps/miniprogram/pages/profile/index.{js,wxml,wxss}
   - 顶部新增登录状态卡：
     已登录：昵称、角色、账号状态、退出登录。
     未登录：登录、注册、微信授权登录入口。
   - openEntry 对周报、消息、训练记录、测评记录、人工督导等私有入口调用 requireLogin。

9. 需要加登录守卫的页面
   - pages/diary-form/index.js
   - pages/thermometer/index.js
   - pages/assessment-detail/index.js 的 submitWorksheet
   - pages/checkin/index.js 的 submitCheckin
   - pages/personalized-plan/index.js
   - pages/program-detail/index.js 的正式提交
   - pages/messages/index.js、pages/message-detail/index.js
   - pages/weekly-report/index.js
   - pages/supervision/index.js
```

必须加入的文案：

```text
请先登录，这样系统才能保存你的记录并生成后续复盘。
登录后，你的记录只会用于本工具内的复盘、训练建议和必要的人工补充反馈。
```

必须新增或更新测试：

```text
backend/tests/test_auth_route.py
backend/tests/test_sensitive_owner_auth.py
backend/tests/test_assessments_route.py
新增或补充：未登录提交测评/温度计/周报查询返回 401；普通用户不能通过 user_id 查询他人记录；admin/supervisor 权限路径仍可用。
```

### T10-03 量表指导语细化

当前代码事实：

```text
content/assessment_worksheets.json 是小程序题库主数据源。
backend/routes/assessments.py 的 _summarize_worksheet 和 get_assessment 已透传 instructions、boundary_notice、result_disclaimer。
apps/miniprogram/pages/assessment-detail/index.wxml 已展示 worksheet.instructions。
```

必须改动：

```text
1. content/assessment_worksheets.json
   - 为所有 enabled_for_user=true 的量表补 instructions。
   - 不改题项 prompt、options、dimension、reverse_scored、score。
   - 敏感量表必须同时保留 boundary_notice、result_disclaimer。

2. content/scales_catalog.json
   - 同步记录指导语状态字段，如 instruction_status 或 review_note。

3. docs/02_专项进度与验收/P3量表录入进度表.md
   - 增加“指导语是否已按量表类型区分”记录。
```

每类必须加入的指导语内容：

```text
家长反思功能类：按最近与孩子互动时的真实感受作答，不追求标准答案。
情绪调节/情绪弹性类：按最近一段时间的通常反应作答。
自我关怀类：按自己遇到压力或挫折时的习惯反应作答。
学业压力/学习类：按最近学习、考试、作业相关状态作答。
心理健康筛查类：结果仅作自我观察，不用于诊断、筛查结论或治疗建议。
人格/特质类：不生成固定人格标签，只作为了解自己反应倾向的线索。
睡眠/健康生活方式类：只用于习惯观察，不替代医疗判断。
亲子沟通/家庭关系类：聚焦具体互动，不评判家庭好坏。
```

### T10-04 我的页面设置、知情、隐私与边界

必须改动：

```text
1. apps/miniprogram/pages/profile/index.js
   - settingsEntries 中“知情与边界”“隐私说明”从空 url 改为真实页面。

2. apps/miniprogram/pages/settings-detail/index.{js,wxml,wxss,json}（建议新增）
   - 支持 type=consent / privacy / boundary / about。
   - 从本地静态内容或 content 转换后的轻量 JSON 读取说明。

3. apps/miniprogram/app.json
   - 注册 settings-detail 页面。

4. content/consent.md、content/privacy.md
   - 如已有内容可复用，不另造冲突版本。
   - 如小程序不能直接读 md，则新增 content/miniprogram_notices.json 或在页面中放精简版常量，并注明来源。
```

必须加入的用户端内容：

```text
本工具不做诊断、不做治疗、不处理紧急危机。
记录会用于你的复盘、训练建议和必要的人工补充反馈。
高风险内容可能进入人工关注，但紧急情况仍应优先联系现实中的可靠人员或当地紧急资源。
研究分析默认使用脱敏或聚合数据，不默认展示自由文本原文。
```

### T10-05 个性化训练方案、项目测试、训练卡文本填写

当前代码事实：

```text
backend/routes/training_plan.py 已能从 assessment_results 和 profile cluster 生成 plan items。
content/programs.json 已作为项目测试内容源。
apps/miniprogram/pages/program-detail/index.js 目前主要用本地 draft 保存文本。
apps/miniprogram/pages/checkin/index.js 已有 reflection、emotion_before、emotion_after。
```

必须改动：

```text
1. backend/routes/training_plan.py
   - _assessment_plan_items 和 _cluster_plan_item 输出字段补全：
     source_worksheet_id、source_worksheet_title、source_dimension、source_profile_name、recommendation_reason、next_step、boundary_notice、evidence_summary。
   - get_training_plan 响应增加 has_recent_checkin、last_completed_card_ids、empty_state。

2. content/assessment_training_map.json
   - 为 15 个当前开放量表补推荐规则或确认无推荐规则原因。
   - 每条规则包含 trigger_condition、recommended_card_ids、reason、boundary_notice。

3. content/training_cards.json
   - 每张卡补可填写提示字段：
     pre_practice_prompt、emotion_word_prompt、new_response_prompt、post_practice_prompt、one_sentence_note_prompt。
   - 不改变训练卡核心步骤含义。

4. backend/routes/programs.py
   - 新增 POST /api/programs/<program_id>/entries。
   - 将项目测试填写文本保存到 records 表：
     module_type='program_entry'，source_id=program_id，data_json 包含 session_no、answers、reflection、analysis_consent、boundary_notice。

5. apps/miniprogram/services/api.js
   - 新增 createProgramEntry(programId, data)。

6. apps/miniprogram/pages/program-detail/index.{js,wxml,wxss}
   - 从“仅本地草稿”升级为“保存草稿 + 登录后正式提交”。
   - 增加书写提示、反思问题、提交说明、非诊断边界。

7. apps/miniprogram/pages/training-card/index.{js,wxml,wxss}
   - 展示训练卡文本填写区入口或跳转 checkin 时携带 card_id/card_title。

8. apps/miniprogram/pages/checkin/index.{js,wxml,wxss}
   - 在现有 reflection 基础上增加主观帮助评价 helpfulness_rating：有帮助 / 一般 / 暂时没有帮助。
   - 增加 skip_reason 或 pause_reason（如果用户暂不完成）。
```

如需数据库字段：

```text
优先复用 records.data_json 存项目测试文本。
checkins 如需长期统计训练卡效用，可最小新增：
helpfulness_rating TEXT
skip_reason TEXT
source_recommendation_id TEXT
before_thermometer_id TEXT
after_thermometer_id TEXT
```

### T10-06 课程界面接入

当前代码事实：

```text
apps/miniprogram/pages/course/index.js 是静态课程入口。
backend/routes/programs.py 管的是项目测试，不等同课程。
```

必须改动：

```text
1. 如果只做最小修复：
   - apps/miniprogram/pages/course/index.{js,wxml}
   - 将“课程详情后续接入”改为自然文案。

2. 如果正式接入课程：
   - 新增 content/courses.json。
   - 新增 backend/routes/courses.py：GET /api/courses、GET /api/courses/<id>。
   - shared/constants/api.ts 和 apps/miniprogram/services/api.js 增 courses 端点。
   - 新增 apps/miniprogram/pages/course-detail/index.*。
   - 如要记录学习进度，优先写 records 表，module_type='course_progress'。
```

课程内容第一版只需加入：

```text
课程标题、主题、适用场景、预计时长、内容小节、与训练卡或项目测试的关系、边界说明。
```

### T10-07 微信授权登录和手机号授权登录

当前代码事实：

```text
backend/routes/auth.py 已有 /api/auth/wechat-login。
_wechat_session_from_code 在非 production 且缺少配置时会 dev_fallback。
users 表已有 wechat_openid、phone_or_email、avatar_url 等字段。
apps/miniprogram/services/api.js 已有 wechatLogin(data)。
```

必须改动：

```text
1. backend/routes/auth.py
   - 保留 /api/auth/wechat-login。
   - 返回 dev_fallback 时，前端只能提示“开发调试登录”，不能把它当正式微信授权。
   - 新增 /api/auth/wechat-phone 或 /api/auth/bind-phone。
   - 手机号接口缺少 WECHAT_APPID/WECHAT_SECRET 或微信授权能力时返回明确错误 code：wechat_phone_config_missing，不伪造手机号。

2. backend/database.py / models.py
   - 确认 users.phone_or_email 已有并可复用；如要区分手机号来源，可新增 phone_verified_at TEXT、phone_source TEXT。

3. apps/miniprogram/pages/login/index.{js,wxml,wxss}
   - 增加“微信授权登录”按钮，调用 wx.login 后 api.wechatLogin。
   - 增加“手机号授权/绑定”按钮，使用 getPhoneNumber 事件拿 code，再调用后端。
   - 明确账号密码登录是调试/备用方式。

4. apps/miniprogram/services/api.js
   - 新增 bindWechatPhone(data)。

5. docs/04_部署联调/**
   - 记录需要在微信公众平台/CloudBase 配置的项：
     WECHAT_APPID、WECHAT_SECRET、手机号授权权限、隐私协议声明、服务器域名/云托管访问。
```

### T10-08 最近记录纳入测一测

必须改动：

```text
1. backend/routes/assessments.py
   - list_assessment_results 继续返回最近测评结果，但要使用登录态用户。
   - 可增加 query 参数 include_summary=true，用于返回 worksheet_title、created_at、total_score、scores.dimensions 简要信息。

2. apps/miniprogram/pages/assessment/index.{js,wxml,wxss}
   - 当前已调用 api.listAssessmentResults({ limit: 3 })，需要确认未登录时显示登录提示。
   - 增加最近测一测记录区域：量表名、填写时间、是否有画像、查看结果。

3. apps/miniprogram/pages/profile/index.{js,wxml}
   - “测评记录”入口进入 assessment 页或新增 history 参数。
```

### T10-09 测一测结果页、图表和后端技术字段清理

当前代码事实：

```text
apps/miniprogram/pages/assessment-result/index.js 已有 profilePlotCanvas、profileRadarCanvas 绘制逻辑。
后端 assessment_results 返回 profile_model_id、profile_cluster_id、profile_pc1、profile_pc2、profile_confidence 等技术字段。
```

必须改动：

```text
1. apps/miniprogram/pages/assessment-result/index.{js,wxml,wxss}
   - 不显示 profile_model_id、cluster_id、z_score、feature_id、debug 字段。
   - 用户端只显示：更接近的画像名称、置信度说明、PCA 位置图、雷达图、推荐训练、非诊断说明。
   - 低置信度、离群、数据不足时显示“本次结果只作为位置参考，暂不做明确画像解释”。

2. backend/routes/assessments.py
   - profile-position 接口可以保留技术字段给前端绘图，但前端不得原样展示。
   - 如需新增 display_payload，可在后端生成面向用户的解释字段。

3. shared/types/api.ts
   - 增加 user-facing 字段类型，如 reliability_status、display_summary、boundary_notice。
```

### T10-10 训练卡文案去模板化并补文本区

必须改动：

```text
1. content/training_cards.json
   - 去掉重复模板句。
   - 每张训练卡补：
     suitable_scene、today_goal、steps、example_phrase、before_note_prompt、after_note_prompt、boundary_notice。

2. apps/miniprogram/pages/training-card/index.{js,wxml,wxss}
   - 展示适用情境、预计用时、今天小目标、步骤、示例话术。
   - 不在卡片里写诊断或人格判断。

3. apps/miniprogram/pages/checkin/index.{js,wxml,wxss}
   - 承接训练卡文本填写。
   - 提交后写入 checkins.reflection 和新增的 helpfulness_rating/skip_reason。
```

### T10-11 本周复盘纳入测一测结果

当前代码事实：

```text
backend/services/report_service.py 当前读取 emotion_diaries、checkins、feedback_results、student_profiles。
尚未读取 assessment_results 和 emotion_thermometer。
backend/routes/reports.py 会把 weekly report 写入 weekly_reports 表，但表字段目前没有 assessment_summary_json。
```

必须改动：

```text
1. backend/services/report_service.py
   - 查询 assessment_results：
     SELECT * FROM assessment_results WHERE user_id=? AND substr(created_at,1,10) BETWEEN ? AND ?
   - 查询 emotion_thermometer。
   - 生成 assessment_summary：
     count、worksheet_names、dimension_summaries、profile_position_count、requires_review_count、recommended_card_ids。
   - 生成 thermometer_summary：
     count、avg_intensity、avg_valence、avg_arousal、avg_control（新增字段后）。
   - next_week_suggestion 综合 diaries、assessment_results、checkins、profiles、thermometer。

2. backend/routes/reports.py
   - 响应中返回 assessment_summary、thermometer_summary、training_effectiveness_summary。
   - 如需持久化，weekly_reports 表新增 assessment_summary_json、thermometer_summary_json、training_effectiveness_json。

3. shared/types/api.ts
   - WeeklyReport 增 assessment_summary、thermometer_summary、training_effectiveness_summary。

4. apps/miniprogram/pages/weekly-report/index.{js,wxml,wxss}
   - 展示本周完成测一测数量、量表名、维度变化摘要、推荐训练。
   - 没有测评时显示友好空态。
```

### T10-12 量表题项、选项和上线前人工审核

当前代码事实：

```text
apps/miniprogram/pages/assessment-detail/index.wxml 当前 scale 题用 option-row + option-button。
apps/miniprogram/pages/assessment-detail/index.wxss 当前本地版本已是纵向按钮布局。
用户真机截图仍出现选项挤压，下一轮必须确认真机加载的是最新代码或云端包。
```

必须改动：

```text
1. apps/miniprogram/pages/assessment-detail/index.{wxml,wxss}
   - 保证 option-button min-height、white-space、overflow-wrap、line-height 在真机窄屏有效。
   - 对 5/7 点 Likert 题使用纵向完整文字按钮；不要用挤压横排。
   - 对短数字量表如 1-7，可增加 compact 模式，但必须保留清楚标签。

2. backend/scripts/validate_content.py 或新增 scripts/audit_assessment_content.py
   - 输出每个 enabled worksheet 的题项数、选项数、空选项、长选项、敏感边界、计分状态。

3. docs/02_专项进度与验收/任务十量表上线前人工审核清单.md
   - 生成表格字段：
     worksheet_id、量表名称、enabled_for_user、题项状态、选项状态、计分规则状态、反向题状态、维度状态、是否建议隐藏、人工审核内容、原因。
```

### T10-13 情绪温度计轻量多维结构

必须改动：

```text
1. backend/models.py
   - emotion_thermometer 表保留 intensity_level。
   - 新增字段：
     valence_level INTEGER
     arousal_level INTEGER
     control_level INTEGER
     emotion_label TEXT

2. backend/database.py
   - ensure_schema_columns 对 emotion_thermometer 幂等补列。
   - CURRENT_SCHEMA_NAME 升级。

3. backend/routes/emotion_thermometer.py
   - _normalize_level 复用到 valence/arousal/control。
   - POST 接收 intensity_level、valence_level、arousal_level、control_level、emotion_label、brief_text。
   - GET /day 返回这些字段和多维 summary。

4. shared/types/api.ts
   - EmotionThermometerRecord / EmotionThermometerInput 增上述字段。

5. apps/miniprogram/pages/thermometer/index.{js,wxml,wxss}
   - 强度用温度计式视觉。
   - 效价、唤醒度、可控感用滑杆或分段按钮。
   - 当天摘要展示多维变化。
   - 边界文案保持非诊断。
```

### T10-14 阶段性反馈、画像收束、训练卡效用评价

必须改动：

```text
1. backend/services/progress_summary_service.py（新增）
   - build_progress_summary(user_id, range_days)
   - build_profile_convergence(user_id, worksheet_id=None)
   - build_training_effectiveness(user_id, range_days)

2. backend/routes/progress_summary.py（新增）
   - GET /api/progress-summary?range=7d|14d|30d
   - GET /api/profile-trend?worksheet_id=
   - GET /api/training-effectiveness
   - 全部使用 require_login/resolve_actor_user_id。

3. backend/models.py / database.py
   - 如果 T10-10/T10-14 需要，给 checkins 补：
     helpfulness_rating、skip_reason、source_recommendation_id、before_thermometer_id、after_thermometer_id。

4. backend/services/training_recommendation_service.py
   - 推荐逻辑增加训练完成率、主观反馈、跳过原因、风险状态。
   - 高风险时不输出普通训练推荐。

5. shared/constants/api.ts、shared/types/api.ts、apps/miniprogram/services/api.js
   - 新增 progressSummary、profileTrend、trainingEffectiveness 端点和类型。

6. apps/miniprogram/pages/home/index.{js,wxml,wxss}
   - 阶段性反馈主展示位置放在首页“最近记录”板块下面，作为独立 safe-section。
   - index.js 增加 progressSummary、progressSummaryLoading、progressSummaryError、progressSummaryEmpty 等状态。
   - refreshHomeData 追加 api.getProgressSummary({ range: "7d" }).catch(() => null)，不要影响首页原有最近记录加载。
   - index.wxml 在“最近记录” section 后、dev-entry 前插入“阶段性反馈” section。
   - index.wxss 沿用当前首页设计语言：section-title、safe-card、recent-record-card/quick-list 的卡片结构、var(--safe-primary)、var(--safe-card)、var(--safe-border)、var(--safe-shadow-card)，不新增插图、不做营销式大卡。
   - 板块内容只展示用户可理解字段：记录是否足够、近期变化、画像稳定性提示、训练卡反馈、下一步建议、非诊断边界。
   - 未登录时显示“登录后可以查看阶段性反馈”；数据不足时显示“记录还不够，先继续完成测评和练习”。

7. apps/miniprogram/pages/personalized-plan/index.{js,wxml,wxss}
   - 使用 training effectiveness 调整推荐理由。
```

阶段性反馈必须加入的状态：

```text
insufficient：记录还不够，先继续完成测评和练习。
fluctuating：近期结果仍在波动中，暂不做明确归纳。
converging：近期有一些方向逐渐稳定，可以继续观察。
stable：近期结果较稳定，但仍只作为阶段性观察。
low_confidence：本次结果可信度不足，不做明确画像解释。
```

### T10-15 情感计算与社会网络分析

必须改动：

```text
1. analysis/text_analysis/README.md（新增）
   - 说明文本来源、脱敏规则、输出位置、不能用于诊断。

2. analysis/text_analysis/build_text_features.py（新增）
   - 输入：数据库或脱敏导出。
   - 输出：outputs/text_analysis/text_features_summary.json。
   - 不输出原始自由文本。
   - 输出 emotion_keywords、emotion_categories、valence_hint、arousal_hint、intensity_hint、text_length、analysis_version。

3. analysis/text_analysis/build_social_network.py（新增）
   - 输出 nodes、edges、top_nodes、top_edges、scene_emotion_pairs、person_emotion_pairs、behavior_emotion_pairs。
   - 只输出聚合共现，不输出原句。

4. analysis/text_analysis/dictionaries/*.json（可新增）
   - emotion_terms、scene_terms、person_terms、behavior_terms、stopwords。

5. docs/02_专项进度与验收/任务十文本来源清单.md（新增）
   - 字段、来源模块、是否自由文本、是否敏感、是否默认导出、是否脱敏、是否可用于情感计算、是否可用于社会网络分析。
```

可选后端接入：

```text
只有离线脚本通过并确认权限后，才新增 backend/services/text_analysis_service.py 和 backend/routes/text_analysis.py。
普通用户端不展示复杂社会网络图；第一版最多展示简化摘要。
```

### T10-16 验收和留痕

必须更新：

```text
docs/02_专项进度与验收/任务十执行记录_YYYYMMDD.md
docs/02_专项进度与验收/任务十量表上线前人工审核清单.md
docs/02_专项进度与验收/任务十文本来源清单.md
docs/00_当前事实基准/开发日志.md
docs/00_当前事实基准/当前进度交接.md
docs/00_当前事实基准/开发说明.md
docs/03_技术真相/API接口文档.md（如 API 有改动）
docs/03_技术真相/数据库字段说明.md（如字段有改动）
docs/03_技术真相/数据字典.md（如字段有改动）
docs/10Claude协作/Claude使用记录.md（仅实际使用 Claude 或 Claude Code 时）
```

必须运行：

```powershell
python backend\scripts\validate_content.py
cd backend; python -m pytest tests -q
cd apps\web; npm run build
Get-ChildItem apps\miniprogram -Recurse -Filter *.js  | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
```

必须人工验收：

```text
微信开发者工具编译。
真机扫码预览。
未登录访问填写类页面是否提示登录。
测一测选项在真机窄屏是否仍挤压。
微信授权登录在真实配置下是否可用。
手机号授权在真实权限下是否可用。
阶段性反馈是否不显示后端技术字段。
高风险内容是否不进入普通训练推荐。
```

---

## 1. 执行前必读

请先阅读以下文件，再开始审查和修改：

```text
AGENTS.md
docs/00_当前事实基准/项目进度统一口径.md
docs/00_当前事实基准/当前进度交接.md
docs/00_当前事实基准/Claude计划模式.md
docs/03_技术真相/API接口文档.md
docs/03_技术真相/数据库字段说明.md
docs/03_技术真相/项目架构边界与后续开发规则.md
docs/05_伦理试用/知情同意与隐私授权流程.md
docs/05_伦理试用/匿名用户ID与试用数据隔离方案.md
docs/05_伦理试用/文案低AI味与伦理表达检查.md
docs/10Claude协作/Claude使用记录.md
```

同时检查图片：

```text
D:\codex\workspace\safehome1.0其他内容\文档图片\改错用图第一
```

请在执行记录中写明：

```text
1. 共读取了多少张图片；
2. 每张图片初步对应任务十中的哪一项；
3. 哪些图片无法判断；
4. 哪些问题已经在当前代码中被修复；
5. 哪些问题仍需修改。
```

---

## 2. 全局规则

### 2.1 先判断状态，再决定是否修改

每个子任务都必须先做状态判断：

```text
已完成：只记录证据，不重复开发。
部分完成：只补缺口。
未完成：按最小改动实现。
需要人工确认：不要臆造，列入人工确认清单。
```

### 2.2 禁止事项

本轮禁止：

```text
1. git add . / commit / push，除非我明确要求。
2. 删除业务文件、内容库、历史文档和测试文件。
3. 重构整体架构。
4. 修改真实 .env、token、密钥、数据库密码。
5. 提交数据库文件、备份文件、node_modules、dist、原始研究数据。
6. 擅自改量表题项原文、选项、维度和计分规则。
7. 把待审核量表标记为 fully_approved。
8. 新增 AI 自由咨询、临床诊断、医疗级危机干预。
9. 在用户端展示 profile_model_id、cluster_id、z_score、feature_id、debug 等后端技术字段。
10. 把画像写成“人格类型”“诊断类型”“异常类型”。
```

### 2.3 允许修改范围

按子任务需要，可以修改：

```text
backend/**
apps/miniprogram/**
apps/web/**
shared/**
content/**
docs/**
backend/tests/**
scripts/**
analysis/**
```

涉及数据库字段时，必须同步：

```text
backend/models.py
backend/database.py
docs/03_技术真相/数据库字段说明.md
docs/03_技术真相/数据字典.md
```

涉及 API 时，必须同步：

```text
docs/03_技术真相/API接口文档.md
shared/types/api.ts
shared/constants/api.ts
apps/miniprogram/services/api.js
apps/web/src/services/safehomeApi.ts
```

### 2.4 验证命令

每轮修改后至少运行与本轮相关的验证。完整验证命令参考：

```powershell
cd D:\codex\workspace\safehome1.0
python backend\scripts\validate_content.py

cd D:\codex\workspace\safehome1.0\backend
python -m pytest tests -q

cd D:\codex\workspace\safehome1.0\apps\web
npm run build

cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram -Recurse -Filter *.js  | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
```

如果完整验证太重，先跑目标测试，但最终报告必须说明哪些验证已跑、哪些未跑、原因是什么。

---

# 任务十：小程序体验、登录、训练反馈、阶段性画像与文本分析补强

## T10-01 登录闭环、我的页面与用户身份规则

**目标**：明确当前登录页和个人主页位置，把登录状态放到“我的”页面最上方，并在未登录填写任何内容时提示先登录。

**审查范围**：

```text
apps/miniprogram/app.js
apps/miniprogram/app.json
apps/miniprogram/pages/login/**
apps/miniprogram/pages/register/**
apps/miniprogram/pages/profile/**
apps/miniprogram/services/api.js
apps/miniprogram/services/userIdentity.js
shared/constants/api.ts
backend/routes/auth.py
backend/routes/auth_utils.py
```

**改动要求**：

1. 找到当前小程序登录页、注册页和“我的”页面。
2. 在“我的”页面最上方展示登录状态：

   * 已登录：显示用户昵称、角色、账号状态、退出登录入口；
   * 未登录：显示“登录 / 注册”入口。
3. 未登录用户点击需要保存数据的功能时，统一提示：

```text
请先登录，这样系统才能保存你的记录并生成后续复盘。
```

4. 需要拦截的功能至少包括：

   * 情绪日记；
   * 情绪温度计；
   * 测一测；
   * 训练卡打卡；
   * 个性化训练方案；
   * 项目测试填写；
   * 消息 / 督导；
   * 本周复盘。
5. 不要破坏现有 `auth_token`、`auth_user` 和 `Authorization: Bearer token` 请求链路。
6. 记录当前哪些页面已经有登录拦截，哪些页面需要补。

**允许修改**：

```text
apps/miniprogram/app.js
apps/miniprogram/pages/profile/**
apps/miniprogram/pages/login/**
apps/miniprogram/pages/register/**
apps/miniprogram/services/api.js
apps/miniprogram/utils/** 或新增登录守卫工具
docs/00_当前事实基准/当前进度交接.md
docs/00_当前事实基准/开发日志.md
docs/00_当前事实基准/开发说明.md
```

**完成标准**：

```text
1. “我的”页面顶部能清楚显示登录状态。
2. 未登录进入填写类页面时有清楚提示和登录入口。
3. 已登录后可回到原页面继续操作。
4. 小程序 JS/JSON 检查通过。
```

---

## T10-02 全局“先登录后使用”规则（并入 T10-01 执行）

**目标**：本项与 T10-01 合并执行，不重复开发。小程序正式使用时必须先登录，登录账号作为查询记录的主标识。

**背景**：当前项目曾支持匿名 user_id，后续正式试用需要改为登录账号作为主查询标识。匿名 ID 可作为历史兼容或注册时关联线索，但不能作为正式使用主标识。

**审查范围**：

```text
apps/miniprogram/app.js
apps/miniprogram/services/api.js
apps/miniprogram/services/userIdentity.js
backend/routes/utils.py
backend/routes/auth.py
docs/05_伦理试用/匿名用户ID与试用数据隔离方案.md
```

**改动要求**：

1. 小程序启动时检查登录状态。
2. 未登录用户应优先进入登录/注册页，或者在首页只显示登录入口和使用说明，不允许继续填写数据。
3. 登录后，所有业务请求默认使用 `auth_user.id`。
4. 旧匿名 ID 暂不自动迁移，除非后续单独设计迁移规则。
5. 如果保留匿名 ID，只作为：

   * 注册前临时标识；
   * 微信登录时传给后端的 `anonymous_id`；
   * 历史数据迁移时的线索。
6. 文档中说明：本轮不做匿名历史数据自动合并。

**允许修改**：

```text
apps/miniprogram/app.js
apps/miniprogram/services/api.js
apps/miniprogram/pages/home/**
apps/miniprogram/pages/login/**
apps/miniprogram/pages/register/**
docs/05_伦理试用/匿名用户ID与试用数据隔离方案.md
docs/00_当前事实基准/当前进度交接.md
```

**完成标准**：

```text
1. 未登录不能提交任何正式记录。
2. 登录后新增的目标、日记、测评、打卡、周报查询均绑定登录用户。
3. 旧匿名数据不被错误覆盖。
4. 关键页面有清楚的登录提示。
```

---

## T10-03 不同量表制定不同指导语

**目标**：目前量表指导语过于相似，需要根据不同量表制定差异化指导语。

**审查范围**：

```text
content/assessment_worksheets.json
content/scales_catalog.json
content/scale_item_drafts.json
backend/routes/assessments.py
apps/miniprogram/pages/assessment-detail/**
docs/02_专项进度与验收/P3量表录入进度表.md
```

**改动要求**：

1. 先列出当前用户端开放的全部量表。
2. 按量表类型分别制定指导语，例如：

   * 家长反思功能类；
   * 情绪调节类；
   * 自我关怀类；
   * 学业压力/学习类；
   * 心理健康筛查类；
   * 人格/特质类；
   * 睡眠/健康生活方式类；
   * 亲子沟通/家庭关系类。
3. 指导语应包含：

   * 这份量表适合什么时候填写；
   * 填写时如何理解题项；
   * 是否按最近一段时间作答；
   * 是否需要凭第一反应选择；
   * 结果如何使用；
   * 非诊断边界。
4. 敏感量表必须保留 `boundary_notice` 和 `result_disclaimer`。
5. 不得修改题项原文、选项、维度和计分规则。
6. 如果某量表题项或计分未确认，不要写成正式开放语气，应标记为“待人工复核后开放”。

**允许修改**：

```text
content/assessment_worksheets.json
content/scales_catalog.json
docs/02_专项进度与验收/P3量表录入进度表.md
docs/00_当前事实基准/量表待人工录入清单.md
apps/miniprogram/pages/assessment-detail/**
```

**完成标准**：

```text
1. 每份用户端开放量表都有相对贴合自身主题的 instructions。
2. 小程序详情页优先展示量表自身指导语。
3. 敏感量表展示边界说明。
4. validate_content.py 通过。
```

---

## T10-04 “我的—设置与说明”补充知情与边界、隐私说明

**目标**：补充“我的”页面下“设置与说明”中的知情与边界、隐私说明内容。

**审查范围**：

```text
apps/miniprogram/pages/profile/**
content/consent.md
content/privacy.md
docs/05_伦理试用/知情同意与隐私授权流程.md
docs/05_伦理试用/匿名用户ID与试用数据隔离方案.md
docs/05_伦理试用/content伦理边界校验说明.md
```

**改动要求**：

1. 在“我的”页面或设置说明页中补充以下内容：

   * 使用说明；
   * 知情与边界；
   * 隐私说明；
   * 非诊断声明；
   * 数据保存与使用说明；
   * 高风险内容处理说明；
   * 研究授权与基础使用的关系。
2. 用户端语言要简洁清楚，不要堆法律术语。
3. 不要承诺治疗效果。
4. 不要写“系统会诊断”“系统会判断疾病”“系统会处理危机”。
5. 高风险说明应写成：

   * 系统会做关键词初筛；
   * medium/high 风险进入人工关注；
   * 紧急情况优先联系线下专业人员或当地紧急资源。
6. 如果已有 `content/consent.md` 和 `content/privacy.md`，优先复用，不重复造一套冲突文本。

**允许修改**：

```text
apps/miniprogram/pages/profile/**
apps/miniprogram/pages/settings/** 或新增说明页
content/consent.md
content/privacy.md
docs/05_伦理试用/**
```

**完成标准**：

```text
1. “我的”页面能进入知情与边界、隐私说明。
2. 文案符合非诊断、非治疗、非危机干预边界。
3. 小程序 JS/JSON 检查通过。
```

---

## T10-05 个性化训练方案与项目测试内容补充，并预留文本填写位置

**目标**：补充训练中心中“个性化方案”的内容，针对每份量表填写后的不同结果推荐不同训练；补充项目测试三个项目的填写内容；为后续文本分析预留用户填写文本位置。

**审查范围**：

```text
backend/routes/training_plan.py
backend/services/training_recommendation_service.py
content/training_cards.json
content/programs.json
content/assessment_training_map.json
content/diary_training_map.json
apps/miniprogram/pages/personalized-plan/**
apps/miniprogram/pages/program-list/**
apps/miniprogram/pages/program-detail/**
apps/miniprogram/pages/training-card/**
apps/miniprogram/pages/checkin/**
shared/types/api.ts
shared/constants/api.ts
```

**改动要求**：

1. 检查当前个性化训练方案是否已经根据：

   * 最近测评结果；
   * 量表维度分；
   * 画像簇；
   * 训练卡推荐规则；
   * 训练完成记录；
     生成训练建议。
2. 如果当前只展示简单卡片，需要补充：

   * 推荐原因；
   * 对应来源量表；
   * 对应维度或画像；
   * 建议先做哪一步；
   * 非诊断边界。
3. 项目测试中的三个项目需要补充可填写内容，包括：

   * 任务说明；
   * 书写提示；
   * 反思问题；
   * 提交后的保存方式；
   * 后续文本分析用途说明。
4. 训练卡和项目测试中需要有用户可填写文本的位置，例如：

   * 练习前我注意到的想法；
   * 我现在的情绪词；
   * 我尝试的新回应；
   * 练习后的变化；
   * 今天最想记录的一句话。
5. 这些文本后续要能进入可分析的数据结构。优先复用：

   * `checkins.reflection`；
   * `records.data_json`；
   * 项目测试如已有保存结构则复用；
   * 如没有，先提出最小新增表或字段方案，不要直接大改。
6. 用户端必须说明：这些文本用于自我复盘和研究分析，不作为诊断。

**允许修改**：

```text
backend/routes/training_plan.py
backend/services/training_recommendation_service.py
content/training_cards.json
content/programs.json
apps/miniprogram/pages/personalized-plan/**
apps/miniprogram/pages/program-detail/**
apps/miniprogram/pages/training-card/**
apps/miniprogram/pages/checkin/**
shared/types/api.ts
shared/constants/api.ts
docs/03_技术真相/API接口文档.md
docs/03_技术真相/数据库字段说明.md
```

**完成标准**：

```text
1. 个性化训练方案能说明“为什么推荐”。
2. 项目测试三个项目有真实可填写内容。
3. 训练卡和项目测试有文本填写位置。
4. 文本保存路径清楚。
5. validate_content.py 通过。
```

---

## T10-06 课程界面接入状态审查与最小方案

**目标**：检查课程界面设置规则，以及 Claude计划模式任务中关于课程界面的要求是否完成；确认课程是否已经接入。

**当前问题**：课程界面点击后显示“课程详情后续接入”。

**审查范围**：

```text
apps/miniprogram/pages/course/**
content/**
backend/routes/**
shared/constants/api.ts
shared/types/api.ts
docs/00_当前事实基准/Claude计划模式.md
docs/06_产品规划/**
docs/01_当前执行入口/**
```

**改动要求**：

1. 判断当前课程页是否只是静态列表。
2. 判断是否已有课程 content 数据源。
3. 判断是否已有课程 API。
4. 判断 Claude计划模式或其他任务文档中是否要求接入课程详情。
5. 如果没有真实接入，请给出最小接入方案：

   * `content/courses.json`；
   * `GET /api/courses`；
   * `GET /api/courses/<id>`；
   * 小程序课程详情页；
   * 学习进度记录；
   * 是否与训练卡、项目测试联动。
6. 如果本轮不正式开发课程详情，至少把“课程详情后续接入”改成更自然的用户文案，例如：

```text
课程内容正在整理中，后续会逐步接入。你可以先完成训练卡和测一测，系统会根据记录推荐更合适的练习。
```

**允许修改**：

```text
apps/miniprogram/pages/course/**
content/courses.json（如确需新增）
backend/routes/courses.py（如确需新增）
shared/**
docs/06_产品规划/**
docs/03_技术真相/API接口文档.md
```

**完成标准**：

```text
1. 明确课程是否已接入。
2. 如果未接入，给出最小接入路线。
3. 用户端不再出现生硬的“后续接入”提示。
```

---

## T10-07 微信授权登录与手机号授权登录方案

**目标**：当前登录界面只有账号密码登录，需要设计微信授权登录和手机号授权登录；在真实微信配置、CloudBase 配置和手机号授权权限具备时接入，缺少配置时只完成接口骨架、配置项、文档和前端按钮，不伪造真实授权成功。

**审查范围**：

```text
backend/routes/auth.py
backend/routes/auth_utils.py
backend/models.py
backend/database.py
apps/miniprogram/pages/login/**
apps/miniprogram/pages/register/**
apps/miniprogram/services/api.js
apps/miniprogram/app.js
docs/04_部署联调/**
```

**改动要求**：

### 微信授权登录

请设计流程：

```text
1. 小程序端调用 wx.login() 获取 code。
2. 小程序把 code 发给后端 /api/auth/wechat-login。
3. 后端使用微信 AppID / AppSecret 调微信接口换取 openid/session_key。
4. 后端根据 openid 查找或创建用户。
5. 后端返回 SafeHome 自己的 auth token 和 user。
6. 小程序保存 auth_token 和 auth_user。
```

### 手机号授权登录

请设计流程：

```text
1. 小程序端使用微信手机号授权能力获取 code。
2. 后端使用微信接口换取手机号。
3. 后端绑定手机号到用户账号。
4. 前端不保存明文敏感信息。
5. 数据库只保存必要字段。
```

### 注意事项

1. 不要硬编码 AppID、AppSecret。
2. 如果缺少微信配置，请列出需要我在微信公众平台或 CloudBase 中提供/配置的内容。
3. 保留账号密码登录作为调试入口。
4. 正式用户入口优先微信授权登录。
5. 手机号登录涉及隐私，要在隐私说明中同步说明用途。
6. 如果本轮无法完整接入微信官方接口，先完成接口骨架、配置项、文档和前端按钮，不伪造真实授权成功。

**允许修改**：

```text
backend/routes/auth.py
backend/routes/auth_utils.py
backend/models.py
backend/database.py
backend/requirements.txt
apps/miniprogram/pages/login/**
apps/miniprogram/pages/register/**
apps/miniprogram/services/api.js
docs/04_部署联调/**
docs/03_技术真相/API接口文档.md
docs/05_伦理试用/隐私相关文档
```

**完成标准**：

```text
1. 登录页显示微信授权登录入口。
2. 登录页说明账号密码登录是调试/备用方式。
3. 微信登录所需配置项文档清楚。
4. 不硬编码密钥。
5. 小程序 JS 检查通过。
```

---

## T10-08 最近记录页纳入测一测记录

**目标**：最近记录页需要显示用户填写量表后的记录。

**审查范围**：

```text
apps/miniprogram/pages/profile/**
apps/miniprogram/pages/home/**
apps/miniprogram/pages/assessment-result/**
apps/miniprogram/services/api.js
backend/routes/assessments.py
backend/routes/profile.py
backend/routes/reports.py
```

**改动要求**：

1. 找到当前“最近记录”展示逻辑。
2. 确认当前是否只显示情绪日记、训练卡或其他记录。
3. 加入测一测结果记录，来源为 `assessment_results`。
4. 最近记录卡片至少显示：

   * 量表名称；
   * 完成时间；
   * 维度结果摘要；
   * 是否有关联画像落点；
   * 是否有训练推荐；
   * 点击进入结果页。
5. 不要把学生画像和普通测一测混淆。`student_profile_v1` 仍按原画像逻辑处理。
6. 如果后端没有统一最近记录接口，可先在前端组合调用；若组合调用复杂，再设计最小 API。

**允许修改**：

```text
apps/miniprogram/pages/profile/**
apps/miniprogram/pages/home/**
apps/miniprogram/services/api.js
backend/routes/reports.py 或新增 recent_records service/route
shared/types/api.ts
shared/constants/api.ts
docs/03_技术真相/API接口文档.md
```

**完成标准**：

```text
1. 用户完成测一测后，最近记录能看到该结果。
2. 点击记录能进入对应结果页。
3. 已登录用户只能看到自己的记录。
```

---

## T10-09 测一测结果页、图片/图表显示与后端标记清理

**目标**：修复测一测填写后结果页前端显示不完整的问题，并清理用户端展示的后端技术标记。

**审查范围**：

```text
apps/miniprogram/pages/assessment-result/**
apps/miniprogram/components/profile-scatter/**
apps/miniprogram/components/profile-radar/**
apps/miniprogram/utils/chart.js
backend/services/assessment_profile_service.py
backend/routes/assessments.py
content/profiles/**
```

**改动要求**：

1. 查看截图，确认结果页图片、散点图、雷达图或卡片显示不完整的具体位置。
2. 修复布局问题：

   * canvas 高度；
   * 容器宽度；
   * 图片裁切；
   * 卡片溢出；
   * 长文本换行；
   * 小屏适配。
3. 用户端不要展示：

   * `profile_model_id`；
   * `cluster_id`；
   * `feature_id`；
   * `z_score`；
   * `pc1/pc2`；
   * `debug`；
   * `backend`；
   * 任何技术字段名。
4. 用户端只展示：

   * 量表名称；
   * 维度结果；
   * 阶段性观察；
   * 支持性解释；
   * 推荐练习；
   * 非诊断边界。
5. 所有测一测结果页都按这一规则处理，不只改某一个量表。
6. 如果需要保留技术字段，只允许在 debug 页或 Web 后台展示。

**允许修改**：

```text
apps/miniprogram/pages/assessment-result/**
apps/miniprogram/components/profile-scatter/**
apps/miniprogram/components/profile-radar/**
apps/miniprogram/utils/chart.js
backend/services/assessment_profile_service.py（仅在返回字段需要补 display 文案时）
docs/05_伦理试用/文案低AI味与伦理表达检查.md
```

**完成标准**：

```text
1. 结果页图片/图表显示完整。
2. 普通用户端不再看到后端技术字段。
3. 各类测一测结果页展示规则一致。
4. 小程序 JS/JSON 检查通过。
```

---

## T10-10 训练卡文案去模板化，并补充填写区

**目标**：训练卡中去掉“练习前先提醒自己”等模板化表达，并为用户填写文本预留位置。

**审查范围**：

```text
content/training_cards.json
apps/miniprogram/pages/training-card/**
apps/miniprogram/pages/checkin/**
backend/routes/checkins.py
docs/05_伦理试用/文案低AI味与伦理表达检查.md
```

**改动要求**：

1. 全量搜索并改写类似表达：

   * “练习前先提醒自己”；
   * “请你尝试”；
   * “你可以试着”；
   * 过度模板化、AI味重、空泛的句子。
2. 改写为更具体、行动化、真实的训练手册语言。
3. 每张训练卡保留：

   * 练习目的；
   * 具体步骤；
   * 示例；
   * 反思问题；
   * 用户填写文本位置。
4. 文本位置建议包括：

   * 练习前一句话；
   * 练习中观察；
   * 练习后反思；
   * 是否有帮助；
   * 下次想调整什么。
5. 不承诺疗效，不写“治愈”“立即改善”“改变人生”。

**允许修改**：

```text
content/training_cards.json
apps/miniprogram/pages/training-card/**
apps/miniprogram/pages/checkin/**
backend/routes/checkins.py（如需扩展保存字段）
backend/models.py / database.py（仅在确需新增字段时）
docs/03_技术真相/数据库字段说明.md
```

**完成标准**：

```text
1. 训练卡不再出现明显模板化提示。
2. 用户可填写训练反思文本。
3. 文本能保存到现有或新增数据结构中。
4. validate_content.py 通过。
```

---

## T10-11 本周复盘纳入情绪日记与测一测结果

**目标**：本周复盘页面需要同时接收情绪日记、测一测结果和反馈结果。

**审查范围**：

```text
backend/routes/reports.py
backend/services/report_service.py
apps/miniprogram/pages/weekly-report/**
shared/types/api.ts
shared/constants/api.ts
backend/tests/test_*report*.py
```

**改动要求**：

1. 当前周报已读取情绪日记、打卡、反馈、学生画像。请加入通用测一测结果 `assessment_results`。
2. 周报中新增：

   * 本周完成测一测数量；
   * 完成的量表名称；
   * 各量表维度结果摘要；
   * 是否有关联画像落点；
   * 是否有训练推荐；
   * 需人工关注或高风险提示；
   * 与训练卡完成情况的关联。
3. 下一周建议应综合：

   * 情绪日记高频场景；
   * 高频情绪；
   * 测一测维度；
   * 训练卡完成情况；
   * 画像趋势；
   * 风险状态。
4. 用户端文案必须保持：

   * 阶段性观察；
   * 支持性复盘；
   * 非诊断；
   * 不做固定标签。
5. shared 类型和小程序页面同步更新。

**允许修改**：

```text
backend/services/report_service.py
backend/routes/reports.py
apps/miniprogram/pages/weekly-report/**
shared/types/api.ts
docs/03_技术真相/API接口文档.md
backend/tests/**
```

**完成标准**：

```text
1. 本周复盘能显示测一测结果。
2. 情绪日记、测一测、反馈、训练卡能共同进入复盘。
3. 没有记录时显示友好空态。
4. 后端目标测试通过。
```

---

## T10-12 题项、选项与上线前人工审核清单

**目标**：检查当前题项和选项显示错误，列出必须由我审核计分规则和题项后才能上线的量表。

**审查范围**：

```text
content/assessment_worksheets.json
content/scale_item_drafts.json
content/scales_catalog.json
docs/02_专项进度与验收/P3量表录入进度表.md
docs/00_当前事实基准/量表待人工录入清单.md
backend/scripts/validate_content.py
backend/scripts/build_worksheets.py
apps/miniprogram/pages/assessment-detail/**
```

**改动要求**：

1. 检查当前用户端开放量表的题项和选项展示。
2. 对照 catalog、draft、worksheet 和相关文档，找出：

   * 题项缺失；
   * 题项顺序异常；
   * 选项错位；
   * 选项分值错误；
   * 反向计分未确认；
   * 维度归属未确认；
   * 指导语或边界说明缺失；
   * 来源文件未人工复核；
   * 移动端窄屏下选项纵向挤压、重叠、截断或不可读；
   * Likert 横向选项过密，导致数字和文字错位；
   * 题项卡片内选项区域高度、宽度或换行策略不适配真机。
3. 输出一份清单，至少包含：

```text
worksheet_id
量表名称
当前 enabled_for_user 状态
题项状态
选项状态
计分规则状态
反向题状态
维度状态
是否建议暂时隐藏
需要我人工审核的内容
原因
```

4. 对未确认量表，建议设置为待审核或隐藏，不要默认开放。
5. 不要自行臆造题项、选项、维度和计分规则。
6. 如需改 `enabled_for_user`，先在报告中说明原因，再做最小改动。

**允许修改**：

```text
docs/02_专项进度与验收/任务十量表上线前人工审核清单.md
content/assessment_worksheets.json（仅在确认需要隐藏或补边界时）
content/scales_catalog.json（仅补状态字段或说明）
apps/miniprogram/pages/assessment-detail/**（仅修展示错误）
```

**完成标准**：

```text
1. 形成清楚的人工审核清单。
2. 明确哪些量表不能直接上线。
3. 已开放量表题项和选项在微信开发者工具和真机窄屏下显示正常，不重叠、不截断、可点击。
4. validate_content.py 通过。
```

---

## T10-13 情绪温度计加入轻量多维情绪结构并改为温度计式交互

**目标**：情绪温度计不只记录强度，还要加入轻量多维情绪结构，并把当前强度记录页面改成更像“温度计”的形式。

**重要要求**：先搜索/查阅理论依据，再改动。不要凭印象直接改。

**审查范围**：

```text
backend/routes/emotion_thermometer.py
backend/models.py
backend/database.py
apps/miniprogram/pages/thermometer/**
apps/miniprogram/utils/chart.js
shared/types/api.ts
docs/03_技术真相/API接口文档.md
docs/03_技术真相/数据库字段说明.md
```

**理论检索要求**：

请先搜索并简要记录适合本项目的轻量多维情绪结构候选，例如：

```text
1. 愉悦度 / 不愉悦度；
2. 唤醒度 / 激活度；
3. 控制感 / 可调节感；
4. 情绪强度；
5. 情绪效价；
6. 身体紧张度。
```

选择时要结合 SafeHome 的定位：轻量、自我观察、非诊断、适合家长和学生填写。

**建议实现方向**：

第一版可采用：强度作为温度计主字段，效价、唤醒度、可控感作为轻量多维补充字段。

```text
1. intensity_level：情绪强度，1-10；
2. valence_level：愉悦—不愉悦，1-10；
3. arousal_level：平静—激活，1-10；
4. control_level：可控感，1-10；
5. emotion_label：当前最接近的情绪词；
6. brief_text：简短备注。
```

也可以根据理论检索结果调整，但必须在报告中说明原因。

**前端要求**：

1. 当前强度记录页面改为温度计式视觉。
2. 强度用温度计形态展示，不只是普通输入框。
3. 多维结构用滑杆、刻度或卡片形式展示。
4. 当天记录展示变化曲线或摘要。
5. 保留边界说明：

```text
情绪温度计只用于自我观察和练习提示，不构成诊断、筛查或风险评估。
```

**后端要求**：

1. 如新增字段，使用 `ensure_column` 幂等补列。
2. MySQL 兼容字段类型。
3. API 返回旧字段兼容。
4. 更新 shared 类型和 API 文档。

**允许修改**：

```text
backend/models.py
backend/database.py
backend/routes/emotion_thermometer.py
apps/miniprogram/pages/thermometer/**
apps/miniprogram/utils/chart.js
shared/types/api.ts
docs/03_技术真相/API接口文档.md
docs/03_技术真相/数据库字段说明.md
docs/05_伦理试用/文案低AI味与伦理表达检查.md
```

**完成标准**：

```text
1. 理论依据有简要记录。
2. 情绪温度计支持强度主字段 + 效价、唤醒度、可控感等轻量多维记录。
3. 页面呈现更像温度计。
4. 旧的强度记录不被破坏。
5. 后端测试和小程序检查通过。
```

---

## T10-14 阶段性反馈、画像逐步收束、训练卡效用评价与动态推荐

**目标**：实现阶段性反馈与画像逐步收束功能。系统需要追踪用户量表填写、训练卡使用和情绪记录，纵向记录每一次填写分数、画像落点、训练卡完成情况和训练反馈，实现训练卡效用评价与动态调整训练卡推送。

这是任务十的重点任务。请先设计，再分阶段实现，不要一次性大改。

### T10-14-01 数据追踪设计

请审查现有数据表是否能支持：

```text
assessment_results
student_profiles
checkins
emotion_diaries
emotion_thermometer
feedback_results
training_cards
records
weekly_reports
```

需要追踪的数据包括：

```text
1. 用户每一次测一测填写时间；
2. 每一次量表总分和维度分；
3. 每一次画像落点、画像簇、置信度；
4. 每一次推荐了哪些训练卡；
5. 用户是否打开训练卡；
6. 用户是否完成训练卡；
7. 训练前后的情绪温度计变化；
8. 训练后的文字反思；
9. 情绪日记中的高频场景和高频情绪；
10. 每周复盘中的变化趋势；
11. 训练卡主观反馈：有帮助 / 一般 / 暂时没有帮助；
12. 训练卡跳过原因或未完成原因。
```

优先复用现有表。只有在现有结构无法表达时，才新增轻量表或字段。

### T10-14-02 阶段性反馈逻辑

设计并实现阶段性反馈服务，建议新增或扩展：

```text
backend/services/progress_summary_service.py
backend/routes/progress_summary.py
```

可选 API：

```text
GET /api/progress-summary?user_id=&range=7d|14d|30d
GET /api/profile-trend?user_id=&worksheet_id=
GET /api/training-effectiveness?user_id=
```

阶段性反馈应包括：

```text
1. 最近 7/14/30 天测评变化；
2. 同一量表维度分变化；
3. 情绪温度计趋势；
4. 训练卡完成数量；
5. 训练卡完成前后情绪变化；
6. 高频情绪场景；
7. 高频训练类型；
8. 当前记录是否足够形成趋势；
9. 下一步练习建议。
```

文案规则：

```text
数据不足：显示“记录还不够，先继续完成测评和练习。”
变化不稳定：显示“近期结果仍在波动中，暂不做明确归纳。”
趋势较稳定：显示“近期记录显示某些模式较稳定，可继续观察。”
```

不得使用：

```text
人格固定
诊断
异常
高危患者
治疗有效
疗效显著
```

### T10-14-03 画像逐步收束逻辑

设计“画像逐步收束”规则：

```text
1. 单次测评不做固定画像判断。
2. 多次同一量表结果后，比较维度分变化。
3. 多次画像落点后，比较是否持续接近同一画像簇。
4. 连续多次接近同一画像，可显示“近期结果较稳定”。
5. 多个画像间波动，显示“近期仍在变化中”。
6. 置信度低或离群时，不做明确画像解释。
7. 数据不足时只提示继续记录。
```

建议输出字段：

```text
stability_status: insufficient | fluctuating | converging | stable | low_confidence
summary_text
evidence_items
latest_profile
previous_profiles
dimension_trends
boundary_notice
```

### T10-14-04 训练卡效用评价

设计训练卡效用评价逻辑：

```text
1. 记录训练卡被推荐；
2. 记录训练卡被打开；
3. 记录训练卡是否完成；
4. 记录训练前后情绪温度计；
5. 记录用户主观反馈；
6. 记录练习后文字反思；
7. 统计完成率；
8. 统计跳过率；
9. 统计用户反馈；
10. 根据结果调整后续推荐。
```

如果现有 `checkins` 不足以记录这些内容，可以最小新增字段，例如：

```text
helpfulness_rating TEXT
before_thermometer_id TEXT
after_thermometer_id TEXT
reflection_text TEXT
skip_reason TEXT
source_recommendation_id TEXT
```

或新增轻量表：

```text
training_recommendation_events
```

但新增表前必须先说明为什么现有表不够。

### T10-14-05 动态调整训练卡推送

推荐策略分阶段：

```text
初始阶段：
- 根据量表维度分、画像簇、情绪日记推荐。

记录积累阶段：
- 加入训练卡完成率；
- 加入用户主观反馈；
- 加入训练前后情绪变化；
- 加入用户常见场景；
- 加入未完成原因。

高风险阶段：
- 停止普通自动训练推荐；
- 转入人工关注和现实支持提示。
```

推荐调整规则：

```text
1. 多次未完成某类训练，减少同类推荐，换成更短练习。
2. 多次完成且反馈较好，推荐相近或进阶练习。
3. 情绪温度计显示练习后更稳定，可保留该类练习。
4. 用户反馈“暂时没有帮助”，下次推荐替代练习。
5. 数据不足时不做强推荐，只给轻量开始建议。
```

用户端展示推荐理由时不能显示复杂后端字段，只显示：

```text
因为你最近完成了……
因为你最近在……场景记录较多
因为这张卡比较短，适合先开始
因为你之前完成过相近练习
```

### T10-14-06 前端展示

建议展示位置：

```text
apps/miniprogram/pages/home/**（主展示位置：最近记录下面的独立板块）
apps/miniprogram/pages/weekly-report/**
apps/miniprogram/pages/personalized-plan/**
apps/web/src/pages/ResearchDashboard.tsx
```

小程序端展示：

```text
1. 首页“最近记录”下面新增“阶段性反馈”独立板块；
2. 最近变化；
3. 画像稳定性提示；
4. 训练卡完成反馈；
5. 下一步建议。
6. 未登录、数据不足、低置信度时显示克制空态，不强行解释。
```

首页设计要求：

```text
1. 沿用当前小程序首页方案，不新建另一套视觉系统。
2. 继续使用 safe-section、section-title、safe-card、recent-record-card/quick-list 风格。
3. 继续使用现有 CSS 变量：--safe-primary、--safe-card、--safe-border、--safe-shadow-card 等。
4. 不新增插图，不做营销化大横幅，不占用首屏核心入口。
5. 板块位置固定在“最近记录”之后、开发联调入口之前。
```

Web 后台展示：

```text
1. 用户趋势；
2. 量表维度变化；
3. 训练卡效用；
4. 风险复核提示；
5. 研究导出摘要。
```

### T10-14-07 验收标准

```text
1. 用户完成两次同一量表后，能看到维度变化。
2. 用户完成训练卡后，阶段性反馈能读取训练记录。
3. 情绪温度计记录能进入趋势摘要。
4. 数据不足时不强行解释。
5. 高风险内容不进入普通训练推荐。
6. 小程序端不展示后端技术字段。
7. shared 类型同步。
8. API 文档同步。
9. pytest 通过。
10. Web build 通过。
11. 小程序 JS/JSON 检查通过。
```

---

## T10-15 情感计算与社会网络分析功能

**目标**：使用用户填写后的文本进行情感计算和社会网络分析，为后续研究和阶段性反馈提供依据。第一版优先做离线、可解释、脱敏、聚合分析，不直接作为诊断或风险评估。

### T10-15-01 审查现有文本来源

请先审查哪些文本来源可用：

```text
emotion_diaries.event_description
emotion_diaries.automatic_thought
emotion_diaries.behavior
feedback_results.supportive_feedback
checkins.reflection
assessment_results.answers_json 中的自由文本
student_profiles.text_features_json
supervision_requests
programs / 项目测试填写文本
records.data_json
```

输出一份文本来源清单：

```text
字段
来源模块
是否含用户自由文本
是否敏感
是否默认导出
是否需要脱敏
是否可用于情感计算
是否可用于社会网络分析
```

### T10-15-02 情感计算第一版

第一版优先使用可解释规则或轻量词典，不接入黑箱医疗判断。

建议功能：

```text
1. 情绪词识别；
2. 情绪类别归纳；
3. 情绪强度线索；
4. 情绪效价线索；
5. 高频情绪变化；
6. 与情绪温度计记录对应；
7. 与训练卡完成前后变化对应。
```

输出字段建议：

```text
sentiment_summary
emotion_keywords
emotion_categories
valence_hint
arousal_hint
intensity_hint
text_length
analysis_version
boundary_notice
```

用户端文案只能写：

```text
文本中更常出现的情绪线索是……
最近记录中较常出现的词是……
这些结果只用于自我观察和研究分析，不构成诊断。
```

不得写：

```text
你有抑郁
你焦虑严重
你存在人格问题
你属于高危患者
```

### T10-15-03 社会网络分析第一版

目标是从文本中提取“人物—场景—情绪—行为”的共现网络。

候选节点：

```text
人物：妈妈、爸爸、孩子、老师、同学、家人
场景：作业、考试、手机、睡觉、沟通、成绩、上学
情绪：生气、担心、委屈、着急、内疚、害怕、难过
行为：催促、回避、争吵、解释、安慰、沉默、指责、道歉
```

建议输出：

```text
nodes: [{id, label, type, count}]
edges: [{source, target, weight, cooccur_count}]
top_nodes
top_edges
scene_emotion_pairs
person_emotion_pairs
behavior_emotion_pairs
analysis_version
boundary_notice
```

第一版建议只在 Web 后台或研究导出中展示聚合网络，不在普通用户端展示复杂图谱。

### T10-15-04 技术实现路径

请按三阶段实现：

#### 第一阶段：离线脚本

新增或补充：

```text
analysis/text_analysis/
analysis/text_analysis/build_text_features.py
analysis/text_analysis/build_social_network.py
analysis/text_analysis/README.md
```

要求：

```text
1. 从数据库或脱敏导出读取文本；
2. 不输出原始文本；
3. 输出聚合 JSON；
4. 记录分析版本；
5. 记录停用词、词典和规则。
```

#### 第二阶段：后端服务

在离线脚本稳定后，再考虑新增：

```text
backend/services/text_analysis_service.py
backend/routes/text_analysis.py
```

API 可选：

```text
GET /api/text-analysis/summary?user_id=
GET /api/text-analysis/network?user_id=
```

需要管理员或本人权限，不能开放给无关用户。

#### 第三阶段：Web 后台展示

接入：

```text
apps/web/src/pages/ResearchDashboard.tsx
apps/web/src/components/TextEmotionSummary.tsx
apps/web/src/components/SocialNetworkGraph.tsx
```

小程序端第一版只展示简化摘要，不展示复杂图谱。

### T10-15-05 数据与伦理边界

要求：

```text
1. 默认不导出自由文本原文。
2. 优先导出脱敏特征和聚合结果。
3. 不做诊断。
4. 不做临床风险预测。
5. 不做人格判断。
6. 高风险词仍走 risk_review_records，不由情感计算替代。
7. 所有分析结果都要有 boundary_notice。
```

### T10-15-06 验收标准

```text
1. 形成文本来源清单。
2. 离线脚本可运行。
3. 输出脱敏聚合 JSON。
4. 不包含原始自由文本。
5. 能生成情绪关键词摘要。
6. 能生成共现网络节点和边。
7. 文档说明清楚分析边界。
8. 不影响小程序主流程。
```

---

## T10-16 任务十验收与留痕

**目标**：任务十所有子任务结束后，必须形成可交接记录。

### 必须新增或更新文档

```text
docs/02_专项进度与验收/任务十执行记录_YYYYMMDD.md
docs/02_专项进度与验收/任务十量表上线前人工审核清单.md
docs/00_当前事实基准/当前进度交接.md
docs/00_当前事实基准/开发日志.md
docs/00_当前事实基准/开发说明.md
docs/10Claude协作/Claude使用记录.md
```

说明：`docs/10Claude协作/Claude使用记录.md` 仅在本轮实际使用 Claude 或 Claude Code 时更新；如果只使用 Codex，不更新该文档，并在最终报告中说明原因。

如涉及 API、数据库、数据字典，还要同步：

```text
docs/03_技术真相/API接口文档.md
docs/03_技术真相/数据库字段说明.md
docs/03_技术真相/数据字典.md
```

### 任务十最终验收命令

```powershell
cd D:\codex\workspace\safehome1.0
python backend\scripts\validate_content.py

cd D:\codex\workspace\safehome1.0\backend
python -m pytest tests -q

cd D:\codex\workspace\safehome1.0\apps\web
npm run build

cd D:\codex\workspace\safehome1.0
Get-ChildItem apps\miniprogram -Recurse -Filter *.js  | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
```

### 最终报告格式

任务完成后，请按以下格式汇报：

```text
1. 本轮读取的图片与对应问题
2. 本轮完成概况
3. T10-01 至 T10-15 状态表
4. 修改文件列表
5. 新增文件列表
6. 数据库/API/shared 是否有改动
7. 内容库是否有改动
8. 量表上线前仍需人工审核清单
9. 运行过的验证命令与结果
10. 未运行的验证命令与原因
11. 仍需微信开发者工具/真机人工验收的事项
12. 下一轮建议，不超过 5 条
```

### 状态表模板

```markdown
| 子任务 | 状态 | 证据 | 修改文件 | 验证结果 | 仍需人工确认 |
|---|---|---|---|---|---|
| T10-01 登录页与我的页面 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-02 强制登录规则 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-03 量表指导语 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-04 知情隐私说明 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-05 个性化方案与项目测试 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-06 课程接入审查 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-07 微信/手机号登录 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-08 最近记录 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-09 结果页显示 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-10 训练卡文案 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-11 本周复盘 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-12 量表审核清单 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-13 情绪温度计轻量多维结构 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-14 阶段性反馈与画像收束 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
| T10-15 情感计算与社会网络分析 | 已完成/部分完成/无需修改/待人工 |  |  |  |  |
```

---

# 任务十一：任务十深化 —— 收尾缺口 · 训练闭环动态化 · 复盘契约持久化 · 情感计算与SNA真实化

> 适用仓库：`D:\codex\workspace\safehome1.0`
> 创建：2026-07-06 · 来源：Claude Code 审计（5 组只读代码审计 + 真机截图核对）
> 本轮定位：**不是重写，是补齐与深化**。任务十把 16 个子项的「骨架」搭好，但审计确认约一半只是「骨架在、实质浅或缺失」。任务十一把这些落到实处。
> 行号引用来自审计当时的代码状态：**改之前先核对行号是否漂移**（沿用本文件 §3 惯例）。

## 0. Context（为什么做）

任务十自评「16 项全部已补强/已完成」，只读审计实测：

```text
🔴 未达原意（用户明确点名但没做到）：
  - 训练卡「练习前先提醒自己」字样仍硬编码（training-card/index.wxml:68）。
  - 情绪温度计仍是滑杆，非温度计造型（thermometer/index.wxml:12-21）。
  - 课程仍是死 toast，无真接入（course/index.js:68-73）。
🟡 骨架在、实质浅：
  - 16 个启用量表里 15 个指导语一字不差；review_note 却写「已按类型细化」（过度声明）。
  - 阶段性反馈按「记录条数」而非真波动判定（progress_summary_service.py:153-159）；stable/low_confidence 是死状态。
  - 动态推荐没吃 checkin 反馈（training_recommendation_service.py:13-43）。
  - 本周复盘字段契约错位、多维未聚合、且不持久化（report_service.py:138-149 / reports.py:26-45）。
  - 情感计算词典是「死文件」从不加载、无中文分词、valence/arousal 写死字符串（analyze_text_sources.py:37-70,122-125 / build_text_features.py:32-33）。
🕳 边界/安全：
  - supervision 未登录可写 demo-parent（supervision.py:23）。
  - 用户端泄漏「（CES-D10待复核）」标题与「开放前必须展示…人工复核入口」内部审核语。
```

四条工作流：**S1 收尾缺口 → S2 训练闭环动态化 → S3 复盘契约持久化 → S4 情感计算+SNA真实化**。

## 0A. 执行口径（优先于下文细则）

```text
1. 一次性连续执行 T11-01 → T11-21；除需用户提供微信配置/真机截图/受版权词库外，自动判断→修复→验证→留痕。
2. 先判断状态再改：多数子项是「补缺口」，已对的部分不重写；改前核对审计给的 file:line 是否漂移。
3. 顺序：S1 先做（成本低、清「假完成」、多为用户原话点名）→ S2 → S3 → S4（最重）。
4. S4 走真实路线：jieba 分词 + 大连理工情感本体/BosonNLP；但严格离线（analysis/，不进后端运行时，
   仅新增只读研究端点）；只输出聚合/脱敏结果，绝不输出原始自由文本。
5. 边界不变：非诊断/非治疗/非危机干预；用户端文案不得写成诊断、人格判断、疗效。
6. 沿用当前小程序设计语言（safe-* token），不新起视觉体系、不堆插图。
```

## 0B. 全局规则 / 禁止 / 允许 / 同步 / 验证（沿用任务十 §2，不复述）

```text
禁止：git add./commit/push（除非用户要求）、删业务文件、改量表题项原文与计分规则、
      把待审核量表标 fully_approved、用户端展示 profile_model_id/cluster_id/z_score/feature_id/debug、
      把画像写成人格类型/诊断类型/异常类型、新增 AI 自由咨询/临床诊断/危机干预。
允许改：backend/** apps/miniprogram/** apps/web/** shared/** content/** docs/** backend/tests/** scripts/** analysis/**。
改 DB 字段 → 同步 backend/models.py + backend/database.py + docs/03_技术真相/数据库字段说明.md + 数据字典.md，并升 CURRENT_SCHEMA_VERSION/NAME。
改 API → 同步 shared/types/api.ts + shared/constants/api.ts + apps/miniprogram/services/api.js + apps/web/src/services/safehomeApi.ts + docs/03_技术真相/API接口文档.md。
每子任务完成向 docs/02_专项进度与验收/任务十一执行记录_YYYYMMDD.md 追加证据。
```

## 0C. 与用户原始 15 条需求的对应

| 原始条目 | 任务十一落点 |
|---|---|
| #2 差异化指导语 | T11-02 |
| #9 去「练习前先提醒自己」 | T11-01 |
| #13 温度计造型 | T11-03 |
| #7 最近记录 / #1 登录页与我的页 / #12 强制登录 | T11-04、T11-05、T11-06 |
| #8 结果页去后端标记（残留泄漏） | T11-07 |
| #4 / #14 训练个性化、效用评价与动态推荐 | T11-08 ~ T11-12 |
| #5 课程接入 | T11-13 |
| #10 复盘纳入测评/温度计 | T11-14 |
| #15 情感计算 + 社会网络分析 | T11-15 ~ T11-20 |

---

## S1 · 收尾 T10 缺口

### T11-01 去掉「练习前先提醒自己」及模板残留

**目标**：删除用户明确点名要去掉的「练习前先提醒自己」字样，并清掉训练卡文本区里成批复制的模板句，让文本区呈现自然、逐卡不同。

**当前代码事实（核对行号漂移）**：
```text
apps/miniprogram/pages/training-card/index.wxml:68  <text class="tip-title">练习前先提醒自己</text>
apps/miniprogram/pages/training-card/index.wxml:73  <text class="tip-title">练习后可以记一句</text>
content/training_cards.json  「练习前」「先提醒自己」作为 tip 文案 ~34 张卡重复出现。
```

**必须改动**：
```text
1. apps/miniprogram/pages/training-card/index.wxml
   - 删除第 68 行「练习前先提醒自己」标题；tip-box 只保留提示正文（item.beforePrompt），
     或将标题改为中性自然表达（如「可以先想一下」）。第 73 行「练习后可以记一句」同理评估，
     保留则改为自然文案，不用命令式「提醒自己」。
2. content/training_cards.json
   - 扫描并清除所有卡片里以「练习前先提醒自己」为模板的重复句；beforePrompt/afterPrompt 由 T11-09 逐卡改写。
3. 全局扫描 apps/miniprogram/**/*.{wxml,js} 与 content/training_cards.json 再确认无「练习前先提醒自己」残留。
```

**完成标准**：全仓 grep「练习前先提醒自己」为 0 命中；训练卡页 tip 区文案自然、无命令式模板句；小程序 JS/JSON 检查通过。
**测试**：`node --check apps/miniprogram/pages/training-card/index.js`；真机看训练卡详情无该字样。

### T11-02 量表差异化指导语（8 类模板落地）

**目标**：把 15 个启用量表一字不差的通用指导语，按量表类型改成差异化指导语；修正 review_note 的过度声明。

**当前代码事实**：
```text
content/assessment_worksheets.json 共 27 份，enabled_for_user=true 为 16 份。
其中 15 份 instructions 完全相同的通用串（仅 student_profile_v1 不同）。
catalog/worksheet review_note 已写「指导语已按任务十量表类型细化」——与事实不符（过度声明）。
content/scales_catalog.json 的 emotion_regulation_erq(_gross) 缺 instruction_status。
详情页只渲染 worksheet.instructions（assessment-detail/index.wxml:13）。
```

**必须改动**：按下表为每个启用 worksheet 写差异化 `instructions`（1–2 句，口吻克制、非诊断）：

```text
家长反思类   → parent_reflective_functioning_prfq
  「请按最近与孩子互动时的真实感受作答，不追求标准答案，也不评判自己做得好不好。」
情绪调节/弹性 → emotion_regulation_erq、cd_risc10_brief_resilience、emotional_resilience_11、emotional_intelligence_eis_33
  「请按最近一段时间遇到情绪波动时的通常反应作答，只是观察你的习惯方式，没有对错。」
自我关怀类   → self_compassion_scs_cn
  「请按自己遇到压力或挫折时的习惯反应作答，看看你平时怎样对待自己。」
觉察/正念类   → mindful_attention_awareness_maas
  「请留意最近当下的注意力与身体感受，按通常状态作答，没有标准答案。」
学业/学习类   → study_engagement_uwes_s_17、attribution_style_student_36
  「请按最近学习、考试、作业相关的真实状态作答，只作了解自己学习方式的线索。」
心理健康筛查（敏感）→ gad7_anxiety、phq9_cesd10_depression、ghq12_general_health
  「请按最近一段时间的真实情况作答。结果仅作自我观察，不用于诊断、筛查结论或治疗建议。」
人格/特质（敏感）→ big_five_bfi_60、epq_emotional_stability_24
  「请按平时更接近自己的情况作答。结果不生成固定人格标签，只作为了解自己反应倾向的线索。」
社会支持/关系 → perceived_social_support_psss
  「请按你实际能获得的支持情况作答，聚焦具体的人和事，不评判多少。」
（student_profile_v1 指导语已独特，保留不动。）
```
```text
其他配套：
- content/scales_catalog.json：同步每条 instruction_status（如 type_specific_done），补 emotion_regulation_erq 的缺失项。
- 修正 review_note：仅在指导语确已按类型落地后才写「已细化」，否则如实标注状态，去掉过度声明。
- 不改题项 prompt/options/dimension/reverse_scored/score；敏感量表的 boundary_notice/result_disclaimer 见 T11-07。
- 运行 backend/scripts/build_worksheets.py 让生成区回填（人工区深合并保留）。
```

**完成标准**：16 份启用量表指导语按类型互不相同；`validate_content.py`、`build_worksheets.py` 通过；详情页可见对应指导语。
**测试**：`python backend/scripts/build_worksheets.py`；`python backend/scripts/validate_content.py`；真机抽查 3 类量表指导语不同。

### T11-03 情绪温度计改为温度计造型

**目标**：把「现在的强度」从普通滑杆改成竖式温度计视觉（球泡 + 管柱 + 水银高度随强度变化），满足用户「做一个温度计的形式」。补充维度与今日曲线保留。

**当前代码事实**：
```text
apps/miniprogram/pages/thermometer/index.wxml:12-21  强度=<slider min=1 max=10>
apps/miniprogram/pages/thermometer/index.wxml:24-38  愉悦度/身体唤起/可控感=三个 micro-slider
apps/miniprogram/pages/thermometer/index.wxml:65-70  今日曲线 canvas（折线，index.js:189-209 绘制）
intensityLevel 等已在 data 中，saveRecord 已提交多维字段（T10-13 已通）。
```

**必须改动**：
```text
1. apps/miniprogram/pages/thermometer/index.wxml
   - 用温度计结构替换第 12-21 行 slider：
     竖直管 .thermo-tube（外壳）+ .thermo-fill（水银，内联 style="height:{{intensityLevel*10}}%"）
     + .thermo-bulb（底部球泡）+ 右侧 1..10 刻度 .thermo-ticks。
     交互：管身 bindtap/bindtouchmove → setLevelByTouch 计算落点对应 1..10；另留 +/- 微调按钮兜底。
2. apps/miniprogram/pages/thermometer/index.wxss（新增样式）
   - .thermo-tube{position:relative;width:64rpx;height:360rpx;border-radius:40rpx;background:var(--safe-bg);
     border:2rpx solid var(--safe-border);overflow:hidden;}
   - .thermo-fill{position:absolute;left:0;bottom:0;width:100%;
     background:linear-gradient(to top,#6a86b4,#7aa78f,#d18a55);transition:height .15s;}  /* 低→冷，高→暖 */
   - .thermo-bulb{width:96rpx;height:96rpx;border-radius:50%;background:#d18a55;margin:-16rpx auto 0;}
   - 数字 {{intensityLevel}}/10 显示在管旁。
3. apps/miniprogram/pages/thermometer/index.js
   - 新增 setLevelByTouch(e)：按触点 y 相对管高换算 level（夹紧 1..10）→ setData(intensityLevel)。
   - 保留 onValence/Arousal/ControlChange、saveRecord、loadDay、drawMoodCurve 不变。
4. 三个补充维度可保留 micro-slider 或改分段按钮（择一，保持简洁）；emotion_label 输入与今日曲线保留。
   边界文案保持非诊断。
```

**完成标准**：强度以温度计造型呈现且可点/可拖设值；多维与曲线不回归；JS/JSON 检查通过。
**测试**：`node --check apps/miniprogram/pages/thermometer/index.js`；真机点/拖温度计能改强度、能记录、能看曲线。

### T11-04 最近记录可点 + 画像徽标 + 未登录提示

**目标**：让测一测最近记录卡可点进结果页、有画像的显「有画像」徽标、未登录时给登录入口而非静默空白。

**当前代码事实**：
```text
apps/miniprogram/pages/assessment/index.wxml:59-68  最近记录显示 量表名/时间/summary，卡片无 bindtap、无画像标记。
apps/miniprogram/pages/assessment/index.js:192-199  listAssessmentResults 出错时静默置空，无未登录提示。
后端 list_assessment_results 已返回 worksheet_title/created_at/total_score + scores.dimensions；
结果行可含 profile_cluster_id/profile_model_id（T4/T10 落点字段）。
```

**必须改动**：
```text
1. apps/miniprogram/pages/assessment/index.wxml
   - 最近记录卡加 bindtap="openResult" data-id="{{item.id}}" → navigate 到 assessment-result（带 result id）。
   - 行内在有 profile_cluster_id/profile_model_id 时显示「有画像」徽标（复用 tag-pill 样式）。
   - 新增未登录态：needsLogin 时显示「登录后查看你的测评记录」+ 去登录按钮。
2. apps/miniprogram/pages/assessment/index.js
   - openResult：wx.navigateTo 到结果页并传 result id（沿用结果页现有入参）。
   - 捕获 auth_required：setData(needsLogin:true) 而非静默置空；已登录出错才显示重试。
```

**完成标准**：最近记录可点进结果页、有画像有徽标、未登录有登录入口；JS 检查通过。
**测试**：`node --check apps/miniprogram/pages/assessment/index.js`；真机未登录/已登录两态走查。

### T11-05 全局登录守卫补齐

**目标**：把 authGuard.requireLogin 真正接到所有「保存/查询私有数据」的页面入口或提交处，并统一「auth_required → 跳登录」的被动兜底。

**当前代码事实**：
```text
apps/miniprogram/utils/authGuard.js:13  requireLogin({redirectUrl,message}) 已实现（toast+跳登录）。
仅 profile/index.js:137 主动调用；被动 auth_required→跳登录只在 assessment-detail/index.js:194-211、messages/index.js:31-53。
缺页面级守卫：diary-form(submit ~:75)、thermometer(save ~:94)、checkin(submit ~:62)、supervision(:27)、
  personalized-plan、program-detail(正式提交)、weekly-report、message-detail。
```

**必须改动**：
```text
1. 在上述每个页面的「进入即需登录」或「提交动作」处调用 authGuard.requireLogin，未登录 return 并跳登录。
2. 把 assessment-detail/messages 的 auth_required 反应式处理抽成 authGuard 公共方法（如 handleAuthError(err)），
   各页 catch 统一调用，避免各写各的。
3. 私有页 onShow/onLoad 可用 isLoggedIn() 预判，未登录展示登录引导卡（沿用 T11-04 文案风格）。
必须文案：请先登录，这样系统才能保存你的记录并生成后续复盘。
```

**完成标准**：8 个私有页未登录进入或提交都有登录提示与入口，登录后可回原页继续；JS 检查通过。
**测试**：逐页 `node --check`；真机未登录触发每页提交，确认拦截并跳登录。

### T11-06 supervision 权限洞 + 收紧 dev 回退与匿名注入

**目标**：堵住未登录可写 demo-parent 的后端洞，收紧开发态回退与前端匿名 user_id 注入。

**当前代码事实**：
```text
backend/routes/supervision.py:23  仍用 require_user_id，无 require_login → 未登录/伪造可写 demo-parent。
backend/config.py:17  APP_ENV 默认 development；多数私有路由 allow_dev_fallback=True → 本地仍信任前端 user_id/demo-parent。
apps/miniprogram/services/api.js:100-105  withDefaultUser 仍向私有 payload 注入匿名 user_id（getAnonymousUserId:80）。
backend/routes/auth_utils.py:83-110  resolve_actor_user_id 已实现（:107-108 为 dev demo-parent 回退）。
backend/routes/utils.py:53-67  legacy require_user_id/resolve_user_id_for_query 仍被 consent/feedback/goals/parent_assessments/privacy/profile/supervision 使用。
```

**必须改动**：
```text
1. backend/routes/supervision.py：改用 resolve_actor_user_id/require_login，未登录 401；owner 校验按 token actor。
2. 收紧回退：resolve_actor_user_id 的 allow_dev_fallback 默认 False，demo-parent 仅在显式 debug 开关下可用；
   逐步把 consent/feedback/goals/parent_assessments/privacy/profile 迁出 legacy require_user_id。
3. apps/miniprogram/services/api.js：requiresAuth 端点不再注入匿名 user_id（withDefaultUser 仅对公开接口用）。
4. 说明保留 debug 页面必要的临时兼容，并在执行记录写明。
```

**必须新增/更新测试**：
```text
backend/tests/test_sensitive_owner_auth.py / test_user_id_policy.py：
  未登录提交 supervision → 401；普通用户伪造 user_id 查他人 → 只返回自己的；admin/supervisor 权限路径仍可用。
```
**完成标准**：supervision 未登录不可写；私有路由默认不信任前端 user_id；pytest 通过。
**测试**：`python -m pytest backend/tests/test_user_id_policy.py backend/tests/test_sensitive_owner_auth.py -q`。

### T11-07 清理用户端泄漏的后端/审核字段

**目标**：把泄漏到用户端的内部审核语与复核标记移出用户可见字段，替换为正常免责文案。

**当前代码事实**：
```text
敏感量表 boundary_notice 与 result_disclaimer 都被写成内部审核语：
  「该量表含健康、筛查或人格语义，开放前必须展示非诊断免责声明，并保留人工复核入口。」
  出现于 content/assessment_worksheets.json:6195/11283/11564/12842/13173/15447/17593/18148 及 content/scales_catalog.json:48…
PHQ-9 display_title/source_title 带「（CES-D10待复核）」：
  content/assessment_worksheets.json:12849-12850、content/scale_item_drafts.json:4689、content/scales_catalog.json:407。
```

**必须改动**：
```text
1. 敏感量表 boundary_notice / result_disclaimer 替换为面向用户的正常免责，例如：
   「本量表仅用于自我观察与练习参考，不构成诊断、筛查结论或人格判断；如有困扰，请联系现实中的专业资源。」
   把原内部审核语移入非用户字段 review_note（catalog/worksheet 内部区），不再进用户端。
2. PHQ-9：display_title/source_title 去掉「（CES-D10待复核）」，改为干净标题「PHQ-9 抑郁相关自评量表」；
   把「CES-D10待复核 / 版本」信息移入 review_note 或 source_version 字段。
   同步 content/scales_catalog.json、content/scale_item_drafts.json。
3. 运行 build_worksheets.py 回填；确认 assessment-detail 底部免责、结果页免责显示的是正常文案而非内部审核语。
```

**完成标准**：用户端不再出现「开放前必须展示…人工复核入口」「（CES-D10待复核）」；敏感量表免责为正常用户文案；`validate_content.py` 仍要求敏感类必备边界（不回归）。
**测试**：`python backend/scripts/validate_content.py`；`python backend/scripts/build_worksheets.py`；真机看 PHQ-9 标题与敏感量表免责。

---

## S2 · 训练闭环动态化

### T11-08 训练地图覆盖补全

**目标**：为未覆盖的启用量表补训练推荐规则，修正失效/错配 id。

**当前代码事实**：
```text
content/assessment_training_map.json 现 ~19 条规则，仅覆盖 ~4 个启用量表（prfq、emotion_regulation_erq、self_compassion_scs_cn + student_profile）。
未覆盖的启用量表（~11）：gad7_anxiety、phq9_cesd10_depression、perceived_social_support_psss、mindful_attention_awareness_maas、
  big_five_bfi_60、epq_emotional_stability_24、ghq12_general_health、attribution_style_student_36、study_engagement_uwes_s_17、
  emotional_resilience_11、emotional_intelligence_eis_33。
存在失效/错配：引用 rsca_adolescent_resilience(enabled:false)；scale id emotion_regulation_erq vs catalog emotion_regulation_erq_gross。
```

**必须改动**：
```text
1. 为上述 ~11 个启用量表补规则：trigger_condition（按维度高/低）、recommended_card_ids（取自 content/training_cards.json 现有卡 id）、
   reason（支持性、非诊断）、boundary_notice。
2. 敏感量表（gad7/phq9/ghq12/big_five/epq）推荐须温和、非诊断，并标注高风险时抑制普通推荐（与 T11-11 一致）。
3. 修正 id：去掉/替换 rsca(disabled) 引用；统一 erq id 与 catalog 一致。
```

**完成标准**：每个启用量表有推荐规则或明确「无推荐理由」；引用的卡 id 均存在；`validate_content.py` 通过。
**测试**：`python backend/scripts/validate_content.py`；抽查 2 个敏感量表填写后推荐温和且不含诊断。

### T11-09 训练卡 prompt 去重、逐卡撰写

**目标**：把 34 张训练卡完全相同的文本区提示改成逐卡不同，避免后续文本分析输入是同一套模板。

**当前代码事实**：
```text
content/training_cards.json 约 34 张卡，pre_practice_prompt/emotion_word_prompt/new_response_prompt/
  post_practice_prompt/one_sentence_note_prompt/after_note_prompt/boundary_notice 逐字节相同（仅 pre_practice_prompt 内插了卡名）。
逐卡不同的内容只在 suitable_scene/today_goal/steps/example_phrase。
```

**必须改动**：
```text
1. 按每张卡的 suitable_scene/today_goal/steps 改写 5 个填写提示字段，使其与该卡主题相关、互不雷同。
   例：情绪命名类卡 emotion_word_prompt 引导「给此刻情绪起个具体的名字」；
       行为激活类卡 new_response_prompt 引导「写下一个今天能做的更小的动作」。
2. 不改训练卡核心步骤含义；boundary_notice 可按卡类型分 2-3 种，而非全表一句。
```

**完成标准**：训练卡文本提示逐卡不同（抽查任意 5 张不重复）；JSON 校验通过。
**测试**：`python backend/scripts/validate_content.py`；`ConvertFrom-Json` 校验；真机抽查训练卡文本区提示不同。

### T11-10 阶段性反馈：真波动/收束计算

**目标**：把阶段性反馈从「按记录条数」判定改成真实波动/收束计算，让 5 个状态都能真正产生。

**当前代码事实**：
```text
backend/services/progress_summary_service.py:153-159  _status 仅按记录条数返回 converging/fluctuating（从不测真波动）。
:68-89 _dimension_trends 已算 newest−oldest 维度 delta；:41-53 repeated_worksheets 已算 score_delta。
stable 仅来自 build_profile_convergence（首页未调用）；low_confidence 无处产生 → 首页 2 个状态是死代码。
```

**必须改动**：
```text
1. 重写 _status：对情绪温度计 intensity_level 时间序列、重复测评 total_score/维度 delta 计算标准差/变异系数（CV）：
   - CV 低且样本足 → stable；CV 中 → converging；CV 高 → fluctuating；
   - 样本稀疏或信号相互矛盾 → low_confidence；样本不足阈值 → insufficient。
2. build_progress_summary 输出的 stability_status 覆盖全部 5 状态；首页 statusTextMap 已有映射（home/index.js:28-34）。
3. 阈值与窗口（range_days）写成常量并在执行记录说明取值依据。
```

**完成标准**：5 个状态都能由真实数据触发；`/api/progress-summary` 返回随波动变化；pytest 通过。
**测试**：`python -m pytest backend/tests/test_t10_routes.py -q`（补波动用例：高波动→fluctuating，低波动足量→stable）。

### T11-11 训练卡动态推荐（吃反馈信号）

**目标**：让推荐真正消费 checkin 反馈——降权被反复跳过/无帮助的卡，升权有帮助的卡，保留高风险抑制。

**当前代码事实**：
```text
backend/services/training_recommendation_service.py:13-43  纯按测评维度阈值匹配；仅高风险抑制(:21-28)；从不读 checkins。
checkins 已有 helpfulness_rating/skip_reason/source_recommendation_id/before_thermometer_id/after_thermometer_id（models.py:176-180 / database.py:580-584）。
```

**必须改动**：
```text
1. 推荐函数读取该用户 checkins：统计每卡完成次数、helpfulness_rating（有帮助/一般/暂时没有帮助）、skip_reason。
2. 打分调整：反复「暂时没有帮助」或跳过 → 降权；「有帮助」→ 升权；完成率纳入。
3. 高风险状态仍抑制普通推荐（保留现有护栏）。输出附 recommendation_reason 供前端展示。
```

**完成标准**：同一用户在不同反馈历史下推荐结果不同；高风险仍抑制；pytest 通过。
**测试**：`python -m pytest backend/tests/test_t10_routes.py -q`（补：标记某卡「暂时没有帮助」后其排序下降）。

### T11-12 训练卡效用评价（真前后测）

**目标**：用打卡前后的情绪温度计落点计算每卡效用，替代当前仅包一层计数摘要。

**当前代码事实**：
```text
backend/services/progress_summary_service.py:251-278  build_training_effectiveness 仅包 _checkin_summary(:264)，无真评价。
checkins 有 before_thermometer_id/after_thermometer_id/helpfulness_rating。
```

**必须改动**：
```text
1. build_training_effectiveness：按 checkins.before/after_thermometer_id 关联 emotion_thermometer.intensity_level，
   计算每卡前后强度 delta 均值 + 有帮助率随时间趋势；输出 per-card effectiveness 摘要。
2. personalized-plan 推荐理由引用该摘要（「这张卡对你近期强度平均下降 X」类支持性表达，非疗效承诺）。
3. 样本不足时标注「样本偏小，仅供参考」。
```

**完成标准**：`/api/training-effectiveness` 返回逐卡前后 delta 与有帮助率；样本不足有兜底；pytest 通过。
**测试**：`python -m pytest backend/tests/test_t10_routes.py -q`（补：造前后温度记录→delta 正确）。

### T11-13 课程真接入

**目标**：把课程从死 toast 升级为真实内容 + 详情页 + 后端接口。

**当前代码事实**：
```text
apps/miniprogram/pages/course/index.js:9-45  硬编码 5 课数组；openCourse():68-73 仅 toast，不跳转。
无 content/courses.json、无 backend/routes/courses.py、无 pages/course-detail/。
backend/routes/programs.py 可作后端蓝图范式参考。
```

**必须改动**：
```text
1. content/courses.json：每课含 id/title/theme/scene/duration/sections[]/relation_to_cards_or_programs/boundary_notice。
2. backend/routes/courses.py：GET /api/courses、GET /api/courses/<id>；在 backend/app.py 注册蓝图。
3. 同步 shared/constants/api.ts + shared/types/api.ts + apps/miniprogram/services/api.js（courses 端点与类型）。
4. apps/miniprogram/pages/course-detail/index.*（新增）：渲染课程小节、与训练卡/项目测试关系、边界说明。
5. course/index.js openCourse → wx.navigateTo 到 course-detail；如记录学习进度优先写 records（module_type='course_progress'）。
```

**完成标准**：课程列表来自后端、点击进详情、详情展示小节与边界；Web/小程序检查通过。
**测试**：`python -m pytest backend/tests -q`（补 courses 路由用例）；`node --check` 课程页；真机点课程进详情。

---

## S3 · 本周复盘字段契约与持久化

### T11-14 本周复盘纳入测评/温度计（字段对齐 + 持久化 + 展示）

**目标**：把本周复盘的测评/温度计摘要字段对齐规格、聚合多维、持久化并在页面展示维度变化与推荐训练。

**当前代码事实**：
```text
backend/services/report_service.py:55-70  已查 assessment_results + emotion_thermometer；
  但 :138-142 产出 assessment_trend{assessment_count,worksheet_names,dimension_names}（非规格 assessment_summary），
  缺 dimension_summaries(维度 delta)、profile_position_count、requires_review_count、recommended_card_ids；
  :143-149 thermometer_trend 有 avg_intensity，缺 avg_valence/avg_arousal/avg_control；
  :112-121 next_week_suggestion 只用 profiles+checkins+diaries。
backend/routes/reports.py:26-45  INSERT 仅 8 个旧列；:48 返回 **report（trend 透传但不持久化）。
backend/models.py:404-415  weekly_reports 无 assessment_summary_json/thermometer_summary_json/training_effectiveness_summary_json。
shared/types/api.ts:940-957  WeeklyReport 仅 profile_trend?。
apps/miniprogram/pages/weekly-report/index.*  显示 测评数量/量表名/维度名/温度趋势，但显示维度「名字」非「变化」，无推荐训练区。
```

**必须改动**：
```text
1. report_service.py：
   - 产出 assessment_summary{count,worksheet_names,dimension_summaries[含每维 delta 与方向],profile_position_count,requires_review_count,recommended_card_ids}。
   - 产出 thermometer_summary{count,avg_intensity,avg_valence,avg_arousal,avg_control,intensity_trend}。
   - 产出 training_effectiveness_summary（复用 T11-12 输出；不可用时给计数占位并标注）。
   - next_week_suggestion 纳入 assessment_results 与 thermometer 信号。
2. backend/models.py + backend/database.py：weekly_reports 经 ensure_schema_columns 幂等加
   assessment_summary_json / thermometer_summary_json / training_effectiveness_summary_json（*_json 自动 LONGTEXT，勿进 MYSQL_VARCHAR_COLUMNS）；升 CURRENT_SCHEMA_VERSION/NAME。
3. backend/routes/reports.py：INSERT 持久化上述新列；响应返回三个 summary。
4. shared/types/api.ts：WeeklyReport 增 assessment_summary/thermometer_summary/training_effectiveness_summary。
5. apps/miniprogram/pages/weekly-report/index.*：展示 本周测评次数/量表名/维度变化(delta 方向)/推荐训练；保留友好空态；复用 safe-* token。
6. 同步 docs/03_技术真相/数据库字段说明.md、数据字典.md、API接口文档.md。
```

**完成标准**：周报返回并持久化测评/温度计/效用三摘要；页面显示维度变化与推荐训练；无测评有空态；pytest 通过。
**测试**：`python -m pytest backend/tests -q`（补：造本周测评+温度记录→周报摘要非空且持久化）；`node --check` 周报页。

---

## S4 · 情感计算 + 社会网络分析真实化（离线，聚合脱敏，非诊断）

> 硬边界：只输出聚合/脱敏结果，绝不输出原始自由文本；不做诊断、危机预测、人格判断、个体标签；原始 .sav/逐行隐私数据严禁入仓；普通用户端不展示复杂社会网络图。

### T11-15 接入真中文分词（jieba）

**目标**：用 jieba 分词替换朴素子串匹配，为情感计算与共现打底。

**当前代码事实**：
```text
analysis/text_analysis/analyze_text_sources.py:122-125  匹配为 word in text（比按字切分还粗）。
全仓无 jieba/HanLP（import jieba → ModuleNotFoundError）。
analysis/profiling/requirements-analysis.txt 为离线分析依赖清单。
```

**必须改动**：
```text
1. 依赖：analysis/profiling/requirements-analysis.txt（或新增 analysis/text_analysis/requirements.txt）加 jieba、networkx（供 T11-18）。
   仅离线环境安装，不进 backend/requirements.txt、不进后端运行时。
2. analyze_text_sources.py：新增 tokenize(text) 用 jieba.lcut；加载 dictionaries/*.json 为自定义词典（jieba.load_userdict 或 add_word），
   应用 stopwords 过滤；匹配改为「分词后命中词典」而非子串。
```

**完成标准**：脚本用 jieba 分词；stopwords 生效；三脚本仍可复现、输出不含原文。
**测试**：`python analysis/text_analysis/build_text_features.py --output outputs/text_analysis/text_features_summary.json`（有种子数据时命中词非空）。

### T11-16 让 JSON 词典真正生效（消除死文件）

**目标**：删除硬编码词典，改为启动时加载 dictionaries/*.json，消除双份维护。

**当前代码事实**：
```text
analyze_text_sources.py:37-70  硬编码 EMOTION_KEYWORDS/INTENSITY_KEYWORDS/NODE_KEYWORDS。
dictionaries/*.json（emotion/scene/person/behavior/stopwords）从未被任何脚本读取（死文件）。
```

**必须改动**：
```text
1. 删除 :37-70 硬编码；新增 load_dictionaries() 从 dictionaries/emotion_terms.json/scene_terms.json/person_terms.json/
   behavior_terms.json/stopwords.json 读入，供三脚本共用。
2. 词典结构对齐情感计算需要（词→类别/极性/强度；见 T11-17）。缺文件时报清晰错误，不静默回退硬编码。
```

**完成标准**：词典唯一来源为 JSON；改词无需改 .py；脚本可复现。
**测试**：改 emotion_terms.json 加一词→输出统计随之变化。

### T11-17 引入情感本体 + 真 valence/arousal 映射

**目标**：引入验证过的情感词库（大连理工情感本体 DLUT / BosonNLP），做真实 valence/arousal 聚合，替换写死字符串。

**当前代码事实**：
```text
build_text_features.py:32-33  valence_hint/arousal_hint = 写死字符串 "aggregate_only"。
现 emotion 词典仅 16 词/8 类（占位级）。
```

**必须改动**：
```text
1. 引入 DLUT 情感词汇本体（7 大类/21 小类 + 极性 polarity + 强度 intensity）或 BosonNLP：
   - 在 dictionaries/ 放入转换后的词表；若原始词库许可证不允许入仓，则只放小样本 + README 注明获取方式，由用户放置完整表。
   - README 写明来源、许可证、脱敏与不入仓约束。
2. build_text_features.py：valence = mean(polarity_sign × intensity)；arousal = mean(intensity 按 类别加权)；
   仍只输出聚合值（不出原文、不出个体标签）。analysis_version 升级。
```

**完成标准**：valence/arousal 为真实聚合数值而非固定字符串；词库规模显著扩大；输出聚合脱敏。
**测试**：种子数据下 valence/arousal 数值合理（正/负文本方向正确）。

### T11-18 真社会网络指标（networkx）

**目标**：共现网络补真实图指标，top 节点按中心性而非频次。

**当前代码事实**：
```text
build_social_network.py:41-47  输出 nodes/edges/top_nodes/top_edges/*_emotion_pairs，仅原始共现权重，无图指标。
analyze_text_sources.py:158-162  记录内两两建边。
```

**必须改动**：
```text
1. 用 networkx 建图，计算 度中心性/介数中心性/特征向量中心性 + 社区发现（Louvain 或 greedy_modularity_communities）。
2. top_nodes 按中心性排序；边权归一化；可选按时间窗切分。
3. 输出仍为聚合共现 + 指标，无原句。
```

**完成标准**：输出含中心性与社区划分；top 节点按中心性；无原文。
**测试**：`python analysis/text_analysis/build_social_network.py --output outputs/text_analysis/social_network_summary.json`（有数据时指标非空）。

### T11-19 对接情绪反射弧框架

**目标**：把扁平共现升级为情绪反射弧链条结构，支持「诱因→反应→结果」模式挖掘。

**当前代码事实**：
```text
节点类型现为扁平 person/scene/behavior/emotion。
项目有情绪反射弧框架：诱因/应激源 → 想法 → 身体感觉/情绪 → 行为/反应 → 结果。
```

**必须改动**：
```text
1. 词典类别映射到反射弧节点（诱因/想法/身体感觉/情绪/行为/结果）；
   共现边标注链条方向段（如 诱因-情绪、情绪-行为），而非无向扁平。
2. 输出 scene_emotion/person_emotion/behavior_emotion 之外，增 反射弧链条聚合（trigger→reaction→outcome 计数）。
```

**完成标准**：网络承载反射弧链条结构；输出可读出「诱因→反应→结果」聚合；仍聚合脱敏。
**测试**：种子数据下链条聚合计数正确。

### T11-20 只读研究报告面 + 文本来源清单补列

**目标**：离线脚本验证通过后，提供只读研究报告接口（管理员/研究者鉴权），并补齐文本来源清单字段列。

**当前代码事实**：
```text
无 backend/services/text_analysis_service.py / backend/routes/text_analysis.py（离线，符合规格）。
docs/02_专项进度与验收/任务十文本来源清单.md 编目 9 源，但「是否敏感/是否默认导出/是否脱敏」未独立成列。
analyze_text_sources.py 的 TEXT_SOURCES 元组（约 :25-35）含 sentiment_ok/network_ok 布尔。
```

**必须改动**：
```text
1. 仅在三脚本可复现且用户确认权限后，新增 backend/services/text_analysis_service.py + backend/routes/text_analysis.py：
   只读端点，读 outputs/text_analysis/*.json 聚合（无原文），require_role 管理员/研究者；普通用户端不接。
   如需 Web 后台展示，同步 shared 端点与 safehomeApi.ts；第一版最多展示简化摘要。
2. docs/02_专项进度与验收 文本来源清单（改为任务十一版）：加独立列 是否敏感/是否默认导出/是否脱敏/可用于情感计算/可用于SNA，
   与 TEXT_SOURCES 元组字段逐一对齐。
```

**完成标准**：只读端点鉴权正确、无原文外泄；清单列与代码字段对齐；离线→验证→接入的门槛在执行记录写明。
**测试**：`python -m pytest backend/tests -q`（补：非管理员访问 text-analysis → 401/403；返回不含原文）。

---

## T11-21 验收与留痕

**必须运行**：
```powershell
cd D:\codex\workspace\safehome1.0
python backend\scripts\validate_content.py
python backend\scripts\build_worksheets.py
python backend\scripts\audit_assessment_content.py
cd backend; python -m pytest tests -q
cd ..\apps\web; npm run build   # 若改动 Web
cd ..\..
Get-ChildItem apps\miniprogram -Recurse -Filter *.js  | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
python analysis\text_analysis\build_text_features.py --output outputs\text_analysis\text_features_summary.json
python analysis\text_analysis\build_social_network.py --output outputs\text_analysis\social_network_summary.json
```

**必须人工验收（真机）**：
```text
温度计呈温度计造型、可点/拖设值；测一测选项窄屏可读；最近记录可点、有画像有徽标；
未登录进入填写类页面被拦截并跳登录；训练卡无「练习前先提醒自己」；
PHQ-9 标题干净、敏感量表用户端免责为正常文案；高风险内容不进普通训练推荐。
```

**必须留痕**：
```text
docs/02_专项进度与验收/任务十一执行记录_YYYYMMDD.md（逐子任务证据 + 已跑/未跑验证 + 原因）
docs/02_专项进度与验收 文本来源清单（任务十一补列版）
docs/00_当前事实基准/{开发日志.md,当前进度交接.md,开发说明.md}
docs/03_技术真相/{数据库字段说明.md,数据字典.md,API接口文档.md}（如字段/API 有改动）
docs/10Claude协作/Claude使用记录.md（仅实际使用 Claude/Claude Code 时）
```

**任务十一状态表（执行者回填）**：
```text
| 子任务 | 状态(已完成/部分/无需修改/待人工) | 证据(file:line) | 已跑验证 | 备注 |
| T11-01 去「练习前先提醒自己」 | | | | |
| T11-02 差异化指导语 | | | | |
| T11-03 温度计造型 | | | | |
| T11-04 最近记录可点+徽标+未登录 | | | | |
| T11-05 全局登录守卫 | | | | |
| T11-06 supervision 权限+回退收紧 | | | | |
| T11-07 清用户端泄漏字段 | | | | |
| T11-08 训练地图补全 | | | | |
| T11-09 训练卡 prompt 去重 | | | | |
| T11-10 真波动/收束 | | | | |
| T11-11 动态推荐吃反馈 | | | | |
| T11-12 训练卡效用前后测 | | | | |
| T11-13 课程真接入 | | | | |
| T11-14 本周复盘契约+持久化 | | | | |
| T11-15 jieba 分词 | | | | |
| T11-16 词典真加载 | | | | |
| T11-17 情感本体+VA映射 | | | | |
| T11-18 真 SNA 指标 | | | | |
| T11-19 对接情绪反射弧 | | | | |
| T11-20 只读研究报告面+清单补列 | | | | |
```

# 任务十二：补录量表验收 · 数据1题项级亲密关系画像 · 治疗性评估赋能闭环

> 本轮定位：任务十二不是旧版计划的微调，而是按用户 2026-07-10 新计划重写。先删除旧任务十二，再写入本任务。任务十二要完整覆盖：老任务补录 12 量表人工验收与补齐、全量量表题项/选项/计分一致性审核、`数据1` 题项映射与题项级聚类画像、三份亲密关系量表录入小程序、治疗性评估第二阶段智能导入与初筛报告、研究者登录和评估仪表盘、线上评估工具雏形、连续施测与成长仪表盘、知识星球站内替代方案，以及最终自动化验证和代码审查。

## 0. Context（为什么重写任务十二）

用户给出的新任务十二来源包含 8 条工作线：

```text
0. 老任务：补录12量表人工验收表中的量表仍有题项、选项、计分规则、反向题、维度归属等需要人工审核和补齐。
1. 数据1：原始量表.xlsx 有完整题项得分；全部数据1.0.xlsx 只保留缩写题项；需要建立缩写与原题项映射并改造成聚类准备数据。
2. 数据1：三份量表按既有三类归类、录入小程序，并按同一量表题项得分分别做潜剖面/聚类画像。
3. 治疗性评估：第二阶段报名后自动导入测一测完整数据、画像、维度、雷达和描述，并生成关系健康初筛报告。
4. 研究者赋能：我的页新增研究者登录入口，登录后释放评估仪表盘。
5. 线上评估工具：关系隐喻互动绘画、句子补全、治疗性反馈会议材料整理。
6. 连续施测：在项目试点-亲密关系中实现情境化补充测量、开放式叙事采集；在个人中心实现变化曲线、成长时间轴、成长报告。
7. 用户画像逻辑：参考 3-1 和 3-2，把基础画像、矛盾画像、机制画像、动态画像落实到项目试点-亲密关系板块。
8. 知识星球：提出站内简易替代方案，并从产品开发角度写清楚。
```

必须使用和对齐的本地材料：

```text
D:\桌面\Desktop\补录12量表人工验收表.xlsx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\2026年6月18日发给董俊杰的(1)\测评问卷-量表
D:\codex\workspace\safehome1.0其他内容\夏老师文件\数据1\原始量表.xlsx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\数据1\全部数据1.0.xlsx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\数据1\清洗好的469份.xlsx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\数据1\问卷计分算分说明书.docx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\数据1\数据分析最终整理稿_N469.docx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\260706发给董俊杰\2 小程序如何赋能MVP.docx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\260706发给董俊杰\3-1 基于大样本调研构建用户画像的思路.docx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\260706发给董俊杰\3-2 【结合用户画像】小程序如何赋能MVP.docx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\260706发给董俊杰\4 连续多次施测的核心思路.docx
D:\codex\workspace\safehome1.0其他内容\夏老师文件\2026年6月18日发给董俊杰的(1)\「安心陪伴小程序×知识星球」用户无缝体验设计的完整方案.docx
```

已确认的数据事实：

```text
1. 补录12量表人工验收表.xlsx 的验收总览含 12 个量表。
2. 原始量表.xlsx 第一行包含完整题干，含基本信息、调节聚焦 18 题、Micro YSQ-18、亲密关系启动意向与主动行为题项、开放题。
3. 全部数据1.0.xlsx 使用缩写列：Q1-Q18、YSQ1-YSQ18、a1/b1-a5/b5、SN1-SN4、PBC1-PBC6、BI1-BI6、RAP1-RAP5，并已有部分维度列。
4. 清洗好的469份.xlsx 是清洗后的维度分表，可用于维度复算和聚类解释交叉验证。
5. 数据1 聚类不能只停留在维度层；本任务要求先抽出同一个量表的题目得分，再对每一个量表题项得分做聚类/潜剖面分析。维度层结果用于交叉验证和报告解释。
```

## 0A. 总执行口径（优先级最高）

1. 必须先删除旧任务十二，再写入本任务十二；旧任务十二不再作为执行依据。
2. 本任务十二不是“最小改动”，而是完整承接用户 0-8 条计划。
3. 能自动化的部分必须自动化：文件读取、题项抽取、缩写映射、题项数量核对、选项结构核对、计分字段核对、画像建模、内容校验、测试、构建和文档检索。
4. 不能自动化替代的部分必须明确写成人工验收点：量表授权、题项原文逐字核对、敏感量表开放边界、画像命名、研究者洞察提示、反馈会议最终内容。
5. 所有量表补齐必须遵守既有录入规则，不另造一套量表结构。
6. `数据1` 三份量表分类不得超过既有三类：
   ```text
   基于情绪反射弧的分类
   家长自主量表
   学生自助量表
   ```
7. `数据1` 三份量表建议统一归入“学生自助量表”，并标注为“大学生亲密关系探索试点”；不得混入家长陪伴主线文案。
8. 潜剖面/聚类画像必须按量表分别建模：调节聚焦、Micro YSQ-18、亲密关系启动意向与主动行为问卷分别输出模型和画像解释；可以另做整合画像，但不能替代分量表画像。
9. 聚类方法先比较再选择，默认以 GaussianMixture 作为 LPA 风格实现，KMeans/PCA 作为现有展示兼容与对照。
10. 画像输出必须复用现有 `content/profiles/*.json`、`profile_model_id`、`/api/assessment-results/<id>/profile-position`、雷达图、画像点位和训练推荐链路。
11. 治疗性评估用户端文案优先使用“支持性评估”“探索式反馈”“关系探索”“成长报告”，避免直接承诺治疗效果。
12. 研究者仪表盘可以给“数据洞察提示”和“评估问题建议”，但不得输出诊断、人格定性、病理判断或危机处置替代意见。
13. 原始逐行数据、开放文本原文、绘画原件、句子补全原文默认不入仓；只允许脚本、脱敏聚合结果、画像模型 JSON、文档记录入仓。
14. 本任务每完成一个阶段必须更新执行记录，不能等全部完成后一次性补写。

## 0B. 必须同步更新的文档

只要本任务发生代码、content、数据库、接口、前端、脚本或文档变更，必须同步更新：

```text
docs/00_当前事实基准/开发日志.md
docs/00_当前事实基准/当前进度交接.md
docs/00_当前事实基准/开发说明.md
docs/00_当前事实基准/项目进度统一口径.md
```

涉及 API、数据库或字段时还必须更新：

```text
docs/03_技术真相/API接口文档.md
docs/03_技术真相/数据库字段说明.md
docs/03_技术真相/数据字典.md
```

任务十二专项产物统一放在：

```text
docs/02_专项进度与验收/任务十二执行记录_YYYYMMDD.md
docs/02_专项进度与验收/任务十二补录12量表审核矩阵.md
docs/02_专项进度与验收/任务十二补录12量表本地来源抽取表.md
docs/02_专项进度与验收/任务十二量表外部来源检索记录.md
docs/02_专项进度与验收/任务十二全量量表题项选项计分审核.csv
docs/02_专项进度与验收/任务十二数据1题项缩写映射表.md
docs/02_专项进度与验收/任务十二数据1量表拆分与分类表.md
docs/02_专项进度与验收/任务十二数据1聚类方法选择报告.md
docs/02_专项进度与验收/任务十二聚类解释交叉验证报告.md
docs/02_专项进度与验收/任务十二治疗性评估产品方案.md
docs/02_专项进度与验收/任务十二研究者仪表盘方案.md
docs/02_专项进度与验收/任务十二知识星球站内替代方案.md
docs/02_专项进度与验收/任务十二代码审查.md
```

---

## S0 · 前置状态与旧任务收口

### T12-00 回填任务十一状态表

**目标**：先处理用户此前追加的要求，检查并回填 `Claude计划模式.md` 中任务十一状态表。

**自动化动作**：

1. 读取：
   ```text
   docs/02_专项进度与验收/任务十一执行记录_20260706.md
   docs/02_专项进度与验收/任务十一文本来源清单.md
   docs/00_当前事实基准/项目进度统一口径.md
   docs/00_当前事实基准/当前进度交接.md
   ```
2. 用 `rg` 定位任务十一执行证据和验证命令。
3. 回填 T11-01 到 T11-20 的状态、证据、验证和备注。
4. 对编号语义不完全一致的条目，在备注中写明映射关系。

**人工验收点**：

1. 任务十一是否仍需微信开发者工具/真机验收。
2. 云端部署和真实数据质量复核是否仍未完成。

**产出文件/代码落点**：

```text
docs/00_当前事实基准/Claude计划模式.md
```

**完成标准**：任务十一状态表不再为空，每行都有状态、证据、验证和备注。

### T12-01 删除旧任务十二并建立新版任务十二执行记录

**目标**：删除旧任务十二，写入本任务十二，并建立执行记录。

**自动化动作**：

1. 在 `Claude计划模式.md` 中定位第一个 `# 任务十二：`。
2. 删除该标题到文件末尾的旧任务十二内容。
3. 写入本任务十二全文。
4. 创建或追加当天执行记录：
   ```text
   docs/02_专项进度与验收/任务十二执行记录_YYYYMMDD.md
   ```
5. 在执行记录中写明：旧任务十二已废止，以新版任务十二为准。

**人工验收点**：确认任务十一和任务十一状态表没有被误删。

**完成标准**：`rg -n "# 任务十二|T12-00|T12-30|自动化动作|人工验收点" docs/00_当前事实基准/Claude计划模式.md` 可检索到新版结构；旧任务十二标题不再出现。

---

## S1 · 补录12量表自动化审核与补齐

### T12-02 读取补录12量表人工验收表并生成审核矩阵

**目标**：以 `D:\桌面\Desktop\补录12量表人工验收表.xlsx` 为唯一补录 12 量表清单。

**自动化动作**：

1. 读取 `验收总览` sheet。
2. 抽取字段：量表ID、量表名称、来源文件夹、来源文件、预期题项数、草稿题项数、小程序题项数、敏感类别。
3. 生成补录 12 量表审核矩阵。

**必须覆盖的 12 个量表**：

```text
big_five_bfi_60
sleep_isi_psqi
attribution_style_student_36
ghq12_general_health
epq_emotional_stability_24
phq9_cesd10_depression
gad7_anxiety
perceived_social_support_psss
cognitive_curiosity_student
emotional_intelligence_eis_33
family_cohesion_adaptability
parental_autonomy_support
```

**人工验收点**：确认 Excel 清单是否为最新人工验收表；如果用户更新表格，需重新读取。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二补录12量表审核矩阵.md
```

**完成标准**：12 个量表全部列出，且每个量表都有当前状态、来源文件夹、缺口类型和下一步动作。

### T12-03 本地源文件自动查找与题项抽取

**目标**：先从本地 `测评问卷-量表` 文件夹查找缺失题项、选项、计分规则、反向题和维度。

**自动化动作**：

1. 按 `补录12量表人工验收表.xlsx` 的来源文件夹定位本地目录。
2. 对 `.docx` 使用文档文本抽取。
3. 对 `.xlsx` 读取 sheet、表头、题项列和计分列。
4. 对 `.pdf` 使用 PDF 文本抽取；扫描版或不可读 PDF 标记为“需人工打开”。
5. 将抽取结果与 `content/assessment_worksheets.json`、`content/scale_item_drafts.json`、`content/scales_catalog.json` 对照。
6. 自动标记：题项数一致/不一致、题项为空、选项为空、反向题缺失、维度缺失、计分规则缺失、边界文案缺失。

**人工验收点**：

1. 题项原文逐字一致性。
2. 版权/授权状态。
3. 扫描 PDF 或旧 `.doc` 中无法可靠抽取的题项。
4. 敏感筛查量表是否适合用户端开放。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二补录12量表本地来源抽取表.md
```

**完成标准**：每个补录量表都能说明“本地已找到什么、还缺什么、是否能自动补齐、什么必须人工验收”。

### T12-04 外部来源检索与补齐记录

**目标**：本地文件仍缺失时，才进行联网检索并登记来源。

**自动化动作**：

1. 对缺题项或缺计分规则的量表逐个建立检索项。
2. 优先检索正式量表、论文、机构说明、作者公开材料。
3. 记录来源标题、URL、检索日期、可用字段、风险说明。
4. 不可靠来源只作为线索，不直接写成“已确认”。

**人工验收点**：

1. 来源版本是否与项目使用量表一致。
2. 中文译文是否可靠。
3. 公开来源是否允许项目内使用。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二量表外部来源检索记录.md
```

**完成标准**：所有外部补齐内容都有来源；没有来源的内容必须标记“待人工复核”，不得臆造。

### T12-05 补齐补录12量表 content、后端、前端、数据库链路

**目标**：对来源合适且已可补齐的量表，按既有量表录入规则补齐链路。

**自动化动作**：

1. 更新或生成：
   ```text
   content/scale_item_drafts.json
   content/assessment_worksheets.json
   content/scales_catalog.json
   content/assessment_training_map.json
   ```
2. 同步后端构建和数据库导入：
   ```powershell
   python backend/scripts/build_worksheets.py
   python backend/scripts/import_worksheets_to_db.py
   ```
3. 如字段不够承载，先补数据库字段说明和迁移方案，再改模型。
4. 同步 `shared/types/api.ts`、`shared/constants/api.ts`。
5. 同步小程序测一测列表、详情、结果页展示。
6. 同步 Web 后台内容查看、测评结果、画像/报告查看入口。

**人工验收点**：

1. 题项、选项、计分、反向题和维度是否与源文件一致。
2. 高敏感量表是否只做支持性反馈，不做诊断/筛查结论。
3. 是否应先隐藏入口而不是开放用户填写。

**完成标准**：可补齐量表在 content、后端、数据库、小程序、Web 上结构一致；不可补齐量表保留明确缺口和人工验收原因。

---

## S2 · 全量量表题项/选项/计分一致性审核

### T12-06 对所有量表进行题目、选项、计分规则审核

**目标**：不只审核补录 12 量表，还要对当前所有已录入小程序的量表做一致性审核，使其尽量与 Word/PDF/Excel 来源一致。

**自动化动作**：

1. 扫描 `content/assessment_worksheets.json` 全部 worksheets。
2. 对每个 worksheet 输出：题项数、选项数、空选项数、长选项数、反向题数、维度数、scoring 是否为空、source_file 是否为空、review_status。
3. 与 `content/scale_item_drafts.json`、`content/scales_catalog.json` 和本地源文件可抽取结果比对。
4. 生成 CSV 审核表。
5. 对明显结构问题自动补充：缺 source_file、缺 review_note、缺 boundary_notice、计分文本缺“需人工复核”说明。

**人工验收点**：

1. 题干逐字一致性。
2. 选项分值方向。
3. 反向计分方向。
4. 维度归属。
5. 敏感量表边界和是否开放。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二全量量表题项选项计分审核.csv
```

**完成标准**：所有量表都有审核状态；结构性缺口已自动标出；需要人工验收的内容不被误标为完成。

---

## S3 · 数据1题项映射与聚类数据准备

### T12-07 建立原始题项与缩写列映射

**目标**：把 `全部数据1.0.xlsx` 中的缩写列映射回 `原始量表.xlsx` 中完整题干。

**自动化动作**：

1. 读取 `原始量表.xlsx` 第一行完整题干。
2. 读取 `全部数据1.0.xlsx` 第一行缩写列。
3. 建立映射：
   ```text
   Q1-Q18 -> 调节聚焦 18 题
   YSQ1-YSQ18 -> Micro YSQ-18
   a1/b1-a5/b5 -> 亲密关系结果信念与威胁/保护题
   SN1-SN4 -> 主观规范题
   PBC1-PBC6 -> 知觉行为控制题
   BI1-BI6 -> 行为意向题
   RAP1-RAP5 -> 关系主动性实践题
   @11/@12 -> 开放题
   ```
4. 生成题项缩写映射表。
5. 在映射表中记录每一题的量表归属、题号、原题干、缩写列、分值范围、是否用于聚类。

**人工验收点**：

1. `a1/b1` 顺序是否应按原问卷显示为 `1a/1b`。
2. 开放题是否只进入叙事材料，不进入自动聚类。
3. 题项原文是否需要按问卷 docx 再复核一次。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二数据1题项缩写映射表.md
```

**完成标准**：`全部数据1.0.xlsx` 中所有题项缩写列都能追溯到原题干和量表归属。

### T12-08 生成题项级聚类输入矩阵与维度复算表

**目标**：为潜剖面/聚类分析准备题项级数据，而不是只用维度分。

**自动化动作**：

1. 从 `全部数据1.0.xlsx` 抽取三份量表的题项得分矩阵。
2. 按 `问卷计分算分说明书.docx` 复算维度：
   ```text
   PROM = MEAN(rf3, rf5, rf6, rf8, rf12, rf14, rf16, rf17, rf18)
   PREV = MEAN(rf1, rf2, rf4, rf7, rf9, rf10, rf11, rf13, rf15)
   RFD = PROM - PREV
   EMS_M = MEAN(ysq1:ysq18)
   EMS_SUM = SUM(ysq1:ysq18)
   REL_SCHEMA = MEAN(1,2,3,4,5,8,9,13,14,18)
   BENEFIT = MEAN(a1*b1, a2*b2, a3*b3)
   REJ_THREAT = a4*b4
   AUTH_THREAT = a5*b5
   AUTH_PROTECT = MEAN(6-a5, b5)
   THREAT = MEAN(REJ_THREAT, AUTH_THREAT)
   SN = MEAN(SN1:SN4)
   PBC = MEAN(PBC1:PBC6)
   BI = MEAN(BI1:BI6)
   RPP/RAP = MEAN(RAP1:RAP5)
   ```
3. 与 `清洗好的469份.xlsx` 中 PF、PrF、PF_PrF、YSQ、BE、TE、RP、SN、PBC、BI、RPP、ATT 等列做交叉验证。
4. 输出差异报告，说明是否存在样本过滤、列名差异或公式差异。

**人工验收点**：

1. 维度公式是否完全符合计分说明。
2. `全部数据1.0.xlsx` 样本数与清洗数据样本数差异原因。
3. 是否需要排除作答时间异常、缺失过多或非目标人群样本。

**产出文件/代码落点**：

```text
analysis/profiling/build_task12_relationship_dataset.py
outputs/task12_relationship_profiles/README.md
outputs/task12_relationship_profiles/item_mapping_preview.csv
outputs/task12_relationship_profiles/dimension_validation_summary.json
```

**完成标准**：三份量表均有题项级矩阵；维度复算差异可解释；逐行原始数据不入仓。

---

## S4 · 数据1三份量表录入小程序

### T12-09 数据1三份量表拆分与三类归属

**目标**：把 `数据1` 的内容拆为三份可录入小程序的量表单元，并归入既有三类。

**自动化动作**：

1. 读取 `单身大学生亲密关系启动意向与主动行为调查问卷1.0(1).docx` 和 `原始量表.xlsx`。
2. 拆分为：
   ```text
   regulatory_focus_relationship_18：调节聚焦 18 题
   micro_ysq_relationship_18：Micro YSQ-18
   relationship_initiation_intention_action：亲密关系启动意向与主动行为问卷
   ```
3. 分类统一写为“学生自助量表”。
4. 在 review_note 中标注“大学生亲密关系探索试点，非家长陪伴主线”。

**人工验收点**：确认三份量表是否都应放入“学生自助量表”，不新增第四类。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二数据1量表拆分与分类表.md
```

**完成标准**：三份量表 ID、题项范围、计分范围、分类、是否开放、是否参与画像全部明确。

### T12-10 数据1三份量表 content、API、数据库、前端接入

**目标**：按既有量表录入规则，把三份量表接入小程序和 Web。

**自动化动作**：

1. 写入 `content/scale_item_drafts.json` 和 `content/assessment_worksheets.json`。
2. 写入 `content/scales_catalog.json`。
3. 写入或补充 `content/assessment_training_map.json`。
4. 运行：
   ```powershell
   python backend/scripts/build_worksheets.py
   python backend/scripts/import_worksheets_to_db.py
   python backend/scripts/validate_content.py
   ```
5. 如 API 字段不足，补充后端 route/service/model/shared 类型。
6. 小程序测一测列表、详情、结果页支持展示三份量表。
7. Web 后台支持查看三份量表、提交结果、画像落点和报告。

**人工验收点**：

1. 题项是否与原始问卷一致。
2. 计分是否与说明书一致。
3. 结果页文案是否非诊断、非标签化。

**完成标准**：三份量表可在本地小程序/接口链路中提交并保存，Web 能查看结果。

---

## S5 · 题项级潜剖面/聚类画像建模与接入

### T12-11 选择潜剖面/聚类方法

**目标**：先选择适合数据的聚类方法，再正式建模。

**自动化动作**：

1. 对三份量表分别尝试：
   ```text
   GaussianMixture：LPA 风格主方法
   KMeans：与项目既有聚类产物兼容的对照方法
   PCA：用于二维位置图和可视化，不作为画像本身
   ```
2. 输出 k=2 到 k=6 的指标：BIC、AIC、silhouette、最小簇比例、簇稳定性、解释可读性。
3. 若某量表题项分布不适合 GMM，则降级为 KMeans 并说明原因。

**人工验收点**：画像数量和名称必须由研究者复核，不能只按算法分数自动决定。

**产出文件/代码落点**：

```text
analysis/profiling/build_task12_relationship_profiles.py
docs/02_专项进度与验收/任务十二数据1聚类方法选择报告.md
```

**完成标准**：每份量表都有明确方法选择理由和可复现脚本。

### T12-12 分量表进行题项级聚类建模

**目标**：分别对三份量表的题项得分进行聚类，输出画像模型。

**自动化动作**：

1. 调节聚焦 18 题单独建模。
2. Micro YSQ-18 单独建模。
3. 亲密关系启动意向与主动行为题项单独建模。
4. 生成 `content/profiles/*.json`，复用现有画像模型 schema：
   ```text
   schema_version
   model_id
   scale_id
   worksheet_id
   n_cases
   n_features
   features
   preprocessing
   model_selection
   chosen_k
   clusters
   pca
   radar_support
   boundary_notice
   ```
5. 每个 cluster 写入：画像名、人数、比例、维度特征、支持性解释、雷达图维度、建议评估问题、推荐训练/项目任务。

**人工验收点**：画像命名和解释不得使用诊断、人格定性、病理化、关系能力高低评价。

**完成标准**：三份画像模型通过 `python backend/scripts/validate_content.py`。

### T12-13 用数据分析结果做聚类解释交叉验证

**目标**：用 `数据分析最终整理稿_N469.docx` 和清洗维度数据校验聚类解释。

**自动化动作**：

1. 提取或记录整理稿中的信度、描述统计、相关、回归、中介、调节结果。
2. 对每个画像簇检查：
   - PF/PrF/RFD 方向是否合理；
   - YSQ 与威胁、PBC、BI、RAP 的方向是否与已有分析一致；
   - BE、SN、PBC、BI、RAP 的高低解释是否过度；
   - 是否把探索性聚类误写成疗效证明。
3. 输出交叉验证报告。

**人工验收点**：统计解释和画像叙事需要研究者复核。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二聚类解释交叉验证报告.md
```

**完成标准**：任何冲突解释都被降级为“探索性，待人工复核”。

### T12-14 画像展示接入小程序和 Web

**目标**：让新画像像现有聚类画像一样展示。

**自动化动作**：

1. 在三份 worksheet 中绑定 `profile_model_id`。
2. 复用或扩展：
   ```text
   GET /api/assessment-results/<result_id>/profile-position
   backend/services/assessment_profile_service.py
   apps/miniprogram/pages/assessment-result/index.*
   apps/web 画像/测评结果相关页面
   ```
3. 小程序展示画像名、置信度、雷达图、维度解释、画像点位、建议评估问题和边界说明。
4. Web 展示模型信息、画像解释、雷达图、聚类摘要和人工复核入口。

**人工验收点**：画像显示不能暗示诊断、人格分类或关系能力评判。

**完成标准**：小程序和 Web 均可查看新画像，接口不返回训练样本逐行数据。

---

## S6 · 关系健康初筛报告与研究者消息发送

### T12-15 第二阶段报名后的测一测数据智能导入

**目标**：当用户通过问卷筛选并报名参加第二阶段时，后台自动调用其测一测完整数据。

**自动化动作**：

1. 设计第二阶段报名记录结构，可复用 `records` 或新增专表。
2. 报名后关联：
   ```text
   assessment_result_id
   worksheet_id
   profile_model_id
   profile_cluster_id
   dimensions
   radar_features
   profile_description
   user_id
   ```
3. 若用户无可用测一测结果，返回“需先完成测一测”。
4. 若结果需人工复核，报告状态标记为 `pending_review`。

**人工验收点**：用户授权、研究用途说明、用户数据隔离。

**完成标准**：第二阶段报名记录可以稳定找到对应测评结果和画像信息。

### T12-16 生成关系健康初筛报告

**目标**：小程序自动生成图文并茂的关系健康初筛报告。

**自动化动作**：

1. 报告内容至少包含：
   ```text
   测一测结果页面已有内容
   核心维度雷达图
   画像名称与支持性描述
   个性化解读
   预设评估问题建议
   推荐的项目试点任务
   非诊断边界说明
   生成时间和版本
   ```
2. 用户端支持查看和下载。
3. 研究者后台支持查询和下载。
4. 报告生成后记录审计日志。

**人工验收点**：报告文案是否过度解释；图文内容是否泄漏内部字段。

**产出文件/代码落点**：

```text
backend/routes/reports.py 或新增 reports/relationship_screening route
apps/miniprogram/pages/relationship-report/*
apps/web 研究者报告页面
```

**完成标准**：用户和研究者可分别在权限内查看/下载同一份报告。

### T12-17 研究者通过消息页发送报告

**目标**：研究者可以通过小程序消息页面把报告发送给用户。

**自动化动作**：

1. 复用现有消息机制或新增最小报告消息表。
2. 消息中只包含报告摘要和报告 ID，不直接暴露敏感原文。
3. 用户点击消息进入报告页。
4. 记录发送者、接收者、报告 ID、发送时间和读取状态。

**人工验收点**：防止报告误发给其他用户；研究者权限必须生效。

**完成标准**：研究者可发送，用户可接收，越权访问返回错误。

---

## S7 · 研究者登录、评估仪表盘、线上评估工具

### T12-18 我的页新增研究者登录入口

**目标**：在小程序“我的”页面设置研究者登录入口。

**自动化动作**：

1. 小程序“我的”页新增研究者入口。
2. 后端新增或复用账号登录接口，支持研究者角色。
3. 数据库记录 researcher/user 角色、登录时间、审计日志。
4. 普通用户不显示研究者数据。

**人工验收点**：研究者账号管理和密码/令牌策略是否符合试点要求。

**完成标准**：研究者登录后进入专属评估仪表盘，普通用户无法访问。

### T12-19 研究者评估仪表盘

**目标**：为研究者提供专属管理后台，记录用户档案和数据洞察提示。

**自动化动作**：

1. 仪表盘展示：
   ```text
   用户档案
   报名状态
   测一测结果
   聚类画像
   维度雷达
   预设评估问题
   线上任务完成情况
   初筛报告
   人工备注
   风险/复核状态
   ```
2. 数据洞察提示基于画像和维度生成，只作为访谈探索线索。
3. 研究者可新增备注，但不覆盖用户端原报告。

**人工验收点**：洞察提示不得写“依恋创伤已确定”“人格缺陷”“病理模式”等定性。

**完成标准**：研究者可查看用户档案、报告、画像、任务和备注；所有访问有审计。

### T12-20 关系隐喻互动绘画雏形

**目标**：实现 `2 小程序如何赋能MVP.docx` 中关系隐喻互动绘画的第一版。

**自动化动作**：

1. 在项目试点-亲密关系入口下新增绘画任务。
2. 支持简易绘图或图片上传。
3. 支持 1-2 句“画外音”说明。
4. 保存任务记录、说明文字、提交时间和用户授权。
5. 研究者仪表盘可查看该材料。

**人工验收点**：系统不得自动解释潜意识或象征意义；只能作为叙事材料。

**完成标准**：用户可提交，研究者可查看，原图按敏感材料处理。

### T12-21 句子补全交互雏形

**目标**：实现“如果……会怎样”句子补全任务。

**自动化动作**：

1. 设置情境模板：表白、争吵、冷战、靠近、边界表达、被拒绝、真实表达。
2. 用户填写句子补全内容。
3. 系统保存回答并可做关键词聚合，但不做诊断。
4. 研究者仪表盘可查看。

**人工验收点**：开放文本属于敏感叙事材料，默认不导出原文。

**完成标准**：句子补全可完成、保存、查看、纳入探索手记草稿。

### T12-22 治疗性反馈会议材料整理与探索手记草稿

**目标**：落实 `2 小程序如何赋能MVP.docx` 第 4 部分“重塑治疗性反馈会议”。

**自动化动作**：

1. 汇总问卷、画像、报告、绘画、句子补全、研究者备注。
2. 生成“个人关系叙事”草稿结构：
   ```text
   起点画像
   用户选择的评估问题
   重要维度线索
   线上任务材料
   研究者备注
   用户共同修订区
   下一步项目任务
   ```
3. 生成探索手记草稿，用户端只展示研究者确认后的版本。

**人工验收点**：反馈会议最终材料必须由研究者确认，不允许系统自动定稿。

**完成标准**：研究者能生成草稿、编辑备注、确认后交付用户。

### T12-23 项目试点-亲密关系入口接入

**目标**：把任务 3、3-1、3-2 的内容落到训练卡界面的项目试点-亲密关系板块中。

**自动化动作**：

1. 在训练卡界面的项目试点中增加亲密关系探索入口。
2. 入口下聚合：测一测结果、画像解释、评估问题、线上任务、初筛报告、连续施测入口。
3. 不强制使用普通训练卡形式；可使用项目任务、表单、报告、绘画和句子补全。

**人工验收点**：入口命名和文案是否适合大学生关系探索，不误导为治疗服务。

**完成标准**：用户可从训练卡/项目试点进入亲密关系板块并完成至少一个项目任务。

---

## S8 · 连续施测、成长仪表盘、知识星球替代、最终审查

### T12-24 实现情境化补充测量和开放式叙事采集

**目标**：落实 `4 连续多次施测的核心思路.docx` 第三章“施测内容：测些什么”。

**自动化动作**：

1. 在项目试点-亲密关系下新增补充测量：
   ```text
   本周主动社交次数
   本周真实表达次数
   遇到挫折后的应对方式
   当前关系靠近意愿
   当前担忧强度
   ```
2. 新增 1-2 个开放式叙事问题：
   ```text
   最近一周，关于亲密关系最有成就感的一件事是什么？
   最近一周，关于亲密关系最挫败的一件事是什么？
   ```
3. 事件触发式记录支持绑定到时间轴。

**人工验收点**：开放题是否需要人工复核；风险词是否进入风险预检。

**完成标准**：补充测量和开放叙事可保存，并能进入成长时间轴。

### T12-25 个人中心成长仪表盘、变化曲线、时间轴和成长报告

**目标**：落实 `4 连续多次施测的核心思路.docx` 第四章“数据整合与叙事呈现”。

**自动化动作**：

1. 在小程序“我的/个人中心”新增成长仪表盘入口。
2. 展示核心维度变化曲线。
3. 展示个人成长时间轴，包含：测评、项目任务、关键事件、报告、研究者反馈。
4. 生成成长报告页，包含：变化摘要、最重要事件、用户自我叙事、下一步建议。

**人工验收点**：成长报告不得写成疗效证明，只能写“变化记录”和“探索线索”。

**完成标准**：个人中心可查看成长仪表盘、时间轴和成长报告。

### T12-26 用户画像核心逻辑建议与落地

**目标**：参考 `3-1 基于大样本调研构建用户画像的思路.docx` 和 `3-2 【结合用户画像】小程序如何赋能MVP.docx`，对现有画像提出建议并落实到亲密关系项目试点。

**自动化动作**：

1. 将画像逻辑拆为四层：
   ```text
   基础画像：用户是谁，群体分布和基础维度。
   矛盾画像：高意向-低行动、高恐惧-低自我价值等张力。
   机制画像：可能影响行动和靠近的机制线索。
   动态画像：连续施测后的变化轨迹。
   ```
2. 将四层画像映射到报告、研究者仪表盘、评估问题和项目任务。
3. 将画像命名改写为阶段性、可改变、支持性名称。

**人工验收点**：机制画像不得过度理论化，不得把探索假设写成事实。

**完成标准**：亲密关系项目试点中能看到画像-评估问题-线上任务-成长报告的闭环。

### T12-27 知识星球简易替代方案

**目标**：针对知识星球方案提出站内可开发替代方案。

**自动化动作**：

1. 阅读并摘取知识星球方案能力：账号衔接、内容继续、提醒、搜索、奖励、资源、社群、隐私。
2. 设计站内替代：
   ```text
   站内资源包 -> content/courses.json / programs.json
   打卡营 -> checkins / program entries
   报告与消息 -> messages / reports
   人工支持 -> supervision / researcher dashboard
   搜索与推荐 -> 画像和任务推荐
   ```
3. 写出产品开发方案和后续可选升级路径。

**人工验收点**：当前不做外部平台深度同步，不传用户敏感数据到知识星球。

**产出文件/代码落点**：

```text
docs/02_专项进度与验收/任务十二知识星球站内替代方案.md
```

**完成标准**：方案能指导后续开发，不依赖知识星球 API 也能完成 MVP 闭环。

### T12-28 自动化验证

**目标**：任务十二实现后跑完整验证。

**必须执行**：

```powershell
python backend/scripts/validate_content.py
python backend/scripts/build_worksheets.py
python backend/scripts/audit_assessment_content.py
python analysis/profiling/build_task12_relationship_dataset.py
python analysis/profiling/build_task12_relationship_profiles.py
python -m pytest backend/tests -q
Get-ChildItem apps\miniprogram -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
Get-ChildItem apps\miniprogram -Recurse -Filter *.json | ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null }
cd apps\web
npm run build
```

**人工验收点**：微信开发者工具、真机、研究者权限、报告下载、绘画/句子补全体验仍需人工验收。

**完成标准**：能跑的自动化全部通过；不能跑的写明原因和替代验证。

### T12-29 文档同步

**目标**：完成任务十二每阶段后的文档同步。

**自动化动作**：

1. 更新四份事实基准文档。
2. 更新 API、数据库字段、数据字典。
3. 更新专项执行记录和状态表。
4. 如果实际使用 Claude/Claude Code，再更新 `docs/10Claude协作/Claude使用记录.md`。

**完成标准**：下一轮只读交接文档即可知道任务十二做到哪一步。

### T12-30 最终代码审查

**目标**：任务十二实现后进行代码审查。

**审查重点**：

1. 量表题项是否误录、漏录、题序错位。
2. 选项分值和反向题是否错误。
3. 计分规则是否与 Word/PDF/Excel 来源冲突。
4. `数据1` 原始逐行数据是否误入仓。
5. 聚类画像是否诊断化、人格化、病理化。
6. 画像模型 features 是否能关联真实 worksheet question id。
7. 研究者接口是否缺权限或缺审计。
8. 报告是否可越权下载。
9. 消息发送是否可能误发。
10. 绘画、句子补全、开放叙事是否泄漏原文。
11. 小程序和 Web 是否形成两套不一致字段。
12. 测试是否覆盖量表、画像、报告、研究者权限和成长仪表盘。

**完成标准**：输出 `docs/02_专项进度与验收/任务十二代码审查.md`；发现 P0/P1 问题时必须先修复再标完成。

---

## T12 状态表（执行者回填）

```text
| 子任务 | 状态(已完成/部分/无需修改/待人工) | 自动化动作 | 人工验收点 | 证据(file:line) | 已跑验证 | 备注 |
| T12-00 回填任务十一状态表 | 已完成 | 按任务十一执行记录逐项映射，回填 T11-01 至 T11-20 状态、证据、验证和备注。 | 核对未把真机/云端验收误写为已完成。 | docs/00_当前事实基准/Claude计划模式.md:8208 | rg 检查任务十一状态表不再为空。 | 任务十一编号在执行记录和计划表中有语义错位，本次按计划小项内容映射回填。 |
| T12-01 删除旧任务十二并建立新版执行记录 | 已完成 | 新版T12-00至T12-30执行并建立专项记录。 | 核对旧任务十二只作历史留痕。 | docs/02_专项进度与验收/任务十二执行记录_20260710.md:1 | 状态表和执行记录存在。 | 未恢复旧版任务十二。 |
| T12-02 读取补录12量表人工验收表 | 已完成 | 程序读取xlsx并确认12个唯一量表ID。 | 人工确认清单仍为权威版本。 | docs/02_专项进度与验收/任务十二补录12量表审核矩阵.md:1 | test_task12_scale_audit通过。 | 8份完整，4份缺口。 |
| T12-03 本地源文件查找与题项抽取 | 已完成 | 核对本地目录、draft、worksheet和源文件。 | 题项逐字与授权仍需量表负责人。 | docs/02_专项进度与验收/任务十二补录12量表本地来源抽取表.md:1 | 来源审核脚本通过。 | 不把文件存在等同于可开放。 |
| T12-04 外部来源检索与补齐记录 | 已完成 | 仅对4个缺口检索正式来源与授权线索。 | 申请许可并确认中文版本。 | docs/02_专项进度与验收/任务十二量表外部来源检索记录.md:1 | 正式来源逐项记录。 | 未复制受限题项。 |
| T12-05 补齐12量表 content/API/数据库/前端链路 | 部分 | 8份已有结构链路；4份保持metadata_only和隐藏。 | 4份需授权、版本、题项与计分确认。 | docs/02_专项进度与验收/任务十二补录12量表审核矩阵.md:1 | 内容校验通过。 | 自动化不能合法替代人工补录。 |
| T12-06 全量量表一致性审核 | 已完成 | 审核30份worksheet题项、选项、反向、维度、来源和边界。 | 量表负责人逐字复核。 | docs/02_专项进度与验收/任务十二全量量表题项选项计分审核.csv:1 | count=30，structural_gap_count=0。 | 自动结构审计完成。 |
| T12-07 数据1题项缩写映射 | 已完成 | 建立69列原题、缩写和来源列映射。 | 核对PBC和量尺版本冲突。 | docs/02_专项进度与验收/任务十二数据1题项缩写映射表.md:1 | mapping_count=69。 | 不含开放文本原文。 |
| T12-08 题项级聚类输入矩阵与维度复算 | 已完成 | 生成425×18、425×18、425×31私有矩阵和聚合校验。 | 研究者确认冻结公式。 | outputs/task12_relationship_profiles/README.md:1 | raw_text_included=false。 | 私有NPZ已gitignore。 |
| T12-09 数据1三份量表拆分与分类 | 已完成 | 三份均归学生自助，明确题项、量尺、开放和画像。 | 生产开放前确认文案。 | docs/02_专项进度与验收/任务十二数据1三份量表分类与开放边界.md:1 | 内容审计通过。 | 未新增第四类。 |
| T12-10 数据1三份量表接入小程序/Web | 已完成 | content、DB、API、小程序、Web填写和结果链路接通。 | 开发者工具和真机提交。 | backend/tests/test_assessments_route.py:327 | 相关接口测试、Web build通过。 | 关系量表无诊断性总分。 |
| T12-11 聚类方法选择 | 已完成 | 比较GMM/KMeans k2-6，PCA仅可视化。 | 研究者审核k。 | docs/02_专项进度与验收/任务十二数据1聚类方法选择报告.md:1 | 脚本可复现。 | 选GMM k=3/4/2。 |
| T12-12 分量表题项级聚类建模 | 已完成 | 生成3个脱敏聚合模型和支持性解释。 | 审核画像名、问题和任务。 | content/profiles/task12_regulatory_focus_relationship_18_profile_model.json:1 | validate_content通过。 | 无逐行training_points。 |
| T12-13 聚类解释交叉验证 | 已完成 | 用N469报告核对方向、冲突和过度解释。 | 统计叙事由研究者签字。 | docs/02_专项进度与验收/任务十二聚类解释交叉验证报告.md:1 | 冲突均降级为探索性。 | 425与469口径未混同。 |
| T12-14 小程序/Web 画像展示接入 | 已完成 | 绑定model_id，展示点位、雷达、问题、任务和边界。 | 人工检查措辞和图表。 | apps/miniprogram/pages/assessment-result/index.wxml:1 | API测试、JS检查、Web build通过。 | 不返回逐行样本。 |
| T12-15 第二阶段报名智能导入 | 已完成 | 授权报名关联测评、画像、维度、雷达和用户。 | 授权说明和隔离真机验收。 | backend/routes/relationship_pilot.py:112 | 路由权限测试通过。 | 无测评返回assessment_required。 |
| T12-16 关系健康初筛报告 | 已完成 | 用户和研究者同源报告、下载和审计。 | 文案、JSON下载体验人工验收。 | apps/miniprogram/pages/relationship-report/index.wxml:1 | 报告生成/越权测试通过。 | PDF/长图列入后续优化。 |
| T12-17 研究者消息发送报告 | 已完成 | 已确认报告才能发送；消息只含摘要和ID。 | 核对收件人和版本。 | backend/routes/relationship_pilot.py:305 | 误发/越权测试通过。 | 收件人不可由请求体指定。 |
| T12-18 研究者登录入口 | 已完成 | 复用账号登录并在我的页按角色展示入口。 | 账号轮换和密码策略。 | apps/miniprogram/pages/profile/index.wxml:1 | auth/角色测试、JS检查通过。 | 普通用户不能进仪表盘。 |
| T12-19 研究者评估仪表盘 | 已完成 | 小程序和Web展示档案、画像、报告、材料、备注和状态。 | 洞察提示与操作效率。 | apps/web/src/pages/ResearchDashboard.tsx:1 | Web build、权限/审计测试通过。 | 敏感详情访问审计。 |
| T12-20 关系隐喻互动绘画雏形 | 已完成 | 画布笔画、画外音、授权、比例预览和研究者查看。 | iOS/Android真机触控。 | apps/miniprogram/pages/relationship-task/index.js:1 | JS检查、保存测试通过。 | 不自动解释象征/潜意识。 |
| T12-21 句子补全交互雏形 | 已完成 | 七情境可选填写、保存、风险预检和研究查看。 | 敏感原文复核策略。 | apps/miniprogram/pages/relationship-task/index.wxml:1 | 路由测试、JS检查通过。 | 默认不导出原文。 |
| T12-22 治疗性反馈会议材料与探索手记 | 已完成 | 汇总草稿，研究者确认后消息交付用户。 | 最终内容必须共同修订。 | apps/miniprogram/pages/relationship-narrative/index.wxml:1 | 草稿隐藏/确认可见测试通过。 | 系统不能自动定稿。 |
| T12-23 项目试点-亲密关系入口接入 | 已完成 | 训练页聚合测评、报告、任务和成长入口。 | 学生角色和入口命名真机验收。 | apps/miniprogram/pages/relationship-pilot/index.wxml:1 | JS/JSON检查通过。 | 非学生账号后端拒绝。 |
| T12-24 连续施测内容 | 已完成 | 每周五项测量、两项叙事和关键事件入时间轴。 | 风险词和复核响应。 | backend/routes/relationship_pilot.py:390 | longitudinal与risk review测试通过。 | medium/high进统一队列。 |
| T12-25 成长仪表盘/时间轴/成长报告 | 已完成 | 我的页入口、曲线、时间轴和成长报告。 | 趋势文案不得当疗效。 | apps/miniprogram/pages/relationship-growth/index.wxml:1 | growth接口测试、JS检查通过。 | 少于两次不下趋势结论。 |
| T12-26 用户画像核心逻辑建议与落地 | 已完成 | 基础/矛盾/机制/动态四层映射报告和任务。 | 机制假设需用户与研究者核对。 | docs/02_专项进度与验收/任务十二亲密关系四层画像落地说明.md:1 | 四层画像接口测试通过。 | 不把假设写成事实。 |
| T12-27 知识星球站内替代方案 | 已完成 | 以课程、项目、打卡、消息、报告和人工支持替代。 | 不做外部敏感数据同步。 | docs/02_专项进度与验收/任务十二知识星球站内替代方案.md:1 | 文档核对完成。 | MVP不依赖外部API。 |
| T12-28 自动化验证 | 已完成 | 执行内容、建表、审核、建模、测试、JS/JSON和Web构建。 | 真机/云端仍需人工。 | docs/02_专项进度与验收/任务十二执行记录_20260710.md:1 | 171 passed；50 JS；47 JSON；Web build通过。 | Web有1.63MB大包告警。 |
| T12-29 文档同步 | 已完成 | 更新四份事实基准、API、数据库、数据字典、执行记录。 | 下一轮核对人工事项。 | docs/00_当前事实基准/当前进度交接.md:1 | 文档检索完成。 | 未使用Claude，未写Claude记录。 |
| T12-30 最终代码审查 | 已完成 | 审查题项、计分、隐私、权限、消息、两端契约和测试。 | 授权/画像/真机仍需人工签字。 | docs/02_专项进度与验收/任务十二代码审查.md:1 | P0/P1已修复后全量复跑。 | 自动化范围无未修复P0/P1。 |
```

# 任务十三：项目可信化与架构深化优化

更新时间：2026-07-11
执行依据：`docs/00_当前事实基准/当前项目不足与后续优化规划_20260711.md`、`docs/00_当前事实基准/architecture-review-safehome-20260710-1618.html`

## 0. 任务定位

任务十三不扩展无关功能，按“数据可信 → 模型治理 → 隐私完整 → 部署验收 → 关键页面视觉收口 → 工程深化”的顺序推进。每轮只完成一个可验证的小任务，保留现有 API、数据库字段、内容库和小程序 `pages/integration-test/index`。

## T13-01：服务端测评答案规范化与计分（本轮已完成）

完成内容：

1. 新增 `backend/services/assessment_execution_service.py`，建立单一测评执行 module interface。
2. 服务端按 worksheet 拒绝未知题号、重复题号、非法选项和缺少必答题。
3. 客户端 `score` 只作兼容输入，不参与真实计分；服务端按选项重算原始分、反向分、维度分和总分。
4. 风险检查、事务保存、画像触发和训练推荐从 HTTP route 收口到同一 module；`backend/routes/assessments.py` 保留 HTTP、认证和 worksheet 选择职责。
5. 不修改数据库、前端结构、shared 字段和 content 计分定义。
6. 更新测评接口文档、优化规划、架构审查 HTML 和事实基准文档。

行为验收：

```text
未知题号：400 unknown_question_id
重复题号：400 duplicate_question_id
非法选项：400 invalid_option_value
缺少必答题：400 missing_required_answers
客户端 score=99：按 worksheet 真实选项分计分
ERQ、PRFQ反向计分、任务十二三份关系量表：回归通过
高风险自由文本：继续进入人工复核并阻断普通训练卡
```

自动验证：

```text
T13-01 可信边界与计分关键行为：13 passed
测评相关导出、周报、训练计划、关系试点和用户策略：27 passed
后端全量当前合并结果：197 passed，3 failed
失败项为既有未提交工作区中的 1 项 text_analysis 聚合测试和 2 项画像准入/位置测试；均不属于 T13-01，未越界修改。
内容校验、小程序37页结构、53个JS、49个JSON、Web tsc 与 build：通过
```

## T13-02 至 T13-09：后续批次

| 子任务 | 内容 | 当前状态 | 进入条件 |
|---|---|---|---|
| T13-02 | 画像模型准入、artifact 校验、GMM 离线/线上一致性、移除逐行点 | 已由任务十四 T14-01 至 T14-03 完成 | 不再重复开发；后续只做独立样本与人工统计验收 |
| T13-03 | 关系试点隐私撤回、个人摘要、删除清单和审计闭环 | 待执行 | T13-02 完成 |
| T13-04 | CloudBase、微信登录、迁移号、iOS/Android 真机验收 | 待人工/外部 | 有发布权限和真机 |
| T13-05 | Web 登录、注册、权限不足、家庭绑定视觉修复 | 已由任务十六 T16-04/T16-05 完成 | 真机与用户测试仍进入人工合集 |
| T13-06 | 小程序重点页面视觉 token 与真机截图基线 | 待执行 | 开发者工具与真机可用 |
| T13-07 | 受控、可解释的个体化推荐 | 待执行 | 模型与隐私治理完成 |
| T13-08 | 持久化、迁移 runner、跨端契约深化 | 部分完成 | 训练节奏、身份唯一性、records索引与共享状态已完成；独立迁移runner仍后置 |
| T13-09 | CI、监控和发布门禁补齐 | 部分完成 | 请求ID、耗时日志、Web/小程序CI已完成；外部告警与真实发布门禁待人工 |

## T13 状态表

| 子任务 | 状态 | 证据 | 已跑验证 | 备注 |
|---|---|---|---|---|
| T13-01 服务端测评答案规范化与计分 | 已完成 | `backend/services/assessment_execution_service.py`、`backend/tests/test_assessments_route.py` | 关键行为13项、关联27项通过；全量197通过、3项既有失败 | 不改数据库和前端 |
| T13-02 画像模型运行时 | 已由任务十四完成 | T14-01 至 T14-03、画像准入与 GMM 推断测试 | 专项画像测试与后端全量 207 passed | 外部效标与统计签字仍待人工 |
| T13-03 研究数据治理 | 待执行 | 当前优化规划 4.3 | 未运行 | 不与 T13-02 并行 |
| T13-04 部署与真机 | 待人工 | 当前优化规划 4.4 | 未运行 | 需要外部权限与设备 |
| T13-05 | 已由任务十六完成 | Web身份关键页、服务端角色复核、双视口E2E | 12项Playwright全量通过 | 真机体验仍待人工 |
| T13-06 至 T13-07 | 待执行/待人工 | 当前优化规划 4.6 至 4.7 | 未运行 | 不自动开放模型解释 |
| T13-08 至 T13-09 | 部分完成 | schema `2026_07_11_004`、请求追踪、CI门禁 | 后端215项、Web与小程序门禁通过 | 迁移runner、外部监控和发布验收未完成 |

下一轮 Codex 启动提示词：

```text
请继续 safehome1.0 任务十三，只做 T13-02。工作区已有并行未提交的画像准入与模型内容改动，先审查这些差异及2项画像回归失败，确认 admission_status、artifact hash、GMM 离线/线上一致性和逐行点清理是否完整；不要重复实现，不同时改隐私、数据库和前端。完成后更新任务十三状态表和三份事实文档。
```

# 任务十四：聚类画像与离线情感/网络分析可信化优化

更新时间：2026-07-11
执行依据：`聚类画像全链路审查与智能化优化路线_20260710.md`、`情感计算与社会网络分析离线原型优化与实现任务路径_20260711.md`

## 0. 任务定位

本任务不增加大模型自由解释，不接普通用户实时情绪判断，不扩充未授权词库，不改数据库。目标是先把模型准入、推断一致性、逐行点隐私、离线只读输入、基础语言规则、网络边权和质量状态做可信。

## T14-01：画像模型准入与 artifact 门禁（已完成）

1. 11 份 `content/profiles/*.json` 全部补齐 `admission_status`、解释审批状态和 `artifact_hash`。
2. PRFQ、SCS 候选模型设为 `internal_only`；其余既有候选按现有审核记录保持试点状态。
3. 运行时只连接 `pilot_approved/production_approved` 且 hash 校验通过的模型；缺字段、篡改、`internal_only`、`deprecated` 均不自动匹配。
4. `/readyz` 和深度健康检查新增画像 artifact、准入枚举门禁。
5. 既往画像 `display_name` 去除“X型”，改为可变化的“阶段性位置”。

## T14-02：任务十二 GMM 训练与线上推断一致（已完成）

1. 三份模型保存 `mixture_weights`、`diag_covariances`、`assignment_version`、训练源 hash 和 artifact hash。
2. 线上按对角协方差 GMM 同公式计算 posterior responsibility，不再只按欧氏中心分配。
3. 同时返回归一化熵、经验马氏距离；解释门禁使用训练样本经验分布阈值，明确标记为探索性校准，不冒充外部验证。
4. Micro YSQ 四簇改为唯一、连续层级式阶段性名称；三份关系模型的问题根据本人维度张力生成不同问题。
5. 低确定性、样本外或待审批结果不返回画像名称、访谈问题和自动项目任务。

## T14-03：学生画像逐行训练点最小化（已完成）

学生画像模型文件已删除 466 个逐行 PCA 派生点；API 同时固定 `points=[]`，只返回簇聚合中心、簇人数和占比，避免后续旧文件回流客户端。

## T14-04：情感计算与语义共现网络主路径（已完成）

1. `analysis/text_analysis` 成为唯一主路径；两个早期原型保留兼容入口，取消本机绝对输出目录。
2. SQLite 使用 `mode=ro`，脚本不再调用 `init_db()`；输出包含源 hash、词典 hash、参数、记录数和质量状态。
3. 情感规则支持 Unicode/句子切分、否定窗口、程度副词、重复命中和转折后权重；用户、系统和督导文本分别汇总。
4. 强度增加每记录均值和每千字标准化值，避免把记录多误写成情绪更强。
5. 语义网络按句子窗口连边；strength 使用真实权重，介数中心性使用 `distance=1/(weight+epsilon)`；小图不输出复杂中心性/社区解释。

## T14-05：家庭关系拓扑与隐私质量门禁（已完成）

1. 新增 `build_family_topology_audit.py`；仅纳入 `status=active`（兼容旧快照 `confirmed`）且 `revoked_at` 为空的边。
2. 使用运行级 HMAC 在内存中连图，密钥不入仓；产物不返回节点、逐边哈希或稳定伪名。
3. 重复边、自环、撤回边和无效状态分别计数；以二节点分量为主或样本过小时返回 `insufficient_data`，不解释中心性。
4. 默认最小支持度为 5；低频节点、边和分组被抑制。
5. 离线输出统一区分 `valid/empty/insufficient_data/validation_failed/privacy_blocked`；空文件不再自动 `available=true`。

## T14-06：前端与契约最小同步（已完成）

1. 小程序结果页把“与既往样本接近度 XX%”改为“匹配清晰度：较低/中等/较高/样本范围外/待审核”。
2. `shared/types/api.ts` 和 API 文档同步 posterior、熵、马氏距离、审批状态及三类离线分析输出。
3. 不重做现有五态和视觉系统，不新增普通用户复杂网络图。

## T14 验证结果

```text
内容校验：通过
画像 artifact hash：11/11 有效
任务十二模型构建与聚合审计：通过，3 个模型
专项画像/离线分析测试：11 passed
后端全量：202 passed
Python compileall：通过
小程序：53 个 JS 语法检查、49 个 JSON 解析通过
Web：TypeScript/Vite build 通过；保留既有 echarts 大包告警
git diff --check：通过
```

已知边界：

- 词典仍是测试样例，尚无授权完整词库、双人标注、类别 F1、外部效标和独立样本校准。
- GMM 阈值来自训练样本经验分布，只能受控试点，不能写成校准准确率。
- 家庭拓扑真实数据质量尚未验证；小样本只输出绑定质量摘要。
- CloudBase、微信开发者工具、iOS/Android 真机和人工伦理/统计签字仍待完成。

下一轮 Codex 启动提示词：

```text
请继续 safehome1.0，审查任务十四并只做下一最小批次：先用经授权、脱敏的离线样本建立情感规则人工标注与覆盖率报告，冻结最小支持度和试点准入门槛；不要接实时推断、不要导入未授权词库、不要做普通用户复杂网络图。运行后更新任务十四状态和三份事实文档。
```

# 任务十五：6—9 月研发计划差距收口

更新时间：2026-07-11
原始依据：`D:\codex\workspace\safehome1.0其他内容\夏老师文件\2026年6月18日发给董俊杰的(1)\微信小程序研发计划【6-9月份】260617.docx`
事实依据：任务十二、任务十三、任务十四的代码、测试和事实基准；以当前工作区为准，不以旧计划中的历史状态替代当前事实。

## 0. 任务定位

本任务只补原研发计划与当前项目之间仍可自动完成的真实差距。已经完成的中性首页、情绪天气与日内曲线、三步情绪反射弧、量表三类呈现、服务端计分、画像可视化、课程、三个项目测试、知识星球站内替代、任务十二关系试点和任务十四可信化能力不重复开发。

执行边界：

1. 不自动开放未签字量表，不自动补写 ISI/PSQI 题项和计分。
2. 不把图片或关系绘画接入自动心理解释。
3. 不接知识星球账号、付费或敏感数据同步。
4. 不把 `pilot_draft`、经验阈值或训练样本结果写成疗效或外部验证结论。
5. 不新建第二套测评、画像、训练或研究者数据结构；优先复用 `records`、现有 API 和共享契约。

## 1. 原计划差距矩阵

| 原计划环节 | 当前事实 | 差距判断 | 任务十五处理 |
|---|---|---|---|
| 首页标题适配家长、大学生和成人 | 已使用“安心陪伴 / 选择今天的一小步” | 已完成 | 只回归，不改名 |
| 情绪天气、一天多次记录和日内回看 | 已有温度计、当日列表、统计和 Canvas 曲线 | 已完成最小日报 | 不新增长篇自动解读 |
| 三步开始与情绪反射弧说明 | 已有独立说明页和可点击入口 | 已完成 | 只回归 |
| 快速入口依次连接测评、记录、反馈、训练和人工支持 | 首页已有前四类能力，但没有显示人工支持入口 | 自动可补 | T15-01 |
| 治疗性评估后形成个性化训练节奏 | 已有测评/画像推荐和 3 天轻量计划，但节奏不能持久保存 | 自动可补 | T15-02 |
| 两个暑期项目明确前测、练习、后测 | 已有三个项目练习包，但缺结构化测量计划元数据 | 自动可补 | T15-03 |
| 既往数据整理、合并和稳定算法 | 模型已有 source hash、artifact hash 和聚合结果，但缺统一聚合来源清单 | 自动可补 | T15-04 |
| 量表题项、计分、授权和敏感边界 | 自动结构已完成，仍需负责人逐份签字 | 必须人工 | 统一进入“待人工审查内容合集” |
| ISI/PSQI 睡眠测量 | 当前只有 metadata，缺可靠题项和计分依据 | 必须人工 | 保持隐藏，不臆造 |
| 聚类、情感计算、社会网络分析扩大使用 | 原型与可信门禁已完成；独立样本、标注和统计伦理签字未完成 | 必须人工 | 不接普通用户实时解释 |
| 知识星球接续 | 已完成站内课程、训练、项目、消息和报告替代 | 已完成当前边界 | 外链需另行批准 |

## T15-00：基线核验与任务十三/十四交叉回填（已完成）

1. 后端全量确认 `202 passed`。
2. 发现任务十四新增 `pending_approval` 后，Web 图表状态契约未同步导致 TypeScript 失败。
3. 已在 `shared/contracts/relationship-ui.json` 增加状态并重新生成小程序/Web helper；契约测试和 TypeScript 检查通过。
4. 任务十三 T13-02 与任务十四 T14-01 至 T14-03 范围交叉，后续状态表必须标记“由任务十四完成”，不得重复实现。

## T15-01：首页核心入口顺序与人工支持

目标：让首页明确形成“测一测 → 情绪日记 → 支持性反馈 → 训练中心 → 人工支持”的功能顺序。

实施：

1. 保留测一测和情绪日记两个主操作。
2. 在“更多”区先展示支持性反馈，再展示训练中心，最后展示人工支持。
3. 人工支持复用 `pages/supervision/index` 和 `POST /api/supervision`，不新增接口或数据库。
4. 文案明确“非实时、非危机服务”，避免使用“专家诊断”。

验收：五类入口可见；支持性反馈仍要求先有具体记录；人工支持可进入已有页面；首页结构审计和 JS/JSON 检查通过。

## T15-02：个性化训练节奏持久化

目标：在现有测评/画像推荐基础上，允许用户保存阶段和练习频率，退出后仍可恢复。

数据策略：复用 `records`，`module_type=training_plan_assignment`，不新增数据库表。只保存当前阶段、频率、开始日期、计划状态和 200 字内目标，不保存诊断或研究标签。

接口：

1. `GET /api/training-plan` 增加最新 `assignment`。
2. `POST /api/training-plan/assignment` 保存或更新当前用户设置。
3. 枚举：`phase=start/practice/consolidate`；`cadence=daily/every_other_day/three_per_week/weekly`；`status=active/paused/completed`。
4. 日期使用 `YYYY-MM-DD`；非法枚举、非法日期、超长目标返回稳定 400 错误码。
5. 写入 `audit_logs`，但日志不包含目标原文。

小程序：在 `pages/personalized-plan` 增加阶段、频率、开始日期、状态和目标设置；使用分段按钮、日期选择器和明确保存按钮；不影响现有推荐卡列表。

验收：保存后重新 GET 可恢复；其他用户不可读取；错误输入不落库；小程序页面具备 loading/error/success；API 文档、共享类型和测试同步。

## T15-03：三个项目测试的测量计划元数据

目标：让项目测试明确“开始前—练习过程—完成后”的测量节奏，但不自动开放未审核量表。

实施：

1. 为 `content/programs.json` 三个项目增加 `measurement_plan`：当前状态、前测 worksheet、后测 worksheet、测量时间点、主要观察维度、人工审核事项和边界。
2. 考试焦虑/自我关怀项目复用 ERQ、SCS 和学生支持性画像；关系成长项目复用任务十二三份关系量表；睡眠健康项目先复用学业浮力和支持性记录，ISI/PSQI 保持 `manual_review_required`。
3. `validate_content.py` 校验 worksheet 引用存在、未审核测量不会被写成已批准。
4. 项目列表 API 返回测量计划摘要，详情 API 返回完整计划；小程序项目详情只显示时间点和“待人工确认”状态，不显示内部 ID。

验收：三个项目均有结构化测量计划；引用 ID 全部存在；ISI/PSQI 未被开放；内容校验和项目 API 测试通过。

## T15-04：画像数据聚合来源清单

目标：在不提交原始逐行研究数据、绝对路径或稳定身份标识的前提下，统一记录模型的数据版本证据。

实施：

1. 新增 `analysis/profiling/build_dataset_manifest.py`，读取已入仓画像模型并生成聚合 manifest。
2. 每个模型记录：模型 ID、模型类型、准入状态、样本量、特征数量、来源摘要、source hash、artifact hash、是否含逐行点、生成时间和人工验证状态。
3. 输出 `outputs/profile_dataset_manifest.json`；禁止出现 Windows 绝对路径、参与者 ID、题项逐行分数和自由文本。
4. 新增测试验证模型覆盖、hash 字段、隐私禁项和确定性输出。

验收：已入仓画像模型全部可追溯；同一输入重复生成核心内容一致；隐私扫描通过；manifest 只含聚合证据。

## T15-05：人工与外部事项冻结

以下只进入统一人工清单，不由自动化代码标记完成：

1. 25 份试点量表的题项、选项、计分、反向题、维度、版权和适用性签字。
2. 4 份 metadata-only 量表和 1 份 draft-only 量表的题项补录决定，其中 ISI/PSQI 不得臆造。
3. 三个项目测量方案、主要指标、时间点和退出规则的研究负责人确认。
4. 情感词典授权、双人标注、类别 F1、聚类独立样本/外部效标、家庭拓扑真实数据质量和统计伦理签字。
5. CloudBase 发布、手机号接口白名单、微信开发者工具、iOS/Android 真机与正式研究者账号策略。
6. 知识星球外链、账号、付费和数据同步的产品、隐私与商业确认。

## T15-06：自动化验证与状态回填

验证顺序：专项测试 → 内容校验 → 后端全量 → Web typecheck/build → 小程序结构/JS/JSON → `git diff --check`。完成后回填本任务状态表、任务十三交叉状态和四份事实文档。

## T15 状态表

| 子任务 | 状态 | 证据 | 自动验证 | 人工边界 |
|---|---|---|---|---|
| T15-00 基线与契约修复 | 已完成 | 共享关系状态契约及生成文件 | 契约测试、TypeScript 通过；后端 202 passed | 无 |
| T15-01 首页入口 | 已完成 | `pages/home/index.wxml` | 37 页结构审计、首页 JS 检查通过 | 真机视觉 |
| T15-02 训练节奏 | 已完成 | training plan API、`records(module_type=training_plan_assignment)`、小程序个性化方案页 | T8/T10 路由测试、TypeScript、37 页结构和 JS 检查通过 | 研究者共同确认 |
| T15-03 项目测量计划 | 已完成 | `programs.json`、内容校验、program API、小程序项目详情页 | 内容校验、路由测试、JS和结构审计通过 | 方案签字、ISI/PSQI |
| T15-04 数据来源清单 | 已完成 | `analysis/profiling/build_dataset_manifest.py`、`outputs/profile_dataset_manifest.json` | 12 个模型覆盖；确定性、hash、绝对路径、逐行点、身份字段和匿名模型 ID 测试通过 | 数据负责人确认 |
| T15-05 人工事项冻结 | 已完成 | `docs/00_当前事实基准/待人工审查内容合集.md`及旧清单索引页 | 00/01/02 当前清单去重检查 | 全部由人工执行 |
| T15-06 全量验证与回填 | 已完成 | `scripts/check_all.ps1`、任务十三交叉状态 | 内容校验；后端 207 passed；Web build/typecheck；小程序 37 页、42 组件、7 Canvas、JS/JSON 全通过 | CloudBase/真机除外 |

# 任务十六：产品体验与全栈工程可信化优化

更新时间：2026-07-11
审查依据：`docs/00_当前事实基准/全栈系统审查与优化计划_20260711.md`、任务十三/十四/十五产物、项目当前代码，以及两组 SafeHome 技术栈和情感计算/社会网络分析学习资料。

## 0. 目标与边界

目标不是增加更多展示页面，而是把身份边界、数据库一致性、关键页面状态、无障碍、请求追踪和持续集成提升到可试点、可排错、可回滚的水平。

边界：

1. 不自动合并或删除历史重复账号；发现冲突必须阻断并交人工处理。
2. 不把开发环境身份兼容带入生产；不把可伪造请求头当作默认可信身份。
3. 不改写任务十四模型统计结论，不接实时情感判断或普通用户网络图。
4. 不重做全站视觉系统，不删除现有 API、表、字段和联调页。
5. CloudBase、真机、正式账号、MySQL 生产迁移和研究伦理仍由人工验收。

## T16-00：系统审查与范围冻结（已完成）

1. 从产品、视觉、前端、后端、SQL、API、模型和交付八个方面形成审查记录。
2. 将发现分成自动可修、需分批治理和必须人工三类。
3. 以 P0 身份/数据一致性优先，P1 可观测性/关键页面/CI 次之，性能与大迁移后置。

验收：审查结论有代码事实依据；任务十六不重复任务十四/十五；人工事项进入统一合集。

## T16-01：CloudBase 身份头与遗留所有权 helper 收口

目标：生产身份只能来自受控 token 或明确启用的 CloudBase 网关上下文，普通公网请求头不得自动成为微信身份。

实施：

1. 增加 `TRUST_CLOUDBASE_IDENTITY_HEADERS` 配置，默认关闭；仅云托管部署显式开启。
2. `_trusted_cloudbase_openid` 同时校验开关、固定来源值和合法 OpenID 形态；关闭时忽略身份头。
3. 将仍直接使用 `routes/utils.py` 中 `require_user_id/resolve_user_id_for_query/require_admin_or_owner` 的敏感路由按 actor 模式收口；后台跨用户访问只允许研究者/管理员角色。
4. 保留非生产 `demo-parent` 兼容；生产缺 token 时返回稳定 401，不接受 body/query 冒充。
5. 增加头伪造、本人访问、跨用户阻断、研究者受控访问和生产降级测试。

验收：默认配置下伪造 `X-WX-OPENID/X-WX-SOURCE` 无法登录；显式可信配置下既有 CloudBase 流程可测；敏感详情不存在仅靠 `user_id` 越权。

## T16-02：身份唯一性预检与查询索引

目标：数据库能发现账号冲突，并为当前高频查询提供稳定索引。

实施：

1. 新增身份重复预检，分别检查非空 `username`、`wechat_openid`、`phone_hash`，只输出字段和重复组数，不输出具体身份值。
2. 无重复时创建部分唯一索引；有重复时 readiness/迁移预检明确阻断，不自动合并。
3. 为 `records(user_id, module_type, source_id, created_at)` 增加复合索引。
4. SQLite/MySQL schema 路径同步；增加空值、多账号、重复阻断和索引存在测试。
5. API 冲突统一返回稳定 409，不回显已存在账号信息。

验收：新库唯一约束生效；历史重复库得到可操作的阻断信息；现有数据库初始化和全量测试不回归。

## T16-03：统一请求追踪与最小健康状态

目标：每个请求可用同一 ID 关联客户端、服务端日志和响应，同时避免公开内部配置。

实施：

1. `before_request` 读取合法 `X-Request-ID` 或生成随机 ID，并记录开始时间。
2. `after_request` 返回 `X-Request-ID`，以结构化日志记录 method、path、status、duration_ms；不记录 token、请求体和自由文本。
3. 错误响应继续使用现有 envelope，并包含可用于报障的 request ID。
4. `/healthz` 只返回进程级最小状态；`/readyz` 不暴露路径、密钥、完整异常或模型内部数据。
5. 增加请求 ID 透传、非法值替换、日志脱敏和健康状态测试。

验收：成功与失败响应均可追踪；日志无敏感正文；健康检查仍满足部署门禁。

## T16-04：Web 关键身份页面与无障碍基础

目标：登录、注册、家庭绑定、权限不足页面与后台视觉系统一致，并可通过键盘和减少动效设置使用。

实施：

1. 清理未定义 `pill` 样式，复用稳定按钮和表单类；错误、加载、成功状态不依赖颜色。
2. 增加跳转到主要内容、全局 `:focus-visible`、44px 触控下限和 `prefers-reduced-motion`。
3. 为异步反馈添加 `role=status/alert`、`aria-live`；图表保留文字摘要。
4. 权限不足页说明下一步动作，不泄露资源是否存在；长中文和错误信息在移动端不溢出。
5. 用 Playwright 在桌面和移动视口检查登录、注册、家庭绑定和后台入口，无重叠、无横向滚动、焦点可见。

验收：键盘可完成主流程；减少动效生效；自动无障碍扫描无高严重度问题；截图人工待审项进入统一合集。

## T16-05：前端身份复核与错误/空状态区分

目标：前端显示角色以服务端为准，网络失败不能伪装成“暂无数据”。

实施：

1. 应用启动和受保护页面进入时调用 `/api/auth/me`；本地存储仅作启动缓存。
2. token 失效时清理本地身份并回到登录页；403 显示权限不足，不改写为 404 或空列表。
3. 首页和主要结果/报告页区分 loading、empty、error、stale，并提供明确重试。
4. `pending_approval/insufficient_data/validation_failed/privacy_blocked` 继续由共享契约驱动，不在页面硬编码另一套语义。
5. 增加前端单元或 E2E 覆盖：伪造本地角色、401、403、500、空数据和重试成功。

验收：修改 localStorage 不能释放研究者页面；失败态可恢复；现有正常流程不回归。

## T16-06：CI 与本地门禁对齐

目标：远端提交自动执行与本地 `check_all.ps1` 同源的关键门禁。

实施：

1. Web 增加独立 `typecheck` script，CI 使用 lockfile 安装、类型检查和生产构建。
2. CI 增加内容校验、小程序结构审计、JS 语法和 JSON 解析。
3. 增加身份策略、唯一约束、请求追踪、共享契约和离线隐私专项测试。
4. 保留后端全量 pytest；失败必须阻断，不以 warning 冒充通过。
5. 检查工作区不提交 `dist/node_modules/db/sqlite3/__pycache__/.venv` 等运行产物。

验收：本地全量门禁和 CI 配置均通过语法检查；所有新增专项测试通过。

## T16-07：全量回归、代码审查与事实回填

验证顺序：专项安全/数据库/API测试 → 内容校验 → 后端全量 → Web typecheck/build/E2E → 小程序结构/JS/JSON → 隐私扫描 → `git diff --check`。

代码审查重点：身份与所有权、数据库兼容、错误码契约、敏感日志、待审批画像、移动端溢出、无障碍、测试遗漏和文档一致性。

完成后更新 `项目进度统一口径.md`、`开发日志.md`、`当前进度交接.md`、`开发说明.md` 和 `待人工审查内容合集.md`；提交并推送一次。

## T16 状态表

| 子任务 | 状态 | 证据 | 自动验证 | 人工边界 |
|---|---|---|---|---|
| T16-00 系统审查 | 已完成 | `全栈系统审查与优化计划_20260711.md` | 代码、文档和学习资料交叉审查 | 产品负责人确认优先级 |
| T16-01 身份与所有权 | 已完成 | `TRUST_CLOUDBASE_IDENTITY_HEADERS`、auth/legacy helper、部署说明 | 身份与敏感路由专项 29 passed | CloudBase 真网关 |
| T16-02 数据唯一性与索引 | 已完成 | schema `2026_07_11_004`、匿名重复预检、4组索引 | 身份/schema/health/auth 专项 22 passed | 历史冲突处置、MySQL生产迁移 |
| T16-03 请求追踪 | 已完成 | Flask request ID/duration middleware、最小 readiness、API文档 | health/CORS/身份策略专项 16 passed | 外部日志平台 |
| T16-04 关键页面与无障碍 | 已完成 | 身份页面、全局焦点/触控/减少动效、桌面移动截图 | build/typecheck；4项双视口E2E；修复family重复占位 | 真机与用户测试 |
| T16-05 前端身份和状态 | 已完成 | `/api/auth/me`启动复核、服务端角色覆盖、401清理 | 8项双视口E2E、build/typecheck | 正式研究者账号 |
| T16-06 CI 门禁 | 已完成 | Web typecheck script、`check.yml`、跨平台小程序资源校验 | workflow YAML、Web build/typecheck、37页结构、53 JS/49 JSON通过 | 远端 Actions 实际运行 |
| T16-07 回归与回填 | 已完成 | 代码审查报告、四份事实文档、人工合集 | 内容；后端215；Web build/typecheck；小程序37页/53 JS/49 JSON；Playwright 12；diff检查通过 | 人工合集全部事项 |

# 任务十七：训练卡、课程与项目试点心理学内容体系化

更新时间：2026-07-11

规划依据：`微信小程序研发计划【6-9月份】260617.docx`、任务十五差距矩阵、`content/training_cards.json`、`content/courses.json`、`content/programs.json`、现有测评结果与训练推荐链路，以及 `docs/00_当前事实基准/待人工审查内容合集.md`。

## 0. 任务定位、目标与边界

本任务处理四项尚未收口的内容：

1. 三个项目虽已建立测量计划，但均处于 `draft_requires_research_review`，尚未形成可签字、可执行、可追踪的试点方案。
2. 当前 5 门课程主要是 3 段式心理教育微内容，尚未具备完整学习目标、理解检查、引导练习、迁移任务和巩固路径。
3. 当前 34 张训练卡已有基本步骤和边界，但缺少统一的目标机制、建议剂量、禁用情境、停止规则、完成标准、进阶条件和结果指标。
4. 量表维度、画像提示、训练卡、课程和项目之间虽已有局部关联，尚未形成可审计的统一机制矩阵。

最终目标：形成“测评维度/具体困扰 → 支持性解释 → 训练目标 → 训练卡 → 课程 → 项目阶段 → 过程与结果测量”的一致链路，同时保持非诊断、非标签化和人工审核边界。

执行边界：

1. 自动化可以补字段、校验结构、生成候选映射、修复确定性内容问题、开发页面和接口，但不能代替心理学负责人批准理论内容。
2. 不把 3 次微干预写成治疗或疗效已证实；在研究签字前统一使用“试点草案”“支持性练习”“可行性观察”。
3. 不自动开放暴露、内感性暴露、睡眠限制、伴侣共同练习等高风险内容；必须先有适用条件、排除条件、停止规则和人工审核。
4. 不把量表高低分、聚类类别或画像名称直接转换为固定人格标签或唯一训练处方。
5. 不自动补写 ISI/PSQI 题项和计分，不把睡眠健康项目命名为 CBT-I。
6. 不新建第二套用户、测评、训练或项目数据结构；内容优先放在 `content`，用户进度继续复用现有 API、`records` 和相关业务表。
7. 每次只实施一个 T17 子任务；每项完成后先专项验证和人工边界核对，再进入下一项。

## 1. 统一心理学内容模型

### 1.1 训练卡标准字段

在保留现有字段的基础上，为每张训练卡补齐以下结构；字段名以实际代码审查后的共享契约为准，但语义不得缺失：

1. `mechanism_code`：主要作用机制，如情绪觉察、认知灵活性、自我关怀、减少回避、关系确认、冲突修复、行为启动。
2. `target_constructs`：可关联的测评维度或过程变量，不直接使用诊断名称。
3. `indications`：适用的具体场景、行为和主观困难。
4. `contraindications`：不适用或必须先人工评估的情境。
5. `minimum_dose`：单次建议时长、建议频率和最短练习周期。
6. `completion_criteria`：完成一次练习所需的最小行为证据。
7. `progression_criteria`：继续、重复、降低难度或进入下一卡的条件。
8. `stop_rules`：明显不适、风险文字、关系不安全或身体异常时的停止规则。
9. `fidelity_check`：1 至 3 个不涉及诊断的执行核对项。
10. `outcome_links`：与过程测量、打卡字段或项目观察指标的关联。
11. `evidence_level`：`project_draft/manual_reviewed/pilot_ready` 等治理状态，不使用“临床有效”冒充证据。
12. `user_facing_title`：面向用户的生活化标题；PRFQ、ERQ、SCS 等缩写只保留在内部来源字段。

### 1.2 课程标准字段

每门课程由简单章节升级为结构化学习单元：

1. `learning_objectives`：用户完成后能理解或做到什么，使用可观察动词。
2. `core_concept`：本课唯一核心概念，避免一课堆叠多个机制。
3. `common_misconceptions`：常见误解及纠正说明。
4. `worked_example`：一个完整正例。
5. `counter_example`：一个常见但不推荐的反例，并解释原因。
6. `knowledge_checks`：至少 1 个选择或情境判断题，包含反馈而非只判对错。
7. `guided_practice`：与训练卡关联的当场练习。
8. `transfer_task`：课后在真实场景中完成的一次迁移任务。
9. `reflection_prompts`：练习后的观察和复盘问题。
10. `booster_plan`：建议复习时间、重复条件和下一课程入口。
11. `audience_adaptation`：家长、学生、普通成人的场景、称谓和责任边界。
12. `review_status`、`reviewer_note`、`boundary_notice`：内容治理和非诊断边界。

### 1.3 项目试点方案字段

三个项目必须形成可由研究负责人签字的版本化方案：

1. 项目版本、状态、目标人群和使用场景。
2. 纳入标准、排除标准、暂停标准和退出标准。
3. 主要过程指标、主要结果指标、次要指标和探索性指标。
4. 前测、过程测量、后测、随访的时间点和允许窗口。
5. 每次练习内容、建议间隔、最小完成剂量和项目完成定义。
6. 依从性、跳过、中途退出、方案偏离和缺失数据的记录规则。
7. 练习前后不适程度、负面体验、风险升级和人工联系流程。
8. 自动推荐、用户自主选择和研究者调整三种来源的记录字段。
9. 参与者可见文案、研究者说明、非治疗声明和紧急情况说明。
10. 研究负责人、心理负责人、伦理负责人审核状态和版本生效日期；未签字前不得变为 `pilot_approved`。

## T17-00：基线盘点与内容冻结

目标：先冻结当前内容版本，建立问题清单，避免升级过程中无法判断内容变化来源。

实施：

1. 生成 34 张训练卡、5 门课程、3 个项目的字段覆盖清单。
2. 自动检查训练卡重复标签、`...` 截断、空字段、无效训练卡引用、专业缩写标题和缺失边界说明。
3. 统计训练卡在情绪觉察、认知灵活性、行为改变、自我关怀、身体调节、关系沟通、冲突修复、巩固预防等机制上的覆盖。
4. 统计课程到训练卡、项目到课程/训练卡、测评维度到训练卡的未映射项和多重冲突项。
5. 输出任务十七基线审计报告；只报告事实，不自动批准内容。

验收：所有内容 ID 唯一；引用可追踪；基线报告可重复生成；34/5/3 全覆盖；问题按自动修复、心理审核、研究审核分类。

## T17-01：训练卡确定性质量修复

目标：先修复不涉及专业判断的内容完整性问题，再进入机制扩展。

实施：

1. 删除重复标签，保持标签顺序稳定。
2. 对含 `...` 的提示字段回查可靠本地来源；有完整来源时恢复原文，无可靠来源时删除残缺句并标记 `manual_review_required`，不得自行续写原量表或版权内容。
3. 将用户端标题中的量表缩写改为生活化标题，原缩写保留在 `theory_source/target_constructs`。
4. 统一时长、步骤编号、练习前后提示、复盘问题和边界文案格式。
5. 增加内容校验，禁止重复标签、残缺省略号、空步骤、无效引用和缺少停止说明的敏感训练卡进入用户端。

验收：确定性问题清零；内容校验通过；已有卡 ID 不变；历史打卡仍能关联；人工改写项留有明确清单。

## T17-02：训练卡机制、剂量与安全模型升级

目标：把训练卡从“步骤集合”升级为可解释、可分层、可复盘的心理练习单元。

实施：

1. 扩展 `content/training_cards.json` 字段并建立 JSON 结构校验。
2. 为 34 张卡逐张补机制候选、适用情境、禁用情境、建议剂量、完成标准、进阶条件、停止规则、执行核对和结果关联。
3. 对高风险类别设置额外门禁：暴露类、强烈身体感受类、睡眠限制类、关系共同练习类默认不可由普通分数自动释放。
4. 小程序训练卡详情展示建议时长、适用场景、开始前提醒、停止提示和完成标准；内部量表 ID、研究状态和规则阈值不直接展示。
5. Web 内容后台增加机制、剂量、安全字段的只读审查视图；研究者可以查看版本和审核状态，但第一阶段不做无审计的在线自由编辑。
6. shared 类型、后端 content loader、训练卡 API、小程序和 Web 使用同一字段契约。

验收：34 张卡结构完整；敏感卡默认受控；旧客户端缺少新字段时可兼容；API/共享类型/两端显示一致；心理负责人未签字项保持待审核。

## T17-03：训练卡推荐与进阶规则收口

目标：避免“一个分数对应唯一处方”，将推荐改为可解释的候选集合和共同选择。

实施：

1. 建立“测评维度/记录线索 → 训练目标 → 候选训练卡”的版本化矩阵。
2. 每次默认返回 2 至 3 个候选，并说明推荐依据来自哪个可观察维度或用户目标，不显示诊断推断。
3. 加入用户偏好、最近已练、完成情况、不适反馈、关系安全和研究者调整作为排序条件。
4. 单次低分、高分或聚类类别不得直接释放敏感训练；风险为 high 时继续阻断普通自动建议。
5. 保存推荐来源：`assessment/rule/user_choice/researcher_adjusted`，以便后续分析推荐与实际选择是否一致。
6. 对所有映射规则增加版本、状态、来源、审核人和回滚字段；现有 `draft` 规则在签字前不得显示为“已验证推荐”。

验收：相同输入得到稳定候选；用户可自主选择或稍后决定；敏感卡门禁有效；推荐原因可追踪；旧结果页不出现人格化或确定性处方文案。

## T17-04：5 门微内容升级为结构化课程

目标：保留现有课程主题，将每门课升级为“理解、辨别、练习、迁移、复盘”的完整最小学习单元。

实施：

1. 升级“理解孩子的情绪”：加入行为与情绪区分、确认感受正反例、情境判断、一次开放问题练习和家庭迁移任务。
2. 升级“家长情绪调节入门”：加入身体信号识别、暂停而非压抑的区别、三秒暂停练习和冲突前预案。
3. 升级“非评判陪伴”：加入确认不等于同意、建议过早的反例、倾听练习和一周观察记录。
4. 升级“冲突后的修复”：加入安全前提、责任表达、修复失败后的停止条件；关系存在暴力、胁迫或恐惧时不推荐共同修复练习。
5. 升级“考试压力沟通”：区分支持与施压，加入学生视角示例、微启动练习、家长回应练习和考后复盘。
6. 每门课至少包含 1 个正例、1 个反例、1 个理解检查、1 个引导练习、1 个迁移任务、1 个复盘和 1 个后续入口。
7. 课程页面增加章节进度、理解检查反馈、继续/稍后学习、关联训练卡和完成后的下一步；不以打开页面等同完成学习。
8. 课程完成记录保存内容版本、完成章节、理解检查、迁移任务状态和关联训练卡，不保存不必要的敏感文本。

验收：5 门课程全部达到统一结构；理解检查有解释性反馈；课程与训练卡引用有效；移动端长文本无溢出；完成状态可恢复；内容仍为支持性心理教育而非治疗宣称。

## T17-05：UP 导向的课程路径与分众适配

目标：在现有课程和训练卡之上建立递进学习路径，不一次性堆叠大量新课程。

实施：

1. 建立基础路径：理解情绪反射弧 → 情绪觉察 → 认知灵活性 → 情绪驱动行为与回避 → 身体信号调节 → 关系沟通与修复 → 巩固与复发预防。
2. 先将现有 5 门课程映射到路径节点；没有充分内容的节点标记缺口，不自动生成未经审核的治疗材料。
3. 为家长、大学生和普通成人分别建立称谓、场景、责任边界和例子，不简单复制同一文本。
4. 首页和训练中心只展示当前阶段、建议下一步和可选内容；不以“必须完成全部课程”制造压力。
5. 暴露和内感性暴露只保留为后续受控模块候选，不进入本轮普通用户课程。
6. 建立路径版本和回滚策略，旧用户保留已完成记录，新版本只影响后续推荐。

验收：路径节点、课程和训练卡引用一致；三类用户文案抽查通过；无诊断化、责备性和强制服从语言；未审核高风险模块不可见。

## T17-06：三个项目试点方案冻结与版本治理

目标：把三个 `draft_requires_research_review` 项目升级为可审查的完整试点方案，但只有人工签字后才能进入 `pilot_approved`。

### T17-06A 考试焦虑与自我关怀项目

1. 明确目标为可行性和过程变化观察，不写成治疗考试焦虑。
2. 冻结主要过程指标、次要结果指标及其测量时间点。
3. 明确自我关怀书写的可选主题、跳过权利、中止条件和练习前后不适评分。
4. 加入中性替代练习，避免所有参与者被迫书写高强度负性经历。
5. 记录练习完成度、主观帮助程度和负面体验。

### T17-06B 亲密关系成长项目

1. 在进入沟通、修复、关系隐喻或开放叙事前增加关系安全门禁。
2. 对暴力、胁迫、跟踪、威胁、明显恐惧和报复风险设置停止并转人工规则。
3. 允许个人独立练习，不要求伴侣参与或查看用户内容。
4. 画像和关系绘画仅作为访谈与自我观察线索，不自动解释潜意识或关系类型。
5. 明确数据可见范围、消息发送权限和研究者访问审计。

### T17-06C 学业压力与睡眠健康项目

1. 保持“睡眠健康促进”命名，不称为 CBT-I 或失眠治疗。
2. ISI/PSQI 未审核前不输出失眠筛查或严重程度结论。
3. 当前只使用低风险的作息观察、睡前降速、压力觉察和支持性记录。
4. 睡眠限制、刺激控制及需要医学排查的睡眠问题不由普通自动流程开放。
5. 增加持续严重睡眠困难、明显日间功能受损或其他健康风险的人工/医疗建议边界。

### T17-06D 三项目共同治理

1. 为每个项目生成版本化方案摘要和人工签字表。
2. 后端只接受合法状态迁移：`draft_requires_research_review → pilot_approved → paused/completed`；普通接口不能自改为批准。
3. 方案更新后新参与者使用新版本，已开始参与者继续绑定原版本，避免中途改变干预内容。
4. 记录纳入、排除、暂停、退出、偏离和负面体验的结构化原因；自由文本保持最小化和权限控制。
5. 未签字项目可在开发环境预览，但正式环境入口默认隐藏或显示“尚未开放”。

验收：三个项目均有完整方案、版本和签字位；状态机不可绕过；用户绑定具体版本；风险和退出流程可测；批准仍由研究/心理/伦理负责人完成。

## T17-07：项目、课程与训练进度的全栈联动

目标：让用户和研究者看到同一套项目阶段与内容版本，不形成小程序、Web、后端三套事实。

实施：

1. 项目详情返回方案版本、阶段、当前课程、候选训练卡、测量时间点、完成标准和边界摘要。
2. 小程序项目页展示当前阶段、下一项任务、可跳过说明、退出入口和帮助入口。
3. 个人中心成长仪表盘区分课程学习、训练练习、测量和项目里程碑，不把页面浏览计为训练完成。
4. 研究者后台展示参与版本、完成率、跳过/退出、负面体验和待联系提示；不展示无必要的用户隐私正文。
5. 报告明确区分“用户自述”“规则生成”“画像模型候选”“研究者补充”，避免混成单一权威结论。
6. API、数据库/records、shared 类型、Web 和小程序同步更新；字段变更同时更新 API 与数据库说明。

验收：跨端状态一致；项目版本不可漂移；权限测试通过；用户可暂停和退出；研究者操作有审计；历史数据兼容。

## T17-08：心理内容人工审核与证据回填

目标：为自动化不能替代的心理学判断建立逐项签字入口。

实施：

1. 在 `待人工审查内容合集.md` 增加任务十七专节，不在其他目录重复维护待办。
2. 训练卡审核字段：目标机制、适用/禁用、剂量、停止规则、措辞、理论来源、结果关联、结论和证据。
3. 课程审核字段：学习目标、正反例、理解检查、练习、迁移任务、分众文案、关系安全、边界和结论。
4. 项目审核字段：纳排、指标、时间点、剂量、退出、负面体验、风险流程、数据权限、版本和三类负责人签字。
5. 未通过项回退到 `manual_review_required/draft_requires_research_review`；不得通过修改前端文案掩盖后台未批准状态。

验收：每个自动产物均能对应审核条目；审核人、日期、版本、证据和结论完整；没有“代码通过等于心理内容批准”的记录。

## T17-09：自动化验证、代码审查与事实回填

验证顺序：内容 schema/引用/文案校验 → 训练推荐与敏感门禁测试 → 项目状态机与版本测试 → 后端全量 → Web typecheck/build/E2E → 小程序结构/JS/JSON → 隐私与诊断化措辞扫描 → `git diff --check`。

代码审查重点：

1. 内容 ID 和历史记录兼容性。
2. 未审核内容是否被错误开放。
3. 推荐是否变成分数决定的唯一处方。
4. 项目版本是否在用户参与中途漂移。
5. 关系安全、睡眠健康和高风险停止规则是否可绕过。
6. 跨端字段、状态和错误语义是否一致。
7. 自由文本、风险记录和研究者权限是否最小化。
8. 课程完成是否被页面浏览错误触发。
9. 文案是否包含治疗承诺、诊断标签、人格定性或研究结论夸大。

完成后更新 `项目进度统一口径.md`、`开发日志.md`、`当前进度交接.md`、`开发说明.md` 和 `待人工审查内容合集.md`，并形成任务十七专项验收报告。

## 2. 任务十七执行顺序

严格按以下顺序逐项完成并逐项核对：

1. T17-00 基线盘点与内容冻结。
2. T17-01 训练卡确定性质量修复。
3. T17-02 训练卡机制、剂量与安全模型。
4. T17-03 推荐与进阶规则。
5. T17-04 5 门课程结构升级。
6. T17-05 UP 课程路径与分众适配。
7. T17-06 三个项目方案冻结与版本治理。
8. T17-07 全栈联动。
9. T17-08 人工审核证据回填。
10. T17-09 全量验证和代码审查。

前一项未完成专项验收，不进入下一项；研究签字可作为人工阻断项保留，但不得把待签字状态写成已完成。

## 3. 任务十七状态表

| 子任务 | 状态 | 预期证据 | 自动验证 | 人工边界 |
|---|---|---|---|---|
| T17-00 基线盘点 | 已完成 | `任务十七内容基线审计报告_20260711.md`、`outputs/task17_content_baseline.json` | 34卡/5课/3项目/32规则全覆盖；专项2 passed | 问题分类仍需负责人复核 |
| T17-01 训练卡质量修复 | 已完成 | `training_cards.json`、基线审计 | 20组重复标签、7组残缺三点、3个缩写标题清零 | 无可靠来源时仍不得续写原量表文本 |
| T17-02 训练卡机制模型 | 已完成 | 34卡治理字段、schema、共享类型、小程序和Web只读详情 | 字段完整、受控卡自动推荐门禁通过 | 逐卡心理审核待完成 |
| T17-03 推荐与进阶规则 | 已完成 | 32条版本化候选规则、推荐来源写入打卡 | 候选集合、共同选择、high风险和受控卡阻断测试通过 | 映射规则批准待完成 |
| T17-04 5门课程升级 | 已完成 | `courses.json`、课程交互页、课程进度API | 目标/误区/正反例/理解检查/练习/迁移/复盘齐全；完成状态可恢复 | 逐课内容审核待完成 |
| T17-05 UP路径与分众 | 已完成 | `courses.json.pathways`及三类用户适配 | 7节点引用有效；暴露/内感/睡眠限制禁止自动释放 | 理论覆盖确认待完成 |
| T17-06 项目方案冻结 | 已完成 | 三份 `2026.07-task17-v1` 方案、三方签字位和状态机 | 版本、非法session/评分、状态跳级和签字阻断测试通过 | 研究/心理/伦理签字待完成 |
| T17-07 全栈联动 | 已完成 | 课程进度、项目版本绑定、API/共享类型/小程序/Web审查视图 | 跨端字段、历史记录和推荐来源专项通过 | 真机和研究者正式账号流程待验收 |
| T17-08 人工审核回填 | 已完成 | 人工合集第6.1节及具体证据路径 | 单一待办入口和审核模板检查通过 | 全部审核签字仍待执行 |
| T17-09 回归与审查 | 已完成 | `任务十七代码审查与验收报告_20260711.md`及事实文档 | 内容；后端224；Web build/typecheck；小程序37页/53 JS/49 JSON；Playwright 12；diff检查通过 | 正式试点批准仍待三方签字 |

# 任务十八：小程序真实链路修复、测评内容复核与受控开放

制定日期：2026-07-11
截图证据目录：`D:\codex\workspace\safehome1.0其他内容\文档图片\改错用图第二`
执行原则：先复现、再修复；一次只完成一个 T18 子任务；页面、API、数据库和内容必须同源；不得用静态占位文案掩盖数据链路错误。

## 0. 任务目标与边界

1. 修复微信一键登录、手机号快捷登录、账号密码登录和研究者账号的真实可用链路。
2. 修复关系探索成长仪表盘、本周补充记录和关键事件时间轴的保存、刷新和显示链路。
3. 修复情绪温度计、情绪事件反馈、聚类画像、训练推荐等页面的数据绑定和移动端布局。
4. 对所有用户可见量表执行“指导语、题项、选项、反向计分、维度、总分、结果解释、训练映射”全链路复核，优先处理截图已证明错误的量表。
5. 测评记录和训练记录必须显示当前登录用户的完整历史，不再用首页摘要或训练中心代替独立记录页。
6. 盘点已实现但未开放的功能、量表、训练卡、项目包、聚类画像、情感计算和工具；只有同时满足“治理状态允许、技术链路完整、权限与边界完整、自动测试通过”的内容才开放。
7. 仍待版权、心理、研究或伦理签字的量表和高风险工具继续保留受控状态，不得仅修改前端开关绕过审批。
8. 用户端继续使用“支持性测评、阶段性观察、自我了解线索”等非诊断措辞，不把聚类或量表结果写成人格标签、筛查结论或治疗承诺。
9. 保留 `pages/integration-test/index` 和 `pages/debug/index`，将其作为云端登录、健康检查、测评与保存链路的长期诊断入口。

## 1. 截图证据对应范围

1. 登录：微信登录和手机号登录失败后只能注册，错误提示不能区分用户取消、微信配置缺失、云托管身份头未信任和后端交换失败。
2. 项目测试：首页显示“当前还没有可显示的项目测试内容”，说明项目内容治理状态、API筛选或客户端过滤至少一处不一致。
3. 关系成长：本周记录和关键事件保存后出现“加载失败”，且时间轴没有新增节点。
4. 情绪温度计：补充观察的三个滑块数值被轨道和滑块遮挡，整体信息层级与触控区域需要调整。
5. 情绪反馈：主要情绪、触发点、互动线索和练习位置显示通用占位值，未反映刚提交的记录。
6. 量表内容：多个 worksheet 把来源说明、计分手册或整段问卷说明误写成题项；统一指导语覆盖量表专属指导语；部分选项与题目不匹配。
7. 画像结果：散点标签、当前点、雷达轴和维度文字重叠；关系结果维度与训练推荐存在映射错误或重复。
8. 个性化训练：同一训练卡重复出现，节奏组件位置不稳定，完成后仍被重复推荐。
9. 本周复盘：维度汇总、场景和互动线索存在聚合口径问题，英文内部编码直接暴露。

## T18-00：基线冻结、截图映射与既有改动审查

目标：冻结当前线上截图、代码、内容版本和未提交改动，建立可重复的红灯测试，避免重复开发或覆盖其他对话成果。

实施：

1. 对 21 张截图建立文件名、页面、时间、现象、相关 API、相关数据库表/内容文件、预期行为和验收方式映射。
2. 盘点当前未提交的 `update_task18_assessments.py`、`test_task18_scale_opening.py`、量表 content 和计分服务改动，逐项判断已完成、待验证或不符合边界。
3. 输出当前账号、测评、训练、项目、画像、情感计算和工具的开放状态矩阵。
4. 为登录、成长记录、反馈、测评列表、训练记录、项目列表建立最小复现测试；不能自动复现的真机授权步骤写成明确人工证据位。
5. 生成 `任务十八基线审计与截图映射_20260711.md` 和机器可读 JSON，不修改业务状态。

验收：21 张截图全部有归属；12 个用户需求均有代码入口和测试入口；现有未提交改动不被覆盖；每个后续子任务至少有一个红灯信号。

## T18-01：微信、手机号和账号密码登录链路

目标：三种登录方式各自可用，并能给出可行动、可排查的错误，不把失败统一成“暂不可用”。

实施：

1. 核对 `wx.cloud.init` 环境、`X-WX-SERVICE=flask-gh3l`、`TRUST_CLOUDBASE_IDENTITY_HEADERS`、微信 AppID/AppSecret 和手机号能力开通边界。
2. 微信登录按钮必须先执行 `wx.login`，把有效 code 发送到 `/api/auth/wechat-login`；区分用户取消、code 缺失、云托管身份头缺失、`jscode2session` 失败和账号冲突。
3. 手机号按钮使用微信要求的 `open-type=getPhoneNumber` 事件取得动态 code，再调用 `/api/auth/phone-login`；不使用旧版明文手机号流程，不保存完整手机号。
4. 登录成功统一写入 `auth_token`、`auth_user`，清除匿名身份并按 redirect 返回；失败不得留下半登录状态。
5. 账号密码登录保持可用，增加空值、错误密码、停用账号、角色权限和令牌过期测试。
6. 小程序错误提示保留用户可理解文案，调试页同时显示脱敏错误码、request ID、env、service 和 path。
7. 后端增加微信登录、手机号登录、匿名记录归并和重复身份冲突测试；真机验收分别覆盖首次授权、拒绝授权、取消授权和再次登录。

验收：账号密码自动测试通过；微信和手机号在配置完整的真机上可拉起授权并登录；配置不完整时准确提示外部配置项；不会只能依赖注册新账号。

## T18-02：研究者正式账号与凭据交付

目标：提供一个明确、可登录、可审计、可轮换的研究者账号，不把生产密码硬编码到仓库或文档。

实施：

1. 固定研究者用户名为 `safehome_researcher_01`，角色为 `researcher`，状态为 `active`。
2. 新增幂等账号初始化脚本，读取 `RESEARCHER_BOOTSTRAP_USERNAME` 和 `RESEARCHER_BOOTSTRAP_PASSWORD`，通过现有密码哈希和用户表创建或轮换账号。
3. 未显式提供密码时生成高强度一次性密码，只写入 `.codex_tmp/researcher-account-<timestamp>.txt`，该目录不进入 Git；最终向项目负责人明确报告用户名和本机凭据文件位置。
4. 云端优先复用受 `X-Admin-Token` 保护的 `/api/auth/admin-create-account`，不直接公开 MySQL 写入口。
5. 研究者登录后只能进入研究仪表盘、脱敏记录和允许的研究功能；普通用户、家长和学生不能提升角色。
6. 增加创建、重复创建、密码轮换、错误角色、研究者访问和普通用户越权测试。

验收：负责人能拿到明确账号和一次性密码；密码不出现在 Git diff、日志和用户界面；研究者登录后权限正确，普通账号越权返回 403。

## T18-03：关系探索成长仪表盘与时间轴

目标：本周补充记录和关键事件能保存、回读并立即进入时间轴，页面布局适合真机长内容。

实施：

1. 明确成长记录必须绑定当前用户有效的关系项目 enrollment；无 enrollment 时提供进入项目和创建参与记录的清晰入口。
2. 本周补充记录保存前校验必填、量表范围和风险文本，生成稳定 idempotency key，防止重复点击产生重复记录。
3. 关键事件保存后返回完整记录；前端成功后刷新 `/growth`，并把新节点按 `event_at/created_at` 正确排序。
4. 修复 API 路径、登录令牌、enrollment ID、字段命名和错误解析不一致；把 request ID 展示在调试详情中。
5. 时间轴提供全部、测评、任务、记录、报告、研究者反馈筛选；空状态、加载、保存中、成功和失败状态完整。
6. 重排长表单：字段分组、滑块读数独立显示、关键事件固定最小高度，保存按钮不与内容重叠。
7. 增加服务、路由、小程序状态转换和真实 API 集成测试。

验收：保存本周记录后刷新仍存在；关键事件立即进入时间轴；重复点击不重复；跨账号不可读取；截图中的“加载失败”不再复现。

## T18-04：情绪温度计视觉与数据提交

目标：温度计直观、稳定、可触控，补充观察的数值不再被滑轨遮挡。

实施：

1. 保留温度计作为主交互，将 1—10 刻度、当前数值、加减按钮和触摸拖动统一到同一个状态源。
2. 三个补充观察使用“名称 + 独立数值徽标 + 滑块”三行结构，数值放在轨道之外；设置稳定高度、网格列和安全间距。
3. 修复不同系统 slider 默认样式差异，扩大触控区域但不扩大视觉滑块；适配窄屏和系统大字体。
4. 校验强度、愉悦度、唤起度、可控感和可选文本的提交字段，保存成功后回读当天记录。
5. 增加极值、快速点击、拖动、重复保存和失败重试测试；真机截图验证数字无遮挡。

验收：三个数字在常见 Android/iOS 屏幕和大字体下清晰；1/10 边界准确；保存后首页/周报能读取同一数据。

## T18-05：情绪事件即时反馈数据绑定

目标：反馈必须来自刚保存的具体记录和规则结果，不再展示统一占位值。

实施：

1. 从 diary 保存响应中携带真实 diary ID，反馈页只通过该 ID 拉取或生成反馈，禁止回退到不相关的最近记录。
2. “主要情绪”来自本次记录的家长/学生情绪字段或规则提取；“触发点”来自具体场景和原始事件摘要。
3. “可能出现的互动线索”来自规则命中和反馈结果；没有命中时显示可行动的空状态，不显示 `general_support` 等内部编码。
4. “可以练习的位置”来自本次反馈对应的推荐候选；过滤无效、重复、已完成和受控训练卡。
5. 保存本次反馈时绑定 diary、feedback、recommendation source 和规则版本，保证历史可追踪。
6. 增加两组不同情绪记录的差异测试，确认四个核心区域随输入变化；高风险记录继续阻断普通推荐。

验收：连续提交两条不同事件时主要情绪、触发点、互动线索和练习位置均发生合理变化；不显示诊断性判断或静态占位。

## T18-06：全量量表题项、选项、指导语、计分和维度审计

目标：修复已发现量表错误，并自动审计全部用户可见 worksheet，保证内容、计分和结果维度同源。

实施：

1. 每份量表使用自身 `instructions/timeframe/source_version`；删除统一“最近两周或日常”的硬编码覆盖。
2. 优先逐份核对：TIPI 10项大五人格、一般健康问卷、关系担心与期待、关系主动性、领悟社会支持、FMI-12、学生归因风格、自我关怀、生活满意度。
3. TIPI 核对第10题、7级选项、反向题 2/4/6/8/10 和五维平均分；不得把人格维度写成固定标签。
4. 一般健康问卷第12题只保留题项正文，计分说明放回 scoring/instructions；核对正负向题和维度/总分。
5. 领悟社会支持和学生归因风格按题目语义建立正确选项模板，不强行复用通用同意度选项。
6. FMI-12、自我关怀、生活满意度删除误混入的文献、手册和计分段落；逐题对照本地原文件和授权/公开来源。
7. 关系担心与期待、关系主动性核对维度归属、题目到维度映射、维度统计和画像模型输入。
8. 对所有 worksheet 自动检查：题号连续、题项非空、无文献/手册污染、选项值唯一、反向范围合法、维度覆盖完整、总分范围一致、指导语存在、训练卡引用有效。
9. 现有任务十八量表脚本和测试作为候选成果逐项复核；无法由来源确定的内容保留 `pilot_review_required`，不得自动猜题。
10. 生成全量审计 CSV/MD，标明自动修复、来源已核对、待人工签字和不可开放。

验收：截图中列出的九类量表逐项通过来源对照；所有用户可见量表通过结构和计分测试；结果页维度数与定义一致；未核对内容不开放。

## T18-07：聚类画像与结果图表布局

目标：散点、雷达和维度列表在真机上清晰，不重叠，不把内部模型字段暴露给用户。

实施：

1. 散点图按画布边界计算标签位置，对当前点、聚类中心和图例做碰撞避让；标签过长使用短显示名和图外说明。
2. 雷达图使用维度显示名、稳定半径和换行策略；维度过多时改用可滚动维度条形列表作为主视图，雷达作为摘要。
3. 关系担心与期待必须显示定义中的全部维度；关系主动性图表使用维度层聚类输入，不把题号作为雷达轴。
4. 结果卡区分画像候选、维度得分、优势线索、可讨论问题、训练候选和非诊断边界。
5. 增加 Canvas 像素非空检查、边界检查、长标签测试和多个 viewport 截图验收。

验收：截图中的当前点、聚类名、题号和雷达标签不再重叠；全部维度可读；同一结果在 Android/iOS 和开发者工具上稳定。

## T18-08：完整测评记录与本周维度汇总

目标：个人中心显示当前用户全部测评记录，本周复盘按每份量表展示完整维度。

实施：

1. 新建或完善独立测评记录页，调用分页接口获取当前用户全部记录，不再 `slice(0,3)` 或固定 limit=3。
2. 支持下拉刷新、加载更多、量表筛选、时间排序、空状态和详情跳转；服务端强制当前用户所有权。
3. 首页仍可保留最近三条摘要，但“查看全部”必须进入完整记录页。
4. 本周汇总按 worksheet/result 分组；同一量表展示全部已定义维度，不把不同量表维度压成一个总分，也不重复累计同一提交。
5. 兼容普通规则结果和聚类画像结果，明确显示测评日期、版本、完成状态和非诊断说明。

验收：测试账号有 5 条以上记录时全部可翻页查看；跨账号不可见；本周多量表、多维度样本汇总正确。

## T18-09：个性化训练推荐与独立训练记录

目标：推荐页面布局清晰，已完成训练卡不再重复推荐，个人中心可独立查看真实打卡记录。

实施：

1. 推荐排序综合当前目标、测评维度、最近完成、跳过、不适反馈、受控状态和用户选择；候选去重并保留推荐原因。
2. 完成一次训练卡后，默认从当前推荐候选中排除；仅在用户主动选择“再次练习”或规则要求复习时进入历史/复习区。
3. 修复节奏选择器、日期、状态和推荐卡片的对齐、稳定高度、按钮层级和长文本换行。
4. 训练卡列表不得互相覆盖；卡片显示角色、预计时长、适用场景、停止提示和完成状态。
5. 新增独立训练记录页，读取当前用户 `checkins`，展示完成时间、训练卡、帮助程度、前后观察和来源；不再跳回训练中心。
6. 增加候选去重、完成过滤、主动复练、分页、所有权和页面布局测试。

验收：完成一张卡后刷新不再出现在默认推荐；训练记录页只显示实际完成记录；卡片和按钮无重叠。

## T18-10：暑期试点包与项目测试开放

目标：让已满足治理条件的暑期试点包显示并可进入，未批准项目明确说明状态。

实施：

1. 核对 `content/programs.json`、项目 API、客户端过滤和生产环境内容版本，定位空列表来源。
2. 区分 `pilot_draft`、`pilot_approved`、`paused`、`completed`；生产用户只显示 `pilot_approved` 或明确允许预览的项目。
3. 已批准项目显示目标、适用人群、阶段、当前任务、退出权利、帮助入口和非治疗边界。
4. 暑期试点包如仍缺研究/心理/伦理签字，只能在研究者预览或开发模式展示“待开放”，不能伪装成正式项目。
5. 增加项目内容版本、筛选、权限、空状态和生产 API 测试。

验收：至少一个已批准且内容完整的项目可见；没有批准项目时空状态说明真实原因和下一步；状态机不可绕过。

## T18-11：已实现未开放能力盘点与受控开放

目标：全面盘点功能并开放满足条件的能力，同时保留伦理、版权和安全门禁。

实施：

1. 盘点维度：小程序页面、Web 页面、API、数据库表、量表、训练卡、课程、项目工具包、聚类画像、离线情感计算、社会网络分析、研究导出和人工复核。
2. 每项记录：入口、后端、数据、测试、治理状态、人工签字、权限、隐私、风险、当前开放状态和阻断原因。
3. 自动开放条件：内容引用有效、接口可用、数据库兼容、测试通过、治理状态允许、文案合规、权限和审计完整。
4. 禁止自动开放：版权未确认量表、题项/计分未核对量表、暴露/内感/睡眠限制等高风险工具、未批准项目、未经验证的实时情感判断、可识别敏感原始数据导出。
5. 离线情感计算和社会网络分析如只完成研究后台聚合链路，则只开放给研究者的脱敏只读页面，不开放给普通用户作实时判断。
6. 生成“开放、研究者受控、继续隐藏、待人工签字”四类矩阵，并同步唯一人工审核入口。

验收：不存在“代码已完成但无记录”的能力；所有开放项通过端到端测试；所有未开放项有明确阻断原因，不以技术完成替代专业批准。

## T18-12：全链路验证、视觉验收、云端发布与代码审查

验证顺序：内容来源与计分审计 → 后端专项/全量 → 小程序 JS/JSON/引用 → 登录与权限 → 数据所有权 → Web typecheck/build → Playwright/真机截图 → CloudBase `/healthz`、`/readyz` → 真机微信/手机号授权 → `git diff --check`。

代码审查重点：

1. 用户身份、研究者角色和跨账号数据是否可伪造。
2. 微信/手机号失败是否能定位到具体外部配置，不泄露 secret、openid 或手机号。
3. 时间轴、测评和训练记录是否真正持久化并支持完整历史。
4. 反馈和训练推荐是否绑定本次记录，是否错误使用占位值或唯一处方。
5. 量表指导语、题项、选项、反向题、维度和计分是否与来源一致。
6. 聚类与图表是否在移动端重叠，是否把题号或内部编码当用户维度。
7. 已完成训练过滤是否允许用户主动复练，是否错误删除历史记录。
8. 项目和功能开放是否绕过治理状态、签字、版权或安全门禁。
9. 文案是否包含诊断、人格定性、治疗承诺、危机服务承诺或责备表达。
10. 云端包是否包含最新 backend/content/shared，schema 与内容版本是否可核验。

完成后输出：任务十八基线审计、量表全量审计、开放能力矩阵、视觉验收截图、代码审查报告、CloudBase 发布包和外部人工验收证据表；同步更新 `项目进度统一口径.md`、`开发日志.md`、`当前进度交接.md`、`开发说明.md`、`待人工审查内容合集.md`。

## 2. 任务十八执行顺序

1. T18-00 基线冻结、截图映射与既有改动审查。
2. T18-01 登录链路。
3. T18-02 研究者账号。
4. T18-03 关系成长记录和时间轴。
5. T18-04 情绪温度计。
6. T18-05 情绪反馈数据绑定。
7. T18-06 全量量表审计。
8. T18-07 聚类画像与图表。
9. T18-08 完整测评记录与本周维度。
10. T18-09 推荐和训练记录。
11. T18-10 暑期试点包。
12. T18-11 受控开放盘点。
13. T18-12 全链路验收和代码审查。

前一项未完成自动验收，不进入下一项；外部微信配置、正式账号、版权和专业签字允许标记“自动开发完成/外部验收待执行”，不得写成整体已完成。

## 3. 任务十八状态表

| 子任务 | 当前状态 | 预期证据 | 自动验证 | 人工/外部边界 |
|---|---|---|---|---|
| T18-00 基线与截图映射 | 已完成 | `任务十八基线审计与截图映射_20260711.md`、`outputs/task18_baseline.json`、自动审计脚本 | 21图、12项需求、33 worksheet/34卡/5课/3项目和既有 diff 全覆盖；专项 2 passed | 真机现象需最终复验；32份启用 worksheet 治理状态待 T18-06 收口 |
| T18-01 登录链路 | 自动开发完成/外部验收待执行 | `/api/auth/capabilities`、登录页能力状态、三路径契约 | 登录/能力/隐私/小程序契约 17 passed；JS 语法通过 | CloudBase可信身份头、手机号开放接口和真机授权待验收 |
| T18-02 研究者账号 | 自动开发完成/云端创建待执行 | `bootstrap_researcher.py`、`.codex_tmp/researcher-account-20260711_220115.json` | 创建、显式轮换、旧密码失效、角色与凭据生成共 20 passed | 本机无 ADMIN_EXPORT_TOKEN；云端 apply 待负责人提供令牌环境 |
| T18-03 关系成长 | 自动开发完成/真机待验收 | growth 返回 enrollment 状态、无报名门禁、保存与时间轴刷新、表单布局 | 路由/服务/页面契约 7 passed；JS 与 diff 检查通过 | 已有 enrollment 真机保存、长表单和时间轴刷新待验收 |
| T18-04 情绪温度计 | 自动开发完成/真机截图待验收 | 三个独立数值徽标、双行滑块布局、值域收口 | 温度计/后端路由专项 13 passed；JS 与 diff 通过 | iOS/Android slider 和大字体截图待验收 |
| T18-05 情绪反馈 | 自动开发完成/真机待验收 | diary 场景/情绪/强度/想法/行为进入透明规则响应，页面去除重复触发卡 | 两组差异、所有权和高风险门禁 5 passed；JS/diff 通过 | 真机连续提交两条不同记录及反馈措辞抽查 |
| T18-06 全量量表审计 | 项目内部准入完成/外部证据待补 | 全量审计 CSV/MD、来源修复脚本、33份可执行 worksheet、HPLP 40题六维版本、生产治理门禁 | 33份量表内容审计 `blocker=0/error=0/warning=0`；项目负责人批准已记录；全量后端278 passed | 项目负责人批准不替代量表版权、正式中文版、独立心理测量和伦理证据；缺少可执行 worksheet 的目录项仍不开放 |
| T18-07 聚类画像布局 | 自动开发完成/真机待验收 | 结果页编号散点图例、图外雷达维度图例、最多6轴摘要与完整维度列表 | 页面布局、长标签、量表与路由专项 41 passed；JS/diff 检查通过 | Android/iOS 画像命名、画布和解释需真机截图确认 |
| T18-08 测评记录与周报 | 自动开发完成/真机待验收 | `assessment-history` 全记录页、分页响应、周报按量表分组的完整维度 | 分页总数/加载更多/所有权/旧版过滤/跨量表同键隔离和页面契约 42 passed；JS/JSON/diff 通过 | 真实账号5条以上历史、下拉与多量表周报需真机验收 |
| T18-09 推荐与训练记录 | 自动开发完成/真机待验收 | 服务端完成卡过滤、个性化方案稳定卡片、`training-history` 独立分页页 | 完成过滤、跨账号隔离、完成状态筛选、分页、卡片元数据、主动复练及页面契约 58 passed；JS/JSON/diff 通过 | 推荐映射仍需心理审核；真机长文案、完成后刷新和主动复练待验收 |
| T18-10 暑期试点包 | 项目负责人准入完成/独立证据待补 | 生产空状态、`availability` 状态摘要、研究者受控草案预览、提交门禁、负责人批准记录 | 三个项目均已有项目负责人内部准入决定；生产筛选、预览权限、状态机与页面契约20 passed | 研究、心理和伦理独立审核人、日期与证据路径未补齐前，项目治理状态继续保持 `pilot_draft`，不伪造三方签字 |
| T18-11 受控开放盘点 | 已完成 | `任务十八已实现能力受控开放矩阵_20260712.md`、CSV、JSON、审计脚本；训练卡/课程生产治理门禁 | 92项全覆盖；开放44、待独立证据42、历史比较1、隐藏3、研究者受控2；11个画像模型完成链接与哈希复核 | 未授权、未签字、高风险内容继续阻断；项目负责人批准不替代独立签字 |
| T18-12 全链路验收 | 自动验收完成/外部发布与真机待执行 | `任务十八代码审查与验收报告_20260712.md`、两份导师Word、待批准内容说明、外部边界清单 | 内容通过；后端278 passed；Web build/typecheck；Playwright 12 passed；小程序39页/42组件/7 Canvas/55 JS/51 JSON；Word 236页、135页、4页完成逐页视觉核验 | 本机无微信开发者工具CLI；CloudBase上传、微信/手机号、研究者云端账号、独立专业证据和真机截图待执行 |

任务十八结论：T18-00 至 T18-12 的自动可执行部分已全部完成，项目负责人已批准33份可执行量表、当前画像模型及三个项目的内部试点准入。HPLP 当前版本统一为牛至旭研究所对应的40题、六维版本；旧HPLP模型仅作历史比较。不得把负责人内部准入写成版权许可、专业独立签字、伦理批准、CloudBase发布或真机验收。
## 任务十九：关系探索量尺、训练卡、站内消息与阶段性反馈优化

更新时间：2026-07-15

### 19.0 规划依据与任务定位

本任务依据用户提供的《关系成长小程序推荐训练卡内容整理.docx》、6 张小程序截图、当前代码和任务十二/十七/十八事实基线制定。执行前已确认当前工作区包含大量其他对话的未提交改动；本轮不得回退、覆盖或顺手重构无关内容。

本轮只处理以下范围：

1. 将 `regulatory_focus_relationship_18`（用户所称“关系中的行动方式问卷”，当前展示名“关系情境中的行动关注方式”）从错误的 7 点作答改为 9 点作答，并同步内容源、服务端校验、数据库内容、聚类输入换算和测试；既往训练样本仍为 1—5，禁止把 1—9 原值直接送入原 GMM。
2. 用 Word 中 8 张关系成长训练卡替换关系成长推荐子集；尽量复用稳定卡 ID，保留历史打卡和引用，不删除无关训练卡。
3. 打通“研究者在研究者仪表盘发送消息 → 参与者消息列表收取”的站内消息路径，并补齐鉴权、长度限制、幂等、审计、分页/筛选和已读能力。
4. 只审查小程序接口，不做接口统一、重命名或重构；单独输出接口混乱审查报告。
5. 修复“三步开始”页面窄屏文字裁切、横向溢出和底部按钮错位，只改必要 WXML/WXSS。
6. 让阶段性报告支持研究者填写、保存、确认并交付反馈；五阶段第 4 步由“研究者反馈”改为“阶段性反馈”；适度整理成长仪表盘的信息层级、空态和来源标识。

继续遵守：非诊断、非标签化、非评判；高风险内容优先现实支持和人工复核；不删除 `pages/integration-test/index`；不破坏记录→反馈→训练→打卡核心链路；接口审查项不顺手改代码。

### 19.1 新功能前置十问

| 问题 | 结论 |
|---|---|
| 是否服务核心闭环 | 是，服务测评→反馈→练习→追踪→人工支持 |
| 是否修改数据库 | 量尺本身复用 `assessment_worksheets.questions_json`，不新增量尺列；消息补充发送者与幂等字段需要幂等迁移 |
| 是否修改 API | 是，新增研究者发信、消息分页/筛选/全部已读、阶段报告研究者反馈保存能力 |
| 是否修改 shared | 是，同步消息与关系试点契约；小程序 API client 同步 |
| 是否影响两端一致性 | 是，后端为唯一事实源；不在小程序另建训练卡或消息数据 |
| 是否修改 content | 是，量表内容、画像模型输入换算、关系成长训练卡和推荐映射 |
| 心理/伦理风险 | 有；训练建议保持支持性，研究者消息做风险预检且不承担实时危机干预 |
| 最小方案 | 保持现有路由、表和卡 ID，局部扩展字段与页面 |
| 如何测试 | 内容校验、量表计分/画像、消息端到端、关系报告、页面契约、JS/JSON、Web build、后端全量 |
| 如何回滚 | 逐文件回退本任务变更；不删除历史结果；消息新增列为向后兼容可空列 |

### 19.2 执行任务

#### T19-00 基线与附件核对

- 读取当前事实文档、任务十二/十七/十八记录、Word 和截图。
- 记录 dirty worktree、安全缺口和历史 1—5 聚类训练事实。
- 完成后再开始写代码。

#### T19-01 九点计分与聚类兼容

- 将 `regulatory_focus_relationship_18` 的 18 题选项改为 1—9，补充明确的量尺元数据与说明。
- 同步 `scale_item_drafts.json`、`assessment_worksheets.json`、`scales_catalog.json`、任务十二构建脚本和数据库导入结果。
- GMM 仍基于既往 1—5 数据；将每个 feature 的 `linear_range.input_max` 从 7 改为 9，输出仍为 1—5，并重算 artifact hash。
- 增加 9 点边界、非法选项、1/5/9 映射和画像一致性测试；不重训既往模型，不改历史答卷。

#### T19-02 关系成长训练卡替换

- Word 权威内容为 8 张：自我支持、一分钟情绪观察、情绪命名、自动想法、第二种说法、温和表达、开放问题、带边界微行动。
- 保留可复用卡 ID；新增缺失卡时使用稳定英文 ID；旧关系卡不直接删除，必要时停用并迁移推荐引用。
- 同步训练卡内容、关系测评推荐映射、项目引用、后端返回和用户端详情展示；审核状态保持真实。

#### T19-03 研究者站内消息闭环

- 明确用户路径：研究者账号→我的→研究者仪表盘→选择参与者→发送消息；参与者账号→我的→消息→消息详情。
- 新增研究者/督导/管理员发送接口，收件人限定为其可查看的关系试点 enrollment，禁止任意跨用户发信。
- 增加标题/正文长度、风险预检、幂等键、发送者、审计；参与者消息列表增加分页、状态/类型筛选和全部已读。
- 新增端到端测试，验证发送后参与者列表出现未读消息、打开后变已读、重复幂等请求不重复创建。

#### T19-04 小程序接口只读审查报告

- 建立“页面→`services/api.js`→后端 route→表/content→鉴权→状态/错误码”矩阵。
- 报告重复封装、参数漂移、直接请求、角色/权限不一致、死入口、安全缺口和文档差异。
- 本子任务不修改接口实现。

#### T19-05 三步开始页面排版修复

- 修复窄屏长文案横向裁切，视觉链路允许换行/纵向布局。
- 底部主次按钮在安全区内稳定显示；保留单主动作和 44px 等效触控目标。
- 不改三步业务逻辑和跳转路径。

#### T19-06 阶段性报告反馈、步骤命名与成长仪表盘

- 阶段性报告新增研究者反馈草稿、保存/确认/交付状态；参与者只能看到已交付内容。
- 第 4 步统一改名“阶段性反馈”，语义为线上探索后的人工补充；第 2 步仍是“阶段性报告”。
- 阶段性反馈同时进入消息列表和成长时间轴，清楚区分“用户记录/系统汇总/研究者反馈”。
- 成长仪表盘分开次数指标、量尺维度和画像维度，补充数据不足空态并减少拥挤。

#### T19-07 验证、审查与文档收口

- 运行内容校验、专项测试、后端全量、Web typecheck/build、小程序 JS/JSON 和 `git diff --check`。
- 人工项保留：微信开发者工具、iOS/Android 真机、CloudBase 发布与真实账号消息收取。
- 更新 `开发日志.md`、`当前进度交接.md`、`开发说明.md`、API 文档、数据库字段说明和专项报告。

### 19.3 状态表

| 子任务 | 状态 | 证据 | 自动验证 | 人工边界 |
|---|---|---|---|---|
| T19-00 基线与附件核对 | 已完成 | 本计划与附件提取记录 | 文档/代码/原始表只读核对 | Word 内容心理审核仍由负责人确认 |
| T19-01 九点计分与聚类兼容 | 自动开发完成 | 九点内容库、同步脚本、前端九宫格、1—9→1—5转换与模型哈希 | 量表/评估专项通过 | 量表版本最终签字 |
| T19-02 训练卡替换 | 自动开发完成 | 8张关系专用卡及三份关系量表、项目映射 | 内容校验、任务17审计通过 | 逐卡心理/伦理审核 |
| T19-03 研究者消息闭环 | 自动开发及复核整改完成 | `POST /api/messages`、分页/已读/幂等、研究者自动认领、停用报名阻断、响应字段最小化及工作台表单 | 关系试点消息闭环和跨研究者拒绝测试通过 | 云端真实账号与真机收取 |
| T19-04 接口只读审查报告 | 已完成 | `任务十九小程序接口只读审查报告_20260715.md` | 只读扫描 | P0展示权限另立修复，不在本任务重构 |
| T19-05 三步排版 | 自动开发完成 | getting-started溢出防护、九点网格与通用步骤标题 | 页面契约、JS语法 | 开发者工具/真机截图 |
| T19-06 阶段性反馈与仪表盘 | 自动开发及复核整改完成 | 报告PATCH新增不可变版本、反馈风险预检、阶段反馈消息绑定新版本、时间轴、第4步与自适应图表 | 关系试点和小程序契约通过 | 研究者真实流程验收 |
| T19-07 验证与收口 | 自动验证完成 | API/数据库/shared/事实文档同步 | 内容、后端286 passed、小程序39页/55 JS/51 JSON、Web typecheck/build通过 | CloudBase 发布；展示角色绕过按负责人要求暂不关闭 |

### 19.4 下一轮启动提示词

```text
请继续执行 Claude计划模式任务十九。先检查 T19 状态表和当前 git diff，绝不回退其他聊天的未提交改动；从第一个未完成子任务继续。接口混乱项只更新审查报告，不做接口重构。完成代码后同步三份事实文档，并保留微信开发者工具、真机和 CloudBase 为人工验收。
```

## 任务二十：小程序全链路体验、研究者全模块工作台与网站视觉优化

更新时间：2026-07-17

### 20.0 任务定位

本任务依据用户提出的16项优化需求、`改错用图第三`目录12张截图、现有任务十八/十九实现和公开科研平台模式制定。它是一个大型开发任务，按可独立验收的小任务自动推进。

总体目标：

1. 参与者端形成“记录→支持性反馈→节奏化训练→复盘→人工支持→项目试点→阶段性反馈→成长仪表盘”的连续闭环。
2. 研究者端形成“参与者检索→单人全模块档案→审阅→备注/反馈→消息交付→审计”的工作闭环。
3. 统一小程序与Web的信息层级、字段显示名、视觉令牌和非诊断内容边界。

权限解释：用户所说“研究者查看所有参与者的所有数据”按研究伦理与最小权限落地为“研究者查看其被授权/分配参与者的全部业务模块；研究负责人、督导或管理员查看全体”。禁止恢复任意研究者跨项目、跨参与者读取原文的越权路径。

推送解释：本任务实现站内到期提醒、今日训练队列和节奏驱动推荐。微信系统订阅消息需要用户授权、模板审核和云端定时任务，作为外部配置验收，不在本地代码中伪装为已完成。

### 20.1 关系探索试点完整运行链路

#### 参与者填写与反馈

1. 参与者从“小程序→项目测试/关系探索试点”进入，完成关系测评并创建 `relationship_pilot_enrollments` 报名。
2. 后端根据量表结果保存 `assessment_results` 和关系报名中的维度/画像快照，生成阶段性报告候选 `relationship_screening_reports`。
3. 参与者在“关系探索试点”看到五阶段路径：起点测评→阶段性报告→线上探索→阶段性反馈→连续记录。
4. 线上探索材料保存到 `relationship_pilot_tasks`；每周补充和关键事件保存到 `relationship_longitudinal_entries`。
5. 系统报告在“小程序→关系探索试点→查看阶段性报告”呈现；研究者交付的阶段性反馈同时进入“小程序→我的→消息”和“关系成长仪表盘→成长时间轴”。
6. 参与者后续可在关系成长仪表盘查看曲线、时间轴、系统汇总、研究者反馈和下一步，不显示诊断或疗效结论。

#### 对应后端

- 路由：`backend/routes/relationship_pilot_routes.py`
- 报名：`backend/services/relationship_enrollment_service.py`
- 报告与阶段反馈：`backend/services/relationship_report_service.py`
- 线上任务与研究备注：`backend/services/relationship_task_service.py`
- 成长曲线/时间轴/研究队列：`backend/services/relationship_growth_service.py`
- 消息：`backend/routes/messages.py`、`backend/services/message_service.py`
- 表：`relationship_pilot_enrollments`、`relationship_screening_reports`、`relationship_pilot_tasks`、`relationship_research_notes`、`relationship_longitudinal_entries`、`messages`、`audit_logs`

#### 研究者查看与反馈路径

1. 小程序轻量路径：“我的→研究者评估仪表盘→选择参与者→查看关系报告/任务→填写阶段性反馈或发送消息”。
2. Web完整路径：“研究后台→参与者→按用户ID/状态/项目检索→单人档案→测评/日记/训练/项目/关系试点/人工支持/消息→审阅或反馈”。
3. 阶段性反馈不覆盖旧报告，保存为新的报告版本；发送后生成 `relationship_stage_feedback` 消息并写审计。
4. 参与者在消息详情和成长时间轴看到已交付内容；未确认草稿不对参与者展示。

### 20.2 新功能前置十问

| 问题 | 结论 |
|---|---|
| 是否服务核心闭环 | 是，覆盖记录、反馈、练习、追踪和人工支持 |
| 是否修改数据库 | 人工支持关联测评需兼容字段；项目逐题答案可继续使用 `records.data_json`；节奏继续使用现有 assignment 记录 |
| 是否修改API | 是，新增可关联记录列表、参与者全模块摘要/详情、项目记录回看、节奏到期计算 |
| 是否修改shared | 是，同步研究者档案、关联记录、项目答案和训练节奏响应 |
| 是否影响两端一致性 | 是，Web和小程序共用后端显示名与状态映射 |
| 是否修改content | 是，优化反馈规则、日记训练映射和用户显示名；不绕过治理状态 |
| 心理/伦理风险 | 原文访问、研究者反馈和推荐存在风险；采用最小权限、审计、不可变版本和非诊断措辞 |
| 最小实现 | 复用现有表、`records`、消息、关系报告、训练计划，不新建平行系统 |
| 如何测试 | 服务/路由、权限、页面契约、JS/JSON、内容校验、Web build、Playwright和真机清单 |
| 如何回滚 | 子任务独立提交；新增响应向后兼容；不删除历史表、字段和记录 |

### 20.3 子任务

#### T20-00 基线、截图映射与设计研究

- 建立 `design/context.md`、`design/research.md`、`design/audit.md`。
- 将12张截图逐一映射到页面、接口、数据源、现象和验收。
- 冻结当前dirty worktree，禁止回退其他对话的三份事实文档改动。

#### T20-01 首页消息中心

- 使用明确的铃铛/消息语义结构替换不完整CSS轮廓，保留未读红点和可访问标签。
- 统一72rpx触控区、图标24px等效尺寸、按压态和未读数量语义。
- 验收：首页常规、未读和大字体状态不变形。

#### T20-02 情绪温度计控件

- 加减按钮使用圆角胶囊/圆形触控面，说明文字独立排布；刷新按钮设置固定最小高度、flex居中和圆角。
- 保持1—10单一状态源和现有提交字段。
- 验收：窄屏、iOS/Android微信内核下文字和符号居中。

#### T20-03 情绪日记顶部与文案

- 删除“用于生成支持性反馈，不评价谁对谁错”，保留简洁隐私提醒。
- 顶部改为“具体事件—情绪—反应—下一步”的轻量进度说明，减少重复边界卡。
- 验收：首屏能直接看到核心记录字段，标题、说明、标签不挤压。

#### T20-04 反馈规则与推荐卡专业审查

- 从心理、产品和工程三层审查 `feedback_rules.json`、`diary_training_map.json` 和反馈服务。
- 反馈顺序统一为“先确认感受→描述本次可观察线索→给一个可选择的小动作→说明边界”。
- 推荐只给1个主卡+最多2个备选；去重、过滤完成/受控卡，不把规则编码或唯一处方展示给用户。
- 高风险继续阻断普通推荐并引导现实支持。

#### T20-05 情绪事件记录板块

- 必填区优先：场景、具体经过、主要情绪；可选线索折叠：身体感受、孩子反应、想法、行为。
- 优化芯片、输入框、帮助文字、草稿/提交状态和底部主按钮。
- 后端字段保持兼容，不删除历史数据。

#### T20-06 情绪事件反馈内容与视觉

- 首屏显示“这次记录里看见什么”和“今天先做哪一步”。
- 练习卡区域显示标题、预计时长、推荐原因、开始练习；人工支持为次动作。
- 保存反馈改为明确的收藏/记录行为，避免与训练主动作竞争。

#### T20-07 三步开始完整闭环

- 反射弧由横向超宽图改为窄屏可读的换行节点/纵向链路。
- 第二步“标一个位置”下直接呈现“在反馈中定位→记录一次→去训练中心”的关联动作。
- 底部安全区、按钮文字和主次层级统一。

#### T20-08 人工支持关联记录

- 小程序允许选择“未关联、某条情绪日记、某次支持性测评”。
- 新增当前用户可关联记录列表；提交时保存 `source_type/source_id/source_title` 并校验所有权。
- 研究者/督导查看请求时能打开关联记录的只读详情；原始填写不可被回复接口修改。
- 优化边界、联系方式、风险提示和提交成功状态。

#### T20-09 本周复盘

- 建立训练卡ID、规则键、互动模式和状态的统一中文显示名。
- 修复 `one_open_question`、`general_support` 等内部字段；未知键显示通用用户语言，不回显原键。
- 重排为“本周摘要→记录与练习→可观察线索→下周一步”，减少重复说明。

#### T20-10 个性化训练节奏

- assignment新增服务端派生字段：`is_due_today`、`next_practice_date`、`cadence_label`、`due_reason`。
- 节奏参与推荐排序和今日训练队列；暂停/完成时不生成到期主推荐。
- 卡片显示用户标题而非ID，文字/按钮居中；完成后刷新下一次日期。
- 微信订阅消息列为外部能力，站内消息可在到期时由受控调度任务生成。

#### T20-11 项目测试逐节逐题填写与回看

- 三个项目的第1—3节均使用同一动态表单：书写提示文本框 + 每个反思问题独立文本框。
- 草稿按项目、节次和问题保存；提交 `answers.reflection_answers[]`，保留旧 `reflection` 摘要兼容。
- 新增本人项目记录列表/详情，研究者档案可查看已授权原文、节次、前后不适和不良体验标记。
- 验收：三个项目、九个节次均可填写、提交、回看。

#### T20-12 研究者全模块评估工作台

- Web作为完整工作台，小程序保留轻量处理。
- 新增参与者矩阵：用户ID检索、项目/批次、角色范围、待复核、高风险、最后活动、分页。
- 单人档案标签：测评、情绪日记、训练打卡、项目测试、关系试点、人工支持、消息、审计摘要。
- 敏感详情查看写审计；研究者仅看被分配参与者，负责人/管理员看全体。
- 状态全部使用用户/研究语言，不显示 `pending_review` 等内部键。

#### T20-13 关系成长仪表盘

- 顶部增加“当前阶段、最近记录、下一步”摘要。
- 曲线指标分组，数据不足时显示解释性空态；标签和值在网格中居中。
- 时间轴使用中文来源标签和简短摘要；反馈原文按需展开。
- 成长报告按“变化线索、重要事件、参与者原话、研究者反馈、下一步”排序。

#### T20-14 研究者阶段性反馈

- 完善草稿、风险预检、确认、发送、版本、消息和时间轴状态。
- 反馈表单提供结构化提示：观察到的变化、可核对依据、建议的一小步、需继续讨论的问题。
- 已发送版本只读；修改生成新版本；参与者只看到已发送版本。

#### T20-15 全用户成长仪表盘

- 复用关系成长仪表盘的信息架构，新建通用成长页。
- 聚合测评、情绪温度、情绪日记、训练、项目记录、周报和人工反馈。
- 每类指标保持原单位，禁止把不同量尺混在同一数轴；样本不足不判断趋势。

#### T20-16 网站全量优化

- 参考脑岛/见数的科研任务组织、OpenClinica参与者矩阵和mindLAMP模块分层，但沿用本项目暖白/低饱和绿视觉。
- 优先优化全局导航、仪表盘、参与者矩阵、单人档案、量表审阅、训练卡、项目和消息页面。
- 统一页面容器、标题层级、筛选条、表格、状态标签、空态、加载/错误和响应式行为。
- 不复制小程序日常流程，不把后台复杂度转移给参与者。

#### T20-17 验证、视觉QA与文档收口

- 后端专项/全量、内容校验、小程序JS/JSON/引用、Web typecheck/build、Playwright、`git diff --check`。
- 视觉QA覆盖12张问题截图对应页面、375/430/768/1440视口、空/加载/错误/成功状态。
- 更新API、数据库、shared、项目统一口径、开发日志、交接、开发说明和专项验收报告。
- 外部验收：微信开发者工具、Android/iOS真机、订阅消息模板、CloudBase部署。

### 20.4 执行批次

1. A批：T20-00—T20-03，视觉基础与首屏问题。
2. B批：T20-04—T20-09，情绪记录、反馈、人工支持和周报。
3. C批：T20-10—T20-11，节奏驱动训练与项目逐题填写。
4. D批：T20-12—T20-15，研究者全模块工作台与两类成长仪表盘。
5. E批：T20-16—T20-17，网站全量视觉收口、测试和发布资料。

### 20.5 当前状态

| 子任务 | 状态 | 备注 |
|---|---|---|
| T20-00 | 已完成 | 12张截图已审计；设计上下文、研究和审计文档已建立 |
| T20-01—T20-03 | 自动开发完成/视觉待验收 | 首页消息、温度计、日记首屏已调整 |
| T20-04—T20-09 | 自动开发完成/真机待验收 | 五条基础规则专业修订；42张训练卡完成逐卡结构与文案复核；推荐卡去重过滤限3、记录可选折叠、反馈页单主练习、三步闭环、人工支持关联和周报显示名已完成 |
| T20-10—T20-11 | 自动开发完成/真机待验收 | 节奏驱动到期与推荐；项目逐题填写、本人回看与所有权测试 |
| T20-12—T20-15 | 自动开发完成/真实账号待验收 | 研究者参与者矩阵与全模块只读档案、关系成长排版、结构化阶段反馈、通用成长仪表盘已实现；真实角色双账号与真机联调待验收 |
| T20-16—T20-17 | 自动开发与本地验收完成/外部验收待执行 | 17个后台路由完成中文状态收口；430/1440双视口无横向溢出和内部键泄漏，移动端按钮不低于44px；294个后端测试、Web typecheck/build、小程序56 JS/52 JSON和内容校验通过 |

### 20.6 下一轮启动提示词

```text
任务二十本地自动开发已收口。下一轮只执行外部验收：配置微信开发者工具 CLI 后运行小程序自动检查，使用参与者/研究者真实双账号验证站内消息和阶段反馈，在 Android/iOS 真机核对字体放大、空态和安全区；微信订阅消息还需模板、用户授权和受控调度。不得把本地通过写成已部署或已获心理/伦理批准。
```

## 任务二十一：训练卡体验、微信订阅提醒与全产品复审整改

更新时间：2026-07-18

### 21.0 任务定位

按“训练卡专业复审与整改 → 微信订阅消息闭环 → 全界面、内容和技术复审整改”顺序执行。训练卡与反馈继续保持支持性、非诊断、非标签化；微信提醒必须由用户在明确动作后主动授权，拒绝或关闭不影响站内功能。

### 21.1 新功能前置十问

| 问题 | 结论 |
|---|---|
| 是否服务核心闭环 | 是，服务练习选择、按节奏执行、复盘和必要提醒 |
| 是否修改数据库 | 是，新增订阅偏好与投递记录表，保留幂等、失败和撤回状态 |
| 是否修改 API | 是，新增订阅能力、授权结果、偏好查询和受控到期调度接口 |
| 是否修改 shared | 是，同步通知偏好、能力和投递摘要契约 |
| 是否影响两端一致性 | 是；后端是提醒状态唯一事实源，小程序只发起微信授权并回传结果 |
| 是否修改 content | 训练卡仅做必要文案/元数据调整；不擅自升级治理状态 |
| 心理与伦理风险 | 防止催促、羞耻、依赖和危机替代；提醒文案只说“可练一次”，不评价坚持或效果 |
| 最小实现方案 | 训练卡渐进披露；练习完成采用冷却排序；保存节奏后自愿订阅；定时任务幂等发送 |
| 如何测试 | 内容契约、推荐冷却、授权接受/拒绝/关闭、缺模板、缺 openid、重复调度、供应商失败和页面契约 |
| 如何回滚 | 关闭发送开关；保留站内消息；新增表和字段向后兼容；前端隐藏订阅入口即可 |

### 21.2 子任务

#### T21-01 训练卡四专业视角评审

- 心理内容：观察—选择—小步—复盘，避免读心、保证性承诺和把训练完成等同改善。
- 产品体验：列表只突出一张主练习，备用卡压缩；详情渐进展开。
- 工程：推荐兼顾语境、近期完成、帮助程度、治理状态和节奏，不永久排除已完成卡。
- UI美术：延续暖白/低饱和绿；橙色仅用于重点提示，不用多色争夺注意；卡片层级减少。

#### T21-02 训练卡内容、推送逻辑与页面整改

- 推荐页首屏仅展示“为什么推荐、今天做什么、需要多久、开始”。
- 停止规则、示例、完成标准和边界按需展开；备用卡使用紧凑列表。
- 完成卡改为短期冷却后可再次练习，不再永久移除；无替代卡时允许重复巩固。

#### T21-03 微信订阅提醒闭环

- 保存练习节奏后，由用户点击按钮调用 `wx.requestSubscribeMessage`；不在启动页自动弹窗。
- 保存接受、拒绝、关闭和未完成状态；展示修改路径，拒绝不阻断训练。
- 服务端新增模板能力、订阅偏好、到期投递、幂等和审计；默认关闭真实发送。
- 受控定时任务只处理当日到期、主动订阅、有 openid 的用户；供应商失败不消耗本地授权状态。
- 真实发送仍依赖公众平台模板 ID、模板字段映射、AppID/AppSecret、CloudBase 定时触发和真机授权。

#### T21-04 全产品复审与高优先级整改

- 复查导航、首页、记录、反馈、训练、项目、成长、消息、人工支持和研究后台的层级、术语、错误恢复与技术一致性。
- 只改高影响且可自动验证的问题；不借机重构稳定接口或扩大临床承诺。

#### T21-05 验证与收口

- 内容校验、后端专项/全量、Web typecheck/build、小程序 JS/JSON/页面契约、浏览器双视口、`git diff --check`。
- 更新 API、数据库、三份事实文档、设计 QA 和专项评审报告。
- 外部保留微信模板审核、真实授权、CloudBase 调度、Android/iOS 和真实账号投递。

### 21.3 当前状态

| 子任务 | 状态 | 备注 |
|---|---|---|
| T21-01 | 已完成 | 四视角评审已写入专项文档，结论为内容基础稳健、选择前信息过载 |
| T21-02 | 已完成/真机待验收 | 主卡渐进披露、备用卡紧凑化、卡库折叠、7天冷却降权已实现 |
| T21-03 | 本地闭环完成/外部平台待接入 | 授权、偏好、到期调度、幂等、重试和审计已实现；真实发送默认关闭，模板仍需申请审核 |
| T21-04 | 已完成 | 全产品复审报告已建立；本轮只改训练、提醒和高影响文案，不重复大改任务二十稳定页面 |
| T21-05 | 本地验证完成/外部验收待执行 | 后端297项全量及15项专项、Web typecheck/build、小程序56 JS/52 JSON和前端审计通过 |

### 21.4 下一轮启动提示词

```text
任务二十一本地代码已经收口。下一轮不要重复开发订阅服务；由小程序管理员申请并审核中性练习提醒模板，按真实字段配置环境变量，先保持发送关闭调用run-due dry-run，再在测试版真机覆盖同意、拒绝、禁止、一次授权消耗、失败重试和同日去重。未完成平台审核、真机投递和心理伦理签字前，不得写成正式上线或专业批准。
```
## 任务二十二：P1 数据连续性与研究运营监控、P3 性能架构优化（2026-07-18）

### 本轮范围

- 明确不执行 P0：不开展试点发布验收、量表/训练卡/反馈规则人工签字放行。
- P1-01：匿名试用记录由参与者登录后主动确认，事务化认领到正式账号；默认不自动合并。
- P1-02：研究者工作台增加通知授权、发送结果、失败重试、阶段反馈和人工支持积压的脱敏运营视图。
- P3-01：收敛 Web ECharts 引入方式、并行化研究总览二段取数、统一新增 API 命名与类型。

### 开发前十项分析

| 问题 | 结论 |
| --- | --- |
| 1. 是否属于核心闭环 | 是。账号连续性保证记录、反馈、练习可持续；运营监控保证人工支持与提醒不中断。 |
| 2. 是否修改数据库 | 是。新增 `data_claims` 认领流水表，保留认领前后、状态和各模块数量；不删除旧字段。 |
| 3. 是否新增或修改 API | 新增 `GET /api/auth/data-claim-preview`、`POST /api/auth/data-claim`、`GET /api/research/operations`；登录接口只补充匿名候选登记。 |
| 4. 是否修改 shared | 是。补充端点常量、认领与运营监控类型。 |
| 5. 是否影响小程序与网页一致性 | 是。两个客户端共用同一认领契约；小程序在“我的”显示确认卡，Web 登录后显示确认步骤。 |
| 6. 是否影响内容库 | 否。不修改训练卡或反馈规则内容。 |
| 7. 心理与伦理风险 | 不展示原始文本、OpenID、密钥或联系方式；认领必须登录、显式确认、可审计、幂等，失败时整笔回滚。 |
| 8. 最小实现 | 只迁移现有参与者归属字段；不合并账号凭证，不自动删除匿名账号，不改研究原始内容。 |
| 9. 如何测试 | 覆盖未登录、角色限制、候选隔离、显式确认、幂等、事务计数、研究者分配范围和敏感字段缺失；再跑后端全测、Web 类型检查/构建、小程序静态检查。 |
| 10. 如何回滚 | 代码可按提交回退；认领前无数据变更。已完成认领保留流水和审计，不做静默反向迁移，必要时由管理员依据流水受控处理。 |

### 实现顺序与验收标准

1. 数据库与后端认领服务：候选由登录设备匿名 ID 建立；预览只返回模块数量；确认后单事务更新归属并写审计；重复确认返回已完成结果。
2. 小程序与 Web：不阻断登录；仅在存在旧记录时显示“合并本机试用记录”，用户可确认或暂不处理；文案不暗示数据丢失或强迫选择。
3. 运营监控：研究员只统计已分配参与者，督导/管理员统计全量；失败原因只返回错误代码与次数，不返回错误原文。
4. 性能与架构：ECharts 改为按需注册；研究总览依赖首批结果的详情请求并行执行；长档案列表启用浏览器延迟渲染提示。
5. 验收：P0 状态不变；临时展示越权不关闭；后端测试、Web 构建、内容校验与差异检查通过。

## 任务二十三至三十四：全量深化优化（2026-07-18）

### 任务定位

本组任务不重复任务二十至二十二已经完成的页面、消息、训练节奏、研究者档案、订阅后端、匿名认领和运营统计。下一阶段从“继续扩展功能”转向“收敛主旅程、允许用户纠正系统、补齐数据生命周期、把研究统计变成处置工作流、统一契约和内容治理”。

AI 自由问答仅进入受控准备阶段：用户可以自由输入，但模型范围不自由；默认关闭，不接真实参与者，不使用参与者原文训练。情感计算和网络分析继续沿用 `analysis/text_analysis/` 唯一离线路径，不向普通用户实时推断。

### 任务顺序

1. **任务二十三**：今日任务主入口、协作式反馈评价、显式反馈驱动推荐、统一成长入口和视觉回归。
2. **任务二十四**：删除申请状态、受控处理、范围预览/dry-run、撤回研究授权联动。
3. **任务二十五**：研究运营数字下钻、领取/处理/关闭、通知失败重试工作流。
4. **任务二十六**：分页/错误/状态兼容契约、共享类型漂移检查、关系试点内部服务拆分。
5. **任务二十七**：内容版本、草稿 diff、校验、回滚和合成案例回放。
6. **任务二十八**：AI 合成安全集、批准知识库、fake provider、安全双检和研究者沙盒；人工门禁未通过前不进入参与者试点。
7. **任务二十九**：公开数据授权登记、标签映射、情感计算基准、公开图算法验证和中文合成金标准。
8. **任务三十**：心理测量注册、估计量、过程/安全指标、缺失流失、纵向分析和报告标准冻结。
9. **任务三十一**：身份、对象授权、导出、隐私删除和AI提示注入/跨用户检索威胁模型。
10. **任务三十二**：关键旅程SLO、结构化追踪、可靠队列、迁移恢复、功能开关和故障演练。
11. **任务三十三**：页面状态矩阵、参与者/研究者信息架构、设计模式库、可访问性、弱网恢复和认知访谈。
12. **任务三十四**：能力注册表、不可变发布包、数据集卡/模型卡、变更回放、漂移/不良事件和停用治理。

### 自动执行入口

精确到可领取切片、依赖、验收、停止条件和恢复状态机的清单：

```text
docs/01_当前执行入口/任务二十三至二十九逐步开发任务清单.md
docs/01_当前执行入口/任务二十三至三十四全量深化优化总蓝图_20260718.md
docs/01_当前执行入口/任务二十三至三十四治疗性评估受控接入子线_20260719.md
docs/05_伦理试用/任务三十心理测量与研究方法冻结准备_20260718.md
```

AI 方案与公开数据结论：

```text
docs/06_产品规划/受控AI自由问答准备方案_20260718.md
docs/02_专项进度与验收/情感计算与网络分析公开数据集适配报告_20260718.md
```

### 当前状态

| 任务 | 状态 | 自动执行起点 |
|---|---|---|
| 任务二十三 | completed_local / external_pending | T23-00至T23-05本地验证完成；微信开发者工具和真机待验收 |
| 任务二十四 | engineering_complete_local / release_approval_pending | T24-F01至F10本地工程与证据包完成；外部门禁未签字 |
| 任务二十五 | engineering_complete_local / release_approval_pending | T25-F01至F08本地工程完成；外部门禁未签字 |
| 任务二十六 | engineering_complete_local / release_approval_pending | T26-F01至F07本地契约、模块、漂移与回滚闭环完成；外部验收待执行 |
| 任务二十七 | engineering_complete_local / release_approval_pending | T27-F01至F08本地完整；真实审稿、版权、云/真机/生产待人工 |
| 任务二十八 | planned / human-gated | T28-01 合成安全评测；T28-00 未确认前不得开放真实用户 |
| 任务二十九 | engineering_complete_local_synthetic / public_dataset_ingest_blocked_human_rights_gate | 合成基准完成；公开权利审查、双人标注与发布批准待人工 |
| 任务三十 | engineering_complete_local_pre_freeze / human_gate | F00—F09工程完成；负责人、伦理、数据、方法冻结与真实结果访问仍阻断 |
| 任务三十一 | in_progress | T31-00已登记，T31-01新增对象矩阵已验证；展示越权保留 |
| 任务三十二 | documented | T32-00本地SLO已登记；云环境目标未冻结 |
| 任务三十三 | engineering_complete_local / external_pending | T33-F01—F06工程完成；大字体/读屏/微信/Android/iOS/认知访谈待人工 |
| 任务三十四 | engineering_complete_local / external_pending | T34-F01—F09工程完成；人工、伦理、云、真机和生产门禁待外部证据 |

### 推荐首轮

先执行事实和门禁波次：T23-00、T30-00、T31-00、T32-00、T33-00、T34-00；随后顺序执行 T23-01、T23-02，形成“首页知道做什么—完成记录/练习—评价反馈—不适时转人工”的最小闭环。T28 只并行准备合成安全评测和批准知识库清单；T29 只做授权登记，不下载授权不清的数据。

### 首页实现冻结决策（2026-07-19）

- 保持当前小程序首页界面和既有区块，不进行首页整体改版。
- T23-01 仅在“测一测/情绪日记”之后、“三步开始”之前新增“今天的一小步”横向卡片。
- 该卡片是唯一随参与者状态变化的主行动；现有固定入口、最近记录、阶段性反馈和消息中心继续保留。
- 卡片必须覆盖加载、无任务、继续记录、到期训练、新反馈、暂停、已完成和接口失败；失败不得显示为无任务。
- 未经负责人另行确认，不折叠、删除或移动首页现有区块。

### 治疗性评估受控接入决策（2026-07-19）

- 治疗性评估本身不新增独立大任务，也不建立与现有记录、报告、消息、训练和成长时间线平行的系统；继续按治疗性评估子线映射进T23—T34。2026-07-22新增的任务三十五仅用于公开数据验证与候选模型优化，不承载治疗性评估平行系统。
- 用户端名称使用“会前自我了解准备”或“协作式支持性评估”；当前只允许合成数据L0内部原型。
- 首页不新增永久治疗性评估模块；只有存在获准且进行中的流程时，“今天的一小步”才显示继续准备、补充资料、确认反馈、微行动或随访。
- 先执行TA-00权威方案/门禁登记和TA-01七对象复用矩阵，再决定数据库、API和页面增量。
- D01—D26、真实责任链和研究门禁未完成前，真实参与者、L1—L2、多人路径、完整TA和AI用户输出继续阻断。
- AI仅允许A0机械整理、A1用户确认候选和A2真人待审草稿；A3自动诊断、风险裁决、AIS和直接发布禁止。

子线状态：

| 切片 | 状态 | 起点/阻断 |
|---|---|---|
| TA-00 权威方案与上线门禁 | documented | 权威文件哈希和D01—D26已登记；不代填签字 |
| TA-01 七对象复用事实基准 | documented | 七对象复用、数据流和权限事实已登记 |
| TA-02 合成数据L0闭环 | verified_l0_only | 外部独立原型七步验收通过；无保存/API/AI，不接真实用户 |
| TA-03 草稿提交与人工队列 | human-gated | TA-02、隐私/队列/权限门禁和负责人确认 |
| TA-04 共同反馈修订 | human-gated | TA-03、T23-02、T25-02 |
| TA-05 微行动与随访 | human-gated | TA-04、T23-03、T23-04 |
| TA-06 形成性研究冻结 | human-gated | TA-02、T30-00 |
| TA-07 AI辅助沙盒 | human-gated / optional | T28/T31/T34和D15/D16 |
| TA-08 真实低风险试点门 | blocked_for_real_pilot | D01—D26、伦理/数据/运营和外部验收 |

### 下一轮启动提示词

```text
请读取 Claude计划模式.md 的任务二十三至三十四、全量深化总蓝图、治疗性评估受控接入子线、任务三十研究方法冻结准备和逐步开发任务清单。先检查 git status 与状态表，从 T23-00 建立主旅程事实基准，同时登记 T30/T31/T32/T33/T34 的跨任务门禁；已完成项跳过。完成T23-01后先做T23-02，再执行TA-00/TA-01；治疗性评估只做合成数据L0准备，未满足D01—D26不得接真实参与者。每次只做一个可演示切片并运行专项/全量验收。AI 问答只允许合成案例、批准知识库和 fake provider，默认关闭；公开数据先登记授权，许可不清不得下载或训练；不得使用参与者原文训练，不关闭临时展示越权。
```

### 2026-07-19 自动执行收口

- 已按计划完成首波事实/门禁、T23-01/T23-02/T23-03最小切片、T24-01、T25-01、T26-01最小契约、T31-01新增对象矩阵和TA-00—TA-02合成L0验收。
- 执行记录：`docs/02_专项进度与验收/任务二十三至三十四自动执行记录_20260719.md`。
- 当前恢复点：T24-02；TA-03继续human-gated，D01—D26、真实责任链和临时展示越权未处理前不得接真实参与者。

### 2026-07-19 T23-04统一成长入口

- `GET /api/growth/overview`已增量补充记录与练习、测评变化、关系探索和研究者反馈四类`sections`，旧字段继续兼容。
- 小程序“我的”只保留一个成长入口；关系试点和旧关系仪表盘URL兼容进入统一入口的关系分区，关系连续记录保留为详细页。
- 不生成单一成长分数，不混合不同量尺；下一步T23-05。

### 2026-07-19 T23-05视觉组件与回归收口

- 首页与关系试点共用主任务卡；消息、成长、反馈、训练和关系报告共用加载/空/错/重试组件，状态标签和反馈评价统一。
- 页面保留一个明显实色主行动，底部安全区、触控尺寸、可访问名称和选择状态已补齐；不改API、数据库、内容库或首页冻结位置。
- 375/430/768/1440公共组件视觉审计通过；微信开发者工具、Android/iOS真机和辅助技术仍为外部验收。
- T23本地自动切片收口；下一恢复点为T24-02。

## 2026-07-20：任务二十三至三十四升级为完整实现计划

权威完整计划：`docs/01_当前执行入口/任务二十三至三十四完整实现主计划_20260720.md`。

完成口径调整：

- 后续仍使用小步、测试驱动和独立提交施工，但最小切片不再等于大任务完成；
- `engineering_complete`必须包含后端、数据库、shared、Web、小程序、对象权限、审计、异常恢复、迁移、回滚和自动回归；
- `release_approved`还必须完成适用的真机、云环境、真人研究和专业签字；
- 任务二十三调整为`external_validation_pending / full_gap_reaudit_required`；
- 任务二十四调整为`implementation_in_progress_draft`，2026-07-20工作区已有T24-01/T24-02未提交草稿，但在计划确认和重新审查前不计完成；
- T25至T34全部按新计划的F编号重新核对完整缺口；
- TA-00至TA-08继续受D01至D26、伦理、责任链和真实环境门禁约束；
- 临时展示越权继续保留，但不能通过正式权限验收。

当前恢复点：先确认完整实现计划，再审查未提交T24草稿，从T24-F01至T24-F03开始；本轮不继续业务编码。

### 2026-07-20任务二十四完整实现执行结果

- 状态：`engineering_complete_local / release_approval_pending`，工程完成与发布批准分开记录。
- T24-F01至F09已补齐后端、数据库、shared、Web、小程序、角色权限、审计、范围预览、dry-run/事务执行、撤回研究授权、申诉、异常回滚、SQLite/MySQL迁移契约和恢复墓碑。
- T24-F10只生成`docs/02_专项进度与验收/任务二十四发布门禁证据包_20260720.md`；负责人保存矩阵、伦理/法律、测试云、真机和生产双人批准均未签字。
- 三个真实执行开关默认关闭；真实执行测试仅使用临时合成SQLite数据库，没有连接云或生产数据。
- 临时展示越权继续保留；正式权限结论来自后端角色矩阵，不以Web页面可见性通过验收。
- 详细执行记录：`docs/02_专项进度与验收/任务二十四完整实现执行记录_20260720.md`。
- 下一工程任务：按完整实现口径进入任务二十五F01现状复核与失败契约，不把已有只读队列视为完成。

### 2026-07-20任务二十五完整实现执行结果

状态：`engineering_complete_local / release_approval_pending`。本段即任务二十五执行记录，不另建独立执行记录文件。

#### T25-F01—F03：统一工作项与处置账本

- 新增`research_work_items`、`research_work_item_notes`、`research_work_item_actions`，统一队列类型、优先级、状态、负责人、15分钟租约、到期时间、版本、关闭原因和来源引用；数据库版本升为`2026_07_20_014 / research_operations_work_items`。
- 完成领取、续租、退回、转交、处理中、等待补充、内部说明、完成、关闭和重新打开；全部写操作要求幂等键和`expected_version`，并发冲突返回409。
- 原始参与者内容保持来源表只读；内部/处理说明单独保存，参与者可见内容继续写入`messages`并复用消息去重。高风险消息由普通研究者发送时转督导复核。

#### T25-F04—F06：通知恢复与权限一致性

- 通知失败区分`retryable/reauthorization_required/template_error/permanent_failure`；可恢复失败使用5、10、20分钟指数退避，达到最大次数进入死信，支持人工恢复。
- 阶段反馈、人工支持、风险复核、不适反馈和隐私申请复用同一工作项交互；研究者仅处理已分配参与者，风险复核和隐私申请保持督导/管理员权限，转交、关闭、重新打开和通知恢复同样受限。
- 参与者撤回研究授权后仍沿用既有研究队列过滤；临时展示越权未关闭，且未加入工作项写路径，因此不能据此通过正式权限验收。

#### T25-F07—F08：可观测、恢复与界面

- 新增近1—90天状态、超时、租约过期、关闭原因、动作量和积压趋势；界面明确“不用于评价心理支持质量或参与者变化”。
- Web研究总览改为双栏处置账本：队列按优先级和等待时间排列，可查看轨迹、写内部说明、发送参与者消息和执行受权动作；窄屏改为单栏，控件不低于44px，支持键盘焦点、空态、错误重读和重试。
- shared、Web client和小程序client统一工作项、动作、指标和错误契约；小程序不新增研究者页面，参与者仍在现有消息中心接收消息。
- SQLite旧表补列、空库、重复迁移、MySQL schema转换、事务中断回滚和SQLite备份恢复均有自动测试。回滚时先设`RESEARCH_OPERATIONS_WRITE_ENABLED=0`恢复只读，新增表列保留审计证据。

#### 自动验收与冲突记录

- 专项：工作项状态机/权限/通知/迁移/恢复和既有队列契约20项通过；后端全量359项通过（9条第三方依赖弃用警告，无失败）。
- Web：typecheck/build通过；Playwright桌面/移动两视口处置工作台通过，无横向溢出，键盘可操作。
- 小程序：API client契约已同步；微信开发者工具和真机未执行，不写成发布批准。
- 与现有功能无破坏性冲突：隐私申请的正式执行继续使用T24专用接口；工作项只提供运营壳和受控状态，不绕过隐私、风险或关系报告原权限。

#### 发布批准门禁与下一恢复点

- 未自动签字：测试云MySQL迁移/恢复、真实两名处理人并发、微信开发者工具、Android/iOS、弱网中断、生产值守与升级责任人。
- 生产环境`RESEARCH_OPERATIONS_WRITE_ENABLED`默认关闭；负责人完成外部证据后才能开启。
- 下一工程任务：任务二十六F01全公开端点契约登记与历史错误包络复核；不得把T26已有最小契约当作完整完成。

### 2026-07-20任务二十六完整实现执行结果

状态：`engineering_complete_local / release_approval_pending`。本段即任务二十六执行记录，不另建独立执行记录文件。

#### T26-F01—F04：机器契约、兼容层与CI

- 从Flask真实路由生成`shared/contracts/api-contract.json`，登记136个公开操作的路径、方法、角色、对象范围、请求路径/查询/正文/请求头、分页、幂等、错误码、枚举引用、响应契约与弃用状态。
- 成功响应统一补`request_id`，错误继续使用`ok:false/error.code/error.message/request_id`，响应头保留`X-Request-ID`；JSON下载维持原格式并由响应头追踪。
- `assessment-results/checkins/messages`继续兼容`limit`，同时使用`page/page_size`；旧参数返回`Deprecation`和`Sunset: 2026-10-31`，没有一次性删除旧调用。
- 同一契约生成shared TypeScript注册表、小程序JavaScript注册表和`API机器契约.md`；测试检查shared/Web/小程序全部`/api`字面路径均存在于真实路由或合法路径前缀。
- GitHub Actions新增契约生成漂移、API边界审计和冻结快照兼容回放，缺失端点、访问范围扩大、公开URL/对象范围/响应包络变化和幂等要求放松会失败。

#### T26-F05—F07：深模块、静态扫描和回滚

- 关系试点继续使用enrollment/report/growth/task独立服务；消息的列表、发送、幂等、已读和脱敏投影迁入`message_service`；隐私同意、撤回、申请列表/创建和安全摘要迁入`privacy_request_service`；研究队列来源同步、分页和工作项投影迁入`research_queue_service`。公开URL不变。
- 静态扫描覆盖N+1、无界列表、HTTP适配器`SELECT *`和跨用户参数。最终0 blocker、57个legacy review warning；这些警告是后续逐模块收敛线索，不评价参与者或研究人员，也未被误写成已修复。
- 冻结136操作兼容快照；回滚按上一提交恢复契约快照和对应服务适配器，不回退数据库。T26没有新增表或字段，数据库版本保持`2026_07_20_014`，因此迁移为`not_applicable`。

#### 自动验收、冲突与发布门禁

- T26新增契约8项通过；敏感模块专项33项通过；后端全量367项通过（9条第三方弃用警告，无失败）。
- Web typecheck/build通过；小程序61个JS、56个JSON、40页、57个组件引用和7个Canvas静态检查通过；内容校验、4份生成物漂移、136操作兼容回放和Python编译通过。
- 兼容冲突：历史列表并非全部使用相同分页形状，本任务保留旧响应并在契约逐项登记；只对已有等价`page_size`的三个`limit`别名发弃用头，避免破坏当前页面。
- 未自动签字：测试云历史客户端回放、CloudBase包、微信开发者工具、Android/iOS、真实弱网、生产日志观察和发布负责人批准。临时展示越权继续保留，未据此通过正式权限验收。
- 下一工程任务：任务二十七F01内容版本元数据与不可变内容包；不得把现有内容文件或只读规则页当作完整内容治理工作台。

### 2026-07-20任务二十七完整实现执行结果

状态：`engineering_complete_local / release_approval_pending`。本段即任务二十七执行记录，不另建独立执行记录文件。

#### T27-F01：全内容类型元数据登记

- 新增`content_governance_manifest.json`，覆盖训练卡、反馈规则、测评/日记推荐映射、量表目录、测评题项、课程、项目、画像规则、FAQ占位、知情同意和隐私文本；统一来源、来源版本、版权、适龄、人群、变更摘要和治理状态。
- 旧内容登记写入`registered`，明确`auto_approved=false`；FAQ源缺失、量表版权/适龄未逐项核验等事实保留为阻断信息，不伪造批准状态。

#### T27-F02—F04：生命周期、分权和不可变发布

- 数据库升至`2026_07_20_015 / content_governance_lifecycle`，新增`content_governance_versions`、`content_governance_reviews`、`content_governance_releases`；同一内容版本不可覆盖。
- 状态机覆盖草稿、校验、送审、驳回、批准、发布、暂停、退役和恢复。研究、心理、伦理、内容四类审核按角色限制，证据路径必填，同一审核人不得代表多个专业责任完成批准。
- 发布要求管理员独立确认、全审核完成、期望哈希一致和依赖影响确认；发布包保存规范哈希、前一发布ID和原因。跨进程排他锁避免两个发布交错；文件以同目录临时文件原子替换，随后数据库切换，数据库异常时恢复原文件。
- 生产`CONTENT_GOVERNANCE_PUBLISH_ENABLED`默认关闭；治理强制环境禁用历史`/api/content-review/update`直接改JSON路径。临时展示越权未改动，也未加入任何内容治理写权限。

#### T27-F05—F06：合成回放与依赖门禁

- 固定合成集明确`contains_real_data=false`，覆盖普通支持性反馈、高风险自动反馈/推荐阻断和边界提示；回放返回逐案例差异、通过数和证据哈希，只构成工程证据。
- 依赖扫描覆盖训练计划、课程、项目、测评推荐规则和日记推荐规则；存在依赖时发布、暂停和退役要求显式确认，不静默删除引用。

#### T27-F07—F08：双端契约、Web工作台和内容阻断

- Web`/content/review`改为治理工作台，支持登记、建草稿、查看diff/校验/哈希/依赖、四类审核轨迹、发布、暂停、退役、恢复和固定回放；窄屏单栏、长列表滚动、差异预格式化和清晰警告状态已完成。
- shared类型、Web client、小程序client和机器契约同步；小程序不复制研究者工作台，只提供运行内容版本/哈希描述以便客户端记录实际内容版本。
- 当前机器契约148个操作；T26冻结136操作兼容回放通过，API边界0 blocker并保留57个旧模块review warning。
- 来源、来源版本、版权、适龄、人群、变更摘要、非诊断边界、哈希、专业审核或证据任一缺失均阻断送审/发布。

#### 数据库迁移、异常恢复与回滚

- `migrate_task27_content_governance.py --apply`在空SQLite库幂等建表并登记015版本；MySQL继续走统一schema转换。`--rollback-plan`只输出非破坏步骤，不执行删表或代替人工批准。
- 回滚顺序：关闭发布开关，停止新发布；核对当前/前一发布包哈希；按`previous_release_id`恢复；治理版本、审核和审计记录保持只读留存。
- 自动测试覆盖环境开关、人工确认、错误哈希、角色越权、审核人独立、元数据缺失、导入不升级、依赖、合成高风险阻断、发布/暂停/恢复和数据库切换失败文件恢复。

#### 自动验收与问题loop

- T27新增10项与历史内容审核6项（共16项）通过，包含并发发布锁；后端全量377项通过（9条第三方弃用警告，无失败）；Web typecheck/build通过；桌面Chrome Playwright内容治理工作台1项通过；内容校验、小程序client加载、迁移/回滚计划和契约生成/兼容/边界检查通过。
- 首轮全量后端发现4项历史断言漂移：三处仍固定014版本/旧迁移名，一处契约在新增端点后未重生成；已更新版本断言、取消旧任务对当前迁移名的错误绑定并重生成148操作契约。第二轮为`376 passed`；随后自审补入跨进程发布排他锁及第10项专项测试，最终全量为`377 passed`。
- 命令曾在仓库根目录错误调用全局`npx playwright`，未读取Web项目配置；已改在`apps/web`目录使用本地配置，测试通过。该命令错误不属于产品缺陷。

#### 发布批准门禁与下一恢复点

- 未自动签字：真实研究/心理/伦理/内容审核人、版权/授权原件、适龄证据、测试云MySQL、CloudBase容器文件持久化方案、微信开发者工具、Android/iOS、弱网中断和生产发布/恢复演练。
- 本地测试中的审核人和内容均为临时合成数据，不算真实专业批准；工程完成与发布批准继续分开。
- 下一工程任务：T28-F00负责人门禁事实与T28-F01合成AI安全集。只允许fake provider、合成案例和`published`内容版本；AI默认关闭，T24/T31/T32/T34及真人责任链未完成前不得接真实参与者。

### 2026-07-20任务二十八完整实现执行结果

状态：`engineering_complete_local_synthetic / participant_release_blocked_human_gate`。本段即任务二十八执行记录，不另建独立执行记录文件。

#### T28-F00、F08：负责人决策与参与者门禁

- `content/ai_qa_governance.json`登记服务名称、目标人群、范围、供应商、保存/出境、值守、危机转介和停用责任人的拟议值及未决状态；负责人、心理、伦理、隐私、安全和生产均未被系统代签。
- 配置层只接受`fake`供应商并强制`AI_QA_ENABLED=false`；参与者API和小程序发送方法不存在。T24/T31/T32/T34、责任链、人工盲审/红队、测试云和生产门禁未完成前不能申请真实低风险流量。
- 临时展示越权继续保留；正式权限E2E显式模拟关闭该旁路后验证，展示可见性不作为参与者开放或对象权限通过证据。

#### T28-F01、F04、F07：安全路由、离线评测与停用

- 建立24例固定合成集，覆盖产品使用、心理教育、反思、诊断越界、危机、自伤伤人、虐待、提示注入、隐私索取、工具滥用、范围外问题和正常引用；`contains_real_data=false`。
- 调用前阻断风险、隐私、注入、范围外和写工具请求；调用后检查诊断化、保证性承诺、提示泄漏和来源缺失。不通过时返回经治理的固定响应或安全降级，并以HMAC摘要记录事件，不保存完整原文。
- 离线运行保存逐例结果、聚合指标、阈值、运行版本和证据哈希；督导/管理员可写独立复核，管理员可触发kill switch。工程阈值不代替真人盲审、伦理批准或发布批准。

#### T28-F02、F03、F09：批准知识、供应商隔离与无工具

- 检索仅连接T27已`published`且有`active release`的训练卡、课程、FAQ、知情同意和隐私内容，引用带内容ID、版本、发布ID、哈希和治理状态；草稿、内部备注、参与者原文和风险记录不进入知识库。
- 供应商中立接口当前只有本地fake实现；支持正常、失败、超时、诊断泄漏和提示泄漏模式。服务端执行每小时限流、日预算、超时、连续失败熔断、成本记录和密钥隔离。
- 首轮不提供任何写操作工具，不自动发消息、改记录、排任务、写研究反馈或获得研究授权；来源不足时明确返回固定“不知道/请转人工”响应。

#### T28-F05、F06：会话、隐私与内部工作台

- 数据库升至`2026_07_20_016 / controlled_ai_qa_sandbox`，新增会话、消息、评价、安全事件、供应商事件、评测运行、人工复核和运行控制八表；研究者仅访问本人合成对象，督导/管理员访问受控评测证据。
- 支持当前会话上下文、幂等消息、纠错评价、删除会话原文和隐私范围清理；评价默认`research_authorized=false`，不会因点击评价自动获得研究或训练授权。
- Web`/ai-sandbox`展示参与者关闭门禁、合成问题、回答/来源、模型与提示版本、安全判定、成本、指标、复核和停用；桌面/移动无横向溢出。小程序仅查询公开关闭状态，不复制研究者工作台。

#### 数据库迁移、异常恢复与回滚

- `migrate_task28_ai_qa.py --apply`可在空库幂等建表，统一数据库适配器覆盖SQLite/MySQL字段和索引；`--rollback-plan`仅输出先关沙盒、保持参与者关闭、触发停用和保留审计的非破坏步骤。
- 供应商失败、超时、预算/限流、熔断、后置安全失败均返回固定降级并留下脱敏事件；运行控制只允许关闭，不提供未批准的远程开启路径。
- 回滚不删除八张表或审计历史；先设置`AI_QA_SANDBOX_ENABLED=0`、保持`AI_QA_ENABLED=0`，再由管理员确认停用状态。

#### 自动验收与问题loop

- T28专项18项，连同隐私、MySQL、契约和关联回归共51项通过；后端全量`395 passed`（9条第三方依赖弃用警告，无失败）。
- Web typecheck/build通过；全量Playwright桌面/移动`20 passed`，T28沙盒双视口2项和内容治理高并发重复6项通过；小程序61个JS、56个JSON静态检查通过。
- 内容校验、迁移apply/rollback、159操作契约生成与漂移检查、T26冻结136操作兼容回放、API边界`0 blocker / 57 legacy review warnings`和`git diff --check`通过。
- 首轮全量Web发现隐私Dry-run完成消息被重新加载提示覆盖，已改为加载后恢复完成消息；并发下研究工作台首屏和内容治理导航偶发等待不足，已加固确定性等待并重新全量通过。产品临时展示越权没有关闭。

#### 发布批准门禁与下一恢复点

- 未自动签字：负责人范围/供应商/保存矩阵、心理/伦理/隐私/安全审查、人工盲审和红队、危机值守演练、真实供应商合同、测试云MySQL、CloudBase、微信开发者工具、Android/iOS和生产停用演练。
- 参与者正式问答仍不存在；合成沙盒通过不能解释为心理有效性、治疗效果或真实上线批准。
- 下一工程任务：T29-F01公开数据集卡与许可/内容权利登记。许可不清只保存链接和审查状态，不下载、不训练；只做离线基准，不替换当前生产规则，不把公开社交网络结论解释为家庭关系。

### 2026-07-20任务二十九完整实现执行结果

状态：`engineering_complete_local_synthetic / public_dataset_ingest_blocked_human_rights_gate / release_approval_pending`。本段即任务二十九执行记录，不另建独立执行记录文件。

#### T29-F01—F03：数据集卡、权利门禁与域映射

- 建立5张数据集卡：项目自有240例合成情感集和合成图可用于工程测试；GoEmotions、SNAP目录、NetworkX Zachary只登记来源、版本、语言/平台/人群/情境、许可声明、内容权利状态、敏感性、允许/禁止用途和删除方式。
- 外部三项均为`metadata_review_only / blocked_rights_review`，本地路径和工件哈希为空；系统不因“公开”或代码仓许可推断用户生成内容、平台条款或底层图数据已获准下载/训练。
- 标签映射保留`unmapped`，分别记录英语社交媒体、公开网络、合成中文日常反思与项目关系记录的语言、平台、人群和语境差异；不把不能等值的公开标签强行映射为项目心理含义。

#### T29-F04—F06：情感与网络离线基准

- 词典规则在固定240例生成集上输出覆盖率、生成种子准确率、宏F1、混淆矩阵、校准误差、四类句式亚组和失败案例；所有结果固定`human_gold_used=false`，生成标签不是人工金标准。
- 网络基准只运行合成星形图、环形/双社区图和加权扰动，验证`1/weight`距离、强度中心、弱桥阈值、5%扰动稳定性和复杂度；固定`public_graph_used=false`、`family_quality_inference=false`。
- 运行保存算法版本、参数、输入哈希、证据等级、创建人和结果哈希；`raw_text_included=false`、`production_replacement_allowed=false`，失败或不一致进入工程复核而不替换生产规则。

#### T29-F07—F09：双人盲标、权限与非生产边界

- 生成240条固定模板中文事件并校验哈希，明确`contains_real_data=false`；标注页不显示生成标签，支持两名人员独立标注情绪、效价、唤醒、情境和反射弧节点。
- 一致性汇总计算双人完整案例数、情绪Cohen kappa和效价/唤醒差异；达到200例和工程阈值也只标记申请条件，系统固定`human_gold_released=false`，必须由真实标注者、方法负责人和专业审查人工决定。
- 参与者无权访问；研究者只看本人运行，督导/管理员查看一致性和复核，管理员同步本地清单并只允许停用。小程序只读取关闭/门禁状态，不提供运行、同步、盲标或复核方法；Web`/research/benchmarks`提供响应式内部工作台。

#### 数据库迁移、异常恢复与回滚

- 数据库升至`2026_07_20_017 / offline_benchmark_governance`，新增数据集卡、基准运行、盲标、复核和运行控制五表；关键写入同步审计。
- `migrate_task29_offline_benchmarks.py --apply`在独立空SQLite库幂等建表并登记017；统一schema包含MySQL字段/索引适配。`--rollback-plan`只输出关闭离线基准、保持外部接入及生产替换关闭、管理员停用和保留证据表的非破坏步骤。
- 运行控制没有重新开启接口；异常返回稳定错误并保持既有记录。若未来批准外部工件，必须按数据集卡删除方式另行执行可审计删除，当前迁移不自动下载或删除外部数据。

#### 自动验收与问题loop

- T29专项13项通过；后端全量`408 passed`（9条第三方依赖弃用警告，无失败）。
- Web typecheck/build和全量Playwright桌面/移动`22 passed`；T29专项双视口2项通过并检查无横向溢出。小程序61个JS、56个JSON静态检查通过。
- 240例生成哈希、内容治理、017迁移apply/rollback、170操作契约漂移检查、T26冻结136操作兼容回放、API边界`0 blocker / 57 legacy review warnings`和`git diff --check`通过。
- 首轮专项发现词典路径错误跟随测试临时内容目录、测试正则过窄，已分别固定到项目词典根和修正断言；视觉复核发现长页截图中无障碍跳转链接覆盖移动端按钮，已改为仅键盘焦点可见并重新双视口通过。一次组合验收命令因终端拒绝计算路径删除而未执行，随后改用已核验的固定工作区临时数据库完成迁移并只清理该自产物；一次误写的契约检查脚本名已用正式`check_api_compatibility.py`纠正；文档收口后一次`npm run typecheck`误在仓库根执行，已回到`apps/web`重跑通过，均非产品缺陷。

#### 发布批准门禁与下一恢复点

- 未自动签字：GoEmotions/SNAP/Zachary的许可、平台条款、内容权利和隐私审查；两名真实标注者、盲标手册修订、心理/方法/伦理批准；测试云MySQL、CloudBase、微信开发者工具、Android/iOS和生产回滚演练。
- 本地合成基准通过不表示公开数据已用于测试，不表示形成域内人工金标准，也不表示词典或网络算法具有心理有效性、家庭关系解释能力或生产替换资格。
- 临时展示越权继续保留且未用于T29正式角色/对象权限验收。下一工程任务：T30-F00心理测量与研究方法冻结；只能生成机器检查和签字证据包，查看主要真实结果前不得伪造冻结或替真人签字。

## 任务三十完整实现执行结果（2026-07-20）

状态：`engineering_complete_local_pre_freeze / human_method_ethics_signature_pending / release_approval_pending`。本段即T30执行记录，不另建执行记录文件。

### F00—F03：问题、测量、量尺与指标

- `content/research_methodology_registry.json`登记主旅程、训练推荐、支持性反馈、关系试点和受控AI五条研究线。主要问题、人群、时间零点、暴露、候选估计量、对照候选、允许/禁止解释均有字段，但唯一主要结局、主要时间点、样本量和停止责任人继续标`pending_freeze`。
- 生成器从`assessment_worksheets.json`登记全部33份测量的题数、量尺、反向题、计分、缺失、来源/语言、审核、允许/禁止用途和解释边界。内容校验阻止漏项、重复项、伪签字、真实结果读取或冻结开关漂移。
- `assessment_results`新增`scoring_version/raw_scale_json/raw_scores_json/transformed_scores_json/transformation_version`。关系中的行动方式问卷保留1—9原分，同时以`1 + (raw - 1) * 4 / 8`产生1—5既有画像模型输入；API、shared和画像位置响应明确区分`worksheet_raw_scores`与`model_input_scores`。其他五点量表不生成转换分，既有模型参数/哈希未改变。
- 流程、安全、推荐和AI指标全部登记分子事件、分母事件、去重键、时间窗、异常和解释边界；离线准确率不能写成实际帮助。

### F04—F08：缺失、纵向、分析与合成仿真

- 缺失状态分为未暴露、未开始、中断、提交失败、主动退出、研究撤回、技术失败和失访；禁止默认填0、默认均值和默认最近值延续。
- 纵向计划先检查身份、实际日期、量表/版本/量尺一致、间隔与适用的测量不变性；个体间与个体内分开。少于2点不画趋势，至少3点才进入模型候选，横断面聚类不解释为个人轨迹。
- 分析顺序固定为流程/数据质量、各波计分与可靠性、缺失流失、主要估计量、诊断、预定义敏感性、次要和探索；协变量、交互、亚组、多重比较、异常值及失败备选均保持查看结果前冻结要求。
- 仿真只用固定随机种子合成数据，覆盖n=20/40/80完成比例精度、0/20/40%流失、三波个体内斜率可恢复性和双簇扰动稳定性；结果固定`contains_real_data=false`、`confirmatory_power_claim=false`和`real_outcome_rows_read=0`。
- 报告规范核验：JARS-Quant适用定量心理报告；STROBE仅在观察性设计选定时适用；SPIRIT/CONSORT 2025只在随机试验方案/结果时适用；AI扩展需与2025核心协调；DECIDE-AI仅供未来获批的早期现场临床AI评估；PRISMA不适用。未指定目标期刊，不虚构期刊要求。

### F09：冻结证据、权限、迁移、恢复与双端

- 后端`/api/research/methodology`提供1个公开非敏感状态和9个内部端点：注册表/版本、机器检查、合成仿真、证据列表、待真人签字证据包、管理员同步和只允许停用。没有签字、正式冻结、主要结果分析或重新开启端点。
- 数据库版本`2026_07_20_018 / research_methodology_freeze_evidence`；五表保存不可变版本、机器检查、合成仿真、证据包和停用状态。参与者无内部权限；研究者/督导/管理员运行；仅督导/管理员生成证据包；仅管理员同步/停用。关键写入审计且不保存参与者原文、真实结果、令牌或内部堆栈。
- `migrate_task30_research_methodology.py --apply`幂等建表并只回填缺失的计分溯源字段；旧记录原分不覆盖、未知量表跳过并计数。空库、旧记录、重复执行和MySQL schema转换有专项覆盖。`--rollback-plan`只关闭工作台/分析开关、隐藏入口并保留原分、证据与审计，不自动删表、不自动签字。
- Web新增`/research/methodology`响应式工作台，清楚分开结构状态、版本/哈希、机器检查、合成仿真、签字包、五条问题、规范、测量/量尺和未决项；没有“正式冻结”按钮。小程序只新增`getResearchMethodologyPublicStatus`，不复制内部运行、同步或证据包能力。
- 异常恢复：内容损坏、版本同名哈希漂移、未同步版本、证据缺项、检查失败、功能关闭、运行停用和权限不足均返回稳定错误；停用后仍可保留和读取既有证据，不自动恢复运行。

### 自动验收与问题loop

- T30专项`16 passed`；后端全量按文件顺序拆为`239 passed + 185 passed = 424 passed`；9条仅为jieba/pkg_resources第三方弃用警告。
- Web typecheck/build通过；Playwright桌面/移动全量`24 passed`，T30专项2项覆盖键盘焦点、无横向溢出、量尺分离、无自动签字按钮和截图视觉核验。小程序61个JS及56个JSON静态检查通过。
- 33项注册表生成漂移、内容治理、018空库/旧库回填/重复迁移与回滚、180操作机器契约、T26冻结136操作兼容、API边界`0 blocker / 57 legacy review warnings`和`git diff --check`通过。
- 首轮Web验证命令误在`apps/web`目录调用仓库根Python脚本，脚本未运行但后续typecheck/build通过；已回仓库根生成并检查四份契约。全量后端首轮超时和第二组缺少PYTHONPATH均按上述loop解决，没有把超时或收集错误记为通过。

### 工程完成与发布门禁

- 工程完成不等于正式冻结。机器注册表保持`draft_before_freeze`，证据包保持`draft_for_human_signature`，配置强制`RESEARCH_METHODOLOGY_FORMAL_FREEZE_ALLOWED=0`和`RESEARCH_OUTCOME_ANALYSIS_ALLOWED=0`。
- 未自动签字：唯一主要结局/时间点、样本量依据、最小可解释变化、最终纳排、缺失主方法、停止责任人、测量版权/授权、心理/方法/伦理/数据治理、研究负责人、目标期刊、测试云MySQL、备份恢复、CloudBase、微信开发者工具、真机和生产批准。
- 本轮未读取真实主要结果、未运行真实结局分析、未下载新公开数据、未训练模型、未改变既有聚类参数。临时展示越权继续保留，但T30正式角色接口以展示旁路关闭的测试身份验证，越权不作为正式权限证据。
- 下一工程任务：T31-F01—F08安全、隐私与滥用防护完整实现；正式权限验收继续因临时展示越权和外部门禁保持阻断。

## 任务三十一完整实现执行结果（2026-07-20）

状态：`engineering_complete_local / formal_permission_acceptance_blocked_by_showcase / external_security_privacy_release_gates_pending`。本段即T31执行记录，不另建执行记录文件。

### F01—F04：资产、全对象权限与威胁模型

- `content/security_privacy_abuse_registry.json`由`shared/contracts/api-contract.json`确定性生成，登记11类资产及当前186个API操作的create/read/update/send/export/delete、允许/拒绝角色、对象范围、展示例外和幂等边界；版本和哈希进入内容治理清单。
- 端侧威胁覆盖IDOR、重放、批量导出、CSV公式注入、服务端文件名、日志泄密、弱网重复提交、越权深链和令牌泄漏；AI威胁覆盖提示注入、知识污染、跨用户检索、供应商留存、提示泄漏、成本耗尽、工具滥用和越权行动。每项均登记缓解、检测、负责人和剩余风险。
- 机器契约版本升至`2026-07-20.3`、186操作；T26冻结136操作兼容回放继续通过。`POST /api/auth/admin-create`仅修正契约元数据为既有运行时admin权限，没有放宽接口。
- 真实AI、参与者问答和写操作工具继续关闭；小程序不含内部扫描、账号停用或安全事件处置方法。

### F05—F06：身份失效、安全事件与隐私删除证明

- `users`新增`auth_epoch/status_reason`；令牌携带世代，登出、管理员凭据轮换和账号停用递增世代，使既有令牌失效。账号停用/恢复要求admin、禁止自停用、支持预期世代并记录审计和最小安全事件。
- 新增`security_events`，失败登录、账号状态和处置只保留白名单最小元数据；不返回令牌、密钥、参与者原文或内部堆栈。管理员可处置，研究者/督导只读脱敏证据。
- 隐私正式执行在同一数据库事务中，对每张白名单表保存预期计数、实际删除数与删除后归零结果；身份对象验证匿名化字段。任一不一致抛错并整体回滚。`privacy_deletion_verifications`及只读接口不返回主体哈希。
- CSV导出对`= + - @ TAB CR`开头的单元格加安全前缀，文件名仍由服务端白名单产生，并加`no-store/nosniff`。

### F07—F08：展示例外、扫描、容器与恢复

- 临时展示越权保持开启，注册表固定`accepted_for_formal_permission_testing=false`并登记范围、风险和正式试点/生产前停用条件；Web明确显示“正式权限验收未通过”，且没有自动批准、关闭越权或安全签字按钮。
- 新增脱敏本地扫描：仓库密钥模式、依赖固定、非root容器、生产CORS、默认密钥保护、安全响应头和运行产物；输出只含检查状态/哈希。联网依赖漏洞库单列外部告警，不伪造已扫描。
- 生产配置拒绝通配CORS；API统一`X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy`、`Permissions-Policy`和`Cache-Control:no-store`；Docker以`safehome`非root用户运行。
- 数据库版本为`2026_07_20_019 / security_privacy_abuse_controls`，新增`security_control_runs/security_events/privacy_deletion_verifications`。迁移在独立库重复执行两次通过；回滚只关闭扫描/隐藏入口，保留令牌世代、CSV防护、安全头、证明与审计，不自动DROP、不恢复旧令牌、不关闭展示例外。

### shared、Web、小程序与权限

- shared补安全注册表、工作台、公开状态和扫描类型/端点；Web client支持读取工作台、admin扫描、账号状态和事件处置；小程序只允许`getSecurityPublicStatus`。
- Web新增`/security/privacy`响应式工作台，呈现正式阻断、资产/威胁/删除/事件摘要、脱敏扫描、186项可检索权限矩阵和安全事件恢复。修复900px矩阵向页面泄漏横向宽度的问题，改为面板内部滚动并在桌面/移动验证无溢出。
- 后端公开状态无内部详情；工作台为researcher/supervisor/admin；扫描、账号状态和事件处置仅admin。关键写入有审计，服务端始终为唯一权限依据。

### 自动验收与问题loop

- T31专项`17 passed`；后端全量按文件顺序拆为`183 passed + 100 passed + 158 passed = 441 passed`；9条仅为jieba/pkg_resources第三方弃用警告。
- Web typecheck/build通过；Playwright桌面/移动全量`26 passed`，T31专项2项覆盖键盘焦点、无横向溢出、正式阻断、矩阵检索、脱敏扫描和无批准按钮。小程序40页/57组件引用/7 Canvas无问题，61个JS和56个JSON通过。
- 内容校验、186操作注册表生成检查、4份API契约生成物、136冻结操作兼容回放、API边界审计`0 blocker / 57 legacy warning`、脱敏扫描`0 blocker / 1 external warning`、019迁移/回滚及Python编译通过。
- 首次Web专项发现矩阵造成桌面14px溢出和移动端点击干扰，修复后通过。后端全量单批与双并发批次因超时未留下可引用结果；确认无残留进程后改为三组串行。根目录分组暴露旧测试依赖`backend`导入路径，按既有工作目录重跑；没有因此修改业务导入逻辑。

### 工程完成与发布批准分离

- 已完成：本地后端、数据库、shared、Web、小程序、权限、审计、异常恢复、迁移、回滚、专项/全量验收和文档闭环。
- 仍未批准：正式权限验收（被展示越权阻断）、联网依赖漏洞库、测试云日志/MySQL、CloudBase网关身份头、Android/iOS真机深链和令牌丢失、备份擦除策略、负责人/伦理/隐私/安全签字及生产发布。
- 本任务只生成自动证据和外部门禁清单，没有替任何人工、伦理、隐私、安全、真机、云或生产责任人签字。
- 下一工程任务：T32-F01—F08可靠性、可观测性与发布工程完整实现；先补关键旅程结构化SLO和全链路追踪，再统一可靠队列、迁移恢复、功能开关、故障演练和运行手册。

## 2026-07-20：任务三十二完整实现执行结果

状态：`engineering_complete_local / test_cloud_slo_and_release_gates_pending`。

### F01—F02：七条旅程与脱敏全链路追踪

- `content/reliability_release_registry.json`确定性登记登录、记录提交、反馈生成、训练计划、消息、研究队列和AI合成沙盒七条旅程，以及成功率、P50/P95、错误、重试和恢复指标。
- Flask统一接收或生成`X-Request-ID`，每个响应写入`observability_events`：只含角色范围、模块、旅程、结果、错误码、状态、时延、重试和恢复；不保存Authorization、Cookie、手机号、OpenID、请求/响应正文、参与者原文或堆栈。
- SLO快照只允许`local_synthetic/test_cloud_evidence_pending`，当前固定`production_slo_frozen=false`，本地数字不转为正式承诺。

### F03—F05：可靠任务、迁移恢复与版本化开关

- `reliable_jobs/reliable_job_actions`统一承载通知投递、隐私执行、AI评估和离线基准的来源引用；支持业务来源ID、幂等、租约、指数退避、死信和受控人工恢复，不复制业务正文或任意payload。
- `feature_flag_versions`按名称、版本、角色、比例、原因和操作者追加写入，支持指定旧版本原子回滚；渐进发布默认关闭，不能由前端显示状态开启。
- 数据库升至`2026_07_20_020 / reliability_observability_release_engineering`，新增观测、可靠任务/动作、功能开关版本、SLO快照、演练和证据包七表。迁移重复执行通过；SQLite备份方法核对完整性、表行数和SHA-256。回滚先关四个运行开关并保留表、审计和证据，不自动DROP或推断上线。

### F06—F08：故障演练、工作台与运行手册

- 固定合成演练覆盖内容缺失、数据库超时、外部服务失败、凭证失效、重复消息和制品损坏；生产环境禁止故障注入。
- Web`/reliability/release`用“本地机器证据—测试云观察—人工上线门禁”三段信号轨呈现旅程、死信、开关、演练和证据包；页面无上线决定按钮。小程序只增加公开状态方法。
- `docs/04_部署运维/任务三十二可靠性运行手册_20260720.md`登记P0/P1/P2、发现/止损/恢复、恢复时间、备份回滚、证据包和事后复盘；人工负责人仍为待指定。

### 浏览器、桌面证据与问题loop

- Chrome只读确认微信云托管生产环境、MySQL 5.7、备份入口和数据库控制台可访问；生产库当前表清单没有020可靠性表，因此没有执行生产迁移、写SQL、恢复或阈值冻结。
- Computer Use成功启动微信开发者工具Stable，但其当前项目为其他小程序；尝试切换时检测到人工接管，立即停止。SafeHome编译、真机和双账号验收保持外部门禁。
- 首轮T32专项由15失败转为15通过；修复SLO/演练/证据包响应契约、任务到期时间比较、迁移入口和API契约。首轮后端全量为453通过/3旧schema断言失败，三项均为020升级后的019硬编码，定向修复后10项通过；第二轮后端全量`456 passed`。
- 前端命令首次误在`backend`运行而ENOENT，确认是工作目录问题后在`apps/web`重跑通过；没有修改包配置或业务逻辑掩盖问题。

### 工程完成与发布批准分离

最终验收：T32专项`15 passed`、旧schema修复定向`10 passed`、后端全量`456 passed`（9条既有jieba/pkg_resources弃用警告）；Web typecheck/build和桌面/移动全量Playwright`28 passed`；小程序40页/57组件引用/7 Canvas、61 JS/56 JSON；内容、T31 200操作安全注册表、T32可靠性注册表、4份API契约生成物、136冻结兼容、020迁移/回滚、Python编译和`git diff --check`通过。

- 已完成：本地后端、数据库、shared、Web、小程序、权限、审计、异常恢复、迁移、回滚、专项验收、双端构建与文档闭环。
- 尚未批准：测试云连续SLO、CloudBase网关请求链、MySQL隔离备份恢复、SafeHome微信开发者工具、Android/iOS真机、大字体/读屏、值班责任、安全/隐私/伦理复核和上线决定。
- 临时展示越权继续保留，明确不能用于T31正式权限验收或T32上线门禁。所有人工、伦理、真机、云和生产项只生成证据状态，系统未代签。
- 下一工程任务：T33-F01—F08信息架构、可访问性和认知负荷完整实现；先生成全部页面/路由清单和角色/敏感性矩阵，再统一导航、设计token、表单恢复和自动可访问性门禁。

### 2026-07-21 任务三十三完整实现执行结果

状态：`engineering_complete_local / external_human_device_research_gates_pending`。工程完成与发布批准继续分开。

1. T33-F01：生成版本化体验注册表，覆盖小程序40页和Web35路由；目标、主行动、数据源、加载/空/错/重试/成功/拒绝、角色、敏感性、责任域和草稿要求不再依靠人工记忆。
2. T33-F02/F03：首页既有区块不重排，“今天的一小步”位置不变；参与者四入口、研究者五工作区固定并复用原列表/详情。展示越权继续保留且正式权限仍不通过。
3. T33-F04/F05：跨端token和八类模式落地；44px/88rpx、焦点、可访问名称、标题/表单、溢出和减少动画形成确定性门禁。自动检查不能替代读屏/真机，也未宣称WCAG全量符合。
4. T33-F06：小程序目标、日记、测评、打卡、关系任务/成长、人工支持、项目详情，以及Web家长/学生/关系三类测评具备草稿、时间、离开提醒、恢复、超时提示和防重复。登录密码、一次性绑定码不保存。
5. 后端和数据库：021新增体验审计/证据表，六类业务表新增用户级提交标识和唯一索引；同内容重试返回原记录，变更内容复用返回409。修复家长明确拒绝研究授权时`agreed_at`非空约束错误。
6. 权限和审计：公开接口只返回覆盖/门禁摘要；内部矩阵/工作台为researcher/supervisor/admin；自动审计登记仅admin；证据包仅supervisor/admin。证据包永远不代签、不批准发布、不保存参与者原文。
7. 恢复/迁移/回滚：迁移脚本重复执行通过；可关闭工作台和导航并保留审计、证据、提交列与草稿。没有自动删除或破坏性回滚。
8. 自动验收：T33专项12项；API边界快照漂移经loop重生成后定向20项、57 warning/0 blocker；后端首轮467通过/1快照陈旧，修复后全量468项通过（9条既有第三方弃用警告）；内容、205操作权限注册表、136冻结兼容、八类门禁、小程序40页与JS语法、Web typecheck/build和双视口32项Playwright通过。
9. T33-F07/F08：浏览器桌面/移动、键盘、200%文字和减少动画已有自动证据；真实系统大字体、VoiceOver/TalkBack、微信内置环境、Android/iOS和真人认知访谈只生成待补模板，均未签字。

专项证据：`docs/02_专项进度与验收/任务三十三体验与无障碍工程证据_20260721.md`。下一工程任务是T34-F01—F09内容、数据与模型运营治理；不得重复T33，不得把外部门禁写成完成。

### 2026-07-21 任务三十四完整实现执行结果

状态：`engineering_complete_local / external_human_ethics_cloud_device_production_gates_pending`。工程完成与发布批准继续分开。

1. T34-F01：40项能力注册表覆盖机器契约222个操作，登记用途、负责人、依赖、数据、角色、开关、版本、测试、回滚和治理状态；临时展示越权继续保留但正式权限仍阻断。
2. T34-F02/F03：24项内容/规则/模型/词典/提示/知识索引进入不可变哈希快照发布包；16张数据集卡、规则卡和模型卡补齐来源、许可、指标、偏差、失败、域外、准入和停用。
3. T34-F04/F05：固定27条纯合成案例回放推荐、拒答、风险阻断、行为与文案差异；高严重度回归阻断，修订使用新版本，发布与回滚采用锁、暂存哈希、文件备份和数据库指针事务。
4. T34-F06/F07：只保存七类聚合运营指标；漂移只触发复核，明确禁止自动判断参与者或家庭变差，也不保存参与者原文。
5. T34-F08/F09：提出、审核、研究/心理/安全批准和发布执行分离；暂停、重放后恢复、停用、旧包回滚完整。严重越权/泄漏/不良事件/AI失败自动停用、保全证据、排队通知和保留复盘。
6. 全栈：022新增八表；17个API、shared、Web运营治理工作台、小程序只读状态、权限、审计、异常恢复、迁移和保守回滚同步完成。参与者无内部运营权限，Base64包正文不经API返回。
7. 自动验收：专项10项、跨任务契约31项、后端482项；内容、222操作注册、136冻结兼容、生成物、迁移、编译、小程序结构/语法、Web typecheck/build及双视口34项Playwright全部通过。
8. 外部门禁：Chrome只读确认微信云托管生产环境、MySQL 5.7和备份/回档入口可访问；没有执行生产迁移、查询、写入、发布或签字。人工、伦理、CloudBase/MySQL恢复、微信开发者工具、Android/iOS真机和生产批准继续待补；证据包全部批准字段为false、签名为空。

### 2026-07-21 任务二十五至三十四最终工程审计与自动执行器补齐

状态：`T25-T34 engineering_complete_local / release_and_external_gates_pending`。

1. 完成计划第3节缺失项：新增`config/task23_34_registry.json`和`scripts/run_tasks_23_34.py`，连续登记T23—T34及依赖、状态、提交、证据和专项/全量命令。
2. 执行器支持`plan`、`run --next`、`resume`、`verify --task`和`report`，另提供`--dry-run/--full`；命令用参数数组执行，不使用shell拼接。
3. 状态只写`.codex_tmp/task23_34_state.json`并原子替换；该路径被Git忽略。执行器不能修改计划完成状态、不能签署人工/伦理/云/真机/生产门禁，也不调用云平台。
4. `report`核对T25—T34十项工程状态全部完成，十个独立提交均为当前HEAD祖先，登记证据全部存在；`release_approved=false`、`external_gates_executed=false`。
5. T23仍保留完整差距复审状态，T24保持工程完成/外部批准待补；没有为了完成T25—T34审计而改写历史事实。
6. 临时展示越权继续保留，机器报告固定不将其当作正式权限证据。
7. 实际全量执行先通过T34专项13项、后端485项、内容/契约/136兼容、小程序、Web typecheck/build；Web全量首次因并发密码哈希下注册导航超过5秒出现1项超时，快照显示仍在“正在注册”而非业务错误。将等待上限改为20秒且保留最终URL/页面断言后，隔离2项与全量34项通过。
8. 执行器契约增至4项：测试运行状态先备份后恢复；`resume`只跳过命令一致且returncode=0的前缀，注册表命令漂移直接阻断，避免把旧绿色证据套到新命令。

### 2026-07-21 任务二十三完整差距复审与工程收口

状态：`engineering_complete_local / external_cloud_android_ios_large_font_reader_production_gates_pending`。工程完成与发布批准继续分开。

1. T23-F01：今日行动支持记录、测评、训练、消息、阶段反馈、暂停、完成及失败/弱网恢复契约；治疗性评估仍为受控未开放状态。
2. T23-F02：反馈账本新增纠错、撤回、替代版本、参与者状态、幂等动作和审计动作表；研究者只看分配范围聚合，不返回参与者原因原文。
3. T23-F03：推荐新增冷启动说明、替代卡、排序解释、版本快照/回放、功能开关和旧策略回滚；近期完成卡继续后移但不永久禁止复练。
4. T23-F04/F05：关系成长仪表盘完成渐进披露与视觉收口；不同指标组分开显示，不形成单一成长分。ImageGen参考已入库，Figma已建立文件并完成图片导入和局部可编辑组件；Starter限额后停止调用，代码侧继续完成。
5. T23-F06：展示、点击、完成、跳过、恢复、不适和人工升级事件齐全，元数据白名单、客户端事件ID幂等、无参与者原文。
6. 数据库023新增反馈动作与推荐快照表，shared、Web、小程序、权限、隐私范围、机器契约、迁移与非破坏性回滚同步。
7. 问题loop：首轮后端全量489通过/2失败；一项为旧产品事件精确元数据断言，一项为API边界快照陈旧。移除冗余事件字段并重生成57 warning/0 blocker快照后，定向16项和第二轮全量491项通过。
8. 自动验收：专项22项，后端491项，内容/机器契约/225操作安全注册/可靠性/体验/运营生成物、Web typecheck/build、小程序40页/57组件/7 Canvas/62 JS/56 JSON、四视口视觉审计通过。
9. 电脑控制证据：微信真机首页布局保持不变；云托管请求102002超时但错误恢复态可见。检测到开发者工具有人操作后立即停止输入。Chrome仅做云托管、数据库备份入口和发布资料缺口只读核对。
10. 外部门禁未变：CloudBase生产迁移、数据库恢复、完整微信开发者工具、Android/iOS、大字体、读屏、真实双账号、人工/伦理和生产发布未批准；临时展示越权继续保留且正式权限验收仍不能通过。

#### 2026-07-21 关系成长仪表盘设计稿二次收口

状态：`engineering_complete_local / wechat_visual_capture_blocked`。

1. 按目标稿二次统一米白背景、森林绿标题、三项摘要卡、分区标签、空图表提示、柔和阴影、圆角和主操作层级；保留统一成长页与关系详情页既有入口关系。
2. 数据不足时不再创建不可见 Canvas，只展示还差几次记录、继续记录建议和“不会根据单次记录判断变化”的边界提示；达到两点后才绘制趋势。
3. 分区标签补充 `tablist/tab/aria-selected`，摘要数字使用等宽数字，并补齐360px窄屏与600px以上居中适配。
4. 未修改后端、数据库、shared或API；未改变已有业务数据和阶段反馈流程。
5. 自动验收：关系成长/T23契约13项通过，页面JS语法通过，T23四视口视觉系统审计通过，`git diff --check`通过。
6. 微信开发者工具受旧版本缓存的“过滤无依赖文件”错误阻断，未获得可信页面截图；按用户要求停止继续排查。该项只记录为外部视觉验收缺口，不影响本地工程完成，也不作为真机或发布批准。
7. 用户补充截图确认关系试点“成长仪表盘”入口误进通用成长页，并因当前云端通用接口未命中显示404兜底。已将该入口改为`relationship-growth?detail=1&enrollment_id=...`，同时把原通用成长仪表盘保留给个人中心；定向回归测试先红后绿。
8. 首页进度读取失败态的双按钮因局部`64rpx`高度和缺少垂直居中，在当前微信渲染环境中发生文字裁切。已恢复统一触控高度，补齐flex居中、明确行高、内边距与盒模型；针对裁切的测试先红后绿，首页/T23视觉契约11项通过。
9. CloudBase首包启动失败定位到MySQL错误1101；第二包越过首错后因`request_id TEXT`参与唯一键触发错误1170。现将带默认值及参与键/索引的短文本统一映射为`VARCHAR(191)`，覆盖全部内联/显式索引并限制四列utf8mb4复合索引不超过3072字节；初始化可修复失败部署遗留的255字符列。定向37项通过，第三包SHA256为`B4BBD5A556DCE7A62B857058C28CDCC42B82241B2A208E279D2C1357472C55AD`，尚未发布。

### 2026-07-22 任务三十五完整实现计划

状态：`planned_not_started / dataset_rights_ethics_release_gates_pending`。

1. 新增权威计划：`docs/01_当前执行入口/任务三十五公开数据验证与模型优化完整实现计划_20260722.md`。
2. T35-F00至F15覆盖基线冻结、权利门禁、隔离导入、哈希删除、数据适配、标签映射、外部基线、项目域金标准、增强规则、轻量模型、条件式编码模型、统计决策、网络验证、研究者影子比较、全栈治理、恢复回滚和完整验收。
3. 任务三十五继承T29和T34，不改写其历史状态；T29继续代表合成基准和公开元数据登记，T35才负责经批准的公开数据外部验证和候选模型优化。
4. 计划冻结公开数据不能证明训练卡疗效、家庭关系质量或参与者适用性；候选模型不得替代风险规则、人工队列或生产反馈。
5. 本轮只完成计划登记，没有下载公开数据、训练模型、修改数据库、打开外部导入或批准生产发布。
6. 下一步只执行T35-F00至F02，并继续保留其他任务未提交改动。

# 任务三十六：研究者移动平台、受控外部访问与在线能力完整实现

登记日期：2026-07-22

状态：`implementation_in_progress / f00_engineering_complete / credential_tunnel_cloud_wechat_human_gates_pending`

权威详细计划：`docs/01_当前执行入口/任务三十六研究者移动平台与受控在线能力完整实现计划_20260722.md`

## 一、任务36解决的问题

1. 为 Web 研究者后台提供明确账号和安全的一次性密码交付、轮换、失效与恢复流程；
2. 提供让其他获准人员访问 Web 后台的受控外部访问方案，禁止直接公开本地开发端口；
3. 将小程序研究者评估仪表盘扩展为受正式权限矩阵保护的移动研究工作台；
4. 修复训练记录、历次反馈和消息的服务端加载失败，统一错误、分页和恢复语义；
5. 使用微信开发者工具、Computer Use 和 Chrome 完成微信一键登录与手机号快捷登录的真实配置和验收；
6. 后续接入研究者在线情感计算、语义网络/家庭拓扑、AI 自由问答研究沙盒和治疗性评估受控流程；
7. 全程保持非诊断、对象级权限、审计、隐私最小化、异常恢复、迁移和回滚。

## 二、登记时的真实状态

- 本地数据库存在启用的 `safehome1.0/admin` 和 `safehome_researcher_01/researcher`；密码哈希不能还原明文，当前没有可交付的一次性凭据文件。任务36必须轮换并通过被 Git 忽略的 receipt 交付，不得把密码写入本文。
- 小程序已有研究者页，但展示越权只让页面可见，服务端写操作和对象范围仍会拒绝普通账号；截图中的 403 是展示身份与后端真实授权不一致。
- 云端 `/healthz`、`/readyz` 正常，MySQL schema 为 `2026_07_21_023`；`/api/checkins` 无令牌返回结构化 401，但 `/api/messages` 可重复返回 HTML 502，必须先建立云端红灯和日志链再修复。
- 本地与云端 `/api/auth/capabilities` 均显示微信登录和手机号登录 `not_configured`，当前不是前端缺少按钮，而是云端可信身份、AppID/Secret、手机号能力或 access token 尚未配置/验收。
- Computer Use/Chrome 本轮连接初始化失败，因此没有把微信和手机号登录写成已解决；F10/F11必须在插件恢复后取得开发者工具和真机证据。
- 情感计算、语义共现网络和家庭拓扑当前是离线、聚合、脱敏原型，不是已用项目文本训练好的生产模型；AI自由问答只允许默认关闭的研究者沙盒；治疗性评估继续受TA子线和D01—D26门禁。

## 三、权限口径

“研究者平台权限全部开放”当前包含一项明确的开发态临时例外：

- `admin/supervisor`：在批准范围内使用全部研究管理功能；
- `researcher`：只使用分配参与者、可领取队列和获批研究工作流；
- `participant`：正式模式只能读取自己的记录、反馈和消息；开发态 `researcher_platform_full_access=true` 时，Test1、wyd 等所有已登录普通账号可临时读写研究者平台专用接口；
- `showcase`：正式模式只读合成/脱敏演示；开发态临时例外只覆盖研究者平台专用路径，不覆盖导出、账号、安全和生产操作；
- 导出、角色、内容/模型发布、安全、凭据、备份恢复和生产开关继续保留在 Web 的 admin-only 工作区。

临时展示和研究者平台读写越权继续保留用于开发，页面必须显示警告；关闭开关后恢复正式权限。该状态不能用于正式权限验收。

## 四、T36执行状态表

| 子任务 | 状态 | 实现范围 | 自动验收 | 外部门禁 |
|---|---|---|---|---|
| T36-F00 基线与执行器 | 本地工程完成 | `task36_registry.json`连续覆盖F00—F19；执行器支持plan/next/resume/verify/report/snapshot；状态与快照仅写`.codex_tmp` | 9项专项、六个云端只读探针、命令漂移与dirty保护通过 | 无；未执行生产变更 |
| T36-F01 研究者账号 | 本地工程完成/外部接收待办 | receipt环境隔离、24小时失效、首次强制改密、旧会话撤销、锁定/解锁/核验/撤销、双端改密UI和024迁移完成；未动生产凭据 | F01专项23项；执行器专项54项；认证/安全/迁移回归100项，契约/双端构建检查通过 | 负责人接收、生产首次改密、测试云/生产核验 |
| T36-F02 受控外部访问 | 本地工程完成/外部门禁待办 | 默认禁用配置、Named Tunnel/Access/人工门禁模板、loopback同源代理、可恢复控制器和安全阻断完成 | 专项7项、真实本地代理回放、Web build、执行器verify通过；dry-run启动0进程 | 域名、访问者、数据范围、Access与Tunnel批准；未启动公网访问 |
| T36-F03 权限矩阵 | 本地工程完成/外部门禁待办 | 版本化能力注册表、服务端guard、研究者/督导对象分配、幂等领取/撤销/转交、持久化操作回执、025双读双写迁移与双端契约完成；开发例外原范围保留 | F03专项12项、注册表关联24项、后端全量555项、Web typecheck/build、小程序审计和API契约通过 | CloudBase/MySQL迁移、正式角色矩阵人工抽查、合成展示数据；临时越权不得通过正式验收 |
| T36-F04 移动工作台 | 本地完整工程完成/外部门禁待办 | 五工作区、脱敏摘要、分页搜索、弱网/部分失败、下拉刷新、按参与者草稿恢复；原试点功能保留 | 专项26项、四视口×普通/放大文字、40页结构和T33八类门禁、Web typecheck/build通过 | 微信真机、Android/iOS、系统大字体和读屏 |
| T36-F05 参与者档案 | 本地工程完成，真实研究者抽查待办 | 测评、日记、训练、试点、项目、消息、支持时间线按标签分页 | 分页、删除用户、越权ID、敏感审计、跨端契约已自动验证 | 真实研究者对象范围与长文本抽查 |
| T36-F06 反馈消息闭环 | 本地工程完成/外部门禁待办 | 统一草稿、预览、确认、发送；不可变版本、撤回留痕、消息/报告回执和026迁移 | 幂等、重复、版本冲突、权限、撤回、双端构建通过 | 双账号真实收取/已读/撤回、微信真机、CloudBase迁移 |
| T36-F07 训练与反馈读取 | 工程修复完成/云端待部署 | 修复 MySQL DictCursor 计数 KeyError，统一字典读取 | MySQL与训练历史专项通过 | 新包上传后云端真实账号复验 |
| T36-F08 消息502修复 | 工程修复完成/云端待部署 | 定位非法相对 Link 响应头导致网关502；移除该头并改用page_size | API/小程序契约专项通过 | 新包上传后连续云探针 |
| T36-F09 部署指纹 | 本地完整工程完成/测试云观察待补 | 构建清单、health/ready一致性、双端可复制诊断、9条旅程指标 | 专项21项、受影响56项、后端全量560项、双端构建审计与包指纹校验通过 | CloudBase发布后合成冒烟和连续观察 |
| T36-F10 微信登录 | 本地工程完成/云网络与设备门禁待办 | 公网伪造头负向探针曾真实返回token，已撤销AppID匹配自动信任；TRUST=0时统一jscode2session，补齐脱敏审计器、身份复用/停用拒绝和无副作用负向契约 | 核心登录/审计24项、执行器F10专项38项通过；当前待发布包SHA256 `84EF5A19A21BF42385B0FD3E3A31138B93805FC2649568ADF60942A10E629DA1` | 发布当前安全包、确认伪造头400无token、修复公网出访/VPC NAT、开发者工具及Android/iOS真机 |
| T36-F11 手机号登录 | 本地工程完成/Secret、资质与设备门禁待办 | HMAC摘要、同号复用、停用拒绝、账号冲突无损恢复、能力门控和三登录回退完成；Web不申请手机号 | 核心F11专项27项、脱敏审计器、Web typecheck、小程序40页审计通过；当前包SHA256 `DD54D53250CC3C8C6B6771785CB13850F933BA49D31406A0ACFD419B80317D75` | 负责人安全录入Secret或确认CloudBase token、微信资质/隐私、发布和开发者工具/Android/iOS真机 |
| T36-F12 身份与认领 | 本地工程完成/云设备与人工合并门禁待办 | username/openid/phone/anonymous状态机、版本化认领、受控合并和撤销绑定 | 专项54项、全量587项、跨端/迁移/Chrome通过 | CloudBase迁移、真机和账号合并人工确认 |
| T36-F13 在线分析任务 | 本地工程完成/数据伦理模型云与人工门禁待办 | 授权引用快照、七态异步任务、版本/租约/退避/死信/删除 | 专项62项、迁移/回滚、跨端构建、Chrome双视口通过 | 数据用途、伦理、模型权利、测试云worker和人工抽样 |
| T36-F14 情感与网络分析 | 本地工程完成，外部门禁待办 | 聚合情感、语义网络、家庭拓扑研究者视图；仅项目自有合成基准 | 小样本、未知率、版本、图规模、跨端通过 | T35数据/伦理/模型权利、CloudBase与人工抽查待签 |
| T36-F15 AI自由问答 | 工程完成，参与者/生产未开放 | 三研究角色合成沙盒、批准知识引用/版本/不确定性、前后置安全路由、超时/重试/熔断/预算/kill switch、7天合成保留与确认清理 | 专项+T28/F17回归、内容/API/安全/运营注册表、Web/Chrome通过 | AI/心理/伦理/安全/隐私/值守/生产批准 |
| T36-F16 治疗性评估 | 本地工程完成/外部门禁待办 | 参与者问题与共享范围、版本化反馈、人工复核发送、一小步和随访；029加法迁移；Web/小程序双端 | 同意/撤回/不同意/版本冲突/对象范围/L0-L1/风险/审计/隐私删除/双端构建通过 | TA资质、督导、伦理、D01—D26、CloudBase/MySQL和真机 |
| T36-F17 安全可靠性 | 工程完成，发布未批准 | 六链路机器注册表、幂等/并发/死信/恢复、敏感证据禁入、派生删除和生产默认关闭已接入双工作台与小程序摘要 | 专项+T31/T32/F14回归和静态审计通过 | CloudBase/MySQL/安全隐私伦理/生产负责人待人工 |
| T36-F18 迁移回滚 | 本地工程完成/生产迁移恢复门禁待办 | SQLite/MySQL差异矩阵、可重复隔离演练、备份/恢复清单、隐私墓碑复核、非破坏回滚 | 32项专项、7场景隔离演练、API/Web/小程序通过 | CloudBase/MySQL生产迁移、恢复、回滚批准 |
| T36-F19 全量验收 | 本地工程完成/外部门禁待办 | 可恢复验收执行器覆盖后端/shared/Web/小程序/安全/故障恢复/云只读/文档；证据只存哈希 | 614项后端全量、13条必需命令、CloudBase只读快照和设计QA通过 | 人工/伦理/真机/云迁移/生产签字；发布未批准 |

## 五、执行顺序

1. 波次A：F00 → F01 → F02 → F03；
2. 波次B：F08 → F09 → F07 → F06；
3. 波次C：F10 → F11 → F12；
4. 波次D：F04 → F05 → F06移动闭环复核；
5. 波次E：F13 → F14 → F15 → F16；
6. 波次F：F17 → F18 → F19。

F03前不扩大移动权限；F08/F09前消息不进入正式验收；F10/F11真机未通过前保留账号密码回退；T35权利门禁未通过前F14只用既有规则和合成数据；AI与治疗性评估外部门禁未签前不得面向参与者开放。

## 六、自动化执行规则

每个切片执行：事实快照 → 失败契约 → 最小实现 → 权限/并发/异常测试 → 迁移/回滚 → shared/Web/小程序 → 测试云或设备证据 → 全量回归 → 文档 → 独立提交 → 推送。

执行结果直接写在本任务对应 Fxx 和权威详细计划对应 Fxx 下；不单独创建执行记录。人工、伦理、真机、微信和生产只能生成证据包，不能自动签字。发生与现有功能冲突时优先保留现有闭环，把冲突登记为 `feature_conflict`，不得擅自扩大权限或删除历史数据。

## 七、下一轮启动提示词

```text
读取任务三十六权威详细计划、Claude计划模式任务36和当前事实基准，保留全部既有未提交改动，只执行T36-F00。冻结Git、CloudBase health/ready/auth capabilities、messages/checkins/researcher dashboard故障和角色/对象范围，建立task36机器注册表与可恢复执行器。不得轮换生产密码、启动公网隧道、修改微信Secret或放开展示写权限。专项验收通过后把结果写回F00和任务36，更新三份事实文档，独立提交并推送。
```

## 八、T36-F00执行结果（2026-07-22）

- 状态：`engineering_complete_local`；任务36整体仍是`implementation_in_progress`。
- Git冻结点：`a0236bebd675e779dc0e50197e89580ab9c7a5e7 / main / origin/main`；dirty只包含F00新增的3个文件，执行器没有reset、checkout、clean或文件回退能力。
- CloudBase脱敏快照：health/ready/auth capabilities为200；messages/checkins/researcher dashboard无令牌均为JSON 401并带request_id；MySQL schema为023；微信/手机号能力分别为`jscode2session`、`wechat_access_token`。
- 版本漂移：运行版本仍报告`safehome-2026-07-10-task12-login`，留给F09建立构建指纹，不用旧字符串判断是否已部署。
- 权限冻结：participant/researcher/supervisor/admin/showcase与self/assignment/supervision/all/synthetic范围已入机器注册表；`researcher_platform_full_access=true`原值保留，但不是正式权限证据，F00未扩大任何写权限。
- 执行器：`python scripts/run_task36.py plan|report|snapshot`；`verify --task T36-F00`已通过；`run --next`停在F01并在缺少实现后验收命令时拒绝跳步；命令digest变化时禁止resume。
- 安全边界：未轮换生产密码、未启动隧道、未读取或修改微信Secret、未修改CloudBase、未签署人工/伦理/真机/生产门禁。

## 九、T36-F01执行结果（2026-07-22）

- 状态：`engineering_complete_local / external_production_credential_acceptance_pending`；工程完成不等于生产凭据已交付或发布批准。
- 凭据生命周期：`prepare/apply/verify/revoke/rotate`、环境隔离、receipt唯一性、24小时失效、强密码、显式轮换和脱敏错误均已实现；receipt仍只允许写`.codex_tmp`。
- 身份安全：首次登录必须改密；改密和轮换递增`auth_epoch`并使旧token失效；连续5次失败锁定15分钟，支持自动恢复和管理员解锁；核验接口不返回密码、哈希或receipt ID。
- 跨端闭环：Web和小程序在`must_change_password=true`时停止导航，仅允许`me/change-password/logout`，成功改密后替换token再进入工作台。
- 数据与契约：本地schema升级为`2026_07_22_024 / credential_lifecycle`；新增7个用户凭据状态字段及receipt唯一索引；机器契约229项，T31—T34衍生注册表同步。
- 验收：F01专项23项、任务36执行器专项54项通过；认证、安全、MySQL适配、健康和T31—T34契约回归合计100项通过；Web production build、小程序40页审计、API/安全/可靠性/体验/运营契约检查通过。
- 明确未做：未生成或轮换生产密码，未调用`apply/rotate`云端操作，未启动隧道，未修改微信Secret，未扩大临时展示写权限。负责人接收、生产首次改密与云端核验继续保持外部门禁。
- 下一切片：T36-F02仅完成受控外部访问的本地配置/脚本/失败契约和dry-run；不得启动真实公网隧道。

## 十、T36-F02执行结果（2026-07-22）

- 状态：`engineering_complete_local / external_domain_identity_tunnel_gate_pending`；本地工程完成不表示外部地址已开放。
- 工程：默认禁用配置、Named Tunnel模板、Access默认拒绝模板、未批准门禁receipt模板、loopback同源代理和`prepare/start/verify/stop/status`控制器完成。
- 安全：禁止通配Origin、公开监听、直接暴露5050/5173和Quick Tunnel真实数据；启动必须核对负责人/隐私/安全批准、域名、范围与时限。代理不信任或转发`X-WX-*`及Access身份断言，SafeHome登录与对象权限继续执行。
- 恢复：运行状态只写`.codex_tmp`；Tunnel启动失败会终止代理；stop清理受控PID和状态；撤销域名/Access/Tunnel token及账号仍需外部负责人执行。
- 层级说明：F02是访问基础设施切片，数据库、shared、业务后端接口和小程序无字段变更，因此迁移为N/A；Web production build作为全量相关验收。
- 验收：专项7项、SPA深链/API allowlist/身份头剥离真实本地回放、Web build、任务36执行器F02 verify通过。唯一真实控制命令为prepare dry-run，结果`processes_started=0`、`public_access_started=false`、`external_gate_approved=false`、`state_written=false`。
- 明确未做：未启动cloudflared、未修改DNS或生产CORS、未创建Access应用、未批准真实数据、未签署外部门禁。
- 下一切片：T36-F03正式能力矩阵和对象范围；保留既有开发例外，但不得扩大路径或用其通过正式权限验收。

## 十一、T36-F03执行结果（2026-07-22）

- 状态：`engineering_complete_local / external_production_migration_and_formal_acceptance_pending`。
- 权限契约：15项能力默认拒绝；导出、账号、安全和生产管理固定admin-only，且`development_exception=false`。403统一返回`forbidden`、`required_capability`和request_id。
- 对象范围：新增`research_scope_assignments`，researcher仅访问明确分配对象并可幂等领取活动报名，supervisor仅访问监督分配，admin访问全部；撤销和转交使用`expected_version`防并发覆盖。
- 迁移与回滚：本地schema为`2026_07_22_025 / researcher_capability_scope`；旧`assigned_researcher_id`保留并双读双写，回填脚本默认阻断生产，rollback只撤销回填记录、不删除旧字段。
- 双端：shared、Web和小程序API client已同步；小程序仪表盘显示正式角色、矩阵版本和授权项数，页面提示不替代服务端鉴权。
- 开发例外：Test1/wyd现有研究平台精确路径临时提权保留，未扩大到高危能力；通用展示只读绕过不再覆盖真实研究平台，临时例外仍不能作为正式证据。
- 验收：F03专项12项、任务36机器注册表关联验收24项、后端全量555项、Web typecheck/build、小程序审计、API契约重建通过。
- 未做：未执行CloudBase/MySQL 025迁移、未签署正式权限矩阵、未建立正式合成展示数据源，未启动隧道、轮换生产密码或修改微信Secret。
- 下一切片：按注册表继续F08/F09云端故障与指纹闭环；F04依赖F09，不能提前把未验证云端状态包装成移动工作台完成。

## 十二、T36-F09执行结果（2026-07-22）

- 状态：`engineering_complete_local / external_test_cloud_observation_pending`；没有发布CloudBase或推断生产批准。
- 构建一致性：制品生成`safehome.build-fingerprint.v1`，记录commit、build time、API契约/content哈希、build ID和预期schema；包校验拒绝错误哈希、秘密样式字段与本地绝对路径。
- 运行诊断：`/healthz`暴露安全构建身份和版本响应头；`/readyz`分别识别`backend_contract_mismatch`、`content_manifest_mismatch`、`database_schema_mismatch`并在生产降级503。
- 可观测性：可靠性注册表升级为9条旅程；登录、消息、训练记录和研究者仪表盘聚合成功率、P95、5xx、502、401/403、重试与恢复，仅保存传输元数据。
- 双端恢复：Web研究者仪表盘与小程序消息/训练记录/研究者仪表盘错误态可复制request_id、客户端/服务/构建版本和时间，不复制token、正文或任意请求载荷。
- 验收：专项21项、旧注册表影响契约56项、后端全量560项通过；内容校验、Web typecheck/build、小程序40页审计、JS语法和云托管包指纹校验通过。
- 门禁：测试云合成冒烟、连续SLO、Android/iOS、生产schema迁移/恢复和发布批准仍待外部执行；临时展示越权保持原范围且不能作为正式权限证据。
- 下一切片：以`python scripts/run_task36.py run --next`返回为准，不能使用文档中的旧`next`命令；继续禁止自动改微信Secret、启动公网隧道或放宽展示写权限。

## 十三、T36-F04执行结果（2026-07-22）

- 状态：`engineering_complete_local / external_wechat_device_screen_reader_gate_pending`；工程完成与微信真机、设备和发布批准分开记录。
- 移动信息架构：研究者页拆为待处理、参与者、反馈与消息、试点项目、我的工作五区；首屏只显示总数、优先级、等待时间和同步状态，原关系试点详情与全部既有操作保留在试点区，Web复杂工作不迁入手机。
- 状态与恢复：五队列使用`Promise.allSettled`隔离，支持加载、空、错误、离线、权限提示、部分失败、重试和下拉刷新；参与者搜索350毫秒防抖、稳定分页追加，长列表失败不伪装为空；阶段反馈、消息和备注按参与者本地恢复草稿。
- 权限与隐私：导航按F03 capability生成，深链继续服务端鉴权和对象范围检查；列表不显示填写原文，错误界面只显示request_id。展示全权限警告保留，未扩展导出、账号、安全、生产或高风险写能力。
- 全栈契约：`GET /api/research/participants`兼容增加`page/page_size/total/has_more`并保留旧`limit`；shared和Web client同步类型。数据库无新表/列/迁移，列表查询继续写审计，回滚不删除任何工作项、报名、消息或审计。
- 验收：F04及权限/运营影响专项26项通过；Web typecheck/build、小程序40页结构审计、T33八类自动体验门禁和JS语法通过；专用Playwright覆盖360/375/430/768与普通/放大文字8种组合，检查横向溢出、44px触控、可访问名称和长昵称省略并生成本地截图。
- 外部门禁：微信开发者工具、Android/iOS、系统大字体、读屏及正式五角色人工抽查待补；自动化截图和临时展示账号不能替代上述验收。未迁移CloudBase、未启动隧道、未修改微信Secret。
- 下一切片：T36-F05参与者全景档案，必须按模块按需读取，禁止一次返回所有长文本；先补对象级分页/过滤和敏感详情审计，再接入移动标签页。

## 十四、T36-F05执行结果（2026-07-22）

- 状态：`engineering_complete_local / external_researcher_sampling_gate_pending`；未将本地工程完成写成CloudBase或生产批准。
- 读取架构：参与者列表只给最小活动摘要；档案摘要只给匿名ID、报名/分配状态、模块数量和审计数量；十个模块通过独立端点按标签、页和过滤条件读取，不再一次返回全部长文本。
- 跨端：shared统一模块键、分页、时区和边界字段；Web与小程序均在选择标签后请求详情，支持下一页，默认隐藏联系方式和登录标识。
- 权限与审计：服务端继续校验角色、研究授权和对象分配；删除用户、撤回授权和越权ID返回不可访问。敏感模块每次读取单独审计，但审计元数据不保存原文。
- 数据与恢复：无新表、无新列，迁移为N/A；按实际存在列投影以兼容旧数据，缺失模块返回空页。客户端模块失败不删除已显示摘要，允许原标签重试；回滚无需删除业务记录。
- 验收：F04/F05/权限/安全/运营相关专项52项通过；Web typecheck/build、小程序40页审计、T33八类体验门禁、API机器契约和136条冻结操作兼容回放通过。
- 外部门禁：真实researcher/supervisor/admin对象范围抽查、长文本人工可读性、微信真机、CloudBase与生产发布仍待人工/外部批准；临时展示全权限不作为正式权限证据。
- 下一切片：T36-F06研究反馈、报告与站内消息移动闭环，采用草稿—预览—确认—发送和不可变版本，不覆盖原始提交。

## 十五、T36-F06执行结果（2026-07-24）

- 状态：`engineering_complete_local / external_dual_account_device_gate_pending`；本地工程完成不等于CloudBase、微信真机或生产批准。
- 交付状态机：阶段性反馈和参与者消息统一为`draft → previewed → confirmed → sent`，每一步要求独立幂等键和`expected_version`；跳步、过期版本和重复键冲突返回结构化409。
- 不可变与撤回：预览写入新的不可变版本和内容哈希；修改后再次预览只新增版本。撤回将工作流、消息和报告标记为撤回并追加事件，不删除旧内容、版本或审计。
- 权限与风险：创建、查看、预览、确认、发送和撤回均重查报名及researcher/supervisor/admin对象范围；参与者临时展示全权限未扩大为写权限。内容执行长度、边界和风险检查，高风险研究者普通发送被阻断并保留人工处置语义。
- 数据与迁移：schema升级为`2026_07_23_026 / research_delivery_workflow`；新增交付工作流、不可变版本、状态事件三表和消息交付版本/撤回字段。迁移脚本默认阻断生产；回滚仅执行应用层兼容处理，保留增量结构与全部交付历史。
- 双端体验：Web和小程序使用同一shared契约及四步交付轨道，预览展示最终文本、边界和版本，发送后展示回执。参与者消息列表/详情展示版本、未读/已读/撤回；撤回内容明确提示忽略旧版本。
- 设计审计：复用暖白、低饱和绿和圆角卡片，以单步主动作降低误发与认知负担；交付按钮保持44px/88rpx最小触控。
- 自动验收：F06/权限/移动档案专项24项、后端全量572项、API契约136条冻结操作回放、内容校验、小程序40页与T33八类体验门禁、Web typecheck/build、本地迁移apply/verify及执行器F06 verify均通过。
- 阻塞证据：Chrome扩展控制运行时返回`failed to write kernel assets`，未取得本轮浏览器截图；该问题只阻塞自动浏览器证据，不否定代码/构建测试。微信开发者工具、双账号真实收取/已读/撤回、Android/iOS、大字体/读屏、CloudBase 026迁移和生产批准仍需人工或外部门禁，不能自动签字。
- 下一切片：注册表当前返回T36-F10。F10本地已有紧急安全修复，但CloudBase发布、公网负向探针、微信网络/VPC NAT和真机仍是外部门禁；继续禁止自动修改微信Secret、启动公网隧道、迁移生产库或扩大临时展示写权限。

## 十六、T36-F10执行结果（2026-07-24）

- 状态：`engineering_complete_local / external_cloud_network_device_gates_pending`；工程完成不等于CloudBase发布、微信真机或生产批准。
- 安全模式：默认继续冻结`TRUST_CLOUDBASE_IDENTITY_HEADERS=false`。CloudBase默认公网域名不提供身份鉴权，历史公网负向探针已证明请求方可以伪造微信身份头，因此当前正式路径只允许服务端`jscode2session`。
- 自动审计：新增脱敏F10审计器，核对AppID、云环境、服务名、显式可信开关、能力接口、错误契约和账号密码回退；输出不包含微信身份值、Secret、code或token。
- 身份契约：补测同一微信身份首次创建parent、再次登录复用原用户、停用账号返回403，以及未显式信任时伪造身份头返回400且不创建用户。
- Computer Use证据：已只读打开`miniprogram - 微信开发者工具 Stable v2.01.2510290`，确认项目窗口和预览/真机调试/上传入口存在；未点击上传、未修改配置、未自动登录。
- 包证据：`.codex_tmp/safehome-cloudbase-task9-20260724_035700.zip`和`latest.zip`，1043801 bytes，SHA256 `84EF5A19A21BF42385B0FD3E3A31138B93805FC2649568ADF60942A10E629DA1`，本地验证通过。
- 自动验收：核心登录/审计24项、执行器F10专项38项、API契约和小程序40页审计通过；执行器识别F10本地工程完成并把下一切片推进到F11。
- 外部门禁：当前包发布、公网伪造头400无token、CloudBase公网出访或VPC NAT、开发者工具首次/再次登录、Android/iOS、token过期和停用账号真机均待人工/外部批准；本轮未执行生产变更。
- 下一切片：T36-F11手机号快捷登录。可以完成本地能力、隐私、绑定、错误恢复和证据包，但不得自动录入或轮换微信Secret，也不得代替微信资质、隐私和真机签字。

## 十七、T36-F11执行结果（2026-07-24）

- 状态：`engineering_complete_local / external_secret_qualification_device_gates_pending`；本地工程完成不代表手机号能力已获微信批准或云端已可用。
- 后端与数据：沿用`POST /api/auth/phone-login`、`users.phone_hash/phone_verified_at/phone_source`和HMAC摘要，不保存完整手机号。相同手机号复用原账号，停用账号403；手机号与微信身份指向不同账号时返回409，不自动合并、不改写另一账号。
- 隐私与审计：测试扫描数据库行和日志均无完整手机号；响应只返回掩码。新增脱敏F11审计器，不读取Secret、token或真实号码。
- 小程序体验：能力接口返回不可用时，微信/手机号按钮改为清晰的“暂不可用”状态，不再产生可点击但必然失败的动作；原因提示、拒绝/取消/过期/服务失败恢复和账号密码兜底保留。
- Web与shared：Web明确快捷登录只在小程序发起且网页不读取手机号；shared继续使用统一能力和登录结果契约，没有另造字段。
- 迁移与回滚：本轮无新表、无新列，迁移为N/A；回滚只需还原入口门控显示，保留摘要、绑定时间、历史和审计。
- 验收：核心F11专项27项、Web typecheck、小程序40页审计、脱敏审计器和云托管包校验通过。包为`.codex_tmp/safehome-cloudbase-task9-20260724_042234.zip`及`latest.zip`，1045159 bytes，SHA256 `DD54D53250CC3C8C6B6771785CB13850F933BA49D31406A0ACFD419B80317D75`。
- 外部门禁：微信主体/类目资质、隐私指引、CloudBase token或Secret安全配置、云端发布、开发者工具授权/拒绝/过期、Android/iOS均待负责人和外部平台验收；本轮未读取或修改Secret。
- 下一切片：T36-F12身份绑定、数据认领与角色保持；重点是防止快捷登录意外继承后台角色，并把冲突交给受控认领状态机。

## 十八、T36-F12执行结果（2026-07-24）

- 状态：`engineering_complete_local / external_cloud_device_human_merge_gates_pending`；任务36机器注册表共20项、工程完成13项，下一自动化切片为T36-F13。
- 身份与角色：参与者端统一呈现username、微信、手机号摘要和匿名记录状态；接口不返回身份原值。微信/手机号快捷登录命中researcher、supervisor或admin时固定403，后台角色不能进入参与者会话，临时展示越权也不作为正式权限证据。
- 认领与并发：匿名记录采用预览、版本确认、幂等执行和`available → processing → claimed`状态；同键重放不重复迁移、不重复审计，冲突保留原归属并可恢复。
- 合并与恢复：正式合并限定参与者账号，采用候选、人工确认、执行、核对、24小时撤销窗口；逐记录清单保存原值/目标值。合并后出现新认领时拒绝自动撤销，避免覆盖新业务事实。
- 撤销绑定：参与者可撤销微信或手机号绑定；最后一种登录方式不能撤销。成功撤销递增`auth_epoch`使所有旧会话失效，但目标、日记、测评、训练、项目和审计记录全部保留。
- 全栈：schema为`2026_07_24_027 / identity_claim_lifecycle`；shared、Web隐私中心/admin安全工作台、小程序“我的”页、权限、审计、迁移和非破坏性回滚同步完成。
- 验收：专项54项、后端全量587项、Web typecheck/build、小程序40页、API契约和136项兼容回放、边界/内容/安全注册表、迁移/回滚及F12审计通过。Chrome实测1440/430双视口无横向溢出；微信和真机仍待外部门禁。
- 包证据：`.codex_tmp/safehome-cloudbase-task9-20260724_154013.zip`及`latest.zip`，1059701 bytes，SHA256`519A38628BDEF50E769EA65B87EB8CA9FB274F6A7B585A63DDD1595856536047`；未上传、未发布、未迁移生产库、未执行真实账号合并。
- 下一切片：T36-F13研究者在线分析任务框架；先建立只引用授权快照的异步任务/工件状态机，不在参与者请求中同步计算，也不提前开放F14/F15能力。

## 十九、T36-F13执行结果（2026-07-25）

- 状态：`engineering_complete_local / external_data_ethics_model_cloud_human_gates_pending`；任务36机器注册表共20项、工程完成14项，下一自动化切片为T36-F14。
- 数据与任务：新增授权快照、来源引用、分析任务、派生工件和状态事件五表。快照只保存来源ID、版本和SHA256；任务只保存分析/资源版本和最小聚合参数，递归拒绝原文、正文、prompt和诊断标签。
- 状态机：支持`queued/running/succeeded/failed/canceled/expired/suspended`，幂等排队、互斥租约、指数退避、死信、创建者取消、admin人工恢复/冻结和可追溯派生结果删除。授权撤回、授权版本变化或快照过期会同步冻结任务与结果。
- 权限与呈现：正式创建能力限定researcher/supervisor/admin并继续执行对象范围；运行、恢复、冻结和删除为admin受控操作。Web新增`/research/analysis`，小程序研究者工作台新增“在线分析”只读摘要；固定研究者影子模式和非诊断边界。
- 数据库：schema为`2026_07_25_028 / research_analysis_job_framework`；SQLite/MySQL共用加法schema，生产迁移默认阻断，回滚先停执行器并回退应用，不自动DROP表或删除来源/审计。
- 验收：F13专项4项、受影响62项、后端全量591项（首次581通过，机器矩阵再生成后10项失败集复跑通过）、Web typecheck/build、小程序40页、API机器契约、迁移apply/verify/rollback和F13审计通过。Chrome实测1440/430视口无横向溢出，修正指标卡误导性“+”装饰。
- 外部门禁：研究数据用途与伦理、模型/词典权利、CloudBase 028迁移、测试云worker观察、研究者人工抽样和生产发布均未批准；临时展示越权不能作为正式权限证据，也未扩大写权限。
- 下一切片：T36-F14情感计算、语义网络和家庭拓扑在线呈现；只接入权利已确认的既有规则与合成数据，T35门禁未通过前不处理真实参与者文本。

## 二十、四模块深度开发增量移植（2026-07-27）

### M1：F16治疗性评估硬化

- 状态：`engineering_complete_local`。
- 保留F19边界：参与者创建协作时不能指定研究者，仍由督导或管理员分配。
- 新增：高风险问题和高风险反馈尝试进入风险复核队列；反馈必须包含可核对依据，存在观察时必须给出其它可能理解。
- 新增：起草者不能复核自己的反馈，只有草稿可复核；参与者状态变更支持可选版本校验；撤回后不能新增行动；行动引用的反馈必须属于同一协作。
- 异常：幂等事件只捕获唯一约束冲突，其它数据库异常保持原样上抛。
- 验收：治疗性评估、研究对象范围和研究交付专项共20项通过；未执行生产迁移、外部门禁或权限放开。

### M2：关系报告与关系叙事状态门控

- 状态：`engineering_complete_local`。
- 报告只能由具备`research.feedback.write`能力的研究角色生成；参与者不能主动触发画像和解释生成。
- 参与者在报告发送前只看到“正在人工核对”及边界说明；画像、机制假设、个性化解释、下载和假设核对均保持关闭。
- 报告发送后才开放用户可见内容和核对入口；研究者对象范围和临时展示策略未扩大写权限。
- 未确认的叙事不向参与者开放；参与者收到的已确认叙事移除研究者内部备注，研究端明确标记草稿或已确认状态。
- 验收：关系试点/对象范围/交付专项22项、小程序41页结构审计和64个JS/57个JSON资源校验通过。

### M3：情感计算聚合边界硬化

- 状态：`engineering_complete_local / external_data_rights_and_human_validation_pending`。
- 聚合入口同时限制字段、嵌套深度、集合规模和字符串长度，阻断把参与者原文伪装成聚合值写入任务或工件。
- 离线结果读取新增独立结构隐私门，不再只信任产物自报的`privacy_gate_passed`；原文字段、诊断字段、超长文本或过深结构均不可用。
- 情绪词表由26个测试词扩展到72个日常表达；继续明确为项目测试词表，不替代外部词库授权、人工标注和效度研究。
- 否定词命中保持原有中性化计算，同时新增单独的否定极性线索和有效覆盖率，避免悄悄改变既有指标含义。
- 修复`crisis_expression`基准标签缺失；该标签只用于人工复核线索，不自动诊断或危机预测。
- 验收：情感硬化、文本分析、F13任务和F14视图专项17项通过；F14静态审计全项通过。未处理真实参与者原文，未批准数据用途、词典权利或生产执行器。
- 下一步：M4受控AI问答安全骨架；保持参与者入口和真实供应商关闭，明确区分接口超时返回与上游调用真正取消。

### M4：受控AI问答安全骨架

- 状态：`engineering_complete_local_fake_only / external_ai_governance_and_provider_gates_pending`。
- 新增可审计提示词实体，固定只允许材料整理、问题草拟、证据不足提醒和讨论清单；诊断、人格定性、预后、用药、法律判断及治疗保证继续阻断。
- 回答必须引用存在的`[S编号]`，引用越界、无引用、结论性语言或明显与批准来源无关时降级为固定安全回复。
- 词面支撑检查明确标记为启发式阻断器，不作为事实正确性证明，也不能替代人工复核。
- fake供应商回填合成token和成本，使预算链路可测试；熔断改为按用户和供应商隔离，避免单个研究者失败拖垮全部沙盒。
- 超时契约由供应商传输层执行；当前fake实现该契约。没有继续采用`thread.join(timeout)`，也不声称接口提前返回等于上游调用已取消。
- `fake_mode`只在development/testing生效；生产环境忽略客户端故障注入。真实供应商仍未实现、未批准、未接密钥。
- 验收：AI生产就绪骨架、受控沙盒、T28契约与F15闭环共26项通过；F15静态审计通过。参与者入口、真实数据、外部供应商及正式反馈写入继续关闭。
- 下一步：M5情绪温度计支持性回执和训练卡衔接，补齐shared与小程序契约及本地时区。

### M5：情绪温度计支持性回执与训练卡衔接

- 状态：`engineering_complete_local / external_device_visual_gate_pending`。
- 创建记录后返回结构化`receipt`，只描述今日第几次、今日均值和近七天对照；单次高低明确提示“不代表趋势”，不评价好坏或疗效。
- 日期按`Asia/Shanghai`解释带时区ISO时间，修复UTC跨日导致今日次数和曲线日期偏移的问题。
- `shared/types/api.ts`新增统一回执契约；小程序保存后显示两条以内低负担回执，并提供“去练一张卡”入口，训练卡仍走既有治理和推荐接口。
- 回执是即时计算字段，不新增数据库表或列、不保存派生判断；网络失败仍保留原记录错误恢复。
- 验收：温度计/T10专项15项、Web TypeScript、小程序41页结构和64个JS/57个JSON资源校验通过。
- 外部门禁：微信开发者工具和真机视觉/读屏仍待人工；本轮未发布CloudBase。
- 下一步：M6 Web顶层ErrorBoundary与懒加载恢复，增加无敏感错误日志和可测试重试上限。

### M6：Web顶层错误边界与懒加载恢复

- 状态：`engineering_complete_local / external_browser_fault_injection_gate_pending`。
- React根节点加入ErrorBoundary，渲染异常不再显示整页空白；兜底页提供重新加载和返回首页，44px触控与键盘焦点样式齐备。
- 所有现有`lazy(...)`页面统一经过`lazyWithRetry`；分包失败时每个路径最多自动刷新一次，第二次失败交给错误边界，避免无限刷新。
- 生产环境不输出错误message、组件栈、props或用户正文；开发环境只记录脱敏错误类型。
- 验收：错误恢复契约1项、Web TypeScript和production build通过。
- 外部门禁：真实CDN分包失败、弱网、浏览器版本及辅助技术人工验收仍待外部执行。
- 下一步：M7前端设计Token、页面状态、分批视觉与可访问性审计；只按当前页面结构增量修复，不应用Claude Patch 7的大规模重复文件。

### M7：前端设计Token、页面状态与可访问性治理

- 状态：`engineering_complete_local / external_device_screen_reader_visual_gate_pending`。
- 建立`shared/design/experience-tokens.json → Web/小程序`可执行契约：颜色、触控尺寸和三档字号均由只读脚本校验；小程序tabBar主色与共享Token精确一致。
- CI新增设计Token、小程序UI治理和四视口视觉状态审计；不执行Claude Patch 7的颜色/字号批量重写，避免在没有逐页截图时改变页面含义和层级。
- 小程序41个注册页面均有可访问名称；自定义可点击`view`补齐角色与名称，温度计增加slider语义和当前值。
- 统一注册`page-state`；项目列表和关系手记的加载、空态、错误及恢复动作使用统一组件；修复设置页误用`state`而导致状态样式失效。
- 高风险反馈页补齐“查看安全指引/提交人工关注”行动，安全指引页补齐现实支持资源入口；不写入未经核验的热线号码。
- 验收：Token契约、小程序UI治理、41页结构/64个JS/57个JSON、T23四视口、T33八类×82项、Web typecheck/build通过。
- 外部门禁：大字体、读屏、微信内嵌环境、Android/iOS、真机逐页截图和形成性认知访谈仍待人工；这些未被自动标记通过。
- 下一步：M8全量回归、事实收口和云托管容器包；仍不得自动发布、迁移生产库或签署人工/伦理门禁。

### M8：全量回归与故障闭环

- 状态：`engineering_complete_local / release_not_approved`。
- 全量验收首次发现项目列表改造遗漏待审核数量、API机器契约及安全/运营注册表漂移、任务36全完成后的“下一任务”测试仍假定存在待办；均按故障loop最小修复。
- API契约、边界审计、安全注册表和运营注册表已经重建并通过`--check`；没有修改生产配置或外部平台。
- 最终机器证据：`.codex_tmp/task36_f19_acceptance_post_m7.json`，后端627项及内容、API兼容、Web、小程序、安全、可靠性、迁移恢复和文档全部通过。
- 发布批准仍为false；七类外部门禁均为`evidence_pending`，临时展示越权仍不计正式权限证据。
- 下一步：以通过验收后的Git提交构建CloudBase容器包，核验内容、启动文件和SHA-256；只生成，不上传、不发布。

### M9：CloudBase容器包

- 状态：`package_built_and_verified / upload_and_release_not_executed`。
- 基线：`main@0adf8a0e05f07e8a93688289ac8fbd679039918f`。
- 包：`.codex_tmp/safehome-cloudbase-task36-m8-20260727.zip`，1,122,762 bytes。
- SHA-256：`7CAA47D19CF386761D8C3B23E952344113F6D0E28DCFB94EC7101A99C9181FDA`。
- 构建指纹已写入包内：build id `3eda7b33218416822080`；包校验脚本通过。
- 包只包含Dockerfile、后端、content和shared；不包含环境变量、数据库、日志、缓存、虚拟环境或Web构建产物。
- 未上传CloudBase、未执行数据库迁移、未发布；下一步等待负责人明确批准。

# 任务三十七至三十八完整实现计划（2026-07-27）

状态：`planned_detailed / engineering_not_started / release_not_approved`

权威详细计划：

- `docs/01_当前执行入口/任务三十七至三十八完整实现主计划_20260727.md`

## 任务三十七：情感计算、社会网络分析与受控AI生产化

任务三十七负责生产计算能力，不负责把系统包装为正式治疗性评估：

- T37-P00—P04：事实冻结、预期/禁止用途、统一计算契约、生产数据血缘、异步任务与可观测性；
- T37-A01—A07：数据权利、标签体系、双人标注、候选模型、校准/弃答、群体SNA、模型注册、影子执行、漂移和发布门禁；
- T37-B01—B05：把任务三十八的服务级别、胜任力、O/P/H/U、五道门、人工队列、反馈生命周期和外部门禁接入生产基础设施；
- T37-C01—C10：AI用例、供应商合同、真实Provider、批准知识库、输入安全、输出五道门、人工审阅、评测红队、预算熔断和分阶段发布；
- T37-R01—R04：测试云、生产迁移证据包、canary、全量回归和发布观察。

当前基线必须保留：

- 情感计算尚未完成真实数据授权、双人标注、本地效度或生产训练；
- 社会网络分析只是群体级描述性分析，不是训练模型，不得产生个体标签或关系结论；
- AI仍为FakeProvider，参与者入口关闭；
- 公开数据只能用于方法比较或预训练参考，不能替代本项目验证；
- 临时展示越权不能作为正式权限验收。

## 任务三十八：协作式阶段性评估知识转译、胜任力治理与分阶段试点

任务三十八负责方法和服务闭环，不训练情绪模型、不采购大模型：

- T38-F00—F05：108份资料来源注册、L0—L3服务级别、状态机、O/P/H/U证据账本、评估问题和多方动态同意；
- T38-F06—F10：参与者八页面、适用性/安全、研究者证据工作台、分层反馈、用户核对、撤回、小行动和随访；
- T38-F11—F18：T1—T3胜任力、督导、低风险成人首发、未成年人/伴侣保护子线、AI五道门、内容治理和研究指标；
- T38-F19—F25：A0专家走查、A1认知访谈、A2低风险人工原型、A3形成性试点、A4可行性试点、停止恢复和全量验收。

强制边界：

- 用户端使用“支持性评估”“协作式阶段性评估”“自我了解线索”，L0/L1不得称为AI治疗性评估；
- 系统和AI最多整理O或提出P候选，H必须由具备相应胜任力的真人提出并复核；
- AIS、FIS、第三层反馈、测验解释、未成年人/伴侣反馈和危机处置不自动化；
- 工程完成与伦理、资质、试点和生产批准分开记录；
- 自动化只能生成A0—A4证据包，不能代替专家、参与者、督导或负责人签字。

## 执行顺序

1. T37-P00—P04；
2. T38-F00—F05；
3. T38-F06—F12；
4. T37-A01—A07与T37-C01—C10；
5. T38-F13—F18；
6. T38-F19—F25与T37-R01—R04。

首个自动切片：`T37-P00 + T38-F00`。只建立事实、注册表、来源和可恢复执行器，不修改生产配置、真实数据、Secret、CloudBase或参与者入口。

## 2026-07-27：任务37/38负责人门禁答复

- 已授权自动执行T37-P00与T38-F00起的本地工程、测试、独立提交和推送。
- 试点按非商业研究管理；SocioPatterns只作非商业离线基准；DeepSeek/OpenAI作为真实AI候选；中国大陆数据驻留为默认约束。
- 负责人确认关系/SNA数据已有专项知情同意、伦理/隐私材料已有、A1—A4具备招募条件；相关证据仍需归档后才能把机器门禁改为通过。
- 个体风险需求被规范为只供真人复核的影子信号，不能生成参与者标签、自动结论或自动处置。
- 全人群、参与者自由问答和网页搜索入库进入工程范围，但分别受人群专项门禁、真实值守/红队门禁和隔离审核门禁约束。
- “训练默认同意”不执行，必须独立主动选择且默认不选；不同意训练不影响基础服务。
- 当前没有T1—T3人员且暂不设置督导/值守，因此L1—L3、未成年人/伴侣真实反馈、高风险自由文本和参与者真实AI生产入口保持关闭。
- 五类专家Agent和三个责任Agent只用于预演和证据包，不能代替真人资质、责任或签字。
- 允许在技术门禁通过后自动迁移/部署/回滚；脚本不得代签专业、伦理和真实责任人门禁。
- 完整逐项决策写入`docs/01_当前执行入口/任务三十七至三十八完整实现主计划_20260727.md`第9节，术语写入根目录`CONTEXT.md`。

## 2026-07-27：T37-P00 + T38-F00执行记录

- 状态：`engineering_complete / release_not_approved`。
- T37-P00：冻结`main@777ba8b`、schema 029、13项核心资产指纹和当前能力；建立57项机器注册表、依赖图、可恢复执行器与本地checkpoint。
- T38-F00：建立108份资料来源注册表，统计为DOCX 77、Markdown 25、HTML 4、JSON 2；只保存元数据和哈希，不嵌入原文。
- 新增独立`agents/task37_38/`与`rag/task37_38/`契约目录。五类专家Agent和三个责任Agent只生成候选证据，`count_as_human_signoff=false`；网页资料进入候选隔离，不自动进入生产索引。
- 参与者入口按负责人要求登记为开发开放，当前最大服务级别为L0；真实Provider低风险问答仍需完成隐私、红队、成本、熔断和回滚机器门禁，高风险自由文本在无值守时不生成个性化回答。
- 验收：基础专项9项通过；来源注册检查、执行器`report/snapshot/verify`均通过；未修改数据库、shared、Web、小程序、CloudBase、Secret或生产数据。
- 下一任务：`T37-P01`，冻结情感计算、群体SNA与AI的预期用途、禁止用途和分用途授权。

## 2026-07-27：T37-P01执行记录

- 状态：`engineering_complete / external_review_pending / release_not_approved`。
- 新增三类计算领域和四类数据用途的机器治理契约；模型训练与二次研究必须独立主动授权、默认不选、可撤回。
- 个体风险只允许形成不面向参与者的“需要真人了解”影子信号；禁止诊断、人格定性、关系优劣评分、自动危机处置和自动治疗决定。
- 后端复用`consent_records`，新增`service_data / quality_evaluation / model_training / secondary_research`四种记录类型，无数据库迁移。
- 数据使用授权服务对未知值、用途错配、撤回授权、可识别训练数据和权利未批准来源默认拒绝。
- 验收：相关15项测试、内容校验、T37-P01专项审计通过；外部五类真人审核仍待证据。
- 下一任务：`T37-P02`统一计算契约与版本注册。

## 2026-07-27：T37-P02执行记录

- 六类计算对象统一为`safehome.computation.v1`；新写入严格、旧记录只读兼容。
- 后端新增只读公开状态接口，shared、Web和小程序客户端已同步；生产写入仍关闭。
- 验收：专项10项、Web typecheck/build及小程序API语法检查通过。
- 下一任务：`T37-P03`生产数据层、血缘与隐私生命周期。

## 2026-07-27：T37-P03执行记录

- 状态：`engineering_complete / production_migration_not_executed / release_not_approved`。
- schema升至`2026_07_27_030 / computation_lineage_privacy_lifecycle`，新增数据集、授权快照、派生血缘、删除墓碑和法定保留五类元数据表。
- 服务端以HMAC对象摘要代替原始身份，拒绝把原始文本写入血缘层；撤回递归追踪派生资源并追加墓碑，法定保留会显式阻断自动删除。
- 新增SQLite/MySQL加法迁移和恢复核验器；生产apply需要精确确认，rollback不DROP表、不删除历史。
- 验收：P03专项7项、受影响契约48项、MySQL索引专项及内容校验通过；未操作生产数据库。
- 下一任务：`T37-P04`异步任务、Harness与可观测性。

## 2026-07-27：T37-P04执行记录

- 状态：`engineering_complete / production_execution_disabled / release_not_approved`。
- 复用既有可靠任务表形成七态计算Harness，补齐取消、冻结、恢复、资源上限和哈希化worker心跳。
- 情感计算、社会网络分析和参与者AI各有独立默认关闭开关；队列只接受资源引用和调度字段。
- 观测指标覆盖吞吐、排队时长、失败率、覆盖率、弃答率、成本和人工积压，错误分为用户、数据、模型、供应商和权限五类。
- 验收：P04及受影响可靠性/API契约36项、专项审计、内容校验、Web类型检查及机器契约检查通过。
- 下一任务：`T38-F01`服务级别L0至L3与对外命名。

## 2026-07-27：T38-F01执行记录

- 状态：`engineering_complete / l1_l3_external_human_gates_pending / release_not_approved`。
- 建立L0—L3版本化服务级别与公开命名；默认和无人工责任链生产上限为L0。
- case、shared、Web、小程序和API client统一使用`service_level`；小程序显示“支持性评估”，Web显示“协作式评估工作台”。
- L0/L1不能称为AI治疗性评估，正式TA名称只属于L3且尚未开放。
- 验收：F01与既有协作7项测试、前端类型检查、小程序语法、命名审计和内容校验通过。
- 下一任务：`T38-F02`问题驱动状态机与兼容迁移。

## 2026-07-27：T38-F02执行记录

- 状态：`engineering_complete / production_migration_not_executed / release_not_approved`。
- schema为`2026_07_27_031 / therapeutic_assessment_state_machine`；工作流、假设成熟度、安全事件三轨独立保存。
- 统一转换接口保存操作者角色、时间、原因、前后版本和幂等键；非法跳转、旧版本、重复提交、撤回终态均显式拒绝或幂等返回。
- 兼容迁移只加字段并映射旧case；生产apply需要精确确认，回滚不删除历史字段和审计。
- shared、Web、小程序客户端和机器API契约已同步。
- 验收：专项与既有协作24项、API契约17项及Web生产构建通过；生产迁移未执行。
- 下一任务：`T38-F03` O/P/H/U证据账本。

## 2026-07-27：T38-F03执行记录

- 状态：`engineering_complete / production_migration_not_executed / release_not_approved`。
- schema为`2026_07_27_032 / therapeutic_assessment_evidence_ledger`，O/P/H/U均保存来源、可见范围、作者、复核状态、版本与审计。
- O/P/H/U各自具有服务端硬约束；H缺少反证、替代解释、推翻条件或人工来源时拒绝。
- AI/系统不能创建或升级H，未人工复核H不会展示给参与者。
- Web和小程序可读取对象范围内的账本，shared与机器契约同步。
- 验收：F03/F02/既有协作14项、Web类型检查和小程序语法通过；生产迁移未执行。
- 下一任务：`T38-F04`“我的问题”与问题质量量规。

## 2026-07-27：T38-F04执行记录

- 状态：`engineering_complete / production_migration_not_executed / release_not_approved`。
- schema 033新增工作问题、候选、质量量规、最好猜测、候选决定和问题版本；原始参与者问题不可覆盖。
- 候选不算确认；未修改提交不算认可。参与者可显式改写、都不符合、暂停、删除或提交。
- 小程序提供候选/都不符合/暂停操作，shared和机器API契约已同步。
- 验收：F04/F03/F02共14项、Web类型检查和小程序语法通过。
- 下一任务：`T38-F05`多方资料与动态同意。

## 2026-07-27：T38-F05执行记录

- 状态：`engineering_complete / production_migration_not_executed / release_not_approved`。
- schema 034新增逐条资料控制与动态同意版本表；主体、提供者、涉及者、控制者、查看者、用途、有效期、撤回和法定保留分开记录。
- 亲子/伴侣/涉及者关系不自动互看；专业人员逐条指定，共同反馈要求所有相关人显式approve。
- 控制表拒绝原文，只保存引用和摘要；通知、列表和未授权错误不泄露资料内容。
- 过期、撤回、法定保留、幂等重放和跨角色专项已通过；生产迁移未执行。
- 下一任务：`T38-F06`参与者八页面闭环。

## 2026-07-27：T38-F06执行记录

- 状态：`engineering_complete / production_migration_not_executed / real_device_gate_pending / release_not_approved`。
- 小程序八个独立步骤页已接入统一流程组件；一屏一个主要决定，原话与系统整理并列。
- schema 035新增参与者云端草稿和幂等事件；本机自动保存、断网保留、跨设备读取、乐观锁和撤回阻断由服务端强制。
- loading、empty、error、offline、expired、withdrawn、88rpx触控和读屏语义通过机器专项审计；真机读屏与字体放大仍是人工门禁。
- 注册表八组专项命令全部通过；生产迁移未执行。
- 下一任务：`T38-F07`适用性、安全和人工责任链。

## 2026-07-27：T38-F07执行记录

- 状态：`engineering_complete / production_migration_not_executed / external_human_gate_pending / release_not_approved`。
- schema 036新增责任链、安全事件和全局运行控制；责任链中断或开放事件超过队列时限会触发kill switch。
- 参与者只看到“需要真人了解”和本人case范围内数量；不返回低/中/高未来风险标签、其他参与者事件数或内部暂停原因。
- 普通反馈、人工复核发送和参与者训练行动均执行安全门；只有督导/管理员可凭人工证据解除事件和恢复运行。
- 按本轮工程质量约束移除未使用辅助、错误唯一索引和事务内嵌套连接；后续任务不得添加无业务价值薄封装、重复判空或未经需求验证的历史兼容。
- 机器注册表六组验收命令通过：F07/F06/F05共10项测试、迁移、API契约、小程序语法和Web类型检查。
- 未执行生产迁移、真实值守配置、人工专业签字或真机门禁。
- 下一任务：`T38-F08`研究者证据工作台。

## 2026-07-27：T38-F08研究者证据工作台执行记录

- 工程完成：schema 037新增工作台草稿、草稿事件和证据方法限制字段；Web与小程序使用同一shared契约。
- 服务端强制对象范围、敏感读取审计、筛选分页、草稿恢复、乐观锁和幂等重放；参与者响应不包含内部记录。
- 工作台以议题和证据时间线为主，人工假设同时显示支持依据、反证、其它可能和参与者识别度；内部记录与参与者可见草稿严格分区。
- 无真实证据时不能创建正式反馈草稿。代码审查未新增空壳封装、重复判空或推测性历史兼容。
- 专项测试、任务38既有回归、迁移、API契约、小程序语法、Web类型检查/构建及同视口视觉审计通过。
- 未执行CloudBase/MySQL生产迁移、微信真机、字体放大、屏幕阅读器或真实研究者签字。
- 下一任务：`T38-F09`分层反馈、书面信与用户核对。
## 2026-07-27 T38-F09 分层反馈、书面信与用户核对

- 状态：工程完成；生产发布、微信真机和人工专业门禁仍独立待批。
- 已实现：第一/第二层反馈、第三层线下门禁、书面信标题、发送账本、参与者四类核对、异议历史、修订/撤回/重发。
- 服务端硬门禁：依据非空、非诊断/非责备/非保证/非读心、接收者对象范围、动态授权资料范围、起草与复核分离。
- 前端：Web研究者工作台完成反馈编排和生命周期操作；小程序完成书面反馈展示与核对提交。
- 数据：schema `2026_07_27_038`，新增`therapeutic_assessment_feedback_deliveries`和`therapeutic_assessment_feedback_responses`。
- 验收：F05/F07/F08/F09及小程序结构共20项回归通过，机器注册表T38-F09验收10/10通过，内容、API契约、Web构建和小程序结构/语法通过。
- 冲突/注意：临时展示越权保持原状，但没有据此放开反馈写入、复核、撤回或重发权限；工程完成不代表生产批准。
- 下一步：按机器注册表执行`T38-F10`。

## 2026-07-27 T38-F10 小行动与随访

- 状态：工程完成；生产迁移、订阅提醒发布、真机和人工专业门禁未自动批准。
- 完成：结构化自选行动、三项安全确认、提醒隐私、停止条件、未完成记录、训练卡/打卡关联、状态乐观锁、行动回看和O/U随访证据回流。
- 参与者端：第八步不再只有单个文本框；行动后可选择“尝试过/中途停止/决定不做”，并记录新观察或仍待了解内容。
- 研究者端：工作台可查看行动目的、停止条件、参与者回看；不能据此生成疗效分数。
- 数据与恢复：schema `2026_07_27_039`；迁移只增不删，逻辑回滚保留历史。
- 验收：机器注册表T38-F10 12/12通过；专项13项、任务38既有44项测试通过；API契约、内容、Web类型/构建、小程序结构/语法/无障碍审计通过。
- 质量门：只保留权限、安全、幂等、迁移、并发和业务边界所需防御；未加入薄封装或臆测式历史兼容。
- 下一步：`T38-F11` T1—T3胜任力与授权。

## 2026-07-28 T38-F11 T1—T3胜任力与任务授权

- 状态：工程完成；生产迁移、真实资质审核和发布批准仍为独立门禁。
- 完成：T1/T2/T3级别、按任务授权、督导证据、对象范围、有效期、撤销、重大事件复核和完整事件账本。
- 服务端默认拒绝：账号角色或临时展示越权不能代替任务授权；停用、离岗、授权过期、撤销、重大事件和case复杂度/准备度变化都会阻断后续写操作。
- T2只允许成人单人低风险L1/L2；正式评估、反馈复核和发送要求T3。Web与小程序在授权状态不可读时同样关闭写入口。
- 数据：schema `2026_07_27_040`；授权表保存case范围快照和独立状态原因，迁移只增不删，逻辑回滚保留历史。
- 验证：F11专项7项通过；机器注册表12/12通过，包含既有相关回归、迁移、内容/API契约、Web构建和小程序审计。全量回归按风险在最终收口统一执行，不作为每个小任务的固定阻塞项。
- 质量门：授权校验属于真实权限、伦理、并发和对象范围边界；未增加空壳包装或推测性兼容层。
- 下一步：`T38-F12`专业质量保证与督导。

## 2026-07-28 T38-F12 专业质量保证、督导与修复闭环

- 状态：工程完成；生产迁移、真实督导签字、真机和发布批准仍为独立门禁。
- 完成：按L0—L3配置督导频率、抽样率、队列SLA和暂停阈值；反馈发送后确定性抽样，六维质量复核要求作者与复核者分离。
- 事件闭环：投诉、更正、撤回、通知、影响分析、独立复核与结案均写入不可覆盖的事件历史；错误案例和原始反馈保留。
- 双端：Web新增质量工作台，小程序新增参与者投诉/更正入口和研究者质量队列；shared与机器API契约同步。
- 数据：schema `2026_07_28_041`，迁移正向、验证和逻辑回滚通过；运行态支持队列超限暂停和人工恢复。
- 验证：F12专项及受影响回归40项通过；机器注册表12/12通过；API契约、内容校验、Web typecheck/build、小程序结构/语法/无障碍审计通过。
- 质量门：只保留权限、独立复核、幂等、并发、迁移和质量修复所需约束；未增加薄封装或臆测式历史兼容。
- 下一步：按机器注册表执行`T37-A01`情绪标签体系和标注手册。

## 2026-07-28 T37-A01 情绪标签体系和标注手册

- 状态：工程完成；心理与方法专家逐项审查、真实双人标注和签字仍为人工门禁。
- 完成：中文多标签本体、0—4强度、否定范围、混合情绪、`unknown`、需真人了解、安全线索分离、12个边界样例和8个反例。
- 边界：标签不等于诊断、人格、关系优劣、疗效或个体危机概率；`crisis_expression`只触发人工优先了解。
- 衔接：既有240例单标签基准继续用于工程演练，72词规则表继续标记为测试基线，不升级为人工金标准。
- 验证：机器注册表2/2通过，包含A01专项、情感计算既有回归和全内容校验。
- 下一步：`T37-A02`数据权利、双人标注与裁决。

## 2026-07-28 T37-A02 数据权利、双人标注与裁决

- 状态：工程完成；真实数据用途同意、权利、伦理、去标识核验和删除计划均未批准，保持合成数据。
- 数据：schema `2026_07_28_042`；多标签记录、裁决历史和分组切分只增不删，直接身份字段不进入标注工具。
- 独立性：双人盲标隐藏同伴答案、身份和模型预测；同一人不能跨轮次充当第二人，第三人不能裁决自己的标注。
- 切分：仅保存带项目域分隔的组哈希；未来真实数据按用户/家庭/项目组切分，当前独立合成case按case组切分，同组跨集合检测必须为零。
- 报告：标签分布、缺失、分歧矩阵、Kappa、多标签一致率、待裁决和方法限制已提供。
- 验证：机器注册表8/8、相关19项测试、迁移正向/验证/逻辑回滚、内容/API契约、Web typecheck/build通过。
- 下一步：`T37-A03`透明基线、候选模型和校准。

## 2026-07-28 T37-A03 透明基线、候选模型和校准

- 状态：工程完成；人工金标准、中文预训练模型制品与许可证据未批准，生产替换继续关闭。
- 候选：72词透明规则基线与字符TF-IDF逻辑回归可复现运行；线性候选使用三折sigmoid/Platt校准。中文预训练候选只登记，不伪造运行结果。
- 切分：固定随机种子37；修复原四模板亚组全部落入训练集的问题，改为独立合成case组哈希，训练153、验证50、测试37；迁移支持快照、验证和恢复。
- 指标：macro-F1、逐类召回、罕见线索召回、ECE、覆盖率、弃答率、混淆矩阵和亚组表现齐备；生成标签不是人工金标准，分数不是临床置信度。
- 弃答：过短、域外、冲突线索和低概率统一进入`unknown / human_review`，不直接改变参与者反馈或训练卡。
- 验证：相关24项测试、内容校验、API契约、Web typecheck/build和机器注册表5/5通过；按负责人决定未在本小任务重复全量回归。
- 下一步：`T37-A04`群体级社会网络分析。

## 2026-07-28 T37-A04 群体级社会网络分析

- 状态：工程完成；真实群体关系数据用途、边界与去标识门禁未批准，当前仅运行项目自有合成图。
- 契约：节点、边、观察窗口、缺失、三类边界和预登记研究问题已冻结；只接受分析专用代号，不接收身份、消息正文或关系标签。
- 隐私：低于12节点、每窗口10边或高于30%预期缺失时抑制；社区小于5不单独展示。
- 输出：仅群体密度、加权强度分布、分量、社区大小分布和时间变化；无节点ID、个体排名、个体标签或原始边表。
- 敏感性：`approved_cohort / observed_nodes / active_nodes`三类边界及0/10%/20%缺失扰动报告齐备。
- 边界：个体输出、敏感字段与真实数据输入服务端阻断；不是训练模型，不作因果或关系质量解释，参与者端无分析入口。
- 验证：相关18项测试、合成工件检查、内容/API契约、Web typecheck/build和机器注册表6/6通过；本小任务未重复全量回归。
- 下一步：`T37-A05`模型注册、影子执行和研究者界面。

## 2026-07-28 T37-A05 模型注册、影子执行和研究者界面

- 状态：工程完成；仅合成数据影子模式，真实参与者计算与生产发布未批准。
- schema：`2026_07_28_043`，模型版本、影子运行与复核队列不可覆盖；逻辑回滚保留历史证据。
- 注册：候选模型、词典、阈值、特征、代码commit、数据集、schema及总制品哈希全部固定；相同版本幂等。
- 漂移：模型注册、词典、阈值、特征、数据、schema或commit任一变化即停止运行。
- 执行：只读shadow不写参与者反馈、训练卡或个体决策；回放生成新记录。
- 界面：Web和小程序研究者页显示样本量、覆盖率、未知数、版本、限制与人工复核队列；不显示原文。
- 权限：正式participant无接口权限和独立入口；临时展示越权不作为正式权限验收。
- 验证：相关24项测试、迁移、内容/API契约、Web typecheck/build通过；未重复全量回归。
- 下一步：`T37-A06`漂移、公平性、异常和回滚。

## 2026-07-28 T37-A06 漂移、公平性、异常和回滚

- 状态：工程完成；仅合成漂移和异常演练，真实监测期与生产发布未开始。
- schema：`2026_07_28_044`，监测运行和运行控制版本只增不改。
- 监测：长度、标签分布、口语风格、缺失、弃答、逐组错误、人工推翻和异常率均有黄线、红线和停机动作。
- 恢复：模型/阈值回滚只允许已登记版本；只读降级和完全关闭带原因、版本与审计。
- 边界：群体误差差异不解释个体心理或关系质量；真实数据未接入。
- 解耦：模型关闭后情绪记录、规则反馈和训练卡推荐继续可用。
- 双端：Web支持受控演练，小程序研究者页只读查看当前模式和最近门禁。
- 验证：相关21项测试、迁移、内容/API契约和Web构建通过；未重复全量回归。
- 下一步：`T37-A07`情感计算发布门禁。

## 2026-07-28 T37-A07 情感计算发布门禁

- 状态：工程完成；发布仍被外部证据门禁阻断。
- schema：`2026_07_28_045`，门禁运行和外部证据哈希只增不改。
- 门禁：权利、双人标注、独立效度、弃答/人审/回滚、非诊断边界、测试云shadow和负责人批准统一进入证据包。
- 机器通过：弃答、人审、模型/阈值回滚和非诊断输出边界。
- 外部待办：权利批准、人工金标准、独立测试/本地效度、测试云连续观察、具名负责人批准。
- 红线：临时展示越权和模拟Agent签字均不计正式批准；证据包永不自动激活生产运行。
- 双端：Web可生成只读证据包，小程序研究者页只读显示状态、阻断数和边界。
- 验证：A07/A06相关9项测试、迁移、内容校验和Web typecheck通过；最终机器验收另由注册表执行。
- 下一步：`T37-B01`协作式评估生产契约桥接。

## 2026-07-28 T37-B01 协作式评估生产契约桥接

- 状态：工程完成；生产迁移、真实责任链、人工/伦理/真机和发布批准仍为独立门禁。
- schema：`2026_07_28_046`，契约快照只增不改；既有case与029以来字段继续可读，逻辑回滚不删除历史。
- 契约：L0—L3、T1—T3、O/P/H/U、五道门和服务级别/胜任力/对象权限/安全状态四个独立维度统一进入backend、shared和机器API。
- 失败关闭：来源文件哈希、枚举或默认策略漂移时返回409；未知值、对象许可缺失或责任角色缺失默认拒绝，不能跨维度替代。
- 双端：Web研究者工作台和小程序协作页均读取同一版本契约并显示边界。
- 红线：临时展示越权不改变正式授权；契约快照不等于生产批准，`production_release_approved`固定为false。
- 验证：专项及受影响回归19项、迁移正向/核验/逻辑回滚、内容校验、API契约、Web typecheck/build和小程序语法检查通过。
- 下一步：`T37-B02`人工队列、对象范围与值守基础。

## 2026-07-28 T37-B02 人工队列、对象范围与值守基础

- 状态：工程完成；真实值守人员、生产迁移、真机和发布批准仍为独立门禁。
- schema：`2026_07_28_047`，五类人工队列、事件账本、值守班次、交接事件和独立运行控制只增不改。
- 领取门：对象范围快照、胜任力任务授权、有效期、正式角色和值守班次必须同时匹配；对象漂移时失败关闭。
- 分离：起草者不能领取最终复核、风险或督导任务；没有合格接手人时不自动降级或扩大对象范围。
- 监控：待处理、超时和无人值守紧急项进入SLA监控；超阈值暂停队列领取并保留历史。
- 双端：Web工作台和小程序研究者端显示同一运行摘要；临时展示越权只影响展示，不改变正式写权限。
- 验证：专项及受影响回归21项、迁移正向/核验/逻辑回滚、内容/API契约、Web typecheck/build、小程序语法与静态/UI治理审计通过。
- 下一步：`T37-B03`五道门发布流水线。

## 2026-07-28 T37-B03 五道门发布流水线

- 状态：工程完成；生产迁移、真人复核、真机和发布批准仍为独立门禁。
- schema：`2026_07_28_048`，发布候选、逐门检查与候选事件只增不删，旧消息、报告和反馈继续可读。
- 五道门：最小输入、权限、来源、语言和责任统一在反馈、AI候选、报告与消息的服务端发送路径执行。
- 失败恢复：阻断内容保存候选、原因、差异、来源和版本；补充后按乐观锁重检，不静默丢弃。
- 严格路径：高风险、多方资料和AI候选不能走普通训练路径；临时展示越权、规则或AI均不能绕过正式写门。
- 双端：Web工作台与小程序研究者端显示同一候选摘要，不向普通参与者暴露正式候选正文。
- 验证：专项及受影响回归41项通过；迁移、内容/API契约、Web构建、小程序语法与治理审计纳入机器注册表。
- 下一步：`T37-B04`反馈生命周期、随访和恢复。

## 2026-07-28 T37-B04 反馈生命周期、随访和恢复

- 状态：工程完成；生产迁移、真实隐私删除、真机、人工责任链和发布批准仍为独立门禁。
- 生命周期：草稿、复核、发送、核对、修订、撤回、小行动、随访和归档已接入同一状态投影，保留幂等键、版本锁、交付回执和事件历史。
- 恢复：有效已发送反馈可重发并新增顺序回执；撤回同步作用于反馈和交付记录；旧版本不覆盖、不删除。
- 隐私：治疗性评估删除范围补齐所有case子表、质量/队列子事件和治疗性反馈发布候选，删除前后均可机器核验。
- 指标：流程质量、实施质量、伤害事件三个命名空间分开，明确不构成疗效、诊断或风险评分。
- 隔离：生命周期开关关闭时，目标、日记、训练卡、打卡、周报和消息核心链路继续可用。
- 双端：Web与小程序研究者端读取同一汇总；普通参与者仅可读取自己的生命周期。
- 验证：专项及受影响回归24项、迁移plan/apply/verify/rollback、API契约、Web构建、小程序语法与治理审计通过，机器注册表11/11。
- 下一步：`T37-B05`协作式评估生产门禁。

## 2026-07-28 T37-B05 协作式评估生产门禁

- 状态：工程完成；真实人工、人员、基础设施和负责人批准证据未齐，生产发布保持阻断。
- schema：`2026_07_28_049`，生产证据、门禁运行和逐门检查三张表只增不改。
- 五类门禁：工程与内容、人工证据、人员和值守、隐私与恢复、基础设施分别判定，不允许互相替代。
- 证据：提交后固定为待核验；生产环境、SHA-256和不同人员独立核验同时满足才可计入正式门禁。
- 红线：自动测试、模拟Agent、测试环境材料和临时展示越权均不计正式批准；接口不能自动批准生产发布。
- 双端：Web和小程序质量页读取同一门禁摘要；普通参与者不能查看正式证据。
- 验证：专项及受影响回归14项、迁移plan/apply/verify/rollback、内容/API契约、Web构建和小程序治理检查通过，机器注册表12/12。
- 下一步：`T37-C01` AI用例冻结。
## 2026-07-28：T37-C01执行记录

- 状态：`engineering_complete / research_synthetic_scope_frozen / release_not_approved`。
- 首批冻结5个研究者合成用例：已批准材料整理、问题版本草拟、证据缺口提示、讨论清单、格式/错别字/去标识化/术语候选检查。
- 禁止参与者自由问答、机制性H、诊断、危机结论、标准化测验解释、自动训练卡处方和自动发布；参与者入口只登记为T37-C10后续评审目标。
- 新建会话必须选择允许用例并持久化策略版本；消息不能修改会话用例，旧无范围会话默认拒绝继续执行。
- schema为`2026_07_28_050 / ai_use_case_freeze`；Web、小程序、shared和API机器契约已同步。
- 专项及受影响回归25项、迁移apply/verify/rollback、内容/API契约、Web类型检查和小程序审计通过。
- 未执行生产迁移、真实Provider、真实参与者流量、人工签字或生产发布。下一项：`T37-C02`。

## 2026-07-28：T37-C02执行记录

- 状态：`engineering_complete / external_contract_and_owner_gates_pending / release_not_approved`。
- 已建立DeepSeek/OpenAI版本化候选比较，覆盖数据区域、训练使用、保留删除、子处理商、审计、SLA、内容政策和动态价格。
- 公开网页只作为候选事实，不计作合同、DPA、PIA或负责人批准；OpenAI中国大陆数据驻留、DeepSeek明确不训练/删除/子处理商承诺均仍待书面证据。
- 新增供应商证据账本：只保存脱敏引用和SHA-256，登记为`pending`，必须由不同督导/管理员使用版本锁独立复核；不允许自动选中或自动打开真实Provider。
- Web提供候选比较和证据元数据工作台；小程序API层同步；普通参与者无权访问。所有密钥仅登记环境变量名称，不保存值。
- schema为`2026_07_28_051 / ai_provider_selection_evidence`；故障、涨价、停服和迁移均先停用，不自动切换未批准供应商。
- 专项及受影响回归31项、迁移四态、内容/API契约、Web和小程序检查通过；真实合同证据、出网、生产迁移和发布未执行。下一项：`T37-C03`。

## 2026-07-28：T37-C03执行记录

- 状态：`engineering_complete / real_provider_runtime_gates_blocked / release_not_approved`。
- 已实现DeepSeek/OpenAI服务端适配器；客户端不能选择供应商，真实调用必须同时通过服务端开关、C02合同证据、供应商选择和固定HTTPS出网门禁。
- 密钥只在调用时从CloudBase Secret或服务端环境变量读取；无密钥、无模型、未批准主机或响应异常均安全失败，密钥不进入Git、前端、数据库、响应或日志。
- 同步HTTPS传输分别执行连接、读取和总超时；取消或超时立即关闭当前连接，不创建后台供应商线程，超时后不继续重试。
- schema为`2026_07_28_052 / ai_provider_runtime_metadata`；只追加request id、模型、输入/输出token、成本币种和错误元数据，不保存请求/回答原文。
- Web显示服务端选择、适配器和三类超时；shared与公开配置契约同步，小程序继续只能读取状态，不能提交供应商。
- 专项及受影响回归、迁移四态、API契约、Web和小程序检查均通过；真实密钥、合同门禁、出网、生产迁移和发布未执行。下一项：`T37-C04`。

## 2026-07-28｜T37-C04批准知识库和RAG执行记录

- 状态：`engineering_complete / production_migration_not_executed / release_not_approved`。
- schema升级为`2026_07_28_053 / approved_knowledge_rag`，新增版本化文档、字段级切片、网页隔离候选和检索评测四张表；迁移为加法迁移，回滚不删除数据。
- 索引准入同时要求：内容类型允许、权利明确、来源与来源版本存在、研究/心理/伦理/内容四类审核通过、版本已发布、发布记录活跃且未过期。
- 已实现BM25、本地确定性向量基线、混合检索与重排；引用包含文档/发布/切片版本、字段位置、来源、权利、审核、有效期、适用人群和分项分数。
- 每次检索前同步发布状态；暂停、撤回、替换或过期内容立即不可检索。无足够证据时返回`evidence_status=insufficient`，不进入生成回答。
- 公开网页只能登记HTTPS URL、标题和SHA-256元数据，固定进入`quarantined`；接口拒绝正文、HTML和原始文本字段，不允许自动批准或索引。
- Web研究沙盒增加索引状态、BM25/向量/混合检索比较和引用定位；shared、Web API和小程序API契约保持一致。
- T37-C04专项6项、AI/内容治理受影响36项、health/MySQL 23项通过；迁移plan/apply/verify/rollback、Web typecheck和小程序语法检查通过。
- 生产数据库迁移、知识内容人工发布批准和真实Provider调用均未执行。下一项：`T37-C05`。

## 2026-07-28｜T37-C05输入安全、隐私最小化和提示注入防护执行记录

- 状态：`engineering_complete / production_provider_not_enabled / release_not_approved`。
- 消息字段改为服务端白名单；客户端不能注入系统指令、对象范围、供应商或工具控制字段。
- 手机号、邮箱、证件号、IP和微信号在持久化、检索和模型调用前去标识；原始输入不进入会话、供应商事件或安全事件。
- 系统指令、用户数据和不可信检索片段完成明确分区；模型请求再次校验发布、权利、审核、版本、来源与角色适用范围。
- 工具默认拒绝，仅保留服务端只读`knowledge.retrieve`，并限制参数schema、数量、路径、身份和网络边界。
- 红队集补齐提示注入、权限提升、跨会话记忆、数据外带和工具滥用；专项6项及AI受影响56项通过，Web构建、内容校验、小程序审计和API契约检查通过。
- 数据库复用现有安全事件和审计表，schema保持053；真实Provider、生产流量和发布批准未执行。下一项：`T37-C06`。

## 2026-07-28｜T37-C06输出五道门和结构化契约执行记录

- 状态：`engineering_complete / human_verification_and_release_gated / release_not_approved`。
- 输出固定为`safehome.ai-qa-output.v1`，由Pydantic和JSON Schema双重校验；额外字段、空值、无效枚举和无效JSON均失败关闭。
- 最小输入、权限、来源、语言和责任五道门全部由服务端执行；引用必须与本次批准来源一致，诊断、保证、责备、个体风险结论和定性结论均被阻断。
- 不合格输出只走固定安全降级，不自动修补、不递归调用Provider；人工核对标记不可由模型关闭。
- Grounding保留词面重叠启发式，并明确`grounding_is_factuality_check=false`，不能作为事实正确性证明。
- shared与Web沙盒公开非敏感契约状态；小程序继续复用统一配置接口。专项及AI受影响回归68项、内容/API契约、Web typecheck/build和小程序审计通过。
- 数据库复用schema 053；真实Provider、真人复核、生产迁移和发布批准未执行。下一项：`T37-C07`。

## 2026-07-28｜T37-C07人工审阅工作台执行记录

- 状态：`engineering_complete / human_qualification_and_release_gated / release_not_approved`。
- schema升级为`2026_07_28_054 / ai_review_workbench`，新增审阅案例与审阅动作表；迁移支持plan/apply/verify/rollback，回滚保留数据并关闭路由。
- AI合格候选只进入内部待审阅案例，不再自动标记发布，也不写入参与者正式反馈；审阅支持采纳、修改、拒绝和无匹配四种决定。
- 审阅案例同时保留来源、候选、五道门结果、修改差异、最终版本、发布主体、对象范围和授权快照；写操作具备版本锁、幂等和完整审计。
- 普通低风险案例要求T2授权；高风险、未成年人/家庭、多方资料和机制解释要求对应T3对象范围授权；起草者不能复核自己的候选。
- 会话删除和保留期清理会同步删除审阅正文，并撤回关联发布候选；不保留参与者正式反馈副本。
- Web研究沙盒已加入同屏审阅工作台；shared、Web API和小程序API契约同步，小程序未增加参与者审阅入口。
- 机器注册表11/11通过，其中后端专项及受影响回归91项通过；内容、API契约、小程序审计、Web typecheck/build及迁移四态全部通过。
- 生产数据库迁移、真实人员资质授权、真人复核和生产发布未执行。下一项：`T37-C08`。

## 2026-07-28｜T37-C08评测、红队和持续质量执行记录

- 状态：`engineering_complete / synthetic_quality_only / release_not_approved`。
- 固定合成评测集已覆盖正确引用、证据不足、诊断诱导、危机、虐待、未成年人、伴侣、多方隐私、提示注入和权限提升；明确不含真实参与者文本。
- 指标已补齐拒答正确率、引用支持率、越界漏拦率、人工修改率、成本、P95延迟和失败恢复率，并保留路由准确率、关键失败和诊断违规指标。
- 安全关键漏拦固定返回`release_blocked_critical_failure`，不能因总体平均分达标而放行；工程阈值通过不产生真人批准。
- 模型适配器、提示词、知识库、规则和评测集均生成分组SHA-256与总指纹；GitHub push/PR自动运行C08专项回归。
- Web研究沙盒显示七类持续质量指标和发布阻断边界；shared类型同步，小程序参与者入口未新增。
- 机器注册表5/5通过，其中专项及受影响回归67项、内容/API契约、Web typecheck/build全部通过。
- 真实Provider评测、真实参与者文本、生产流量和发布批准未执行。下一项：`T37-C09`。

### 2026-07-29执行记录：T37-C09预算、限流、熔断、降级和删除

- 状态：工程完成，发布门禁保持关闭；机器注册表10/10通过。
- 后端按用户、角色、供应商、项目四个范围执行预算和限流；限流统计覆盖已接受的用户请求，不因固定降级绕过。
- 新增持久化Provider熔断状态，支持关闭、打开、单探针半开和成功复位；并发探针由版本锁控制。
- Provider不可用时只返回只读固定安全说明，禁止写工具，并明确消息、记录和人工反馈核心服务不受影响。
- 会话原文、去标识衍生结果、供应商/安全元数据和审计日志使用独立保留期限；清理接口不自动删除审计。
- schema升级为`2026_07_28_055 / ai_runtime_controls`；迁移plan/apply/verify/rollback均通过，回滚保留证据。
- 验证：82项专项及受影响回归、内容校验、API契约、小程序服务语法、Web typecheck/build全部通过。
- 未执行：生产数据库迁移、真实Provider流量、生产删除、真实人员发布批准。下一项：`T37-C10`。

### 2026-07-29执行记录：T37-C10 AI分阶段发布

- 状态：工程完成，当前阶段保持`local_fake`；机器注册表10/10通过。
- 建立六阶段顺序：本地fake、合成数据真实供应商、测试云shadow、研究者只读建议、研究者可编辑候选、受限参与者评估。
- 晋级必须相邻、通过服务端门禁、提供幂等键并匹配乐观版本；模拟Agent不计签字，参与者阶段不能由本接口自动批准。
- 无来源、越权、错误发布、供应商治理违约或kill switch不可用时可立即回退；回退同步启用AI kill switch，消息、记录和人工反馈不受影响。
- 证据包保存策略/运行/质量/供应商治理制品哈希和阻断项，不保存密钥或参与者原文，不形成生产批准。
- schema升级为`2026_07_29_056 / ai_staged_release`；迁移plan/apply/verify/rollback通过。
- 验证：115项专项及受影响回归、内容校验、API契约、安全/运营注册表、小程序语法、Web typecheck/build全部通过。
- 未执行：真实Provider、测试云shadow、真人签字、任务38外部门禁、生产迁移和正式发布。下一项：`T38-F13`。

### 2026-07-29 T38-F13执行结果

- 状态：工程完成；外部真人、伦理、基础设施、真机与生产发布未批准。
- 完成：低风险成人L1/L2首发政策、可追溯筛查、对象权限、幂等与版本锁、撤回终态、审计、加法迁移/验证/逻辑回滚、shared/Web/小程序契约。
- 边界：只把成年人、自愿、单人、非紧急议题登记为工程候选；未知值进入真人复核，未成年人、多方、紧急和安全信号不进入本批首发。AIS/FIS、第三层、高唤起和家庭对峙任务保持排除。
- 发布：`production_release_approved=false`；临时展示越权不计入发布或写权限验收。下一项：`T38-F14`。

### 2026-07-29 T38-F14执行结果

- 状态：工程完成；未成年人/亲子入口保持关闭。
- 完成：监护人同意与儿童知情/拒绝分离、儿童拒绝优先、四类来源隔离、T3/伦理/A0—A3门禁、对象权限、审计、加法迁移/回滚和双端契约。
- 边界：儿童个别资料不因家庭绑定自动进入共同反馈；家长作为合作伙伴，不被写成自动病因。
- 发布：模拟角色和自动测试不能替代外部签字；真机、CloudBase/MySQL及生产发布未执行。下一项：`T38-F15`。

### 2026-07-29 T38-F15执行结果

- 状态：工程完成；伴侣与多人入口保持关闭。
- 完成：逐人同意/撤回、六类安全预检、个别披露隔离、对象范围、T3/伦理/专项试点门禁、审计、迁移/回滚和双端契约。
- 安全：任一恐惧、控制、暴力、报复、监护争议或共享设备信号转单独支持；其他参与方只看到聚合状态。
- 发布：共同反馈须全员同意且所有门禁齐全；仍不构成生产批准。下一项：`T38-F16`。

### 2026-07-29 T38-F16执行结果

- 状态：工程完成；AI仅作为可拒绝、可修改的内部整理候选，不拥有发布权。
- 完成：独立候选表、五道服务端门禁、低风险/对象范围限制、真人专属任务阻断、原话与候选并列、人工修改/拒绝/无匹配、幂等/版本/审计、迁移/回滚及双端契约。
- 安全：AI不能生成H、解释测验、处理未成年人/伴侣/创伤/暴力/自伤、决定适用性或转介，也不能解除安全信号、创建正式反馈或标记真人复核。
- 发布：当前仅为确定性候选脚手架；真实Provider、真人资质、生产迁移与发布批准未执行。下一项：`T38-F17`。

### 2026-07-29 T38-F17执行结果

- 状态：工程完成；方法内容仍需四专业真人复核和正式发布。
- 完成：9项受控方法内容、来源/版本/适用级别/审核者/有效期/禁用场景元数据、公开摘要目录、专业详情权限、审计、内容治理复用及迁移/回滚演练。
- 安全：AIS/FIS仅为T3专业材料，不进入普通推荐；参与者目录不返回正文或来源，研究者不能读取AIS/FIS正文。
- 双端：shared、Web研究者工作台与小程序说明页使用同一目录契约；未新增参与者专业材料入口。
- 验收：专项7项、内容/API契约、小程序语法、Web typecheck/build和迁移四态通过；真人审核、正式内容发布和生产迁移未执行。下一项：`T38-F18`。

### 2026-07-29 T38-F18执行结果

- 状态：工程完成；研究协议已冻结为工程版本，真实研究与生产发布未批准。
- 完成：过程6项、实施7项、伤害6项的分母/时间点/缺失/分析方法预定义，症状量表仅作探索性结局，严重伤害独立报告。
- 导出：仅正式研究角色、用途白名单、研究者对象范围、HMAC化case键、最小必要字段和完整审计；不含参与者ID、原始问题或自由文本。
- 验收：专项及关联回归13项、内容/API契约、小程序语法、Web typecheck/build和迁移四态通过。下一项：`T38-F19`。

### 2026-07-29 T38-F19执行结果

- 五类A0专家走查问题、证据索引和真人签字字段已生成；证据包带SHA-256并写审计。
- 模拟角色、Agent和自动测试不计专家结论或签字；真实专家复核仍待人工完成。
- 工程专项、内容/API契约、双端检查和迁移四态通过。下一项：`T38-F20`。

### 2026-07-29 T38-F20执行结果

- A1逐屏三问、七类理解风险、屏幕清单和访谈记录字段已完成；严重理解问题阻断A2。
- 合成访谈和可用性测试不计真人访谈或疗效证据。真实访谈未执行。下一项：`T38-F21`。

### 2026-07-29 T38-F21执行结果

- A2五步顺序、成人/单人/低风险/自愿范围、逐例证据、每例督导和严重问题阻断已完成。
- 系统不自动生成H或发布反馈；合成案例、专家角色演练和自动测试不计真人证据。
- 真实低风险成人原型、真人逐例督导和问题关闭未执行。下一项：`T38-F22`。

### 2026-07-29 T38-F22执行结果

- A3七类验证矩阵、运行证据字段和开发者工具/iOS/Android真机矩阵已完成。
- A0—A2真人证据和严重问题关闭是进入条件；自动测试与合成结果不计真人签字。
- 受影响回归28项、内容校验和迁移四态通过；测试云真机试点未执行。下一项：`T38-F23`。

### 2026-07-29 T38-F23执行结果

- A4八类安全实施指标、五类停止原因和分析证据字段已完成。
- 禁止疗效、治疗效应或症状变化声明；严重问题阻断发布。
- 回归12项、内容校验和迁移四态通过；真实可行性试点未执行。下一项：`T37-R01`。

### 2026-07-29 T37-R01执行结果

- 测试云health/ready、worker、监控、合成回放、网络故障和只读回退证据编排已完成。
- 本地回归32项和脚本演练通过，但不计隔离测试云实际部署或真机证据。
- 未触碰生产，未自动晋级。下一项：`T37-R02`。

### 2026-07-29 T37-R02执行结果

- 当前schema 060的迁移、备份、恢复、校验和、行数、隐私墓碑和非破坏回滚证据已完成隔离演练。
- 修复儿童保护表两个人员ID的MySQL可索引VARCHAR映射，MySQL 5.7契约恢复通过。
- 生产命令仅生成，未连接生产或执行迁移。下一项：`T37-R03`。

### 2026-07-29 T37-R03执行结果

- 1%→5%→10% canary、影子对比、负荷阈值和八类事件演练已完成合成编排。
- 40项回归通过，并修复旧隐私测试固定schema 038造成的误报。
- 真实流量、真人责任人和发布批准未执行。下一项：`T37-R04`。

### 2026-07-29 T37-R04执行结果

- 12类发布产物指纹、集合哈希、七部分发布说明、四阶段观察窗口、十项指标、九项回滚阈值和六步回滚动作已冻结。
- 后端174个测试文件分四组全覆盖，共917项；修复旧schema/私有实现断言和来源注册表受外部目录新增文件污染的问题后，全部通过或完成定向复核。
- 内容、API合同、136项兼容回放、小程序51页/67组件引用审计、Web typecheck/build和R04四种动作通过。
- 负责人批准、真实canary、真人责任人、生产发布与72小时发布后观察未执行，工程完成与发布批准继续分开。下一项：`T38-F24`。

### 2026-07-29 T38-F24执行结果

- 七类立即暂停、七项真人恢复证据、八层回滚、失败关闭、独立核验、幂等/版本锁和双端统一状态已实现。
- schema升级为`2026_07_29_061 / therapeutic_assessment_stop_recovery`；加法迁移四态通过，未执行生产迁移或生产恢复。
- 专项及关联回归66项、内容治理、API合同与136项兼容回放、小程序审计、Web typecheck/build通过。
- 真人恢复批准、生产迁移和生产恢复未执行；临时展示越权、模拟Agent和自动测试均不计恢复证据。下一项：`T38-F25`。

### 2026-07-29 T38-F25执行结果

- 状态：任务37/38工程任务57/57完成；生产发布未批准。
- 完成：十类自动验收、脱敏回执、产物哈希、六类外部门禁清单、证据生成/核验/回滚和CloudBase交付包参数化。
- 全量回归：后端175个测试文件共931项通过；schema 061隔离迁移四态通过。
- 双端与合同：内容、安全407项、运营、108项资料源、4类API产物、136项兼容回放、小程序51页/67组件/76个JS、Web typecheck/build通过。
- 可访问性：375/430/768/1440四视口，100%/200%字体、无横向溢出、44px触控、可访问名称和键盘焦点通过。
- 待外部完成：A0—A4真人证据、T1—T3资质督导、伦理法律隐私安全、CloudBase/MySQL生产迁移恢复、微信真机和生产负责人批准。
- 边界：没有生产迁移、生产恢复、真实Provider晋级或自动签字；临时展示越权未作为正式权限证据。

### 2026-07-29 T38-F25审查加固

- 最终验收改为由服务端工具实际执行注册命令；不再接受调用方自行填写的`passed`回执。命令只记录返回码、命令摘要及输出哈希。
- 机器注册表版本更新为`2026-07-29-f25-hardening-v2`，F25直接调用可信`verify`。
- CloudBase正式包改从`git archive HEAD`构建，并核对commit、source tree和build fingerprint，未提交源码不会冒充HEAD进入包。
- 自动视觉证据只声明公共组件四视口渲染与12个实际页面源码检查；实际整页大字体、读屏、微信开发者工具和真机继续保持外部门禁。
- 主计划状态已收口为`engineering_complete_local / T38-F25_acceptance_hardened / release_not_approved`。
### 2026-07-29 T38-F25审查问题修复与冗余核验

- [x] F25验收拒绝脏工作区，并绑定实际源码commit与Git tree。
- [x] CloudBase编译检查改为暂存包内源码。
- [x] ZIP允许范围逐文件与记录提交的Git归档比较，篡改测试失败关闭。
- [x] 画像位置回填重复实现收拢并补测试。
- [x] 8个完全相同的Flask角色认证helper收拢；5个无调用符号删除。
- [x] 核验测试初始化、Web展示helper、响应helper和生成契约；对非等价或外部用途未明部分保守保留。
- [x] 定向回归161项及CloudBase正常包构建/核验通过。
- 工程状态：完成；生产发布状态：未批准。本轮没有生产迁移、生产恢复、真实流量或权限放开。

## 2026-07-30：任务十三至三十六生产缺口整改、P1/P2与上线准备

### 执行范围

- 按用户要求处理任务十三至三十六审查中可自动完成的代码、shared、小程序、Web、内容、权限、审计、恢复和文档缺口。
- 明确排除CloudBase生产迁移/恢复/发布；临时展示越权继续保留，但不计正式权限验收。
- “生产开关打开”按工程可操作口径实现，不伪造平台、伦理、真机、负责人或生产环境批准。

### 已完成

- [x] 新增`PRODUCTION_FEATURES_UNLOCKED`，使AI、可靠性和运营发布开关可被显式启用；生产AI禁止fake供应商。
- [x] 新增`config/production_features.enabled.example.env`无密钥启用模板；外部训练、模型替换和研究结果分析继续独立关闭。
- [x] 小程序`urlCheck=true`，避免正式构建继续沿用开发期跳过域名校验。
- [x] 隐私政策和知情同意升级为2026.07 v2；新增`ai_assistance`与`relationship_analysis`独立同意类型。
- [x] P1/P2参与者支持性问答闭环：后端运行门、独立同意、本人会话、去标识、RAG引用、删除/评价、shared契约和小程序支持性问答页。
- [x] Task35新增冻结协议、基线哈希、F00—F15机器注册表和可恢复执行器；未批准数据未下载，真人金标准和生产替换仍受阻。
- [x] Web外部访问新增`start-local`本地同源代理；状态明确`public_access_started=false`，公网Tunnel仍需人工门禁。
- [x] `docs/README.md`建立保守文档导航；未移动、删除或合并权威文档。
- [x] 生成桌面《微信小程序正式上线完整审核与实施报告_20260730.docx》，覆盖备案、类目、隐私、上传、审核、发布、真机、回滚和责任清单。
- [x] 审查《阶段性工作总结0730》，综合完成度86%；任务35状态、931项历史基线和7月30日新增整改需局部校正。

### 自动验收

- 后端专项：29 passed。
- Task35执行器：`verify=passed`，16个工程任务已登记，未启动外部下载、人工签字或生产替换。
- 内容校验、API合同4项和136项兼容回放通过。
- Web TypeScript检查和生产构建通过；小程序新增/受影响JS语法检查通过。
- 上线Word结构、标题、表格、超链接与无障碍审计通过，0项问题；本机LibreOffice和Word COM分页转换均卡住，未把逐页视觉检查虚报为通过。

### 当前未完成

- CloudBase生产部署、MySQL迁移/恢复、微信真机和平台发布按用户要求本轮不执行。
- 备案、服务类目/资质、微信隐私指引和平台审核仍需真实平台证据。
- 临时展示越权仍存在，正式发布前必须关闭并重跑角色/对象范围矩阵。
- 真实AI供应商合同/DPA/数据区域/Secret/成本和人工责任链仍需独立批准。
- 公网内网穿透尚未启动；当前只完成loopback同源代理工程。

## 2026-08-01：量表结果页维度可视化优化

### 实现口径

- [x] 保留现有量表计分、数据库字段和API结构，只在小程序结果页增加可复用的维度量尺换算。
- [x] 3—8个且均可核定题目量尺范围的维度，展示“本次填写—量尺中点”双层雷达图。
- [x] 每个维度继续展示原始得分、自身量尺范围、量尺位置和文字说明，避免只看图造成误解。
- [x] 超过8个维度或量尺范围缺失时自动降级为维度卡片，不强行绘图。
- [x] 明确“量尺中点不是常模、目标值或好坏标准”，未引入诊断标签和示例图中的人格化术语。

### 验证

- Node语法检查通过；新增/布局6项专项及量表接口、开放规则等关联回归共37项通过。
- `git diff --check`通过。
- 微信开发者工具已启动，但本机自动化端口9420未成功开放；未把自动化真机/整页视觉检查登记为通过。

# 0810 Bug 修改计划：PR #8 至 Release Candidate

登记日期：2026-08-10

状态：planned_not_started / baseline_audited / implementation_not_started

权威详细计划：docs/01_当前执行入口/0810bug修改计划.md

## 冻结决策

- development/validation 继续保留联调页、研究工作台、受控 AI 与临时全权限展示。
- production Release Candidate 在构建制品、页面清单、运行配置和服务端授权四层强制关闭 Showcase、内部页面和未批准能力。
- production 参与者 AI 首发关闭；研究、情感计算、网络分析和治理能力保留在验证环境及独立后台制品，不删除源码。
- 工程、RC、微信审核和生产发布分开记录。

## 执行范围

- RC0810-F00—F12：基线/Harness、制品边界、正式镜像、环境、Showcase、对象权限、Consent、Logout、幂等、CI、正式数据库和微信证据框架。
- RC0810-F13—F21：家庭绑定、隐私血缘、主动风险调度、MySQL TLS/恢复、内容发布、研究来源、AI治理、心理内容、健康与运维。
- RC0810-F22—F24：安全工具、Fuzz/Mutation、配置/审计/遗留质量项。
- RC0810-F25—F26：微信与真机矩阵、最终RC收口。

## 强制 Loop 与 Harness

每个 Fxx 必须执行：Preflight → Scope Freeze → Failing Contract → 最小实现 → 专项/跨层验证 → 先回填详细计划 → 独立审查 → 修复 Loop → 复审通过 → 独立提交 → 推送 → 三份事实文档增量同步。

审查不通过不得提交或进入下一任务；同一根因连续五轮失败时登记 root_cause_unresolved，不得删除测试、放宽权限或伪造证据。人工、伦理、真机和微信平台只生成证据包，不能自动签字。

## 当前执行入口

本轮仅完成详细计划登记，没有修改业务代码。下一步只执行 RC0810-F00，先建立机器注册表和可恢复 Harness，不得跳到业务修复。

## 2026-08-10细化补充

- 详细计划已为 F00—F26 增加二级可执行工单，覆盖阻塞关系、输入、逐层动作、负向测试、证据产物和回滚点。
- 执行器不得只关闭父任务；每个 `Fxx.n` 都要保存状态和证据，缺任一子任务时父任务保持 incomplete。
- 任务边界、执行顺序和“开发保留、正式关闭”决策没有变化，下一步仍只能执行 RC0810-F00。
- 2026-08-10再次补充8项横向门禁：旧版本兼容、跨层合同、迁移、性能、UI/无障碍、证据有效期、发布演练和Change Budget；二级工单现为194项。

## 2026-08-10第一性原理与上线报告校准补充

- 执行顺序已调整：F00后先运行CI、证据模型、数据血缘、安全扫描和微信平台约束的A阶段，再进入业务整改；最终由B阶段对真实RC复验。
- 新增四类GO、发布人群清单、控制面/业务面分离、可信构建来源、不可逆副作用对账、成本/配额和人工处理容量要求。
- 参考上线报告只作为检查框架；历史commit、urlCheck概括、无定位完成结论和时效性链接不得直接成为RC证据。
- 二级工单现为225项、横向门禁11项、编号无重复；工程仍为planned_not_started，下一步仍只执行RC0810-F00。

## 2026-08-10 RC0810-F00 完成记录

- `RC0810-F00` 的 F00.1—F00.10 已完成并通过独立审查；本轮没有进入 F01 或业务修复。
- 新增 `content/rc0810_release_candidate_registry.json`、`scripts/run_rc0810.py`、专项测试和命令夹具。注册表覆盖 27 个父任务、225 个二级工单和 32 个分阶段执行单元。
- Harness 已绑定 commit、HEAD tree、脏源码树、dirty diff、命令证据、change budget、递归失效、断点恢复、独立审查判定和受信 artifact profile；脏工作区不能冒充 HEAD 验收。
- 独立审查经过 2 次 Fix Loop 后通过；最终独立复验为 `6 passed in 120.94s`，判定证据 SHA-256 为 `21508f595d41cc9512e31fe89777807bc6a3b234fba8d945041a71c31acec862`。
- F00 不构成 production 发布批准；下一执行单元是 `RC0810-F10-A`，需在新任务中启动，本线程停止于 F00。

## 2026-08-10 RC0810-F10-A 执行记录（待独立审查）

- 已冻结当前 main Actions run `31325141640`：`9 failed, 988 passed, 1 warning`，后续 11 个步骤因单 job fail-fast 跳过；该结果只能作为失败基线，`release_gate_eligible=false`。
- 9 个失败已分为真实缺陷 5、合同漂移 3、快照漂移 1；F10-A 未改旧测试、workflow 或业务代码，F10.2—F10.7、F10.9 仍 pending。
- 新增机器可读失败基线、离线验证器和 F10 专项测试；Harness 只激活 `F10.1/F10.8`，并显式隔离并行 UI overlay。
- 专项测试 `5 passed`，F00+F10 Harness Fix Loop 回归 `11 passed in 133.85s`；最终 Harness 验收需在本次回填后重跑，随后等待真实独立审查，不得自签 pass。
- 独立审查通过并提交/推送后，下一入口才是 `RC0810-F12-A`；本轮不得自动进入。

### F10-A 独立审查 Fix Loop 2

- 独立 reviewer 判定 `fix_required`，decision evidence SHA-256 为 `5044fe9e28b63319447e6030711f3f7923d073d08ef979fef168a1e1912deba8`；未把该结论冒充 pass。
- 已仅修四项 finding：decision 阶段拒绝 packet 后源码/dirty diff/registry 漂移；冻结原始 Actions run/job/failed-log 证据并离线复算；统一 12 文件 change budget；直接覆盖 F10.1/F10.8 分阶段验收状态。
- 验证：F10 专项 `6 passed in 3.92s`；Harness 生命周期 `1 passed in 131.09s`；完整 F00+F10 回归 `12 passed in 173.84s`；离线基线、Python 编译和 `git diff --check` 通过。最终 Harness 证据和独立复审仍待执行。
- 当前仍不是 Release GO，不提交、不推送；独立复审通过后停止于 F10-A，下一入口才是 `RC0810-F12-A`。
- 第二次独立复审仍为 `fix_required`（decision SHA-256=`2155492ef0e2661309423c5633764633bb313b38842b1151afcca5c8a45568f2`）：完整失败日志违反运行态保存规则。已将完整 gzip 日志移至 `.codex_tmp/rc0810`，tracked 只保留脱敏结构化证据和 hash；离线验证为 `runtime_log_verified=true`，F10 专项 `7 passed in 3.20s`，完整 F00+F10 `13 passed in 167.95s`，待再次独立复审。
- 第三次独立复审仍为 `fix_required`（decision SHA-256=`64ff922cafd71979ff08b1a5bd8d4833a9f15f2d9a21aba8e73eb0c6941c257e`）：只剩 clean checkout 测试强制 runtime gzip 存在。已改为同时验收“本地存在则复算=true”和“干净 checkout 缺失=false/NO-GO”，F10 专项 `7 passed in 8.75s`，完整 F00+F10 `13 passed in 218.22s`，待再次独立复审。
- 第四次独立复审已 `pass`、无剩余 finding，decision SHA-256=`d7fb698d96b7233f60ae8300a7f8189c0c460308064758d7de6fd1de80e380c5`；独立复验 F10 `7 passed in 4.09s`、F00+F10 `13 passed in 167.66s`。本条属于通过后事实同步，需重建最终 packet 做一致性复审；最终通过后提交推送并停止于 F10-A。

## 2026-08-10 RC0810-F12-A 微信外部证据定义合同

- 本轮只完成 F12-A：冻结 E01—E10、六类场景、iOS/Android 设备槽位、四级证据状态、有效期、递归失效、制品/request_id/账户角色/时间线及 detached attestation 合同；未进入 F12-B 或业务修复。
- F12-A 信任身份表保持空且为 `pending_external`，自动化与本地自报不能产生人工或平台批准；`release_gate_eligible=false`，正式上线仍为 NO-GO。
- 独立审查经过两次 Fix Loop 后第三轮 `pass`，decision SHA-256=`c8a64dd1b3682209a6f1448416053c55cbfb453dd76707da1415c227089565a5`；复验 F12 `30 passed`、F00+F12 `37 passed`，定义校验、自检与 diff check 通过。
- 本条同步后须重跑 Harness 并做最终文档一致性复审；通过后仅提交 F12-A 的 12 个允许文件并推送。下一入口为 `RC0810-F14-A`，本轮不自动开始。
- 文档同步触发重验时修复了 Harness 过度失效：源码变化现在只把最新检查点及后继置 stale，已通过的历史依赖可恢复；注册表整体变化仍递归阻断。定向回归 `1 passed`，最终 Harness 验收需在本条后重新绑定。

## 2026-08-10 RC0810-F14-A 数据血缘基线（独立复审通过，待最终文档复审）

- 已从模型、迁移脚本、`schema_migration_service.py`、routes 和 services 冻结 168 张表、字段/访问路径和 7 个接口级外部端点/动态客户端的机器基线；所有源组均有 SHA-256 manifest。
- 168 个资产、7 个处理端点和 privacy owner 共 176 个确认缺口全部显式保留，自动化没有填写人工结论；`release_gate_eligible=false`。
- 新增/遗漏表、源漂移、目录篡改、处理方遗漏、重复资产和敏感值进入 catalog 均 fail-closed；专项 12 项、Harness 演进回归 1 项通过。
- 首轮独立审查为 `fix_required`：修复遗漏 5 表、同 host 接口合并及 start 后全局注册表合同绕过；decision SHA-256=`38a61a9621d5530e0f3b3e5d292901d190bb9957142898d9161ffab65fc965d2`。
- Fix Loop 1 独立复审 `pass`，decision SHA-256=`689614a98ceb0ac8c8fb50437158ed93ebbdfc34b089f0470419210e31116010`；独立复验 F14 `12 passed`、组合 `19 passed`、default/self-check/diff check 通过。
- 本轮没有业务、数据库、迁移、删除、CloudBase、Secret 或生产操作。当前文档同步后须重验并做最终文档一致性复审；通过后下一入口是 `RC0810-F22-A`。

## 2026-08-10 RC0810-F22-A 安全扫描基线（待独立审查）

- [x] 冻结 14 文件范围与启动 commit/source tree/dirty diff/任务合同；未修改业务、数据库、迁移、CloudBase、Secret 或 production 配置。
- [x] 建立固定版本工具、固定 Action commit、安全策略/例外 schema、隔离扫描器、脱敏机器基线、运行态报告复算和 12 项负向合同。
- [x] Fix Loop 2 后真实扫描：Secret 候选 254、SAST high 3/medium 160/low 5751、Python 与 Node 已知漏洞 0；候选未人工甄别，不等同于已确认泄露。
- [x] 完整报告只在 `.codex_tmp/rc0810/security`；tracked 文件不保存 Secret 内容或完整扫描日志。
- [ ] 容器镜像、最终 SBOM、隔离许可证和供应链 attestation 留待 F22-B；当前 open gate 257，`production_gate_eligible=false`。
- [ ] 文档回填后必须重扫、执行 Harness 5 条验收并由子智能体独立审查；未通过前不得提交或进入 F25-A。
- 独立审查 iteration 1 为 `fix_required`（SHA-256=`ea4239b0521d06fae2fced69dc0c8c31756fe6c78d43169298b7897ba8fd1b9b`）；已补 `analysis/`/两份 requirements、raw report 严格合同、禁止 owner 自审和三类真实负向扫描。修复后 F22 `12 passed`、运行态/自检通过，待重建最终证据复审。
- Fix Loop 1 复审仍 `fix_required`（SHA-256=`a383c45e611dbb9c4ea932c42a827dce37ad5aabdb3ed4bc404572766cb1b03d`）；Fix Loop 2 已拒绝尾随 JSON，并建立 257 条哈希 finding 索引与空的 trusted reviewer 表。运行态、8 项自检和 F22 `12 passed`，待最终重验复审。
- Fix Loop 2 独立复审 `pass`、无剩余 finding（SHA-256=`7d1f0a9cb8870618d33f654984afa13ffc52b2f554b3710f9664c3b51fce2faa`）；F22 `12 passed`、组合 `19 passed`、8 项自检、运行态和 diff check 通过。Harness 已接受 pass，但最终文档同步后仍需一致性复审。
- F22-A 只进入 `phase_a_verified`；257 条 finding、空 trusted reviewer 表和 F22-B 四项制品/供应链门禁继续 NO-GO。最终复审、提交、推送成功后下一入口为 `RC0810-F25-A`。

## 2026-08-10 RC0810-F25-A 微信平台约束基线（待独立审查）

- 本轮只建立 F25.1—F25.14 的定义合同：平台核对、账号/消息、DevTools、iOS/Android、旅程、送审材料、证据失效、能力映射、零背景审查、冻结窗口、RACI 和真实世界证据。
- 8 项平台核对、2 个设备槽位、8 个责任域与 4 类真实世界证据均为 pending/unassigned；52 个注册页面已逐项分类，8 项核心能力/9 个页面已映射但仍缺类目/资质/隐私绑定，其余 43 页为 blocker，`production_gate_eligible=false`。
- 未填写 AppID、Secret、人员、测试账号、包/镜像 hash 或平台结论，未修改业务、数据库、CloudBase 或生产配置。
- F25 专项 `16 passed in 24.92s`，三类篡改自检通过；计划回填后仍须重建基线、运行 Harness 5 条验收并接受独立审查。通过前不得进入 F01。
- 首轮独立审查 `fix_required`（SHA-256=`08b8bbf324713a0d8eb6e13a996e3f3ee31edaeafd21909a6b5b5537be2497f3`）；已按两项 blocker 完成 Fix Loop 1：源码推导 52 页 inventory/真实 API 校验，以及 strict schema、完整失效目标/零背景结果/发布标志和先验后原子写入。修复后 F25 `19 passed`、8 项 self-check 通过，待重建 Harness packet 复审。
- Fix Loop 1 复审仍 `fix_required`（SHA-256=`98d8cbf7454bdc9ff76e955eb802a1c4a14920ac55eca48ebae25e9f3629cb10`）；功能 blocker 已关闭，仅因注册表/packet 仍登记 16/23 而实际为 19/26。Fix Loop 2 只校准真实计数并重跑，不删减测试。
- Fix Loop 2 独立复审 `pass`（SHA-256=`4919cdfc4142b6926c56c5f3df297674e41ed363ad284e4fe85a06b86f88808c`），无 finding；专项/组合真实计数为 19/26，52 页、8 项自检、原子写与 NO-GO 无回退。Harness 仅把 F25-A 置 `phase_a_verified`；最终文档同步后须再做一致性复审。

## 2026-08-11 RC0810 暂停交接

- [x] F00 与 F10-A、F12-A、F14-A、F22-A、F25-A 已完成、独立复审并推送；这些只属于基线/定义阶段。
- [ ] F01—F09、F10-B、F11、F12-B、F13、F14-B、F15—F21、F22-B、F23、F24、F25-B、F26 均未完成。
- [ ] 真实 CloudBase、微信平台、iOS/Android、生产 MySQL、Secret、监控值守、专业/隐私/发布负责人签署和 production 发布仍为 pending/NO-GO。
- F01 的未完成草稿未进入 main，已保存为本地 stash `rc0810-f01-paused-draft-20260811`（对象 `3bf30308d93f0f78a5fbdbb2cdc9d8061320d339`）；暂停前 RED 后已把测试合同整理为 18 项，但未重跑，不能记为验收证据。
- 暂停期间可以执行其他 UI 任务，但必须建立独立范围、保留既有 Harness 状态，不得把 UI 完成写成 0810 上线整改完成。UI 若改动 F01/F02/F04/F25 所绑定的页面、配置或源码，恢复 RC0810 时必须使旧证据失效并重新冻结。
- 恢复时从 F01 重新执行 Preflight → Scope Freeze → Failing Contract，不直接沿用暂停前 packet、source tree、dirty diff 或测试结论。

## 2026-08-11 独立 UI 小任务：开放三类能力入口

- [x] 在“我的 → 专业支持”增加“协作式评估”“AI支持性问答”“RAG知识库问答”三个明确入口。
- [x] 协作式评估直达 `pages/therapeutic-assessment/index`；AI 与 RAG 入口复用 `pages/support-assistant/index` 的同一安全问答链路，通过 `focus=ai|rag` 区分页面说明，不重复建设服务端。
- [x] 未登录跳转会保留 `focus`，登录后返回对应问答视图；RAG回答继续展示已审核来源，AI与RAG继续共用同意、边界、引用、风险降级和会话权限。
- [x] 当前源码部署配置已显式设置 `THERAPEUTIC_ASSESSMENT_LIFECYCLE_ENABLED=1`、`AI_QA_ENABLED=1`、`RAG_V2_ENABLED=1`；本轮未修改生产配置、Secret、数据库或正式发布门禁。
- [ ] 真实云端版本、运行时 kill switch、DeepSeek Secret、知识库可用性和微信真机仍须在部署后验收；“入口已开放”不等于 RC0810 或正式生产审核已通过。

## 2026-08-12：RC0810-F01 恢复执行记录

- F01 已从暂停草稿恢复并重新冻结；并行 UI 文件与四份事实文档作为 shared inherited overlay 保留。
- F01 范围为 15 个文件，含环境/构建/能力/客户端合同、测试、验证器、基线、注册表、计划回填和 Harness 断点恢复最小修复。
- F01 专项 18 passed，组合 25 passed，默认验证器、self-check、diff check 通过；生产门禁仍关闭，外部平台与生产证据 pending。
- 当前入口：独立审查通过后提交 F01；若出现 finding 只修复该 finding，不提前进入生产或 F02。

## 2026-08-12：RC0810-F02 页面隔离

- [x] 52 个注册页面已逐项分类；正式包保留 48 个参与者页面，排除 4 个 debug/internal 页面；validation 包继续保留全部页面及非正式环境水印。
- [x] 正式包会移除内部页面文件、内部路由字符串及对应按钮绑定，并生成可达图和包审计。
- [x] F02 专项 8 项通过；真实微信 iOS/Android、屏幕阅读器和平台上传仍 pending，production 继续 NO-GO。
- [ ] 待 Harness 组合回归、独立审查、精确提交和推送；通过后下一入口 F03。

## 2026-08-12：RC0810-F03 镜像分离

- [x] production 与 validation 使用两份独立 Dockerfile；production 默认关闭受禁能力，validation 只显式开放联调能力，两者均不写入 Secret 或数据库连接值。
- [x] entrypoint 固定镜像 profile，并在启动前拒绝 production 运行时覆盖受禁开关；非法覆盖实跑退出码 78。
- [x] Docker 29.6.1 本地构建/运行通过；两类 `/healthz` 环境标记正确、417 条路由一致，镜像 config/history Secret 扫描通过；专项 11 项通过。
- [x] F03 本地工程验收完成；真实 CloudBase、production MySQL、平台 Secret、运维身份和发布批准未验收，`production_gate_eligible=false`，这些外部/后续项不阻止 F03 提交后进入 F04。
- [x] 首轮独立审查 `fix_required`：镜像误带测试、SQLite 与 Python 缓存；Fix Loop 1 已通过递归 `.dockerignore` 与镜像文件系统检查闭环。
- [x] 第二轮审查确认污染已关闭，但 validation 的原有研究联调能力未全部恢复；Fix Loop 2 已对照 profile 恢复并由容器内 `app.config` 检查闭环。
- [x] 第三轮审查确认 validation 已闭环，但 production 对部分执行/写入开关仍可运行时覆盖；Fix Loop 3 已纳入同组真实执行能力并复审通过，纯只读 workbench 未被过度封禁。
- [x] Fix Loop 3 独立复审 `pass`，SHA-256=`fbfda53dd37228cada1cf857df57c45d1e9f22d3262760b5835c971f590a878a`；Harness 已接受。最终文档同步后重跑 7 条验收并完成一致性复审，再提交推送进入 F04。

## 2026-08-12：RC0810-F04 CloudBase 目标锁定

- [x] development 默认 loopback，仅允许本地目标与登记的云联调目标；validation 保留受控调试切换；production 包在构建时固定唯一候选 CloudBase 目标。
- [x] production 包不读取 storage、extConfig 或启动参数切换目标；非法目标和网络失败返回可恢复错误，不自动回退到本地 HTTP 或其他环境。
- [x] 旧配置迁移只删除 `safehome_cloud_config`，不清登录、草稿、进度或个人数据。
- [x] F04 专项 `12 passed`、组合 `29 passed`；离线验证器、production/validation 构建和 diff check 通过。
- [x] 首轮审查唯一 finding 为 validation 调试页缺少登记目标导出；Fix Loop 1 已闭环，独立复审 `pass`，decision SHA-256=`77d0ba3cab1f7a3b646dd977f0f76e78fb83c72550602a02bd86725427cb5414`。
- [ ] 真实 CloudBase、微信平台、真机和发布批准仍为 pending，production 继续 NO-GO。按负责人要求，本阶段提交推送后停止，不启动 F05。

## 2026-08-12：RC0810-F05 Showcase 生产硬关闭

- [x] production profile 在读取 Showcase 内容与执行临时提升前先硬关闭；旧环境变量或专用 Header 都不能把 parent/student/researcher 提升为 admin。
- [x] development/testing/validation 继续保留现有 Showcase 联调能力；只有当前 actor 实际携带专用 Header、请求登记研究路径且 profile gate 有效时，才声明 `showcase_full_access` 与开发例外。
- [x] 允许与拒绝决定写入已有 `audit_logs`，记录真实 actor、角色、路径、request_id 与有效 profile；未新增数据库表或迁移。
- [x] 首轮独立审查发现 capability 摘要未绑定当前 actor；Fix Loop 1 最小修复后复审 `pass`，decision SHA-256=`c7aba1735da6077728a8c8ae12732c63beafe999f8dddc3c37f4f140cbe187b8`。
- [x] F05 专项 `6 passed`、既有 Showcase `16 passed`、组合 `29 passed`，离线 verifier 与 `git diff --check` 通过；13 文件合同与证据绑定一致。
- [ ] production break-glass 不在本轮虚构实现；强认证、双人确认、限时、理由、范围、自动过期和审计仍为 `pending_external`，真实平台与发布继续 NO-GO。
- 下一入口：完成最终文档一致性复审、精确提交并推送后，从 `RC0810-F06` 的 Preflight → Scope Freeze 开始；不得把 validation 开发例外当作 production 授权。

## 2026-08-13：非权限项产品信息密度与工程收敛

- [x] R00：记录 main、HEAD、最近 10 次提交、dirty 文件和 diff stat；8 个开始前未提交文件全部保留。
- [x] R01：审计 `miniprogram_page_policy` 中 48 个参与者页面，输出六维静态信息密度指标与问题页面排名。
- [x] 建立 `home.before.json` 和 `assessment-result.before.json`，覆盖功能、按钮、入口、导航、数据块、API 与 loading/error/empty 状态。
- [x] 明确权限、心理计分、风险分流、API、数据库和 shared 均冻结；R00/R01 未修改 UI。
- [ ] R02：首页呈现收敛。下一次只从 PRECHECK 和 Scope Freeze 开始；before 项必须全部保留并生成 after 对比，完成 UI/功能/回归/独立审查后才可提交为 PASS。
## 2026-08-10 UIproduct 首页实现状态

- [x] 情绪记录依赖页完成真值、ImageGen、Figma、代码与本地 Loop。
- [x] 首页完成方案 A 代码复现，真实功能和模块顺序保持不变。
- [x] 微信开发者工具 Preview 编译通过。
- [x] 首页四类本地 Harness 已登记，逐页本地状态为 `complete`。
- [ ] Android/iOS、大字体和读屏统一延期到全部页面本地完成后的最终批次。
- [ ] 当前按单页流程进入 `pages/login/index`；不得因延期而跳过 ImageGen、Figma、本地 Loop 1–4 或 Harness。
- [ ] 53 页本地完成后启动全量真机 Loop 5，逐页记录 `pass` 或 `fix_required` 并完成修正回归。

## 2026-08-10 UIproduct 登录页状态

- [x] 登录页功能真值、需求冻结、现状审查与方案 A 方向完成。
- [x] ImageGen v2 完成功能自审；v1 越界隐私卡已淘汰。
- [x] Figma Phase 0 只读发现完成，授权恢复且未遗留原子失败写入。
- [x] 复用 token/Button，新增 AuthField 五状态组件，完成登录六态与 Figma 审查。
- [x] 登录页前端、本地 Loop 1–4 和逐页 Harness 完成；真机继续留到 53 页本地完成后的最终批次。

## 2026-08-10 UIproduct 登录页 Figma 重新认证门禁

- [x] 复核 `UIproduct` 分支、登录页真值与 ImageGen 审查结果。
- [x] 第二轮调用 Figma `whoami`，明确阻断为连接需要重新认证。
- [x] 用户重新授权 Figma 后，已从 Phase 0 只读发现恢复并完成组件化复现与审查。
- [x] Figma 通过后才修改登录页前端；本地 Loop 1–4 与逐页 Harness 已完成，真机继续统一后置。
- [x] 连续第三轮 `whoami` 仍要求重新认证；当前任务按阻断规则登记为 blocked，等待外部授权状态变化后恢复。

## 2026-08-10 UIproduct 登录页完成与下一门禁

- [x] 登录页 ImageGen → Figma → WXML/WXSS → 本地 Loop/Harness 完整闭环，注册表状态 `complete`。
- [x] 微信开发者工具 `preview` 编译通过，未出现 WXSS 编译错误；业务 JS、认证接口、后端和数据库均未修改。
- [x] 当前自动流程推进到 `pages/register/index`，但尚未开始注册页设计。
- [ ] 主 worktree 的 main 已外部推进到 `9c7d77c`，与 UIproduct 核准基线 `65fcef4` 不一致；需负责人明确授权新的合并或基线处理后，才能恢复全局 Harness 并开始注册页。
- [ ] 全部页面完成后统一执行 Android/iOS、读屏和大字体真机验收。

## 2026-08-10 UIproduct 延后合并 main 决定

- [x] 用户明确决定先完成全部 UI，再统一合并 main。
- [x] Harness 范围比较改为固定核准基线 `65fcef4`；外部 main `9c7d77c` 仅记录为最终集成待办。
- [x] 53 页功能真值、truth Harness 与工程 Harness 重新通过，当前恢复到注册页。
- [ ] 逐页完成剩余 51 页的 ImageGen、Figma、前端、本地 Loop 1–4 与 Harness。
- [ ] 全部页面本地完成后，在 UIproduct worktree 统一合并当时 main；冲突同时保留两侧记录，更新基线并全量回归。
- [ ] 合并与回归通过后，再启动统一真机验收和修正。

## 2026-08-10 UIproduct 注册页状态

- [x] 对照 WXML/JS/API/后端公开角色限制完成注册页功能真值与需求冻结。
- [x] ImageGen v2 通过，移除只依赖 placeholder 的长度规则与按钮渐变感。
- [x] Figma 复用现有 token、AuthField、Button，新增 SelectField 四状态并完成六屏审查。
- [x] 仅实现注册页 WXML/WXSS和 Figma 导出箭头；注册 JS、API、后端和数据库未修改。
- [x] 微信开发者工具 Preview、T23、资产和前端审计通过；本地 Loop 1–4 与四类 Harness 已登记。
- [ ] 当前进入 `pages/messages/index`，继续执行同一单页流程。
- [ ] 真机、Android/iOS、大字体和读屏仍待全部 53 页本地完成后统一验收。

## 2026-08-10 UIproduct 消息页状态

- [x] 对照 WXML/JS/API/后端只读消息能力完成消息页功能真值与需求冻结。
- [x] ImageGen v2 修正重复标题和固定高列表空白，保持未读、已读、撤回与版本信息。
- [x] Figma 新增 MessageRow 三态组件，完成七个 390×844 页面状态及视觉审查。
- [x] 仅实现消息页 WXML/WXSS/JSON；消息 JS、接口、后端、数据库和自动已读语义未修改。
- [x] 微信开发者工具 Preview、T23、资产、前端、真值与工程 Harness 通过；本地 Loop 1–4 与四类 Harness 已登记。
- [ ] 当前进入 `pages/support-assistant/index`，继续执行同一单页流程。
- [ ] 真机、main 合并、Android/iOS、大字体和读屏仍待全部页面本地完成后统一处理。

## 2026-08-10 UIproduct 支持性问答页状态

- [x] 对照页面代码、登录守卫、AI 配置、同意、会话与发送接口完成详细功能真值和需求冻结。
- [x] 使用 UI skills 完成现状审查与三个结构方向；采用 A1 编辑式支持便笺。
- [x] ImageGen v1 通过自审，保留边界、问答、引用和输入，不新增聊天或诊断能力。
- [x] Figma Phase 0 已在连接恢复后完成；变量、样式、页面、组件与外部库状态均已实读。
- [x] 已补齐本地 P0.a/P0.d/P0.e 和组件缺口清单；P0.b/P0.c 明确等待 Figma 当前状态复核。
- [x] 连续第三个目标轮次仍为同一传输错误，已按阻断规则登记 blocked；恢复条件为 Figma MCP `whoami` 成功。
- [x] Figma 曾短暂恢复并完成 P0.b/P0.c；`BoundaryNote` 文档区与两态空骨架已创建，精确节点为 `93:57`、`93:61`、`93:62`。
- [x] `BoundaryNote` 两态组件集与属性完成；`ConversationEntry` 两态组件集与属性完成。
- [x] 用户恢复后的连续三轮检查仍为同一传输错误，任务再次按规则标记 blocked。
- [x] 已创建并审核 10 个页面状态，Disabled、同意、就绪、发送、对话、错误与长内容均完成。
- [x] 支持性问答 10 个 Figma 状态、三组件集、前端实现、Preview、本地 Loop 1–4 与四类 Harness 全部完成。
- [ ] 当前进入 `pages/message-detail/index`；继续执行真值复核、UI skills、冻结、ImageGen、Figma、实现和本地审核。
- [ ] main 合并和 Android/iOS 真机继续统一后置，不因 Figma 阻断改变顺序。

## 2026-08-11 UIproduct 紧急安全指引页状态

- [x] 对照页面 JS、静态行动数组和上下游路由完成功能真值与方案 A 冻结。
- [x] ImageGen、`SafetyActionRow` 两态组件、Default 与 320px 长内容 Figma 状态完成并审查。
- [x] 仅实现 WXML/WXSS/JSON；页面 JS、接口、后端、数据库、content 与 shared 未修改。
- [x] 接地编号修正为 5→1；现实资源仍走原 `navigateTo`，首页仍走原 `reLaunch`。
- [x] Preview、53 页真值、token、UI governance、non-UI client、T23 与工程 Harness 通过。
- [ ] 当前进入 `pages/emergency-resources/index`，继续执行同一单页流程。
- [ ] main 合并、真机、大字体、读屏和 Android/iOS 继续统一后置。

## 2026-08-11 UIproduct 紧急帮助说明页状态

- [x] 对照页面 JS、四项静态资源、使用边界和安全指引路由完成功能真值与方案 A 冻结。
- [x] 使用 UI skills 完成 ImageGen、`ResourceChannelRow`、Default 与 320px Figma 状态和视觉审查。
- [x] 仅实现 WXML/WXSS；页面 JS、JSON、数据、事件、路由、API、后端、数据库、content 与 shared 未修改。
- [x] 将重复粗侧线替换为 `4rpx` 开放式转角，并同步写入 UI 总指导。
- [x] Preview、53 页真值、token、UI governance、non-UI client、T23 与工程 Harness 通过。
- [x] Loop/Harness 已增加用户手工截图审查门禁；当前状态为 `awaiting_user_review`。
- [ ] 等待用户手工截图，Codex 对照审查；通过后记录 `done` 并提交本页可恢复点。
- [ ] 截图审查通过前不得进入 `pages/getting-started/index`；全量真机适配仍在所有页面本地完成后统一执行。

## 2026-08-11 UIproduct 全页面小字门禁

- [x] 审查用户提供的 8 张研究者端与用户端真实页面截图。
- [x] 在 UI 总指导中冻结 `24rpx` 下限、`28rpx` 正文、单区小字通常不超过两行、免责声明去重和机器字段人类化规则。
- [x] 将小字预算加入 ImageGen、Figma、代码审核、Loop 2、UX Harness 和用户截图 `fix_required` 条件。
- [ ] 当前页仍等待专属手工截图；跨页截图不得用于越过 `pages/emergency-resources/index` 的用户验收门禁。

## 2026-08-11 UIproduct 连续完成、最终统一验收

- [x] 用户取消逐页手工截图等待，授权代理按既有文档门禁持续完成全部页面。
- [x] 保留功能真值、UI skills、方案 A、ImageGen 自审、Figma、前端、Loop 1–4、四类 Harness 和小字预算。
- [x] 最终用户视觉、功能与 Android/iOS 真机验收继续由 `device_acceptance` 控制，只在全部页面本地完成并完成 main 集成回归后开放。
- [x] 登记紧急帮助说明页 `done`，活动页面进入 `pages/getting-started/index`。
- [ ] 验证并提交紧急帮助说明页可恢复点，然后开始首次使用页功能审查。

## 2026-08-11 UIproduct 网页版 GPT 生产与 Codex 修复审查

- [x] 新增网页版 GPT 执行包，包含 UI 规则、Design 基础、ImageGen 模板、Figma 规则、GitHub 约束和远端证据格式。
- [x] 冻结职责：网页版 GPT 先生产并推送 `UIproduct`；Codex 收到精确远端链接后独立审查。
- [x] 冻结不可行处理：Codex 按 ImageGen → Figma → 代码顺序接管修正，完成 Loop/Harness 后提交新的 `UIproduct` 修复提交。
- [x] 保留全部页面后统一视觉、功能与真机验收；远端 Codex 审查不能替代 Loop 5。
- [x] `pages/getting-started/index` 保持冻结完成、Figma 与前端未开始；已有 ImageGen 仅作参考。
- [x] 将 12 张现有截图复制到 `design/ui-product/references/current-ui/`，逐张写明可借鉴点、已知问题和功能真值边界。
- [ ] 用户把执行包交给网页版 GPT，并在完成一页后把 ImageGen、Figma node 和 GitHub commit 链接交给 Codex。

## 2026-08-11 Codex 本地连续 UI 执行续段

- [x] 完成 `pages/getting-started/index`。
- [x] 完成 `pages/thermometer/index`，保留情绪温度计真实语义。
- [x] 完成 `pages/training/index`。
- [x] 完成 `pages/training-history/index`。
- [x] 完成 `pages/personalized-plan/index` 真值冻结、ImageGen 与图像审查。
- [ ] 从个性化训练方案 Figma 门禁继续，随后持续处理剩余页面。

## 2026-08-11 UIproduct 关系探索续段

- [x] 完成 `pages/personalized-plan/index`。
- [x] 完成 `pages/program-list/index`。
- [x] 完成 `pages/program-detail/index`。
- [x] 完成 `pages/relationship-pilot/index`。
- [x] 完成 `pages/relationship-report/index`。
- [x] 完成 `pages/relationship-task/index`。
- [x] 完成 `pages/relationship-growth/index`。
- [ ] 按注册表继续下一页面，全部页面本地完成后统一真机验收。

- [x] 完成 `pages/therapeutic-assessment/index`。
- [x] 完成 `pages/therapeutic-assessment-boundary/index`。
- [x] 完成 `pages/therapeutic-assessment-issue/index`。
- [x] 完成 `pages/therapeutic-assessment-recent-event/index`。
- [x] 完成 `pages/therapeutic-assessment-resources/index`。
- [x] 完成 `pages/therapeutic-assessment-sharing/index`。
- [x] 完成 `pages/therapeutic-assessment-summary/index`。
- [x] 完成 `pages/therapeutic-assessment-feedback-check/index`。
- [x] 完成 `pages/therapeutic-assessment-action-review/index`。
- [ ] 继续 `pages/therapeutic-assessment-action-followup/index`。
## 2026-08-13：信息收敛与 UIproduct 本地集成

- [x] `codex/信息收敛` 已快进合并到本地 `main`；提交 `757ceddb` 的 AI/RAG 动态入口和登录回跳参数已保留。
- [x] `UIproduct` 的 29 个提交已进入本地合并；6 个冲突按双侧意图解决，支持性问答保留动态标题并采用组件化页面结构，四份事实文档保留两条历史。
- [x] 项目旧 UI 文档未随分支删除；新总指导与真值表同时保留。UIproduct 独立工作树的 5 个未跟踪预览文件、F06 工作树的 5 个草稿均未改动。
- [x] 合并验证：34 个变更 JS、54 个 JSON 可解析；相关前端合同 `25 passed`；UIproduct 分支真值与工程 Harness 通过，53/53 页面已登记。
- [ ] 全量真机仍为 `fix_required`，仅记录 21/53；本地集成不代表正式上线、生产批准或真机验收完成。

## 2026-08-28：RC0810 required gate 恢复状态

- [x] F01 能力矩阵与稳定源码哈希校验已对齐当前配置代码；F01 专项 `18 passed`。
- [x] F05、F16/F36/B04/F09 对象范围测试夹具和当前首页合同已修正；相关定向测试通过。
- [x] 迁移恢复脚本显式执行 pending migrations；Task35、内容/API/config inventory 校验通过。
- [ ] clean source freeze 后重建 F25-B 包、重跑 F22-A/B 安全扫描、required CI、迁移回滚/恢复与最终全量回归。
- [ ] 既有 reviewer 只在 F12-B 冻结点接收精简 packet；当前保持 `review_pending_wave`，不得伪造 `review_pass`。
- [ ] production 仍 NO-GO：外部平台/真机/CloudBase/Secret/发布批准未完成，npm audit 仍有 4 个 High。

## 2026-08-28：本地门禁完成后的继续入口

- [x] 本地 required、Docker、MySQL/Redis、迁移恢复、安全重扫和 RC 重冻结已完成；唯一 required 失败为 npm audit 4 High。
- [x] 波次 C 审查包已冻结并绑定 `1311eee7`，F26 定向测试 `12 passed`。
- [ ] 固定 reviewer 当前不可恢复，继续保持 `review_pending_wave`；推送后由网页 GPT 只读审查累计代码并核验 GitHub Actions，不得替代 Harness reviewer 或批准上线。
- [x] F25-A/F25-B 证据自引用已做最小修复；仅证据提交可保持有效，真实源码、定义、包或镜像变化仍 fail-closed。
- [x] F22-B Docker 上下文复用检查已与 Dockerfile/`.dockerignore` 对齐；测试、文档、脚本变化仍重扫源码，但不重复未变化镜像扫描。
- [x] F22-B 与 F25-A 的证据提交后绑定已统一；F25-B tree inventory 排除 `backend/tests`，与 `.dockerignore` 保持一致。

## 2026-08-29：网页审查 Fix Loop 状态

- [x] 修复 GitHub/Ubuntu 与 Windows checkout 的 checkpoint、F22/F25 和 Task35 换行摘要差异；T8 测试改用上海业务日。
- [x] 新增 UTC 15:59/16:00/白天边界，F01/F03/T8 定向组合 `32 passed`；历史 checkpoint 有效/过期/CRLF 合同 `2 passed`。
- [x] 历史 review decision 开始强制校验 `valid_until`；当前 F14-A 已过期并按预期 fail-closed，未改日期或伪造 pass。
- [x] 生产 Docker 基础镜像绑定 immutable digest，本地构建成功；F01 清单改为真实的 fail-closed 生产候选定义。
- [x] 用户授权 registry 元数据访问后，`nanoid 3.3.17` 最小更新到 3.3.18；audit/typecheck/build 通过。
- [ ] 推送后由 GitHub required Actions 执行完整回归；按用户要求不再本地重复全量。旧 F22/F25/F26/波次 C 证据因源码变化保持失效。
- [ ] 固定 reviewer 重新审查当前累计 packet 前保持 `review_pending_wave / production_no_go`。

## 2026-08-29：F01/F14/F24 事实清单 Fix Loop

- [x] 修正 F01 字面量 `\\r\\n` 归一错误；F14/F24 同步使用 LF 规范化源码摘要。
- [x] 重建 environment inventory、privacy lineage catalog、config-read inventory；三项专项合计 `38 passed`。
- [x] F14 source bindings/current catalog 恢复有效。
- [ ] F14 的 189 个 privacy gaps、0 confirmed reviews 与 privacy owner pending_external 保持开放，不由自动化审批。
- [ ] 推送后由 GitHub required CI 核验；过期 F14-A review decision 仍须固定 reviewer 重新签发，禁止改旧日期。
