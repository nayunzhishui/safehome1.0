import { useEffect, useMemo, useState } from "react";

import { safeHomeApi as api } from "../services/safehomeApi";
import type { ProfileDimension, StudentProfileRecord } from "../../../../shared/types/api";

function parseJson<T>(value: string | null | undefined, fallback: T): T {
  if (!value) return fallback;
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

function formatConfidence(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "未计算";
  return `${Math.round(Number(value) * 100)}%`;
}

function riskText(level?: string): string {
  if (level === "high") return "高风险";
  if (level === "medium") return "需关注";
  return "低风险";
}

function reviewStatusText(status?: string | null): string {
  if (status === "in_progress") return "复核中";
  if (status === "reviewed") return "已复核";
  if (status === "escalated") return "已升级";
  if (status === "closed") return "已关闭";
  return "未复核";
}

export function ProfilesManagement() {
  const [items, setItems] = useState<StudentProfileRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selectedDetail, setSelectedDetail] = useState<StudentProfileRecord | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState("正在读取学生画像结果...");

  const pathProfileId = useMemo(() => {
    const match = window.location.pathname.match(/^\/profiles\/([^/]+)$/);
    return match ? decodeURIComponent(match[1]) : "";
  }, []);
  const selected = useMemo(() => selectedDetail ?? items.find((item) => item.id === selectedId) ?? items[0] ?? null, [items, selectedDetail, selectedId]);
  const reviewCount = items.filter((item) => item.requires_review).length;
  const highRiskCount = items.filter((item) => item.risk_level === "high").length;

  useEffect(() => {
    async function loadProfiles() {
      setStatus("loading");
      setMessage("正在读取学生画像结果...");
      try {
        const result = await api.listProfileResults({ limit: 100 });
        const profiles = result.items || [];
        setItems(profiles);
        const selectedProfile = profiles.find((item) => item.id === pathProfileId) ?? profiles[0];
        setSelectedId(selectedProfile?.id ?? "");
        setStatus("ready");
        setMessage(profiles.length ? "已读取学生画像结果。" : "暂无学生画像结果。");
      } catch (error) {
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "学生画像结果读取失败。");
      }
    }

    loadProfiles();
  }, [pathProfileId]);

  useEffect(() => {
    async function loadDetail() {
      if (!selectedId) {
        setSelectedDetail(null);
        return;
      }
      try {
        const detail = await api.getProfileResult(selectedId);
        setSelectedDetail(detail);
      } catch {
        setSelectedDetail(null);
      }
    }

    loadDetail();
  }, [selectedId]);

  function selectProfile(id: string) {
    setSelectedId(id);
    setSelectedDetail(null);
    window.history.pushState(null, "", `/profiles/${encodeURIComponent(id)}`);
  }

  const dimensions = parseJson<ProfileDimension[]>(selected?.dimensions_json, []);
  const recommendedCards = parseJson<string[]>(selected?.recommended_task_ids_json, []);

  return (
    <div className="adminPage">
      <section className="dashboardHero">
        <div>
          <span className="eyebrow">Student Profile</span>
          <h1>{pathProfileId ? "学生画像详情" : "学生画像列表"}</h1>
          <p>从 `student_profiles` 读取画像记录，用于查看置信度、风险状态、推荐训练卡、维度观察和人工复核状态。</p>
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
              {items.map((item) => (
                <button
                  className={`recordItem ${selected?.id === item.id ? "active" : ""}`}
                  key={item.id}
                  type="button"
                  onClick={() => selectProfile(item.id)}
                >
                  <strong>{item.profile_name || "未命名画像"}</strong>
                  <span>{item.anonymous_id} · {formatConfidence(item.confidence)} · {riskText(item.risk_level)}</span>
                  <small>{item.created_at}</small>
                </button>
              ))}
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
              <div className="detailRow"><span>画像名称</span><strong>{selected.profile_name || "未命名画像"}</strong></div>
              <div className="detailRow"><span>画像编码</span><strong>{selected.profile_code || "未设置"}</strong></div>
              <div className="detailRow"><span>匿名 ID</span><strong>{selected.anonymous_id}</strong></div>
              <div className="detailRow"><span>置信度</span><strong>{formatConfidence(selected.confidence)}</strong></div>
              <div className="detailRow"><span>风险状态</span><strong>{riskText(selected.risk_level)}</strong></div>
              <div className="detailRow"><span>人工关注</span><strong>{selected.requires_review ? "需要" : "暂不需要"}</strong></div>
              <div className="detailRow"><span>复核状态</span><strong>{reviewStatusText(selected.latest_review?.review_status)}</strong></div>
              <div className="detailRow"><span>推荐训练卡</span><strong>{recommendedCards.join("、") || "暂无"}</strong></div>
              <div className="detailRow"><span>画像 ID</span><strong>{selected.id}</strong></div>
              <div className="detailRow"><span>关联测评 ID</span><strong>{selected.assessment_result_id || "暂无"}</strong></div>
              <div className="detailRow"><span>保存时间</span><strong>{selected.created_at}</strong></div>
              <div className="detailRow"><span>详情链接</span><strong>{`/profiles/${selected.id}`}</strong></div>

              <div className="detailBlock">
                <h3>维度观察</h3>
                {dimensions.length ? (
                  dimensions.map((dimension) => (
                    <p key={dimension.key || dimension.label}>
                      <strong>{dimension.label}</strong>：{dimension.summary}（{dimension.level}）
                    </p>
                  ))
                ) : (
                  <p>暂无维度摘要。</p>
                )}
              </div>

              <div className="detailBlock">
                <h3>人工复核摘要</h3>
                {selected.latest_review ? (
                  <>
                    <p><strong>结论：</strong>{selected.latest_review.review_decision || "暂无"}</p>
                    <p><strong>处置：</strong>{selected.latest_review.action_summary || "暂无"}</p>
                    <p><strong>备注：</strong>{selected.latest_review.note || "暂无"}</p>
                  </>
                ) : (
                  <p>暂无人工复核记录。</p>
                )}
              </div>

              <div className="detailBlock">
                <h3>边界说明</h3>
                <p>{selected.boundary_notice || "本结果只用于支持性理解和练习推荐，不构成诊断。"}</p>
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
