const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");

const api = createSafeHomeApi();

const sceneOptions = ["作业拖延", "睡前冲突", "手机使用", "出门准备", "亲子沟通"];
const parentEmotionOptions = ["着急", "生气", "担心", "失望", "无力", "内疚"];
const childEmotionOptions = ["烦躁", "委屈", "紧张", "生气", "沉默", "不确定"];
const bodySensationOptions = ["胸口紧", "心跳快", "头胀", "肩膀紧", "胃不舒服", "说不清"];
const DRAFT_FIELDS = ["goalId", "selectedScene", "customScene", "eventDescription", "parentEmotion", "parentEmotionIntensity", "childEmotion", "childEmotionIntensity", "automaticThought", "bodySensation", "bodySensationNote", "behavior", "childReaction", "shortTermResult", "longTermImpact", "showMoreFields"];

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
    showMoreFields: false,
    errorMessage: "",
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSubmitting: false,
  },

  onLoad(options) {
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
    if (restored) this.setData({ ...restored.values, saveStatus: restored.saveStatus, draftRestored: true });
  },

  onHide() { if (this.draftController && !this.data.submitting) this.setData(this.draftController.flush(this.data)); },
  onUnload() { if (this.draftController && !this.data.submitting) this.draftController.flush(this.data); },

  scheduleDraftSave() {
    if (!this.draftController) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule(this.data, (status) => this.setData(status));
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  selectScene(event) {
    this.setData({ selectedScene: event.currentTarget.dataset.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  selectParentEmotion(event) {
    this.setData({ parentEmotion: event.currentTarget.dataset.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  selectChildEmotion(event) {
    this.setData({ childEmotion: event.currentTarget.dataset.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  selectBodySensation(event) {
    this.setData({ bodySensation: event.currentTarget.dataset.value, errorMessage: "" }, () => this.scheduleDraftSave());
  },

  onParentIntensityChange(event) {
    this.setData({ parentEmotionIntensity: Number(event.detail.value), errorMessage: "" }, () => this.scheduleDraftSave());
  },

  onChildIntensityChange(event) {
    this.setData({ childEmotionIntensity: Number(event.detail.value), errorMessage: "" }, () => this.scheduleDraftSave());
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

    if (!eventDescription) {
      this.setData({ errorMessage: "请先写下发生了什么。" });
      return;
    }

    if (this.data.submitting) return;
    if (this.draftController) this.setData(this.draftController.flush(this.data));
    this.setData({ submitting: true, slowSubmitting: false, errorMessage: "" });
    this.slowTimer = setTimeout(() => this.setData({ slowSubmitting: true }), 8000);

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
