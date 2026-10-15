const { createSafeHomeApi } = require("../../services/api");
const { beginServiceEntry, finishServiceConsent } = require("../../utils/serviceConsent");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");
const emotionEntry = require("../../utils/emotion-entry");

const api = createSafeHomeApi();

const sceneOptions = ["作业拖延", "睡前冲突", "手机使用", "出门准备", "亲子沟通"];
const PARENT_GROUPS = emotionEntry.emotionGroups("parent");
const CHILD_GROUPS = emotionEntry.emotionGroups("child");
const BODY_REGIONS = emotionEntry.bodyRegions();
const DRAFT_FIELDS = [
  "goalId", "selectedScene", "customScene", "eventDescription",
  "parentEmotions", "parentIntensity", "parentIntensitySet",
  "childEmotions", "childIntensity", "childIntensitySet",
  "automaticThought", "bodySensations", "bodySensationNote",
  "behavior", "childReaction", "shortTermResult", "longTermImpact", "showMoreFields",
];

// 场景、情绪、强度、身体感觉都不预选，避免没改的默认值进入记录和统计。
Page({
  retryServiceEntry() { return this.onLoad(this._entryOptions || {}); },
  returnToPrivacyHome() { wx.switchTab({ url: "/pages/home/index" }); },
  data: {
    serviceReady: false,
    sceneOptions,
    categoryLabels: emotionEntry.customCategoryLabels(),
    customMaxLength: emotionEntry.CUSTOM_MAX_LENGTH,
    bodyNoteMaxLength: emotionEntry.BODY_NOTE_MAX_LENGTH,
    maxSelected: emotionEntry.MAX_SELECTED,
    goalId: "",
    submitting: false,
    selectedScene: "",
    customScene: "",
    eventDescription: "",
    parentEmotions: [],
    parentIntensity: 0,
    parentIntensitySet: false,
    childEmotions: [],
    childIntensity: 0,
    childIntensitySet: false,
    customParentWord: "",
    customParentCategoryIndex: -1,
    customChildWord: "",
    customChildCategoryIndex: -1,
    parentGroups: emotionEntry.decorateEmotionGroups(PARENT_GROUPS, []),
    childGroups: emotionEntry.decorateEmotionGroups(CHILD_GROUPS, []),
    parentCustom: [],
    childCustom: [],
    bodyRegions: emotionEntry.decorateBodyRegions(BODY_REGIONS, []),
    automaticThought: "",
    bodySensations: [],
    bodySensationNote: "",
    behavior: "",
    childReaction: "",
    shortTermResult: "",
    longTermImpact: "",
    showMoreFields: false,
    errorMessage: "",
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSubmitting: false,
  },

  onLoad(options = {}) { return beginServiceEntry(this, api, "diary", options, "/pages/diary-form/index"); },
  loadAfterConsent(options) {
    const redirect = options && options.goal_id
      ? `/pages/diary-form/index?goal_id=${encodeURIComponent(decodeURIComponent(options.goal_id))}`
      : "/pages/diary-form/index";
    if (!requireLogin({
      redirectUrl: redirect,
      message: "请先登录后再记录事件。",
    })) {
      return;
    }
    if (options && options.goal_id) {
      this.setData({ goalId: decodeURIComponent(options.goal_id) });
    }
    this.draftController = createResilientForm({
      storageKey: `safehome:resilientDraft:diary:${this.data.goalId || "general"}`,
      fields: DRAFT_FIELDS,
      submissionPrefix: "diary",
      hasContent: (values) => Boolean(String(values.eventDescription || "").trim() || String(values.customScene || "").trim()),
    });
    const restored = this.draftController.restore();
    if (restored) {
      this.setData({ ...restored.values, saveStatus: restored.saveStatus, draftRestored: true });
      this.refreshChoiceViews();
    }
  },

  onHide() { if (this.draftController && !this.data.submitting) this.setData(this.draftController.flush(this.data)); },
  onUnload() { this._consentDisposed = true; finishServiceConsent(this, false); if (this.draftController && !this.data.submitting) this.draftController.flush(this.data); },

  scheduleDraftSave() {
    if (!this.draftController) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule(this.data, (status) => this.setData(status));
  },

  // 早先版本的草稿没有这些数组字段，读回时按空选择处理。
  refreshChoiceViews() {
    const parentEmotions = Array.isArray(this.data.parentEmotions) ? this.data.parentEmotions : [];
    const childEmotions = Array.isArray(this.data.childEmotions) ? this.data.childEmotions : [];
    const bodySensations = Array.isArray(this.data.bodySensations) ? this.data.bodySensations : [];
    this.setData({
      parentEmotions,
      childEmotions,
      bodySensations,
      parentGroups: emotionEntry.decorateEmotionGroups(PARENT_GROUPS, parentEmotions),
      childGroups: emotionEntry.decorateEmotionGroups(CHILD_GROUPS, childEmotions),
      parentCustom: emotionEntry.customSelections(parentEmotions),
      childCustom: emotionEntry.customSelections(childEmotions),
      bodyRegions: emotionEntry.decorateBodyRegions(BODY_REGIONS, bodySensations),
    });
  },

  updateEmotions(role, result) {
    const key = role === "child" ? "childEmotions" : "parentEmotions";
    this.setData({ [key]: result.selected, errorMessage: result.error || "" }, () => {
      this.refreshChoiceViews();
      if (!result.error) this.scheduleDraftSave();
    });
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  selectScene(event) {
    const value = event.currentTarget.dataset.value;
    this.setData({ selectedScene: this.data.selectedScene === value ? "" : value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  toggleEmotion(event) {
    const { role, word } = event.currentTarget.dataset;
    const selected = role === "child" ? this.data.childEmotions : this.data.parentEmotions;
    this.updateEmotions(role, emotionEntry.toggleEmotion(selected, word));
  },

  removeCustomEmotion(event) {
    const { role, word } = event.currentTarget.dataset;
    const selected = role === "child" ? this.data.childEmotions : this.data.parentEmotions;
    this.updateEmotions(role, { selected: emotionEntry.removeEmotion(selected, word) });
  },

  onCustomCategoryChange(event) {
    const key = event.currentTarget.dataset.role === "child" ? "customChildCategoryIndex" : "customParentCategoryIndex";
    this.setData({ [key]: Number(event.detail.value), errorMessage: "" });
  },

  addCustomEmotion(event) {
    const role = event.currentTarget.dataset.role;
    const child = role === "child";
    const result = emotionEntry.addCustomEmotion(
      child ? this.data.childEmotions : this.data.parentEmotions,
      child ? this.data.customChildWord : this.data.customParentWord,
      child ? this.data.customChildCategoryIndex : this.data.customParentCategoryIndex,
    );
    if (!result.error) {
      this.setData(child
        ? { customChildWord: "", customChildCategoryIndex: -1 }
        : { customParentWord: "", customParentCategoryIndex: -1 });
    }
    this.updateEmotions(role, result);
  },

  toggleBody(event) {
    const bodySensations = emotionEntry.toggleBody(this.data.bodySensations, event.currentTarget.dataset.word);
    this.setData({ bodySensations, errorMessage: "" }, () => {
      this.refreshChoiceViews();
      this.scheduleDraftSave();
    });
  },

  onParentIntensityChange(event) {
    this.setData({ parentIntensity: Number(event.detail.value), parentIntensitySet: true, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  onChildIntensityChange(event) {
    this.setData({ childIntensity: Number(event.detail.value), childIntensitySet: true, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  toggleMoreFields() {
    this.setData({ showMoreFields: !this.data.showMoreFields }, () => this.scheduleDraftSave());
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

    if (!scene) {
      this.setData({ errorMessage: "请选一个场景，或者在“其他场景”里写一个。" });
      return;
    }
    if (!eventDescription) {
      this.setData({ errorMessage: "请先写下发生了什么。" });
      return;
    }
    if (!this.data.parentEmotions.length) {
      this.setData({ errorMessage: "请至少选一个你当时的情绪。" });
      return;
    }
    if (!this.data.parentIntensitySet) {
      this.setData({ errorMessage: "请在强度条上选一下主要情绪有多强。" });
      return;
    }

    if (this.data.submitting) return;
    if (this.draftController) this.setData(this.draftController.flush(this.data));
    this.setData({ submitting: true, slowSubmitting: false, errorMessage: "" });
    this.slowTimer = setTimeout(() => this.setData({ slowSubmitting: true }), 8000);

    const childEmotion = emotionEntry.composeEmotions(this.data.childEmotions);
    try {
      const diary = await api.createDiary({
        goal_id: this.data.goalId || undefined,
        scene,
        event_description: eventDescription,
        parent_emotion: emotionEntry.composeEmotions(this.data.parentEmotions),
        parent_emotion_intensity: this.data.parentIntensity,
        child_emotion: childEmotion || undefined,
        child_emotion_intensity: childEmotion && this.data.childIntensitySet ? this.data.childIntensity : undefined,
        automatic_thought: this.data.automaticThought.trim(),
        body_sensation: emotionEntry.composeBody(this.data.bodySensations, this.data.bodySensationNote) || undefined,
        behavior: this.data.behavior.trim(),
        raw_text: rawText,
        client_submission_id: this.draftController ? this.draftController.getSubmissionId() : undefined,
      });

      if (this.draftController) this.draftController.clear();

      wx.navigateTo({
        url: `/pages/feedback-result/index?diary_id=${encodeURIComponent(diary.id)}`,
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "这次记录暂时没能保存，可能是网络的原因。你写的内容还在，检查网络后再点一次保存就好。",
      });
    } finally {
      if (this.slowTimer) clearTimeout(this.slowTimer);
      this.setData({ submitting: false, slowSubmitting: false });
    }
  },
});
