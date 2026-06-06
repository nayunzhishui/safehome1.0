import { useEffect, useMemo, useState } from "react";

import { formatSafeHomeError, safeHomeApi as api } from "../services/safehomeApi";
import { getStoredAdminToken, setStoredAdminToken } from "../services/adminToken";
import type { ProfileReviewInput, ProfileReviewStatus, StudentProfileRecord } from "../../../../shared/types/api";

interface ReviewDraft {
  review_status: ProfileReviewStatus;
  review_decision: string;
  note: string;
  action_summary: string;
}

function needsReview(result: StudentProfileRecord): boolean {
  return !!result.requires_review || result.risk_level === "high" || Number(result.confidence ?? 1) < 0.5;
}

function riskText(level?: string): string {
  if (level === "high") return "高风险";
  if (level === "medium") return "需关注";
  return "低风险";
}

function confidenceText(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "未计算";
  return `${Math.round(Number(value) * 100)}%`;
}

function reviewStatusText(status?: string | null): string {
  if (status === "in_progress") return "复核中";
  if (status === "reviewed") return "已复核";
  if (status === "escalated") return "已升级";
  if (status === "closed") return "已关闭";
  return "未复核";
}

function defaultDraft(): ReviewDraft {
  return {
    review_status: "reviewed",
    review_decision: "维持支持性反馈，建议继续观察",
    note: "",
    action_summary: "已完成后台人工复核，未修改学生端报告。",
  };
}

export function ReviewManagement() {
  const [items, setItems] = useState<StudentProfileRecord[]>([]);
  const [drafts, setDrafts] = useState<Record<string, ReviewDraft>>({});
  const [savingId, setSavingId] = useState("");
  const [adminToken, setAdminToken] = useState(getStoredAdminToken);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("正在读取需复核画像...");

  const highRiskCount = useMemo(() => items.filter((item) => item.risk_level === "high").length, [items]);
  const lowConfidenceCount = useMemo(() => items.filter((item) => Number(item.confidence ?? 1) < 0.5).length, [items]);

  async function loadReviewItems() {
    setStatus("loading");
    setMessage("正在读取需复核画像...");
    try {
      const result = await api.listProfileResults({ limit: 100 }, getStoredAdminToken().trim());
      const reviewItems = (result.items || []).filter(needsReview);
      setItems(reviewItems);
      setDrafts((current) => {
        const next = { ...current };
        reviewItems.forEach((item) => {
          if (!next[item.id]) next[item.id] = defaultDraft();
        });
        return next;
      });
      setStatus("ready");
      setMessage(reviewItems.length ? "已筛选需复核画像。" : "当前暂无需复核画像。");
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "需复核画像读取失败。"));
    }
  }

  useEffect(() => {
    loadReviewItems();
  }, []);

  function updateDraft(id: string, patch: Partial<ReviewDraft>) {
    setDrafts((current) => ({
      ...current,
      [id]: {
        ...(current[id] ?? defaultDraft()),
        ...patch,
      },
    }));
  }

  async function submitReview(id: string) {
    const draft = drafts[id] ?? defaultDraft();
    const input: ProfileReviewInput = {
      reviewer_id: "web-admin",
      review_status: draft.review_status,
      review_decision: draft.review_decision,
      note: draft.note,
      action_summary: draft.action_summary,
      visible_to_student: false,
    };
    setSavingId(id);
    setMessage("正在保存人工复核记录...");
    try {
      await api.createProfileReview(id, input, adminToken.trim());
      setMessage("人工复核记录已保存，学生端报告未被覆盖。");
      await loadReviewItems();
    } catch (error) {
      setStatus("error");
      setMessage(formatSafeHomeError(error, "人工复核保存失败。"));
    } finally {
      setSavingId("");
    }
  }

  return (
    <div className="adminPage">
      <section className="dashboardHero">
        <div>
          <span className="eyebrow">Human Review</span>
          <h1>人工复核列表</h1>
          <p>筛选需人工关注的学生画像。人工备注单独保存，不自动覆盖学生端报告。</p>
        </div>
        <div className={`status compact ${status}`}>{message}</div>
      </section>

      <section className="guidanceBox" aria-label="后台令牌">
        <label className="tokenField">
          后台令牌
          <input
            type="password"
            value={adminToken}
            onChange={(event) => {
              setAdminToken(event.target.value);
              setStoredAdminToken(event.target.value);
            }}
            placeholder="请输入 X-Admin-Token"
          />
        </label>
      </section>

      <section className="metricGrid">
        <div className="metricCard">
          <span>需复核</span>
          <strong>{items.length}</strong>
        </div>
        <div className="metricCard">
          <span>高风险</span>
          <strong>{highRiskCount}</strong>
        </div>
        <div className="metricCard">
          <span>低置信度</span>
          <strong>{lowConfidenceCount}</strong>
        </div>
      </section>

      <section className="panel">
        <div className="sectionHeader">
          <div>
            <h2>复核队列</h2>
            <p>命中条件：高风险、requires_review=true，或置信度低于 50%。</p>
          </div>
          <span className="countBadge">{items.length} 条</span>
        </div>

        {items.length === 0 ? (
          <div className="emptyState">暂无需要人工复核的画像记录。</div>
        ) : (
          <div className="tableList">
            {items.map((item) => {
              const draft = drafts[item.id] ?? defaultDraft();
              return (
                <article className="tableCard" key={item.id}>
                  <div>
                    <strong>{item.profile_name || "未命名画像"}</strong>
                    <p>{item.boundary_notice || "本结果只用于支持性理解和练习推荐，不构成诊断。"}</p>
                  </div>
                  <div className="tagCluster">
                    <span className="countBadge">{riskText(item.risk_level)}</span>
                    <span className="countBadge">{confidenceText(item.confidence)}</span>
                    <span className="countBadge">{item.requires_review ? "需复核" : "低置信度"}</span>
                    <span className="countBadge">{reviewStatusText(item.latest_review?.review_status)}</span>
                  </div>
                  <div className="detailRow"><span>画像 ID</span><strong>{item.id}</strong></div>
                  <div className="detailRow"><span>匿名 ID</span><strong>{item.anonymous_id}</strong></div>
                  <div className="detailRow"><span>最新复核</span><strong>{item.latest_review?.review_decision || "暂无"}</strong></div>

                  <div className="reviewForm">
                    <label>
                      复核状态
                      <select
                        value={draft.review_status}
                        onChange={(event) => updateDraft(item.id, { review_status: event.target.value as ProfileReviewStatus })}
                      >
                        <option value="reviewed">已复核</option>
                        <option value="in_progress">复核中</option>
                        <option value="escalated">已升级</option>
                        <option value="closed">已关闭</option>
                      </select>
                    </label>
                    <label>
                      复核结论
                      <input
                        value={draft.review_decision}
                        onChange={(event) => updateDraft(item.id, { review_decision: event.target.value })}
                        placeholder="例如：维持支持性反馈，建议继续观察"
                      />
                    </label>
                    <label>
                      处置摘要
                      <input
                        value={draft.action_summary}
                        onChange={(event) => updateDraft(item.id, { action_summary: event.target.value })}
                        placeholder="例如：已联系督导老师进一步查看"
                      />
                    </label>
                    <label>
                      人工备注
                      <textarea
                        value={draft.note}
                        onChange={(event) => updateDraft(item.id, { note: event.target.value })}
                        placeholder="仅后台可见，不自动同步学生端"
                      />
                    </label>
                    <div className="buttonRow">
                      <a className="textLink" href={`/profiles/${encodeURIComponent(item.id)}`}>查看画像详情</a>
                      <button className="primaryButton" type="button" onClick={() => submitReview(item.id)} disabled={savingId === item.id}>
                        {savingId === item.id ? "保存中..." : "保存复核"}
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
