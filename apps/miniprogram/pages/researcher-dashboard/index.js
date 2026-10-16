const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, requireLogin } = require("../../utils/authGuard");
const { buildErrorDiagnostic, copyErrorDiagnostic } = require("../../utils/errorDiagnostics");

const api = createSafeHomeApi({
  defaultHeaders: { "X-SafeHome-Researcher-Workspace": "1" },
});

// 四个分区：待办、参与者、分析、项目与评估；“管理”只给总管理，在 onLoad 里另加。
const WORKSPACES = [
  { id: "pending", label: "待办", capability: "research.dashboard.read" },
  { id: "participants", label: "参与者", capability: "research.participant.read" },
  { id: "analysis", label: "分析", capability: "research.analysis.read" },
  { id: "projects", label: "项目与评估", capability: "research.dashboard.read" },
];
const PROJECT_VIEWS = ["pilots", "assessment"];
// 关系试点报名时同意了研究人员联系，所以只有他们能在档案里直接发消息、写备注。
const PILOT_CONTACT_STATUSES = ["enrolled", "active"];

const QUEUES = [
  { id: "risk_review", label: "风险信号复核" },
  { id: "supervision", label: "人工支持" },
  { id: "stage_feedback", label: "阶段性反馈" },
  { id: "feedback_review", label: "不适反馈复核" },
  { id: "notification_failed", label: "发送失败的消息" },
];

const PRIORITY_ORDER = { urgent: 0, attention: 1, routine: 2 };
const PRIORITY_LABELS = { urgent: "优先处理", attention: "需要关注", routine: "常规" };
const DRAFT_PREFIX = "researcher_workspace_draft_v1:";
const MODULE_PRIMARY_FIELDS = ["title", "worksheet_title", "scene", "card_id", "message_type", "task_type", "status", "created_at"];
const MODULE_FIELD_LABELS = {
  title: "标题",
  worksheet_title: "量表",
  scene: "场景",
  card_id: "训练卡",
  message_type: "消息类型",
  task_type: "任务类型",
  status: "状态",
  created_at: "时间",
};
const ROLE_LABELS = { researcher: "研究员", supervisor: "督导", admin: "总管理" };
const SCOPE_LABELS = { assigned_participants: "分配给我的参与者", all_participants: "全部参与者" };
const VISIBILITY_LABELS = { participant: "参与者", research_team: "研究团队", supervisor: "督导" };
const EVIDENCE_REVIEW_LABELS = {
  recorded: "已记录",
  candidate: "候选",
  draft: "草稿",
  human_reviewed: "已人工复核",
  changes_requested: "需修改",
  participant_checked: "参与者已核对",
};
const GROUP_WINDOWS = [30, 90, 180, 365];

// Server times are UTC ISO strings; show them in the phone's local time.
function parseTime(value) {
  const text = String(value || "").trim();
  if (!text) return null;
  // Python writes microseconds; some iOS engines only parse milliseconds.
  const parsed = Date.parse(text.replace(/(\.\d{3})\d+/, "$1"));
  return Number.isFinite(parsed) ? parsed : null;
}

function localTime(value) {
  const parsed = parseTime(value);
  if (parsed === null) return String(value || "").slice(0, 16).replace("T", " ");
  const date = new Date(parsed);
  const pad = (number) => String(number).padStart(2, "0");
  const year = date.getFullYear() === new Date().getFullYear() ? "" : `${date.getFullYear()}-`;
  return `${year}${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function durationText(minutes) {
  const value = Math.max(0, Math.round(Number(minutes) || 0));
  if (value < 60) return `${value} 分钟`;
  const hours = Math.floor(value / 60);
  if (hours < 24) return value % 60 ? `${hours} 小时 ${value % 60} 分` : `${hours} 小时`;
  const days = Math.floor(hours / 24);
  return hours % 24 ? `${days} 天 ${hours % 24} 小时` : `${days} 天`;
}

function dueState(dueAt, now = Date.now()) {
  const due = parseTime(dueAt);
  if (due === null) return { text: "", overdue: false };
  const minutes = Math.round((due - now) / 60000);
  return minutes < 0
    ? { text: `已超时 ${durationText(-minutes)}`, overdue: true }
    : { text: `剩余 ${durationText(minutes)}`, overdue: false };
}

function shareText(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function barWidth(value, max) {
  const ratio = (Number(value) || 0) / Math.max(Number(max) || 0, 1e-9);
  return `${Math.max(6, Math.min(100, Math.round(ratio * 100)))}%`;
}

function windowLabel(days) {
  return Number(days) === 365 ? "近一年" : `近 ${days} 天`;
}

function moduleRows(items, moduleKey = "") {
  return (items || []).map((item) => {
    if (moduleKey === "timeline") {
      return { ...item, timeline: true, timeText: localTime(item.created_at) };
    }
    if (item.schema === "safehome.participant-exploratory-analysis.v1") {
      return {
        ...item,
        exploratoryAnalysis: true,
        statusText: {
          available: "可查看",
          insufficient: "记录不足",
          withheld: "暂缓并转人工关注",
          ineligible: "当前阶段未开放",
        }[item.availability] || "暂不可用",
        affectSummary: item.affect && item.affect.summary_text ? item.affect.summary_text : "",
        affectNextCheck: item.affect && item.affect.next_check_text ? item.affect.next_check_text : "",
        affectRows: ((item.affect && item.affect.items) || []).map((row) => `${row.label} · ${row.count} 次 · 平均强度 ${row.average_intensity}`),
        networkSummary: item.interaction_network && item.interaction_network.summary ? item.interaction_network.summary.summary_text : "",
        networkNextCheck: item.interaction_network && item.interaction_network.summary ? item.interaction_network.summary.next_check_text : "",
        networkRows: ((item.interaction_network && item.interaction_network.edges) || []).map((row) => {
          let text = `${row.scene} × ${row.emotion} · ${row.support} 次`;
          if (row.share_in_scene !== undefined && row.share_in_scene !== null) {
            text += ` · 场景内 ${Math.round(row.share_in_scene * 100)}% · 整体 ${Math.round(row.share_overall * 100)}% · 提升度 ${row.lift}`;
          }
          if (row.average_intensity !== undefined && row.average_intensity !== null) text += ` · 平均强度 ${row.average_intensity}`;
          return text;
        }),
        trendSummary: item.affect && item.affect.trend && item.affect.trend.available ? item.affect.trend.summary_text : "",
        parentChildSummary: item.parent_child && item.parent_child.paired_record_count ? item.parent_child.summary_text : "",
        parentChildRows: ((item.parent_child && item.parent_child.pairs) || []).map((row) => `家长“${row.parent_emotion}” × 孩子“${row.child_emotion}” · ${row.support} 次 · 占该家长情绪 ${Math.round(row.share_of_parent_emotion * 100)}%`),
        parentChildNextCheck: item.parent_child ? item.parent_child.next_check_text || "" : "",
      };
    }
    return {
      ...item,
      displayLines: MODULE_PRIMARY_FIELDS
        .filter((key) => item[key] !== undefined && item[key] !== null && item[key] !== "")
        .slice(0, 4)
        .map((key) => {
          let value = item[key];
          if (key === "created_at") value = localTime(value);
          if (key === "status") value = STATUS_LABELS[value] || value;
          return `${MODULE_FIELD_LABELS[key]}：${String(value).slice(0, 180)}`;
        }),
    };
  });
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
    (result.value.items || []).forEach((item) => {
      const due = dueState(item.due_at);
      items.push({
        workItemId: item.work_item_id,
        queueType: queue.id,
        queueLabel: queue.label,
        title: item.title || queue.label,
        priority: item.priority || "routine",
        priorityText: PRIORITY_LABELS[item.priority] || PRIORITY_LABELS.routine,
        status: item.status || "open",
        waitMinutes: Number(item.wait_minutes || 0),
        waitText: durationText(item.wait_minutes),
        dueAt: item.due_at || "",
        dueText: due.text,
        overdue: due.overdue,
      });
    });
  });
  items.sort((a, b) => (PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]) || (b.waitMinutes - a.waitMinutes));
  return { items, failures, total };
}

const WORK_ITEM_STATUS_LABELS = {
  open: "待领取",
  claimed: "已领取",
  processing: "处理中",
  waiting: "等待补充",
  completed: "已完成",
  closed: "已关闭",
  dead_letter: "需人工恢复",
};
const WORK_ITEM_ACTION_LABELS = {
  claim: "领取",
  renew: "延长处理时间",
  return: "放回待办",
  transfer: "转交",
  start_processing: "开始处理",
  wait: "等待补充",
  add_note: "内部说明",
  send_participant_message: "发送参与者消息",
  retry_notification: "重新发送",
  recover_notification: "恢复这条消息",
  complete: "标记完成",
  close: "关闭",
  reopen: "重新打开",
};
const RESOLUTION_OPTIONS = [
  { code: "handled", label: "已完成当前处理" },
  { code: "participant_updated", label: "已向参与者反馈进度" },
  { code: "transferred", label: "已转交合适人员" },
  { code: "no_response", label: "等待期内未收到补充" },
  { code: "duplicate", label: "重复工作项已合并" },
];
const RISK_REVIEW_OPTIONS = [
  { status: "reviewed", label: "已复核，暂不需跟进" },
  { status: "follow_up_needed", label: "需要继续跟进" },
  { status: "transferred", label: "已转介现实支持" },
  { status: "closed", label: "处理完成并关闭" },
];
const MESSAGE_QUEUES = ["stage_feedback", "supervision", "feedback_review"];
const SUPERVISION_STATUS_LABELS = { pending: "待接单", acknowledged: "已接单", replied: "已回复", resolved: "已结束", closed: "已关闭" };
const SUPERVISION_ACTIONS = ["acknowledge", "reply", "resolve"];

function supervisionView(item) {
  return {
    ...item,
    statusText: SUPERVISION_STATUS_LABELS[item.status] || item.status,
    createdText: localTime(item.created_at),
    open: !["resolved", "closed"].includes(item.status),
  };
}
const ACTIVE_WORK_STATUSES = ["claimed", "processing", "waiting"];

function shortTime(value) {
  return localTime(value);
}

function assigneeLabel(assigneeId, currentUserId) {
  if (!assigneeId) return "尚未领取";
  return currentUserId && assigneeId === currentUserId ? "我" : "其他成员";
}

function buildWorkItemView(detail, queueLabel, privileged, currentUserId = "") {
  const item = (detail && detail.work_item) || {};
  const source = (detail && detail.source) || {};
  const status = item.status || "open";
  const active = ACTIVE_WORK_STATUSES.includes(status);
  const actions = ((detail && detail.actions) || []).map((action) => (
    `${shortTime(action.created_at)} · ${WORK_ITEM_ACTION_LABELS[action.action] || "其它动作"} · ${WORK_ITEM_STATUS_LABELS[action.to_status] || "待核对"}`
  ));
  const notes = ((detail && detail.notes) || []).map((note) => (
    `${shortTime(note.created_at)} · ${note.note_type === "internal" ? "内部说明" : "处理说明"} · ${note.content}`
  ));
  const due = active || status === "open" ? dueState(item.due_at) : { text: "", overdue: false };
  return {
    id: item.id,
    version: Number(item.version || 0),
    queueType: item.queue_type,
    queueLabel: queueLabel || "待办",
    status,
    statusText: WORK_ITEM_STATUS_LABELS[status] || "待核对",
    priorityText: PRIORITY_LABELS[item.priority] || PRIORITY_LABELS.routine,
    assigneeText: assigneeLabel(item.assignee_id, currentUserId),
    dueText: item.due_at ? `${shortTime(item.due_at)}${due.text ? `（${due.text}）` : ""}` : "未设置",
    overdue: due.overdue,
    sourceId: source.source_id || item.source_id,
    privileged,
    canClaim: status === "open",
    canWork: active,
    canClose: privileged && status === "completed",
    canReopen: privileged && (status === "completed" || status === "closed"),
    canMessage: active && MESSAGE_QUEUES.includes(item.queue_type),
    isNotification: item.queue_type === "notification_failed",
    canRecover: privileged && status === "dead_letter",
    isRiskReview: item.queue_type === "risk_review",
    trail: [...actions, ...notes],
    boundaryNotice: (detail && detail.boundary_notice) || "",
  };
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

const KNOWLEDGE_METHODS = ["hybrid", "bm25", "vector"];
const KNOWLEDGE_METHOD_OPTIONS = ["综合检索", "关键词检索", "向量检索"];
const AFFECT_REVIEW_REASON_LABELS = {
  text_too_short: "文本线索过短",
  out_of_domain_no_emotion_cue: "缺少情绪线索",
  conflicting_emotion_cues: "情绪线索冲突",
  low_model_confidence: "模型置信不足",
};

function normalizeKnowledgeInventory(payload) {
  const rawDocuments = payload && Array.isArray(payload.documents) ? payload.documents : [];
  const rawCandidates = payload && Array.isArray(payload.candidates) ? payload.candidates : [];
  const documents = rawDocuments.map((item) => ({
    ...item,
    displayTitle: item.title || item.item_id || "已审核内容",
    statusText: item.status === "withdrawn" ? "已撤回" : (item.review_status === "approved" ? "已审核" : "待核对"),
    audiencesText: Array.isArray(item.audiences) && item.audiences.length ? item.audiences.join("、") : "项目范围",
    sourceText: item.source_version || item.version || "已登记来源",
  }));
  const inventorySummary = (payload && payload.inventory_summary) || {};
  const activeDocumentCount = Number(
    inventorySummary.active_document_count !== undefined
      ? inventorySummary.active_document_count
      : documents.filter((item) => item.status === "active").length,
  );
  return {
    ...(payload || {}),
    documents,
    documentCount: documents.length,
    activeDocumentCount,
    withdrawnDocumentCount: Number(inventorySummary.withdrawn_document_count || 0),
    candidateCount: rawCandidates.length,
  };
}

function normalizeKnowledgeResult(payload) {
  const rawCitations = payload && Array.isArray(payload.citations) ? payload.citations : [];
  const citations = rawCitations.map((item) => ({
    ...item,
    sourceText: item.source_ref || "项目来源未标注",
    statusText: item.review_status === "approved" ? "已审核" : "待核对",
    scoreText: item.scores && item.scores.final !== undefined ? `排序参考 ${Number(item.scores.final).toFixed(3)}` : "已返回来源",
    audiencesText: Array.isArray(item.audiences) && item.audiences.length ? item.audiences.join("、") : "适用范围未标注",
    validityText: item.expires_at
      ? `有效至 ${String(item.expires_at).slice(0, 10)}`
      : (item.valid_from ? `自 ${String(item.valid_from).slice(0, 10)} 生效` : "有效期未标注"),
  }));
  return {
    ...(payload || {}),
    citations,
    retrieval_summary: payload && payload.retrieval_summary ? payload.retrieval_summary : null,
    evidenceStatusText: citations.length ? "找到可核对来源" : "证据不足",
  };
}

function normalizeBenchmarkRuns(payload) {
  const statuses = {
    engineering_threshold_passed: "工程阈值通过",
    engineering_review_required: "需要工程复核",
  };
  const runs = payload && Array.isArray(payload.items) ? payload.items : [];
  return runs.slice(0, 5).map((item) => {
    const metrics = item.metrics || {};
    const isNetwork = String(item.benchmark_type || "").includes("network");
    const analysisSummary = metrics.analysis_summary || {};
    const boundaryRange = analysisSummary.boundary_density_range || {};
    const missingnessRange = analysisSummary.missingness_density_range || {};
    const hasDensityRanges = [
      boundaryRange.minimum,
      boundaryRange.maximum,
      missingnessRange.minimum,
      missingnessRange.maximum,
    ].every((value) => value !== null && value !== undefined);
    const metricSummary = isNetwork
      ? `群体网络 ${metrics.suppressed ? "小样本已抑制" : "已生成聚合摘要"}`
      : `情感候选 ${metrics.passed ? "通过" : "待核对"}`;
    return {
      ...item,
      isNetwork,
      benchmarkTypeText: isNetwork ? "群体网络描述" : "情感模型候选",
      statusText: statuses[item.status] || "待核对",
      evidenceText: item.evidence_level === "synthetic_engineering_only" ? "合成工程数据" : "受控证据",
      algorithmText: item.algorithm_version || "未标注版本",
      metricSummary,
      networkSummaryText: isNetwork ? (analysisSummary.summary_text || metricSummary) : "",
      networkDetailText: isNetwork && hasDensityRanges
        ? `边界密度 ${boundaryRange.minimum}—${boundaryRange.maximum} · 缺失敏感性 ${missingnessRange.minimum}—${missingnessRange.maximum}`
        : "",
      networkNextCheck: isNetwork ? (analysisSummary.next_check_text || "") : "",
      rawTextText: item.raw_text_included ? "含原文（不应出现）" : "不含原文",
      createdText: localTime(item.created_at),
    };
  });
}

function withSentText(workflow) {
  return workflow ? { ...workflow, sentText: workflow.sent_at ? localTime(workflow.sent_at) : "" } : workflow;
}

function metricText(value) {
  return value === null || value === undefined ? "—" : Number(value).toFixed(2);
}

function hiddenCategoryText(emotionHidden = {}, sceneHidden = {}) {
  const parts = [];
  if (emotionHidden.hidden_category_count) parts.push(`${emotionHidden.hidden_category_count} 种情绪`);
  if (sceneHidden.hidden_category_count) parts.push(`${sceneHidden.hidden_category_count} 个场景`);
  return parts.length ? `另有 ${parts.join("、")}因记录人数少于 3 人未单独列出。` : "";
}

function labelBars(rows) {
  const max = Math.max(1, ...rows.map((item) => Number(item.participant_count) || 0));
  return rows.map((item) => ({
    key: item.label,
    label: item.label,
    width: barWidth(item.participant_count, max),
    valueText: `${item.participant_count} 人 · ${item.record_count} 条 · 平均强度 ${item.average_intensity}`,
  }));
}

function buildGroupInsightsView(payload) {
  if (!payload) return null;
  const thresholds = payload.thresholds || {};
  const view = {
    available: payload.availability === "available",
    windowText: windowLabel(payload.window_days),
    scopeText: SCOPE_LABELS[payload.scope] || "授权范围内",
    generatedText: localTime(payload.generated_at),
    reason: payload.reason || "",
    consentRule: payload.consent_rule || "",
    boundaryNotice: payload.boundary_notice || "",
    thresholdText: `保护规则：总人数少于 ${thresholds.minimum_participants} 人不展示；单项少于 ${thresholds.minimum_cell_participants} 人不单独列出；每周少于 ${thresholds.minimum_week_participants} 人不显示该周。`,
  };
  if (!view.available) return view;
  const affect = payload.affect || {};
  const network = payload.network || {};
  const cooccurrence = network.emotion_cooccurrence || {};
  const persistence = cooccurrence.persistence || {};
  const weekly = affect.weekly_trend || {};
  const parentChild = affect.parent_child || {};
  const sceneEmotion = network.scene_emotion || {};
  return {
    ...view,
    summaryText: payload.summary_text || "",
    headline: [
      { key: "participants", label: "参与者", value: payload.participant_count, unit: "人" },
      { key: "records", label: "可汇总记录", value: payload.usable_record_count, unit: "条" },
      { key: "intensity", label: "平均强度", value: affect.average_intensity, unit: "/10" },
    ],
    excludedText: payload.excluded_record_count
      ? `另有 ${payload.excluded_record_count} 条记录缺少场景、情绪或有效强度，未计入。`
      : "",
    emotionBars: labelBars(affect.emotions || []),
    sceneBars: labelBars(affect.scenes || []),
    hiddenText: hiddenCategoryText(affect.emotion_hidden, affect.scene_hidden),
    intensityBands: (affect.intensity_bands || []).map((band) => ({
      key: band.key,
      label: band.label,
      width: barWidth(band.record_share, 1),
      valueText: `${shareText(band.record_share)} · ${band.record_count} 条`,
    })),
    weeklyRows: (weekly.items || []).map((item) => ({
      key: item.week_start,
      label: `${String(item.week_start).slice(5)} 这一周`,
      width: barWidth(item.average_intensity, 10),
      valueText: `${item.participant_count} 人 · ${item.record_count} 条 · 平均强度 ${item.average_intensity}`,
    })),
    weeklyNote: weekly.suppressed_week_count
      ? `${weekly.suppressed_week_count} 周的记录人数少于 ${weekly.minimum_week_participants} 人，未单独显示。`
      : "",
    linkRows: (sceneEmotion.links || []).map((item) => ({
      key: `${item.scene}:${item.emotion}`,
      title: `${item.scene} → ${item.emotion}`,
      meta: `${item.participant_count} 人 · 该场景中占 ${shareText(item.share_in_scene)} · 提升度 ${item.lift} · 平均强度 ${item.average_intensity}`,
    })),
    networkSizeText: `${cooccurrence.node_count || 0} 种情绪 · ${cooccurrence.edge_count || 0} 条关联 · ${cooccurrence.component_count || 0} 个相连的组`,
    networkMetrics: [
      { key: "density", label: "关联密度", value: metricText(cooccurrence.density), hint: "0 表示情绪之间互不相连，1 表示两两都被同一批人一起记录过" },
      { key: "clustering", label: "成团程度", value: metricText(cooccurrence.average_clustering), hint: "越接近 1，越常见三种情绪彼此都相连" },
      { key: "centralization", label: "中心化", value: metricText(cooccurrence.degree_centralization), hint: "越接近 1，越像围绕一两种情绪展开" },
      {
        key: "persistence",
        label: "前后稳定",
        value: persistence.persistence_rate === null || persistence.persistence_rate === undefined ? "—" : shareText(persistence.persistence_rate),
        hint: "前半段和后半段都出现过的关联所占比例",
      },
    ],
    centralText: (cooccurrence.central_emotions || [])
      .map((item) => `${item.emotion}（与 ${item.linked_emotion_count} 种情绪相连）`)
      .join("、"),
    strongestRows: (cooccurrence.strongest_links || []).map((item) => ({
      key: `${item.emotion_a}:${item.emotion_b}`,
      text: `${item.emotion_a} + ${item.emotion_b} · ${item.participant_count} 人`,
    })),
    pairRows: (parentChild.pairs || []).map((item) => ({
      key: `${item.parent_emotion}:${item.child_emotion}`,
      text: `家长“${item.parent_emotion}” × 孩子“${item.child_emotion}” · ${item.participant_count} 人 · 占“${item.parent_emotion}”记录的 ${shareText(item.share_of_parent_emotion)}`,
    })),
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
    publicationCandidateSummary: null,
    assessmentLifecycleSummary: null,
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
    dossierPilot: null,
    dossierComposer: "",
    dossierMessageTitle: "",
    dossierMessageBody: "",
    dossierNote: "",
    dossierNotes: [],
    dossierBusy: "",
    projectView: "pilots",
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
    roleText: "",
    scopeText: "",
    groupInsights: null,
    groupInsightsLoading: false,
    groupInsightsError: "",
    groupWindow: 90,
    groupWindowOptions: GROUP_WINDOWS.map((days) => ({ days, label: windowLabel(days) })),
    showEngineering: false,
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
    knowledgeInventory: null,
    knowledgeDocumentCount: 0,
    knowledgeQuery: "",
    knowledgeMethod: "hybrid",
    knowledgeMethodText: KNOWLEDGE_METHOD_OPTIONS[0],
    knowledgeMethodOptions: KNOWLEDGE_METHOD_OPTIONS,
    knowledgeResult: null,
    knowledgeLoading: false,
    knowledgeError: "",
    networkPolicy: null,
    offlineBenchmarkRuns: [],
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
    workItem: null,
    workItemLoading: false,
    workItemBusy: false,
    workItemError: "",
    workItemNote: "",
    workItemMessageTitle: "",
    workItemMessageBody: "",
    workItemResolutionIndex: 0,
    resolutionLabels: RESOLUTION_OPTIONS.map((option) => option.label),
    riskReviewIndex: 0,
    riskReviewLabels: RISK_REVIEW_OPTIONS.map((option) => option.label),
    riskReviewAction: "",
    supervisionCase: null,
    supervisionReply: "",
    supervisionBusy: "",
  },

  async onLoad() {
    if (!requireLogin({ redirectUrl: "/pages/researcher-dashboard/index" })) return;
    const user = getAuthUser();
    const [showcase, capabilityScope] = await Promise.all([
      api.getShowcaseAccess().catch(() => ({ enabled: false })),
      api.getResearchCapabilities().catch(() => null),
    ]);
    const workspaces = visibleWorkspaces(capabilityScope);
    // “管理”只给真正的总管理和督导（督导只看删除申请）；展示模式临时开放的研究权限不算。
    const isOwner = Boolean(user && user.role === "admin");
    if (isOwner || (user && user.role === "supervisor")) workspaces.push({ id: "manage", label: "管理" });
    const formalRole = capabilityScope && capabilityScope.formal_role;
    this.setData({
      developmentFullAccess: Boolean(showcase.researcher_platform_full_access),
      isOwner,
      capabilityScope,
      roleText: formalRole ? (ROLE_LABELS[formalRole] || formalRole) : "",
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
    if (this.data.activeWorkspace === "projects") {
      if (this.data.projectView === "assessment") return this.loadAssessmentCases();
      return Promise.all([this.loadWorkbench(), this.loadDashboard()]);
    }
    if (this.data.activeWorkspace === "analysis") return Promise.all([this.loadGroupInsights(), this.loadAnalysisJobs()]);
    return this.loadWorkbench();
  },

  async switchWorkspace(event) {
    const id = event.currentTarget.dataset.id;
    if (!this.data.workspaces.some((item) => item.id === id)) return;
    this.setData({ activeWorkspace: id });
    if (id === "participants" && !this.data.participantItems.length) await this.loadParticipants(true);
    if (id === "projects") await this.loadProjectView(this.data.projectView);
    if (id === "analysis" && !this.data.groupInsights) this.loadGroupInsights();
    if (id === "analysis" && !this.data.analysisJobs.length) await this.loadAnalysisJobs();
  },

  // “项目与评估”里分关系试点和评估证据两块，各自第一次打开时才读取。
  async switchProjectView(event) {
    const view = event.currentTarget.dataset.view;
    if (!PROJECT_VIEWS.includes(view) || view === this.data.projectView) return;
    this.setData({ projectView: view });
    await this.loadProjectView(view);
  },

  async loadProjectView(view) {
    if (view === "pilots" && !this.data.items.length) await this.loadDashboard();
    if (view === "assessment" && !this.data.assessmentCases.length) await this.loadAssessmentCases();
  },

  async loadGroupInsights(windowDays = this.data.groupWindow) {
    if (this.data.offline) {
      this.setData({ groupInsightsError: "当前离线，联网后再查看群体分析。" });
      return;
    }
    this.setData({ groupInsightsLoading: true, groupInsightsError: "", groupWindow: windowDays });
    try {
      const payload = await api.getResearchGroupInsights(windowDays);
      this.setData({ groupInsights: buildGroupInsightsView(payload) });
    } catch (error) {
      this.setData({ groupInsightsError: error.message || "群体分析暂时无法读取。" });
    } finally {
      this.setData({ groupInsightsLoading: false });
    }
  },

  selectGroupWindow(event) {
    const days = Number(event.currentTarget.dataset.days);
    if (!GROUP_WINDOWS.includes(days) || this.data.groupInsightsLoading) return;
    this.loadGroupInsights(days);
  },

  refreshGroupInsights() {
    return this.loadGroupInsights();
  },

  toggleEngineering() {
    this.setData({ showEngineering: !this.data.showEngineering });
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
        reviewStatusText: EVIDENCE_REVIEW_LABELS[item.review_status] || "待核对",
        observedText: item.observed_at ? localTime(item.observed_at) : "",
        visibilityText: (item.visibility_scope || []).map((scope) => VISIBILITY_LABELS[scope] || scope).join("、"),
        supportingText: (item.supporting_evidence || []).map((entry) => entry.ref || String(entry)).join("；"),
        counterText: (item.counter_evidence || []).join("；"),
        alternativesText: (item.alternative_explanations || []).join("；"),
      }));
      this.setData({
        assessmentWorkbench: {
          ...result,
          evidence_summary: result.evidence_summary || null,
          case: {
            ...result.case,
            sharedScopeText: (result.case.shared_scope || []).map((scope) => VISIBILITY_LABELS[scope] || scope).join("、"),
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
      const optional = (promise) => promise.catch(() => null);
      const [result, catalog, modelVersions, shadowRuns, shadowQueue, affectMonitoring, affectReleaseGate, knowledgeInventoryResult, networkPolicyResult, benchmarkRunsResult] = await Promise.all([
        api.getResearchAnalysisJobs({ limit: 30 }),
        api.getResearchAnalysisCatalog(),
        api.listOfflineModelVersions(),
        api.listOfflineModelShadowRuns(),
        api.listOfflineModelReviewQueue(),
        api.getOfflineModelMonitoring(),
        api.getOfflineModelReleaseGate(),
        optional(api.getAiKnowledgeInventory()),
        optional(api.getGroupNetworkAnalysisPolicy()),
        optional(api.listOfflineBenchmarkRuns()),
      ]);
      const knowledgeInventory = knowledgeInventoryResult ? normalizeKnowledgeInventory(knowledgeInventoryResult) : null;
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
          createdText: localTime(item.created_at),
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
          unknownRateText: `${Math.round(Number(item.unknown_rate || 0) * 100)}%`,
          shadowStatusText: item.status === "completed_shadow_only" ? "影子运行完成" : "待核对",
          shadowSummaryText: item.summary_text || `合成样本 ${item.sample_count || 0} 条，未知 ${item.unknown_count || 0} 条。`,
          shadowNextCheck: item.next_check_text || "先复核未知案例，再比较版本。",
          reviewReasonText: Object.entries(item.review_reason_counts || {})
            .map(([reason, count]) => `${AFFECT_REVIEW_REASON_LABELS[reason] || "其它待核对原因"} ${count}`)
            .join(" · "),
          createdText: localTime(item.created_at),
        })),
        affectShadowReviewCount: (shadowQueue.items || []).length,
        affectMonitoring,
        affectReleaseGate,
        knowledgeInventory,
        knowledgeDocumentCount: knowledgeInventory ? knowledgeInventory.activeDocumentCount : 0,
        knowledgeError: knowledgeInventoryResult ? "" : "已审核知识库摘要暂时无法读取。",
        networkPolicy: networkPolicyResult || null,
        offlineBenchmarkRuns: normalizeBenchmarkRuns(benchmarkRunsResult).filter((item) => item.isNetwork),
      });
    } catch (error) {
      this.setData({ analysisError: error.message || "在线分析任务暂时无法读取。" });
    } finally {
      this.setData({ analysisLoading: false });
    }
  },

  onKnowledgeQueryInput(event) {
    this.setData({ knowledgeQuery: event.detail.value || "", knowledgeError: "" });
  },

  onKnowledgeMethodChange(event) {
    const index = Number(event.detail.value || 0);
    this.setData({
      knowledgeMethod: KNOWLEDGE_METHODS[index] || KNOWLEDGE_METHODS[0],
      knowledgeMethodText: KNOWLEDGE_METHOD_OPTIONS[index] || KNOWLEDGE_METHOD_OPTIONS[0],
    });
  },

  async searchKnowledge() {
    const query = String(this.data.knowledgeQuery || "").trim();
    if (!query) {
      this.setData({ knowledgeError: "请先写下要查找的已审核内容。", knowledgeResult: null });
      return;
    }
    this.setData({ knowledgeLoading: true, knowledgeError: "" });
    try {
      const result = await api.retrieveAiKnowledge(query, this.data.knowledgeMethod);
      this.setData({ knowledgeResult: normalizeKnowledgeResult(result) });
    } catch (error) {
      this.setData({ knowledgeResult: null, knowledgeError: error.message || "知识库检索暂时无法完成。" });
    } finally {
      this.setData({ knowledgeLoading: false });
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
      api.listPublicationCandidates(),
      api.getTherapeuticAssessmentLifecycleMetrics(),
    ]);
    const queueResults = workbenchResults.slice(0, QUEUES.length);
    const runtimeResult = workbenchResults[QUEUES.length];
    const dutyResult = workbenchResults[QUEUES.length + 1];
    const publicationResult = workbenchResults[QUEUES.length + 2];
    const lifecycleResult = workbenchResults[QUEUES.length + 3];
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
      scopeText: SCOPE_LABELS[operations.scope] || "授权范围内",
      workspaces: this.data.workspaces.map((item) => ({ ...item, badge: item.id === "pending" ? preview.total : 0 })),
      pendingItems: preview.items,
      pendingTotal: preview.total,
      pendingVisibleItems: preview.items.slice(0, pageSize),
      pendingPage: 1,
      pendingHasMore: preview.items.length > pageSize,
      urgentCount: preview.items.filter((item) => item.priority === "urgent").length,
      assessmentQueueRuntime: runtimeResult.status === "fulfilled" ? runtimeResult.value : null,
      assessmentDutyShifts: dutyResult.status === "fulfilled" ? (dutyResult.value.items || []) : [],
      publicationCandidateSummary: publicationResult.status === "fulfilled"
        ? {
            blocked: (publicationResult.value.items || []).filter((item) => item.status === "blocked").length,
            approved: (publicationResult.value.items || []).filter((item) => item.status === "approved").length,
            published: (publicationResult.value.items || []).filter((item) => item.status === "published").length,
          }
        : null,
      assessmentLifecycleSummary: lifecycleResult.status === "fulfilled"
        ? lifecycleResult.value
        : null,
      partialFailures,
      lastSyncText: syncTimeLabel(),
    });
  },

  canManageSensitiveWorkItems() {
    const user = getAuthUser();
    return Boolean(this.data.developmentFullAccess) || Boolean(user && ["supervisor", "admin"].includes(user.role));
  },

  currentUserId() {
    const user = getAuthUser();
    return (user && user.id) || "";
  },

  async openWorkItem(event) {
    const { id, label } = event.currentTarget.dataset;
    if (!id || this.data.workItemBusy) return;
    this.setData({
      workItemLoading: true,
      workItemError: "",
      workItemNote: "",
      workItemMessageTitle: "",
      workItemMessageBody: "",
      riskReviewAction: "",
    });
    this.setData({ supervisionCase: null, supervisionReply: "" });
    try {
      const detail = await api.getResearchWorkItem(id);
      const workItem = buildWorkItemView(detail, label, this.canManageSensitiveWorkItems(), this.currentUserId());
      this.setData({ workItem });
      if (workItem.queueType === "supervision" && workItem.privileged && workItem.sourceId) this.loadSupervisionCase(workItem.sourceId);
    } catch (error) {
      this.setData({ workItem: null, workItemError: error.message || "待办详情暂时无法读取。" });
    } finally {
      this.setData({ workItemLoading: false });
    }
  },

  closeWorkItem() {
    this.setData({ workItem: null, workItemError: "", workItemNote: "", supervisionCase: null, supervisionReply: "" });
  },

  // 人工支持待办里直接处理请求本身：看原文、接单、回复（参与者在人工支持页和消息里看到）、结束。
  async loadSupervisionCase(requestId) {
    try {
      const item = await api.getSupervisionForReviewer(requestId);
      if (!this.data.workItem || this.data.workItem.sourceId !== requestId) return;
      this.setData({ supervisionCase: supervisionView(item), supervisionReply: item.supervisor_reply || "" });
    } catch (error) {
      this.setData({ supervisionCase: null });
    }
  },

  onSupervisionReplyInput(event) {
    this.setData({ supervisionReply: event.detail.value || "" });
  },

  async runSupervisionAction(event) {
    const action = event.currentTarget.dataset.action;
    const item = this.data.supervisionCase;
    if (!item || !SUPERVISION_ACTIONS.includes(action) || this.data.supervisionBusy) return;
    const reply = this.data.supervisionReply.trim();
    if (action === "reply" && !reply) {
      wx.showToast({ title: "请先写回复", icon: "none" });
      return;
    }
    const data = action === "reply" ? { supervisor_reply: reply } : action === "resolve" ? { resolution_code: "support_completed" } : {};
    this.setData({ supervisionBusy: action });
    try {
      const updated = await api.actOnSupervision(item.id, action, data);
      this.setData({ supervisionCase: supervisionView({ ...item, ...updated }) });
      wx.showToast({ title: { acknowledge: "已接单", reply: "回复已发出", resolve: "已结束" }[action], icon: "success" });
      this.loadWorkbench();
    } catch (error) {
      wx.showToast({ title: error.message || "没有成功，请稍后再试", icon: "none" });
    } finally {
      this.setData({ supervisionBusy: "" });
    }
  },

  onWorkItemInput(event) {
    this.setData({ [event.currentTarget.dataset.key]: event.detail.value || "", workItemError: "" });
  },

  onWorkItemPicker(event) {
    this.setData({ [event.currentTarget.dataset.key]: Number(event.detail.value || 0) });
  },

  async runWorkItemAction(event) {
    const workItem = this.data.workItem;
    const action = event.currentTarget.dataset.action;
    if (!workItem || !action || this.data.workItemBusy) return;
    const note = String(this.data.workItemNote || "").trim();
    const payload = {
      action,
      expected_version: workItem.version,
      idempotency_key: `work-item:${workItem.id}:${action}:${Date.now()}`,
    };
    if (["add_note", "reopen", "recover_notification"].includes(action) && !note) {
      this.setData({ workItemError: "请先在内部处理说明里写下原因。" });
      return;
    }
    if (note && ["add_note", "complete", "close", "reopen", "recover_notification"].includes(action)) payload.note = note;
    if (action === "complete" || action === "close") {
      payload.resolution_code = (RESOLUTION_OPTIONS[this.data.workItemResolutionIndex] || RESOLUTION_OPTIONS[0]).code;
    }
    if (action === "send_participant_message") {
      const title = String(this.data.workItemMessageTitle || "").trim();
      const body = String(this.data.workItemMessageBody || "").trim();
      if (!title || !body) {
        this.setData({ workItemError: "请填写消息标题和正文。" });
        return;
      }
      payload.title = title;
      payload.body = body;
    }
    this.setData({ workItemBusy: true, workItemError: "" });
    try {
      await api.actOnResearchWorkItem(workItem.id, payload);
      const detail = await api.getResearchWorkItem(workItem.id);
      const patch = { workItem: buildWorkItemView(detail, workItem.queueLabel, this.canManageSensitiveWorkItems(), this.currentUserId()), workItemNote: "" };
      if (action === "send_participant_message") Object.assign(patch, { workItemMessageTitle: "", workItemMessageBody: "" });
      this.setData(patch);
      wx.showToast({ title: "已更新", icon: "success" });
      this.loadWorkbench();
    } catch (error) {
      this.setData({ workItemError: error.message || "待办更新失败，请刷新后重试。" });
    } finally {
      this.setData({ workItemBusy: false });
    }
  },

  async submitRiskReview() {
    const workItem = this.data.workItem;
    if (!workItem || !workItem.isRiskReview || this.data.workItemBusy) return;
    const option = RISK_REVIEW_OPTIONS[this.data.riskReviewIndex] || RISK_REVIEW_OPTIONS[0];
    const note = String(this.data.workItemNote || "").trim();
    const actionTaken = String(this.data.riskReviewAction || "").trim();
    if (!note) {
      this.setData({ workItemError: "请先写下复核说明，不要复制参与者原文。" });
      return;
    }
    this.setData({ workItemBusy: true, workItemError: "" });
    try {
      await api.updateRiskReview(workItem.sourceId, {
        review_status: option.status,
        review_note: note,
        action_taken: actionTaken || undefined,
        closed_reason: option.status === "closed" ? (actionTaken || note) : undefined,
      });
      wx.showToast({ title: "复核已保存", icon: "success" });
      this.setData({ workItem: null, workItemNote: "", riskReviewAction: "" });
      this.loadWorkbench();
    } catch (error) {
      this.setData({ workItemError: error.message || "复核结论暂时无法保存。" });
    } finally {
      this.setData({ workItemBusy: false });
    }
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

  // 档案以时间线为中心：打开先看时间线，点一条跳到对应标签；试点参与者可在这里直接发消息、写备注。
  async selectParticipantDossier(event) {
    const userId = event.currentTarget.dataset.id;
    this.setData({ participantLoading: true, participantError: "", participantDossier: null, participantModule: null, ...this.emptyDossierTools() });
    try {
      const dossier = await api.getResearchParticipant(userId);
      const modules = dossier.modules || [];
      const enrollment = dossier.enrollment;
      this.setData({
        participantLoading: false,
        participantDossier: {
          ...dossier,
          modules: [...modules.filter((item) => item.key === "timeline"), ...modules.filter((item) => item.key !== "timeline")],
        },
        dossierPilot: enrollment && PILOT_CONTACT_STATUSES.includes(enrollment.status) ? enrollment : null,
      });
      if (modules.some((item) => item.key === "timeline")) {
        await this.loadParticipantModule({ currentTarget: { dataset: { key: "timeline", page: 1 } } });
      }
    } catch (error) {
      this.setData({ participantLoading: false, participantError: error.message || "参与者档案暂时无法读取。", participantDiagnostic: buildErrorDiagnostic(error) });
    }
  },

  closeParticipantDossier() {
    this.setData({ participantDossier: null, participantModule: null, ...this.emptyDossierTools() });
  },

  emptyDossierTools() {
    return { dossierPilot: null, dossierComposer: "", dossierMessageTitle: "", dossierMessageBody: "", dossierNote: "", dossierNotes: [], dossierBusy: "" };
  },

  toggleDossierComposer(event) {
    const composer = event.currentTarget.dataset.composer;
    const next = this.data.dossierComposer === composer ? "" : composer;
    this.setData({ dossierComposer: next });
    if (next === "note") this.loadDossierNotes();
  },

  onDossierInput(event) {
    const key = event.currentTarget.dataset.key;
    if (!["dossierMessageTitle", "dossierMessageBody", "dossierNote"].includes(key)) return;
    this.setData({ [key]: event.detail.value || "" });
  },

  async sendDossierMessage() {
    const pilot = this.data.dossierPilot;
    const title = this.data.dossierMessageTitle.trim();
    const body = this.data.dossierMessageBody.trim();
    if (!pilot || this.data.dossierBusy) return;
    if (!title || !body) {
      wx.showToast({ title: "请填写标题和正文", icon: "none" });
      return;
    }
    const confirmed = await new Promise((resolve) => {
      wx.showModal({
        title: "发送消息",
        content: "参与者会在“我的 → 消息”里看到，发出后不能撤回。确定发送吗？",
        confirmText: "发送",
        success: (result) => resolve(Boolean(result.confirm)),
        fail: () => resolve(false),
      });
    });
    if (!confirmed) return;
    this.setData({ dossierBusy: "message" });
    try {
      await api.sendResearcherMessage({
        enrollment_id: pilot.id,
        title,
        body,
        idempotency_key: `dossier-message-${pilot.id}-${Date.now()}`,
      });
      this.setData({ dossierMessageTitle: "", dossierMessageBody: "", dossierComposer: "" });
      wx.showToast({ title: "已发送", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "没有发出去，请稍后再试", icon: "none" });
    } finally {
      this.setData({ dossierBusy: "" });
    }
  },

  async loadDossierNotes() {
    const pilot = this.data.dossierPilot;
    if (!pilot) return;
    try {
      const detail = await api.getRelationshipEnrollment(pilot.id);
      if (!this.data.dossierPilot || this.data.dossierPilot.id !== pilot.id) return;
      this.setData({
        dossierNotes: (detail.research_notes || [])
          .map((item) => ({ id: item.id, note: item.note, timeText: localTime(item.created_at) }))
          .reverse(),
      });
    } catch (error) {
      wx.showToast({ title: error.message || "备注暂时读不出来", icon: "none" });
    }
  },

  async saveDossierNote() {
    const pilot = this.data.dossierPilot;
    const note = this.data.dossierNote.trim();
    if (!pilot || !note || this.data.dossierBusy) return;
    this.setData({ dossierBusy: "note" });
    try {
      await api.createRelationshipResearchNote(pilot.id, { note });
      this.setData({ dossierNote: "" });
      await this.loadDossierNotes();
      wx.showToast({ title: "备注已保存", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "备注没有保存成功", icon: "none" });
    } finally {
      this.setData({ dossierBusy: "" });
    }
  },

  async loadParticipantModule(event) {
    if (!this.data.participantDossier) return;
    const moduleKey = event.currentTarget.dataset.key;
    const requestedPage = Number(event.currentTarget.dataset.page || 1);
    this.setData({ participantModuleLoading: true, participantError: "" });
    try {
      const payload = await api.getResearchParticipantModule(this.data.participantDossier.participant.user_id, moduleKey, { page: requestedPage, page_size: 10 });
      const items = moduleRows(payload.items, moduleKey);
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
    this.setData({ [stateKey]: withSentText(workflow) });
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
      this.setData({ [stateKey]: withSentText(result) });
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
