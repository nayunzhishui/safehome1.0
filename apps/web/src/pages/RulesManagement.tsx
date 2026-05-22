import { useMemo, useState } from "react";

import feedbackRules from "../../../../content/feedback_rules.json";

type RiskLevel = "low" | "medium" | "high";

interface FeedbackRule {
  id: string;
  label: string;
  explanation: string;
  supportive_feedback: string;
  recommended_card_ids: string[];
  risk_level: RiskLevel;
}

interface FeedbackRulesContent {
  version: string;
  rules: FeedbackRule[];
  safety_notes: string[];
}

const rulesContent = feedbackRules as FeedbackRulesContent;

function displayText(value?: string | number | null) {
  if (value === undefined || value === null || value === "") {
    return "未填写";
  }
  return String(value);
}

function riskLabel(value: RiskLevel) {
  const labels: Record<RiskLevel, string> = {
    low: "低",
    medium: "中",
    high: "高",
  };
  return labels[value] ?? value;
}

export function RulesManagement() {
  const [selectedId, setSelectedId] = useState<string | undefined>(rulesContent.rules[0]?.id);

  const selectedRule = useMemo(() => {
    return rulesContent.rules.find((rule) => rule.id === selectedId) ?? rulesContent.rules[0];
  }, [selectedId]);

  const mediumOrHighRules = rulesContent.rules.filter((rule) => rule.risk_level !== "low");
  const recommendedCardIds = new Set(rulesContent.rules.flatMap((rule) => rule.recommended_card_ids));

  return (
    <section className="dashboardShell" aria-label="反馈规则管理后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Content Management</p>
          <h1>反馈规则管理</h1>
          <p className="summary">只读查看当前反馈规则，用于确认规则标签、解释、支持性反馈和推荐训练卡是否适合试点使用。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/dashboard">
            返回总览
          </a>
          <a className="primaryButton" href="/content/cards">
            查看训练卡
          </a>
        </div>
      </div>

      <div className="status success">已读取反馈规则内容。当前页面只读展示，不提供编辑或发布能力。</div>

      <div className="metricGrid" aria-label="反馈规则概况">
        <MetricCard label="规则总数" value={rulesContent.rules.length} />
        <MetricCard label="中高提示" value={mediumOrHighRules.length} />
        <MetricCard label="推荐卡片" value={recommendedCardIds.size} />
        <MetricCard label="安全提示" value={rulesContent.safety_notes.length} />
      </div>

      <div className="dashboardGrid goalsGrid">
        <section className="listPanel" aria-label="反馈规则列表">
          <div className="sectionTitleRow">
            <h2>反馈规则列表</h2>
            <span className="countBadge">{rulesContent.version}</span>
          </div>

          {rulesContent.rules.length === 0 ? (
            <div className="emptyState">当前没有反馈规则。请检查内容库是否已初始化。</div>
          ) : (
            <div className="recordList">
              {rulesContent.rules.map((rule) => (
                <button
                  className={`recordItem ${selectedRule?.id === rule.id ? "active" : ""}`}
                  key={rule.id}
                  type="button"
                  onClick={() => setSelectedId(rule.id)}
                >
                  <span className="recordScene">{rule.label}</span>
                  <span className="recordDescription">{rule.explanation}</span>
                  <span className="recordMeta">
                    风险提示 {riskLabel(rule.risk_level)} · 推荐 {rule.recommended_card_ids.length} 张训练卡
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detailPanel" aria-label="反馈规则详情">
          <div className="sectionTitleRow">
            <h2>反馈规则详情</h2>
            {selectedRule && <span className="countBadge">ID {selectedRule.id}</span>}
          </div>

          {selectedRule ? (
            <div className="detailContent">
              <DetailRow label="规则标签" value={selectedRule.label} />
              <DetailRow label="风险提示" value={riskLabel(selectedRule.risk_level)} />
              <DetailRow label="规则解释" value={selectedRule.explanation} />
              <DetailRow label="支持性反馈" value={selectedRule.supportive_feedback} />
              <DetailRow label="推荐训练卡" value={selectedRule.recommended_card_ids.join("、")} />

              <section className="guidanceBox" aria-label="展示边界提示">
                <h3>展示边界</h3>
                <p>
                  当前页面不直接展示触发词和原始改写例句，避免把高压力表达误当成家长可复制话术。反馈规则只用于辅助试点评估和内容复核，不做诊断判断。
                </p>
              </section>

              <section className="guidanceBox" aria-label="安全提示">
                <h3>安全提示</h3>
                {rulesContent.safety_notes.map((note) => (
                  <p key={note}>{note}</p>
                ))}
              </section>
            </div>
          ) : (
            <div className="emptyState">选择左侧反馈规则后，这里会显示详情。</div>
          )}
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

function DetailRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="detailRow">
      <span className="detailLabel">{label}</span>
      <span className="detailValue">{displayText(value)}</span>
    </div>
  );
}
