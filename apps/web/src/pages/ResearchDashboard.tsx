import { useEffect, useMemo, useState } from "react";

import { ProfileRadarChart } from "../components/ProfileRadarChart";
import { RelationshipStatusBadge } from "../components/RelationshipStatusBadge";
import { ProfileScatterChart } from "../components/ProfileScatterChart";
import {
  formatSafeHomeError,
  SafeHomeApiClient,
  type ResearchParticipantDossier,
  type ResearchParticipantSummary,
} from "../services/safehomeApi";
import { getStoredAdminToken, setStoredAdminToken } from "../services/adminToken";
import { displayQualityStatus, displayStatus } from "../utils/displayLabels";
import type {
  AssessmentProfilePosition,
  AssessmentResult,
  Checkin,
  EmotionDiary,
  Goal,
  RiskReviewRecord,
  RelationshipPilotEnrollment,
  RelationshipScreeningReport,
  StudentProfileRecord,
  TrainingCard,
} from "../../../../shared/types/api";

type LoadStatus = "idle" | "loading" | "success" | "error";

interface OverviewState {
  status: LoadStatus;
  message: string;
  goals: Goal[];
  diaries: EmotionDiary[];
  checkins: Checkin[];
  cards: TrainingCard[];
  riskReviews: RiskReviewRecord[];
  profiles: StudentProfileRecord[];
  assessmentResults: AssessmentResult[];
  selectedAssessmentResultId: string;
  profilePosition: AssessmentProfilePosition | null;
  relationshipEnrollments: RelationshipPilotEnrollment[];
  selectedRelationshipEnrollment: RelationshipPilotEnrollment | null;
  relationshipReport: RelationshipScreeningReport | null;
  textAnalysis: Record<string, Record<string, unknown>>;
}

interface TodoItem {
  title: string;
  value: string | number;
  note: string;
  href?: string;
}

const api = new SafeHomeApiClient();

const COMPLETED_ADMIN_PAGES = [
  { path: "/dashboard", label: "总览", note: "研究者平台运行概况" },
  { path: "/goals", label: "目标管理", note: "查看小程序端目标设定" },
  { path: "/diaries", label: "情绪记录", note: "查看记录列表、详情、反馈和训练卡推荐" },
  { path: "/feedback", label: "反馈结果", note: "通过导出接口查看已生成反馈" },
  { path: "/checkins", label: "练习记录", note: "查看训练卡练习尝试" },
  { path: "/reports", label: "周报记录", note: "通过导出接口查看已生成周报" },
  { path: "/supervision", label: "督导请求", note: "通过导出接口查看人工督导请求" },
  { path: "/content/worksheets", label: "测评题库", note: "管理小程序实际读取的测评入口和画像绑定" },
  { path: "/content/cards", label: "训练卡", note: "只读查看训练卡内容" },
  { path: "/content/rules", label: "反馈规则", note: "只读查看反馈规则边界和支持性反馈" },
  { path: "/export", label: "数据导出", note: "复用后台 CSV 导出接口" },
];

const DEFERRED_ADMIN_PAGES: Array<{ path: string; label: string; note: string }> = [];

function formatTime(value?: string | null) {
  if (!value) {
    return "未记录";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function toDate(value?: string | null) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function dateKey(date: Date) {
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function isToday(value?: string | null) {
  const date = toDate(value);
  if (!date) {
    return false;
  }
  return dateKey(date) === dateKey(new Date());
}

function isThisWeek(value?: string | null) {
  const date = toDate(value);
  if (!date) {
    return false;
  }

  const today = new Date();
  const start = new Date(today);
  const day = today.getDay() === 0 ? 6 : today.getDay() - 1;
  start.setDate(today.getDate() - day);
  start.setHours(0, 0, 0, 0);

  const end = new Date(start);
  end.setDate(start.getDate() + 7);
  return date >= start && date < end;
}

function isOpenRiskReview(item: RiskReviewRecord) {
  return !["reviewed", "closed"].includes(item.review_status);
}

function isOpenProfileReview(item: StudentProfileRecord) {
  const latestStatus = item.latest_review?.review_status;
  return Boolean(item.requires_review) && !["reviewed", "closed"].includes(latestStatus || "");
}

export function ResearchDashboard() {
  const [adminToken, setAdminToken] = useState(getStoredAdminToken);
  const [participantSearch, setParticipantSearch] = useState("");
  const [participantMatrix, setParticipantMatrix] = useState<ResearchParticipantSummary[]>([]);
  const [participantDossier, setParticipantDossier] = useState<ResearchParticipantDossier | null>(null);
  const [state, setState] = useState<OverviewState>({
    status: "idle",
    message: "正在准备研究者平台总览。",
    goals: [],
    diaries: [],
    checkins: [],
    cards: [],
    riskReviews: [],
    profiles: [],
    assessmentResults: [],
    selectedAssessmentResultId: "",
    profilePosition: null,
    relationshipEnrollments: [],
    selectedRelationshipEnrollment: null,
    relationshipReport: null,
    textAnalysis: {},
  });

  const latestDiary = state.diaries[0];
  const latestGoal = state.goals[0];
  const activeGoals = useMemo(() => state.goals.filter((goal) => goal.status === "active"), [state.goals]);
  const completedCheckins = useMemo(() => state.checkins.filter((checkin) => checkin.completed === 1), [state.checkins]);
  const todayDiaries = useMemo(() => state.diaries.filter((diary) => isToday(diary.created_at)), [state.diaries]);
  const todayHighRiskReviews = useMemo(
    () => state.riskReviews.filter((item) => item.risk_level === "high" && isToday(item.created_at)),
    [state.riskReviews],
  );
  const todayHighRiskProfiles = useMemo(
    () => state.profiles.filter((item) => item.risk_level === "high" && isToday(item.created_at)),
    [state.profiles],
  );
  const pendingRiskReviews = useMemo(() => state.riskReviews.filter(isOpenRiskReview), [state.riskReviews]);
  const pendingProfileReviews = useMemo(() => state.profiles.filter(isOpenProfileReview), [state.profiles]);
  const weeklyCheckins = useMemo(() => state.checkins.filter((checkin) => isThisWeek(checkin.created_at)), [state.checkins]);
  const todoItems: TodoItem[] = [
    {
      title: "今日新增记录",
      value: todayDiaries.length,
      note: todayDiaries.length > 0 ? "优先查看是否需要补充反馈或训练卡建议。" : "今天暂未读取到新的情绪记录。",
      href: "/diaries",
    },
    {
      title: "今日高风险",
      value: todayHighRiskReviews.length + todayHighRiskProfiles.length,
      note: "只显示数量，不展示高风险原文；请进入复核或画像页面查看处置状态。",
      href: "/reviews",
    },
    {
      title: "待人工复核",
      value: pendingRiskReviews.length + pendingProfileReviews.length,
      note: "包含风险复核队列和需复核画像。",
      href: "/reviews",
    },
    {
      title: "本周练习尝试",
      value: weeklyCheckins.length,
      note: "用于观察练习积累，不作为完成率或考核。",
      href: "/checkins",
    },
    {
      title: "最近导出记录",
      value: "待接入",
      note: "导出操作已保留审计记录，当前还没有前端列表入口。",
      href: "/export",
    },
    {
      title: "内容文件异常",
      value: "需运行脚本",
      note: "提交前运行 python backend\\scripts\\validate_content.py。",
    },
  ];

  async function loadOverview() {
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取目标、记录、练习、风险复核和训练卡数据...",
    }));

    try {
      const [goals, diaries, checkins, cards, riskReviews, profiles, assessmentResults, relationshipPilot, textAnalysis, researchParticipants] = await Promise.all([
        api.listGoals(),
        api.listDiaries({ limit: 50 }),
        api.listCheckins({ limit: 50 }),
        api.listCards(),
        api.listRiskReviews({ limit: 50 }, getStoredAdminToken().trim()),
        api.listProfileResults({ limit: 50 }, getStoredAdminToken().trim()),
        api.listAdminAssessmentResults({ limit: 50 }, getStoredAdminToken().trim()),
        api.getRelationshipResearchDashboard(getStoredAdminToken().trim()),
        api.getTextAnalysisSummary().catch(() => ({ items: {}, raw_text_included: false, boundary_notice: "离线分析摘要暂不可用。" })),
        api.listResearchParticipants({ limit: 100 }, getStoredAdminToken().trim()),
      ]);
      const firstParticipant = researchParticipants.items[0];
      const firstDossier = firstParticipant
        ? await api.getResearchParticipant(firstParticipant.user_id, getStoredAdminToken().trim())
        : null;
      setParticipantMatrix(researchParticipants.items);
      setParticipantDossier(firstDossier);
      const firstAssessment = assessmentResults.items[0];
      const profilePosition = firstAssessment
        ? await api.getAssessmentProfilePosition(firstAssessment.id, { user_id: firstAssessment.user_id })
        : null;
      const firstRelationship = relationshipPilot.items[0];
      const selectedRelationshipEnrollment = firstRelationship
        ? await api.getRelationshipEnrollment(firstRelationship.id, getStoredAdminToken().trim())
        : null;
      const firstRelationshipReportId = selectedRelationshipEnrollment?.reports?.[0]?.id;
      const relationshipReport = firstRelationshipReportId
        ? await api.getRelationshipReport(firstRelationshipReportId, getStoredAdminToken().trim())
        : null;

      setState({
        status: "success",
        message: "已读取研究者平台总览数据。",
        goals: goals.items,
        diaries: diaries.items,
        checkins: checkins.items,
        cards: cards.items,
        riskReviews: riskReviews.items,
        profiles: profiles.items,
        assessmentResults: assessmentResults.items,
        selectedAssessmentResultId: firstAssessment?.id || "",
        profilePosition,
        relationshipEnrollments: relationshipPilot.items,
        selectedRelationshipEnrollment,
        relationshipReport,
        textAnalysis: textAnalysis.items || {},
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: formatSafeHomeError(error, "读取失败，请确认 backend 是否已启动。"),
      }));
    }
  }

  useEffect(() => {
    void loadOverview();
  }, []);

  async function selectAssessmentResult(resultId: string) {
    const selected = state.assessmentResults.find((item) => item.id === resultId);
    setState((current) => ({ ...current, selectedAssessmentResultId: resultId, profilePosition: null }));
    if (!selected) {
      return;
    }
    try {
      const profilePosition = await api.getAssessmentProfilePosition(selected.id, { user_id: selected.user_id });
      setState((current) => ({ ...current, profilePosition }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: formatSafeHomeError(error, "读取画像落点失败。"),
      }));
    }
  }

  async function selectRelationshipEnrollment(enrollmentId: string) {
    try {
      const enrollment = await api.getRelationshipEnrollment(enrollmentId, getStoredAdminToken().trim());
      const reportId = enrollment.reports?.[0]?.id;
      const relationshipReport = reportId
        ? await api.getRelationshipReport(reportId, getStoredAdminToken().trim())
        : null;
      setState((current) => ({ ...current, selectedRelationshipEnrollment: enrollment, relationshipReport }));
    } catch (error) {
      setState((current) => ({ ...current, status: "error", message: formatSafeHomeError(error, "读取关系试点档案失败。") }));
    }
  }

  async function confirmRelationshipReport() {
    if (!state.relationshipReport) return;
    const report = await api.confirmRelationshipReport(state.relationshipReport.id, getStoredAdminToken().trim());
    setState((current) => ({ ...current, relationshipReport: report }));
  }

  async function sendRelationshipReport() {
    if (!state.relationshipReport) return;
    await api.sendRelationshipReport(state.relationshipReport.id, getStoredAdminToken().trim());
    setState((current) => ({ ...current, message: "关系初筛报告已发送到用户消息。" }));
  }

  async function addRelationshipNote() {
    if (!state.selectedRelationshipEnrollment) return;
    const note = window.prompt("请输入仅供研究者使用的访谈备注：")?.trim();
    if (!note) return;
    await api.createRelationshipResearchNote(state.selectedRelationshipEnrollment.id, note, getStoredAdminToken().trim());
    await selectRelationshipEnrollment(state.selectedRelationshipEnrollment.id);
  }

  async function searchParticipants() {
    try {
      const payload = await api.listResearchParticipants(
        { q: participantSearch.trim(), limit: 100 },
        getStoredAdminToken().trim(),
      );
      setParticipantMatrix(payload.items);
      const selected = payload.items[0]
        ? await api.getResearchParticipant(payload.items[0].user_id, getStoredAdminToken().trim())
        : null;
      setParticipantDossier(selected);
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: formatSafeHomeError(error, "参与者档案暂时无法读取。"),
      }));
    }
  }

  async function selectParticipant(userId: string) {
    try {
      setParticipantDossier(await api.getResearchParticipant(userId, getStoredAdminToken().trim()));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: formatSafeHomeError(error, "参与者档案暂时无法读取。"),
      }));
    }
  }

  return (
    <section className="dashboardShell" aria-label="研究者平台总览">
      <div className="dashboardHeader">
        <div>
          <p className="eyebrow">Research Platform</p>
          <h1>研究者平台总览</h1>
          <p className="summary">用于快速查看试点运行状态。这里不展示诊断性标签，也不替代正式研究数据审查。</p>
        </div>
        <div className="dashboardActions">
          <a className="secondaryButton" href="/diaries">
            查看情绪记录
          </a>
          <button className="primaryButton" type="button" onClick={loadOverview} disabled={state.status === "loading"}>
            {state.status === "loading" ? "刷新中..." : "刷新总览"}
          </button>
        </div>
      </div>

      <div className={`status ${state.status}`}>{state.message}</div>

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

      <section className="guidanceBox" aria-label="今日待处理">
        <div className="sectionTitleRow">
          <h2>今日待处理</h2>
          <span className="countBadge">P2-06</span>
        </div>
        <div className="recordList">
          {todoItems.map((item) =>
            item.href ? (
              <a className="recordItem textLink" href={item.href} key={item.title}>
                <span className="recordScene">{item.title}</span>
                <span className="recordDescription">{item.note}</span>
                <span className="recordMeta">{item.value}</span>
              </a>
            ) : (
              <div className="recordItem" key={item.title}>
                <span className="recordScene">{item.title}</span>
                <span className="recordDescription">{item.note}</span>
                <span className="recordMeta">{item.value}</span>
              </div>
            ),
          )}
        </div>
      </section>

      <div className="metricGrid" aria-label="总览指标">
        <MetricCard label="目标总数" value={state.goals.length} />
        <MetricCard label="进行中目标" value={activeGoals.length} />
        <MetricCard label="情绪记录" value={state.diaries.length} />
        <MetricCard label="已记录尝试" value={completedCheckins.length} />
      </div>

      <div className="metricGrid" aria-label="内容与练习指标">
        <MetricCard label="训练卡" value={state.cards.length} />
        <MetricCard label="尝试记录" value={state.checkins.length} />
        <MetricCard label="已关联目标记录" value={state.diaries.filter((diary) => diary.goal_id).length} />
        <MetricCard label="测评结果" value={state.assessmentResults.length} />
      </div>

      <section className="researchAnalysisDeck" aria-label="离线研究分析">
        <div className="analysisDeckHeader">
          <div>
            <p className="eyebrow">Offline Research Lens</p>
            <h2>情绪线索、语义网络与家庭拓扑</h2>
          </div>
          <span>只读聚合 · 不含原文</span>
        </div>
        <div className="analysisTrack">
          <AnalysisCard title="情感计算" code="AFFECT" artifact={state.textAnalysis.features || state.textAnalysis.summary} description="观察文本中的情绪类别、效价、唤醒与强度线索。" />
          <AnalysisCard title="语义共现网络" code="SEMANTIC" artifact={state.textAnalysis.semantic_network} description="观察人物、场景、情绪和行为概念在记录中的共同出现。" />
          <AnalysisCard title="家庭关系拓扑" code="TOPOLOGY" artifact={state.textAnalysis.family_topology} description="仅审计经授权、已确认且未撤回的结构化家庭绑定。" />
        </div>
        <p className="analysisBoundary">这些结果属于离线、脱敏、聚合研究线索；数据不足或质量门禁未通过时只显示状态，不生成个人或家庭结论。</p>
      </section>

      <section className="participantWorkspace" aria-label="参与者矩阵与单人档案">
        <div className="participantWorkspaceHeader">
          <div>
            <p className="eyebrow">Participant Matrix</p>
            <h2>参与者矩阵与单人全模块档案</h2>
            <p>按用户ID检索，在同一处查看测评、情绪日记、训练、项目、关系试点、人工支持和消息。</p>
          </div>
          <form
            className="participantSearch"
            onSubmit={(event) => {
              event.preventDefault();
              void searchParticipants();
            }}
          >
            <label>
              <span>用户ID或昵称</span>
              <input value={participantSearch} onChange={(event) => setParticipantSearch(event.target.value)} placeholder="输入用户ID" />
            </label>
            <button className="primaryButton" type="submit">查找</button>
          </form>
        </div>
        <div className="participantWorkspaceGrid">
          <div className="participantMatrixList">
            {participantMatrix.map((item) => (
              <button
                type="button"
                key={item.user_id}
                className={`participantMatrixRow ${participantDossier?.participant.user_id === item.user_id ? "active" : ""}`}
                onClick={() => void selectParticipant(item.user_id)}
              >
                <span className="participantIdentity">
                  <strong>{item.nickname || "未设置昵称"}</strong>
                  <small>{item.user_id}</small>
                </span>
                <span className="participantCounts">
                  测评 {item.assessment_count} · 日记 {item.diary_count} · 训练 {item.checkin_count} · 项目 {item.program_count}
                </span>
                <span className="participantAttention">
                  {item.supervision_count ? `人工支持 ${item.supervision_count}` : "暂无人工支持"}
                </span>
              </button>
            ))}
            {!participantMatrix.length ? <div className="emptyState">当前授权范围内没有匹配的参与者。</div> : null}
          </div>
          <div className="participantDossier">
            {participantDossier ? (
              <>
                <div className="participantDossierHead">
                  <div>
                    <h3>{participantDossier.participant.nickname || "参与者档案"}</h3>
                    <p>{participantDossier.participant.user_id}</p>
                  </div>
                  <span className="countBadge">审计事件 {participantDossier.audit_summary.related_event_count}</span>
                </div>
                <div className="dossierMetricGrid">
                  <DossierMetric label="测评" value={participantDossier.modules.assessments?.length || 0} />
                  <DossierMetric label="情绪日记" value={participantDossier.modules.diaries?.length || 0} />
                  <DossierMetric label="训练" value={participantDossier.modules.checkins?.length || 0} />
                  <DossierMetric label="项目练习" value={participantDossier.modules.program_entries?.length || 0} />
                  <DossierMetric label="关系试点" value={participantDossier.modules.relationship_enrollments?.length || 0} />
                  <DossierMetric label="人工支持" value={participantDossier.modules.supervision_requests?.length || 0} />
                </div>
                <DossierModuleSection title="测评记录" items={participantDossier.modules.assessments} primaryKeys={["worksheet_title", "total_score", "created_at"]} />
                <DossierModuleSection title="情绪日记" items={participantDossier.modules.diaries} primaryKeys={["scene", "event_description", "parent_emotion", "created_at"]} />
                <DossierModuleSection title="训练打卡" items={participantDossier.modules.checkins} primaryKeys={["card_id", "completed", "emotion_before", "emotion_after", "helpfulness_rating", "created_at"]} />
                <DossierModuleSection title="项目练习" items={participantDossier.modules.program_entries} primaryKeys={["program_title", "session_no", "reflection", "created_at"]} />
                <DossierModuleSection title="关系试点报名" items={participantDossier.modules.relationship_enrollments} primaryKeys={["status", "review_status", "created_at"]} />
                <DossierModuleSection title="关系试点任务" items={participantDossier.modules.relationship_tasks} primaryKeys={["task_type", "narration", "risk_level", "review_status", "created_at"]} />
                <DossierModuleSection title="关系阶段报告" items={participantDossier.modules.relationship_reports} primaryKeys={["version", "status", "confirmed_at", "created_at"]} />
                <DossierModuleSection title="人工支持" items={participantDossier.modules.supervision_requests} primaryKeys={["source_title", "message", "supervisor_reply", "status", "created_at"]} />
                <DossierModuleSection title="消息与阶段反馈" items={participantDossier.modules.messages} primaryKeys={["title", "body", "status", "created_at"]} />
                <p className="analysisBoundary">{participantDossier.boundary_notice}</p>
              </>
            ) : (
              <div className="emptyState">从左侧选择一位参与者查看档案。</div>
            )}
          </div>
        </div>
      </section>

      <section className="guidanceBox" aria-label="亲密关系项目试点档案">
        <div className="sectionTitleRow">
          <h2>亲密关系项目试点</h2>
          <span className="countBadge">{state.relationshipEnrollments.length} 份报名</span>
        </div>
        {state.relationshipEnrollments.length ? (
          <>
            <label className="tokenField">
              选择用户档案
              <select
                value={state.selectedRelationshipEnrollment?.id || ""}
                onChange={(event) => void selectRelationshipEnrollment(event.target.value)}
              >
                {state.relationshipEnrollments.map((item) => (
                  <option key={item.id} value={item.id}>{item.nickname || item.user_id} · {displayStatus(item.review_status)}</option>
                ))}
              </select>
            </label>
            {state.selectedRelationshipEnrollment ? (
              <div className="dashboardGrid overviewGrid">
                <section className="listPanel">
                  <h3>{state.selectedRelationshipEnrollment.profile.profile_name || "阶段性画像"}</h3>
                  <p>{state.selectedRelationshipEnrollment.profile.profile_description}</p>
                  <DetailRow label="量表" value={state.selectedRelationshipEnrollment.worksheet_id} />
                  <DetailRow label="线上材料" value={`${state.selectedRelationshipEnrollment.tasks?.length || 0} 份`} />
                  <DetailRow label="人工备注" value={`${state.selectedRelationshipEnrollment.research_notes?.length || 0} 条`} />
                  <h4>建议评估问题</h4>
                  <ul>{(state.selectedRelationshipEnrollment.profile.suggested_assessment_questions || []).map((question) => <li key={question}>{question}</li>)}</ul>
                  <button className="secondaryButton" type="button" onClick={() => void addRelationshipNote()}>新增人工备注</button>
                </section>
                <section className="detailPanel">
                  <h3>{state.relationshipReport?.report.title || "尚未生成初筛报告"}</h3>
                  {state.relationshipReport ? (
                    <>
                      <p>{state.relationshipReport.report.personalized_interpretation}</p>
                      <div className="detailRow"><span>报告状态</span><RelationshipStatusBadge status={state.relationshipReport.status} /></div>
                      <DetailRow label="版本" value={state.relationshipReport.version} />
                      <DetailRow label="基础画像" value={state.relationshipReport.report.four_layer_profile?.basic.stage_name || "暂无"} />
                      <DetailRow label="张力线索" value={state.relationshipReport.report.four_layer_profile?.tension.clues.join("；") || "暂无"} />
                      <DetailRow label="机制假设" value={state.relationshipReport.report.four_layer_profile?.mechanism.hypotheses.join("；") || "暂无"} />
                      <div className="dashboardActions">
                        {["confirmed", "updated"].includes(state.relationshipReport.status) ? (
                          <button className="primaryButton" type="button" onClick={() => void sendRelationshipReport()}>发送到用户消息</button>
                        ) : state.relationshipReport.status === "sent" ? (
                          <span className="muted">此版本已发送，如需更正请先生成更新版本。</span>
                        ) : (
                          <button className="secondaryButton" type="button" onClick={() => void confirmRelationshipReport()}>人工确认</button>
                        )}
                      </div>
                      <p className="muted">{state.relationshipReport.report.boundary_notice}</p>
                    </>
                  ) : <div className="emptyState">用户端或研究者端生成报告后可在这里复核。</div>}
                </section>
              </div>
            ) : null}
          </>
        ) : <div className="emptyState">当前还没有第二阶段报名记录。</div>}
      </section>

      <section className="guidanceBox" aria-label="测评画像落点">
        <div className="sectionTitleRow">
          <h2>测评画像落点</h2>
          <span className="countBadge">T4-03</span>
        </div>
        {state.assessmentResults.length > 0 ? (
          <>
            <label className="tokenField">
              选择测评结果
              <select
                value={state.selectedAssessmentResultId}
                onChange={(event) => {
                  void selectAssessmentResult(event.target.value);
                }}
              >
                {state.assessmentResults.map((result) => (
                  <option key={result.id} value={result.id}>
                    {result.worksheet_title} · {formatTime(result.created_at)}
                  </option>
                ))}
              </select>
            </label>
            <div className="dashboardGrid overviewGrid">
              <section className="listPanel" aria-label="画像散点图">
                <div className="sectionTitleRow">
                  <h3>群体位置</h3>
                  <span className="recordMeta">{state.profilePosition?.position?.profile_name || "暂无位置"}</span>
                </div>
                <ProfileScatterChart profile={state.profilePosition} />
              </section>
              <section className="detailPanel" aria-label="画像雷达图">
                <div className="sectionTitleRow">
                  <h3>维度轮廓</h3>
                  <span className="recordMeta">{state.profilePosition?.feature_summary?.data_quality || "暂无数据"}</span>
                </div>
                <ProfileRadarChart profile={state.profilePosition} />
              </section>
            </div>
            {state.profilePosition ? (
              <section className="guidanceBox" aria-label="画像解释字段">
                <h3>{state.profilePosition.position?.display_name || state.profilePosition.position?.profile_name || "阶段性画像"}</h3>
                <p>{state.profilePosition.explanation || state.profilePosition.interpretation?.message || "当前没有可展示的画像解释。"}</p>
                <DetailRow label="优势提示" value={state.profilePosition.strength_note || "暂无"} />
                <DetailRow label="下一小步" value={state.profilePosition.small_step || "暂无"} />
                <DetailRow label="置信度" value={String(state.profilePosition.position?.confidence ?? "暂无")} />
                {state.profilePosition.suggested_assessment_questions?.length ? (
                  <div className="overviewBlock">
                    <h4>建议评估问题</h4>
                    <ul>
                      {state.profilePosition.suggested_assessment_questions.map((question) => (
                        <li key={question}>{question}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {state.profilePosition.recommended_project_tasks?.length ? (
                  <DetailRow label="项目任务线索" value={state.profilePosition.recommended_project_tasks.join("；")} />
                ) : null}
                <a className="textLink" href="/content/worksheets">进入量表与画像人工复核</a>
                <p className="muted">{state.profilePosition.boundary_notice}</p>
              </section>
            ) : null}
            <p className="muted">
              画像落点只用于研究后台查看既往样本相对位置，不构成诊断、筛查或固定标签。
            </p>
          </>
        ) : (
          <div className="emptyState">当前匿名用户下还没有可查看的测评结果。</div>
        )}
      </section>

      <div className="dashboardGrid overviewGrid">
        <section className="listPanel" aria-label="最近情绪记录">
          <div className="sectionTitleRow">
            <h2>最近情绪记录</h2>
            <a className="textLink" href="/diaries">
              查看全部
            </a>
          </div>
          {latestDiary ? (
            <div className="overviewBlock">
              <span className="recordMeta">{formatTime(latestDiary.created_at)}</span>
              <h3>{latestDiary.scene}</h3>
              <p>{latestDiary.event_description}</p>
              <p className="muted">家长情绪：{latestDiary.parent_emotion} / 强度 {latestDiary.parent_emotion_intensity}</p>
            </div>
          ) : (
            <div className="emptyState">还没有情绪记录。</div>
          )}
        </section>

        <section className="detailPanel" aria-label="最近目标">
          <div className="sectionTitleRow">
            <h2>最近目标</h2>
            <a className="textLink" href="/goals">
              查看目标
            </a>
          </div>
          {latestGoal ? (
            <div className="overviewBlock">
              <span className="recordMeta">{formatTime(latestGoal.created_at)} · {displayStatus(latestGoal.status)}</span>
              <h3>{latestGoal.scene}</h3>
              <p>{latestGoal.smart_goal}</p>
              <p className="muted">{latestGoal.motivation || "未填写练习动机"}</p>
            </div>
          ) : (
            <div className="emptyState">还没有目标。</div>
          )}
        </section>
      </div>

      <div className="dashboardGrid overviewGrid">
        <section className="listPanel" aria-label="已完成后台页面">
          <div className="sectionTitleRow">
            <h2>已完成页面</h2>
            <span className="countBadge">{COMPLETED_ADMIN_PAGES.length} 个</span>
          </div>
          <div className="recordList">
            {COMPLETED_ADMIN_PAGES.map((page) => (
              <a className="recordItem textLink" href={page.path} key={page.path}>
                <span className="recordScene">{page.label}</span>
                <span className="recordDescription">{page.note}</span>
                <span className="recordMeta">{page.path}</span>
              </a>
            ))}
          </div>
        </section>

        <section className="detailPanel" aria-label="暂缓后台页面">
          <div className="sectionTitleRow">
            <h2>暂缓页面</h2>
            <span className="countBadge">{DEFERRED_ADMIN_PAGES.length} 个</span>
          </div>
          {DEFERRED_ADMIN_PAGES.length > 0 ? (
            <div className="recordList">
              {DEFERRED_ADMIN_PAGES.map((page) => (
                <a className="recordItem textLink" href={page.path} key={page.path}>
                  <span className="recordScene">{page.label}</span>
                  <span className="recordDescription">{page.note}</span>
                  <span className="recordMeta">{page.path}</span>
                </a>
              ))}
            </div>
          ) : (
            <div className="emptyState">当前没有明确暂缓的后台页面。</div>
          )}
        </section>
      </div>

      <section className="guidanceBox" aria-label="研究者平台边界">
        <h2>平台边界</h2>
        <p>
          当前总览只用于本地试点管理和数据完整性检查。正式研究导出前仍需进行权限控制、匿名化和脱敏处理。
        </p>
      </section>
    </section>
  );
}

function DossierMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="dossierMetric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

const DOSSIER_FIELD_LABELS: Record<string, string> = {
  worksheet_title: "测评",
  total_score: "记录值",
  card_id: "训练卡",
  completed: "是否完成",
  emotion_before: "练习前感受",
  emotion_after: "练习后感受",
  helpfulness_rating: "帮助程度",
  scene: "场景",
  event_description: "事件",
  parent_emotion: "主要情绪",
  program_title: "项目",
  session_no: "节次",
  reflection: "反思",
  review_status: "复核进度",
  task_type: "任务类型",
  narration: "参与者补充",
  risk_level: "风险提示",
  version: "报告版本",
  confirmed_at: "确认时间",
  source_title: "关联记录",
  message: "参与者说明",
  supervisor_reply: "人工反馈",
  title: "标题",
  body: "内容",
  status: "状态",
  created_at: "时间",
};

const DOSSIER_VALUE_LABELS: Record<string, string> = {
  pending: "待处理",
  replied: "已回复",
  closed: "已关闭",
  unread: "未读",
  read: "已读",
  completed: "已完成",
  paused: "已暂停",
  active: "进行中",
  pending_review: "待人工复核",
  priority_review: "优先复核",
  recorded: "已记录",
  ready: "可确认",
  confirmed: "已确认",
  sent: "已发送",
  updated: "有新版本",
  relationship_drawing: "关系绘画",
  sentence_completion: "情境句子补全",
  low: "常规关注",
  medium: "建议人工关注",
  high: "优先人工处理",
  true: "已完成",
  false: "未完成",
};

function dossierValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "未填写";
  const raw = String(value);
  return DOSSIER_VALUE_LABELS[raw] || raw;
}

function DossierModuleSection({
  title,
  items = [],
  primaryKeys,
}: {
  title: string;
  items?: Array<Record<string, unknown>>;
  primaryKeys: string[];
}) {
  return (
    <section className="dossierModule">
      <div className="sectionTitleRow">
        <h4>{title}</h4>
        <span className="countBadge">{items.length} 条</span>
      </div>
      {items.length ? (
        <div className="dossierModuleList">
          {items.slice(0, 20).map((item, index) => (
            <article className="dossierRecord" key={String(item.id || index)}>
              {primaryKeys.map((key) =>
                item[key] !== undefined && item[key] !== null && item[key] !== "" ? (
                  <div className="dossierField" key={key}>
                    <span>{DOSSIER_FIELD_LABELS[key] || key}</span>
                    <p>{dossierValue(item[key])}</p>
                  </div>
                ) : null,
              )}
            </article>
          ))}
        </div>
      ) : (
        <p className="emptyState">暂无{title}。</p>
      )}
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

function AnalysisCard({
  title,
  code,
  artifact,
  description,
}: {
  title: string;
  code: string;
  artifact?: Record<string, unknown>;
  description: string;
}) {
  const status = String(artifact?.quality_status || artifact?.reason || "offline_output_missing");
  const count = Number(artifact?.record_count ?? artifact?.input_edge_count ?? 0);
  const privacyPassed = artifact?.privacy_gate_passed === true;
  const available = artifact?.available === true;
  return (
    <article className={`analysisCard ${available ? "isReady" : "isWaiting"}`}>
      <div className="analysisCode"><span>{code}</span><strong>{available ? "可查看" : "待数据"}</strong></div>
      <h3>{title}</h3>
      <p>{description}</p>
      <dl>
        <div><dt>质量状态</dt><dd>{displayQualityStatus(status)}</dd></div>
        <div><dt>有效记录</dt><dd>{Number.isFinite(count) ? count : 0}</dd></div>
        <div><dt>隐私门禁</dt><dd>{privacyPassed ? "通过" : "待验证"}</dd></div>
      </dl>
    </article>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="detailRow">
      <span className="detailLabel">{label}</span>
      <span className="detailValue">{value || "暂无"}</span>
    </div>
  );
}
