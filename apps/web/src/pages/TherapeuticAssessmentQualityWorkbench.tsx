import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  TherapeuticAssessmentProductionGate,
  TherapeuticAssessmentQualityDimension,
  TherapeuticAssessmentQualityIncident,
  TherapeuticAssessmentQualityReview,
  TherapeuticAssessmentQualityRuntime,
} from "../../../../shared/types/api";
import { safeHomeApi } from "../services/safehomeApi";


const dimensionLabels: Record<TherapeuticAssessmentQualityDimension, string> = {
  question_quality: "问题是否清楚且可探索",
  evidence_sufficiency: "依据是否足够且可追溯",
  authorization: "人员与对象范围是否已授权",
  language: "表达是否非诊断、非评判",
  participant_recognition: "是否保留参与者的不同理解",
  action_fit: "下一步是否具体、可退出且适配",
};

const dimensions = Object.keys(dimensionLabels) as TherapeuticAssessmentQualityDimension[];

type DimensionDraft = Record<
  TherapeuticAssessmentQualityDimension,
  { status: "pass" | "concern" | "not_applicable"; note: string; evidence_ref: string }
>;

function newDimensionDraft(): DimensionDraft {
  return Object.fromEntries(
    dimensions.map((name) => [name, { status: "pass", note: "", evidence_ref: "" }]),
  ) as DimensionDraft;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "服务暂时没有响应，请稍后重试。";
}

export function TherapeuticAssessmentQualityWorkbench() {
  const [reviews, setReviews] = useState<TherapeuticAssessmentQualityReview[]>([]);
  const [incidents, setIncidents] = useState<TherapeuticAssessmentQualityIncident[]>([]);
  const [runtime, setRuntime] = useState<TherapeuticAssessmentQualityRuntime | null>(null);
  const [productionGate, setProductionGate] = useState<TherapeuticAssessmentProductionGate | null>(null);
  const [selectedReviewId, setSelectedReviewId] = useState("");
  const [selectedIncidentId, setSelectedIncidentId] = useState("");
  const [dimensionDraft, setDimensionDraft] = useState<DimensionDraft>(newDimensionDraft);
  const [remediationSummary, setRemediationSummary] = useState("");
  const [impactSummary, setImpactSummary] = useState("");
  const [resolutionSummary, setResolutionSummary] = useState("");
  const [resolutionAction, setResolutionAction] = useState<"no_change" | "withdraw">("no_change");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [reviewResult, incidentResult, gateResult] = await Promise.all([
        safeHomeApi.listTherapeuticAssessmentQualityReviews({ page_size: 100 }),
        safeHomeApi.listTherapeuticAssessmentQualityIncidents(),
        safeHomeApi.getTherapeuticAssessmentProductionGate(),
      ]);
      setReviews(reviewResult.items);
      setRuntime(reviewResult.runtime);
      setIncidents(incidentResult.items);
      setProductionGate(gateResult);
      setSelectedReviewId((current) =>
        reviewResult.items.some((item) => item.id === current)
          ? current
          : reviewResult.items[0]?.id || "",
      );
      setSelectedIncidentId((current) =>
        incidentResult.items.some((item) => item.id === current)
          ? current
          : incidentResult.items[0]?.id || "",
      );
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedReview = reviews.find((item) => item.id === selectedReviewId) || null;
  const selectedIncident = incidents.find((item) => item.id === selectedIncidentId) || null;
  const hasConcern = useMemo(
    () => dimensions.some((name) => dimensionDraft[name].status === "concern"),
    [dimensionDraft],
  );

  const claim = async () => {
    if (!selectedReview) return;
    setSaving(true);
    setError("");
    try {
      await safeHomeApi.claimTherapeuticAssessmentQualityReview(
        selectedReview.id,
        selectedReview.version,
        `quality-claim-${selectedReview.id}-${Date.now()}`,
      );
      setNotice("已认领。请逐项核对后提交结论。");
      await load();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSaving(false);
    }
  };

  const complete = async () => {
    if (!selectedReview) return;
    setSaving(true);
    setError("");
    try {
      await safeHomeApi.completeTherapeuticAssessmentQualityReview(
        selectedReview.id,
        {
          expected_version: selectedReview.version,
          dimensions: dimensionDraft,
          decision: hasConcern ? "remediation_required" : "pass",
          remediation_summary: hasConcern ? remediationSummary : undefined,
        },
        `quality-complete-${selectedReview.id}-${Date.now()}`,
      );
      setNotice(hasConcern ? "已转入独立修复流程，原记录会被保留。" : "质量复核已通过。");
      setDimensionDraft(newDimensionDraft());
      setRemediationSummary("");
      await load();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSaving(false);
    }
  };

  const analyzeIncident = async () => {
    if (!selectedIncident || !impactSummary.trim()) return;
    setSaving(true);
    setError("");
    try {
      await safeHomeApi.analyzeTherapeuticAssessmentQualityIncident(
        selectedIncident.id,
        {
          expected_version: selectedIncident.version,
          impact_analysis: {
            severity: "medium",
            affected_scope: "single_case",
            affected_participant_count: 1,
            immediate_action: impactSummary.trim(),
            evidence_refs: [
              selectedIncident.feedback_id
                ? `feedback:${selectedIncident.feedback_id}`
                : `case:${selectedIncident.case_id}`,
            ],
          },
        },
        `quality-analysis-${selectedIncident.id}-${Date.now()}`,
      );
      setNotice("影响分析已保存，等待另一位人员独立结案。");
      setImpactSummary("");
      await load();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSaving(false);
    }
  };

  const resolveIncident = async () => {
    if (!selectedIncident || !resolutionSummary.trim()) return;
    setSaving(true);
    setError("");
    try {
      await safeHomeApi.resolveTherapeuticAssessmentQualityIncident(
        selectedIncident.id,
        {
          expected_version: selectedIncident.version,
          resolution_action: resolutionAction,
          resolution_summary: resolutionSummary.trim(),
        },
        `quality-resolution-${selectedIncident.id}-${Date.now()}`,
      );
      setNotice("处理结果已保存，并已向参与者发送站内通知。");
      setResolutionSummary("");
      await load();
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="qualityWorkbench" aria-labelledby="quality-title">
      <header className="qualityHero">
        <div>
          <p className="pageEyebrow">治疗性评估 · 质量监督</p>
          <h1 id="quality-title">把抽检、修复和通知放在同一条责任链上</h1>
          <p>这里只核对问题、依据、授权、语言、参与者识别与行动适配，不生成诊断或疗效结论。</p>
        </div>
        <button className="secondaryButton" type="button" onClick={() => void load()} disabled={loading}>
          重新读取
        </button>
      </header>

      {runtime ? (
        <div className={`qualityRuntime ${runtime.paused ? "qualityRuntime--paused" : ""}`} role="status">
          <strong>{runtime.paused ? "新协作记录已自动暂停" : "质量队列在承诺范围内"}</strong>
          <span>待处理 {runtime.pending_count} · 已超时 {runtime.overdue_count} · 规则 {runtime.policy_version}</span>
        </div>
      ) : null}
      {error ? <div className="formError" role="alert">{error}</div> : null}
      {notice ? <div className="qualityNotice" role="status">{notice}</div> : null}

      {productionGate ? (
        <section className="qualityPanel productionGatePanel" aria-labelledby="production-gate-title">
          <div className="qualitySectionHeading">
            <div>
              <p className="pageEyebrow">生产门禁</p>
              <h2 id="production-gate-title">
                {productionGate.status === "blocked" ? "当前不可发布" : "等待负责人最终批准"}
              </h2>
            </div>
            <span>{productionGate.policy_version}</span>
          </div>
          <div className="productionGateChecks" role="list">
            {([
              ["engineering_content", "工程与内容"],
              ["human_evidence", "人工证据"],
              ["workforce_duty", "人员与值守"],
              ["privacy_recovery", "隐私与恢复"],
              ["infrastructure_release", "基础设施"],
            ] as const).map(([name, label]) => (
              <div
                key={name}
                className={`productionGateCheck ${productionGate.checks[name].passed ? "isPassed" : ""}`}
                role="listitem"
              >
                <strong>{label}</strong>
                <span>
                  {productionGate.checks[name].passed
                    ? "已具备证据"
                    : `缺少 ${productionGate.checks[name].missing.length} 项`}
                </span>
              </div>
            ))}
          </div>
          <p className="boundaryNotice">{productionGate.boundary_notice}</p>
        </section>
      ) : null}

      <div className="qualityColumns">
        <section className="qualityPanel" aria-labelledby="review-queue-title">
          <div className="qualitySectionHeading">
            <div>
              <p className="pageEyebrow">抽检队列</p>
              <h2 id="review-queue-title">逐项质量复核</h2>
            </div>
            <span>{reviews.length} 项</span>
          </div>
          {loading ? <p>正在读取质量队列…</p> : null}
          {!loading && !reviews.length ? <p className="emptyCopy">当前授权范围内没有待处理复核。</p> : null}
          <div className="qualityList" role="list">
            {reviews.map((item) => (
              <button
                key={item.id}
                className={`qualityListItem ${selectedReviewId === item.id ? "isSelected" : ""}`}
                type="button"
                onClick={() => setSelectedReviewId(item.id)}
                aria-pressed={selectedReviewId === item.id}
              >
                <span>{item.assessment_question || "协作记录"}</span>
                <small>{item.service_level} · {item.status} · {item.overdue ? "已超时" : "时限内"}</small>
              </button>
            ))}
          </div>
          {selectedReview ? (
            <div className="qualityDetail">
              <p className="qualityMeta">抽检原因：{selectedReview.sample_reason} · 截止：{selectedReview.due_at}</p>
              {selectedReview.status === "pending" ? (
                <button className="primaryButton" type="button" onClick={() => void claim()} disabled={saving}>
                  认领这项复核
                </button>
              ) : null}
              {selectedReview.status === "in_review" ? (
                <>
                  <div className="qualityDimensions">
                    {dimensions.map((name) => {
                      const entry = dimensionDraft[name];
                      return (
                        <fieldset key={name} className="qualityDimension">
                          <legend>{dimensionLabels[name]}</legend>
                          <label>
                            结论
                            <select
                              value={entry.status}
                              onChange={(event) =>
                                setDimensionDraft((current) => ({
                                  ...current,
                                  [name]: { ...current[name], status: event.target.value as DimensionDraft[typeof name]["status"] },
                                }))
                              }
                            >
                              <option value="pass">符合</option>
                              <option value="concern">需要修复</option>
                              <option value="not_applicable">不适用</option>
                            </select>
                          </label>
                          {entry.status === "concern" ? (
                            <div className="qualityDimensionInputs">
                              <label>
                                说明
                                <input
                                  value={entry.note}
                                  onChange={(event) =>
                                    setDimensionDraft((current) => ({
                                      ...current,
                                      [name]: { ...current[name], note: event.target.value },
                                    }))
                                  }
                                />
                              </label>
                              <label>
                                依据引用
                                <input
                                  value={entry.evidence_ref}
                                  onChange={(event) =>
                                    setDimensionDraft((current) => ({
                                      ...current,
                                      [name]: { ...current[name], evidence_ref: event.target.value },
                                    }))
                                  }
                                />
                              </label>
                            </div>
                          ) : null}
                        </fieldset>
                      );
                    })}
                  </div>
                  {hasConcern ? (
                    <label className="qualityTextField">
                      修复说明
                      <textarea value={remediationSummary} onChange={(event) => setRemediationSummary(event.target.value)} />
                    </label>
                  ) : null}
                  <button
                    className="primaryButton"
                    type="button"
                    onClick={() => void complete()}
                    disabled={saving || (hasConcern && !remediationSummary.trim())}
                  >
                    {hasConcern ? "提交并进入修复流程" : "确认质量复核通过"}
                  </button>
                </>
              ) : null}
            </div>
          ) : null}
        </section>

        <section className="qualityPanel" aria-labelledby="incident-title">
          <div className="qualitySectionHeading">
            <div>
              <p className="pageEyebrow">更正与投诉</p>
              <h2 id="incident-title">影响分析与独立结案</h2>
            </div>
            <span>{incidents.length} 项</span>
          </div>
          {!incidents.length ? <p className="emptyCopy">当前授权范围内没有质量事件。</p> : null}
          <div className="qualityList" role="list">
            {incidents.map((item) => (
              <button
                key={item.id}
                className={`qualityListItem ${selectedIncidentId === item.id ? "isSelected" : ""}`}
                type="button"
                onClick={() => setSelectedIncidentId(item.id)}
                aria-pressed={selectedIncidentId === item.id}
              >
                <span>{item.description}</span>
                <small>{item.category} · {item.status}</small>
              </button>
            ))}
          </div>
          {selectedIncident ? (
            <div className="qualityDetail">
              <p>{selectedIncident.requested_resolution}</p>
              {selectedIncident.status === "reported" ? (
                <>
                  <label className="qualityTextField">
                    立即措施与影响摘要
                    <textarea value={impactSummary} onChange={(event) => setImpactSummary(event.target.value)} />
                  </label>
                  <button className="primaryButton" type="button" onClick={() => void analyzeIncident()} disabled={saving || !impactSummary.trim()}>
                    保存影响分析
                  </button>
                </>
              ) : null}
              {selectedIncident.status === "independent_review" ? (
                <>
                  <label>
                    处理动作
                    <select value={resolutionAction} onChange={(event) => setResolutionAction(event.target.value as "no_change" | "withdraw")}>
                      <option value="no_change">保留历史并记录不同理解</option>
                      <option value="withdraw">撤回原反馈</option>
                    </select>
                  </label>
                  <label className="qualityTextField">
                    参与者可理解的处理说明
                    <textarea value={resolutionSummary} onChange={(event) => setResolutionSummary(event.target.value)} />
                  </label>
                  <button className="primaryButton" type="button" onClick={() => void resolveIncident()} disabled={saving || !resolutionSummary.trim()}>
                    独立结案并通知参与者
                  </button>
                </>
              ) : null}
              {selectedIncident.status === "resolved" ? (
                <div className="qualityResolution">
                  <strong>已完成处理</strong>
                  <p>{selectedIncident.resolution_summary}</p>
                  <small>通知状态：{selectedIncident.notification_status}</small>
                </div>
              ) : null}
            </div>
          ) : null}
        </section>
      </div>
      <p className="boundaryNotice">原反馈、异议、分析和修复版本都会保留；临时展示权限不能替代正式任务授权。</p>
    </section>
  );
}
