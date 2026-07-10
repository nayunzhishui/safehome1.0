const { createSafeHomeApi } = require("../../services/api");

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
  { key: "researcher_feedback", label: "研究者反馈" },
];

function formatDate(value) {
  if (!value) return "时间待记录";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
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
    researcher_feedback: "研究者反馈",
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
  weeklySubmissionKey: "",
  eventSubmissionKey: "",
  data: {
    enrollmentId: "",
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
    trendText: "",
    timelineFilters: TIMELINE_FILTERS,
    timelineFilter: "all",
    filteredTimeline: [],
    selfNarratives: [],
    showSelfNarratives: false,
    researcherConfirmations: [],
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

  onLoad(options) {
    this.setData({ enrollmentId: decodeURIComponent(options.enrollment_id || "") });
  },

  onShow() {
    this.loadGrowth();
  },

  async loadGrowth() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const growth = await api.getRelationshipGrowth();
      let enrollmentId = this.data.enrollmentId;
      if (!enrollmentId) {
        const enrollments = await api.listRelationshipEnrollments();
        enrollmentId = (enrollments.items || [])[0]?.id || "";
      }
      const curveGroups = buildCurveGroups(growth.curves);
      const selectedGroup = curveGroups[0]?.key || "";
      const selectedMetric = curveGroups[0]?.metrics[0]?.key || "";
      const timeline = (growth.timeline || []).map((item) => ({
        ...item,
        typeLabel: timelineTypeLabel(item.type),
        dateText: formatDate(item.created_at),
      }));
      this.setData({
        loading: false,
        enrollmentId,
        growth,
        curves: growth.curves || {},
        curveGroups,
        selectedGroup,
        selectedMetric,
        filteredTimeline: timeline,
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
    const points = (this.data.curves[metric.key] || []).map((point, index) => ({ ...point, order: index + 1, dateText: formatDate(point.created_at) }));
    let trendText = "";
    if (points.length >= 2) {
      const change = Number(points[points.length - 1].value) - Number(points[0].value);
      const arrow = change > 0 ? "↑" : change < 0 ? "↓" : "→";
      trendText = `${arrow} 从 ${points[0].value} 到 ${points[points.length - 1].value}，仅作描述，不代表变好或变差。`;
    }
    this.setData({
      selectedGroup: group.key,
      selectedMetrics: group.metrics,
      selectedMetric: metric.key,
      selectedMetricLabel: metric.label,
      selectedPoints: points,
      trendText,
    }, () => this.drawChart(group.key, points));
  },

  selectCurveGroup(event) {
    const key = event.currentTarget.dataset.key;
    const group = this.data.curveGroups.find((item) => item.key === key);
    this.selectCurve(key, group?.metrics[0]?.key);
  },

  selectMetric(event) {
    this.selectCurve(this.data.selectedGroup, event.currentTarget.dataset.key);
  },

  drawChart(groupKey, points) {
    const ctx = wx.createCanvasContext("growthChart", this);
    const width = 620;
    const height = 300;
    ctx.clearRect(0, 0, width, height);
    ctx.setFillStyle("#fbfcfb");
    ctx.fillRect(0, 0, width, height);
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
    const left = 58;
    const right = 24;
    const top = 30;
    const bottom = 52;
    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;
    ctx.setStrokeStyle("#d9e0dc");
    ctx.setLineWidth(1);
    [0, 0.5, 1].forEach((ratio) => {
      const y = top + plotHeight * ratio;
      ctx.beginPath();
      ctx.moveTo(left, y);
      ctx.lineTo(width - right, y);
      ctx.stroke();
    });
    const coordinates = points.map((point, index) => ({
      x: points.length === 1 ? left + plotWidth / 2 : left + (index / (points.length - 1)) * plotWidth,
      y: top + ((max - Number(point.value)) / (max - min || 1)) * plotHeight,
      value: point.value,
      order: index + 1,
    }));
    if (coordinates.length >= 2) {
      ctx.setStrokeStyle("#4f7c6b");
      ctx.setLineWidth(4);
      ctx.setLineJoin("round");
      ctx.beginPath();
      ctx.moveTo(coordinates[0].x, coordinates[0].y);
      coordinates.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
      ctx.stroke();
    }
    coordinates.forEach((point) => {
      ctx.setFillStyle("#4f7c6b");
      ctx.beginPath();
      ctx.arc(point.x, point.y, 7, 0, Math.PI * 2);
      ctx.fill();
      ctx.setFillStyle("#31423c");
      ctx.setFontSize(18);
      ctx.fillText(String(point.value), point.x - 10, point.y - 14);
      ctx.setFillStyle("#728079");
      ctx.setFontSize(16);
      ctx.fillText(`第${point.order}次`, point.x - 20, height - 22);
    });
    ctx.setFillStyle("#728079");
    ctx.setFontSize(16);
    ctx.fillText(String(Number(max.toFixed(1))), 8, top + 6);
    ctx.fillText(String(Number(min.toFixed(1))), 8, top + plotHeight + 6);
    ctx.draw();
  },

  selectTimelineFilter(event) {
    const timelineFilter = event.currentTarget.dataset.key;
    const filteredTimeline = (this.data.growth.timeline || [])
      .filter((item) => timelineMatches(item, timelineFilter))
      .map((item) => ({ ...item, typeLabel: timelineTypeLabel(item.type), dateText: formatDate(item.created_at) }));
    this.setData({ timelineFilter, filteredTimeline });
  },

  toggleSelfNarratives() {
    this.setData({ showSelfNarratives: !this.data.showSelfNarratives });
  },

  onFieldInput(event) {
    this.setData({ [`form.${event.currentTarget.dataset.key}`]: event.detail.value });
  },

  onSliderChange(event) {
    this.setData({ [`form.${event.currentTarget.dataset.key}`]: event.detail.value });
  },

  async saveWeekly() {
    if (!this.data.enrollmentId || this.data.savingWeekly) return;
    const form = this.data.form;
    if (!this.weeklySubmissionKey) this.weeklySubmissionKey = createIdempotencyKey("relationship-weekly");
    this.setData({ savingWeekly: true, errorMessage: "" });
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
        idempotency_key: this.weeklySubmissionKey,
      });
      this.weeklySubmissionKey = "";
      wx.showToast({ title: "本周记录已保存", icon: "success" });
      await this.loadGrowth();
    } catch (error) {
      this.setData({ errorMessage: error.message || "本周记录暂时没能保存。" });
    } finally {
      this.setData({ savingWeekly: false });
    }
  },

  async saveEvent() {
    if (this.data.savingEvent) return;
    if (!this.data.form.event_summary.trim()) {
      wx.showToast({ title: "请先写下关键事件", icon: "none" });
      return;
    }
    this.setData({ savingEvent: true, errorMessage: "" });
    if (!this.eventSubmissionKey) this.eventSubmissionKey = createIdempotencyKey("relationship-event");
    try {
      await api.createRelationshipLongitudinal(this.data.enrollmentId, {
        entry_type: "key_event",
        measures: {},
        narratives: { event_summary: this.data.form.event_summary },
        event_at: new Date().toISOString(),
        idempotency_key: this.eventSubmissionKey,
      });
      this.eventSubmissionKey = "";
      wx.showToast({ title: "关键事件已记录", icon: "success" });
      this.setData({ "form.event_summary": "" });
      await this.loadGrowth();
    } catch (error) {
      this.setData({ errorMessage: error.message || "关键事件暂时没能保存。" });
    } finally {
      this.setData({ savingEvent: false });
    }
  },
});
