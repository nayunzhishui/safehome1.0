const { createSafeHomeApi } = require("../../services/api");
const { createResilientForm } = require("../../utils/resilientForm");

const api = createSafeHomeApi();

const sceneOptions = ["作业拖延", "考试成绩", "睡前冲突", "手机使用", "亲子沟通"];
const oldReactionOptions = ["反复催促", "声音变大", "讲道理停不下来", "直接批评", "沉默冷处理"];
const newReactionOptions = ["先停三秒", "先说出情绪", "问一个小问题", "给一个选择", "用一句话说明期待"];
const DRAFT_FIELDS = ["selectedScene", "customScene", "oldReaction", "newReaction", "smartGoal"];

Page({
  data: {
    sceneOptions,
    oldReactionOptions,
    newReactionOptions,
    selectedScene: "作业拖延",
    customScene: "",
    oldReaction: "反复催促",
    newReaction: "先停三秒",
    smartGoal: "",
    submitting: false,
    errorMessage: "",
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSubmitting: false,
  },

  onLoad() {
    this.draftController = createResilientForm({
      storageKey: "safehome:resilientDraft:goal",
      fields: DRAFT_FIELDS,
      submissionPrefix: "goal",
      hasContent: (values) => Boolean(String(values.smartGoal || "").trim() || String(values.customScene || "").trim()),
    });
    const restored = this.draftController.restore();
    if (restored) this.setData({ ...restored.values, saveStatus: restored.saveStatus, draftRestored: true });
  },

  onHide() { if (this.draftController && !this.data.submitting) this.setData(this.draftController.flush(this.data)); },
  onUnload() { if (this.draftController && !this.data.submitting) this.draftController.flush(this.data); },

  scheduleDraftSave() {
    if (!this.draftController) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule(this.data, (status) => this.setData(status));
  },

  selectScene(event) {
    this.setData({ selectedScene: event.currentTarget.dataset.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  selectOldReaction(event) {
    this.setData({ oldReaction: event.currentTarget.dataset.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  selectNewReaction(event) {
    this.setData({ newReaction: event.currentTarget.dataset.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  async submitGoal() {
    const scene = (this.data.customScene.trim() || this.data.selectedScene).trim();
    const smartGoal = this.data.smartGoal.trim();

    if (!scene) {
      this.setData({ errorMessage: "请先选择或填写一个常见场景。" });
      return;
    }

    if (!smartGoal) {
      this.setData({ errorMessage: "请写下一个本周可以练习的小目标。" });
      return;
    }

    if (this.data.submitting) return;
    if (this.draftController) this.setData(this.draftController.flush(this.data));
    this.setData({ submitting: true, slowSubmitting: false, errorMessage: "" });
    this.slowTimer = setTimeout(() => this.setData({ slowSubmitting: true }), 8000);

    try {
      const goal = await api.createGoal({
        scene,
        smart_goal: smartGoal,
        motivation: `希望减少的旧反应：${this.data.oldReaction}；希望练习的新反应：${this.data.newReaction}`,
        status: "active",
        client_submission_id: this.draftController ? this.draftController.getSubmissionId() : undefined,
      });

      if (this.draftController) this.draftController.clear();

      wx.showToast({
        title: "目标已保存",
        icon: "success",
      });

      wx.navigateTo({
        url: `/pages/diary-form/index?goal_id=${encodeURIComponent(goal.id)}`,
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "目标暂时没能保存，请检查网络后再试一次。",
      });
    } finally {
      if (this.slowTimer) clearTimeout(this.slowTimer);
      this.setData({ submitting: false, slowSubmitting: false });
    }
  },
});
