const { createSafeHomeApi } = require("../../services/api");
const { ensureServiceConsent, finishServiceConsent } = require("../../utils/serviceConsent");
const api = createSafeHomeApi();

// Legacy navigation IDs select a real card; they never provide fallback content.
const TASK_CARD_IDS = {
  emotion_education: "emotion_naming", emotion_awareness: "emotion_naming",
  body_regulation: "three_second_pause", pause_training: "three_second_pause",
  cognitive_adjustment: "cognitive_flexibility", alternative_thought: "cognitive_flexibility",
  communication_expression: "alternative_behavior", positive_interaction: "alternative_behavior",
  nonjudgmental_company: "nonjudgmental_response", relationship_repair: "nonjudgmental_response",
};

Page({
  data: {
    task: null, loading: true, errorMessage: "", diaryId: "",
    reflection: "", emotionLevel: 5, serviceReady: false, serviceConsent: null,
    serviceEntryError: "",
  },
  onLoad(options = {}) {
    this._cardId = decodeURIComponent(options.card_id || "") || TASK_CARD_IDS[decodeURIComponent(options.id || "")] || "";
    this.setData({ diaryId: decodeURIComponent(options.diary_id || "") });
  },
  onShow() {
    this._hidden = false;
    this._userId = (wx.getStorageSync("auth_user") || {}).id;
    this._token = wx.getStorageSync("auth_token");
    return this.loadTask();
  },
  isCurrentAccount() {
    return !this._hidden && !this._consentDisposed && this._userId === (wx.getStorageSync("auth_user") || {}).id && this._token === wx.getStorageSync("auth_token");
  },
  async loadTask() {
    const requestId = this._requestId = (this._requestId || 0) + 1;
    this.setData({ task: null, loading: true, errorMessage: "" });
    try {
      if (!this._cardId) throw new Error("缺少有效的训练卡信息，请返回重新选择。");
      const result = await api.listCards();
      if (requestId !== this._requestId || !this.isCurrentAccount()) return false;
      const card = (result.items || []).find(item => item.id === this._cardId);
      if (!card) throw new Error("这张训练卡当前未开放，请返回选择可用练习。");
      const steps = card.steps || [];
      this.setData({ loading: false, task: {
        id: card.id, cardId: card.id, title: card.title || "陪伴练习",
        subtitle: card.purpose || card.subtitle || "",
        scenario: card.suitable_scene || (card.suitable_for || [])[0] || "请按个人情况选择",
        duration: card.duration_minutes ? `${card.duration_minutes} 分钟` : "按个人节奏",
        goal: steps[0] || "", steps,
        scripts: card.example_phrase || card.example ? [card.example_phrase || card.example] : [],
        boundaryNotice: card.boundary_notice || "陪伴练习不替代专业咨询或紧急帮助。",
        stopText: (card.stop_rules || card.not_suitable_for || []).join("；"),
      } });
      return true;
    } catch (error) {
      if (requestId === this._requestId && this.isCurrentAccount()) this.setData({ loading: false, task: null, errorMessage: error.message || "训练卡未加载成功，请重试。" });
      return false;
    }
  },
  onHide() {
    this._hidden = true;
    this._requestId = (this._requestId || 0) + 1;
    finishServiceConsent(this, false);
    this.setData({ task: null, serviceReady: false, reflection: "", emotionLevel: 5 });
  },
  onUnload() { this._consentDisposed = true; this.onHide(); },
  goBack() { wx.navigateBack(); },
  returnToPrivacyHome() { wx.switchTab({ url: "/pages/home/index" }); },
  onServiceConsent(event) { finishServiceConsent(this, !!event.detail.agreed); },
  async beginReflection() {
    if (!this.data.task || !this.isCurrentAccount() || this._consentPending) return;
    this.setData({ serviceEntryError: "" });
    try {
      const agreed = await ensureServiceConsent(this, api, "checkin");
      if (this.isCurrentAccount()) this.setData({ serviceReady: agreed });
    } catch (error) {
      if (this.isCurrentAccount()) this.setData({ serviceEntryError: error.message || "知情说明暂时无法确认。" });
    }
  },
  onReflectionInput(event) {
    if (this.data.serviceReady && this.isCurrentAccount()) this.setData({ reflection: event.detail.value });
  },
  onEmotionLevelChange(event) {
    if (this.data.serviceReady && this.isCurrentAccount()) this.setData({ emotionLevel: Number(event.detail.value) });
  },
  startPractice() {
    if (this.data.task && this.isCurrentAccount()) wx.showToast({ title: "可以从第一步开始", icon: "none" });
  },
  async finishPractice() {
    if (this._openingCheckin || !this.data.task || !this.isCurrentAccount()) return;
    this._openingCheckin = true;
    try {
      if (!await this.loadTask()) return;
      const task = this.data.task;
      const diaryQuery = this.data.diaryId ? `&diary_id=${encodeURIComponent(this.data.diaryId)}` : "";
      wx.navigateTo({ url: `/pages/checkin/index?card_id=${encodeURIComponent(task.cardId)}&card_title=${encodeURIComponent(task.title)}${diaryQuery}` });
    } finally { this._openingCheckin = false; }
  },
  recordFeeling() {
    if (!this.data.serviceReady || !this.isCurrentAccount()) return;
    wx.showToast({ title: this.data.reflection.trim() ? "仅保留本页，未提交" : "可以先写一句感受", icon: "none" });
  },
});
