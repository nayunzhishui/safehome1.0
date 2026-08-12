const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();
const SECTION_KEYS = ["activity", "assessments", "relationship", "researcher_feedback"];
const SECTION_META = {
  activity: { label: "记录与练习", hint: "我做过什么" },
  assessments: { label: "测评变化", hint: "同量尺再比较" },
  relationship: { label: "关系探索", hint: "单独保留语境" },
  researcher_feedback: { label: "研究者反馈", hint: "共同核对" },
};

function formatDate(value) {
  return value ? String(value).slice(0, 10) : "";
}

function sectionCount(key, section = {}) {
  if (key === "activity") return Number(section.record_count || 0) + Number(section.practice_count || 0);
  if (key === "assessments") return Number(section.group_count || 0);
  if (key === "relationship") {
    return Number(section.task_count || 0) + Number(section.longitudinal_count || 0) + Number(section.report_count || 0);
  }
  return Number(section.count || 0);
}

function buildSectionTabs(sections = {}, activeSection = "activity") {
  return SECTION_KEYS.map((key) => ({
    key,
    ...SECTION_META[key],
    count: sectionCount(key, sections[key]),
    active: key === activeSection,
  }));
}

Page({
  data: {
    loading: true,
    errorMessage: "",
    growth: null,
    activeSection: "activity",
    sectionTabs: buildSectionTabs(),
    activityTimeline: [],
    relationshipTimeline: [],
    feedbackTimeline: [],
    thermometer: [],
    assessmentGroups: [],
    relationshipSummary: {},
    feedbackSummary: {},
    requestedEnrollmentId: "",
    latestEnrollmentId: "",
  },

  onLoad(options = {}) {
    if (!requireLogin({ redirectUrl: "/pages/growth-dashboard/index" })) return;
    const activeSection = SECTION_KEYS.includes(options.section) ? options.section : "activity";
    const requestedEnrollmentId = decodeURIComponent(options.enrollment_id || "");
    this.setData({ activeSection, requestedEnrollmentId });
    this.loadGrowth();
  },

  async loadGrowth() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const growth = await api.getGrowthOverview();
      const sections = growth.sections || {};
      const timeline = (growth.timeline || []).map((item) => ({ ...item, dateText: formatDate(item.created_at) }));
      const activityTypes = new Set(["diary", "checkin", "program", "report"]);
      const relationshipTypes = new Set(["relationship_task", "relationship_record", "relationship_report"]);
      this.setData({
        loading: false,
        growth,
        sectionTabs: buildSectionTabs(sections, this.data.activeSection),
        thermometer: (growth.thermometer || []).map((item) => ({
          ...item,
          dateText: formatDate(item.created_at),
          width: `${Math.max(10, Number(item.intensity_level || 0) * 10)}%`,
        })),
        assessmentGroups: (growth.assessment_groups || []).map((group) => ({
          ...group,
          items: (group.items || []).map((item) => ({
            ...item,
            dateText: formatDate(item.created_at),
            hasValue: item.value !== null && item.value !== undefined && item.value !== "",
          })),
        })),
        activityTimeline: timeline.filter((item) => activityTypes.has(item.type)),
        relationshipTimeline: timeline.filter((item) => relationshipTypes.has(item.type)),
        feedbackTimeline: timeline.filter((item) => item.type === "feedback"),
        relationshipSummary: sections.relationship || {},
        feedbackSummary: sections.researcher_feedback || {},
        latestEnrollmentId: this.data.requestedEnrollmentId || sections.relationship?.latest_enrollment_id || "",
      });
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "成长记录暂时无法读取。" });
    }
  },

  selectSection(event) {
    const activeSection = event.detail.key || event.currentTarget.dataset.key;
    if (!SECTION_KEYS.includes(activeSection)) return;
    this.setData({
      activeSection,
      sectionTabs: this.data.sectionTabs.map((item) => ({ ...item, active: item.key === activeSection })),
    });
  },

  startDiary() {
    wx.navigateTo({ url: "/pages/diary-form/index" });
  },

  openTraining() {
    wx.switchTab({ url: "/pages/training/index" });
  },

  openAssessment() {
    wx.navigateTo({ url: "/pages/assessment/index" });
  },

  openRelationship() {
    if (!this.data.latestEnrollmentId) {
      wx.navigateTo({ url: "/pages/relationship-pilot/index" });
      return;
    }
    wx.navigateTo({
      url: `/pages/relationship-growth/index?detail=1&enrollment_id=${encodeURIComponent(this.data.latestEnrollmentId)}`,
    });
  },

  openMessages() {
    wx.navigateTo({ url: "/pages/messages/index" });
  },
});
