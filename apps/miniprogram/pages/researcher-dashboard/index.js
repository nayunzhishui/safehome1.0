const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, requireLogin } = require("../../utils/authGuard");
const { buildErrorDiagnostic, copyErrorDiagnostic } = require("../../utils/errorDiagnostics");

const api = createSafeHomeApi();

const WORKSPACES = [
  { id: "pending", label: "待处理", capability: "research.dashboard.read" },
  { id: "participants", label: "参与者", capability: "research.participant.read" },
  { id: "feedback", label: "反馈与消息", capability: "research.feedback.write" },
  { id: "analysis", label: "在线分析", capability: "research.analysis.read" },
  { id: "assessment", label: "评估证据", capability: "research.dashboard.read" },
  { id: "pilots", label: "试点项目", capability: "research.dashboard.read" },
  { id: "mine", label: "我的工作", capability: "research.dashboard.read" },
];

const QUEUES = [
  { id: "risk_review", label: "风险信号复核" },
  { id: "supervision", label: "人工支持" },
  { id: "stage_feedback", label: "阶段性反馈" },
  { id: "feedback_review", label: "不适反馈复核" },
  { id: "notification_failed", label: "消息发送恢复" },
];

const PRIORITY_ORDER = { urgent: 0, attention: 1, routine: 2 };
const PRIORITY_LABELS = { urgent: "优先处理", attention: "需要关注", routine: "常规" };
const DRAFT_PREFIX = "researcher_workspace_draft_v1:";
const MODULE_PRIMARY_FIELDS = ["title", "worksheet_title", "scene", "card_id", "message_type", "task_type", "status", "created_at"];

function moduleRows(items) {
  return (items || []).map((item) => ({
    ...item,
    displayLines: MODULE_PRIMARY_FIELDS
      .filter((key) => item[key] !== undefined && item[key] !== null && item[key] !== "")
      .slice(0, 4)
      .map((key) => `${key === "created_at" ? "时间" : key}：${String(item[key]).slice(0, 180)}`),
  }));
}

function emptyOperations() {
  return {
    scope: "assigned_participants",
    notification_deliveries: { failed: 0 },
    backlog: { stage_feedback: 0, supervision: 0, risk_review: 0, privacy_requests: 0 },
  };
}

function visibleWorkspaces(capabilityScope) {
  const ids = new Set((capabilityScope && capabilityScope.capability_ids) || []);
  const development = Boolean(capabilityScope && capabilityScope.development_exception_active);
  return WORKSPACES.filter((item) => development || ids.has(item.capability)).map((item) => ({ ...item }));
}

function queuePreview(results) {
  const failures = [];
  const items = [];
  let total = 0;
  results.forEach((result, index) => {
    const queue = QUEUES[index];
    if (result.status === "rejected") {
      failures.push({ id: queue.id, label: queue.label, requestId: buildErrorDiagnostic(result.reason).requestId || "" });
      return;
    }
    total += Number(result.value.total || result.value.count || 0);
    (result.value.items || []).forEach((item) => items.push({
      workItemId: item.work_item_id,
      queueType: queue.id,
      queueLabel: queue.label,
      title: item.title || queue.label,
      priority: item.priority || "routine",
      priorityText: PRIORITY_LABELS[item.priority] || PRIORITY_LABELS.routine,
      status: item.status || "open",
      waitMinutes: Number(item.wait_minutes || 0),
      dueAt: item.due_at || "",
    }));
  });
  items.sort((a, b) => (PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]) || (b.waitMinutes - a.waitMinutes));
  return { items, failures, total };
}

const STATUS_LABELS = {
  active: "进行中",
  completed: "已完成",
  paused: "已暂停",
  withdrawn: "已退出",
  pending_review: "待人工复核",
  priority_review: "优先复核",
  recorded: "已记录",
  ready: "可确认",
  confirmed: "已确认",
  sent: "已发送",
  updated: "有新版本",
};

function statusLabel(value) {
  const key = String(value || "");
  return STATUS_LABELS[key] || "待核对";
}

function syncTimeLabel(date = new Date()) {
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${hour}:${minute}`;
}

function normalizeDetail(detail) {
  const tasks = (detail.tasks || []).map((task) => ({
    ...task,
    typeText: task.task_type === "relationship_drawing" ? "关系绘画" : "句子补全",
    reviewStatusText: statusLabel(task.review_status),
    answerRows: Object.entries(task.answers || {}).map(([context, answer]) => ({ context, answer })),
    strokeCount: task.drawing_data && Array.isArray(task.drawing_data.strokes) ? task.drawing_data.strokes.length : 0,
  }));
  return {
    ...detail,
    statusText: statusLabel(detail.status),
    reviewStatusText: statusLabel(detail.review_status),
    tasks,
    drawingTask: tasks.find((task) => task.task_type === "relationship_drawing") || null,
    latestReport: (detail.reports || [])[0] || null,
  };
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    errorDiagnostic: null,
    workspaces: [],
    activeWorkspace: "pending",
    offline: false,
    lastSyncText: "尚未同步",
    operations: null,
    pendingItems: [],
    pendingTotal: 0,
    pendingVisibleItems: [],
    pendingPage: 1,
    pendingPageSize: 5,
    pendingHasMore: false,
    urgentCount: 0,
    assessmentQueueRuntime: null,
    assessmentDutyShifts: [],
    partialFailures: [],
    participantLoading: false,
    participantError: "",
    participantDiagnostic: null,
    participantQuery: "",
    participantItems: [],
    participantPage: 1,
    participantHasMore: false,
    participantDossier: null,
    participantModule: null,
    participantModuleLoading: false,
    pilotLoading: false,
    pilotError: "",
    pilotDiagnostic: null,
    items: [],
    selected: null,
    note: "",
    narrative: null,
    stageFeedbackForm: {
      observation: "",
      evidence: "",
      nextStep: "",
      openQuestion: "",
    },
    messageTitle: "研究者补充消息",
    messageBody: "",
    stageFeedbackDelivery: null,
    participantMessageDelivery: null,
    sendingMessage: false,
    sendingFeedback: false,
    developmentFullAccess: false,
    capabilityScope: null,
      analysisJobs: [],
    analysisCatalog: null,
    analysisResilience: null,
      analysisLoading: false,
    analysisError: "",
    affectModelVersions: [],
    affectShadowRuns: [],
    affectShadowReviewCount: 0,
    affectMonitoring: null,
    affectReleaseGate: null,
    assessmentLoading: false,
    assessmentError: "",
    assessmentCases: [],
    assessmentCaseId: "",
    assessmentWorkbench: null,
    assessmentFilters: { kind: "", review_status: "", visibility: "" },
    assessmentInternalNotes: "",
    assessmentParticipantDraft: "",
    assessmentSaving: false,
    assessmentAuthorization: {
      authorized: false,
      task_code: "workbench_draft",
      reason: "尚未确认任务授权",
    },
  },

  async onLoad() {
    if (!requireLogin({ redirectUrl: "/pages/researcher-dashboard/index" })) return;
    const user = getAuthUser();
    const [showcase, capabilityScope] = await Promise.all([
      api.getShowcaseAccess().catch(() => ({ enabled: false })),
      api.getResearchCapabilities().catch(() => null),
    ]);
    const workspaces = visibleWorkspaces(capabilityScope);
    this.setData({
      developmentFullAccess: Boolean(showcase.researcher_platform_full_access),
      capabilityScope,
      workspaces,
      activeWorkspace: workspaces.length ? workspaces[0].id : "pending",
    });
    if (!showcase.enabled && (!user || !["researcher", "admin", "supervisor"].includes(user.role))) {
      this.setData({ loading: false, errorMessage: "当前账号没有研究者权限。" });
      return;
    }
    this.bindNetworkState();
    await this.loadWorkbench();
  },

  onUnload() {
    if (this.networkHandler && wx.offNetworkStatusChange) wx.offNetworkStatusChange(this.networkHandler);
    if (this.searchTimer) clearTimeout(this.searchTimer);
  },

  async onPullDownRefresh() {
    try {
      await this.refreshActiveWorkspace();
    } finally {
      wx.stopPullDownRefresh();
    }
  },

  bindNetworkState() {
    wx.getNetworkType({
      success: (result) => this.setData({ offline: result.networkType === "none" }),
    });
    this.networkHandler = (result) => {
      this.setData({ offline: !result.isConnected });
      if (result.isConnected && this.data.errorMessage) this.loadWorkbench();
    };
    wx.onNetworkStatusChange(this.networkHandler);
  },

  async refreshActiveWorkspace() {
    if (this.data.activeWorkspace === "participants") {
      if (this.data.participantDossier && this.data.participantModule) return this.loadParticipantModule({ currentTarget: { dataset: { key: this.data.participantModule.module, page: 1 } } });
      return this.loadParticipants(true);
    }
    if (this.data.activeWorkspace === "pilots") return Promise.all([this.loadWorkbench(), this.loadDashboard()]);
    if (this.data.activeWorkspace === "assessment") return this.loadAssessmentCases();
    return this.loadWorkbench();
  },

  async switchWorkspace(event) {
    const id = event.currentTarget.dataset.id;
    if (!this.data.workspaces.some((item) => item.id === id)) return;
    this.setData({ activeWorkspace: id });
    if (id === "participants" && !this.data.participantItems.length) await this.loadParticipants(true);
    if (id === "pilots" && !this.data.items.length) await this.loadDashboard();
    if (id === "analysis" && !this.data.analysisJobs.length) await this.loadAnalysisJobs();
    if (id === "assessment" && !this.data.assessmentCases.length) await this.loadAssessmentCases();
  },

  async loadAssessmentCases() {
    this.setData({ assessmentLoading: true, assessmentError: "" });
    try {
      const result = await api.listTherapeuticAssessmentCases();
      const assessmentCases = (result.items || []).map((item) => ({
        ...item,
        displayQuestion: item.working_question || item.assessment_question,
      }));
      const assessmentCaseId = this.data.assessmentCaseId || (assessmentCases[0] && assessmentCases[0].id) || "";
      this.setData({ assessmentCases, assessmentCaseId });
      if (assessmentCaseId) await this.loadAssessmentWorkbench(assessmentCaseId);
    } catch (error) {
      this.setData({ assessmentError: error.message || "评估证据暂时无法读取。" });
    } finally {
      this.setData({ assessmentLoading: false });
    }
  },

  async loadAssessmentWorkbench(caseId = this.data.assessmentCaseId) {
    if (!caseId) return;
    this.setData({ assessmentLoading: true, assessmentError: "" });
    try {
      const result = await api.getTherapeuticAssessmentResearcherWorkbench(caseId, {
        ...this.data.assessmentFilters,
        page: 1,
        page_size: 20,
      });
      let assessmentAuthorization = {
        authorized: false,
        task_code: "workbench_draft",
        reason: "任务授权暂时无法确认，正式写入已按默认拒绝处理。",
      };
      try {
        assessmentAuthorization = await api.getTherapeuticAssessmentAuthorizationStatus(
          caseId,
          "workbench_draft",
        );
      } catch (_error) {
        // 工作台仍可只读；任务授权读取失败时保持写入默认拒绝。
      }
      const evidenceItems = (result.evidence_items || []).map((item) => ({
        ...item,
        kindLabel: { O: "观察", P: "模式候选", H: "人工假设", U: "未知项" }[item.kind] || item.kind,
        visibilityText: (item.visibility_scope || []).join("、"),
        supportingText: (item.supporting_evidence || []).map((entry) => entry.ref || String(entry)).join("；"),
        counterText: (item.counter_evidence || []).join("；"),
        alternativesText: (item.alternative_explanations || []).join("；"),
      }));
      this.setData({
        assessmentWorkbench: {
          ...result,
          case: {
            ...result.case,
            sharedScopeText: (result.case.shared_scope || []).join("、"),
          },
          evidence_items: evidenceItems,
        },
        assessmentInternalNotes: result.draft.internal_notes || "",
        assessmentParticipantDraft: result.draft.participant_visible_draft || "",
        assessmentAuthorization,
      });
    } catch (error) {
      this.setData({ assessmentError: error.message || "评估证据暂时无法读取。" });
    } finally {
      this.setData({ assessmentLoading: false });
    }
  },

  selectAssessmentCase(event) {
    const assessmentCaseId = event.currentTarget.dataset.id;
    this.setData({ assessmentCaseId });
    this.loadAssessmentWorkbench(assessmentCaseId);
  },

  onAssessmentFilter(event) {
    const key = event.currentTarget.dataset.key;
    const options = key === "kind"
      ? ["", "O", "P", "H", "U"]
      : ["", "participant", "research_team", "supervisor"];
    const assessmentFilters = {
      ...this.data.assessmentFilters,
      [key]: options[Number(event.detail.value)] || "",
    };
    this.setData({ assessmentFilters });
    this.loadAssessmentWorkbench(this.data.assessmentCaseId);
  },

  onAssessmentDraftInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value });
  },

  async saveAssessmentDraft() {
    const workbench = this.data.assessmentWorkbench;
    if (!workbench) return;
    if (!this.data.assessmentAuthorization.authorized) {
      wx.showToast({ title: "当前任务尚未获得正式授权", icon: "none" });
      return;
    }
    this.setData({ assessmentSaving: true });
    try {
      const draft = await api.saveTherapeuticAssessmentResearcherDraft(
        this.data.assessmentCaseId,
        {
          internal_notes: this.data.assessmentInternalNotes,
          participant_visible_draft: this.data.assessmentParticipantDraft,
          filters: this.data.assessmentFilters,
          expected_version: workbench.draft.version,
        },
        `mini-ta-workbench-${this.data.assessmentCaseId}-${Date.now()}`,
      );
      this.setData({ "assessmentWorkbench.draft": draft });
      wx.showToast({ title: "草稿已保存", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "保存失败", icon: "none" });
    } finally {
      this.setData({ assessmentSaving: false });
    }
  },

  openAssessmentQuality() {
    wx.navigateTo({ url: "/pages/therapeutic-assessment-quality/index" });
  },

  async loadAnalysisJobs() {
    this.setData({ analysisLoading: true, analysisError: "" });
    try {
      const [result, catalog, modelVersions, shadowRuns, shadowQueue, affectMonitoring, affectReleaseGate] = await Promise.all([
        api.getResearchAnalysisJobs({ limit: 30 }),
        api.getResearchAnalysisCatalog(),
        api.listOfflineModelVersions(),
        api.listOfflineModelShadowRuns(),
        api.listOfflineModelReviewQueue(),
        api.getOfflineModelMonitoring(),
        api.getOfflineModelReleaseGate(),
      ]);
      const labels = {
        affect_aggregate: "聚合情感线索",
        semantic_network: "语义网络",
        family_topology: "家庭关系拓扑",
      };
      const statuses = {
        queued: "等待执行",
        running: "正在运行",
        succeeded: "已有结果",
        failed: "执行失败",
        canceled: "已取消",
        expired: "已过期",
        suspended: "已冻结",
      };
      this.setData({
        analysisJobs: (result.items || []).map((item) => ({
          ...item,
          analysisLabel: labels[item.analysis_type] || item.analysis_type,
          statusLabel: statuses[item.status] || "待核对",
          createdText: String(item.created_at || "").slice(0, 16).replace("T", " "),
          qualityText: item.artifact
            ? `覆盖 ${Math.round(Number(item.artifact.metrics.coverage_rate || 0) * 100)}% · 未知 ${Math.round(Number(item.artifact.metrics.unknown_rate || 0) * 100)}% · 样本 ${item.artifact.metrics.sample_size || 0}`
            : "",
          suppressed: Boolean(item.artifact && item.artifact.metrics && item.artifact.metrics.result && item.artifact.metrics.result.suppressed),
        })),
        analysisCatalog: catalog,
        analysisResilience: catalog.resilience_summary || null,
        affectModelVersions: modelVersions.items || [],
        affectShadowRuns: (shadowRuns.items || []).slice(0, 3).map((item) => ({
          ...item,
          coverageText: `${Math.round(Number(item.coverage_rate || 0) * 100)}%`,
          createdText: String(item.created_at || "").slice(0, 16).replace("T", " "),
        })),
        affectShadowReviewCount: (shadowQueue.items || []).length,
        affectMonitoring,
        affectReleaseGate,
      });
    } catch (error) {
      this.setData({ analysisError: error.message || "在线分析任务暂时无法读取。" });
    } finally {
      this.setData({ analysisLoading: false });
    }
  },

  async loadWorkbench() {
    if (this.data.offline) {
      this.setData({
        loading: false,
        errorMessage: this.data.operations ? "" : "当前处于离线状态，已有内容会保留，联网后可重试。",
      });
      return;
    }
    this.setData({ loading: true, errorMessage: "", errorDiagnostic: null });
    const operationsPromise = api.getResearchOperations();
    const queuePromises = QUEUES.map((queue) => api.getResearchQueue({ queue: queue.id, page: 1, page_size: 20, status: "active" }));
    const [operationsResult, ...workbenchResults] = await Promise.allSettled([
      operationsPromise,
      ...queuePromises,
      api.getTherapeuticAssessmentQueueRuntime(),
      api.listTherapeuticAssessmentDutyShifts(),
    ]);
    const queueResults = workbenchResults.slice(0, QUEUES.length);
    const runtimeResult = workbenchResults[QUEUES.length];
    const dutyResult = workbenchResults[QUEUES.length + 1];
    const preview = queuePreview(queueResults);
    if (operationsResult.status === "rejected" && !preview.items.length && !this.data.operations) {
      this.setData({
        loading: false,
        errorMessage: operationsResult.reason.message || "移动工作台暂时无法读取。",
        errorDiagnostic: buildErrorDiagnostic(operationsResult.reason),
        partialFailures: preview.failures,
      });
      return;
    }
    const operations = operationsResult.status === "fulfilled" ? operationsResult.value : (this.data.operations || emptyOperations());
    const partialFailures = [...preview.failures];
    if (operationsResult.status === "rejected") {
      partialFailures.unshift({ id: "operations", label: "工作台摘要", requestId: buildErrorDiagnostic(operationsResult.reason).requestId || "" });
    }
    const pageSize = this.data.pendingPageSize;
    this.setData({
      loading: false,
      operations,
      pendingItems: preview.items,
      pendingTotal: preview.total,
      pendingVisibleItems: preview.items.slice(0, pageSize),
      pendingPage: 1,
      pendingHasMore: preview.items.length > pageSize,
      urgentCount: preview.items.filter((item) => item.priority === "urgent").length,
      assessmentQueueRuntime: runtimeResult.status === "fulfilled" ? runtimeResult.value : null,
      assessmentDutyShifts: dutyResult.status === "fulfilled" ? (dutyResult.value.items || []) : [],
      partialFailures,
      lastSyncText: syncTimeLabel(),
    });
  },

  showMorePending() {
    const nextPage = this.data.pendingPage + 1;
    const visibleCount = nextPage * this.data.pendingPageSize;
    this.setData({
      pendingPage: nextPage,
      pendingVisibleItems: this.data.pendingItems.slice(0, visibleCount),
      pendingHasMore: visibleCount < this.data.pendingItems.length,
    });
  },

  onParticipantQueryInput(event) {
    const participantQuery = event.detail.value || "";
    this.setData({ participantQuery });
    if (this.searchTimer) clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.loadParticipants(true), 350);
  },

  async loadParticipants(reset = false) {
    if (this.data.offline) {
      this.setData({ participantError: "当前离线，联网后再搜索参与者。" });
      return;
    }
    const page = reset ? 1 : this.data.participantPage + 1;
    this.setData({ participantLoading: true, participantError: "", participantDiagnostic: null });
    try {
      const payload = await api.getResearchParticipants({ q: this.data.participantQuery.trim(), page, page_size: 10 });
      const incoming = (payload.items || []).map((item) => ({
        ...item,
        displayName: item.nickname || item.user_id || "匿名参与者",
        anonymousId: item.anonymous_id || item.user_id,
        displayInitial: String(item.nickname || item.user_id || "匿").slice(0, 1),
        activityCount: Number(item.assessment_count || 0) + Number(item.diary_count || 0) + Number(item.checkin_count || 0) + Number(item.program_count || 0),
      }));
      this.setData({
        participantLoading: false,
        participantItems: reset ? incoming : [...this.data.participantItems, ...incoming],
        participantPage: page,
        participantHasMore: Boolean(payload.has_more),
      });
    } catch (error) {
      this.setData({ participantLoading: false, participantError: error.message || "参与者列表暂时无法读取。", participantDiagnostic: buildErrorDiagnostic(error) });
    }
  },

  retryParticipants() { return this.loadParticipants(true); },
  loadMoreParticipants() { return this.loadParticipants(false); },

  async selectParticipantDossier(event) {
    const userId = event.currentTarget.dataset.id;
    this.setData({ participantLoading: true, participantError: "", participantDossier: null, participantModule: null });
    try {
      const participantDossier = await api.getResearchParticipant(userId);
      this.setData({ participantLoading: false, participantDossier });
    } catch (error) {
      this.setData({ participantLoading: false, participantError: error.message || "参与者档案暂时无法读取。", participantDiagnostic: buildErrorDiagnostic(error) });
    }
  },

  closeParticipantDossier() {
    this.setData({ participantDossier: null, participantModule: null });
  },

  async loadParticipantModule(event) {
    if (!this.data.participantDossier) return;
    const moduleKey = event.currentTarget.dataset.key;
    const requestedPage = Number(event.currentTarget.dataset.page || 1);
    this.setData({ participantModuleLoading: true, participantError: "" });
    try {
      const payload = await api.getResearchParticipantModule(this.data.participantDossier.participant.user_id, moduleKey, { page: requestedPage, page_size: 10 });
      const items = moduleRows(payload.items);
      this.setData({
        participantModuleLoading: false,
        participantModule: requestedPage > 1 && this.data.participantModule && this.data.participantModule.module === moduleKey
          ? { ...payload, items: [...this.data.participantModule.items, ...items] }
          : { ...payload, items },
      });
    } catch (error) {
      this.setData({ participantModuleLoading: false, participantError: error.message || "该档案标签暂时无法读取。", participantDiagnostic: buildErrorDiagnostic(error) });
    }
  },

  async loadDashboard() {
    this.setData({ pilotLoading: true, pilotError: "", pilotDiagnostic: null });
    try {
      const payload = await api.getRelationshipResearchDashboard();
      const items = (payload.items || []).map((item) => ({
        ...item,
        scopeStatus: item.scope_status || "assigned",
        statusText: statusLabel(item.status),
        reviewStatusText: statusLabel(item.review_status),
      }));
      this.setData({ pilotLoading: false, pilotError: "", pilotDiagnostic: null, items });
      const firstAssigned = items.find((item) => item.scopeStatus !== "claimable");
      if (firstAssigned) await this.selectEnrollmentById(firstAssigned.id);
    } catch (error) {
      this.setData({ pilotLoading: false, pilotError: error.message || "试点项目暂时无法读取。", pilotDiagnostic: buildErrorDiagnostic(error) });
    }
  },

  async copyDiagnostic(event) {
    const scope = event && event.currentTarget && event.currentTarget.dataset.scope;
    const diagnostic = scope === "pilot"
      ? this.data.pilotDiagnostic
      : scope === "participants"
        ? this.data.participantDiagnostic
        : this.data.errorDiagnostic;
    try {
      await copyErrorDiagnostic(diagnostic || {});
      wx.showToast({ title: "诊断信息已复制", icon: "success" });
    } catch (error) {
      wx.showToast({ title: "复制失败", icon: "none" });
    }
  },

  async selectEnrollment(event) {
    const id = event.currentTarget.dataset.id;
    const item = this.data.items.find((row) => row.id === id);
    if (item && item.scopeStatus === "claimable") {
      const confirmed = await new Promise((resolve) => {
        wx.showModal({
          title: "领取参与者",
          content: "领取后你可以查看完整档案并留下研究反馈。",
          confirmText: "确认领取",
          success: (result) => resolve(Boolean(result.confirm)),
          fail: () => resolve(false),
        });
      });
      if (!confirmed) return;
      try {
        await api.claimResearchEnrollment(id, `mobile-claim-${id}-${Date.now()}`);
        await this.loadDashboard();
        await this.selectEnrollmentById(id);
      } catch (error) {
        wx.showToast({ title: error.message || "暂时无法领取", icon: "none" });
      }
      return;
    }
    this.selectEnrollmentById(id);
  },

  async selectEnrollmentById(id) {
    try {
      const detail = normalizeDetail(await api.getRelationshipEnrollment(id));
      const draft = this.readDraft(id);
      this.setData({
        selected: detail,
        narrative: null,
        note: draft.note || "",
        messageTitle: draft.messageTitle || "研究者补充消息",
        messageBody: draft.messageBody || "",
        stageFeedbackForm: draft.stageFeedbackForm || { observation: "", evidence: "", nextStep: "", openQuestion: "" },
        stageFeedbackDelivery: null,
        participantMessageDelivery: null,
      }, () => this.drawMaterial(detail.drawingTask));
    } catch (error) {
      wx.showToast({ title: error.message || "档案暂时无法读取", icon: "none" });
    }
  },

  drawMaterial(task) {
    if (!task || !task.drawing_data || !Array.isArray(task.drawing_data.strokes)) return;
    wx.createSelectorQuery().in(this).select(".material-canvas").boundingClientRect((rect) => {
      const width = rect && rect.width ? rect.width : 320;
      const height = rect && rect.height ? rect.height : 180;
      const sourceWidth = Number(task.drawing_data.canvas_width) || width;
      const sourceHeight = Number(task.drawing_data.canvas_height) || height;
      const ctx = wx.createCanvasContext("researchDrawingCanvas", this);
      ctx.scale(width / sourceWidth, height / sourceHeight);
      ctx.setStrokeStyle("#4e7c6b");
      ctx.setLineWidth(3);
      ctx.setLineCap("round");
      task.drawing_data.strokes.forEach((stroke) => {
        if (!stroke.length) return;
        ctx.beginPath();
        ctx.moveTo(stroke[0].x, stroke[0].y);
        stroke.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
        ctx.stroke();
      });
      ctx.draw();
    }).exec();
  },

  draftKey(id) { return `${DRAFT_PREFIX}${id || "none"}`; },
  readDraft(id) {
    try { return wx.getStorageSync(this.draftKey(id)) || {}; } catch (error) { return {}; }
  },
  persistDraft(patch = {}) {
    const selected = this.data.selected;
    if (!selected) return;
    const current = this.readDraft(selected.id);
    try { wx.setStorageSync(this.draftKey(selected.id), { ...current, ...patch, savedAt: new Date().toISOString() }); } catch (error) { /* 本地空间不足时不阻断编辑 */ }
  },
  clearDraft(id) {
    try { wx.removeStorageSync(this.draftKey(id)); } catch (error) { /* 不阻断已完成提交 */ }
  },

  onNoteInput(event) {
    const note = event.detail.value;
    this.setData({ note });
    this.persistDraft({ note });
  },
  onStageFeedbackInput(event) {
    const key = event.currentTarget.dataset.key;
    if (!["observation", "evidence", "nextStep", "openQuestion"].includes(key)) return;
    const stageFeedbackForm = { ...this.data.stageFeedbackForm, [key]: event.detail.value };
    this.setData({ stageFeedbackForm });
    this.persistDraft({ stageFeedbackForm });
  },
  onMessageTitleInput(event) {
    const messageTitle = event.detail.value;
    this.setData({ messageTitle });
    this.persistDraft({ messageTitle });
  },
  onMessageBodyInput(event) {
    const messageBody = event.detail.value;
    this.setData({ messageBody });
    this.persistDraft({ messageBody });
  },

  async saveNote() {
    if (!this.data.note.trim()) return;
    await api.createRelationshipResearchNote(this.data.selected.id, { note: this.data.note.trim() });
    this.setData({ note: "" });
    this.persistDraft({ note: "" });
    await this.selectEnrollmentById(this.data.selected.id);
    wx.showToast({ title: "备注已保存", icon: "success" });
  },

  async createReport() {
    const report = await api.createRelationshipReport(this.data.selected.id);
    await this.selectEnrollmentById(this.data.selected.id);
    wx.navigateTo({ url: `/pages/relationship-report/index?id=${encodeURIComponent(report.id)}` });
  },

  openReport() {
    wx.navigateTo({ url: `/pages/relationship-report/index?id=${encodeURIComponent(this.data.selected.latestReport.id)}` });
  },

  async confirmReport() {
    await api.confirmRelationshipReport(this.data.selected.latestReport.id);
    await this.selectEnrollmentById(this.data.selected.id);
    wx.showToast({ title: "报告已确认", icon: "success" });
  },

  async sendReport() {
    try {
      await api.sendRelationshipReport(this.data.selected.latestReport.id);
      wx.showToast({ title: "已发送到用户消息", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "发送失败", icon: "none" });
    }
  },

  async prepareDelivery(deliveryType) {
    const form = this.data.stageFeedbackForm;
    const selected = this.data.selected;
    const isStage = deliveryType === "stage_feedback";
    const stateKey = isStage ? "stageFeedbackDelivery" : "participantMessageDelivery";
    const current = this.data[stateKey];
    const title = isStage ? "本阶段可以一起核对的变化" : this.data.messageTitle.trim();
    const content = isStage ? {
      observation: form.observation.trim(),
      evidence: form.evidence.trim(),
      next_step: form.nextStep.trim(),
      open_question: form.openQuestion.trim(),
    } : { body: this.data.messageBody.trim() };
    if (!selected || !title || (isStage ? !content.observation || !content.next_step : !content.body)) {
      wx.showToast({ title: isStage ? "请填写观察与下一小步" : "请填写消息标题和正文", icon: "none" });
      return null;
    }
    let workflow = current;
    const nonce = Date.now();
    if (!workflow || ["sent", "withdrawn"].includes(workflow.status)) {
      workflow = await api.createResearchDelivery({
        enrollment_id: selected.id,
        delivery_type: deliveryType,
        title,
        content,
      }, `delivery-create-${deliveryType}-${selected.id}-${nonce}`);
    } else {
      workflow = await api.saveResearchDelivery(workflow.id, {
        expected_version: workflow.version,
        title,
        content,
      }, `delivery-save-${workflow.id}-${nonce}`);
    }
    workflow = await api.runResearchDeliveryAction(
      workflow.id,
      "preview",
      workflow.version,
      `delivery-preview-${workflow.id}-${nonce}`,
    );
    this.setData({ [stateKey]: workflow });
    return workflow;
  },

  async previewStageFeedback() {
    this.setData({ sendingFeedback: true });
    try {
      await this.prepareDelivery("stage_feedback");
      wx.showToast({ title: "预览已生成", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "预览生成失败", icon: "none" });
    } finally {
      this.setData({ sendingFeedback: false });
    }
  },

  async previewParticipantMessage() {
    this.setData({ sendingMessage: true });
    try {
      await this.prepareDelivery("participant_message");
      wx.showToast({ title: "预览已生成", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "预览生成失败", icon: "none" });
    } finally {
      this.setData({ sendingMessage: false });
    }
  },

  async runDeliveryStep(event) {
    const kind = event.currentTarget.dataset.kind;
    const action = event.currentTarget.dataset.action;
    const stateKey = kind === "stage" ? "stageFeedbackDelivery" : "participantMessageDelivery";
    const workflow = this.data[stateKey];
    if (!workflow) return;
    this.setData(kind === "stage" ? { sendingFeedback: true } : { sendingMessage: true });
    try {
      const result = await api.runResearchDeliveryAction(
        workflow.id,
        action,
        workflow.version,
        `delivery-${action}-${workflow.id}-${Date.now()}`,
      );
      this.setData({ [stateKey]: result });
      if (action === "send") {
        wx.showToast({ title: "已发送到参与者消息", icon: "success" });
        if (kind === "stage") this.clearDraft(this.data.selected.id);
      } else {
        wx.showToast({ title: "已确认，可发送", icon: "success" });
      }
    } catch (error) {
      wx.showToast({ title: error.message || "操作失败，请重试", icon: "none" });
    } finally {
      this.setData({ sendingFeedback: false, sendingMessage: false });
    }
  },

  async draftNarrative() {
    const narrative = await api.createRelationshipNarrative(this.data.selected.id, {});
    this.setData({ narrative });
  },

  async confirmNarrative() {
    const narrative = await api.confirmRelationshipNarrative(this.data.narrative.id);
    this.setData({ narrative });
    wx.showToast({ title: "探索手记已确认", icon: "success" });
  },
});
