const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

const sceneOptions = ["作业拖延", "睡前冲突", "手机使用", "出门准备", "亲子沟通"];
const parentEmotionOptions = ["着急", "生气", "担心", "失望", "无力", "内疚"];
const childEmotionOptions = ["烦躁", "委屈", "紧张", "生气", "沉默", "不确定"];
const bodySensationOptions = ["胸口紧", "心跳快", "头胀", "肩膀紧", "胃不舒服", "说不清"];

Page({
  data: {
    sceneOptions,
    parentEmotionOptions,
    childEmotionOptions,
    bodySensationOptions,
    goalId: "",
    submitting: false,
    selectedScene: "亲子沟通",
    customScene: "",
    eventDescription: "",
    parentEmotion: "着急",
    parentEmotionIntensity: 5,
    childEmotion: "烦躁",
    childEmotionIntensity: 5,
    automaticThought: "",
    bodySensation: "说不清",
    bodySensationNote: "",
    behavior: "",
    childReaction: "",
    shortTermResult: "",
    longTermImpact: "",
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

  selectScene(event) {
    this.setData({ selectedScene: event.currentTarget.dataset.value, errorMessage: "" });
  },

  selectParentEmotion(event) {
    this.setData({ parentEmotion: event.currentTarget.dataset.value, errorMessage: "" });
  },

  selectChildEmotion(event) {
    this.setData({ childEmotion: event.currentTarget.dataset.value, errorMessage: "" });
  },

  selectBodySensation(event) {
    this.setData({ bodySensation: event.currentTarget.dataset.value, errorMessage: "" });
  },

  onParentIntensityChange(event) {
    this.setData({ parentEmotionIntensity: Number(event.detail.value), errorMessage: "" });
  },

  onChildIntensityChange(event) {
    this.setData({ childEmotionIntensity: Number(event.detail.value), errorMessage: "" });
  },

  async submitDiary() {
    const scene = (this.data.customScene.trim() || this.data.selectedScene).trim();
    const eventDescription = this.data.eventDescription.trim();
    const childReaction = this.data.childReaction.trim();
    const shortTermResult = this.data.shortTermResult.trim();
    const longTermImpact = this.data.longTermImpact.trim();

    const rawText = [
      childReaction ? `孩子反应：${childReaction}` : "",
      shortTermResult ? `短期结果：${shortTermResult}` : "",
      longTermImpact ? `长期影响：${longTermImpact}` : "",
    ]
      .filter(Boolean)
      .join("\n");

    if (!eventDescription) {
      this.setData({ errorMessage: "请先写下发生了什么。" });
      return;
    }

    this.setData({ submitting: true, errorMessage: "" });

    try {
      const diary = await api.createDiary({
        goal_id: this.data.goalId || undefined,
        scene,
        event_description: eventDescription,
        parent_emotion: this.data.parentEmotion,
        parent_emotion_intensity: this.data.parentEmotionIntensity,
        child_emotion: this.data.childEmotion,
        child_emotion_intensity: this.data.childEmotionIntensity,
        automatic_thought: this.data.automaticThought.trim(),
        body_sensation: [this.data.bodySensation, this.data.bodySensationNote.trim()].filter(Boolean).join("："),
        behavior: this.data.behavior.trim(),
        raw_text: rawText,
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
