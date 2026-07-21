const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");
const { createResilientForm } = require("../../utils/resilientForm");

const api = createSafeHomeApi();
const DRAFT_FIELDS = ["selectedSource", "message", "contact", "riskHint"];

Page({
  data: {
    diaryId: "",
    sourceOptions: [{ type: "", id: "", title: "不关联具体记录", meta: "单独提交一条人工支持请求", selected: true }],
    selectedSource: { type: "", id: "", title: "不关联具体记录" },
    loadingSources: true,
    message: "",
    contact: "",
    riskHint: "",
    submitting: false,
    successMessage: "",
    errorMessage: "",
    saveStatus: "尚未填写",
    draftRestored: false,
    slowSubmitting: false,
  },

  async onLoad(options) {
    const diaryId = decodeURIComponent(options.diary_id || "");
    if (!requireLogin({
      redirectUrl: `/pages/supervision/index?diary_id=${encodeURIComponent(diaryId)}`,
      message: "请先登录后再提交人工督导。",
    })) {
      return;
    }
    this.setData({
      diaryId,
    });
    this.draftController = createResilientForm({
      storageKey: "safehome:resilientDraft:supervision",
      fields: DRAFT_FIELDS,
      submissionPrefix: "supervision",
      hasContent: (values) => Boolean(String(values.message || "").trim() || String(values.contact || "").trim() || String(values.riskHint || "").trim()),
    });
    const restored = this.draftController.restore();
    if (restored) this.setData({ ...restored.values, saveStatus: restored.saveStatus, draftRestored: true });
    await this.loadSourceOptions(diaryId);
  },

  onHide() { if (this.draftController && !this.data.submitting) this.setData(this.draftController.flush(this.data)); },
  onUnload() { if (this.draftController && !this.data.submitting) this.draftController.flush(this.data); },

  scheduleDraftSave() {
    if (!this.draftController) return;
    this.setData({ saveStatus: "正在保存草稿…" });
    this.draftController.schedule(this.data, (status) => this.setData(status));
  },

  async loadSourceOptions(diaryId) {
    try {
      const [diariesPayload, assessmentsPayload] = await Promise.all([
        api.listDiaries({ limit: 8 }),
        api.listAssessmentResults({ limit: 8 }),
      ]);
      const diaryOptions = (diariesPayload.items || []).map((item) => ({
        type: "diary",
        id: item.id,
        title: `情绪日记 · ${item.scene || item.parent_emotion || "具体事件"}`,
        meta: String(item.event_description || "").slice(0, 42) || String(item.created_at || "").slice(0, 10),
      }));
      const assessmentOptions = (assessmentsPayload.items || []).map((item) => ({
        type: "assessment",
        id: item.id,
        title: `测一测 · ${item.worksheet_title || "支持性测评"}`,
        meta: String(item.created_at || "").slice(0, 10),
      }));
      const options = [
        { type: "", id: "", title: "不关联具体记录", meta: "单独提交一条人工支持请求" },
        ...diaryOptions,
        ...assessmentOptions,
      ];
      const restoredSource = this.data.selectedSource || {};
      const selected = options.find((item) => item.type === restoredSource.type && item.id === restoredSource.id)
        || options.find((item) => item.type === "diary" && item.id === diaryId)
        || options[0];
      this.setData({
        sourceOptions: options.map((item) => ({ ...item, selected: item.type === selected.type && item.id === selected.id })),
        selectedSource: selected,
        loadingSources: false,
      });
    } catch (error) {
      this.setData({ loadingSources: false });
    }
  },

  selectSource(event) {
    const type = event.currentTarget.dataset.type || "";
    const id = event.currentTarget.dataset.id || "";
    const selected = this.data.sourceOptions.find((item) => item.type === type && item.id === id) || this.data.sourceOptions[0];
    this.setData({
      selectedSource: selected,
      sourceOptions: this.data.sourceOptions.map((item) => ({
        ...item,
        selected: item.type === selected.type && item.id === selected.id,
      })),
    }, () => this.scheduleDraftSave());
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, successMessage: "", errorMessage: "" }, () => this.scheduleDraftSave());
  },

  async submitSupervision() {
    const message = this.data.message.trim();

    if (!message) {
      this.setData({ errorMessage: "请先写下你想请老师进一步看的内容。" });
      return;
    }

    if (this.data.submitting) return;
    if (this.draftController) this.setData(this.draftController.flush(this.data));
    this.setData({ submitting: true, slowSubmitting: false, successMessage: "", errorMessage: "" });
    this.slowTimer = setTimeout(() => this.setData({ slowSubmitting: true }), 8000);

    try {
      await api.createSupervision({
        source_type: this.data.selectedSource.type || undefined,
        source_id: this.data.selectedSource.id || undefined,
        source_title: this.data.selectedSource.title || undefined,
        message,
        contact: this.data.contact.trim(),
        risk_hint: this.data.riskHint.trim(),
        risk_level: "low",
        client_submission_id: this.draftController ? this.draftController.getSubmissionId() : undefined,
      });

      if (this.draftController) this.draftController.clear();

      this.setData({
        successMessage: "已提交。老师后续可以基于这条记录补充理解和练习建议，请不要把这里当作紧急求助入口。",
        message: "",
        contact: "",
        riskHint: "",
        saveStatus: "已提交",
        draftRestored: false,
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "这次提交暂时没能成功，请检查网络后再试一次。",
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
