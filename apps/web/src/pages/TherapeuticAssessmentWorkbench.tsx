import { useEffect, useMemo, useState } from "react";

import type { TherapeuticAssessmentCase } from "../../../../shared/types/api";
import { safeHomeApi, SafeHomeApiError } from "../services/safehomeApi";


function lines(value: string) {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

const workflowLabels: Record<string, string> = {
  submitted: "已提交",
  pending_human_review: "待人工复核",
  needs_more_info: "待补充资料",
  feedback_ready: "可整理反馈",
  feedback_draft: "反馈草稿",
  professional_review: "待专业复核",
  participant_check: "待参与者核对",
  revision_requested: "待修订",
  action_selected: "已选择小行动",
  followup: "随访中",
  safety_path: "人工安全支持",
  not_applicable: "本轮不适用",
  archived: "已归档",
  withdrawn: "已撤回",
};

export function TherapeuticAssessmentWorkbench() {
  const [cases, setCases] = useState<TherapeuticAssessmentCase[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [form, setForm] = useState({
    observations: "",
    evidence: "",
    alternatives: "",
    uncertainty: "",
    nextStep: "",
    discussion: "",
    participantContent: "",
  });
  const selected = useMemo(() => cases.find((item) => item.id === selectedId) || cases[0], [cases, selectedId]);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await safeHomeApi.listTherapeuticAssessmentCases();
      setCases(result.items);
      if (!selectedId && result.items[0]) setSelectedId(result.items[0].id);
    } catch (caught) {
      setError(caught instanceof SafeHomeApiError ? caught.message : "协作记录暂时无法读取。");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const draft = async () => {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      await safeHomeApi.createTherapeuticAssessmentFeedback(
        selected.id,
        {
          source: "human",
          observations: lines(form.observations),
          evidence: lines(form.evidence),
          alternatives: lines(form.alternatives),
          uncertainty: form.uncertainty,
          next_step: form.nextStep,
          human_discussion: lines(form.discussion),
          participant_content: form.participantContent,
        },
        `web-ta-draft-${selected.id}-${Date.now()}`,
      );
      setNotice("草稿已保存。它还没有发送，需要督导或管理员人工复核。");
      await load();
    } catch (caught) {
      setError(caught instanceof SafeHomeApiError ? caught.message : "草稿保存失败。");
    } finally {
      setSaving(false);
    }
  };

  const actOnFeedback = async (feedbackId: string, action: "review" | "send") => {
    setSaving(true);
    setError("");
    try {
      if (action === "review") {
        await safeHomeApi.reviewTherapeuticAssessmentFeedback(feedbackId, "approved", `web-ta-review-${feedbackId}-${Date.now()}`);
        setNotice("人工复核已记录。");
      } else {
        await safeHomeApi.sendTherapeuticAssessmentFeedback(feedbackId, `web-ta-send-${feedbackId}-${Date.now()}`);
        setNotice("已发送给参与者，并保留版本和审计记录。");
      }
      await load();
    } catch (caught) {
      setError(caught instanceof SafeHomeApiError ? caught.message : "操作未完成。");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="dashboardShell therapeuticAssessmentWorkbench" aria-labelledby="ta-title">
      <header className="dashboardHeader">
        <div>
          <p className="eyebrow">人工主导 · 共同理解</p>
          <h1 id="ta-title">协作式评估工作台</h1>
          <p className="summary">从参与者的问题出发，明确共享范围，形成可讨论的版本化反馈，再共同选择一个低压力的小行动。</p>
        </div>
        <button className="secondaryButton" type="button" onClick={() => void load()} disabled={loading}>重新同步</button>
      </header>

      <div className="summaryGrid" aria-label="协作状态摘要">
        <article className="metricCard"><span>协作记录</span><strong>{cases.length}</strong><small>按对象范围读取</small></article>
        <article className="metricCard"><span>待人工复核</span><strong>{cases.reduce((sum, item) => sum + item.feedback_versions.filter((version) => version.status === "draft").length, 0)}</strong><small>AI 只能生成草稿</small></article>
        <article className="metricCard"><span>已发送版本</span><strong>{cases.reduce((sum, item) => sum + item.feedback_versions.filter((version) => version.status === "sent").length, 0)}</strong><small>参与者可不同意或撤回</small></article>
      </div>

      {error ? <div className="status error" role="alert">{error}</div> : null}
      {notice ? <div className="status success" role="status">{notice}</div> : null}
      {loading ? <div className="status">正在读取协作记录…</div> : null}

      <div className="taWorkspaceGrid">
        <section className="panel" aria-label="协作记录列表">
          <div className="sectionHeader"><div><p className="eyebrow">对象范围</p><h2>参与者问题</h2></div></div>
          {!loading && !cases.length ? <div className="emptyState"><strong>暂无协作记录</strong><p>参与者提交问题并同意共享范围后，会出现在这里。</p></div> : null}
          <div className="taCaseList">
            {cases.map((item) => (
              <button type="button" key={item.id} className={`taCaseButton ${selected?.id === item.id ? "active" : ""}`} onClick={() => setSelectedId(item.id)}>
                <strong>{item.assessment_question}</strong>
                <span>{workflowLabels[item.workflow_state] || item.workflow_state} · {item.service_level.display_name}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="panel" aria-label="结构化反馈工作区">
          {selected ? (
            <>
              <div className="sectionHeader">
                <div><p className="eyebrow">{selected.service_level.display_name} · 版本 {selected.version}</p><h2>结构化共同反馈</h2></div>
                <span className={`statusPill status-${selected.status}`}>{workflowLabels[selected.workflow_state] || selected.workflow_state}</span>
              </div>
              <div className="guidanceBox">
                <strong>参与者的问题</strong>
                <p>{selected.assessment_question}</p>
                <small>共享范围：{selected.shared_scope.join("、")}；复杂范围：{selected.complexity_scope}</small>
                <small>共同理解：{selected.hypothesis_state}；安全支持：{selected.safety_state}</small>
              </div>
              <div className="taFormGrid">
                <label><span>观察（每行一条）</span><textarea value={form.observations} onChange={(event) => setForm({ ...form, observations: event.target.value })} /></label>
                <label><span>依据（每行一条）</span><textarea value={form.evidence} onChange={(event) => setForm({ ...form, evidence: event.target.value })} /></label>
                <label><span>其它可能（每行一条）</span><textarea value={form.alternatives} onChange={(event) => setForm({ ...form, alternatives: event.target.value })} /></label>
                <label><span>不确定性</span><textarea value={form.uncertainty} onChange={(event) => setForm({ ...form, uncertainty: event.target.value })} /></label>
                <label><span>建议讨论的问题</span><textarea value={form.discussion} onChange={(event) => setForm({ ...form, discussion: event.target.value })} /></label>
                <label><span>下一小步</span><textarea value={form.nextStep} onChange={(event) => setForm({ ...form, nextStep: event.target.value })} /></label>
                <label className="taWideField"><span>参与者可见版本</span><textarea value={form.participantContent} onChange={(event) => setForm({ ...form, participantContent: event.target.value })} /></label>
              </div>
              <button className="primaryButton" type="button" disabled={saving} onClick={() => void draft()}>保存为待人工复核草稿</button>
              <div className="taVersionList">
                {selected.feedback_versions.map((version) => (
                  <article className="taVersionCard" key={version.id}>
                    <div><strong>第 {version.version_no} 版</strong><span>{version.source === "ai_draft" ? "AI 草稿" : "人工草稿"} · {version.status}</span></div>
                    <p>{version.participant_content}</p>
                    <small>不确定性：{version.uncertainty}</small>
                    <div className="dashboardActions">
                      {version.status === "draft" ? <button className="secondaryButton" type="button" disabled={saving} onClick={() => void actOnFeedback(version.id, "review")}>人工复核通过</button> : null}
                      {version.status === "reviewed" ? <button className="primaryButton" type="button" disabled={saving} onClick={() => void actOnFeedback(version.id, "send")}>发送给参与者</button> : null}
                    </div>
                  </article>
                ))}
              </div>
            </>
          ) : <div className="emptyState"><strong>请选择一条协作记录</strong></div>}
        </section>
      </div>

      <aside className="guidanceBox" aria-label="协作式评估边界">
        <strong>使用边界</strong>
        <p>儿童、伴侣、多方关系、高风险和诊断性范围继续受 D01–D26 资格、督导与伦理门禁约束。L0/L1 不能确认或发送，临时展示权限不能替代正式对象授权。</p>
        <p>成长仪表盘只记录变化、讨论和行动线索，不生成疗效分数。</p>
      </aside>
    </section>
  );
}
