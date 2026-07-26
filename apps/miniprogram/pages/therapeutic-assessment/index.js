const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

function submissionKey(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

Page({
  data: {
    loading: true,
    saving: false,
    cases: [],
    activeCase: null,
    question: "",
    shareQuestion: true,
    shareRecentRecord: false,
    actionText: "",
    notice: "",
    errorMessage: "",
  },

  onShow() {
    this.loadCases();
  },

  async loadCases() {
    this.setData({ loading: true, errorMessage: "" });
    try {
      const result = await api.listTherapeuticAssessmentCases();
      const cases = (result.items || []).map((item) => ({
        ...item,
        latestFeedback: (item.feedback_versions || []).filter((version) => version.status === "sent").slice(-1)[0] || null,
      }));
      this.setData({ cases, activeCase: cases[0] || null });
    } catch (error) {
      this.setData({ errorMessage: error.message || "协作记录暂时无法读取。" });
    } finally {
      this.setData({ loading: false });
    }
  },

  onQuestionInput(event) {
    this.setData({ question: event.detail.value });
  },

  onActionInput(event) {
    this.setData({ actionText: event.detail.value });
  },

  onScopeChange(event) {
    const values = event.detail.value || [];
    this.setData({
      shareQuestion: values.includes("question"),
      shareRecentRecord: values.includes("recent_record"),
    });
  },

  async createCase() {
    const question = this.data.question.trim();
    const sharedScope = [];
    if (this.data.shareQuestion) sharedScope.push("question");
    if (this.data.shareRecentRecord) sharedScope.push("recent_record");
    if (!question || !sharedScope.length) {
      this.setData({ errorMessage: "请写下想共同理解的问题，并至少选择一项共享范围。" });
      return;
    }
    this.setData({ saving: true, errorMessage: "", notice: "" });
    try {
      await api.createTherapeuticAssessmentCase(
        { assessment_question: question, shared_scope: sharedScope, consent: true },
        submissionKey("mini-ta-case"),
      );
      this.setData({ question: "", notice: "问题已提交。你仍可修改共享范围、表达不同意见或撤回。" });
      await this.loadCases();
    } catch (error) {
      this.setData({ errorMessage: error.message || "问题暂时没有提交成功。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  async chooseAction() {
    const activeCase = this.data.activeCase;
    const actionText = this.data.actionText.trim();
    if (!activeCase || !activeCase.latestFeedback || !actionText) {
      this.setData({ errorMessage: "收到经人工复核的反馈后，再写下一个愿意尝试的小行动。" });
      return;
    }
    this.setData({ saving: true, errorMessage: "", notice: "" });
    try {
      await api.createTherapeuticAssessmentAction(
        activeCase.id,
        { feedback_version_id: activeCase.latestFeedback.id, action_text: actionText },
        submissionKey("mini-ta-action"),
      );
      this.setData({ actionText: "", notice: "已记录你选择的下一小步。" });
      await this.loadCases();
    } catch (error) {
      this.setData({ errorMessage: error.message || "下一小步暂时没有保存成功。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  disagree() {
    const activeCase = this.data.activeCase;
    if (!activeCase) return;
    wx.showModal({
      title: "表达不同意见",
      editable: true,
      placeholderText: "哪些地方与你的体验不一致？",
      success: async (result) => {
        if (!result.confirm || !String(result.content || "").trim()) return;
        try {
          await api.transitionTherapeuticAssessment(activeCase.id, "disagree", { note: result.content }, submissionKey("mini-ta-disagree"));
          this.setData({ notice: "不同意见已记录，研究者会在下一版本中看到。" });
          await this.loadCases();
        } catch (error) {
          this.setData({ errorMessage: error.message || "不同意见暂时没有保存成功。" });
        }
      },
    });
  },

  withdraw() {
    const activeCase = this.data.activeCase;
    if (!activeCase) return;
    wx.showModal({
      title: "确认撤回本次协作？",
      content: "撤回后不会继续发送新的普通反馈，历史审计按隐私规则保留。",
      success: async (result) => {
        if (!result.confirm) return;
        try {
          await api.transitionTherapeuticAssessment(activeCase.id, "withdraw", { note: "参与者主动撤回" }, submissionKey("mini-ta-withdraw"));
          this.setData({ notice: "本次协作已撤回。" });
          await this.loadCases();
        } catch (error) {
          this.setData({ errorMessage: error.message || "撤回暂时没有完成。" });
        }
      },
    });
  },
});
