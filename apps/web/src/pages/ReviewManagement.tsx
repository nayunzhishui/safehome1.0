import { useEffect, useMemo, useState } from "react";

import { safeHomeApi as api } from "../services/safehomeApi";
import type { AssessmentResult, RiskLevel } from "../../../../shared/types/api";

interface ProfileScores {
  profile_code?: string;
  profile_name?: string;
  confidence?: number;
  risk_level?: RiskLevel;
  requires_review?: boolean;
  recommended_card_ids?: string[];
  supportive_explanation?: string;
}

function parseScores(result: AssessmentResult): ProfileScores {
  try {
    return JSON.parse(result.scores_json || "{}") as ProfileScores;
  } catch {
    return {};
  }
}

function needsReview(result: AssessmentResult): boolean {
  const scores = parseScores(result);
  return !!scores.requires_review || scores.risk_level === "high" || Number(scores.confidence ?? 1) < 0.5;
}

function riskText(level?: string): string {
  if (level === "high") return "高风险";
  if (level === "medium") return "需关注";
  return "低风险";
}

function confidenceText(value?: number): string {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "未计算";
  return `${Math.round(Number(value) * 100)}%`;
}

export function ReviewManagement() {
  const [items, setItems] = useState<AssessmentResult[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("正在读取需复核画像...");

  const highRiskCount = useMemo(() => items.filter((item) => parseScores(item).risk_level === "high").length, [items]);
  const lowConfidenceCount = useMemo(() => items.filter((item) => Number(parseScores(item).confidence ?? 1) < 0.5).length, [items]);

  useEffect(() => {
    async function loadReviewItems() {
      setStatus("loading");
      setMessage("正在读取需复核画像...");
      try {
        const result = await api.listAssessmentResults({ limit: 100 });
        const profiles = (result.items || []).filter((item) => item.worksheet_id === "student_profile_v1" || item.category === "学生画像");
        const reviewItems = profiles.filter(needsReview);
        setItems(reviewItems);
        setStatus("ready");
        setMessage(reviewItems.length ? "已筛选需复核画像。" : "当前暂无需复核画像。");
      } catch (error) {
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "需复核画像读取失败。");
      }
    }

    loadReviewItems();
  }, []);

  return (
    <div className="adminPage">
      <section className="dashboardHero">
        <div>
          <span className="eyebrow">Human Review</span>
          <h1>人工复核列表</h1>
          <p>筛选需人工关注的学生画像。当前只读展示，不把人工备注自动同步到学生端。</p>
        </div>
        <div className={`status compact ${status}`}>{message}</div>
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
              const scores = parseScores(item);
              return (
                <article className="tableCard" key={item.id}>
                  <div>
                    <strong>{scores.profile_name || item.worksheet_title}</strong>
                    <p>{scores.supportive_explanation || item.result_summary || "暂无解释摘要。"}</p>
                  </div>
                  <div className="tagCluster">
                    <span className="countBadge">{riskText(scores.risk_level)}</span>
                    <span className="countBadge">{confidenceText(scores.confidence)}</span>
                    <span className="countBadge">{scores.requires_review ? "需复核" : "低置信度"}</span>
                  </div>
                  <div className="detailRow"><span>记录 ID</span><strong>{item.id}</strong></div>
                  <div className="detailRow"><span>用户 ID</span><strong>{item.user_id}</strong></div>
                  <div className="detailRow"><span>推荐训练卡</span><strong>{scores.recommended_card_ids?.join("、") || "暂无"}</strong></div>
                  <a className="textLink" href={`/profiles/${encodeURIComponent(item.id)}`}>查看画像详情</a>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
