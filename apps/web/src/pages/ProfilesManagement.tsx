import { useEffect, useMemo, useState } from "react";

import { safeHomeApi as api } from "../services/safehomeApi";
import type { AssessmentResult, RiskLevel } from "../../../../shared/types/api";

interface ProfileScores {
  profile_code?: string;
  profile_name?: string;
  confidence?: number;
  risk_level?: RiskLevel;
  requires_review?: boolean;
  allow_auto_feedback?: boolean;
  recommended_card_ids?: string[];
  dimensions?: Array<{ key?: string; label?: string; level?: string; summary?: string }>;
}

function parseScores(result: AssessmentResult | null): ProfileScores {
  if (!result?.scores_json) return {};
  try {
    return JSON.parse(result.scores_json) as ProfileScores;
  } catch {
    return {};
  }
}

function formatConfidence(value?: number): string {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "未计算";
  return `${Math.round(Number(value) * 100)}%`;
}

function riskText(level?: string): string {
  if (level === "high") return "高风险";
  if (level === "medium") return "需关注";
  return "低风险";
}

export function ProfilesManagement() {
  const [items, setItems] = useState<AssessmentResult[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("正在读取学生画像结果...");

  const selected = useMemo(() => items.find((item) => item.id === selectedId) ?? items[0] ?? null, [items, selectedId]);
  const selectedScores = useMemo(() => parseScores(selected), [selected]);
  const reviewCount = items.filter((item) => parseScores(item).requires_review).length;
  const highRiskCount = items.filter((item) => parseScores(item).risk_level === "high").length;

  useEffect(() => {
    async function loadProfiles() {
      setStatus("loading");
      setMessage("正在读取学生画像结果...");
      try {
        const result = await api.listAssessmentResults({ limit: 100 });
        const profiles = (result.items || []).filter((item) => item.worksheet_id === "student_profile_v1" || item.category === "学生画像");
        setItems(profiles);
        setSelectedId(profiles[0]?.id ?? "");
        setStatus("ready");
        setMessage(profiles.length ? "已读取学生画像结果。" : "暂无学生画像结果。");
      } catch (error) {
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "学生画像结果读取失败。");
      }
    }

    loadProfiles();
  }, []);

  return (
    <div className="adminPage">
      <section className="dashboardHero">
        <div>
          <span className="eyebrow">Student Profile</span>
          <h1>学生画像列表</h1>
          <p>从现有测一测结果中筛选 `student_profile_v1`，用于查看画像名称、置信度、风险状态和推荐训练卡。</p>
        </div>
        <div className={`status compact ${status}`}>{message}</div>
      </section>

      <section className="metricGrid">
        <div className="metricCard">
          <span>画像结果</span>
          <strong>{items.length}</strong>
        </div>
        <div className="metricCard">
          <span>需人工关注</span>
          <strong>{reviewCount}</strong>
        </div>
        <div className="metricCard">
          <span>高风险</span>
          <strong>{highRiskCount}</strong>
        </div>
      </section>

      <section className="dashboardGrid twoColumn">
        <div className="panel">
          <div className="sectionHeader">
            <div>
              <h2>画像记录</h2>
              <p>默认不展示自由文本原文。</p>
            </div>
            <span className="countBadge">{items.length} 条</span>
          </div>

          {items.length === 0 ? (
            <div className="emptyState">暂无画像结果。请先在小程序“学生支持性画像测评”中提交一次。</div>
          ) : (
            <div className="recordList">
              {items.map((item) => {
                const scores = parseScores(item);
                return (
                  <button
                    className={`recordItem ${selected?.id === item.id ? "active" : ""}`}
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedId(item.id)}
                  >
                    <strong>{scores.profile_name || item.worksheet_title}</strong>
                    <span>{item.user_id} · {formatConfidence(scores.confidence)} · {riskText(scores.risk_level)}</span>
                    <small>{item.created_at}</small>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="panel">
          <div className="sectionHeader">
            <div>
              <h2>画像详情</h2>
              <p>用于后台查看和后续人工复核。</p>
            </div>
          </div>

          {selected ? (
            <div className="detailStack">
              <div className="detailRow"><span>画像名称</span><strong>{selectedScores.profile_name || "未命名画像"}</strong></div>
              <div className="detailRow"><span>画像编码</span><strong>{selectedScores.profile_code || "未设置"}</strong></div>
              <div className="detailRow"><span>置信度</span><strong>{formatConfidence(selectedScores.confidence)}</strong></div>
              <div className="detailRow"><span>风险状态</span><strong>{riskText(selectedScores.risk_level)}</strong></div>
              <div className="detailRow"><span>人工关注</span><strong>{selectedScores.requires_review ? "需要" : "暂不需要"}</strong></div>
              <div className="detailRow"><span>推荐训练卡</span><strong>{selectedScores.recommended_card_ids?.join("、") || "暂无"}</strong></div>
              <div className="detailRow"><span>记录 ID</span><strong>{selected.id}</strong></div>
              <div className="detailRow"><span>保存时间</span><strong>{selected.created_at}</strong></div>

              <div className="detailBlock">
                <h3>维度观察</h3>
                {selectedScores.dimensions?.length ? (
                  selectedScores.dimensions.map((dimension) => (
                    <p key={dimension.key || dimension.label}>
                      <strong>{dimension.label}</strong>：{dimension.summary}（{dimension.level}）
                    </p>
                  ))
                ) : (
                  <p>暂无维度摘要。</p>
                )}
              </div>
            </div>
          ) : (
            <div className="emptyState">请选择一条画像记录。</div>
          )}
        </div>
      </section>
    </div>
  );
}
