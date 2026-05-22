const { createSafeHomeApi } = require("../../services/api");

const api = createSafeHomeApi();

Page({
  data: {
    cardId: "",
    diaryId: "",
    cardTitle: "这张训练卡",
    emotionBefore: 5,
    emotionAfter: 5,
    reflection: "",
    submitting: false,
    successMessage: "",
    errorMessage: "",
  },

  onLoad(options) {
    this.setData({
      cardId: decodeURIComponent(options.card_id || ""),
      diaryId: decodeURIComponent(options.diary_id || ""),
      cardTitle: decodeURIComponent(options.card_title || "这张训练卡"),
    });
  },

  onEmotionBeforeChange(event) {
    this.setData({ emotionBefore: Number(event.detail.value), successMessage: "", errorMessage: "" });
  },

  onEmotionAfterChange(event) {
    this.setData({ emotionAfter: Number(event.detail.value), successMessage: "", errorMessage: "" });
  },

  onReflectionInput(event) {
    this.setData({ reflection: event.detail.value, successMessage: "", errorMessage: "" });
  },

  async submitCheckin() {
    if (!this.data.cardId) {
      this.setData({ errorMessage: "缺少训练卡信息，请返回重新选择训练卡。" });
      return;
    }

    this.setData({ submitting: true, successMessage: "", errorMessage: "" });

    try {
      await api.createCheckin({
        card_id: this.data.cardId,
        diary_id: this.data.diaryId || undefined,
        completed: true,
        emotion_before: this.data.emotionBefore,
        emotion_after: this.data.emotionAfter,
        reflection: this.data.reflection.trim(),
      });

      this.setData({
        successMessage: "已完成本次练习打卡。可以先观察这次练习对自己回应方式的帮助。",
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "打卡保存失败，请确认 backend 是否已启动。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
