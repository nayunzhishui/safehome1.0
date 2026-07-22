const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

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
    sendingMessage: false,
    sendingFeedback: false,
    developmentFullAccess: false,
  },

  async onLoad() {
    if (!requireLogin({ redirectUrl: "/pages/researcher-dashboard/index" })) return;
    const user = getAuthUser();
    const showcase = await api.getShowcaseAccess().catch(() => ({ enabled: false }));
    this.setData({
      developmentFullAccess: Boolean(showcase.researcher_platform_full_access),
    });
    if (!showcase.enabled && (!user || !["researcher", "admin", "supervisor"].includes(user.role))) {
      this.setData({ loading: false, errorMessage: "当前账号没有研究者权限。" });
      return;
    }
    this.loadDashboard();
  },

  async loadDashboard() {
    try {
      const payload = await api.getRelationshipResearchDashboard();
      const items = (payload.items || []).map((item) => ({
        ...item,
        statusText: statusLabel(item.status),
        reviewStatusText: statusLabel(item.review_status),
      }));
      this.setData({ loading: false, items });
      if (items[0]) await this.selectEnrollmentById(items[0].id);
    } catch (error) {
      this.setData({ loading: false, errorMessage: error.message || "仪表盘暂时无法读取。" });
    }
  },

  selectEnrollment(event) {
    this.selectEnrollmentById(event.currentTarget.dataset.id);
  },

  async selectEnrollmentById(id) {
    try {
      const detail = normalizeDetail(await api.getRelationshipEnrollment(id));
      this.setData({ selected: detail, narrative: null }, () => this.drawMaterial(detail.drawingTask));
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

  onNoteInput(event) { this.setData({ note: event.detail.value }); },
  onStageFeedbackInput(event) {
    const key = event.currentTarget.dataset.key;
    if (!["observation", "evidence", "nextStep", "openQuestion"].includes(key)) return;
    this.setData({ [`stageFeedbackForm.${key}`]: event.detail.value });
  },
  onMessageTitleInput(event) { this.setData({ messageTitle: event.detail.value }); },
  onMessageBodyInput(event) { this.setData({ messageBody: event.detail.value }); },

  async saveNote() {
    if (!this.data.note.trim()) return;
    await api.createRelationshipResearchNote(this.data.selected.id, { note: this.data.note.trim() });
    this.setData({ note: "" });
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

  async saveAndSendStageFeedback() {
    const form = this.data.stageFeedbackForm;
    const observation = form.observation.trim();
    const evidence = form.evidence.trim();
    const nextStep = form.nextStep.trim();
    const openQuestion = form.openQuestion.trim();
    const selected = this.data.selected;
    if (!selected || !observation || !nextStep) {
      wx.showToast({ title: "请填写观察与下一小步", icon: "none" });
      return;
    }
    const sections = [
      `近期可观察到的变化：${observation}`,
      evidence ? `可供共同核对的依据：${evidence}` : "",
      `可以先尝试的一小步：${nextStep}`,
      openQuestion ? `后续可继续讨论：${openQuestion}` : "",
    ].filter(Boolean);
    const text = sections.join("\n\n");
    this.setData({ sendingFeedback: true });
    try {
      let report = selected.latestReport;
      if (!report) report = await api.createRelationshipReport(selected.id);
      if (!["confirmed", "sent", "updated"].includes(report.status)) {
        report = await api.confirmRelationshipReport(report.id);
      }
      report = await api.updateRelationshipReport(report.id, {
        version: `2026.07-stage-feedback-${Date.now()}`,
        personalized_interpretation: text,
      });
      await api.sendRelationshipReport(report.id);
      this.setData({
        stageFeedbackForm: {
          observation: "",
          evidence: "",
          nextStep: "",
          openQuestion: "",
        },
      });
      await this.selectEnrollmentById(selected.id);
      wx.showToast({ title: "阶段性反馈已发送", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "阶段性反馈发送失败", icon: "none" });
    } finally {
      this.setData({ sendingFeedback: false });
    }
  },

  async sendParticipantMessage() {
    const title = this.data.messageTitle.trim();
    const body = this.data.messageBody.trim();
    const selected = this.data.selected;
    if (!selected || !title || !body) {
      wx.showToast({ title: "请填写消息标题和正文", icon: "none" });
      return;
    }
    this.setData({ sendingMessage: true });
    try {
      await api.sendResearcherMessage({
        enrollment_id: selected.id,
        title,
        body,
        message_type: "researcher_message",
        idempotency_key: `researcher-message-${selected.id}-${Date.now()}`,
      });
      this.setData({ messageBody: "" });
      wx.showToast({ title: "已发送到参与者消息", icon: "success" });
    } catch (error) {
      wx.showToast({ title: error.message || "消息发送失败", icon: "none" });
    } finally {
      this.setData({ sendingMessage: false });
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
