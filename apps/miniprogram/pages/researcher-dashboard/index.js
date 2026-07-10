const { createSafeHomeApi } = require("../../services/api");
const { getAuthUser, requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

function normalizeDetail(detail) {
  const tasks = (detail.tasks || []).map((task) => ({
    ...task,
    typeText: task.task_type === "relationship_drawing" ? "关系绘画" : "句子补全",
    answerRows: Object.entries(task.answers || {}).map(([context, answer]) => ({ context, answer })),
    strokeCount: task.drawing_data && Array.isArray(task.drawing_data.strokes) ? task.drawing_data.strokes.length : 0,
  }));
  return {
    ...detail,
    tasks,
    drawingTask: tasks.find((task) => task.task_type === "relationship_drawing") || null,
    latestReport: (detail.reports || [])[0] || null,
  };
}

Page({
  data: { loading: true, errorMessage: "", items: [], selected: null, note: "", narrative: null },

  onLoad() {
    if (!requireLogin({ redirectUrl: "/pages/researcher-dashboard/index" })) return;
    const user = getAuthUser();
    if (!user || !["researcher", "admin", "supervisor"].includes(user.role)) {
      this.setData({ loading: false, errorMessage: "当前账号没有研究者权限。" });
      return;
    }
    this.loadDashboard();
  },

  async loadDashboard() {
    try {
      const payload = await api.getRelationshipResearchDashboard();
      const items = payload.items || [];
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
