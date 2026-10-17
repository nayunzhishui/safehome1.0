const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

// 消息带来源时底部按钮的文字；以后加新的来源类型，在这里和 openSource 各补一处。
const SOURCE_BUTTON_LABELS = {
  relationship_screening_report: "查看关系探索报告",
  relationship_narrative: "查看已确认探索手记",
  assessment_worksheet: "去填写",
};

// 来源行用“10月9日 20:15”；不是今年的消息保留年份。
function messageTimeText(value) {
  const matched = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
  if (!matched) return String(value || "").slice(0, 16).replace("T", " ");
  const sameYear = Number(matched[1]) === new Date().getFullYear();
  return `${sameYear ? "" : `${matched[1]}年`}${Number(matched[2])}月${Number(matched[3])}日 ${matched[4]}:${matched[5]}`;
}

Page({
  data: {
    id: "",
    loading: true,
    errorMessage: "",
    message: null,
    messageTime: "",
    bodyParagraphs: [],
    canOpenSource: false,
    sourceButtonLabel: "",
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
        messageTime: messageTimeText(message.created_at),
        // 正文按换行分段显示（Figma 670:3177 两段之间留 12 的间距）。
        bodyParagraphs: String(message.body || "暂无更多内容。").split(/\n+/).map((line) => line.trim()).filter(Boolean),
        canOpenSource: Object.prototype.hasOwnProperty.call(SOURCE_BUTTON_LABELS, message.source_type) && !!message.source_id && !message.is_withdrawn,
        sourceButtonLabel: SOURCE_BUTTON_LABELS[message.source_type] || "",
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

  handleStateAction() {
    if (!this.data.id) {
      this.goMessages();
      return;
    }
    this.loadMessage(this.data.id);
  },

  openSource() {
    const message = this.data.message;
    // 研究者发来的量表邀请：直接打开测一测里的那份量表。
    if (message && message.source_type === "assessment_worksheet" && message.source_id) {
      wx.navigateTo({ url: `/pages/assessment-detail/index?id=${encodeURIComponent(message.source_id)}` });
      return;
    }
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
