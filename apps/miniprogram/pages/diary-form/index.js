const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    goalId: "",
    submitting: false,
    eventDescription: "",
    parentEmotionIntensity: 5,
    childEmotionIntensity: 5,
    automaticThought: "",
    behavior: "",
    childReaction: "",
    errorMessage: "",
  },

  onLoad(options) {
    if (options && options.goal_id) {
      this.setData({ goalId: decodeURIComponent(options.goal_id) });
    }
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, errorMessage: "" });
  },

  onParentIntensityChange(event) {
    this.setData({ parentEmotionIntensity: Number(event.detail.value), errorMessage: "" });
  },

  onChildIntensityChange(event) {
    this.setData({ childEmotionIntensity: Number(event.detail.value), errorMessage: "" });
  },

  async submitDiary() {
    const eventDescription = this.data.eventDescription.trim();
    if (!eventDescription) {
      this.setData({ errorMessage: "请先写下发生了什么。" });
      return;
    }

    this.setData({ submitting: true, errorMessage: "" });

    try {
      const diary = await api.createDiary({
        goal_id: this.data.goalId || undefined,
        scene: "亲子互动记录",
        event_description: eventDescription,
        parent_emotion: "当时情绪",
        parent_emotion_intensity: this.data.parentEmotionIntensity,
        child_emotion: "孩子当时情绪",
        child_emotion_intensity: this.data.childEmotionIntensity,
        automatic_thought: this.data.automaticThought.trim(),
        behavior: this.data.behavior.trim(),
        raw_text: this.data.childReaction.trim(),
      });

      wx.navigateTo({
        url: `/pages/feedback-result/index?diary_id=${encodeURIComponent(diary.id)}`,
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "提交失败，请确认 backend 是否已启动。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },
});
