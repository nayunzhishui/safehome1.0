const { createSafeHomeApi } = require("../../services/api");
const { createResilientForm } = require("../../utils/resilientForm");
const { reportStatusLabel } = require("../../utils/relationshipStatus.generated");

const api = createSafeHomeApi();
const COUNT_KEYS = ["active_social_count", "authentic_expression_count"];
const SCALE_KEYS = ["approach_willingness", "worry_intensity"];
const LABELS = {
  active_social_count: "主动社交次数",
  authentic_expression_count: "真实表达次数",
  approach_willingness: "关系靠近意愿",
  worry_intensity: "担忧强度",
  BI: "关系行动意愿",
  RAP: "近月关系行动",
  PBC: "关系行动可控感",
  SN: "重要他人支持感",
  BENEFIT: "主动关系获益信念",
  THREAT: "综合威胁线索",
};
const TIMELINE_FILTERS = [
  { key: "all", label: "全部" },
  { key: "assessment", label: "测评" },
  { key: "project_task", label: "任务" },
  { key: "event", label: "记录" },
  { key: "report", label: "报告" },
  { key: "researcher_feedback", label: "阶段性反馈" },
];
const SECTION_TABS = [
  { key: "curve", label: "变化曲线" },
  { key: "timeline", label: "时间线" },
  { key: "feedback", label: "阶段反馈" },
  { key: "records", label: "补充记录" },
];

function formatDate(value) {
  if (!value) return "时间待记录";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

// 时间线和曲线日期用“10月9日”（Figma 667:6212）。
function shortDate(value) {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) return "时间待记录";
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

// 时间线小标题里的类型用短词：记录 / 任务 / 报告……
const TIMELINE_KINDS = {
  assessment: "测评",
  project_task: "任务",
  weekly_supplement: "记录",
  key_event: "记录",
  report: "报告",
  researcher_feedback: "反馈",
};

// 后端时间线里任务和报告的摘要是状态码（pending_review、sent…），这里换成参与者能读懂的话；
// 两类任务的名字与试点页一致（关系隐喻绘画、情境句子补全）。
const TASK_REVIEW_TEXT = {
  pending_review: "已提交，等待人工复核",
  priority_review: "已提交，等待人工复核",
  reviewed: "研究者已查看",
};
const TASK_TITLES = { 关系绘画: "关系隐喻绘画", 句子补全: "情境句子补全" };

function timelineSummary(item) {
  if (item.type === "project_task") return TASK_REVIEW_TEXT[item.summary] || item.summary;
  if (item.type === "report" && /^[a-z_]+$/.test(String(item.summary || ""))) {
    const label = reportStatusLabel(item.summary);
    return /^已/.test(label) ? `研究者${label}` : label;
  }
  return item.summary;
}

function timelineView(item) {
  return {
    ...item,
    title: item.type === "project_task" ? TASK_TITLES[item.title] || item.title : item.title,
    summary: timelineSummary(item),
    typeLabel: timelineTypeLabel(item.type),
    dateText: formatDate(item.created_at),
    kicker: `${shortDate(item.created_at)} · ${TIMELINE_KINDS[item.type] || "记录"}`,
  };
}

// 曲线下方最多放四个日期，与折线上等分的位置对应。
function chartDateLabels(points) {
  if (points.length <= 4) return points.map((point) => point.shortDate);
  return [0, 1, 2, 3].map((step) => points[Math.round((step * (points.length - 1)) / 3)].shortDate);
}

const CN_COUNTS = ["零", "一", "两", "三", "四", "五", "六", "七", "八", "九", "十"];

// 只描述范围，不判断变好变差（设计稿：“变化只作为讨论线索”）。
function trendSummary(groupKey, label, points) {
  const values = points.map((point) => Number(point.value)).filter((value) => Number.isFinite(value));
  if (values.length < 2) return "";
  const round = (value) => Number(value.toFixed(1));
  const low = round(Math.min(...values));
  const high = round(Math.max(...values));
  const times = values.length <= 10 ? `${CN_COUNTS[values.length]}次` : `${values.length} 次`;
  const unit = groupKey === "count" ? " 次" : "";
  const range = low === high ? `都是 ${low}${unit}` : `在 ${low}—${high}${unit || " "}之间`;
  return `最近${times}记录里，${label}${range}。变化只作为讨论线索。`;
}

function buildCurveGroups(curves = {}) {
  const keys = Object.keys(curves).filter((key) => Array.isArray(curves[key]) && curves[key].length);
  const groups = [
    { key: "count", label: "次数指标", keys: keys.filter((key) => COUNT_KEYS.includes(key)) },
    { key: "scale", label: "1–5量尺", keys: keys.filter((key) => SCALE_KEYS.includes(key)) },
    { key: "dimension", label: "画像维度", keys: keys.filter((key) => !COUNT_KEYS.includes(key) && !SCALE_KEYS.includes(key)) },
  ].filter((group) => group.keys.length);
  return groups.map((group) => ({
    ...group,
    metrics: group.keys.map((key) => ({ key, label: LABELS[key] || key })),
  }));
}

function timelineTypeLabel(type) {
  const labels = {
    assessment: "测评",
    project_task: "线上任务",
    weekly_supplement: "每周记录",
    key_event: "关键事件",
    report: "报告",
    researcher_feedback: "阶段性反馈",
  };
  return labels[type] || "记录";
}

function timelineMatches(item, filter) {
  if (filter === "all") return true;
  if (filter === "event") return ["weekly_supplement", "key_event"].includes(item.type);
  return item.type === filter;
}

function selfNarrativeRows(rows = []) {
  return rows.map((row, index) => {
    const content = row.content || {};
    const parts = Object.values(content).map((value) => String(value || "").trim()).filter(Boolean);
    return {
      id: `${row.created_at || "row"}-${index}`,
      date: formatDate(row.created_at),
      typeLabel: row.entry_type === "key_event" ? "关键事件原话" : "每周记录原话",
      text: parts.join("；") || "本次没有填写开放文字。",
    };
  });
}

function createIdempotencyKey(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

Page({
  data: {
    enrollmentId: "",
    canRecord: false,
    loading: true,
    savingWeekly: false,
    savingEvent: false,
    errorMessage: "",
    growth: null,
    curves: {},
    curveGroups: [],
    selectedGroup: "",
    selectedMetrics: [],
    selectedMetric: "",
    selectedMetricLabel: "",
    selectedPoints: [],
    chartDates: [],
    trendText: "",
    sectionTabs: SECTION_TABS,
    activeSection: "curve",
    timelineFilters: TIMELINE_FILTERS,
    timelineFilter: "all",
    filteredTimeline: [],
    recentTimeline: [],
    selfNarratives: [],
    showSelfNarratives: false,
    researcherConfirmations: [],
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSaving: false,
    showWeeklyForm: false,
    showEventForm: false,
    weeklySubmissionKey: "",
    eventSubmissionKey: "",
    form: {
      active_social_count: 0,
      authentic_expression_count: 0,
      setback_coping: "",
      approach_willingness: 3,
      worry_intensity: 3,
      achievement: "",
      setback: "",
      event_summary: "",
    },
  },

  goTherapeuticAssessment() {
    wx.navigateTo({ url: "/pages/therapeutic-assessment/index" });
  },

  onLoad(options) {
    const isDetail = options.detail === "1";
    if (!isDetail) {
      this.redirectingToUnified = true;
      const enrollmentId = decodeURIComponent(options.enrollment_id || "");
      const suffix = enrollmentId ? `&enrollment_id=${encodeURIComponent(enrollmentId)}` : "";
      wx.redirectTo({ url: `/pages/growth-dashboard/index?section=relationship${suffix}` });
      return;
    }
    const enrollmentId = decodeURIComponent(options.enrollment_id || "");
    this.draftController = createResilientForm({
      storageKey: `safehome:resilientDraft:relationship-growth:${enrollmentId || "latest"}`,
      fields: ["form", "weeklySubmissionKey", "eventSubmissionKey"],
      submissionPrefix: "relationship-growth",
      hasContent: (values) => {
        const form = values.form || {};
        return Boolean(
          String(form.setback_coping || "").trim() || String(form.achievement || "").trim()
          || String(form.setback || "").trim() || String(form.event_summary || "").trim()
          || Number(form.active_social_count || 0) || Number(form.authentic_expression_count || 0)
          || Number(form.approach_willingness || 3) !== 3 || Number(form.worry_intensity || 3) !== 3
        );
      },
    });
    const restored = this.draftController.restore();
    this.setData({
      enrollmentId,
      ...(restored ? restored.values : {}),
      saveStatus: restored ? restored.saveStatus : "尚未填写",
      draftRestored: Boolean(restored),
    });
  },

  onHide() { if (this.draftController && !this.data.savingWeekly && !this.data.savingEvent) this.setData(this.draftController.flush(this.data)); },
  onUnload() { if (this.draftController && !this.data.savingWeekly && !this.data.savingEvent) this.draftController.flush(this.data); },

  onShow() {
    if (this.redirectingToUnified) return;
    this.loadGrowth();
  },

  async loadGrowth() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const growth = await api.getRelationshipGrowth();
      const enrollmentId = this.data.enrollmentId || growth.latest_enrollment_id || "";
      const curveGroups = buildCurveGroups(growth.curves);
      const selectedGroup = curveGroups[0]?.key || "";
      const selectedMetric = curveGroups[0]?.metrics[0]?.key || "";
      const timeline = (growth.timeline || []).map(timelineView);
      this.setData({
        loading: false,
        enrollmentId,
        canRecord: !!(enrollmentId && growth.can_record),
        growth,
        curves: growth.curves || {},
        curveGroups,
        selectedGroup,
        selectedMetric,
        filteredTimeline: timeline,
        recentTimeline: timeline.slice(0, 3),
        selfNarratives: selfNarrativeRows(growth.growth_report?.self_narratives),
        researcherConfirmations: (growth.growth_report?.researcher_confirmations || []).map((item) => ({ ...item, dateText: formatDate(item.created_at) })),
      }, () => this.selectCurve(selectedGroup, selectedMetric));
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "成长记录暂时无法读取。" });
    }
  },

  selectCurve(groupKey, metricKey) {
    const group = this.data.curveGroups.find((item) => item.key === groupKey);
    const metric = group?.metrics.find((item) => item.key === metricKey) || group?.metrics[0];
    if (!group || !metric) {
      this.setData({ selectedGroup: "", selectedMetrics: [], selectedMetric: "", selectedPoints: [], trendText: "" });
      return;
    }
    const points = (this.data.curves[metric.key] || []).map((point, index) => ({
      ...point,
      order: index + 1,
      dateText: formatDate(point.created_at),
      shortDate: shortDate(point.created_at),
    }));
    const trendText = trendSummary(group.key, metric.label, points);
    this.setData({
      chartDates: chartDateLabels(points),
      selectedGroup: group.key,
      selectedMetrics: group.metrics,
      selectedMetric: metric.key,
      selectedMetricLabel: metric.label,
      selectedPoints: points,
      trendText,
    }, () => {
      if (points.length >= 2) this.drawChart(group.key, points);
    });
  },

  selectCurveGroup(event) {
    const key = event.currentTarget.dataset.key;
    const group = this.data.curveGroups.find((item) => item.key === key);
    this.selectCurve(key, group?.metrics[0]?.key);
  },

  selectMetric(event) {
    this.selectCurve(this.data.selectedGroup, event.currentTarget.dataset.key);
  },

  selectSection(event) {
    const activeSection = event.currentTarget.dataset.section;
    this.setData({ activeSection }, () => {
      if (activeSection === "curve" && this.data.selectedPoints.length >= 2) {
        this.drawChart(this.data.selectedGroup, this.data.selectedPoints);
      }
    });
  },

  showAllTimeline() {
    this.setData({ activeSection: "timeline" });
  },

  showFeedbackSection() {
    this.setData({ activeSection: "feedback" });
  },

  openRecordSection() {
    this.setData({ activeSection: "records", showWeeklyForm: this.data.canRecord });
  },

  toggleRecordPanel(event) {
    const panel = event.currentTarget.dataset.panel;
    if (panel === "weekly") {
      this.setData({ showWeeklyForm: !this.data.showWeeklyForm });
      return;
    }
    if (panel === "event") this.setData({ showEventForm: !this.data.showEventForm });
  },

  // 旧版 canvas 按 CSS 像素绘制：先量画布尺寸，再按设计稿样式画（Figma 667:6264）。
  drawChart(groupKey, points) {
    wx.createSelectorQuery().in(this).select(".growth-chart__canvas").boundingClientRect((rect) => {
      this.paintChart(groupKey, points, rect && rect.width ? rect.width : 310, rect && rect.height ? rect.height : 150);
    }).exec();
  },

  paintChart(groupKey, points, width, height) {
    const ctx = wx.createCanvasContext("growthChart", this);
    ctx.clearRect(0, 0, width, height);
    if (!points.length) {
      ctx.draw();
      return;
    }
    const values = points.map((point) => Number(point.value));
    let min = Math.min(...values);
    let max = Math.max(...values);
    if (groupKey === "count") {
      min = 0;
      max = Math.max(1, Math.ceil(max + 1));
    } else if (groupKey === "scale") {
      min = 1;
      max = 5;
    } else if (min === max) {
      min -= 1;
      max += 1;
    } else {
      const padding = (max - min) * 0.15;
      min -= padding;
      max += padding;
    }
    const top = 8;
    const bottom = height - 22;
    const inset = 12;
    ctx.setStrokeStyle("#e7e1d6");
    ctx.setLineWidth(1);
    [top, (top + bottom) / 2, bottom].forEach((y) => {
      ctx.beginPath();
      ctx.moveTo(0, y + 0.5);
      ctx.lineTo(width, y + 0.5);
      ctx.stroke();
    });
    const span = Math.max(1, points.length - 1);
    const coordinates = values.map((value, index) => ({
      x: points.length === 1 ? width / 2 : inset + (index / span) * (width - inset * 2),
      y: bottom - ((value - min) / (max - min || 1)) * (bottom - top),
    }));
    ctx.setStrokeStyle("#23666e");
    ctx.setLineWidth(2);
    ctx.setLineJoin("round");
    if (coordinates.length >= 2) {
      ctx.beginPath();
      ctx.moveTo(coordinates[0].x, coordinates[0].y);
      coordinates.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
      ctx.stroke();
    }
    coordinates.forEach((point) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
      ctx.setFillStyle("#fffdf9");
      ctx.fill();
      ctx.stroke();
    });
    ctx.draw();
  },

  selectTimelineFilter(event) {
    const timelineFilter = event.currentTarget.dataset.key;
    const filteredTimeline = (this.data.growth.timeline || [])
      .filter((item) => timelineMatches(item, timelineFilter))
      .map(timelineView);
    this.setData({ timelineFilter, filteredTimeline });
  },

  toggleSelfNarratives() {
    this.setData({ showSelfNarratives: !this.data.showSelfNarratives });
  },

  scheduleDraftSave() {
    if (!this.draftController) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule(this.data, (status) => this.setData(status));
  },

  onFieldInput(event) {
    this.setData({ [`form.${event.currentTarget.dataset.key}`]: event.detail.value }, () => this.scheduleDraftSave());
  },

  onSliderChange(event) {
    this.setData({ [`form.${event.currentTarget.dataset.key}`]: event.detail.value }, () => this.scheduleDraftSave());
  },

  requireEnrollment() {
    if (this.data.enrollmentId && this.data.canRecord) return true;
    this.setData({
      errorMessage: "需要先完成一份关系测评并报名参加关系探索，之后才能保存成长记录。",
    });
    return false;
  },

  goRelationshipPilot() {
    wx.navigateTo({ url: "/pages/relationship-pilot/index" });
  },

  async saveWeekly() {
    if (this.data.savingWeekly || !this.requireEnrollment()) return;
    const form = this.data.form;
    const weeklySubmissionKey = this.data.weeklySubmissionKey || createIdempotencyKey("relationship-weekly");
    this.setData({ weeklySubmissionKey, savingWeekly: true, slowSaving: false, errorMessage: "" });
    if (this.draftController) this.setData(this.draftController.flush({ ...this.data, weeklySubmissionKey }));
    this.slowTimer = setTimeout(() => this.setData({ slowSaving: true }), 8000);
    try {
      await api.createRelationshipLongitudinal(this.data.enrollmentId, {
        entry_type: "weekly_supplement",
        measures: {
          active_social_count: Number(form.active_social_count),
          authentic_expression_count: Number(form.authentic_expression_count),
          setback_coping: form.setback_coping,
          approach_willingness: Number(form.approach_willingness),
          worry_intensity: Number(form.worry_intensity),
        },
        narratives: { achievement: form.achievement, setback: form.setback },
        event_at: new Date().toISOString(),
        idempotency_key: weeklySubmissionKey,
      });
      wx.showToast({ title: "本周记录已保存", icon: "success" });
      this.setData({
        weeklySubmissionKey: "",
        "form.active_social_count": 0,
        "form.authentic_expression_count": 0,
        "form.setback_coping": "",
        "form.approach_willingness": 3,
        "form.worry_intensity": 3,
        "form.achievement": "",
        "form.setback": "",
      }, () => this.scheduleDraftSave());
      await this.loadGrowth();
    } catch (error) {
      this.setData({ errorMessage: error.message || "本周记录暂时没能保存。" });
    } finally {
      if (this.slowTimer) clearTimeout(this.slowTimer);
      this.setData({ savingWeekly: false, slowSaving: false });
    }
  },

  async saveEvent() {
    if (this.data.savingEvent) return;
    if (!this.requireEnrollment()) return;
    if (!this.data.form.event_summary.trim()) {
      wx.showToast({ title: "请先写下关键事件", icon: "none" });
      return;
    }
    const eventSubmissionKey = this.data.eventSubmissionKey || createIdempotencyKey("relationship-event");
    this.setData({ eventSubmissionKey, savingEvent: true, slowSaving: false, errorMessage: "" });
    if (this.draftController) this.setData(this.draftController.flush({ ...this.data, eventSubmissionKey }));
    this.slowTimer = setTimeout(() => this.setData({ slowSaving: true }), 8000);
    try {
      await api.createRelationshipLongitudinal(this.data.enrollmentId, {
        entry_type: "key_event",
        measures: {},
        narratives: { event_summary: this.data.form.event_summary },
        event_at: new Date().toISOString(),
        idempotency_key: eventSubmissionKey,
      });
      wx.showToast({ title: "关键事件已记录", icon: "success" });
      this.setData({ "form.event_summary": "", eventSubmissionKey: "" }, () => this.scheduleDraftSave());
      await this.loadGrowth();
    } catch (error) {
      this.setData({ errorMessage: error.message || "关键事件暂时没能保存。" });
    } finally {
      if (this.slowTimer) clearTimeout(this.slowTimer);
      this.setData({ savingEvent: false, slowSaving: false });
    }
  },
});
