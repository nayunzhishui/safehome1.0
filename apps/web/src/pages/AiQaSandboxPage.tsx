import { useCallback, useEffect, useMemo, useState } from "react";

import type { AiQaAnswer, AiQaConfig, AiQaEvaluationRun, AiQaReviewEvidence, AiQaSession } from "../../../../shared/types/api";
import { getStoredAuthUser } from "../services/authState";
import { safeHomeApi } from "../services/safehomeApi";


const SAFE_EXAMPLES = [
  "训练卡在哪里查看？",
  "情绪很强时为什么先暂停一下？",
  "怎样把今天的记录写得更具体？",
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
  const [evidence, setEvidence] = useState<AiQaReviewEvidence | null>(null);
  const [evaluation, setEvaluation] = useState<AiQaEvaluationRun | null>(null);
  const [question, setQuestion] = useState(SAFE_EXAMPLES[0]);
  const [status, setStatus] = useState("正在读取受控沙盒状态…");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [nextConfig, nextEvidence] = await Promise.all([
      safeHomeApi.getAiQaConfig(),
      safeHomeApi.getAiQaReviewEvidence(),
    ]);
    setConfig(nextConfig);
    setEvidence(nextEvidence);
    if (canChat) {
      const listed = await safeHomeApi.listAiQaSessions();
      setSessions(listed.items);
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
    void run("创建合成会话", async () => {
      const created = await safeHomeApi.createAiQaSession();
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
          <div><dt>供应商</dt><dd>{config?.provider || "—"}（不出网）</dd></div>
          <div><dt>超时与重试</dt><dd>{config?.provider_policy ? `${config.provider_policy.timeout_ms}ms / ${config.provider_policy.max_retries}次` : "等待新版本服务"}</dd></div>
          <div><dt>跨会话记忆</dt><dd>关闭</dd></div>
          <div><dt>写操作工具</dt><dd>禁止</dd></div>
          <div><dt>合成原文保留</dt><dd>{config?.data_policy.synthetic_retention_days ? `${config.data_policy.synthetic_retention_days}天` : "待服务更新"}</dd></div>
          <div><dt>训练使用</dt><dd>禁止</dd></div>
        </dl>
      </section>

      <div className="aiQaColumns">
        <section className="panel aiQaConversation" aria-label="合成问答测试">
          <div className="panelHeading">
            <div><span className="panelKicker">安全链路</span><h2>合成问答</h2></div>
            {canChat ? <button className="secondaryButton" disabled={busy || !config?.sandbox_enabled} type="button" onClick={createSession}>新建会话</button> : null}
          </div>
          {!canChat ? <p className="emptyState">当前角色不能创建或读取合成研究会话。</p> : null}
          {canChat && !activeSession ? <p className="emptyState">新建会话后，只输入团队编写的合成文本，不得粘贴真实参与者资料。</p> : null}
          {canChat && activeSession ? (
            <>
              <div className="syntheticBanner"><strong>合成会话</strong><span>{activeSession.id}</span></div>
              <div className="promptChips" aria-label="安全示例">
                {SAFE_EXAMPLES.map((item) => <button type="button" key={item} onClick={() => setQuestion(item)}>{item}</button>)}
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
                  <div><strong>{latest.metrics.route_accuracy}</strong><span>路由准确率</span></div>
                  <div><strong>{latest.metrics.critical_failures}</strong><span>关键失败</span></div>
                  <div><strong>{latest.metrics.citation_coverage}</strong><span>引用覆盖</span></div>
                  <div><strong>{latest.metrics.diagnostic_violations}</strong><span>诊断违规</span></div>
                </div>
                <p className="boundaryCallout">工程阈值通过不等于心理、伦理、隐私、安全或生产批准。</p>
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

      <section className="panel" aria-label="待人工冻结事项">
        <div className="panelHeading"><div><span className="panelKicker">不能自动签字</span><h2>待人工冻结事项</h2></div>{isAdmin ? <button className="textButton dangerText" disabled={busy || Boolean(config?.runtime_control.killed)} type="button" onClick={killSandbox}>立即停用沙盒</button> : null}</div>
        <div className="gateList">
          {gateItems.map(([key, item]) => <div key={key}><strong>{key}</strong><span>{String(item.proposed)}</span><em>{item.status}</em></div>)}
        </div>
      </section>
    </section>
  );
}
