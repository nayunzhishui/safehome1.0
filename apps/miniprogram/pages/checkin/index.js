const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");

const api = createSafeHomeApi();

Page({
  data: {
    cardId: "",
    diaryId: "",
    cardTitle: "这张训练卡",
    sourceRecommendationId: "",
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
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSubmitting: false,
    submitted: false,
  },

  onLoad(options) {
    const cardId = decodeURIComponent(options.card_id || "");
    const diaryId = decodeURIComponent(options.diary_id || "");
    const cardTitle = decodeURIComponent(options.card_title || "这张训练卡");
    const selectedCard = wx.getStorageSync("safehome:selectedTrainingCard");
    if (!requireLogin({
      redirectUrl: `/pages/checkin/index?card_id=${encodeURIComponent(cardId)}&diary_id=${encodeURIComponent(diaryId)}&card_title=${encodeURIComponent(cardTitle)}`,
      message: "请先登录后再记录练习。",
    })) {
      return;
    }
    this.draftController = createResilientForm({
      storageKey: `safehome:resilientDraft:checkin:${cardId}:${diaryId || "none"}`,
      fields: ["emotionBefore", "emotionAfter", "helpfulnessRating", "skipReason", "reflection"],
      submissionPrefix: "checkin",
      hasContent: (values) => Boolean(String(values.reflection || "").trim() || String(values.skipReason || "").trim() || values.helpfulnessRating || values.emotionBefore !== 5 || values.emotionAfter !== 5),
    });
    const restored = this.draftController.restore();
    this.setData({
      cardId,
      diaryId,
      cardTitle,
      sourceRecommendationId: selectedCard && selectedCard.id === cardId ? selectedCard.sourceRecommendationId || "" : "",
      ...(restored ? restored.values : {}),
      saveStatus: restored ? restored.saveStatus : "尚未填写",
      draftRestored: Boolean(restored),
    });
  },

  onHide() { if (this.draftController && !this.data.submitting && !this.data.submitted) this.setData(this.draftController.flush(this.data)); },
  onUnload() { if (this.draftController && !this.data.submitting && !this.data.submitted) this.draftController.flush(this.data); },

  scheduleDraftSave() {
    if (!this.draftController || this.data.submitted) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule(this.data, (status) => this.setData(status));
  },

  onEmotionBeforeChange(event) {
    this.setData({ emotionBefore: Number(event.detail.value), successMessage: "", errorMessage: "" }, () => this.scheduleDraftSave());
  },

  onEmotionAfterChange(event) {
    this.setData({ emotionAfter: Number(event.detail.value), successMessage: "", errorMessage: "" }, () => this.scheduleDraftSave());
  },

  onReflectionInput(event) {
    this.setData({ reflection: event.detail.value, successMessage: "", errorMessage: "" }, () => this.scheduleDraftSave());
  },

  chooseHelpfulness(event) {
    this.setData({
      helpfulnessRating: event.currentTarget.dataset.value || "",
      successMessage: "",
      errorMessage: "",
    }, () => this.scheduleDraftSave());
  },

  onSkipReasonInput(event) {
    this.setData({ skipReason: event.detail.value, successMessage: "", errorMessage: "" }, () => this.scheduleDraftSave());
  },

  async submitCheckin() {
    if (this.data.submitting || this.data.submitted) return;
    if (!this.data.cardId) {
      this.setData({ errorMessage: "缺少训练卡信息，请返回重新选择训练卡。" });
      return;
    }

    if (this.draftController) this.setData(this.draftController.flush(this.data));
    this.setData({ submitting: true, slowSubmitting: false, successMessage: "", errorMessage: "" });
    this.slowTimer = setTimeout(() => this.setData({ slowSubmitting: true }), 8000);

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
        source_recommendation_id: this.data.sourceRecommendationId || undefined,
        client_submission_id: this.draftController ? this.draftController.getSubmissionId() : undefined,
      });

      if (this.draftController) this.draftController.clear();
      this.setData({
        successMessage: "已记录这次尝试。可以先观察这次练习对自己回应方式的帮助。",
        submitted: true,
        saveStatus: "已提交",
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "这次打卡暂时没能保存，请检查网络后再试一次。",
      });
    } finally {
      if (this.slowTimer) clearTimeout(this.slowTimer);
      this.setData({ submitting: false, slowSubmitting: false });
    }
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
