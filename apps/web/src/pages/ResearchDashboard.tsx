import { useEffect, useMemo, useState } from "react";

import { ProfileRadarChart } from "../components/ProfileRadarChart";
import { RelationshipStatusBadge } from "../components/RelationshipStatusBadge";
import { ProfileScatterChart } from "../components/ProfileScatterChart";
import {
  copySafeHomeErrorDiagnostic,
  formatSafeHomeError,
  SafeHomeApiError,
  SafeHomeApiClient,
  type ResearchParticipantDossier,
  type ResearchParticipantModuleKey,
  type ResearchParticipantModulePage,
  type ResearchParticipantSummary,
} from "../services/safehomeApi";
import { getStoredAdminToken, setStoredAdminToken } from "../services/adminToken";
import { getStoredAuthUser } from "../services/authState";
import { displayActorRole, displayNotificationRetry, displayQualityStatus, displayStatus, displayWorkAction, displayWorkPriority, displayWorkQueue } from "../utils/displayLabels";
import type {
  AssessmentProfilePosition,
  AssessmentResult,
  Checkin,
  EmotionDiary,
  Goal,
  RiskReviewRecord,
  RelationshipPilotEnrollment,
  RelationshipScreeningReport,
  ResearchOperationsSnapshot,
  ResearchDeliveryType,
  ResearchDeliveryWorkflow,
  ResearchQueuePage,
  ResearchQueueType,
  ResearchWorkItemAction,
  ResearchWorkItemDetail,
  ResearchWorkItemMetrics,
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
  operations: ResearchOperationsSnapshot | null;
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
  const [participantModule, setParticipantModule] = useState<ResearchParticipantModulePage | null>(null);
  const [participantModuleStatus, setParticipantModuleStatus] = useState<LoadStatus>("idle");
  const [operationsQueue, setOperationsQueue] = useState<ResearchQueuePage | null>(null);
  const [operationsQueueStatus, setOperationsQueueStatus] = useState<LoadStatus>("idle");
  const [selectedWorkItem, setSelectedWorkItem] = useState<ResearchWorkItemDetail | null>(null);
  const [workItemStatus, setWorkItemStatus] = useState<LoadStatus>("idle");
  const [workItemNote, setWorkItemNote] = useState("");
  const [participantMessageTitle, setParticipantMessageTitle] = useState("人工支持进度");
  const [participantMessageBody, setParticipantMessageBody] = useState("");
  const [deliveryType, setDeliveryType] = useState<ResearchDeliveryType>("stage_feedback");
  const [deliveryTitle, setDeliveryTitle] = useState("本阶段可以一起核对的变化");
  const [deliveryObservation, setDeliveryObservation] = useState("");
  const [deliveryEvidence, setDeliveryEvidence] = useState("");
  const [deliveryNextStep, setDeliveryNextStep] = useState("");
  const [deliveryOpenQuestion, setDeliveryOpenQuestion] = useState("");
  const [deliveryMessageBody, setDeliveryMessageBody] = useState("");
  const [deliveryWorkflow, setDeliveryWorkflow] = useState<ResearchDeliveryWorkflow | null>(null);
  const [deliveryBusy, setDeliveryBusy] = useState(false);
  const [resolutionCode, setResolutionCode] = useState("handled");
  const [transferAssigneeId, setTransferAssigneeId] = useState("");
  const [operationsMetrics, setOperationsMetrics] = useState<ResearchWorkItemMetrics | null>(null);
  const [lastError, setLastError] = useState<SafeHomeApiError | null>(null);
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
    operations: null,
  });

  const latestDiary = state.diaries[0];
  const canManageSensitiveWorkItems = Boolean(adminToken.trim()) || ["admin", "supervisor"].includes(getStoredAuthUser()?.role || "");
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
    setLastError(null);
    setState((current) => ({
      ...current,
      status: "loading",
      message: "正在读取目标、记录、练习、风险复核和训练卡数据...",
    }));

    try {
      const [goals, diaries, checkins, cards, riskReviews, profiles, assessmentResults, relationshipPilot, textAnalysis, researchParticipants, operations] = await Promise.all([
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
        api.getResearchOperations(getStoredAdminToken().trim()),
      ]);
      const firstParticipant = researchParticipants.items[0];
      const firstAssessment = assessmentResults.items[0];
      const firstRelationship = relationshipPilot.items[0];
      const [firstDossier, profilePosition, selectedRelationshipEnrollment] = await Promise.all([
        firstParticipant ? api.getResearchParticipant(firstParticipant.user_id, getStoredAdminToken().trim()) : Promise.resolve(null),
        firstAssessment ? api.getAssessmentProfilePosition(firstAssessment.id, { user_id: firstAssessment.user_id }) : Promise.resolve(null),
        firstRelationship ? api.getRelationshipEnrollment(firstRelationship.id, getStoredAdminToken().trim()) : Promise.resolve(null),
      ]);
      setParticipantMatrix(researchParticipants.items);
      setParticipantDossier(firstDossier);
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
        operations,
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

  async function loadOperationsQueue(queue: ResearchQueueType) {
    setOperationsQueueStatus("loading");
    try {
      const result = await api.getResearchQueue(queue, { page: 1, page_size: 20 }, getStoredAdminToken().trim());
      setOperationsQueue(result);
      setSelectedWorkItem(null);
      setOperationsMetrics(await api.getResearchWorkItemMetrics(7, getStoredAdminToken().trim()));
      setOperationsQueueStatus("success");
    } catch (error) {
      setLastError(error instanceof SafeHomeApiError ? error : null);
      setOperationsQueue(null);
      setOperationsQueueStatus("error");
      setState((current) => ({ ...current, message: formatSafeHomeError(error, "队列暂时无法读取。") }));
    }
  }

  async function openWorkItem(workItemId: string) {
    setWorkItemStatus("loading");
    try {
      setSelectedWorkItem(await api.getResearchWorkItem(workItemId, getStoredAdminToken().trim()));
      setWorkItemStatus("success");
    } catch (error) {
      setWorkItemStatus("error");
      setState((current) => ({ ...current, message: formatSafeHomeError(error, "工作项暂时无法读取。") }));
    }
  }

  async function runWorkItemAction(action: ResearchWorkItemAction, extra: Record<string, string> = {}) {
    if (!selectedWorkItem || !operationsQueue) return;
    setWorkItemStatus("loading");
    const idempotencyKey = `work-item:${selectedWorkItem.work_item.id}:${action}:${Date.now()}`;
    try {
      await api.actOnResearchWorkItem(
        selectedWorkItem.work_item.id,
        {
          action,
          expected_version: selectedWorkItem.work_item.version,
          idempotency_key: idempotencyKey,
          ...extra,
        },
        getStoredAdminToken().trim(),
      );
      setSelectedWorkItem(await api.getResearchWorkItem(selectedWorkItem.work_item.id, getStoredAdminToken().trim()));
      const refreshedQueue = await api.getResearchQueue(
        operationsQueue.queue,
        { page: operationsQueue.page, page_size: operationsQueue.page_size },
        getStoredAdminToken().trim(),
      );
      setOperationsQueue(refreshedQueue);
      setOperationsMetrics(await api.getResearchWorkItemMetrics(7, getStoredAdminToken().trim()));
      setWorkItemNote("");
      if (action === "send_participant_message") setParticipantMessageBody("");
      setWorkItemStatus("success");
    } catch (error) {
      setWorkItemStatus("error");
      setState((current) => ({ ...current, message: formatSafeHomeError(error, "工作项更新失败，请刷新后重试。") }));
    }
  }

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
      setDeliveryWorkflow(null);
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

  async function previewResearchDelivery() {
    const enrollment = state.selectedRelationshipEnrollment;
    if (!enrollment) return;
    setDeliveryBusy(true);
    setLastError(null);
    try {
      const content = deliveryType === "stage_feedback"
        ? {
            observation: deliveryObservation.trim(),
            evidence: deliveryEvidence.trim(),
            next_step: deliveryNextStep.trim(),
            open_question: deliveryOpenQuestion.trim(),
          }
        : { body: deliveryMessageBody.trim() };
      const nonce = Date.now();
      let workflow = deliveryWorkflow;
      if (!workflow || ["sent", "withdrawn"].includes(workflow.status) || workflow.delivery_type !== deliveryType) {
        workflow = await api.createResearchDelivery(
          { enrollment_id: enrollment.id, delivery_type: deliveryType, title: deliveryTitle.trim(), content },
          `web-delivery-create-${enrollment.id}-${nonce}`,
        );
      } else {
        workflow = await api.saveResearchDelivery(
          workflow.id,
          { expected_version: workflow.version, title: deliveryTitle.trim(), content },
          `web-delivery-save-${workflow.id}-${nonce}`,
        );
      }
      workflow = await api.runResearchDeliveryAction(
        workflow.id,
        "preview",
        workflow.version,
        `web-delivery-preview-${workflow.id}-${nonce}`,
      );
      setDeliveryWorkflow(workflow);
    } catch (error) {
      setLastError(error instanceof SafeHomeApiError ? error : null);
      setState((current) => ({ ...current, message: formatSafeHomeError(error, "交付预览生成失败。") }));
    } finally {
      setDeliveryBusy(false);
    }
  }

  async function runResearchDeliveryStep(action: "confirm" | "send" | "withdraw") {
    if (!deliveryWorkflow) return;
    setDeliveryBusy(true);
    try {
      const workflow = await api.runResearchDeliveryAction(
        deliveryWorkflow.id,
        action,
        deliveryWorkflow.version,
        `web-delivery-${action}-${deliveryWorkflow.id}-${Date.now()}`,
        action === "withdraw" ? { reason: "研究者发现内容需要重新核对" } : {},
      );
      setDeliveryWorkflow(workflow);
      setState((current) => ({
        ...current,
        message: action === "send" ? "已发送到参与者消息，并生成可审计回执。" : action === "confirm" ? "当前预览版本已确认，可以发送。" : "内容已撤回，历史版本仍保留。",
      }));
    } catch (error) {
      setLastError(error instanceof SafeHomeApiError ? error : null);
      setState((current) => ({ ...current, message: formatSafeHomeError(error, "交付操作失败。") }));
    } finally {
      setDeliveryBusy(false);
    }
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
      setParticipantModule(null);
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
      setParticipantModule(null);
    } catch (error) {
      setState((current) => ({
        ...current,
        status: "error",
        message: formatSafeHomeError(error, "参与者档案暂时无法读取。"),
      }));
    }
  }

  async function loadParticipantModule(moduleKey: ResearchParticipantModuleKey, page = 1) {
    if (!participantDossier) return;
    setParticipantModuleStatus("loading");
    try {
      const payload = await api.getResearchParticipantModule(
        participantDossier.participant.user_id,
        moduleKey,
        { page, page_size: 20 },
        getStoredAdminToken().trim(),
      );
      setParticipantModule((current) => page > 1 && current?.module === payload.module
        ? { ...payload, items: [...current.items, ...payload.items] }
        : payload);
      setParticipantModuleStatus("success");
    } catch (error) {
      setParticipantModuleStatus("error");
      setState((current) => ({ ...current, status: "error", message: formatSafeHomeError(error, "该档案标签暂时无法读取。") }));
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
      {state.status === "error" && lastError ? (
        <section className="errorDiagnosticCard" aria-label="错误诊断信息">
          <div>
            <strong>请求编号：{lastError.requestId || "未返回"}</strong>
            <span>客户端 {lastError.clientVersion} · 服务 {lastError.serviceVersion || "未知"} · 构建 {lastError.buildId || "未知"}</span>
            <span>发生时间：{lastError.occurredAt}</span>
          </div>
          <div className="errorDiagnosticActions">
            <button type="button" onClick={() => void loadOverview()}>重新加载</button>
            <button type="button" onClick={() => void copySafeHomeErrorDiagnostic(lastError)}>复制诊断信息</button>
          </div>
        </section>
      ) : null}

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

      {state.operations ? (
        <section className="operationsPanel" aria-label="研究运营与通知监控">
          <div className="operationsHeader">
            <div>
              <p className="eyebrow">Operations pulse</p>
              <h2>提醒与人工工作水位</h2>
              <p>先看需要处理的数量，再进入对应页面；这里不展示参与者原文或微信身份信息。</p>
            </div>
            <span className="countBadge">{state.operations.scope === "assigned_participants" ? "我的参与者" : "全部参与者"}</span>
          </div>
          <div className="operationsGrid">
            <OperationsMetric label="已授权提醒" value={state.operations.notification_preferences.accepted} tone="stable" />
            <OperationsMetric label="发送失败" value={state.operations.notification_deliveries.failed} tone={state.operations.notification_deliveries.failed ? "attention" : "stable"} />
            <OperationsMetric label="待阶段反馈" value={state.operations.backlog.stage_feedback} tone={state.operations.backlog.stage_feedback ? "attention" : "stable"} />
            <OperationsMetric label="待人工支持" value={state.operations.backlog.supervision} tone={state.operations.backlog.supervision ? "attention" : "stable"} />
            {state.operations.privacy_management_available ? <OperationsMetric label="待隐私处理" value={state.operations.backlog.privacy_requests} tone={state.operations.backlog.privacy_requests ? "attention" : "stable"} /> : null}
          </div>
          <div className="operationsDetails">
            <span>已发送 {state.operations.notification_deliveries.sent}</span>
            <span>待发送 {state.operations.notification_deliveries.pending + state.operations.notification_deliveries.sending}</span>
            <span>可重试 {state.operations.notification_deliveries.retry_queue}</span>
            <span>重试已用尽 {state.operations.notification_deliveries.exhausted}</span>
            <span>已过期未发 {state.operations.notification_deliveries.overdue}</span>
            <span>待风险复核 {state.operations.backlog.risk_review}</span>
            {state.operations.privacy_management_available ? <a href="/privacy-requests">处理隐私申请 {state.operations.backlog.privacy_requests}</a> : null}
          </div>
          <div className="operationsDetails" aria-label="队列下钻">
            <button className="pill muted" type="button" onClick={() => void loadOperationsQueue("notification_failed")}>查看发送失败</button>
            <button className="pill muted" type="button" onClick={() => void loadOperationsQueue("stage_feedback")}>查看阶段反馈</button>
            <button className="pill muted" type="button" onClick={() => void loadOperationsQueue("supervision")}>查看人工支持</button>
            <button className="pill muted" type="button" onClick={() => void loadOperationsQueue("risk_review")}>查看风险复核</button>
            <button className="pill muted" type="button" onClick={() => void loadOperationsQueue("feedback_review")}>查看不适反馈</button>
            {state.operations.privacy_management_available ? <button className="pill muted" type="button" onClick={() => void loadOperationsQueue("privacy_request")}>查看隐私申请</button> : null}
          </div>
          {operationsQueueStatus === "loading" ? <div className="status compact loading">正在读取队列...</div> : null}
          {operationsQueue ? (
            <div className="operationsWorkbench" aria-label="运营队列记录">
              <div className="operationsQueueColumn">
                <div className="operationsQueueTitle">
                  <strong>{operationsQueue.queue} · {operationsQueue.total ?? operationsQueue.items.length} 条</strong>
                  <span>按紧急程度与等待时间排序</span>
                </div>
                {operationsQueue.items.length ? operationsQueue.items.map((item) => (
                  <button
                    className={`workItemRow workItemRow--${item.priority}`}
                    key={item.work_item_id}
                    type="button"
                    aria-pressed={selectedWorkItem?.work_item.id === item.work_item_id}
                    onClick={() => void openWorkItem(item.work_item_id)}
                  >
                    <span className="workItemRowMain">
                      <strong>{item.title}</strong>
                      <small>{item.user_id} · 已等待 {item.wait_minutes} 分钟</small>
                      {item.retry_category ? <small>{displayNotificationRetry(item.retry_category)}{item.next_attempt_at ? ` · 下次 ${formatTime(item.next_attempt_at)}` : ""}</small> : null}
                    </span>
                    <span className="workItemRowState">{displayStatus(item.status)}</span>
                  </button>
                )) : <div className="operationsEmpty">当前队列为空，无需额外操作。</div>}
                <small className="operationsBoundary">{operationsQueue.boundary_notice}</small>
              </div>

              <div className="workItemDetail" aria-live="polite">
                {workItemStatus === "loading" ? <div className="status compact loading">正在同步工作项...</div> : null}
                {workItemStatus === "error" ? <div className="status compact error">工作项更新失败。{selectedWorkItem ? <button type="button" onClick={() => void openWorkItem(selectedWorkItem.work_item.id)}>重新读取</button> : null}</div> : null}
                {selectedWorkItem ? (
                  <>
                    <div className="workItemDetailHeader">
                      <div>
                        <span className="eyebrow">处置账本</span>
                        <h3>{displayWorkQueue(selectedWorkItem.work_item.queue_type)}</h3>
                      </div>
                      <span className="countBadge">{displayStatus(selectedWorkItem.work_item.status)}</span>
                    </div>
                    <dl className="workItemFacts">
                      <div><dt>参与者</dt><dd>{selectedWorkItem.work_item.user_id}</dd></div>
                      <div><dt>负责人</dt><dd>{selectedWorkItem.work_item.assignee_id || "尚未领取"}</dd></div>
                      <div><dt>优先级</dt><dd>{displayWorkPriority(selectedWorkItem.work_item.priority)}</dd></div>
                      <div><dt>版本</dt><dd>v{selectedWorkItem.work_item.version}</dd></div>
                    </dl>
                    <div className="workItemActions" aria-label="工作项状态操作">
                      {selectedWorkItem.work_item.status === "open" ? <button type="button" onClick={() => void runWorkItemAction("claim")}>领取</button> : null}
                      {["claimed", "processing", "waiting"].includes(selectedWorkItem.work_item.status) ? <>
                        <button type="button" onClick={() => void runWorkItemAction("renew")}>续租</button>
                        <button type="button" onClick={() => void runWorkItemAction("start_processing")}>处理中</button>
                        <button type="button" onClick={() => void runWorkItemAction("wait")}>等待补充</button>
                        <button type="button" onClick={() => void runWorkItemAction("return")}>退回队列</button>
                      </> : null}
                      {canManageSensitiveWorkItems && selectedWorkItem.work_item.status === "completed" ? <button type="button" onClick={() => void runWorkItemAction("close", { resolution_code: resolutionCode, note: workItemNote })}>关闭</button> : null}
                      {canManageSensitiveWorkItems && ["completed", "closed"].includes(selectedWorkItem.work_item.status) ? <button type="button" onClick={() => void runWorkItemAction("reopen", { note: workItemNote || "收到新情况，重新进入处理队列。" })}>重新打开</button> : null}
                      {selectedWorkItem.work_item.queue_type === "notification_failed" ? <>
                        <button type="button" onClick={() => void runWorkItemAction("retry_notification")}>安排重试</button>
                        {canManageSensitiveWorkItems && selectedWorkItem.work_item.status === "dead_letter" ? <button type="button" onClick={() => void runWorkItemAction("recover_notification", { note: workItemNote || "已人工核对后恢复。" })}>恢复死信</button> : null}
                      </> : null}
                    </div>
                    <label className="workItemField">
                      <span>内部处理说明</span>
                      <textarea value={workItemNote} maxLength={2000} onChange={(event) => setWorkItemNote(event.target.value)} placeholder="只记录必要的处理信息，不复制参与者原文。" />
                    </label>
                    {canManageSensitiveWorkItems ? (
                      <div className="workItemTransfer">
                        <label className="workItemField">
                          <span>转交给</span>
                          <input value={transferAssigneeId} onChange={(event) => setTransferAssigneeId(event.target.value)} placeholder="输入已获授权的研究者或督导ID" />
                        </label>
                        <button type="button" disabled={!transferAssigneeId.trim()} onClick={() => void runWorkItemAction("transfer", { assignee_id: transferAssigneeId.trim() })}>确认转交</button>
                      </div>
                    ) : null}
                    <label className="workItemField">
                      <span>处理结果</span>
                      <select value={resolutionCode} onChange={(event) => setResolutionCode(event.target.value)}>
                        <option value="handled">已完成当前处理</option>
                        <option value="participant_updated">已向参与者反馈进度</option>
                        <option value="transferred">已转交合适人员</option>
                        <option value="no_response">等待期内未收到补充</option>
                        <option value="duplicate">重复工作项已合并</option>
                      </select>
                    </label>
                    <div className="workItemFormActions">
                      <button type="button" disabled={!workItemNote.trim()} onClick={() => void runWorkItemAction("add_note", { note: workItemNote })}>保存内部说明</button>
                      {["claimed", "processing", "waiting"].includes(selectedWorkItem.work_item.status) ? <button type="button" disabled={!resolutionCode.trim()} onClick={() => void runWorkItemAction("complete", { resolution_code: resolutionCode, note: workItemNote })}>标记完成</button> : null}
                    </div>
                    {["stage_feedback", "supervision", "feedback_review"].includes(selectedWorkItem.work_item.queue_type) ? (
                      <fieldset className="participantMessageBox">
                        <legend>发送参与者可见消息</legend>
                        <label><span>标题</span><input value={participantMessageTitle} maxLength={60} onChange={(event) => setParticipantMessageTitle(event.target.value)} /></label>
                        <label><span>正文</span><textarea value={participantMessageBody} maxLength={2000} onChange={(event) => setParticipantMessageBody(event.target.value)} /></label>
                        <button type="button" disabled={!participantMessageTitle.trim() || !participantMessageBody.trim()} onClick={() => void runWorkItemAction("send_participant_message", { title: participantMessageTitle, body: participantMessageBody })}>发送到消息中心</button>
                      </fieldset>
                    ) : null}
                    <div className="workItemLedger">
                      <h4>处理轨迹</h4>
                      {selectedWorkItem.actions.length ? selectedWorkItem.actions.map((action) => <span key={action.id}>{formatTime(action.created_at)} · {displayActorRole(action.actor_role)} · {displayWorkAction(action.action)} · {displayStatus(action.to_status)}</span>) : <span>尚无处理动作</span>}
                      {selectedWorkItem.notes.map((note) => <span key={note.id}>{formatTime(note.created_at)} · {note.note_type === "internal" ? "内部说明" : "处理说明"} · {note.content}</span>)}
                    </div>
                    <p className="analysisBoundary">{selectedWorkItem.boundary_notice}</p>
                  </>
                ) : <div className="operationsEmpty">从左侧选择一条工作项查看处置轨迹。</div>}
              </div>
            </div>
          ) : null}
          {operationsMetrics ? (
            <div className="operationsMetrics" aria-label="近七天运营指标">
              <span>待处理 {operationsMetrics.totals.open}</span>
              <span>处理中 {operationsMetrics.totals.claimed + operationsMetrics.totals.processing + operationsMetrics.totals.waiting}</span>
              <span>已超时 {operationsMetrics.sla.overdue}</span>
              <span>租约过期 {operationsMetrics.sla.expired_leases}</span>
              <span>近7天新增 {operationsMetrics.trend.reduce((sum, item) => sum + item.opened, 0)}</span>
              <span>近7天关闭 {operationsMetrics.trend.reduce((sum, item) => sum + item.closed, 0)}</span>
              <small>{operationsMetrics.quality_boundary}</small>
            </div>
          ) : null}
          {state.operations.failure_reasons.length ? (
            <div className="operationsFailures" aria-label="发送失败原因代码">
              <strong>失败原因</strong>
              {state.operations.failure_reasons.map((item) => <span key={item.error_code}>{item.error_code} · {item.count}</span>)}
            </div>
          ) : null}
          <p className="analysisBoundary">{state.operations.boundary_notice}</p>
        </section>
      ) : null}

      <section className="participantWorkspace" aria-label="参与者矩阵与单人档案">
        <div className="participantWorkspaceHeader">
          <div>
            <p className="eyebrow">Participant Matrix</p>
            <h2>参与者矩阵与按需档案</h2>
            <p>先看匿名摘要，再按标签读取测评、日记、训练、项目、消息与支持资料。</p>
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
                  <small>{item.anonymous_id || item.user_id}</small>
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
                    <p>{participantDossier.participant.anonymous_id}</p>
                  </div>
                  <span className="countBadge">审计事件 {participantDossier.audit_summary.related_event_count}</span>
                </div>
                <div className="dossierMetricGrid">
                  {participantDossier.modules.map((item) => <DossierMetric key={item.key} label={item.label} value={item.count} />)}
                </div>
                <div className="dossierModuleTabs" aria-label="参与者档案标签">
                  {participantDossier.modules.map((item) => (
                    <button key={item.key} type="button" className={participantModule?.module === item.key ? "active" : ""} onClick={() => void loadParticipantModule(item.key)}>
                      {item.label} {item.count}
                    </button>
                  ))}
                </div>
                {participantModuleStatus === "loading" ? <div className="emptyState">正在按需读取当前标签…</div> : null}
                {participantModule ? (
                  <>
                    <DossierModuleSection title={participantModule.module_label} items={participantModule.items} primaryKeys={["title", "worksheet_title", "scene", "card_id", "status", "created_at"]} />
                    {participantModule.has_more ? <button type="button" className="secondaryButton" onClick={() => void loadParticipantModule(participantModule.module, participantModule.page + 1)}>加载下一页</button> : null}
                    <p className="analysisBoundary">{participantModule.boundary_notice}</p>
                  </>
                ) : <div className="emptyState">选择一个标签后才会读取详情，避免一次加载全部长文本。</div>}
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
              <>
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
              <section className="deliveryComposer" aria-label="研究者反馈与消息交付">
                <div className="sectionTitleRow">
                  <div>
                    <p className="eyebrow">受控交付</p>
                    <h3>草稿、预览、确认、发送</h3>
                  </div>
                  <span className="countBadge">不会覆盖原始填写</span>
                </div>
                <div className="deliveryRail" aria-label="交付进度">
                  {[
                    ["draft", "草稿"],
                    ["previewed", "预览"],
                    ["confirmed", "确认"],
                    ["sent", "发送"],
                  ].map(([status, label], index) => {
                    const order = ["draft", "previewed", "confirmed", "sent"];
                    const activeIndex = deliveryWorkflow ? order.indexOf(deliveryWorkflow.status) : 0;
                    return <span className={index <= activeIndex ? "active" : ""} key={status}><b>{index + 1}</b>{label}</span>;
                  })}
                </div>
                <div className="deliveryFormGrid">
                  <label>交付类型
                    <select value={deliveryType} onChange={(event) => { setDeliveryType(event.target.value as ResearchDeliveryType); setDeliveryWorkflow(null); }}>
                      <option value="stage_feedback">阶段性反馈</option>
                      <option value="participant_message">参与者消息</option>
                    </select>
                  </label>
                  <label>标题
                    <input value={deliveryTitle} maxLength={60} onChange={(event) => setDeliveryTitle(event.target.value)} />
                  </label>
                </div>
                {deliveryType === "stage_feedback" ? (
                  <div className="deliveryFormGrid">
                    <label>近期可观察到的变化<textarea value={deliveryObservation} maxLength={600} onChange={(event) => setDeliveryObservation(event.target.value)} /></label>
                    <label>可供共同核对的依据<textarea value={deliveryEvidence} maxLength={600} onChange={(event) => setDeliveryEvidence(event.target.value)} /></label>
                    <label>可以先尝试的一小步<textarea value={deliveryNextStep} maxLength={600} onChange={(event) => setDeliveryNextStep(event.target.value)} /></label>
                    <label>后续可继续讨论<textarea value={deliveryOpenQuestion} maxLength={400} onChange={(event) => setDeliveryOpenQuestion(event.target.value)} /></label>
                  </div>
                ) : (
                  <label className="deliveryWideField">消息正文<textarea value={deliveryMessageBody} maxLength={2000} onChange={(event) => setDeliveryMessageBody(event.target.value)} /></label>
                )}
                {deliveryWorkflow?.active_version ? (
                  <article className="deliveryPreview">
                    <div className="sectionTitleRow"><strong>{deliveryWorkflow.preview.title}</strong><span>第 {deliveryWorkflow.active_version.version_no} 版</span></div>
                    <p>{deliveryWorkflow.preview.body}</p>
                    <small>{deliveryWorkflow.preview.boundary_notice}</small>
                  </article>
                ) : null}
                <div className="dashboardActions">
                  {(!deliveryWorkflow || ["draft", "previewed"].includes(deliveryWorkflow.status)) ? <button type="button" className="secondaryButton" disabled={deliveryBusy} onClick={() => void previewResearchDelivery()}>生成并核对预览</button> : null}
                  {deliveryWorkflow?.status === "previewed" ? <button type="button" className="secondaryButton" disabled={deliveryBusy} onClick={() => void runResearchDeliveryStep("confirm")}>确认这个版本</button> : null}
                  {deliveryWorkflow?.status === "confirmed" ? <button type="button" className="primaryButton" disabled={deliveryBusy} onClick={() => void runResearchDeliveryStep("send")}>发送到参与者消息</button> : null}
                  {deliveryWorkflow?.status === "sent" ? <button type="button" className="secondaryButton" disabled={deliveryBusy} onClick={() => void runResearchDeliveryStep("withdraw")}>撤回并保留历史</button> : null}
                </div>
                {deliveryWorkflow?.message ? <p className="deliveryReceipt">交付回执：{displayStatus(deliveryWorkflow.message.status)} · 第 {deliveryWorkflow.message.delivery_version} 版 · {formatTime(deliveryWorkflow.sent_at)}</p> : null}
              </section>
              </>
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

function OperationsMetric({ label, value, tone }: { label: string; value: number; tone: "stable" | "attention" }) {
  return (
    <div className={`operationsMetric operationsMetric--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
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
