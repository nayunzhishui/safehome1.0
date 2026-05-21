const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

const sceneOptions = ["作业拖延", "考试成绩", "睡前冲突", "手机使用", "亲子沟通"];
const oldReactionOptions = ["反复催促", "声音变大", "讲道理停不下来", "直接批评", "沉默冷处理"];
const newReactionOptions = ["先停三秒", "先说出情绪", "问一个小问题", "给一个选择", "用一句话说明期待"];

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
  },

  selectScene(event) {
    this.setData({ selectedScene: event.currentTarget.dataset.value, errorMessage: "" });
  },

  selectOldReaction(event) {
    this.setData({ oldReaction: event.currentTarget.dataset.value, errorMessage: "" });
  },

  selectNewReaction(event) {
    this.setData({ newReaction: event.currentTarget.dataset.value, errorMessage: "" });
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, errorMessage: "" });
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

    this.setData({ submitting: true, errorMessage: "" });

    try {
      const goal = await api.createGoal({
        scene,
        smart_goal: smartGoal,
        motivation: `希望减少的旧反应：${this.data.oldReaction}；希望练习的新反应：${this.data.newReaction}`,
        status: "active",
      });

      wx.showToast({
        title: "目标已保存",
        icon: "success",
      });

      wx.navigateTo({
        url: `/pages/diary-form/index?goal_id=${encodeURIComponent(goal.id)}`,
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "保存失败，请确认 backend 是否已启动。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },
});
