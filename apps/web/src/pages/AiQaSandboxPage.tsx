import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  AiProviderContractEvidence,
  AiProviderEvidenceType,
  AiProviderSelection,
  AiQaAnswer,
  AiQaConfig,
  AiQaEvaluationRun,
  AiQaReviewCase,
  AiQaReviewDecision,
  AiQaReviewEvidence,
  AiQaSession,
  AiKnowledgeInventory,
  AiKnowledgeRetrievalMethod,
  AiKnowledgeRetrievalResult,
} from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


const DEFAULT_USE_CASE_ID = "approved_material_organization";
const USE_CASE_EXAMPLES: Record<string, string> = {
  approved_material_organization: "请按来源整理这组已批准材料，不补充材料外事实。",
  question_version_drafting: "请基于已批准材料草拟三个待研究者核对的问题版本。",
  evidence_gap_check: "请标出当前已批准材料中尚未覆盖的证据缺口。",
  discussion_checklist: "请把已批准材料整理为不下结论的团队讨论清单。",
  format_spelling_deidentification_terminology_candidate: "请提出格式、错别字、去标识化和术语一致性候选修改。",
};
const PROVIDER_EVIDENCE_TYPES: AiProviderEvidenceType[] = [
  "service_contract",
  "data_processing_agreement",
  "privacy_impact_assessment",
  "data_residency_commitment",
  "provider_training_non_use",
  "retention_deletion_commitment",
  "subprocessor_register",
  "security_audit",
  "sla_support",
  "content_policy_approval",
  "pricing_snapshot",
  "owner_approval",
];

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "操作失败，请核对权限与沙盒状态。";
}

export function AiQaSandboxPage() {
  const actor = getStoredAuthUser();
  const canChat = ["researcher", "supervisor", "admin"].includes(actor?.role || "");
  const canReview = ["supervisor", "admin"].includes(actor?.role || "");
  const isAdmin = actor?.role === "admin";
  const [config, setConfig] = useState<AiQaConfig | null>(null);
  const [sessions, setSessions] = useState<AiQaSession[]>([]);
  const [activeSession, setActiveSession] = useState<AiQaSession | null>(null);
  const [answer, setAnswer] = useState<AiQaAnswer | null>(null);
  const [reviewCases, setReviewCases] = useState<AiQaReviewCase[]>([]);
  const [activeReviewCase, setActiveReviewCase] = useState<AiQaReviewCase | null>(null);
  const [reviewDecision, setReviewDecision] = useState<AiQaReviewDecision>("adopt");
  const [reviewFinalText, setReviewFinalText] = useState("");
  const [reviewRationale, setReviewRationale] = useState("");
  const [evidence, setEvidence] = useState<AiQaReviewEvidence | null>(null);
  const [evaluation, setEvaluation] = useState<AiQaEvaluationRun | null>(null);
  const [providerSelection, setProviderSelection] = useState<AiProviderSelection | null>(null);
  const [providerEvidence, setProviderEvidence] = useState<AiProviderContractEvidence[]>([]);
  const [knowledge, setKnowledge] = useState<AiKnowledgeInventory | null>(null);
  const [knowledgeQuery, setKnowledgeQuery] = useState("情绪升高时怎样暂停");
  const [knowledgeMethod, setKnowledgeMethod] = useState<AiKnowledgeRetrievalMethod>("hybrid");
  const [knowledgeResult, setKnowledgeResult] = useState<AiKnowledgeRetrievalResult | null>(null);
  const [providerId, setProviderId] = useState<"deepseek" | "openai">("deepseek");
  const [evidenceType, setEvidenceType] = useState<AiProviderEvidenceType>("service_contract");
  const [artifactRef, setArtifactRef] = useState("");
  const [artifactSha256, setArtifactSha256] = useState("");
  const [selectedUseCaseId, setSelectedUseCaseId] = useState(DEFAULT_USE_CASE_ID);
  const [question, setQuestion] = useState(USE_CASE_EXAMPLES[DEFAULT_USE_CASE_ID]);
  const [status, setStatus] = useState("正在读取受控沙盒状态…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [nextConfig, nextEvidence, nextProviderSelection, nextProviderEvidence, nextKnowledge] = await Promise.all([
      safeHomeApi.getAiQaConfig(),
      safeHomeApi.getAiQaReviewEvidence(),
      safeHomeApi.getAiProviderSelection(),
      safeHomeApi.getAiProviderEvidence(),
      safeHomeApi.getAiKnowledgeInventory(),
    ]);
    setConfig(nextConfig);
    const allowedIds = new Set(nextConfig.use_case_policy.allowed_use_cases.map((item) => item.id));
    setSelectedUseCaseId((current) => {
      if (allowedIds.has(current)) return current;
      const fallback = nextConfig.use_case_policy.allowed_use_cases[0]?.id || "";
      setQuestion(USE_CASE_EXAMPLES[fallback] || "");
      return fallback;
    });
    setEvidence(nextEvidence);
    setProviderSelection(nextProviderSelection);
    setProviderEvidence(nextProviderEvidence.items);
    setKnowledge(nextKnowledge);
    if (canChat) {
      const [listed, listedReviewCases] = await Promise.all([
        safeHomeApi.listAiQaSessions(),
        safeHomeApi.listAiQaReviewCases(),
      ]);
      setSessions(listed.items);
      setReviewCases(listedReviewCases.items);
      if (listedReviewCases.items[0]) {
        setActiveReviewCase(listedReviewCases.items[0]);
        setReviewFinalText(listedReviewCases.items[0].candidate_text);
      }
      const current = listed.items.find((item) => item.status === "active");
      if (current) setActiveSession(await safeHomeApi.getAiQaSession(current.id));
    }
    setStatus("受控沙盒状态已更新。");
  }, [canChat]);

  useEffect(() => {
    load().catch((error) => setStatus(errorText(error)));
  }, [load]);

  const gateItems = useMemo(
    () => Object.entries(config?.gate_decisions || {}),
    [config],
  );

  async function run(label: string, callback: () => Promise<void>) {
    setBusy(true);
    setStatus(`${label}…`);
    try {
      await callback();
      setStatus(`${label}完成。`);
    } catch (error) {
      setStatus(errorText(error));
    } finally {
      setBusy(false);
    }
  }

  function createSession() {
    if (!selectedUseCaseId) return;
    void run("创建合成会话", async () => {
      const created = await safeHomeApi.createAiQaSession(selectedUseCaseId);
      setActiveSession(created);
      setSessions((current) => [created, ...current]);
      setAnswer(null);
    });
  }

  function askQuestion() {
    const text = question.trim();
    if (!activeSession || !text) return;
    void run("执行安全路由与已发布内容检索", async () => {
      const nextAnswer = await safeHomeApi.sendAiQaMessage(activeSession.id, text);
      setAnswer(nextAnswer);
      setActiveSession(await safeHomeApi.getAiQaSession(activeSession.id));
      if (nextAnswer.review_case_id) {
        const reviewCase = await safeHomeApi.getAiQaReviewCase(nextAnswer.review_case_id);
        setActiveReviewCase(reviewCase);
        setReviewFinalText(reviewCase.candidate_text);
        setReviewCases((current) => [
          reviewCase,
          ...current.filter((item) => item.id !== reviewCase.id),
        ]);
      }
    });
  }

  function selectReviewCase(caseId: string) {
    void run("读取AI候选审阅任务", async () => {
      const reviewCase = await safeHomeApi.getAiQaReviewCase(caseId);
      setActiveReviewCase(reviewCase);
      setReviewFinalText(reviewCase.final_text || reviewCase.candidate_text);
      setReviewRationale("");
    });
  }

  function decideReviewCase() {
    if (!activeReviewCase) return;
    void run("保存人工审阅决定", async () => {
      const decided = await safeHomeApi.decideAiQaReviewCase(
        activeReviewCase.id,
        {
          decision: reviewDecision,
          expected_version: activeReviewCase.version,
          final_text: reviewDecision === "modify" ? reviewFinalText.trim() : undefined,
          rationale: reviewRationale.trim() || undefined,
        },
        `ai-review:${activeReviewCase.id}:${reviewDecision}:${Date.now()}`,
      );
      setActiveReviewCase(decided);
      setReviewCases((current) => current.map((item) => (
        item.id === decided.id ? decided : item
      )));
      setReviewRationale("");
    });
  }

  function deleteSession() {
    if (!activeSession) return;
    void run("删除会话原文", async () => {
      await safeHomeApi.deleteAiQaSession(activeSession.id);
      setSessions((current) => current.map((item) => item.id === activeSession.id ? { ...item, status: "deleted" } : item));
      setActiveSession(null);
      setAnswer(null);
    });
  }

  function runEvaluation() {
    void run("运行合成安全评测", async () => {
      const result = await safeHomeApi.runAiQaEvaluation();
      setEvaluation(result);
      setEvidence(await safeHomeApi.getAiQaReviewEvidence());
    });
  }

  function reviewLatest(decision: "approved_for_next_internal_stage" | "changes_required" | "stop") {
    const runId = evidence?.runs[0]?.id;
    if (!runId) return;
    void run("保存人工复核证据", async () => {
      await safeHomeApi.reviewAiQaEvaluation(runId, {
        decision,
        evidence_path: `internal://task28/${runId}`,
        note: "只确认进入下一内部工程阶段，不批准参与者开放。",
      });
      setEvidence(await safeHomeApi.getAiQaReviewEvidence());
    });
  }

  function killSandbox() {
    void run("停用内容助手", async () => {
      await safeHomeApi.activateAiQaKillSwitch("T28 研究沙盒人工停用");
      setConfig(await safeHomeApi.getAiQaConfig());
      setActiveSession(null);
    });
  }

  function recordProviderEvidence() {
    if (!artifactRef.trim() || artifactSha256.trim().length !== 64) return;
    void run("登记供应商证据元数据", async () => {
      await safeHomeApi.recordAiProviderEvidence({
        provider_id: providerId,
        evidence_type: evidenceType,
        artifact_ref: artifactRef.trim(),
        artifact_sha256: artifactSha256.trim().toLowerCase(),
      }, `provider-evidence:${providerId}:${evidenceType}:${Date.now()}`);
      setProviderEvidence((await safeHomeApi.getAiProviderEvidence()).items);
      setProviderSelection(await safeHomeApi.getAiProviderSelection());
      setArtifactRef("");
      setArtifactSha256("");
    });
  }

  function verifyProviderEvidence(item: AiProviderContractEvidence, decision: "verified" | "rejected") {
    void run("独立复核供应商证据", async () => {
      await safeHomeApi.verifyAiProviderEvidence(
        item.id,
        { decision, expected_version: item.version },
        `provider-evidence-review:${item.id}:${decision}:${Date.now()}`,
      );
      setProviderEvidence((await safeHomeApi.getAiProviderEvidence()).items);
      setProviderSelection(await safeHomeApi.getAiProviderSelection());
    });
  }

  function rebuildKnowledge() {
    void run("重建批准知识索引", async () => {
      await safeHomeApi.rebuildAiKnowledge();
      setKnowledge(await safeHomeApi.getAiKnowledgeInventory());
      setKnowledgeResult(null);
    });
  }

  function compareKnowledgeRetrieval() {
    const query = knowledgeQuery.trim();
    if (!query) return;
    void run(`运行${knowledgeMethod}检索`, async () => {
      setKnowledgeResult(
        await safeHomeApi.retrieveAiKnowledge(query, knowledgeMethod),
      );
    });
  }

  return (
    <section className="dashboardShell aiQaWorkbench" aria-label="支持性内容助手研究沙盒">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">T28 · 仅限合成数据</p>
          <h1>支持性内容助手研究沙盒</h1>
          <p className="summary">验证范围、安全路由、已发布内容引用和失败降级。这里不是参与者问答服务，也不能替代专业判断。</p>
        </div>
        <span className="gateBadge gateBlocked">参与者入口关闭</span>
      </div>

      <div className="status" role="status" aria-live="polite">{status}</div>

      <section className="aiQaGatePanel" aria-label="发布门禁">
        <div>
          <span className="panelKicker">当前工程边界</span>
          <h2>{config?.sandbox_enabled ? "合成研究沙盒可用" : "沙盒已停用"}</h2>
          <p>{config?.boundary_notice || "正在读取治理状态。"}</p>
        </div>
        <dl className="aiQaFacts">
          <div><dt>服务端供应商</dt><dd>{config?.provider || "—"}（客户端不可指定）</dd></div>
          <div><dt>真实适配器</dt><dd>{config?.provider_policy ? `${config.provider_policy.adapter_candidates.join(" / ")} · ${config.provider_policy.external_provider_enabled ? "门禁通过" : "保持关闭"}` : "等待新版本服务"}</dd></div>
          <div><dt>连接 / 读取 / 总超时</dt><dd>{config?.provider_policy ? `${config.provider_policy.connect_timeout_ms} / ${config.provider_policy.read_timeout_ms} / ${config.provider_policy.timeout_ms}ms` : "等待新版本服务"}</dd></div>
          <div><dt>密钥位置</dt><dd>仅云托管 Secret 或服务端环境变量</dd></div>
          <div><dt>跨会话记忆</dt><dd>关闭</dd></div>
          <div><dt>写操作工具</dt><dd>禁止</dd></div>
          <div><dt>输入去标识</dt><dd>{config?.input_security ? `${config.input_security.deidentification_categories.length}类` : "等待新版本服务"}</dd></div>
          <div><dt>检索片段信任</dt><dd>{config?.input_security?.retrieved_content_trusted === false ? "不可信数据" : "等待新版本服务"}</dd></div>
          <div><dt>只读工具清单</dt><dd>{config?.input_security?.allowlist.join(" / ") || "无"}</dd></div>
          <div><dt>路径与外网参数</dt><dd>{config?.input_security?.arbitrary_paths_allowed === false && config?.input_security?.arbitrary_network_hosts_allowed === false ? "禁止" : "等待新版本服务"}</dd></div>
          <div><dt>输出五道门</dt><dd>{config?.output_contract?.gates.join(" / ") || "等待新版本服务"}</dd></div>
          <div><dt>不合格输出</dt><dd>{config?.output_contract?.fixed_degradation ? "固定降级，不自动重试修复" : "等待新版本服务"}</dd></div>
          <div><dt>Grounding 边界</dt><dd>{config?.output_contract?.grounding_is_factuality_check === false ? "词面启发式，不等于事实正确" : "等待新版本服务"}</dd></div>
          <div><dt>预算与限流范围</dt><dd>{config?.runtime_limits?.scopes.join(" / ") || "等待新版本服务"}</dd></div>
          <div><dt>故障降级</dt><dd>{config?.runtime_limits?.degradation.mode === "read_only_fixed_response" ? "只读固定回执，核心记录链路不受影响" : "等待新版本服务"}</dd></div>
          <div><dt>当前发布阶段</dt><dd>{config?.release_plan?.current_stage || "等待新版本服务"}</dd></div>
          <div><dt>下一阶段门禁</dt><dd>{config?.release_plan?.next_stage_blockers.length ? `${config.release_plan.next_stage_blockers.length}项未通过` : "无自动发布许可"}</dd></div>
          <div><dt>合成原文保留</dt><dd>{config?.data_policy.synthetic_retention_days ? `${config.data_policy.synthetic_retention_days}天` : "待服务更新"}</dd></div>
          <div><dt>训练使用</dt><dd>禁止</dd></div>
        </dl>
      </section>

      <section className="panel" aria-label="批准知识库与检索验证">
        <div className="panelHeading">
          <div>
            <span className="panelKicker">T37-C04 · 只读批准内容</span>
            <h2>知识库与RAG验证</h2>
          </div>
          {canReview ? (
            <button
              className="secondaryButton"
              disabled={busy}
              type="button"
              onClick={rebuildKnowledge}
            >
              重建批准索引
            </button>
          ) : null}
        </div>
        <p className="boundaryCallout">
          只索引已完成四类审核、权利明确且处于有效期内的发布版本；网页候选只保留元数据并停留在隔离区。
        </p>
        <div className="metricGrid compactMetrics">
          <div>
            <strong>{knowledge?.documents.filter((item) => item.status === "active").length || 0}</strong>
            <span>有效文档</span>
          </div>
          <div>
            <strong>{knowledge?.documents.reduce((sum, item) => sum + Number(item.chunk_count || 0), 0) || 0}</strong>
            <span>可追踪切片</span>
          </div>
          <div>
            <strong>{knowledge?.candidates.length || 0}</strong>
            <span>隔离候选</span>
          </div>
          <div>
            <strong>{knowledge?.web_candidate_auto_approval ? "异常" : "关闭"}</strong>
            <span>网页自动准入</span>
          </div>
        </div>
        <div className="formGrid">
          <label>
            合成检索问题
            <input
              value={knowledgeQuery}
              maxLength={500}
              onChange={(event) => setKnowledgeQuery(event.target.value)}
            />
          </label>
          <label>
            检索方法
            <select
              value={knowledgeMethod}
              onChange={(event) => setKnowledgeMethod(event.target.value as AiKnowledgeRetrievalMethod)}
            >
              <option value="bm25">BM25</option>
              <option value="vector">本地向量基线</option>
              <option value="hybrid">混合检索与重排</option>
            </select>
          </label>
          <button
            className="secondaryButton"
            disabled={busy || !knowledgeQuery.trim()}
            type="button"
            onClick={compareKnowledgeRetrieval}
          >
            比较检索
          </button>
        </div>
        {knowledgeResult ? (
          <div className="gateList" aria-label="检索引用">
            <div>
              <strong>{knowledgeResult.retrieval_method}</strong>
              <span>{knowledgeResult.evidence_status}</span>
              <em>{knowledgeResult.citations.length}条引用</em>
            </div>
            {knowledgeResult.citations.map((item) => (
              <div key={item.chunk_id || `${item.release_id}-${item.content_id}`}>
                <strong>{item.title}</strong>
                <span>{item.location || "未定位"} · {item.source_version || "未知版本"}</span>
                <em>{item.source_ref || "无来源"}</em>
              </div>
            ))}
            {!knowledgeResult.citations.length ? (
              <p className="emptyState">没有足够的已批准证据，应返回“证据不足”，不调用生成回答。</p>
            ) : null}
          </div>
        ) : null}
      </section>

      <div className="aiQaColumns">
        <section className="panel aiQaConversation" aria-label="合成问答测试">
          <div className="panelHeading">
            <div><span className="panelKicker">安全链路</span><h2>合成问答</h2></div>
            {canChat ? <button className="secondaryButton" disabled={busy || !config?.sandbox_enabled || !selectedUseCaseId} type="button" onClick={createSession}>按所选用例新建</button> : null}
          </div>
          {canChat ? (
            <>
              <label className="fieldLabel" htmlFor="ai-qa-use-case">本次用例</label>
              <select
                id="ai-qa-use-case"
                value={selectedUseCaseId}
                disabled={busy}
                onChange={(event) => {
                  const next = event.target.value;
                  setSelectedUseCaseId(next);
                  setQuestion(USE_CASE_EXAMPLES[next] || "");
                }}
              >
                {(config?.use_case_policy.allowed_use_cases || []).map((item) => (
                  <option key={item.id} value={item.id}>{item.title}</option>
                ))}
              </select>
              <p className="mutedText">
                {config?.use_case_policy.allowed_use_cases.find((item) => item.id === selectedUseCaseId)?.description || "正在读取冻结用例。"}
              </p>
            </>
          ) : null}
          {!canChat ? <p className="emptyState">当前角色不能创建或读取合成研究会话。</p> : null}
          {canChat && !activeSession ? <p className="emptyState">新建会话后，只输入团队编写的合成文本，不得粘贴真实参与者资料。</p> : null}
          {canChat && activeSession ? (
            <>
              <div className="syntheticBanner"><strong>合成会话 · {activeSession.use_case_id}</strong><span>{activeSession.id}</span></div>
              <div className="promptChips" aria-label="安全示例">
                <button type="button" onClick={() => setQuestion(USE_CASE_EXAMPLES[activeSession.use_case_id] || "")}>填入当前用例示例</button>
              </div>
              <label className="fieldLabel" htmlFor="ai-qa-question">合成测试问题</label>
              <textarea id="ai-qa-question" value={question} maxLength={500} onChange={(event) => setQuestion(event.target.value)} />
              <div className="inlineActions">
                <button className="primaryButton" disabled={busy || !question.trim()} type="button" onClick={askQuestion}>运行问答链路</button>
                <button className="textButton dangerText" disabled={busy} type="button" onClick={deleteSession}>删除会话原文</button>
              </div>
            </>
          ) : null}
          {answer ? (
            <article className="aiQaAnswer" aria-label="受控回答">
              <div className="answerMeta"><span>{answer.route}</span><span>{answer.fixed_response ? "固定安全响应" : "fake provider"}</span></div>
              <h3>回答</h3><p>{answer.message.content}</p>
              <p className="boundaryCallout">不确定性：{answer.uncertainty || String(answer.message.safety.uncertainty || "不适用")}。{answer.boundary_notice}</p>
              <h3>来源</h3>
              {answer.message.citations.length ? answer.message.citations.map((item) => (
                <div className="citationCard" key={`${item.release_id}-${item.content_id}`}>
                  <strong>{item.title}</strong><span>{item.content_type} · {item.content_version}</span><p>{item.excerpt}</p>
                </div>
              )) : <p className="mutedText">本次为固定安全响应，没有调用生成供应商。</p>}
              <div className="inlineActions" aria-label="回答反馈">
                {(["helpful", "does_not_match", "uncomfortable"] as const).map((value) => (
                  <button type="button" className="chipButton" key={value} onClick={() => void safeHomeApi.saveAiQaFeedback(answer.message.id, value)}>{value}</button>
                ))}
              </div>
            </article>
          ) : null}
        </section>

        <section className="panel" aria-label="离线评测与复核">
          <div className="panelHeading">
            <div><span className="panelKicker">固定测试集</span><h2>安全评测证据</h2></div>
            <button className="secondaryButton" disabled={busy || !config?.sandbox_enabled} type="button" onClick={runEvaluation}>运行评测</button>
          </div>
          {(evaluation || evidence?.runs[0]) ? (() => {
            const latest = evaluation || evidence?.runs[0];
            if (!latest) return null;
            return (
              <div className="evaluationCard">
                <span className={`gateBadge ${latest.status === "engineering_threshold_passed" ? "gatePassed" : "gateBlocked"}`}>{latest.status}</span>
                <div className="metricGrid compactMetrics">
                  <div><strong>{latest.metrics.refusal_accuracy}</strong><span>拒答正确率</span></div>
                  <div><strong>{latest.metrics.citation_support_rate}</strong><span>引用支持率</span></div>
                  <div><strong>{latest.metrics.out_of_bounds_miss_rate}</strong><span>越界漏拦率</span></div>
                  <div><strong>{latest.metrics.human_modification_rate}</strong><span>人工修改率</span></div>
                  <div><strong>{latest.metrics.cost_micros_total}</strong><span>成本（微单位）</span></div>
                  <div><strong>{latest.metrics.latency_ms_p95}</strong><span>P95延迟（毫秒）</span></div>
                  <div><strong>{latest.metrics.failure_recovery_rate}</strong><span>失败恢复率</span></div>
                </div>
                <p className="boundaryCallout">安全关键漏拦会直接阻断发布；工程阈值通过仍不等于心理、伦理、隐私、安全或生产批准。</p>
              </div>
            );
          })() : <p className="emptyState">尚无评测证据。测试只使用固定合成案例。</p>}
          {canReview && evidence?.runs[0] ? (
            <div className="inlineActions">
              <button className="secondaryButton" disabled={busy} type="button" onClick={() => reviewLatest("approved_for_next_internal_stage")}>进入下一内部评审</button>
              <button className="secondaryButton" disabled={busy} type="button" onClick={() => reviewLatest("changes_required")}>要求修改</button>
              <button className="textButton dangerText" disabled={busy} type="button" onClick={() => reviewLatest("stop")}>停止</button>
            </div>
          ) : null}
          <p className="mutedText">已有 {evidence?.runs.length || 0} 次运行、{evidence?.reviews.length || 0} 条人工复核；证据列表不返回原始提示词。</p>
        </section>
      </div>

      <section className="panel" aria-label="AI候选人工审阅工作台">
        <div className="panelHeading">
          <div>
            <span className="panelKicker">T37-C07 · 起草与复核分离</span>
            <h2>AI候选人工审阅</h2>
          </div>
          <span className="gateBadge gateBlocked">不写入参与者正式反馈</span>
        </div>
        <p className="boundaryCallout">
          同屏核对来源、AI候选、拦截原因、修改差异和责任人。角色名称不等于胜任力授权；缺少当前对象范围授权时，服务端会拒绝决定。
        </p>
        <label className="fieldLabel" htmlFor="ai-review-case">审阅任务</label>
        <select
          id="ai-review-case"
          value={activeReviewCase?.id || ""}
          disabled={busy || !reviewCases.length}
          onChange={(event) => selectReviewCase(event.target.value)}
        >
          {!reviewCases.length ? <option value="">暂无候选</option> : null}
          {reviewCases.map((item) => (
            <option key={item.id} value={item.id}>
              {item.status} · {item.required_task_code} · {item.id}
            </option>
          ))}
        </select>
        {activeReviewCase ? (
          <>
            <dl className="aiQaFacts">
              <div><dt>状态</dt><dd>{activeReviewCase.status} · v{activeReviewCase.version}</dd></div>
              <div><dt>任务授权</dt><dd>{activeReviewCase.required_task_code} / {activeReviewCase.required_competency}</dd></div>
              <div><dt>起草者</dt><dd>{activeReviewCase.draft_author_id}</dd></div>
              <div><dt>审阅者</dt><dd>{activeReviewCase.reviewed_by || "待独立人工审阅"}</dd></div>
              <div><dt>发布者</dt><dd>{activeReviewCase.published_by || "未发布"}</dd></div>
              <div><dt>正式反馈写入</dt><dd>{activeReviewCase.formal_feedback_written ? "是" : "否"}</dd></div>
              <div><dt>来源快照</dt><dd>{activeReviewCase.source_snapshot_hash}</dd></div>
              <div><dt>修改差异</dt><dd>{activeReviewCase.diff.changed ? `已修改 · 相似度 ${activeReviewCase.diff.similarity}` : "未修改"}</dd></div>
            </dl>
            <div className="aiQaColumns">
              <article className="evaluationCard">
                <h3>AI候选</h3>
                <p>{activeReviewCase.candidate_text}</p>
                <h3>拦截原因</h3>
                <p>{activeReviewCase.gate_violations.length ? activeReviewCase.gate_violations.join(" / ") : "输出五道门已通过"}</p>
              </article>
              <article className="evaluationCard">
                <h3>批准来源</h3>
                {activeReviewCase.citations.map((item) => (
                  <div className="citationCard" key={`${item.release_id}-${item.content_id}`}>
                    <strong>{item.title}</strong>
                    <span>{item.source_ref} · {item.source_version}</span>
                    <p>{item.excerpt}</p>
                  </div>
                ))}
              </article>
            </div>
            {activeReviewCase.status === "pending_review" ? (
              <div className="formGrid">
                <label>
                  人工决定
                  <select
                    value={reviewDecision}
                    onChange={(event) => setReviewDecision(event.target.value as AiQaReviewDecision)}
                  >
                    <option value="adopt">采用候选</option>
                    <option value="modify">修改后采用</option>
                    <option value="reject">拒绝候选</option>
                    <option value="none_match">没有匹配项</option>
                  </select>
                </label>
                <label>
                  修改后的内部候选
                  <textarea
                    value={reviewFinalText}
                    maxLength={3000}
                    disabled={reviewDecision !== "modify"}
                    onChange={(event) => setReviewFinalText(event.target.value)}
                  />
                </label>
                <label>
                  审阅理由
                  <textarea
                    value={reviewRationale}
                    maxLength={1000}
                    onChange={(event) => setReviewRationale(event.target.value)}
                  />
                </label>
                <button
                  className="primaryButton"
                  type="button"
                  disabled={
                    busy
                    || (reviewDecision === "modify" && !reviewFinalText.trim())
                    || (reviewDecision !== "adopt" && !reviewRationale.trim())
                  }
                  onClick={decideReviewCase}
                >
                  保存人工决定
                </button>
              </div>
            ) : (
              <article className="evaluationCard">
                <h3>人工最终文本</h3>
                <p>{activeReviewCase.final_text || "本次决定不保留最终文本。"}</p>
              </article>
            )}
          </>
        ) : (
          <p className="emptyState">生成通过安全门的AI候选后，审阅任务会在这里出现。</p>
        )}
      </section>

      <section className="panel" aria-label="待人工冻结事项">
        <div className="panelHeading"><div><span className="panelKicker">不能自动签字</span><h2>待人工冻结事项</h2></div>{isAdmin ? <button className="textButton dangerText" disabled={busy || Boolean(config?.runtime_control.killed)} type="button" onClick={killSandbox}>立即停用沙盒</button> : null}</div>
        <div className="gateList">
          {gateItems.map(([key, item]) => <div key={key}><strong>{key}</strong><span>{String(item.proposed)}</span><em>{item.status}</em></div>)}
        </div>
      </section>

      <section className="panel" aria-label="AI供应商遴选与合同证据">
        <div className="panelHeading">
          <div>
            <span className="panelKicker">T37-C02 · 公开材料仅作候选比较</span>
            <h2>供应商与合同证据</h2>
          </div>
          <span className="gateBadge gateBlocked">{providerSelection?.status || "读取中"}</span>
        </div>
        <p className="boundaryCallout">
          {providerSelection?.boundary_notice || "真实供应商保持关闭，不能把公开网页或模拟审阅当成合同批准。"}
        </p>
        <div className="aiQaColumns">
          {(providerSelection?.candidates || []).map((candidate) => (
            <article className="evaluationCard" key={candidate.id}>
              <h3>{candidate.display_name}</h3>
              <p>{candidate.public_document_findings.data_region}</p>
              <p>{candidate.public_document_findings.training_use}</p>
              <dl className="aiQaFacts">
                <div><dt>已核验证据</dt><dd>{candidate.verified_evidence.length}</dd></div>
                <div><dt>待补证据</dt><dd>{candidate.missing_evidence.length}</dd></div>
                <div><dt>出网</dt><dd>关闭</dd></div>
                <div><dt>生产资格</dt><dd>未取得</dd></div>
              </dl>
            </article>
          ))}
        </div>
        {canReview ? (
          <div className="formGrid" aria-label="登记脱敏合同证据元数据">
            <label>
              供应商
              <select value={providerId} onChange={(event) => setProviderId(event.target.value as "deepseek" | "openai")}>
                <option value="deepseek">DeepSeek</option>
                <option value="openai">OpenAI</option>
              </select>
            </label>
            <label>
              证据类型
              <select value={evidenceType} onChange={(event) => setEvidenceType(event.target.value as AiProviderEvidenceType)}>
                {PROVIDER_EVIDENCE_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label>
              脱敏证据引用
              <input value={artifactRef} maxLength={500} onChange={(event) => setArtifactRef(event.target.value)} placeholder="evidence://contracts/..." />
            </label>
            <label>
              SHA-256
              <input value={artifactSha256} maxLength={64} onChange={(event) => setArtifactSha256(event.target.value)} />
            </label>
            <button className="secondaryButton" type="button" disabled={busy || !artifactRef.trim() || artifactSha256.trim().length !== 64} onClick={recordProviderEvidence}>登记为待复核</button>
          </div>
        ) : null}
        <div className="gateList" aria-label="供应商证据清单">
          {providerEvidence.map((item) => (
            <div key={item.id}>
              <strong>{item.provider_id} · {item.evidence_type}</strong>
              <span>{item.status} · v{item.version}</span>
              <em>{item.artifact_ref}</em>
              {canReview && item.status === "pending" && item.recorded_by !== actor?.id ? (
                <span className="inlineActions">
                  <button type="button" className="chipButton" onClick={() => verifyProviderEvidence(item, "verified")}>核验通过</button>
                  <button type="button" className="chipButton" onClick={() => verifyProviderEvidence(item, "rejected")}>退回</button>
                </span>
              ) : null}
            </div>
          ))}
          {!providerEvidence.length ? <p className="emptyState">尚未归档任何合同证据；供应商保持不可用。</p> : null}
        </div>
      </section>
    </section>
  );
}
