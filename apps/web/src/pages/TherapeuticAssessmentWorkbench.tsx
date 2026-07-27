import { useEffect, useMemo, useState } from "react";

import type {
  TherapeuticAssessmentCase,
  TherapeuticAssessmentEvidenceItem,
  TherapeuticAssessmentEvidenceKind,
  TherapeuticAssessmentResearcherDraft,
  TherapeuticAssessmentResearcherWorkbench as WorkbenchPayload,
} from "../../../../shared/types/api";
import { safeHomeApi, SafeHomeApiError } from "../services/safehomeApi";


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

const kindLabels: Record<TherapeuticAssessmentEvidenceKind, string> = {
  O: "观察",
  P: "模式候选",
  H: "人工假设",
  U: "未知项",
};

type Filters = TherapeuticAssessmentResearcherDraft["filters"];

function textList(items: unknown[]) {
  return items.map((item) => {
    if (typeof item === "string") return item;
    if (!item || typeof item !== "object") return "";
    const record = item as Record<string, unknown>;
    const reference = typeof record.ref === "string" ? record.ref : "";
    const source = typeof record.source === "string" ? record.source : "";
    return [reference, source].filter(Boolean).join(" · ") || "结构化资料";
  }).filter(Boolean);
}

function EvidenceCard({ item }: { item: TherapeuticAssessmentEvidenceItem }) {
  const metadata = [
    item.source_ref ? `来源：${item.source_ref}` : "",
    item.observed_at ? `时间：${item.observed_at}` : "",
    item.provider_id ? `提供者：${item.provider_id}` : "",
    item.context ? `情境：${item.context}` : "",
    `权限：${item.visibility_scope.join("、")}`,
  ].filter(Boolean);
  return (
    <article className={`taEvidenceCard taEvidence-${item.kind}`}>
      <header>
        <span className="taKindBadge">{item.kind} · {kindLabels[item.kind]}</span>
        <span>{item.review_status}</span>
      </header>
      <p className="taEvidenceContent">{item.content}</p>
      <dl className="taEvidenceMeta">
        {metadata.map((entry) => <div key={entry}><dt>资料</dt><dd>{entry}</dd></div>)}
        <div><dt>方法限制</dt><dd>{item.method_limitations}</dd></div>
        {item.question_link ? <div><dt>关联问题</dt><dd>{item.question_link}</dd></div> : null}
      </dl>
      {item.kind === "H" ? (
        <div className="taHypothesisGrid" aria-label="人工假设核对">
          <section><strong>支持依据</strong>{textList(item.supporting_evidence).map((value) => <p key={value}>{value}</p>)}</section>
          <section><strong>反证</strong>{item.counter_evidence.map((value) => <p key={value}>{value}</p>)}</section>
          <section><strong>其它可能</strong>{item.alternative_explanations.map((value) => <p key={value}>{value}</p>)}</section>
          <section><strong>参与者识别</strong><p>{item.participant_recognition || "尚未核对"}</p></section>
        </div>
      ) : null}
      {item.kind === "U" ? <p className="taUncertainty">未知类型：{item.uncertainty_type}</p> : null}
    </article>
  );
}

export function TherapeuticAssessmentWorkbench() {
  const [cases, setCases] = useState<TherapeuticAssessmentCase[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [workbench, setWorkbench] = useState<WorkbenchPayload | null>(null);
  const [filters, setFilters] = useState<Filters>({});
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [internalNotes, setInternalNotes] = useState("");
  const [participantVisibleDraft, setParticipantVisibleDraft] = useState("");
  const [feedbackLayer, setFeedbackLayer] = useState<"layer_1" | "layer_2">("layer_1");
  const [letterTitle, setLetterTitle] = useState("给你的阶段性反馈");
  const [lifecycleNote, setLifecycleNote] = useState("");
  const selected = useMemo(
    () => cases.find((item) => item.id === selectedId) || cases[0],
    [cases, selectedId],
  );
  const latestFeedback = useMemo(
    () => selected?.feedback_versions?.slice(-1)[0] || null,
    [selected],
  );

  const loadCases = async () => {
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

  const loadWorkbench = async (caseId: string, nextFilters = filters, nextPage = page) => {
    setLoadingEvidence(true);
    setError("");
    try {
      const result = await safeHomeApi.getTherapeuticAssessmentResearcherWorkbench(caseId, {
        ...nextFilters,
        page: nextPage,
        page_size: 8,
      });
      setWorkbench(result);
      setInternalNotes(result.draft.internal_notes);
      setParticipantVisibleDraft(result.draft.participant_visible_draft);
    } catch (caught) {
      setWorkbench(null);
      setError(caught instanceof SafeHomeApiError ? caught.message : "证据工作台暂时无法读取。");
    } finally {
      setLoadingEvidence(false);
    }
  };

  useEffect(() => {
    void loadCases();
  }, []);

  useEffect(() => {
    if (selectedId) void loadWorkbench(selectedId, filters, page);
  }, [selectedId, filters.kind, filters.review_status, filters.visibility, page]);

  const changeFilter = (name: keyof Filters, value: string) => {
    setFilters((current) => ({ ...current, [name]: value }));
    setPage(1);
  };

  const saveDraft = async () => {
    if (!selected || !workbench) return;
    setSaving(true);
    setError("");
    try {
      const draft = await safeHomeApi.saveTherapeuticAssessmentResearcherDraft(
        selected.id,
        {
          internal_notes: internalNotes,
          participant_visible_draft: participantVisibleDraft,
          filters,
          expected_version: workbench.draft.version,
        },
        `web-ta-workbench-${selected.id}-${Date.now()}`,
      );
      setWorkbench({ ...workbench, draft });
      setNotice("工作台草稿已保存；内部备注不会出现在参与者端。");
    } catch (caught) {
      setError(caught instanceof SafeHomeApiError ? caught.message : "工作台草稿保存失败。");
    } finally {
      setSaving(false);
    }
  };

  const createFeedbackDraft = async () => {
    if (!selected || !participantVisibleDraft.trim()) {
      setError("请先填写参与者可见草稿。");
      return;
    }
    const evidenceRefs = workbench?.evidence_items.map((item) => item.source_ref || item.id) || [];
    if (!evidenceRefs.length) {
      setError("当前没有可核对依据，不能提交正式反馈草稿。");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await safeHomeApi.createTherapeuticAssessmentFeedback(
        selected.id,
        {
          source: "human",
          feedback_layer: feedbackLayer,
          recipient_user_id: selected.participant_user_id,
          letter_title: letterTitle,
          observations: ["已依据当前授权资料整理"],
          evidence: evidenceRefs,
          alternatives: ["当前理解仍可随参与者核对和新资料修订"],
          uncertainty: "仅基于当前已授权资料",
          next_step: "与参与者共同核对这份草稿",
          human_discussion: internalNotes ? [internalNotes] : [],
          participant_content: participantVisibleDraft,
        },
        `web-ta-feedback-${selected.id}-${Date.now()}`,
      );
      setNotice("已创建正式反馈草稿，仍需另一位人工复核后才能发送。");
      await loadCases();
    } catch (caught) {
      setError(caught instanceof SafeHomeApiError ? caught.message : "正式反馈草稿创建失败。");
    } finally {
      setSaving(false);
    }
  };

  const runFeedbackAction = async (action: "review" | "send" | "revise" | "withdraw" | "resend") => {
    if (!latestFeedback) return;
    setSaving(true);
    setError("");
    try {
      const key = `web-ta-${action}-${latestFeedback.id}-${Date.now()}`;
      if (action === "review") {
        await safeHomeApi.reviewTherapeuticAssessmentFeedback(latestFeedback.id, "approved", key);
      } else if (action === "send") {
        await safeHomeApi.sendTherapeuticAssessmentFeedback(latestFeedback.id, key);
      } else if (action === "revise") {
        await safeHomeApi.reviseTherapeuticAssessmentFeedback(
          latestFeedback.id,
          {
            expected_lifecycle_version: latestFeedback.lifecycle_version,
            revision_reason: lifecycleNote || "根据参与者核对结果修订",
            feedback_layer: latestFeedback.feedback_layer === "layer_2" ? "layer_2" : "layer_1",
            participant_content: participantVisibleDraft || latestFeedback.participant_content,
            letter_title: letterTitle || latestFeedback.letter_title,
          },
          key,
        );
      } else if (action === "withdraw") {
        await safeHomeApi.withdrawTherapeuticAssessmentFeedback(
          latestFeedback.id,
          {
            expected_lifecycle_version: latestFeedback.lifecycle_version,
            reason: lifecycleNote || "内容需要修订，暂时撤回",
          },
          key,
        );
      } else {
        await safeHomeApi.resendTherapeuticAssessmentFeedback(latestFeedback.id, key);
      }
      setNotice("反馈生命周期操作已记录。");
      await loadCases();
    } catch (caught) {
      setError(caught instanceof SafeHomeApiError ? caught.message : "反馈生命周期操作失败。");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="dashboardShell therapeuticAssessmentWorkbench" aria-labelledby="ta-title">
      <header className="dashboardHeader taWorkbenchHeader">
        <div>
          <p className="eyebrow">人工主导 · 证据可追溯</p>
          <h1 id="ta-title">协作式评估工作台 · 证据时间线</h1>
          <p className="summary">从参与者的问题出发，按时间查看资料、反证和未知项，再分别保存内部记录与参与者可见草稿。</p>
        </div>
        <button className="secondaryButton" type="button" onClick={() => void loadCases()} disabled={loading}>重新同步</button>
      </header>

      {error ? <div className="status error" role="alert">{error}</div> : null}
      {notice ? <div className="status success" role="status">{notice}</div> : null}

      <div className="taWorkspaceGrid">
        <aside className="panel taCaseRail" aria-label="参与者问题">
          <div className="sectionHeader"><div><p className="eyebrow">对象范围</p><h2>参与者问题</h2></div></div>
          {loading ? <p>正在读取…</p> : null}
          {!loading && !cases.length ? <div className="emptyState"><strong>暂无协作记录</strong><p>参与者提交并同意共享后会出现在这里。</p></div> : null}
          <div className="taCaseList">
            {cases.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`taCaseButton ${selected?.id === item.id ? "active" : ""}`}
                onClick={() => { setSelectedId(item.id); setPage(1); }}
              >
                <strong>{item.assessment_question}</strong>
                <span>{workflowLabels[item.workflow_state] || item.workflow_state} · {item.service_level.display_name}</span>
              </button>
            ))}
          </div>
        </aside>

        <main className="panel taEvidenceWorkspace" aria-label="证据时间线">
          {selected ? (
            <>
              <section className="taQuestionFocus">
                <div><p className="eyebrow">{selected.service_level.display_name} · 当前议题 · 版本 {selected.version}</p><h2>{selected.working_question || selected.assessment_question}</h2></div>
                <span className={`statusPill status-${selected.status}`}>{workflowLabels[selected.workflow_state] || selected.workflow_state}</span>
                <p>共享范围：{selected.shared_scope.join("、")}；共同理解：{selected.hypothesis_state}；安全支持：{selected.safety_state}</p>
              </section>

              <section className="taFilterBar" aria-label="证据过滤">
                <label>类型<select value={filters.kind || ""} onChange={(event) => changeFilter("kind", event.target.value)}>
                  <option value="">全部</option>{Object.entries(kindLabels).map(([value, label]) => <option key={value} value={value}>{value} · {label}</option>)}
                </select></label>
                <label>发布状态<select value={filters.review_status || ""} onChange={(event) => changeFilter("review_status", event.target.value)}>
                  <option value="">全部</option><option value="draft">草稿</option><option value="human_reviewed">人工已复核</option><option value="changes_requested">待修订</option><option value="participant_checked">参与者已核对</option>
                </select></label>
                <label>可见范围<select value={filters.visibility || ""} onChange={(event) => changeFilter("visibility", event.target.value)}>
                  <option value="">全部</option><option value="participant">参与者可见</option><option value="research_team">研究团队</option><option value="supervisor">督导</option>
                </select></label>
              </section>

              {loadingEvidence ? <div className="status" role="status">正在读取这一页证据…</div> : null}
              {!loadingEvidence && !workbench?.evidence_items.length ? <div className="emptyState"><strong>当前条件下没有证据</strong><p>可调整过滤条件，或先记录具体观察和未知项。</p></div> : null}
              <div className="taEvidenceTimeline">
                {workbench?.evidence_items.map((item) => <EvidenceCard key={item.id} item={item} />)}
              </div>
              {workbench && workbench.evidence_total > workbench.page_size ? (
                <nav className="taPagination" aria-label="证据分页">
                  <button type="button" className="secondaryButton" disabled={page === 1 || loadingEvidence} onClick={() => setPage((value) => value - 1)}>上一页</button>
                  <span>第 {page} 页 · 共 {workbench.evidence_total} 条</span>
                  <button type="button" className="secondaryButton" disabled={!workbench.has_more || loadingEvidence} onClick={() => setPage((value) => value + 1)}>下一页</button>
                </nav>
              ) : null}

              <section className="taDraftSeparation" aria-label="起草区">
                <label className="taInternalDraft">
                  <span><strong>内部工作备注</strong><small>仅研究团队可见，不会发送给参与者</small></span>
                  <textarea value={internalNotes} onChange={(event) => setInternalNotes(event.target.value)} rows={7} />
                </label>
                <label className="taParticipantDraft">
                  <span><strong>参与者可见草稿</strong><small>提交正式草稿后仍需独立人工复核</small></span>
                  <textarea value={participantVisibleDraft} onChange={(event) => setParticipantVisibleDraft(event.target.value)} rows={7} />
                </label>
              </section>
              <section className="taFeedbackComposition" aria-label="反馈层级和书面信">
                <label>反馈层级
                  <select value={feedbackLayer} onChange={(event) => setFeedbackLayer(event.target.value as "layer_1" | "layer_2")}>
                    <option value="layer_1">第一层 · 与当前理解一致</option>
                    <option value="layer_2">第二层 · 可讨论的新连接</option>
                  </select>
                </label>
                <label>书面信标题
                  <input value={letterTitle} maxLength={120} onChange={(event) => setLetterTitle(event.target.value)} />
                </label>
                <p>第三层挑战性内容不进入数字自动流程，需要在线下人工协作中处理。</p>
              </section>
              <div className="dashboardActions">
                <button className="secondaryButton" type="button" disabled={saving || !workbench} onClick={() => void saveDraft()}>保存工作台草稿</button>
                <button className="primaryButton" type="button" disabled={saving || !workbench} onClick={() => void createFeedbackDraft()}>提交为待复核反馈</button>
              </div>
              <section className="taFeedbackLifecycle" aria-label="反馈生命周期">
                <div className="sectionHeader"><div><p className="eyebrow">最新反馈版本</p><h2>复核、修订与撤回</h2></div></div>
                {!latestFeedback ? <p>尚未创建反馈版本。</p> : (
                  <>
                    <p><strong>{latestFeedback.letter_title}</strong> · {latestFeedback.feedback_layer === "layer_2" ? "可讨论的新连接" : "与当前理解一致"} · {latestFeedback.status}</p>
                    {latestFeedback.participant_responses?.length ? (
                      <p>参与者最近核对：{latestFeedback.participant_responses.slice(-1)[0].recognition}；异议原文会保留。</p>
                    ) : <p>参与者尚未核对。</p>}
                    <label>操作依据
                      <input value={lifecycleNote} onChange={(event) => setLifecycleNote(event.target.value)} placeholder="写明修订或撤回原因" />
                    </label>
                    <div className="dashboardActions">
                      <button type="button" className="secondaryButton" disabled={saving || latestFeedback.status !== "draft"} onClick={() => void runFeedbackAction("review")}>人工复核</button>
                      <button type="button" className="primaryButton" disabled={saving || latestFeedback.status !== "reviewed"} onClick={() => void runFeedbackAction("send")}>发送</button>
                      <button type="button" className="secondaryButton" disabled={saving} onClick={() => void runFeedbackAction("revise")}>新建修订版</button>
                      <button type="button" className="secondaryButton" disabled={saving || latestFeedback.status === "withdrawn"} onClick={() => void runFeedbackAction("withdraw")}>撤回</button>
                      <button type="button" className="secondaryButton" disabled={saving || latestFeedback.status !== "sent"} onClick={() => void runFeedbackAction("resend")}>重新发送</button>
                    </div>
                  </>
                )}
              </section>
              <section className="taFeedbackLifecycle" aria-label="参与者小行动与随访">
                <div className="sectionHeader">
                  <div>
                    <p className="eyebrow">参与者自选</p>
                    <h2>小行动与回看</h2>
                  </div>
                </div>
                {!selected.actions.length ? <p>参与者尚未选择小行动。</p> : selected.actions.map((action) => (
                  <article className="evidenceCard" key={action.id}>
                    <p><strong>{action.action_text}</strong> · {action.status}</p>
                    <p>{action.purpose_text}</p>
                    <p>停止条件：{action.stop_conditions.join("；")}</p>
                    <p>未完成时：{action.setback_plan}</p>
                    {action.followup_note ? <p>参与者回看：{action.followup_note}</p> : null}
                    <small>完成与否只记录参与过程，不作为疗效或能力评价。</small>
                  </article>
                ))}
              </section>
            </>
          ) : <div className="emptyState"><strong>请选择一条协作记录</strong></div>}
        </main>
      </div>

      <aside className="guidanceBox" aria-label="使用边界">
        <strong>使用边界</strong>
        <p>证据工作台用于共同理解和人工讨论，不生成诊断、人格标签或疗效分数。临时展示权限不能替代正式对象授权。</p>
      </aside>
    </section>
  );
}
