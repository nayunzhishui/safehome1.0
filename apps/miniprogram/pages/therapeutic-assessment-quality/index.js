const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();
const DIMENSIONS = [
  { key: "question_quality", label: "问题清楚且可探索" },
  { key: "evidence_sufficiency", label: "依据足够且可追溯" },
  { key: "authorization", label: "人员与对象范围已授权" },
  { key: "language", label: "表达非诊断、非评判" },
  { key: "participant_recognition", label: "保留参与者的不同理解" },
  { key: "action_fit", label: "下一步具体、可退出且适配" },
];
const STATUS_OPTIONS = ["符合", "需要修复", "不适用"];
const STATUS_VALUES = ["pass", "concern", "not_applicable"];

function reviewDimensions() {
  return DIMENSIONS.map((item) => ({
    ...item,
    status: "pass",
    statusIndex: 0,
    statusLabel: STATUS_OPTIONS[0],
    note: "",
    evidenceRef: "",
  }));
}

Page({
  data: {
    loading: true,
    saving: false,
    errorMessage: "",
    notice: "",
    userRole: "",
    isReviewRole: false,
    runtime: null,
    cases: [],
    selectedCaseId: "",
    selectedCaseIndex: 0,
    reviews: [],
    selectedReview: null,
    incidents: [],
    selectedIncident: null,
    reviewDimensions: reviewDimensions(),
    statusOptions: STATUS_OPTIONS,
    remediationSummary: "",
    incidentCategoryIndex: 0,
    incidentCategoryOptions: ["反馈不像我的感受", "希望更正", "希望撤回", "没有收到通知"],
    incidentCategoryValues: ["complaint", "correction_request", "withdrawal_request", "notification_issue"],
    incidentDescription: "",
    requestedResolution: "",
    impactSummary: "",
    resolutionActionIndex: 0,
    resolutionActionOptions: ["保留历史并记录不同理解", "撤回原反馈"],
    resolutionActionValues: ["no_change", "withdraw"],
    resolutionSummary: "",
  },

  async onLoad(options) {
    if (!requireLogin({ redirectUrl: "/pages/therapeutic-assessment-quality/index" })) return;
    const user = getAuthUser() || {};
    this.setData({
      userRole: user.role || "",
      isReviewRole: ["supervisor", "admin"].includes(user.role),
      selectedCaseId: options.caseId || "",
    });
    await this.loadData();
  },

  async onPullDownRefresh() {
    try {
      await this.loadData();
    } finally {
      wx.stopPullDownRefresh();
    }
  },

  async loadData() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const [caseResult, incidentResult, reviewResult] = await Promise.all([
        api.listTherapeuticAssessmentCases(),
        api.listTherapeuticAssessmentQualityIncidents(),
        this.data.isReviewRole
          ? api.listTherapeuticAssessmentQualityReviews({ page_size: 100 })
          : Promise.resolve({ items: [], runtime: null }),
      ]);
      const cases = (caseResult.items || []).map((item) => ({
        ...item,
        displayQuestion: item.working_question || item.assessment_question,
      }));
      const selectedCaseIndex = Math.max(
        0,
        cases.findIndex((item) => item.id === this.data.selectedCaseId),
      );
      const selectedCaseId =
        this.data.selectedCaseId || (cases[selectedCaseIndex] && cases[selectedCaseIndex].id) || "";
      const reviews = (reviewResult.items || []).map((item) => ({
        ...item,
        statusText: {
          pending: "待认领",
          in_review: "复核中",
          passed: "已通过",
          remediation_required: "待修复",
        }[item.status] || item.status,
      }));
      const incidents = (incidentResult.items || []).map((item) => ({
        ...item,
        statusText: {
          reported: "待影响分析",
          independent_review: "待独立结案",
          resolved: "已处理",
        }[item.status] || item.status,
      }));
      this.setData({
        cases,
        selectedCaseId,
        selectedCaseIndex,
        reviews,
        incidents,
        runtime: reviewResult.runtime || null,
        selectedReview: reviews.find((item) => item.id === (this.data.selectedReview && this.data.selectedReview.id)) || reviews[0] || null,
        selectedIncident: incidents.find((item) => item.id === (this.data.selectedIncident && this.data.selectedIncident.id)) || incidents[0] || null,
      });
    } catch (error) {
      this.setData({ errorMessage: error.message || "质量记录暂时没有读取成功。" });
    } finally {
      this.setData({ loading: false });
    }
  },

  onCaseChange(event) {
    const selectedCaseIndex = Number(event.detail.value || 0);
    const item = this.data.cases[selectedCaseIndex];
    this.setData({ selectedCaseIndex, selectedCaseId: item ? item.id : "" });
  },

  selectReview(event) {
    const selectedReview = this.data.reviews.find((item) => item.id === event.currentTarget.dataset.id) || null;
    this.setData({ selectedReview, reviewDimensions: reviewDimensions(), remediationSummary: "" });
  },

  async claimReview() {
    const item = this.data.selectedReview;
    if (!item) return;
    this.setData({ saving: true, errorMessage: "" });
    try {
      await api.claimTherapeuticAssessmentQualityReview(
        item.id,
        item.version,
        `mini-quality-claim-${item.id}-${Date.now()}`,
      );
      this.setData({ notice: "已认领，请完成六项核对。" });
      await this.loadData();
    } catch (error) {
      this.setData({ errorMessage: error.message || "认领失败，请重新读取。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  onDimensionStatus(event) {
    const index = Number(event.currentTarget.dataset.index);
    const statusIndex = Number(event.detail.value);
    const dimensions = this.data.reviewDimensions.slice();
    dimensions[index] = {
      ...dimensions[index],
      status: STATUS_VALUES[statusIndex],
      statusIndex,
      statusLabel: STATUS_OPTIONS[statusIndex],
    };
    this.setData({ reviewDimensions: dimensions });
  },

  onDimensionInput(event) {
    const index = Number(event.currentTarget.dataset.index);
    const key = event.currentTarget.dataset.key;
    const dimensions = this.data.reviewDimensions.slice();
    dimensions[index] = { ...dimensions[index], [key]: event.detail.value };
    this.setData({ reviewDimensions: dimensions });
  },

  onFieldInput(event) {
    this.setData({ [event.currentTarget.dataset.key]: event.detail.value });
  },

  async completeReview() {
    const item = this.data.selectedReview;
    if (!item) return;
    const hasConcern = this.data.reviewDimensions.some((entry) => entry.status === "concern");
    const dimensions = {};
    for (const entry of this.data.reviewDimensions) {
      if (entry.status === "concern" && (!entry.note.trim() || !entry.evidenceRef.trim())) {
        wx.showToast({ title: "修复项需要说明和依据", icon: "none" });
        return;
      }
      dimensions[entry.key] = {
        status: entry.status,
        note: entry.note.trim(),
        evidence_ref: entry.evidenceRef.trim(),
      };
    }
    if (hasConcern && !this.data.remediationSummary.trim()) {
      wx.showToast({ title: "请填写修复说明", icon: "none" });
      return;
    }
    this.setData({ saving: true, errorMessage: "" });
    try {
      await api.completeTherapeuticAssessmentQualityReview(
        item.id,
        {
          expected_version: item.version,
          dimensions,
          decision: hasConcern ? "remediation_required" : "pass",
          remediation_summary: hasConcern ? this.data.remediationSummary.trim() : "",
        },
        `mini-quality-complete-${item.id}-${Date.now()}`,
      );
      this.setData({
        notice: hasConcern ? "已进入独立修复流程，原记录会保留。" : "质量复核已通过。",
        reviewDimensions: reviewDimensions(),
        remediationSummary: "",
      });
      await this.loadData();
    } catch (error) {
      this.setData({ errorMessage: error.message || "提交失败，请重新读取。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  onIncidentCategory(event) {
    this.setData({ incidentCategoryIndex: Number(event.detail.value) });
  },

  async submitIncident() {
    if (!this.data.selectedCaseId || !this.data.incidentDescription.trim() || !this.data.requestedResolution.trim()) {
      wx.showToast({ title: "请完整填写记录和希望的处理方式", icon: "none" });
      return;
    }
    this.setData({ saving: true, errorMessage: "" });
    try {
      await api.createTherapeuticAssessmentQualityIncident(
        this.data.selectedCaseId,
        {
          category: this.data.incidentCategoryValues[this.data.incidentCategoryIndex],
          description: this.data.incidentDescription.trim(),
          requested_resolution: this.data.requestedResolution.trim(),
        },
        `mini-quality-report-${this.data.selectedCaseId}-${Date.now()}`,
      );
      this.setData({
        incidentDescription: "",
        requestedResolution: "",
        notice: "已提交。原记录会保留，处理结果会通过站内消息告知你。",
      });
      await this.loadData();
    } catch (error) {
      this.setData({ errorMessage: error.message || "提交失败，请稍后重试。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  selectIncident(event) {
    const selectedIncident = this.data.incidents.find((item) => item.id === event.currentTarget.dataset.id) || null;
    this.setData({ selectedIncident, impactSummary: "", resolutionSummary: "" });
  },

  async analyzeIncident() {
    const item = this.data.selectedIncident;
    if (!item || !this.data.impactSummary.trim()) return;
    this.setData({ saving: true, errorMessage: "" });
    try {
      await api.analyzeTherapeuticAssessmentQualityIncident(
        item.id,
        {
          expected_version: item.version,
          impact_analysis: {
            severity: "medium",
            affected_scope: "single_case",
            affected_participant_count: 1,
            immediate_action: this.data.impactSummary.trim(),
            evidence_refs: [item.feedback_id ? `feedback:${item.feedback_id}` : `case:${item.case_id}`],
          },
        },
        `mini-quality-analysis-${item.id}-${Date.now()}`,
      );
      this.setData({ impactSummary: "", notice: "影响分析已保存，等待另一位人员独立结案。" });
      await this.loadData();
    } catch (error) {
      this.setData({ errorMessage: error.message || "影响分析保存失败。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  onResolutionAction(event) {
    this.setData({ resolutionActionIndex: Number(event.detail.value) });
  },

  async resolveIncident() {
    const item = this.data.selectedIncident;
    if (!item || !this.data.resolutionSummary.trim()) return;
    this.setData({ saving: true, errorMessage: "" });
    try {
      await api.resolveTherapeuticAssessmentQualityIncident(
        item.id,
        {
          expected_version: item.version,
          resolution_action: this.data.resolutionActionValues[this.data.resolutionActionIndex],
          resolution_summary: this.data.resolutionSummary.trim(),
        },
        `mini-quality-resolution-${item.id}-${Date.now()}`,
      );
      this.setData({ resolutionSummary: "", notice: "已独立结案，并向参与者发送站内通知。" });
      await this.loadData();
    } catch (error) {
      this.setData({ errorMessage: error.message || "结案失败，请重新读取。" });
    } finally {
      this.setData({ saving: false });
    }
  },
});
