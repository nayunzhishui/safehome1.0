const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

function key(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

Page({
  data: {
    caseId: "",
    actionId: "",
    action: null,
    status: "completed",
    note: "",
    followupKind: "O",
    loading: true,
    saving: false,
    error: "",
  },

  onLoad(options) {
    const caseId = decodeURIComponent(options.caseId || "");
    const actionId = decodeURIComponent(options.actionId || "");
    if (!requireLogin({
      redirectUrl: `/pages/therapeutic-assessment-action-followup/index?caseId=${encodeURIComponent(caseId)}&actionId=${encodeURIComponent(actionId)}`,
      message: "请先登录后再回看这次行动。",
    })) {
      this.setData({ loading: false });
      return;
    }
    this.setData({ caseId, actionId });
    this.load();
  },

  async load() {
    this.setData({ loading: true, error: "" });
    try {
      const result = await api.listTherapeuticAssessmentCases();
      const currentCase = (result.items || []).find((item) => item.id === this.data.caseId);
      const action = currentCase
        ? (currentCase.actions || []).find((item) => item.id === this.data.actionId)
        : null;
      if (!action) throw new Error("没有找到这次行动记录。");
      this.setData({ action });
    } catch (error) {
      this.setData({ error: error.message || "行动记录暂时没有读取成功。" });
    } finally {
      this.setData({ loading: false });
    }
  },

  selectStatus(event) {
    this.setData({ status: event.currentTarget.dataset.value });
  },

  selectKind(event) {
    this.setData({ followupKind: event.currentTarget.dataset.value });
  },

  onNoteInput(event) {
    this.setData({ note: event.detail.value });
  },

  async submit() {
    if (!this.data.action || !this.data.note.trim()) {
      this.setData({ error: "请先写下这次发生了什么，或仍有什么不确定。" });
      return;
    }
    this.setData({ saving: true, error: "" });
    try {
      const updated = await api.updateTherapeuticAssessmentAction(
        this.data.actionId,
        {
          status: this.data.status,
          followup_note: this.data.note.trim(),
          expected_version: this.data.action.version,
        },
        key("mini-ta-action-status"),
      );
      await api.createTherapeuticAssessmentActionFollowup(
        this.data.actionId,
        {
          kind: this.data.followupKind,
          content: this.data.note.trim(),
          observed_at: new Date().toISOString(),
          uncertainty_type: this.data.followupKind === "U" ? "unconfirmed" : undefined,
        },
        key("mini-ta-action-followup"),
      );
      this.setData({ action: updated });
      wx.showToast({ title: "已保存回看", icon: "success" });
      setTimeout(() => wx.redirectTo({ url: "/pages/therapeutic-assessment/index" }), 500);
    } catch (error) {
      this.setData({ error: error.message || "暂时没有保存成功，请稍后重试。" });
    } finally {
      this.setData({ saving: false });
    }
  },

  openTrainingCard() {
    if (!this.data.action || !this.data.action.training_card_id) return;
    wx.navigateTo({
      url: `/pages/training-card/index?id=${encodeURIComponent(this.data.action.training_card_id)}`,
    });
  },
});
