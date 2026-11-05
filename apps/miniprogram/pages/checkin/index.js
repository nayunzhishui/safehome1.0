const { createSafeHomeApi } = require("../../services/api");
const { beginServiceEntry, finishServiceConsent } = require("../../utils/serviceConsent");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");

const api = createSafeHomeApi();

const REFLECTION_PROMPTS = ["这次做到哪一步？", "练习前后情绪有什么变化？", "下次想轻一点尝试什么？"];

// 前后分数不给默认值：没拖过滑块就不记分（负责人 11-05 定）；0 分写“平静”。
const UNSET_SCORE_TEXT = "还没选，拖一下滑块";
function scoreText(isSet, value) {
  if (!isSet) return UNSET_SCORE_TEXT;
  return `${value} / 10${Number(value) === 0 ? "（平静）" : ""}`;
}

Page({
  retryServiceEntry() { return this.onLoad(this._entryOptions || {}); },
  returnToPrivacyHome() { wx.switchTab({ url: "/pages/home/index" }); },
  data: {
    serviceReady: false,
    cardId: "",
    diaryId: "",
    cardTitle: "这张训练卡",
    sourceRecommendationId: "",
    emotionBefore: 5,
    emotionAfter: 5,
    beforeSet: false,
    afterSet: false,
    beforeText: UNSET_SCORE_TEXT,
    afterText: UNSET_SCORE_TEXT,
    helpfulnessOptions: [
      { label: "有帮助", value: "helpful" },
      { label: "一般", value: "neutral" },
      { label: "暂时没有帮助", value: "not_helpful_yet" },
    ],
    helpfulnessRating: "",
    skipReason: "",
    reflection: "",
    reflectionPrompts: REFLECTION_PROMPTS,
    reflectionPromptsText: REFLECTION_PROMPTS.join(" · "),
    submitting: false,
    successMessage: "",
    errorMessage: "",
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSubmitting: false,
    submitted: false,
  },

  onLoad(options = {}) { return beginServiceEntry(this, api, "checkin", options, "/pages/checkin/index"); },
  loadAfterConsent(options) {
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
      fields: ["emotionBefore", "emotionAfter", "beforeSet", "afterSet", "helpfulnessRating", "skipReason", "reflection"],
      submissionPrefix: "checkin",
      hasContent: (values) => Boolean(String(values.reflection || "").trim() || String(values.skipReason || "").trim() || values.helpfulnessRating || values.beforeSet || values.afterSet),
    });
    const restored = this.draftController.restore();
    const values = restored ? restored.values : {};
    this.setData({
      cardId,
      diaryId,
      cardTitle,
      sourceRecommendationId: selectedCard && selectedCard.id === cardId ? selectedCard.sourceRecommendationId || "" : "",
      ...values,
      beforeText: scoreText(values.beforeSet, values.emotionBefore),
      afterText: scoreText(values.afterSet, values.emotionAfter),
      saveStatus: restored ? restored.saveStatus : "尚未填写",
      draftRestored: Boolean(restored),
    });
  },

  onHide() { if (this.draftController && !this.data.submitting && !this.data.submitted) this.setData(this.draftController.flush(this.data)); },
  onUnload() { this._consentDisposed = true; finishServiceConsent(this, false); if (this.draftController && !this.data.submitting && !this.data.submitted) this.draftController.flush(this.data); },

  scheduleDraftSave() {
    if (!this.draftController || this.data.submitted) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule(this.data, (status) => this.setData(status));
  },

  onEmotionBeforeChange(event) {
    const value = Number(event.detail.value);
    this.setData({ emotionBefore: value, beforeSet: true, beforeText: scoreText(true, value), successMessage: "", errorMessage: "" }, () => this.scheduleDraftSave());
  },

  onEmotionAfterChange(event) {
    const value = Number(event.detail.value);
    this.setData({ emotionAfter: value, afterSet: true, afterText: scoreText(true, value), successMessage: "", errorMessage: "" }, () => this.scheduleDraftSave());
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
        emotion_before: this.data.beforeSet ? this.data.emotionBefore : undefined,
        emotion_after: this.data.afterSet ? this.data.emotionAfter : undefined,
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
