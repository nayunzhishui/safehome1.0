import { useMemo, useState } from "react";

import assessmentTrainingMap from "../../../../content/assessment_training_map.json";
import diaryTrainingMap from "../../../../content/diary_training_map.json";
import feedbackRules from "../../../../content/feedback_rules.json";
import coursesContent from "../../../../content/courses.json";
import programsContent from "../../../../content/programs.json";
import scalesCatalog from "../../../../content/scales_catalog.json";
import trainingCards from "../../../../content/training_cards.json";
import { safeHomeApi } from "../services/safehomeApi";
import { getStoredAuthUser } from "../services/authState";

interface ReviewItem {
  id: string;
  title: string;
  type: string;
  contentType: string;
  reviewStatus: string;
  enabled: boolean;
  note: string;
}

const REVIEW_STATUS_OPTIONS = ["draft", "pending_review", "reviewed", "trial_enabled", "enabled", "disabled", "metadata_only", "pilot_ready", "draft_requires_psychology_review", "pilot_draft", "pilot_approved", "paused", "completed"];

function statusText(value?: string) {
  const labels: Record<string, string> = {
    draft: "草稿",
    pending_review: "待审核",
    reviewed: "已审核",
    trial_enabled: "试用开放",
    enabled: "正式开放",
    disabled: "已停用",
    metadata_only: "仅元数据",
    pilot_ready: "试点可用",
    draft_requires_psychology_review: "待心理审核",
    pilot_draft: "试点草案",
    pilot_approved: "试点已批准",
    paused: "已暂停",
    completed: "已结束",
  };
  return labels[value || ""] || value || "未标记";
}

function enabledText(value: boolean) {
  return value ? "用户端可见" : "暂不开放";
}

function buildReviewItems(): ReviewItem[] {
  const scaleItems = (scalesCatalog.scales || []).map((scale) => ({
    id: scale.id,
    title: scale.display_name,
    type: "量表目录",
    contentType: "scale",
    reviewStatus: scale.review_status || "未标记",
    enabled: Boolean(scale.enabled),
    note: scale.notes || scale.not_open_reason || "待补充审核说明",
  }));

  const cardItems = (trainingCards.cards || []).map((card) => ({
    id: card.id,
    title: card.title,
    type: "训练卡",
    contentType: "training_card",
    reviewStatus: card.review_status || "未标记",
    enabled: Boolean(card.enabled),
    note: card.reviewer_note || card.purpose || "待补充审核说明",
  }));

  const feedbackRuleItems = (feedbackRules.rules || []).map((rule) => ({
    id: rule.id,
    title: rule.label,
    type: "反馈规则",
    contentType: "feedback_rule",
    reviewStatus: rule.review_status || "未标记",
    enabled: rule.enabled !== false,
    note: rule.boundary_notice || rule.explanation || "待补充审核说明",
  }));

  const assessmentMapItems = (assessmentTrainingMap.rules || []).map((rule) => ({
    id: rule.rule_id,
    title: rule.rule_id,
    type: "测评推荐规则",
    contentType: "assessment_training_rule",
    reviewStatus: rule.review_status || "未标记",
    enabled: false,
    note: rule.reason || rule.boundary_notice || "待补充审核说明",
  }));

  const diaryMapItems = (diaryTrainingMap.rules || []).map((rule) => ({
    id: rule.rule_id,
    title: rule.rule_id,
    type: "日记推荐规则",
    contentType: "diary_training_rule",
    reviewStatus: rule.review_status || "未标记",
    enabled: false,
    note: rule.reason || rule.boundary_notice || "待补充审核说明",
  }));

  const courseItems = (coursesContent.courses || []).map((course) => ({
    id: course.id,
    title: course.title,
    type: "结构化课程",
    contentType: "course",
    reviewStatus: course.review_status || "未标记",
    enabled: Boolean(course.enabled),
    note: `${course.core_concept} · ${course.curriculum_node}`,
  }));

  const programItems = (programsContent.programs || []).map((program) => ({
    id: program.id,
    title: program.title,
    type: "项目方案",
    contentType: "program",
    reviewStatus: program.review_status || "未标记",
    enabled: Boolean(program.enabled),
    note: `${program.protocol_version} · 三方签字状态：${Object.values(program.approval || {}).map((item) => item.status).join("/")}`,
  }));

  return [...scaleItems, ...cardItems, ...courseItems, ...programItems, ...feedbackRuleItems, ...assessmentMapItems, ...diaryMapItems];
}

export function ContentReviewOverview() {
  const [items, setItems] = useState<ReviewItem[]>(() => buildReviewItems());
  const [selectedKey, setSelectedKey] = useState<string>(() => {
    const firstDraft = buildReviewItems().find((item) => ["draft", "metadata_only", "draft_requires_psychology_review", "pilot_draft"].includes(item.reviewStatus));
    return firstDraft ? `${firstDraft.contentType}:${firstDraft.id}` : "";
  });
  const [reviewStatus, setReviewStatus] = useState("");
  const [enabledForUser, setEnabledForUser] = useState(false);
  const [saveMessage, setSaveMessage] = useState("admin 可保存审核状态；开启用户端开放状态会被拦截并要求人工确认。");
  const [saveStatus, setSaveStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const currentUser = getStoredAuthUser();
  const canEdit = currentUser?.role === "admin";
  const selectedItem = useMemo(() => items.find((item) => `${item.contentType}:${item.id}` === selectedKey) || items[0], [items, selectedKey]);
  const openItems = items.filter((item) => item.enabled);
  const draftItems = items.filter((item) => ["draft", "metadata_only", "draft_requires_psychology_review", "pilot_draft"].includes(item.reviewStatus));
  const scaleItems = items.filter((item) => item.type === "量表目录");
  const ruleItems = items.filter((item) => item.type.includes("规则"));

  async function saveReviewUpdate() {
    if (!selectedItem) return;
    setSaveStatus("loading");
    setSaveMessage("正在保存审核状态...");
    try {
      const result = await safeHomeApi.updateContentReview({
        content_type: selectedItem.contentType,
        item_id: selectedItem.id,
        review_status: reviewStatus || selectedItem.reviewStatus,
        enabled_for_user: enabledForUser ? true : undefined,
      });
      setItems((current) =>
        current.map((item) =>
          item.contentType === selectedItem.contentType && item.id === selectedItem.id
            ? {
                ...item,
                reviewStatus: result.review_status || item.reviewStatus,
                enabled: Boolean(result.enabled_for_user),
              }
            : item,
        ),
      );
      setSaveStatus("success");
      setSaveMessage("已保存到本地 content JSON。若需要开启用户端开放状态，仍必须单独人工确认。");
    } catch (error) {
      setSaveStatus("error");
      setSaveMessage(error instanceof Error ? error.message : "保存失败，请确认后台令牌和 backend 状态。");
    }
  }

  return (
    <section className="dashboardShell" aria-label="内容审核总览">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Content Review</p>
          <h1>内容审核总览</h1>
          <p className="summary">
            汇总量表、训练卡、结构化课程、项目方案和规则的审核状态。当前仍以本地 content JSON 为事实源，正式发布前所有内容开放都需要人工复核。
          </p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/content/cards">
            训练卡
          </a>
          <a className="secondaryButton" href="/content/rules">
            规则
          </a>
        </div>
      </div>

      <div className="status success">已读取本地内容审核状态。当前页面不提供发布、上传体验版或提交审核能力。</div>

      <div className="metricGrid" aria-label="内容审核概况">
        <MetricCard label="内容项" value={items.length} />
        <MetricCard label="量表目录" value={scaleItems.length} />
        <MetricCard label="规则项" value={ruleItems.length} />
        <MetricCard label="暂不开放" value={items.length - openItems.length} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="待审核内容">
          <div className="sectionTitleRow">
            <h2>待审核重点</h2>
            <span className="countBadge">{draftItems.length} 项</span>
          </div>
          <div className="recordList">
            {draftItems.map((item) => (
              <button
                className={`recordItem ${selectedItem?.contentType === item.contentType && selectedItem?.id === item.id ? "active" : ""}`}
                key={`${item.type}-${item.id}`}
                type="button"
                onClick={() => {
                  setSelectedKey(`${item.contentType}:${item.id}`);
                  setReviewStatus(item.reviewStatus);
                  setEnabledForUser(false);
                }}
              >
                <span className="recordScene">{item.title}</span>
                <span className="recordDescription">{item.note}</span>
                <span className="recordMeta">
                  {item.type} · {statusText(item.reviewStatus)} · {enabledText(item.enabled)}
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="detailPanel" aria-label="审核规则">
          <div className="sectionTitleRow">
            <h2>第一版审核边界</h2>
            <span className="countBadge">只读</span>
          </div>
          <div className="detailContent">
            <DetailRow label="admin" value="可本地受控修改 review_status 和关闭开放状态；开启用户端开放状态仍需人工单独确认。" />
            <DetailRow label="researcher" value="只读查看内容状态，不直接开放用户端内容。" />
            <DetailRow label="supervisor" value="只读查看风险相关内容，后续细化权限。" />
            <DetailRow label="parent/student" value="不可访问内容审核后台。" />

            <section className="guidanceBox" aria-label="发布边界">
              <h3>发布边界</h3>
              <p>当前是本地开发阶段，可直接修改 content JSON；正式发布前所有 content JSON 修改必须经过人工复核。</p>
              <p>后续进入正式环境后，应改为后端接口加 audit_logs，不允许绕过审核直接开放真实量表。</p>
            </section>

            {canEdit ? (
              <section className="guidanceBox" aria-label="受控修改">
                <h3>受控修改</h3>
                <DetailRow label="当前项目" value={selectedItem ? `${selectedItem.type} / ${selectedItem.title}` : "未选择"} />
                <label className="formLabel">
                  审核状态
                  <select className="formSelect" value={reviewStatus || selectedItem?.reviewStatus || ""} onChange={(event) => setReviewStatus(event.target.value)}>
                    {REVIEW_STATUS_OPTIONS.map((status) => (
                      <option value={status} key={status}>
                        {statusText(status)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="checkboxRow">
                  <input type="checkbox" checked={enabledForUser} onChange={(event) => setEnabledForUser(event.target.checked)} />
                  请求开启用户端开放状态
                </label>
                <p>开启用户端开放状态会被后端拦截，需要单独人工确认；普通保存只用于本地审核状态维护。</p>
                <button className="primaryButton" type="button" onClick={saveReviewUpdate} disabled={saveStatus === "loading"}>
                  {saveStatus === "loading" ? "保存中..." : "保存审核状态"}
                </button>
                <div className={`status ${saveStatus === "error" ? "error" : saveStatus === "success" ? "success" : ""}`}>{saveMessage}</div>
              </section>
            ) : (
              <section className="guidanceBox" aria-label="只读说明">
                <h3>只读说明</h3>
                <p>当前角色只能查看内容审核状态，不能修改 `review_status` 或开放状态。</p>
              </section>
            )}
          </div>
        </section>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="metricCard">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="detailRow">
      <span className="detailLabel">{label}</span>
      <span className="detailValue">{value}</span>
    </div>
  );
}
