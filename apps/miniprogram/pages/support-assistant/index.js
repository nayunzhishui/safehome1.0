const { createSafeHomeApi } = require("../../services/api");
const { isLoggedIn } = require("../../utils/authGuard");

const api = createSafeHomeApi();

Page({
  data: {
    loading: true,
    sending: false,
    enabled: false,
    consented: false,
    sessionId: "",
    question: "",
    messages: [],
    error: "",
    boundary: "回答可能遗漏情境，不构成诊断、治疗、危机处置或关系判断。",
  },

  onLoad() {
    if (!isLoggedIn()) {
      wx.redirectTo({
        url: "/pages/login/index?redirect=%2Fpages%2Fsupport-assistant%2Findex",
      });
      return;
    }
    this.loadStatus();
  },

  async loadStatus() {
    this.setData({ loading: true, error: "" });
    try {
      const config = await api.getAiQaConfig();
      const participant = config.participant_use_case_policy || {};
      this.setData({
        loading: false,
        enabled: Boolean(config.participant_enabled),
        boundary: participant.boundary_notice || this.data.boundary,
      });
    } catch (error) {
      this.setData({
        loading: false,
        error: error.message || "支持性问答状态暂时没有读取成功。",
      });
    }
  },

  async enableConsent() {
    if (this.data.sending) return;
    this.setData({ sending: true, error: "" });
    try {
      await api.createConsent({
        consent_type: "ai_assistance",
        consent_version: "2026.07-consent-v2",
        agreed: true,
      });
      this.setData({ consented: true });
      wx.showToast({ title: "已记录选择", icon: "success" });
    } catch (error) {
      this.setData({ error: error.message || "选择暂时没有保存成功。" });
    } finally {
      this.setData({ sending: false });
    }
  },

  onQuestionInput(event) {
    this.setData({ question: String(event.detail.value || "").slice(0, 1000) });
  },

  async ensureSession() {
    if (this.data.sessionId) return this.data.sessionId;
    const session = await api.createAiQaSession({
      use_case_id: "participant_support_navigation",
    });
    this.setData({ sessionId: session.id });
    return session.id;
  },

  async sendQuestion() {
    const question = this.data.question.trim();
    if (!question || this.data.sending) return;
    if (!this.data.consented) {
      this.setData({ error: "请先阅读边界并确认AI辅助处理。" });
      return;
    }
    this.setData({ sending: true, error: "" });
    try {
      const sessionId = await this.ensureSession();
      const result = await api.sendAiQaMessage(sessionId, { text: question });
      const answer = result.message || {};
      this.setData({
        question: "",
        messages: [
          ...this.data.messages,
          { id: `q-${Date.now()}`, role: "user", content: question },
          {
            id: answer.id || `a-${Date.now()}`,
            role: "assistant",
            content: answer.content || "当前没有足够的已审核内容回答这个问题。",
            citations: answer.citations || [],
          },
        ],
      });
    } catch (error) {
      this.setData({
        error: error.message || "问题暂时没有发送成功，请稍后重试。",
      });
    } finally {
      this.setData({ sending: false });
    }
  },
});
