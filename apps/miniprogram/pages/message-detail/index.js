const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    id: "",
    loading: true,
    errorMessage: "",
    message: null,
    canEvaluate: false,
    feedbackEvaluation: "",
    feedbackEvaluationSaving: false,
  },

  onLoad(options) {
    const id = decodeURIComponent(options.id || "");
    this.setData({ id });
    this.loadMessage(id);
  },

  async loadMessage(id) {
    if (!id) {
      this.setData({ loading: false, errorMessage: "缺少消息 ID。" });
      return;
    }
    this.setData({ loading: true, errorMessage: "" });
    try {
      const message = await api.getMessage(id);
      this.setData({
        loading: false,
        message,
        canEvaluate: ["researcher_message", "relationship_stage_feedback", "supervision_feedback", "relationship_report"].includes(message.message_type),
      });
    } catch (error) {
      this.setData({
        loading: false,
        errorMessage: error.message || "消息暂时没能打开。",
      });
    }
  },

  goMessages() {
    wx.navigateBack();
  },

  openSource() {
    const message = this.data.message;
    if (message && message.source_type === "relationship_screening_report" && message.source_id) {
      wx.navigateTo({ url: `/pages/relationship-report/index?id=${encodeURIComponent(message.source_id)}` });
      return;
    }
    if (message && message.source_type === "relationship_narrative" && message.source_id) {
      wx.navigateTo({ url: `/pages/relationship-narrative/index?id=${encodeURIComponent(message.source_id)}` });
    }
  },

  async submitFeedbackEvaluation(event) {
    const message = this.data.message;
    const evaluation = event.detail.evaluation;
    if (!message || this.data.feedbackEvaluationSaving) return;
    this.setData({ feedbackEvaluationSaving: true });
    try {
      await api.createFeedbackLedgerEntry({
        source_type: "message",
        source_id: message.id,
        content_version: message.created_at || message.id,
        evaluation,
        idempotency_key: `message:${message.id}:${Date.now()}`,
      });
      this.setData({ feedbackEvaluation: evaluation });
      wx.showToast({ title: evaluation === "uncomfortable" ? "已记录并等待人工复核" : "已记录你的核对", icon: "none" });
    } catch (error) {
      wx.showToast({ title: error.message || "暂时没能保存", icon: "none" });
    } finally {
      this.setData({ feedbackEvaluationSaving: false });
    }
  },
});
