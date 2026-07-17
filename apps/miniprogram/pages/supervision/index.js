const { createSafeHomeApi } = require("../../services/api");
const { requireLogin } = require("../../utils/authGuard");

const api = createSafeHomeApi();

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
    await this.loadSourceOptions(diaryId);
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
      const selected = options.find((item) => item.type === "diary" && item.id === diaryId) || options[0];
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
    });
  },

  onTextInput(event) {
    const key = event.currentTarget.dataset.key;
    this.setData({ [key]: event.detail.value, successMessage: "", errorMessage: "" });
  },

  async submitSupervision() {
    const message = this.data.message.trim();

    if (!message) {
      this.setData({ errorMessage: "请先写下你想请老师进一步看的内容。" });
      return;
    }

    this.setData({ submitting: true, successMessage: "", errorMessage: "" });

    try {
      await api.createSupervision({
        source_type: this.data.selectedSource.type || undefined,
        source_id: this.data.selectedSource.id || undefined,
        source_title: this.data.selectedSource.title || undefined,
        message,
        contact: this.data.contact.trim(),
        risk_hint: this.data.riskHint.trim(),
        risk_level: "low",
      });

      this.setData({
        successMessage: "已提交。老师后续可以基于这条记录补充理解和练习建议，请不要把这里当作紧急求助入口。",
      });
    } catch (error) {
      this.setData({
        errorMessage: error.message || "这次提交暂时没能成功，请检查网络后再试一次。",
      });
    } finally {
      this.setData({ submitting: false });
    }
  },

  goHome() {
    wx.reLaunch({ url: "/pages/home/index" });
  },
});
