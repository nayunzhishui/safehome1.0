import { useMemo, useState } from "react";

import assessmentTrainingMap from "../../../../content/assessment_training_map.json";
import diaryTrainingMap from "../../../../content/diary_training_map.json";
import feedbackRules from "../../../../content/feedback_rules.json";
import studentProfileRules from "../../../../content/student_profile_rules.json";
import trainingCardsContent from "../../../../content/training_cards.json";
import { displayRisk, displaySourceType, displayStatus } from "../utils/displayLabels";

type RiskLevel = "low" | "medium" | "high";
type RuleTab = "feedback" | "profile" | "assessmentTraining" | "diaryTraining";

interface FeedbackRule {
  id: string;
  label: string;
  explanation: string;
  supportive_feedback: string;
  recommended_card_ids: string[];
  risk_level: RiskLevel;
  version?: string;
  theory_source?: string;
  review_status?: string;
  enabled?: boolean;
  boundary_notice?: string;
}

interface FeedbackRulesContent {
  version: string;
  rules: FeedbackRule[];
  safety_notes: string[];
}

interface ProfileDimensionRule {
  key: string;
  label: string;
  level: string;
  summary: string;
}

interface StudentProfileRule {
  id: string;
  profile_code: string;
  profile_name: string;
  trigger?: {
    score_conditions?: Record<string, string>;
    confidence_min?: number;
    excluded_risk_levels?: string[];
  };
  dimensions: ProfileDimensionRule[];
  content?: {
    title?: string;
    explanation?: string;
    strength_note?: string;
    small_step?: string;
    boundary_notice?: string;
  };
  recommended_card_ids: string[];
  risk_level: RiskLevel;
  requires_review: boolean;
  enabled: boolean;
}

interface StudentProfileRulesContent {
  version: string;
  module: string;
  review_status: string;
  rules: StudentProfileRule[];
  safety_notes: string[];
}

interface TrainingMapRule {
  rule_id: string;
  source_type: "assessment" | "diary";
  trigger_condition: Record<string, unknown>;
  theme: string[];
  recommended_card_ids: string[];
  reason: string;
  today_suggestion: string;
  long_term_suggestion?: string;
  not_suitable_when: string;
  boundary_notice: string;
  review_status: string;
}

interface TrainingMapContent {
  version: string;
  boundary_notice: string;
  rules: TrainingMapRule[];
}

const rulesContent = feedbackRules as FeedbackRulesContent;
const profileRulesContent = studentProfileRules as StudentProfileRulesContent;
const assessmentTrainingContent = assessmentTrainingMap as TrainingMapContent;
const diaryTrainingContent = diaryTrainingMap as TrainingMapContent;
const trainingCardTitles = new Map(
  trainingCardsContent.cards.map((card) => [card.id, card.title]),
);

function trainingCardNames(ids: string[]) {
  return ids.map((id) => trainingCardTitles.get(id) || "待核对的训练卡").join("、");
}

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

function triggerSummary(rule: StudentProfileRule) {
  const conditions = Object.entries(rule.trigger?.score_conditions ?? {})
    .map(([key, value]) => `${key} ${value}`)
    .join("、");
  const confidence = rule.trigger?.confidence_min ? `置信度下限 ${rule.trigger.confidence_min}` : "";
  return [conditions, confidence].filter(Boolean).join("；") || "未配置触发摘要";
}

export function RulesManagement() {
  const [activeTab, setActiveTab] = useState<RuleTab>("feedback");
  const [selectedId, setSelectedId] = useState<string | undefined>(rulesContent.rules[0]?.id);
  const [selectedProfileId, setSelectedProfileId] = useState<string | undefined>(profileRulesContent.rules[0]?.id);
  const [selectedAssessmentTrainingId, setSelectedAssessmentTrainingId] = useState<string | undefined>(assessmentTrainingContent.rules[0]?.rule_id);
  const [selectedDiaryTrainingId, setSelectedDiaryTrainingId] = useState<string | undefined>(diaryTrainingContent.rules[0]?.rule_id);

  const selectedRule = useMemo(() => {
    return rulesContent.rules.find((rule) => rule.id === selectedId) ?? rulesContent.rules[0];
  }, [selectedId]);
  const selectedProfileRule = useMemo(() => {
    return profileRulesContent.rules.find((rule) => rule.id === selectedProfileId) ?? profileRulesContent.rules[0];
  }, [selectedProfileId]);
  const selectedAssessmentTrainingRule = useMemo(() => {
    return assessmentTrainingContent.rules.find((rule) => rule.rule_id === selectedAssessmentTrainingId) ?? assessmentTrainingContent.rules[0];
  }, [selectedAssessmentTrainingId]);
  const selectedDiaryTrainingRule = useMemo(() => {
    return diaryTrainingContent.rules.find((rule) => rule.rule_id === selectedDiaryTrainingId) ?? diaryTrainingContent.rules[0];
  }, [selectedDiaryTrainingId]);

  const mediumOrHighRules = rulesContent.rules.filter((rule) => rule.risk_level !== "low");
  const recommendedCardIds = new Set(rulesContent.rules.flatMap((rule) => rule.recommended_card_ids));
  const enabledProfileRules = profileRulesContent.rules.filter((rule) => rule.enabled);
  const profileRecommendedCardIds = new Set(profileRulesContent.rules.flatMap((rule) => rule.recommended_card_ids));

  return (
    <section className="dashboardShell" aria-label="反馈规则管理后台">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Content Management</p>
          <h1>规则查看</h1>
          <p className="summary">只读查看当前反馈规则和学生画像规则，用于确认规则版本、启用状态、推荐训练卡和展示边界。</p>
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

      <div className="buttonRow">
        <button className={activeTab === "feedback" ? "primaryButton" : "secondaryButton"} type="button" onClick={() => setActiveTab("feedback")}>
          反馈规则
        </button>
        <button className={activeTab === "profile" ? "primaryButton" : "secondaryButton"} type="button" onClick={() => setActiveTab("profile")}>
          画像规则
        </button>
        <button
          className={activeTab === "assessmentTraining" ? "primaryButton" : "secondaryButton"}
          type="button"
          onClick={() => setActiveTab("assessmentTraining")}
        >
          测评推荐
        </button>
        <button className={activeTab === "diaryTraining" ? "primaryButton" : "secondaryButton"} type="button" onClick={() => setActiveTab("diaryTraining")}>
          日记推荐
        </button>
      </div>

      <div className="status success">已读取反馈规则内容。当前页面只读展示，不提供编辑或发布能力。</div>

      <div className="metricGrid" aria-label="反馈规则概况">
        {activeTab === "feedback" ? (
          <>
            <MetricCard label="规则总数" value={rulesContent.rules.length} />
            <MetricCard label="中高提示" value={mediumOrHighRules.length} />
            <MetricCard label="推荐卡片" value={recommendedCardIds.size} />
            <MetricCard label="安全提示" value={rulesContent.safety_notes.length} />
          </>
        ) : null}
        {activeTab === "profile" ? (
          <>
            <MetricCard label="画像规则" value={profileRulesContent.rules.length} />
            <MetricCard label="启用规则" value={enabledProfileRules.length} />
            <MetricCard label="推荐卡片" value={profileRecommendedCardIds.size} />
            <MetricCard label="规则状态" value={displayStatus(profileRulesContent.review_status)} />
          </>
        ) : null}
        {activeTab === "assessmentTraining" ? (
          <>
            <MetricCard label="测评推荐" value={assessmentTrainingContent.rules.length} />
            <MetricCard label="草稿规则" value={assessmentTrainingContent.rules.filter((rule) => rule.review_status === "draft").length} />
            <MetricCard label="推荐卡片" value={new Set(assessmentTrainingContent.rules.flatMap((rule) => rule.recommended_card_ids)).size} />
            <MetricCard label="规则版本" value={assessmentTrainingContent.version} />
          </>
        ) : null}
        {activeTab === "diaryTraining" ? (
          <>
            <MetricCard label="日记推荐" value={diaryTrainingContent.rules.length} />
            <MetricCard label="草稿规则" value={diaryTrainingContent.rules.filter((rule) => rule.review_status === "draft").length} />
            <MetricCard label="推荐卡片" value={new Set(diaryTrainingContent.rules.flatMap((rule) => rule.recommended_card_ids)).size} />
            <MetricCard label="规则版本" value={diaryTrainingContent.version} />
          </>
        ) : null}
      </div>

      {activeTab === "feedback" ? <FeedbackRulesView selectedRule={selectedRule} setSelectedId={setSelectedId} /> : null}
      {activeTab === "profile" ? (
        <ProfileRulesView selectedProfileRule={selectedProfileRule} selectedProfileId={selectedProfileId} setSelectedProfileId={setSelectedProfileId} />
      ) : null}
      {activeTab === "assessmentTraining" ? (
        <TrainingMapRulesView
          content={assessmentTrainingContent}
          selectedRule={selectedAssessmentTrainingRule}
          selectedRuleId={selectedAssessmentTrainingId}
          setSelectedRuleId={setSelectedAssessmentTrainingId}
          title="测评推荐规则"
        />
      ) : null}
      {activeTab === "diaryTraining" ? (
        <TrainingMapRulesView
          content={diaryTrainingContent}
          selectedRule={selectedDiaryTrainingRule}
          selectedRuleId={selectedDiaryTrainingId}
          setSelectedRuleId={setSelectedDiaryTrainingId}
          title="日记推荐规则"
        />
      ) : null}
    </section>
  );
}

function FeedbackRulesView({
  selectedRule,
  setSelectedId,
}: {
  selectedRule?: FeedbackRule;
  setSelectedId: (id: string) => void;
}) {
  return (
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
                    {displayRisk(rule.risk_level)} · {displayStatus(rule.review_status)} · 推荐 {rule.recommended_card_ids.length} 张训练卡
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
              <DetailRow label="内容版本" value={selectedRule.version} />
              <DetailRow label="理论来源" value={selectedRule.theory_source} />
              <DetailRow label="审核状态" value={displayStatus(selectedRule.review_status)} />
              <DetailRow label="启用状态" value={selectedRule.enabled === false ? "停用" : "启用"} />
              <DetailRow label="规则解释" value={selectedRule.explanation} />
              <DetailRow label="支持性反馈" value={selectedRule.supportive_feedback} />
              <DetailRow label="边界说明" value={selectedRule.boundary_notice} />
              <DetailRow label="推荐训练卡" value={trainingCardNames(selectedRule.recommended_card_ids)} />

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
  );
}

function TrainingMapRulesView({
  content,
  selectedRule,
  selectedRuleId,
  setSelectedRuleId,
  title,
}: {
  content: TrainingMapContent;
  selectedRule?: TrainingMapRule;
  selectedRuleId?: string;
  setSelectedRuleId: (id: string) => void;
  title: string;
}) {
  return (
    <div className="dashboardGrid goalsGrid">
      <section className="listPanel" aria-label={`${title}列表`}>
        <div className="sectionTitleRow">
          <h2>{title}</h2>
          <span className="countBadge">{content.version}</span>
        </div>

        {content.rules.length === 0 ? (
          <div className="emptyState">当前没有推荐规则。请检查内容库是否已初始化。</div>
        ) : (
          <div className="recordList">
            {content.rules.map((rule) => (
              <button
                className={`recordItem ${selectedRuleId === rule.rule_id ? "active" : ""}`}
                key={rule.rule_id}
                type="button"
                onClick={() => setSelectedRuleId(rule.rule_id)}
              >
                <span className="recordScene">{rule.theme.join(" · ") || "推荐规则"}</span>
                <span className="recordDescription">{rule.reason}</span>
                <span className="recordMeta">
                  {displaySourceType(rule.source_type)} · {displayStatus(rule.review_status)} · 推荐 {rule.recommended_card_ids.length} 张训练卡
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="detailPanel" aria-label={`${title}详情`}>
        <div className="sectionTitleRow">
          <h2>推荐规则详情</h2>
          {selectedRule && <span className="countBadge">ID {selectedRule.rule_id}</span>}
        </div>

        {selectedRule ? (
          <div className="detailContent">
            <DetailRow label="规则来源" value={displaySourceType(selectedRule.source_type)} />
            <DetailRow label="审核状态" value={displayStatus(selectedRule.review_status)} />
            <DetailRow label="触发条件" value={JSON.stringify(selectedRule.trigger_condition)} />
            <DetailRow label="主题" value={selectedRule.theme.join("、")} />
            <DetailRow label="推荐训练卡" value={trainingCardNames(selectedRule.recommended_card_ids)} />
            <DetailRow label="推荐理由" value={selectedRule.reason} />
            <DetailRow label="今日建议" value={selectedRule.today_suggestion} />
            <DetailRow label="长期建议" value={selectedRule.long_term_suggestion || "情绪日记规则不生成长期建议"} />
            <DetailRow label="不适合场景" value={selectedRule.not_suitable_when} />
            <DetailRow label="边界说明" value={selectedRule.boundary_notice} />

            <section className="guidanceBox" aria-label="规则边界">
              <h3>规则边界</h3>
              <p>{content.boundary_notice}</p>
              <p>推荐规则只作为支持性练习建议；高风险或现实安全风险场景不得用普通训练卡替代现实支持和人工支持。</p>
            </section>
          </div>
        ) : (
          <div className="emptyState">选择左侧推荐规则后，这里会显示详情。</div>
        )}
      </section>
    </div>
  );
}

function ProfileRulesView({
  selectedProfileRule,
  selectedProfileId,
  setSelectedProfileId,
}: {
  selectedProfileRule?: StudentProfileRule;
  selectedProfileId?: string;
  setSelectedProfileId: (id: string) => void;
}) {
  return (
    <div className="dashboardGrid goalsGrid">
      <section className="listPanel" aria-label="画像规则列表">
        <div className="sectionTitleRow">
          <h2>画像规则列表</h2>
          <span className="countBadge">{profileRulesContent.version}</span>
        </div>

        {profileRulesContent.rules.length === 0 ? (
          <div className="emptyState">当前没有画像规则。请检查内容库是否已初始化。</div>
        ) : (
          <div className="recordList">
            {profileRulesContent.rules.map((rule) => (
              <button
                className={`recordItem ${selectedProfileId === rule.id ? "active" : ""}`}
                key={rule.id}
                type="button"
                onClick={() => setSelectedProfileId(rule.id)}
              >
                <span className="recordScene">{rule.profile_name}</span>
                <span className="recordDescription">{rule.content?.explanation || "暂无解释摘要"}</span>
                <span className="recordMeta">
                  {rule.enabled ? "已启用" : "停用"} · 推荐 {rule.recommended_card_ids.length} 张训练卡
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="detailPanel" aria-label="画像规则详情">
        <div className="sectionTitleRow">
          <h2>画像规则详情</h2>
          {selectedProfileRule && <span className="countBadge">ID {selectedProfileRule.id}</span>}
        </div>

        {selectedProfileRule ? (
          <div className="detailContent">
            <DetailRow label="画像名称" value={selectedProfileRule.profile_name} />
            <DetailRow label="技术标识（仅研究）" value={selectedProfileRule.profile_code} />
            <DetailRow label="启用状态" value={selectedProfileRule.enabled ? "已启用" : "停用"} />
            <DetailRow label="风险提示" value={riskLabel(selectedProfileRule.risk_level)} />
            <DetailRow label="人工关注" value={selectedProfileRule.requires_review ? "需要" : "暂不需要"} />
            <DetailRow label="触发摘要" value={triggerSummary(selectedProfileRule)} />
            <DetailRow label="推荐训练卡" value={trainingCardNames(selectedProfileRule.recommended_card_ids)} />

            <section className="guidanceBox" aria-label="画像维度">
              <h3>维度摘要</h3>
              {selectedProfileRule.dimensions.map((dimension) => (
                <p key={dimension.key}>
                  <strong>{dimension.label}</strong>：{dimension.summary}（{dimension.level}）
                </p>
              ))}
            </section>

            <section className="guidanceBox" aria-label="边界说明">
              <h3>边界说明</h3>
              <p>{selectedProfileRule.content?.boundary_notice || "本规则只用于阶段性支持建议和练习推荐。"}</p>
            </section>
          </div>
        ) : (
          <div className="emptyState">选择左侧画像规则后，这里会显示详情。</div>
        )}
      </section>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
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
