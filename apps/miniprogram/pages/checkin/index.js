const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

Page({
  data: {
    cardId: "",
    diaryId: "",
    cardTitle: "这张训练卡",
    emotionBefore: 5,
    emotionAfter: 5,
    helpfulnessOptions: [
      { label: "有帮助", value: "helpful" },
      { label: "一般", value: "neutral" },
      { label: "暂时没有帮助", value: "not_helpful_yet" },
    ],
    helpfulnessRating: "",
    skipReason: "",
    reflection: "",
    reflectionPrompts: [
      "这次做到哪一步？",
      "练习前后情绪有什么变化？",
      "下次想轻一点尝试什么？",
    ],
    submitting: false,
    successMessage: "",
    errorMessage: "",
  },

  onLoad(options) {
    const cardId = decodeURIComponent(options.card_id || "");
    const diaryId = decodeURIComponent(options.diary_id || "");
    const cardTitle = decodeURIComponent(options.card_title || "这张训练卡");
    if (!requireLogin({
      redirectUrl: `/pages/checkin/index?card_id=${encodeURIComponent(cardId)}&diary_id=${encodeURIComponent(diaryId)}&card_title=${encodeURIComponent(cardTitle)}`,
      message: "请先登录后再记录练习。",
    })) {
      return;
    }
    this.setData({
      cardId,
      diaryId,
      cardTitle,
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

  chooseHelpfulness(event) {
    this.setData({
      helpfulnessRating: event.currentTarget.dataset.value || "",
      successMessage: "",
      errorMessage: "",
    });
  },

  onSkipReasonInput(event) {
    this.setData({ skipReason: event.detail.value, successMessage: "", errorMessage: "" });
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
        helpfulness_rating: this.data.helpfulnessRating || undefined,
        skip_reason: this.data.skipReason.trim() || undefined,
      });

      this.setData({
        successMessage: "已记录这次尝试。可以先观察这次练习对自己回应方式的帮助。",
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "这次打卡暂时没能保存，请检查网络后再试一次。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
